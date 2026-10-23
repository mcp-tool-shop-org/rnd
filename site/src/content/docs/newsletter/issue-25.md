---
title: "What's really inside a packaged program"
description: "Two of the studio's Python tools ship as single-file programs you can run without installing Python. This issue opens those files up. It covers the scan that couldn't see inside them, the CI folder path that ended up in XRPL Camp 1.5.0, and the licence notices a bundled copy of Python owes the libraries built into it."
issue: 25
date: 2026-10-23
highlights:
  - "<strong>A scan that couldn't see in.</strong> The identity scan passed the packaged programs because they are compressed. Unpacked, the same files held 28 lines from third-party libraries. The scanner now unpacks them itself."
  - "<strong>A CI folder in the release.</strong> All three XRPL Camp 1.5.0 programs carry a small install record naming the GitHub runner's checkout folder. A second build-machine path turned up in Python's own settings file. 1.5.1 removes both, and the release gate now refuses any program that carries either."
  - "<strong>Notices for a bundled Python.</strong> A packaged program carries a copy of Python and the C libraries built into it, and their licences ask to travel with it. A hand-written summary is being replaced with the exact texts, copied from pinned sources."
  - "<strong>Caught in review.</strong> The first version of that fix broke `trail licenses` for anyone who installed with pip on a different Python. A review on Python 3.13 found it before release."
---

Escape the Valley and XRPL Camp are written in Python, but most players never install Python. Each release also
ships a single-file program for Windows, macOS and Linux, built with
[PyInstaller](https://pyinstaller.org/). PyInstaller packs the tool, every library it uses, and a copy of the Python
interpreter into one compressed file. The [npm launcher from issue 24](/rnd/newsletter/issue-24/) downloads that file, checks its
checksum and runs it.

What goes into that file is decided by the build, not by anyone reading it. This week the studio looked inside.

## The scan that couldn't see in

Before anything leaves the studio, an identity scan checks it for personal details: home-folder paths, email
addresses, account names. It had passed every packaged program so far.

During a live check on Escape the Valley 1.3.1, the Book Keeper asked whether the scan could see the game's own
copyright line, which is certainly inside. It couldn't: the line appeared **0** times in the raw file, because
PyInstaller compresses its contents. A clean result on a compressed file meant nothing.

Unpacked, the same program gave **28** hits. None was the studio's own:

| What | Count | Where it comes from |
|---|---|---|
| Build-machine folder paths | 21 | the prebuilt Python the build uses ([python-build-standalone](https://github.com/astral-sh/python-build-standalone)) |
| A Python docstring with an example path | 1 | Python's own code |
| Author and example email addresses | 6 | Python and three libraries: rich, pygments, httpx |

Two rules followed:
- **Unpack, then scan, with a positive control.** A string known to be inside, such as the game's copyright line,
  must be found, or the scan is reported as blind. The scanner now unpacks PyInstaller programs, wheels and zips
  itself.
- **Third-party lines need a written exception per release.** Library authors' email lines and the builder's paths
  aren't the studio's to edit. Each release that carries them gets an explicit, named exception, and anything
  outside that pulls the release files.

## The CI folder in XRPL Camp 1.5.0

XRPL Camp 1.5.0 shipped on 2026-10-22, with a lesson that mints and burns an NFT so a learner can watch the
ledger's owner reserve lock and release, a plain-text keepsake certificate, and dated verification receipts in proof
packs. Its release files then went through the new unpacked scan:

| Program | Hits |
|---|---|
| macOS (arm64) | 51 |
| Linux (x64) | 8 |
| Windows (x64) | 27 |

All but one were the third-party kinds above. The exception was inside XRPL Camp's own package: a file called
`direct_url.json`. Python's installer writes it to record where a package was installed from
([PEP 610](https://peps.python.org/pep-0610/)). Here it named the folder where GitHub's macOS build machine had checked out the code, under that
machine's `runner` account, and marked the install as *editable*, linked to that folder.

The scanner had flagged only macOS. Opening the Linux and Windows programs by hand showed the same file in both,
naming the Linux and Windows build machines' checkout folders. Neither of those folder forms was in the scanner's
list.

- **What it is:** a CI machine's folder, not a person's. No one's data was exposed.
- **Why it happened:** the build ran PyInstaller through `uv run`, which quietly reinstalled the package in editable
  mode just before packing it.
- **What was decided:** keep the 1.5.0 files, and fix it in 1.5.1.
- **The fix in 1.5.1:** the build skips that reinstall, deletes the install record before packing, and then lists the
  finished program's contents and fails if the record is there. Run against the real 1.5.0 Linux program, that check
  fails and names the file, so it isn't a check that can only pass.
- **The scanner now treats any bundled `direct_url.json` as a hit,** whatever path it holds.

## Notices for a bundled copy of Python

Open-source licences mostly ask for one thing in return: keep the copyright notice and licence text with the
software. A packaged program redistributes everything inside it, so its notices file has to cover all of it. That's
Python itself, and the C libraries compiled into Python: OpenSSL, zlib, bzip2, libffi, SQLite and others.

Escape the Valley 1.3.1 adds a `trail licenses` command and a notices file attached to each release. Getting
the Python part right took four rounds:

1. **The first version** copied Python's own licence file from the build machine. For the Python that ships
   (3.12.13), the Windows copy runs to 502 lines and includes notices for some of the bundled libraries. The Linux
   copy runs to 279 lines and **mentions none of them**.
2. **The second version** filled that gap with a summary written for the occasion. Review found it was not the text
   it claimed to be: it cut the bzip2 and mpdecimal licences short, gave OpenSSL a web link instead of the licence,
   and missed code compiled into Python itself, such as the Mersenne Twister random generator.
3. **The third version** copies the exact texts from pinned sources:
   - Python's own list of incorporated software, `Doc/license.rst` at the exact Python version shipped (3.12.13);
   - the licence files from python-build-standalone's **full** archive for the same build and each of the three
     platforms. Every archive was checked against the project's published SHA-256 list.

   Each file in the game records its source and SHA-256 hash, and a test checks those hashes on every commit. The
   build refuses to make notices if the Python it's packing isn't the one the texts were copied for.
4. **The fourth version** fixed what review found in the third.

**What review caught in the third.**
- **pip installs broke.** The version check also ran when someone installed the game with pip. On any Python other
  than exactly 3.12.13, `trail licenses` crashed. The tests had replaced the Python version with a matching one, so
  they never ran the failing path. Running the command on Python 3.13 found it.
- **An exclusion that wasn't done.** The notes said the Tk graphics libraries were left out of the program. Nothing in
  the build left them out.

In the fourth version:
- `trail licenses` on a pip install shows the game's own licence and its libraries, with a note that the Python texts
  belong to the packaged programs.
- Tk and dbm are excluded in the build, and the notices check fails if either turns up.
- All 19 licence files in each archive are accounted for.
- The same install-record cleanup as XRPL Camp's is in.

**Listing what's really bundled.** The notices list is now checked against PyInstaller's own record of what it packed:
- On a Linux build, the check found **22** libraries and passed. With one name deleted from a copy of the notices, it
  failed and named the missing library.
- The same build showed the notices listing three libraries that were installed but never packed (Deprecated,
  mdit-py-plugins and wrapt). The list is now trimmed to what the program actually contains.

## A second path, in Python's own settings

The Linux build checks for both tools then found one more build-machine path, and this one wasn't in an install
record. Python keeps a small settings module, `_sysconfigdata`, that records where the interpreter itself is
installed. About 20 of its entries, such as the install prefix and the folder for programs, hold that location, and
PyInstaller packs the module like any other.

The build tool, uv, installs Python under the build machine's user account. So on GitHub's Linux machines those
entries name a folder under the `runner` account's home, and XRPL Camp 1.5.0's Linux program carries them alongside
its install record. Like the install record, it's a CI machine's folder, not a person's.

The ruling was the same as for the install record: it's the studio's own build setup, so it gets fixed, not excused.
- **The build** installs Python into a neutral folder outside any user's home.
- **The bundle check** reads `_sysconfigdata` from inside the finished program, and fails if it names a home folder.
- **The 1.5.0 programs stay as released,** and their receipts record both paths.

## Where things stand

- **XRPL Camp 1.5.0:** released and live-checked through npm on Windows and Linux. Its programs carry both
  build-machine paths described above.
- **XRPL Camp 1.5.1:** passed the studio's own review, the independent review, and a Linux build check. That check
  found the `_sysconfigdata` path, and the fix for it is being built. It then goes through review and the build check
  again.
- **Escape the Valley 1.3.1:** the fourth version of its notices passed the studio's code review, the independent
  review, and a Linux build check. The Linux check confirmed the notices file block by block against its sources. It
  takes the same `_sysconfigdata` fix as XRPL Camp before it ships with its full release checklist.
- **macOS:** neither program's macOS build can run on the studio's machines. So macOS, including what its
  `_sysconfigdata` holds, is first checked unpacked at release, and the receipts say so.

*Records:*
- XRPL Camp 1.5.0 ([release](https://github.com/mcp-tool-shop-org/xrpl-camp/releases/tag/v1.5.0)), its treatment
  (#22) and live-check receipts (#24);
- the install-record fix, [xrpl-camp#23](https://github.com/mcp-tool-shop-org/xrpl-camp/issues/23) and pull request #25;
- Escape the Valley 1.3.1, [pull request #25](https://github.com/mcp-tool-shop-org/escape-the-valley/pull/25), and
  the notices issue, [#28](https://github.com/mcp-tool-shop-org/escape-the-valley/issues/28).
