"""One-row Data Designer job. The real model path refuses to run without a grant."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from egress import EgressGuard
from studio_lock import (
    CONFIGS_FILE,
    HOME,
    LOCAL_DIGEST,
    LOCAL_ENDPOINT,
    LOCAL_MODEL,
    LOCAL_PROVIDER,
    arm,
    assert_provider_list,
    import_data_designer,
    refuse_cloud,
    require_locked_files,
)

HERE = Path(__file__).resolve().parent
OLLAMA = "http://127.0.0.1:11434"

PROMPT = """You are writing one short answer for a local pipeline check.

Purpose: show that one local model can finish a single item and come back with
the reason it stopped.

Criteria: answer the question in two sentences. Name the physical reason. Do not
invent a number. Do not answer a different question.

Worked example, not the item:
Question: Why does a hot-air balloon rise?
Answer: The air inside the balloon is warmer than the air around it, so it is
less dense. The denser outside air pushes the balloon upward.

Item:
Question: {{ question }}
"""


def prompt_hash() -> str:
    return hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()


def install_finish_recorder():
    import data_designer.engine.models.clients.adapters.openai_compatible as adapter
    import data_designer.engine.models.clients.parsing as parsing

    reasons: list[str | None] = []

    def record(response) -> None:
        choices = response.get("choices") if isinstance(response, dict) else None
        if choices:
            reasons.append(choices[0].get("finish_reason"))

    orig_sync = parsing.parse_chat_completion_response
    orig_async = parsing.aparse_chat_completion_response

    def wrapped_sync(response):
        result = orig_sync(response)
        record(response)
        return result

    async def wrapped_async(response):
        result = await orig_async(response)
        record(response)
        return result

    adapter.parse_chat_completion_response = wrapped_sync
    adapter.aparse_chat_completion_response = wrapped_async
    return reasons


def install_local_token_counter() -> None:
    """Column stats call tiktoken, which downloads cl100k_base from a public host.

    Bind a local counter in every module that imported the function, and refuse
    the tokenizer itself. A blocked download is still an attempt.
    """
    import data_designer.engine.analysis.utils.column_statistics_calculations as stats
    import data_designer.engine.models.clients.parsing as parsing
    import data_designer.engine.utils.token_counting as counting

    def count_text_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, len(text.encode("utf-8")) // 4)

    def refuse_tokenizer():
        raise RuntimeError("tiktoken encoding download is refused")

    counting.count_text_tokens = count_text_tokens
    counting.get_cl100k_base_tokenizer = refuse_tokenizer
    stats.count_text_tokens = count_text_tokens
    parsing.count_text_tokens = count_text_tokens


def local_digest() -> str:
    with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=30) as response:
        tags = json.loads(response.read())["models"]
    found = next((model["digest"][:12] for model in tags if model["name"] == LOCAL_MODEL), None)
    if found != LOCAL_DIGEST:
        raise SystemExit(f"{LOCAL_MODEL}: local digest {found} != pinned {LOCAL_DIGEST}")
    return found


def loaded_models() -> list[str]:
    with urllib.request.urlopen(OLLAMA + "/api/ps", timeout=30) as response:
        body = json.loads(response.read())
    return [model["name"] for model in body.get("models", [])]


def build(endpoint: str):
    import data_designer.config as dd

    refuse_cloud(LOCAL_MODEL)
    provider = dd.ModelProvider(
        name=LOCAL_PROVIDER,
        endpoint=endpoint,
        provider_type="openai",
        api_key="OLLAMA_LOCAL_API_KEY",
    )
    model = dd.ModelConfig(
        alias="mistral-small",
        model=LOCAL_MODEL,
        provider=LOCAL_PROVIDER,
        inference_parameters=dd.ChatCompletionInferenceParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=1024,
            max_parallel_requests=1,
            extra_body={"seed": 0},
        ),
    )
    builder = dd.DataDesignerConfigBuilder(model_configs=[model])
    builder.add_column(
        dd.SamplerColumnConfig(
            name="question",
            sampler_type=dd.SamplerType.CATEGORY,
            params=dd.CategorySamplerParams(values=["Why does ice float on liquid water?"]),
        )
    )
    builder.add_column(
        dd.LLMTextColumnConfig(
            name="answer",
            model_alias="mistral-small",
            prompt=PROMPT,
            extract_reasoning_content=True,
            with_trace=dd.TraceType.LAST_MESSAGE,
        )
    )
    return provider, builder


def run(endpoint: str) -> dict:
    arm()
    require_locked_files()
    import_data_designer()
    import data_designer.config as dd
    from data_designer.engine.models.telemetry import TELEMETRY_ENABLED
    from data_designer.interface import DataDesigner

    provider, builder = build(endpoint)
    designer = DataDesigner(model_providers=[provider], artifact_path=HERE / "runs")
    designer.set_run_config(
        dd.RunConfig(
            max_in_flight_tasks=1,
            max_concurrent_row_groups=1,
            non_inference_max_parallel_workers=1,
            buffer_size=1,
            otel_metrics_port=None,
            display_tui=False,
        )
    )
    # The job's provider is the one passed in. The file on disk is checked too,
    # so a later caller that forgets to pass providers still cannot see the defaults.
    file_providers = designer.get_default_model_providers()
    if endpoint == LOCAL_ENDPOINT:
        assert_provider_list(file_providers)
        assert_provider_list(designer.model_provider_registry.providers)
    else:
        rows = [
            {"name": item.name, "endpoint": item.endpoint.rstrip("/")}
            for item in designer.model_provider_registry.providers
        ]
        if rows != [{"name": LOCAL_PROVIDER, "endpoint": endpoint.rstrip("/")}]:
            raise RuntimeError(f"stub provider list is wrong: {rows}")
        assert_provider_list(file_providers)

    reasons = install_finish_recorder()
    install_local_token_counter()
    started = time.perf_counter()
    preview = designer.preview(builder, num_records=1)
    seconds = round(time.perf_counter() - started, 3)
    frame = preview.dataset
    if len(frame) != 1:
        raise RuntimeError(f"expected 1 row, got {len(frame)}")
    answer = str(frame.loc[0, "answer"]) if "answer" in frame.columns else ""
    reasoning = frame.loc[0, "answer__reasoning_content"] if "answer__reasoning_content" in frame.columns else None
    if not answer.strip():
        raise RuntimeError("empty answer is a failure")
    if any(reason == "length" for reason in reasons):
        raise RuntimeError(f"truncation is a failure: finish_reason={reasons}")
    if not reasons or any(reason != "stop" for reason in reasons):
        raise RuntimeError(f"expected every finish_reason to be stop, got {reasons}")
    return {
        "providers": [item.name for item in designer.model_provider_registry.providers],
        "file_providers": [item.name for item in file_providers],
        "telemetry_enabled": bool(TELEMETRY_ENABLED),
        "question": str(frame.loc[0, "question"]),
        "answer": answer,
        "reasoning": None if reasoning is None or (isinstance(reasoning, float) and reasoning != reasoning) else reasoning,
        "finish_reasons": reasons,
        "seconds": seconds,
        "prompt_sha256": prompt_hash(),
        "model": LOCAL_MODEL,
        "max_parallel_requests": 1,
    }


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    if mode == "stub":
        endpoint = os.environ["STUB_ENDPOINT"]
        with EgressGuard() as guard:
            row = run(endpoint)
        row["seen_hosts"] = sorted(set(guard.seen))
        row["blocked_hosts"] = guard.blocked
        if guard.blocked:
            raise SystemExit(f"egress blocked hosts: {guard.blocked}")
        if any(host not in {"127.0.0.1", "::1", "localhost"} for host in guard.seen):
            raise SystemExit(f"non-local host in seen: {guard.seen}")
        print(json.dumps(row))
        return 0

    if os.environ.get("STUDIO_GPU_GRANT") != "granted":
        raise SystemExit("refusing smoke: STUDIO_GPU_GRANT is not 'granted'")
    loaded = loaded_models()
    if loaded != [LOCAL_MODEL] and loaded:
        raise SystemExit(f"refusing smoke: another model is loaded: {loaded}")
    digest = local_digest()
    with EgressGuard() as guard:
        row = run(LOCAL_ENDPOINT)
    row["digest"] = digest
    row["seen_hosts"] = sorted(set(guard.seen))
    row["blocked_hosts"] = guard.blocked
    row["loaded_before"] = loaded
    if guard.blocked:
        raise SystemExit(f"egress blocked hosts: {guard.blocked}")
    out = HERE / "runs" / "phase0-smoke.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(row, indent=2), encoding="utf-8")
    # The on-disk model config must still match the pin file after the run.
    if not CONFIGS_FILE.exists():
        raise SystemExit("model config disappeared during the run")
    print(json.dumps(row, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
