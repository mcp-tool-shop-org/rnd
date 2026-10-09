"""npu_serve API tests. They drive the HTTP layer against fake model objects — no NPU, no OpenVINO
inference — and skip cleanly where openvino/optimum/transformers are not installed (CI)."""

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "experiments" / "npu-probe"))
try:
    import npu_serve
except ImportError:
    npu_serve = None


class FakeEmbedder:
    def __init__(self, boom: Exception | None = None):
        self.device = "NPU"
        self.dim = 3
        self.spec = {"repo": "fake-org/fake-embed", "revision": "deadbeef" * 5,
                     "format": "onnx", "pooling": "mean"}
        self.ir_digest = "sha256:0123456789abcdef"
        self.calls = 0
        self.boom = boom

    def embed(self, text: str):
        self.calls += 1
        if self.boom:
            raise self.boom
        return [0.0, 0.0, 1.0]


class FakeNLI:
    device = "GPU.0"
    ir_digest = "unknown"
    labels = ["entailment", "neutral", "contradiction"]

    def score(self, premise: str, hypothesis: str):
        return {"label": "neutral",
                "probs": {"entailment": 0.1, "neutral": 0.8, "contradiction": 0.1}}


@unittest.skipIf(npu_serve is None, "npu_serve's deps (openvino, optimum, transformers) are not installed")
class ServeApiTest(unittest.TestCase):
    def setUp(self):
        self.state = npu_serve.State()
        self.embedder = FakeEmbedder()
        self.state.embedders["fake-embed"] = self.embedder
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), npu_serve.handler_for(self.state))
        self.srv.daemon_threads = True
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.thread.join(5)

    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def post(self, path, obj=None, raw=None):
        data = raw if raw is not None else json.dumps(obj).encode()
        req = urllib.request.Request(self.base + path, data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_tags_pin_repo_revision_digest(self):
        code, body = self.get("/api/tags")
        self.assertEqual(code, 200)
        details = body["models"][0]["details"]
        self.assertEqual(body["models"][0]["name"], "fake-embed")
        self.assertEqual(details["repo"], "fake-org/fake-embed")
        self.assertEqual(details["revision"], "deadbeef" * 5)
        self.assertEqual(details["ir_digest"], "sha256:0123456789abcdef")
        self.assertEqual(details["pooling"], "mean")

    def test_show_reports_dim_and_pooling(self):
        code, body = self.post("/api/show", {"model": "fake-embed:latest"})
        self.assertEqual(code, 200)
        self.assertEqual(body["dim"], 3)
        self.assertEqual(body["pooling"], "mean")
        code, _ = self.post("/api/show", {"model": "missing"})
        self.assertEqual(code, 404)
        self.state.nli = FakeNLI()
        code, body = self.post("/api/show", {"model": "nli-deberta-v3-base"})
        self.assertEqual(code, 200)
        self.assertIn("entailment", body["labels"])

    def test_embed_happy_path(self):
        code, body = self.post("/api/embed", {"model": "fake-embed", "input": ["a", "b"]})
        self.assertEqual(code, 200)
        self.assertEqual(body["embeddings"], [[0.0, 0.0, 1.0]] * 2)
        self.assertIn("total_duration", body)
        code, body = self.post("/api/embed", {"model": "fake-embed", "input": "one string"})
        self.assertEqual(code, 200)
        self.assertEqual(len(body["embeddings"]), 1)

    def test_embed_unknown_model_is_404(self):
        code, body = self.post("/api/embed", {"model": "missing", "input": "x"})
        self.assertEqual(code, 404)
        self.assertIn("fake-embed", body["error"])

    def test_request_bounds(self):
        code, _ = self.post("/api/embed",
                            {"model": "fake-embed", "input": ["x"] * (npu_serve.MAX_INPUTS + 1)})
        self.assertEqual(code, 400)
        code, _ = self.post("/api/embed", {"model": "fake-embed", "input": [1, 2]})
        self.assertEqual(code, 400)
        code, _ = self.post("/api/embed", raw=b"x" * (npu_serve.MAX_BODY + 1))
        self.assertEqual(code, 413)
        code, body = self.post("/api/embed", raw=b"not json")
        self.assertEqual(code, 400)
        self.assertIn("JSON", body["error"])

    def test_device_error_is_503_never_a_fallback(self):
        self.state.embedders["fake-embed"] = FakeEmbedder(boom=RuntimeError("some driver fault"))
        code, body = self.post("/api/embed", {"model": "fake-embed", "input": "x"})
        self.assertEqual(code, 503)
        self.assertIn("NPU", body["error"])
        code, body = self.get("/health")
        self.assertEqual(body["status"], "ok")  # an ordinary error does not latch the device

    def test_device_lost_latches_until_restart(self):
        fake = FakeEmbedder(boom=RuntimeError("DEVICE_LOST: the NPU hung"))
        self.state.embedders["fake-embed"] = fake
        code, _ = self.post("/api/embed", {"model": "fake-embed", "input": "x"})
        self.assertEqual(code, 503)
        self.assertIsNotNone(self.state.device_lost)
        self.assertEqual(self.state.device_lost["device"], "NPU")
        code, body = self.post("/api/embed", {"model": "fake-embed", "input": "again"})
        self.assertEqual(code, 503)
        self.assertEqual(fake.calls, 1)  # the latch answers before the model is touched again
        self.assertIn("restart", body["error"])
        code, body = self.get("/health")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "device_lost")

    def test_nli(self):
        code, body = self.post("/api/nli", {"premise": "p", "hypothesis": "h"})
        self.assertEqual(code, 404)  # NLI off until loaded
        self.state.nli = FakeNLI()
        code, body = self.post("/api/nli", {"premise": "p", "hypothesis": "h"})
        self.assertEqual(code, 200)
        self.assertEqual(body["results"][0]["label"], "neutral")
        code, _ = self.post("/api/nli", {"pairs": [["p", "h"]] * (npu_serve.MAX_INPUTS + 1)})
        self.assertEqual(code, 400)


if __name__ == "__main__":
    unittest.main()
