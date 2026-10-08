"""Build a small in-domain set of NATURAL (unplanted) errors for checking critics.

    python build.py questions   # new questions over aspire-si's 12 topics, deduplicated against every existing set
    python build.py answers     # one answer per question from a weaker non-Qwen local model
    python build.py screen      # three local judges from different families flag suspect sentences
    python build.py select      # flagged items + a random share of unflagged ones -> review set
    python build.py status

Everything runs through the local Ollama daemon, one model on the GPU at a time, and is
unloaded afterwards. Any model name containing "cloud" is refused (no Ollama Cloud), and each
model's local digest is recorded. Outputs go to ./data/. Design and readout: README.md.
"""

import argparse
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
OLLAMA = "http://127.0.0.1:11434"
RUNS = Path("E:/AI/aspire-si-runs")

QUESTION_MODEL = "mistral-small:24b"
ANSWER_MODEL = "llama3.1:8b"
JUDGES = ["gemma4:31b", "mistral-small:24b", "granite4.1:30b"]
PINNED = {"llama3.1:8b": "46e0c10c039e", "gemma4:31b": "6316f0629137",
          "mistral-small:24b": "8039dd90c113", "granite4.1:30b": "3f3e5df8a021",
          "muse-glimmer:latest": "de878ce33ad8", "nemotron-3.5-lightning:latest": "e7a64ff15fb1"}
# Judges tried after the set was built. They never change screen.json (which chose the review
# set); their flags go to screen_extra.json and are scored against the gold labels.
EXTRA_JUDGES = ["muse-glimmer:latest", "nemotron-3.5-lightning:latest"]
# Ollama's format=json grammar makes muse-glimmer answer {"errors": []} every time (probe on n065,
# 2026-10-08); without it the model flags real errors. These judges reply in plain text and the
# JSON object is pulled out of the reply.
NO_FORMAT = {"muse-glimmer:latest"}


def json_object(text):
    """The first balanced {...} in a reply, parsed."""
    start = text.find("{")
    if start < 0:
        raise json.JSONDecodeError("no object", text, 0)
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj

# aspire-si's topic areas (examples/sft-experiment/lib.py TOPICS), so the set is in-domain.
TOPICS = {
    "programming-concepts": "programming concepts: recursion, data structures, hash tables, types, naming",
    "software-engineering": "software engineering judgment: testing, rewrites vs patches, debugging, race conditions",
    "computer-systems": "how computers and networks work: compilers, interpreters, HTTP/HTTPS, web requests",
    "algorithms": "algorithms and complexity: big-O, searching, sorting, gradient descent",
    "databases": "data storage trade-offs: SQL vs NoSQL, indexing, consistency",
    "everyday-physics": "everyday physics: density, light and colour, heat, seasons, buoyancy",
    "biology-health": "biology and health: vaccines, photosynthesis, the immune system, food safety",
    "earth-climate": "earth science and climate: weather vs climate, the water cycle, energy",
    "probability-puzzles": "probability and reasoning puzzles: Monty Hall, conditional probability, word problems",
    "statistics-causation": "statistics and causation: correlation, sampling, misleading statistics",
    "ethics": "applied ethics: promises, honesty, utilitarianism and its objections, fairness",
    "economics-policy": "economics and public policy: inflation, transport, energy, trade-offs",
}
PER_TOPIC = 9
STOP = set("""a an the and or but if of to in on for with by from as at is are was were be been being this that these
those it its into about how why what which who whom when where can could would should will may might do does did
your you their there them they than then also such some any each other more most much many very just not no
explain describe discuss compare contrast example examples give provide between""".split())

SCREEN = """You are checking an answer for mistakes.

Question: {question}

Answer:
{answer}

List every sentence of the answer that contains a factual error, a wrong number or unit, or a
reasoning step that does not follow from what came before. Do not flag style, vagueness,
omissions or reasonable opinions. Quote each sentence exactly as it appears.

Reply with JSON only: {{"errors": [{{"sentence": "<exact quote>", "why": "<one short reason>"}}]}}
Use an empty list if there are no errors."""


def refuse_cloud(model):
    if "cloud" in model.lower():
        raise SystemExit(f"refusing {model!r}: no Ollama Cloud models")


def post(path, body, timeout=900):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def digest(model):
    with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=30) as r:
        tags = json.loads(r.read())["models"]
    d = next((m["digest"][:12] for m in tags if m["name"] == model), None)
    if d != PINNED.get(model):
        raise SystemExit(f"{model}: local digest {d} != pinned {PINNED.get(model)}")
    return d


def chat(model, prompt, *, json_mode=False, temperature=0.0, num_predict=1400, num_ctx=8192):
    refuse_cloud(model)
    # think=False: thinking models (gemma4) otherwise spend the whole token budget thinking
    # and return empty content. Models without a thinking mode ignore it.
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False, "think": False,
            "options": {"temperature": temperature, "num_predict": num_predict, "num_ctx": num_ctx, "seed": 0}}
    if json_mode:
        body["format"] = "json"
    # muse-glimmer's template leaks its end-of-turn token ("<|eot|>") into content; strip any
    # trailing special tokens so JSON replies parse.
    return re.sub(r"(\s*<\|[a-z_]+\|>)+\s*$", "", post("/api/chat", body)["message"]["content"])


def unload(model):
    post("/api/generate", {"model": model, "keep_alive": 0}, timeout=60)


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save(name, obj):
    DATA.mkdir(exist_ok=True)
    (DATA / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def words(text):
    return {w[:-1] if w.endswith("s") and not w.endswith("ss") else w
            for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOP}


def jaccard(a, b):
    wa, wb = words(a), words(b)
    return len(wa & wb) / len(wa | wb) if wa and wb else 0.0


def existing_prompts():
    """Every prompt any aspire-si set has used or dropped, so the new set shares none."""
    out = set()
    for q in RUNS.glob("*/**/questions.json"):
        d = load_json(q)
        for t, p in d.get("kept", []):
            out.add(p)
        for r in d.get("dropped", []):
            out.add(r["prompt"])
    for f in list(RUNS.glob("**/train_pairs.jsonl")):
        out |= {json.loads(l)["prompt"] for l in f.read_text(encoding="utf-8").splitlines() if l.strip()}
    for f in list(RUNS.glob("**/confirm_set.json")) + list(RUNS.glob("**/judge_set.json")):
        d = load_json(f)
        out |= {p["prompt"] for p in (d if isinstance(d, list) else d.get("pairs", []))}
    return sorted(out)


def cmd_questions(a):
    exclude = existing_prompts()
    digest(QUESTION_MODEL)
    cands = []
    for topic, desc in TOPICS.items():
        req = (f"Write {PER_TOPIC} distinct questions a curious adult might ask about {desc}.\n"
               "Each should call for an explanation or a reasoned answer of one to three paragraphs, not a\n"
               "one-word fact. Vary the style: explain-why, compare, judge a trade-off, solve a short problem,\n"
               f"argue a position.\n\nReply with JSON only: {{\"questions\": [{PER_TOPIC} strings]}}")
        out = json.loads(chat(QUESTION_MODEL, req, json_mode=True, temperature=0.8))
        cands += [(topic, q.strip()) for q in out.get("questions", []) if isinstance(q, str) and q.strip()]
    unload(QUESTION_MODEL)
    kept, dropped = [], []
    for topic, q in cands:
        near = max((jaccard(q, e) for e in exclude), default=0)
        dup = max((jaccard(q, k) for _, k in kept), default=0)
        if near >= 0.4 or dup >= 0.5:
            dropped.append({"topic": topic, "prompt": q, "near_existing": round(near, 2), "near_kept": round(dup, 2)})
        else:
            kept.append((topic, q))
    save("questions.json", {"model": QUESTION_MODEL, "model_digest": PINNED[QUESTION_MODEL],
                            "excluded_prompts": len(exclude), "kept": kept, "dropped": dropped})
    print(f"{len(cands)} candidates, {len(kept)} kept, {len(dropped)} dropped (vs {len(exclude)} existing prompts)")


def cmd_answers(a):
    qs = load_json(DATA / "questions.json")["kept"]
    digest(ANSWER_MODEL)
    rows, t0 = [], time.time()
    for i, (topic, q) in enumerate(qs):
        ans = chat(ANSWER_MODEL, q + "\n\nAnswer in about 450 to 550 words.", temperature=0.7, num_predict=1100)
        rows.append({"id": f"n{i:03d}", "topic": topic, "question": q, "answer": ans.strip()})
    unload(ANSWER_MODEL)
    save("answers.json", {"model": ANSWER_MODEL, "model_digest": PINNED[ANSWER_MODEL], "temperature": 0.7,
                          "seconds": round(time.time() - t0), "items": rows})
    lens = sorted(len(r["answer"]) for r in rows)
    print(f"{len(rows)} answers, median {lens[len(lens)//2]} chars, {round(time.time()-t0)} s")


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 3]


def match(quote, sents):
    import difflib
    best, idx = 0.0, None
    for i, s in enumerate(sents):
        r = 1.0 if quote.strip() and quote.strip() in s else difflib.SequenceMatcher(None, quote, s).ratio()
        if r > best:
            best, idx = r, i
    return idx if best >= 0.75 else None


def cmd_screen(a):
    items = load_json(DATA / "answers.json")["items"]
    judges = JUDGES
    if a.only:
        if a.only not in JUDGES + EXTRA_JUDGES:
            raise SystemExit(f"--only must be one of {JUDGES + EXTRA_JUDGES}")
        extra = a.only in EXTRA_JUDGES
        base = DATA / ("screen_extra.json" if extra else "screen.json")
        if base.exists():
            out = load_json(base)   # re-run one judge, keep the others' flags
        else:
            out = {"judges": {}, "items": {r["id"]: {"sentences": sentences(r["answer"]), "flags": {}} for r in items}}
        judges = [a.only]
    else:
        out = {"judges": {}, "items": {r["id"]: {"sentences": sentences(r["answer"]), "flags": {}} for r in items}}
    for judge in judges:
        out["judges"][judge] = digest(judge)
        t0, bad = time.time(), 0
        for r in items:
            sents = out["items"][r["id"]]["sentences"]
            try:
                reply = chat(judge, SCREEN.format(question=r["question"], answer=r["answer"]),
                             json_mode=judge not in NO_FORMAT, num_predict=700 if judge not in NO_FORMAT else 1500)
                got = json.loads(reply) if judge not in NO_FORMAT else json_object(reply)
                errs = got.get("errors", []) if isinstance(got, dict) else []
            except (json.JSONDecodeError, KeyError, urllib.error.HTTPError):
                # An Ollama 500 (seen once on nemotron-3.5-lightning) counts as an unparsable reply
                # rather than ending the run.
                errs, bad = [], bad + 1
            flags = []
            for e in errs:
                if isinstance(e, dict) and isinstance(e.get("sentence"), str):
                    flags.append({"sentence_index": match(e["sentence"], sents), "quote": e["sentence"][:400], "why": str(e.get("why", ""))[:300]})
            out["items"][r["id"]]["flags"][judge] = flags
        unload(judge)
        print(f"{judge}: {round(time.time()-t0)} s, {bad} unparsable replies")
        save("screen_extra.json" if a.only in EXTRA_JUDGES else "screen.json", out)


def cmd_select(a):
    scr = load_json(DATA / "screen.json")
    rng = random.Random(7)
    flagged, unflagged = [], []
    for iid, it in scr["items"].items():
        votes = {}
        for judge, flags in it["flags"].items():
            for f in flags:
                if f["sentence_index"] is not None:
                    votes.setdefault(f["sentence_index"], set()).add(judge)
        it["votes"] = {str(k): sorted(v) for k, v in votes.items()}
        (flagged if votes else unflagged).append(iid)
    controls = rng.sample(unflagged, k=min(len(unflagged), max(1, round(0.35 * len(unflagged)))))
    review = flagged + controls
    if len(review) > 100:
        review = rng.sample(flagged, k=min(len(flagged), 100 - len(controls))) + controls
    rng.shuffle(review)
    relabel = rng.sample(review, k=min(10, len(review)))
    save("selection.json", {"flagged": len(flagged), "unflagged": len(unflagged), "controls": sorted(controls),
                            "review": review, "relabel_later": relabel, "votes": {i: scr["items"][i]["votes"] for i in review}})
    print(f"flagged {len(flagged)}, unflagged {len(unflagged)}, controls {len(controls)}, review {len(review)}")


def cmd_export(a):
    """The review page's `items` documents: what the Director sees, flags only on screened items."""
    ans = {r["id"]: r for r in load_json(DATA / "answers.json")["items"]}
    scr = load_json(DATA / "screen.json")["items"]
    sel = load_json(DATA / "selection.json")
    docs = []
    for order, iid in enumerate(sel["review"]):
        flags = {}
        for judge, fl in scr[iid]["flags"].items():
            for f in fl:
                if f["sentence_index"] is not None:
                    flags.setdefault(str(f["sentence_index"]), []).append({"judge": judge.split(":")[0], "why": f["why"]})
        docs.append({"id": iid, "order": order, "topic": ans[iid]["topic"], "question": ans[iid]["question"],
                     "sentences": scr[iid]["sentences"], "flags": flags, "review": True,
                     "relabel": iid in sel["relabel_later"]})
    save("review_items.json", docs)
    print(f"{len(docs)} items, {sum(1 for d in docs if d['flags'])} with flags, {sum(d['relabel'] for d in docs)} for re-label")


def cmd_status(a):
    for f in ("questions.json", "answers.json", "screen.json", "selection.json"):
        print(f, "yes" if (DATA / f).exists() else "-")


# ---------------------------------------------------------------- context-rich screen (v2)
# Director rule 2026-10-08: give each judge the purpose, the criteria and worked examples, one
# answer per call, thinking on with room, reasoning before the verdict. The v1 screen
# (screen.json / screen_extra.json) used think off and a 700-token cap, and stays as the record.
SCREEN2 = """You are an expert reviewer helping build a test set of real mistakes in AI-written answers.

Why this matters: the sentences you mark will be compared with careful labels made by other
reviewers, to learn which judges catch real errors. A missed error and a false alarm both cost
us, so read the whole answer carefully before deciding.

What counts as an error (mark it):
- a false fact: a wrong date, name, place, attribution, mechanism or definition;
- a wrong number, unit or calculation, including a step whose arithmetic does not follow;
- a reasoning step that does not follow from what came before, or contradicts the answer itself;
- a cited study, law, person or event that is misdescribed or does not exist as described.

What does not count (do not mark it):
- vagueness, omissions, one-sided arguments, style, or opinions a reasonable expert could hold;
- simplifications a textbook would also make.

Worked examples (none of them come from the answers you will review):
- "The Great Wall of China is easily visible from the Moon with the naked eye." ERROR: it is far
  too narrow to see from the Moon.
- "After a 20% discount a shirt costs $40, so the original price was $48." ERROR: $40 / 0.8 = $50.
- "Antibiotics are effective against viral infections such as the common cold." ERROR: they act
  on bacteria, not viruses.
- "Regular exercise can improve mood for many people." NOT an error: a well-supported claim.
- "Some economists favour carbon taxes over cap-and-trade." NOT an error: a description of views.

Question:
{question}

Answer:
{answer}

{reply_shape}
Use an empty list if the answer has no errors."""

REPLY_THINKING = """Think it through, then reply with JSON only, in this shape:
{"errors": [{"sentence": "<the sentence, quoted exactly>", "why": "<what is wrong and what is right>"}]}"""
# Models without a thinking mode reason in the reply itself, before the verdict.
REPLY_REASONING = """Reply with JSON only, in this shape, writing the reasoning field first: work through the
answer sentence by sentence there, then list the errors you found.
{"reasoning": "<your sentence-by-sentence check>",
 "errors": [{"sentence": "<the sentence, quoted exactly>", "why": "<what is wrong and what is right>"}]}"""


def can_think(model):
    """Ollama's own capability list for the model (thinking or not)."""
    return "thinking" in post("/api/show", {"model": model}, timeout=60).get("capabilities", [])


def chat_full(model, prompt, *, think=True, json_mode=False, num_predict=6000, num_ctx=16384):
    """One call with thinking on; returns (content, thinking, done_reason)."""
    refuse_cloud(model)
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False, "think": think,
            "options": {"temperature": 0.0, "num_predict": num_predict, "num_ctx": num_ctx, "seed": 0}}
    if json_mode:
        body["format"] = "json"
    r = post("/api/chat", body, timeout=1800)
    m = r.get("message", {})
    content = re.sub(r"(\s*<\|[a-z_]+\|>)+\s*$", "", m.get("content") or "")
    return content, m.get("thinking") or "", r.get("done_reason")


def cmd_screen2(a):
    if not a.only:
        raise SystemExit("screen2 runs one judge at a time: --only <model>")
    judge = a.only
    if judge not in JUDGES + EXTRA_JUDGES:
        raise SystemExit(f"--only must be one of {JUDGES + EXTRA_JUDGES}")
    items = load_json(DATA / "answers.json")["items"]
    pilot = bool(a.limit)
    if pilot:
        items = items[: a.limit]
    if a.sample:
        # A fixed, seeded sample (seed 20261008), drawn without looking at the labels; resumes into
        # screen_ctx.json like a full run, so a judge that clears the bar can be extended in place.
        rng = random.Random(20261008)
        keep = set(rng.sample([r["id"] for r in items], a.sample))
        items = [r for r in items if r["id"] in keep]
    path = DATA / ("screen_ctx_pilot.json" if pilot else "screen_ctx.json")
    out = load_json(path) if path.exists() else {
        "prompt": "SCREEN2", "settings": {}, "judges": {},
        "items": {r["id"]: {"sentences": sentences(r["answer"]), "flags": {}, "runs": {}} for r in items}}
    json_mode = judge not in NO_FORMAT
    think = can_think(judge)
    prompt_tail = REPLY_THINKING if think else REPLY_REASONING
    out["judges"][judge] = digest(judge)
    ctx = a.num_ctx or 16384
    budget = a.num_predict or 6000
    out["settings"][judge] = {"think": think, "format_json": json_mode, "num_predict": budget, "num_ctx": ctx,
                              "temperature": 0.0, "seed": 0}
    t0, fails = time.time(), {}
    for r in items:
        sents = out["items"][r["id"]]["sentences"]
        reason, flags, content, thinking, done = None, [], "", "", None
        try:
            content, thinking, done = chat_full(
                judge, SCREEN2.format(question=r["question"], answer=r["answer"], reply_shape=prompt_tail),
                think=think, json_mode=json_mode, num_ctx=ctx, num_predict=budget)
            got = json_object(content)
            errs = got.get("errors", []) if isinstance(got, dict) else None
            if errs is None:
                reason = "no errors list"
            else:
                for e in errs:
                    if isinstance(e, dict) and isinstance(e.get("sentence"), str):
                        flags.append({"sentence_index": match(e["sentence"], sents), "quote": e["sentence"][:400],
                                      "why": str(e.get("why", ""))[:600]})
        except urllib.error.HTTPError as e:
            reason = f"http {e.code}"
        except json.JSONDecodeError:
            reason = "truncated" if done == "length" else "unparsable"
        if reason:
            fails[reason] = fails.get(reason, 0) + 1
        out["items"][r["id"]]["flags"][judge] = None if reason else flags
        out["items"][r["id"]]["runs"][judge] = {"failure": reason, "done_reason": done,
                                                "thinking_chars": len(thinking), "reply": content[:4000]}
        save(path.name, out)   # after every item, so a stop loses nothing
    unload(judge)
    print(f"{judge}: {round(time.time()-t0)} s, failures {fails or 'none'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="screen: re-run just this judge")
    ap.add_argument("--num-ctx", type=int, dest="num_ctx", help="screen2: context window (default 16384)")
    ap.add_argument("--num-predict", type=int, dest="num_predict", help="screen2: token budget incl. thinking (default 6000)")
    ap.add_argument("--sample", type=int, help="screen2: a fixed seeded sample of N answers (seed 20261008)")
    ap.add_argument("--limit", type=int, help="screen2: pilot on the first N answers (separate file)")
    ap.add_argument("step", choices=["questions", "answers", "screen", "screen2", "select", "export", "status"])
    a = ap.parse_args()
    {"questions": cmd_questions, "answers": cmd_answers, "screen": cmd_screen, "screen2": cmd_screen2, "select": cmd_select, "export": cmd_export, "status": cmd_status}[a.step](a)


if __name__ == "__main__":
    sys.exit(main())
