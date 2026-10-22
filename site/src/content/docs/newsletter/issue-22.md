---
title: "Moving a deterministic game to Rust, and proving it plays the same"
description: "Escape the Valley, the studio's Oregon-Trail-style terminal game, is moving from Python to Rust. Before writing any of it, we ran four small spikes, one for each question that could sink the plan: can Rust reproduce Python's random numbers exactly, can it run the game's XRPL ledger features, can it speak without GPL code, and can it ship the same way? All four passed, and the voice spike found three licence traps on the way."
issue: 22
date: 2026-10-22
highlights:
  - "<strong>Python's random numbers, bit for bit.</strong> A 60-line Rust port of CPython's Mersenne Twister matched 2,645 recorded values over six seeds, including a 100-bit seed and a negative one. The values are identical under Python 3.11, 3.12 and 3.13."
  - "<strong>The ledger works from Rust.</strong> One run on the XRPL Testnet did everything the game's ledger feature needs (wallets, a trust line, token and XRP payments with memos, paging, an exact balance, and a deliberately expired transaction) in 35.7 seconds."
  - "<strong>Three licence traps in text-to-speech.</strong> Two popular Rust routes to the Kokoro voice model quietly bring GPL-3.0 code into the binary. A third route doesn't, and starts speaking in 1.9 seconds against 3.5 in Python."
  - "<strong>One build, four platforms.</strong> CI built Linux, macOS and Windows binaries and Python wheels from a Linux runner, with only the Mac builds needing Mac machines."
---

[Escape the Valley](https://github.com/mcp-tool-shop-org/escape-the-valley) is an Oregon-Trail-style survival game
played in the terminal. A deterministic engine decides what happens, so the same seed gives the same journey. A local
AI model narrates, and optionally the XRP Ledger's test network keeps a record of your supplies. It's about 17,700 lines
of Python with 1,042 tests.

An audit of version 1.3.0 found that the game had grown **two turn engines**, one for the full-screen interface and one
for the classic command line, and that features kept landing in one and not the other. The fix the studio chose is a
rewrite in Rust as version 2.0: one engine, two front ends, one self-contained binary.

A rewrite like that can fail in four ways that matter. So before writing the game, we asked four research agents one
question each, then ran a small spike for each question. A spike is a throwaway proof that answers one question with
evidence.

## 1. Can Rust reproduce Python's random numbers exactly?

This decides whether players keep their seeds and saved games. The game draws from Python's `random` module 66 times
across its code, using five operations: a float, an integer in a range, a choice, a shuffle and a sample, plus its own
weighted pick. Saved games store the generator's full internal state (624 numbers and a position).

Python's generator is the Mersenne Twister (MT19937). The spike ported it, and Python's exact way of turning its output
into each operation, to Rust in about 60 lines. A Python script recorded expected values for six seeds:
- 0, 1, 42, and 2³² + 7;
- a 100-bit integer, and a negative one. Python seeds from the absolute value.

For each seed it recorded 200 floats (as exact bit patterns), 200 ranged integers at ten widths, 50 choices, 20
shuffles, 20 samples (covering both of Python's internal methods), 50 weighted picks, and a save-and-restore round trip.

The Rust port matched **all 2,645 values**. A widely used Rust crate, `rand_mt`, matched too.

**One finding we hadn't expected:** the recorded values were byte-identical under Python **3.11, 3.12 and 3.13**. The
game supports all three, so this also confirms that today's Python version plays the same journey whichever of them
you run. Asking for a number in a range of one (say "between 4 and 4") still consumes randomness, and the port has to
copy that too.

The port will be proven the same way at full scale. The Python game becomes the reference: a thousand seeds, sixty
turns each, saved and resumed partway, with the whole game state compared turn by turn. This is differential testing
(McKeeman, 1998), with the old program as the oracle.

## 2. Can Rust run the game's ledger features?

The game's "Ledger Backpack" issues five supplies as tokens on the XRP Ledger's test network, settles them at towns
with transaction memos, sends parcels between players, and proves a run by reading the memos back. The research found
one maintained Rust library, `xrpl-rust` (version 1.3.0, ISC licence, now hosted under the XRPL Foundation's GitHub),
that claimed to cover all of it.

The spike tested that claim on the live test network:

| Step | Time |
|---|---|
| Two wallets from the faucet, each balance checked on a validated ledger | 11.9 s |
| A trust line for a supply token | 8.8 s |
| A token payment carrying a settlement memo | 6.7 s |
| A 12-drop XRP payment carrying a parcel memo | 5.6 s |
| Reading history back across three pages, memos decoded, and the token balance read as an exact decimal | 0.7 s |
| A transaction sent with an expiry ledger already passed, to prove the client reports it as lapsed | 2.0 s |

All of it passed, in 35.7 seconds. Two details the game's Rust code will need:
- the ledger server raises any history page size below 10 up to 10;
- just after an expired transaction, the server can briefly still answer "not validated" before it answers "not
  found". Both mean the transaction will never land.

## 3. Can it speak, without GPL code?

The game can read its narration aloud with Kokoro, an open text-to-speech model (Apache-2.0). A speech model needs a
**phonemizer**, which turns words into sounds. The usual one, espeak-ng, is licensed GPL-3.0. Linking it into the
game's binary would put the whole binary under the GPL, which the game's MIT licence can't allow.

The research suggested sherpa-onnx, a speech toolkit with a Kokoro mode that uses a word list instead of espeak-ng.
Checking the code changed that:
- **Trap 1:** the released sherpa-onnx (1.13.8) builds espeak-ng and piper-phonemize, both GPL, into every build that
  includes speech, whichever mode you use. We read this in its build files at that release. Only the unreleased next
  version removes them.
- **Trap 2:** the spike reported that another Rust Kokoro crate compiles espeak-derived C code even when its pure-Rust
  word list is switched on. We haven't confirmed this one at the source; the route below avoids the crate either way.
- **Trap 3:** sherpa-onnx's English word list was itself generated from espeak-ng's dictionary, so it inherits the
  question.

The route that passed drives the Kokoro model directly through ONNX Runtime, with these parts:

| Part | Licence |
|---|---|
| Kokoro's own pronunciation dictionaries (misaki) | Apache-2.0 |
| The CMU Pronouncing Dictionary as a fallback | BSD-style |
| rodio, for playback only | MIT or Apache-2.0 |

We checked each licence at its source. A symbol dump of the finished Windows binary shows no espeak or piper code.

Measured on the studio's machine:
- the binary is about 24 MB, because it carries ONNX Runtime;
- the model and dictionaries are a 353 MB download, made on first use;
- the first audio arrives **1.9 seconds** after start, against 3.5 seconds for today's Python voice.

Twenty game lines were rendered both ways for a blind listening test, which the studio is still to judge.

## 4. Can it ship the same way?

Today the game installs three ways: `pip`, `npx`, and a downloaded binary. The spike built a tiny Rust program in CI
and produced all of it:
- binaries for Linux, Windows and both kinds of Mac;
- a checksums file;
- Python wheels that install the binary through `pip`, the way the `ruff` and `uv` tools ship.

The Windows binary was built on a Linux machine and then run on Windows. Only the two Mac builds needed Mac machines,
which cost more to run. The build settings strip the build machine's paths out of the binaries.

## What happens next

The plan holds. The rewrite starts with the core engine, tested against the Python game at every turn, and adds the
command line, the full-screen interface, the narrator, the ledger and the voice in that order. Meanwhile, Python 1.3.1
fixes the bugs players hit today.

*Sources:*
- CPython 3.11 `Lib/random.py` and `Modules/_randommodule.c`;
- W. M. McKeeman, "Differential Testing for Software", *Digital Technical Journal* 10(1), 1998;
- `xrpl-rust` 1.3.0 ([XRPLF/xrpl-rust](https://github.com/XRPLF/xrpl-rust));
- sherpa-onnx v1.13.8 `CMakeLists.txt` ([k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx));
- [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) and [hexgrad/misaki](https://github.com/hexgrad/misaki);
- [cmusphinx/cmudict](https://github.com/cmusphinx/cmudict);
- the spike code: escape-the-valley PR #26.
