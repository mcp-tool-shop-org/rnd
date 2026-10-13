# Atlas slice AN: outside security verdicts, and R&D's rulings

**Brief:** [2026-10-13-an-security-brief.md](2026-10-13-an-security-brief.md), against testing-os #169 at `e46e42b4`.

**Run by the Director by hand, 2026-10-13, on two models from other families:**
- **Grok Build:** read the brief only.
- **Kimi K3:** read the brief plus the commit's other files, read-only. It also tested four Node and Windows behaviours on the rig.

**Ruled by:** the R&D seat, the same day. R&D's own code review (part 1, on the PR) came first, and the reviewers didn't see it.

## The verdicts, side by side

| # | Question | Grok | Kimi K3 | Settled by |
|---|---|---|---|---|
| 1 | Traversal and links | holds | holds | Both reviewers: access is exact real-path equality against a set fixed at start, not a prefix test. A link can only alias a root that's already allowed. |
| 2 | Network and device paths | fails (medium): a mapped drive letter isn't caught | holds, with the mapped drive open | **The rig.** Atlas mapped `Z:` to `\\localhost\C$` (approved by the Director, then removed). `realpathSync.native` returns the UNC form, so `isNetworkPath` refuses it as a `--repos` line, as `repo`, and as a client root. The JS `realpathSync` keeps `Z:`, so `.native` is load-bearing. Kimi tested that `win32.isAbsolute` covers every UNC and device spelling, and that a `subst` drive resolves to its local target. |
| 3 | Case | fails (low) | fails (low to medium) | Both found it. Kimi checked on the rig that `realpathSync.native` returns the true-case path. On a case-sensitive directory, `X\Repo` and `X\repo` share a lowercased key, so a `repo` naming one can answer for the other. |
| 4 | Time of check and time of use | fails (high) | holds under the model (low) | R&D's part-1 finding, already fixed and held (`fixRoots`). Kimi's severity is right under the threat model, since the attacker can't write the filesystem. The fix is cheap either way. Grok also found that tools run git in `repo.root`, the path as given, not `repo.real`. |
| 5 | Client roots inside a repository | fails (medium) | holds, with one advisory | Both found the git widening. **Only Kimi found the unbounded part:** `exportedRoot` climbs to *any* ancestor holding `atlas/structure.json`, so a stray `D:\atlas\structure.json` makes `D:\` a root. |
| 6 | Git as a code path | fails (medium) | holds for clones (low) | Both want `--no-textconv` and `--no-ext-diff`, and the textconv flag is already held. **Grok found a real hole:** `git()` passes `process.env` through, so `GIT_DIR` or `GIT_WORK_TREE` in the server's environment would choose the repository instead of the cwd. |
| 7 | Strings as data | fails (low) | holds, one hole (low) | Both found the raw URI in the log (R&D's part-1 finding, already fixed and held). Grok adds that `asName` doesn't quote Markdown link characters. |
| 8 | The `--repos` file | parsing holds; a symlinked file fails (low) | holds (nits) | Relative lines resolve against the link's directory, not the target's. A path that starts with `#` can't be written. |
| 9 | Anything else | `GIT_DIR` in the environment (medium); the silent cap on client roots | silent cap; `atlas_repos` git cost; the refresh fingerprint follows a committed symlink out of the root | Kimi's refresh finding reads bytes outside a root, though only into a SHA-256 and never into an answer. That still breaks must-hold 1 as written. |

## R&D's rulings

**Required in AN's one follow-up commit, before merge**, beside the four already held from part 1 (roots fixed once, the neutralised log line, `--no-textconv` on the blob `show` calls, the mapped drive recorded as checked by hand):
1. **Git runs in the root's stored real path,** never in the path as given (Grok 4).
2. **Strip git's location variables from the child environment:** `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR` and `GIT_NAMESPACE`. Only the cwd chooses the repository (Grok 6 and 9). Test: with `GIT_DIR` set to another repository in the server's environment, the answer still comes from the root.
3. **Compare by exact real path, and stop lowercasing.**
   - `realpathSync.native` already returns the true case on a case-insensitive directory (Kimi, on the rig), so legitimate input still matches.
   - A path that matches a root only when case is ignored is refused, never answered for another root.
   - The twin check uses exact keys too.
   - Test: with an injected `realpath`, or a real case-sensitive directory if the rig can make one.
4. **An exported tree's root must hold `atlas/structure.json` itself,** with no climb to an ancestor. That's the wording of the production spec's Part 1 item 4 ("a directory that holds `atlas/structure.json`"). A working directory inside an exported tree is refused, with a hint to start at the tree's top. The git widening to the working tree's top stays, as ruled in part 1: it's bounded by git and has always been Atlas's unit.
5. **A `--repos` file's relative lines resolve against the file's real directory** (Grok 8).
6. **Log the client roots dropped past 32** (Kimi 9a).
7. **The refresh fingerprint hashes a symlink's link text and never follows it** (Kimi 9c). git records a symlink as its target string anyway. Test, on Linux CI: a committed symlink to a file outside the root is never opened.
8. **Add `--no-ext-diff` to the `diff` call.** `--name-status` renders no content, so this is insurance.

**Not required, with the reason:**
- **A `GetDriveType` gate:** the rig showed that the mapped-drive case is already refused.
- **Markdown characters in `asName`** (Grok 7): tool text reaches the model as text, and quoting `[ ] ( )` changes every tool's wording, including Next.js route folders such as `[id]`. It's a later, separate PR if it's wanted.
- **`atlas_repos` git cost** (Kimi 9b): a performance note. Revisit if 32 roots ever runs slowly.
- **`--repos=file` syntax, and a path starting with `#`:** add a handbook note for the second.

**Merge:** after the follow-up commit carries all twelve items (the four held plus these eight), its clean verify and CI are green, and R&D passes it. No second outside run is needed: the fixes are the reviewers' own, and the tests pin them.
