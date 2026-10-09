#!/usr/bin/env python3
"""How long is the longest chunk offrig will ask the NPU to embed, in nomic tokens?

Answers the npu-serve bucket question for the retrieval benchmark (retrieval-benchmark.md): the ladder
of compiled sequence lengths must cover the longest chunk without truncating, or the option-C parity
check would measure truncation, not model difference.

This is a faithful port of offrig's walk accept rules and chunk() from index.rs @ a45fe53
(MIN_CHARS 800 / MAX_CHARS 2000 / MAX_FILE_BYTES 1_000_000; secret-like names; NUL and UTF-8 and empty
skips; header line "[source \u00b7 kind \u00b7 title]"). It exists for this measurement only: the real chunks come
from `offrig index` in phase 2, and the parity receipt's overflow count (which should then read 0)
cross-checks this one's bucket choice. tests/test_chunk_lengths.py pins the port against the five
chunker cases in index.rs's own test module.

File set: `git archive` exports at the pinned commits (role-os @ ce91be8, offrig @ a45fe53) contain
tracked files only, which is what offrig's ignore-crate walker yields on a clean export; .git/.offrig
are absent from archives. Token counts are the pinned nomic tokenizer's, over "search_document: " +
body (queries: "search_query: " + text); the prefix is part of what the server tokenizes, so it is
part of the count.

    E:/AI/envs/npu-openvino/Scripts/python.exe -X utf8 chunk_lengths.py \
        --corpus role-os=E:/AI/rnd-npu-index/corpus-roleos-ce91be8 \
        --corpus offrig=E:/AI/rnd-npu-index/corpus-offrig-a45fe53 \
        --out results/2026-10-09-nomic-chunk-lengths.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import nomic_parity as np_

MIN_CHARS = 800
MAX_CHARS = 2000
MAX_FILE_BYTES = 1_000_000
BUCKET_LADDER = (128, 256, 512, 1024, 2048, 4096, 8192)

DECL_STARTS = ("fn ", "pub ", "impl", "struct ", "enum ", "trait ", "mod ", "def ", "class ",
               "function ", "export ", "async ", "func ", "type ", "interface ", "const ", "static ",
               "#[")
CODE_EXT = {"rs", "py", "js", "mjs", "cjs", "ts", "tsx", "jsx", "go", "java", "kt", "c", "h", "cc",
            "cpp", "hpp", "cs", "rb", "php", "swift", "lua", "sh", "ps1", "sql", "toml", "yaml",
            "yml", "json", "html", "css", "gd"}


def kind_for(path) -> str:
    ext = str(path).rsplit(".", 1)[-1].lower() if "." in str(path) else ""
    if ext == "log":
        return "log"
    return "code" if ext in CODE_EXT else "doc"


def secret_like(name: str) -> bool:
    n = name.lower()
    return (n.startswith(".env") or n.startswith("id_") or "credentials" in n
            or any(n.endswith(e) for e in (".pem", ".key", ".p12", ".pfx")))


def header(source: str, kind: str, title: str) -> str:
    return f"[{source} \u00b7 {kind} \u00b7 {title}]"


def is_decl(line: str) -> bool:
    if not line or line[0].isspace():
        return False
    return line.startswith(DECL_STARTS)


def is_heading(line: str) -> bool:
    return line.startswith("#") and line.lstrip("#").startswith(" ")


def split_long(s: str, max_chars: int) -> list:
    """Pieces of at most max_chars, on line breaks where it can. Exactly Rust's split_long."""
    out = []
    cur = ""
    for line in s.split("\n"):
        while len(line) > max_chars:
            if cur:
                out.append(cur)
                cur = ""
            out.append(line[:max_chars])
            line = line[max_chars:]
        extra = 1 if cur else 0
        if cur and len(cur) + extra + len(line) > max_chars:
            out.append(cur)
            cur = ""
        if cur:
            cur += "\n"
        cur += line
    if cur:
        out.append(cur)
    return out


def chunk(source: str, kind: str, text: str) -> list:
    """Exactly Rust's chunk(): blocks on blank lines and (per kind) headings or top-level
    declarations, pieces capped at MAX_CHARS on line breaks, packed into the 800..2000-char band, a
    scrap at the end joining the chunk before it when that fits. Bodies carry the header line.
    One deliberate approximation: Python rstrip() stands in for Rust trim_end(); both trim Unicode
    whitespace, and any exotic-space difference moves a char count, never a bucket decision."""
    file_title = source.rsplit("/", 1)[-1]
    title = file_title
    blocks = []
    cur = []
    cur_title = title
    cur_structural = False

    def flush():
        nonlocal cur
        if cur:
            blocks.append({"title": cur_title, "text": "\n".join(cur),
                           "structural": cur_structural})
            cur = []

    for raw in text.split("\n"):
        line = raw.rstrip()
        structure = is_heading(line) if kind == "doc" else is_decl(line) if kind == "code" else False
        if not line:
            flush()
            continue
        if structure:
            flush()
            title = line.lstrip("#").strip()[:80]
        if not cur:
            cur_title = title
            cur_structural = structure
        cur.append(line)
    flush()

    packed = []  # (title, body)
    open_chunk = None
    for b in blocks:
        pieces = split_long(b["text"], MAX_CHARS)
        for i, piece in enumerate(pieces):
            structural = b["structural"] and i == 0
            if open_chunk is not None:
                t, body = open_chunk
                fits = len(body) + 2 + len(piece) <= MAX_CHARS
                if fits and not (structural and len(body) >= MIN_CHARS):
                    open_chunk = (t, body + "\n\n" + piece)
                    continue
                packed.append(open_chunk)
            open_chunk = (b["title"], piece)
    if open_chunk is not None:
        packed.append(open_chunk)
    if len(packed) > 1:
        tail_len = len(packed[-1][1])
        prev_len = len(packed[-2][1])
        if tail_len < MIN_CHARS // 4 and prev_len + 2 + tail_len <= MAX_CHARS:
            _, tail = packed.pop()
            t, prev = packed[-1]
            packed[-1] = (t, prev + "\n\n" + tail)
    return [{"ordinal": i, "title": t, "body": f"{header(source, kind, t)}\n{body}"}
            for i, (t, body) in enumerate(packed)]


def walk_accept(root: Path):
    """(rel_source, kind, text, skipped_reason) for every file under root. The archive export already
    restricts to tracked files (what the ignore walker yields); this applies the rest of offrig's
    accept rules in declaration order."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", ".offrig")]
        for fn in filenames:
            p = Path(dirpath) / fn
            rel = p.relative_to(root).as_posix()
            if secret_like(fn):
                out.append((rel, None, None, "secrets-like file"))
                continue
            if p.stat().st_size > MAX_FILE_BYTES:
                out.append((rel, None, None, "over 1 MB"))
                continue
            data = p.read_bytes()
            if b"\x00" in data[:8192]:
                out.append((rel, None, None, "binary"))
                continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                out.append((rel, None, None, "not UTF-8 text"))
                continue
            if not text.strip():
                out.append((rel, None, None, "empty"))
                continue
            out.append((rel, kind_for(p.name), text, None))
    out.sort(key=lambda r: r[0])
    return out


def _stats(values: list) -> dict:
    s = sorted(values)
    n = len(s)

    def pct(q):
        return s[min(n - 1, max(0, int(q * n)))]

    return {"n": n, "min": s[0], "p50": pct(0.50), "p95": pct(0.95), "p99": pct(0.99),
            "max": s[-1], "mean": round(sum(s) / n, 1)}


def suggest_bucket(max_tokens: int) -> int:
    for b in BUCKET_LADDER:
        if b >= max_tokens:
            return b
    return BUCKET_LADDER[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description="Chunk-length histogram for the nomic bucket ladder.")
    ap.add_argument("--corpus", action="append", required=True, metavar="NAME=PATH")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(np_.NOMIC_ONNX["repo"], revision=np_.NOMIC_ONNX["revision"])
    started = time.time()
    receipt = {"date": time.strftime("%Y-%m-%d"),
               "kind": "chunk-length histogram: nomic tokens per offrig chunk",
               "for": "npu-serve bucket ladder (retrieval-benchmark.md option-C setup)",
               "chunker": "offrig index.rs @ a45fe53, ported; pinned by index.rs's own chunker tests",
               "tokenizer": np_.NOMIC_ONNX, "counts_include": "task prefix + header + body",
               "corpora": {}}
    all_doc_tokens = []
    for spec in a.corpus:
        name, _, path = spec.partition("=")
        root = Path(path)
        rows = walk_accept(root)
        chunks = []
        skipped = {}
        for rel, kind, text, why in rows:
            if why:
                skipped[why] = skipped.get(why, 0) + 1
                continue
            chunks.extend({"source": rel, **c} for c in chunk(rel, kind, text))
        prefixed = [np_.task_prefix("nomic-embed-text", "document") + c["body"] for c in chunks]
        enc = tok(prefixed, add_special_tokens=True)["input_ids"]
        for c, ids in zip(chunks, enc):
            c["tokens"] = len(ids)
        toks = [c["tokens"] for c in chunks]
        all_doc_tokens.extend(toks)
        longest = sorted(chunks, key=lambda c: -c["tokens"])[:10]
        receipt["corpora"][name] = {
            "path": str(root), "files_walked": len(rows), "skipped": skipped,
            "chunks": len(chunks), "tokens": _stats(toks), "over_512": sum(t > 512 for t in toks),
            "longest": [{"source": c["source"], "ordinal": c["ordinal"], "title": c["title"],
                         "tokens": c["tokens"], "body_chars": len(c["body"])} for c in longest]}
        print(f"{name}: {len(chunks)} chunks from {len(rows) - sum(skipped.values())} files; "
              f"max {max(toks)} tokens, over 512: {sum(t > 512 for t in toks)}", flush=True)
    queries = np_.queries_from_facts()
    qpref = [np_.task_prefix("nomic-embed-text", "query") + t for _, t in queries]
    qtoks = [len(ids) for ids in tok(qpref)["input_ids"]]
    observed_max = max(all_doc_tokens + qtoks)
    receipt["queries"] = {"n": len(queries), "tokens": _stats(qtoks),
                          "over_512": sum(t > 512 for t in qtoks)}
    receipt["decision"] = {"observed_max_tokens": observed_max,
                           "suggested_bucket": suggest_bucket(observed_max),
                           "note": "smallest ladder size covering every chunk and query, untruncated"}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(f"observed max {observed_max} tokens -> bucket {suggest_bucket(observed_max)}; "
          f"wrote {a.out}")


if __name__ == "__main__":
    main()
