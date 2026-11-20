# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

Email: **64996768+mcp-tool-shop@users.noreply.github.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Version affected (`python -m rnd --version`)
- Potential impact

### Response timeline

| Action | Target |
|--------|--------|
| Acknowledge report | 48 hours |
| Assess severity | 7 days |
| Release fix | 30 days |

## Scope

`rnd` runs **locally only**.

- **Data touched:** files inside this repo (`entries/`, `questions/`, `changes/`,
  `instruments/`, `catalogs/`, `experiments/`, `datapacks/`, `docs/layout.json`),
  the generated index `rnd.db` (or `--db` / `$RND_DB`) and its sibling local miss
  log `rnd.misses.jsonl`. Outside this repo, `rnd watch` writes its persistent
  state file to `--state`, `$RND_WATCH_STATE` or
  `Path.home() / ".rnd" / "watch-state.json"` (`~/.rnd/watch-state.json`), where
  it stays across runs unless `--no-save` is passed, and `rnd raw` (`ingest`,
  `private`, `relicense`) writes to the companion stores `--public` / `$RND_DATA`
  (`../rnd-data`) and `--private` / `$RND_DATA_PRIVATE` (`../rnd-data-private`).
  The readouts knowledge bases and `rnd collect` source clones are opened or
  read read-only. `rnd sql` uses a read-only connection, and `rnd similar` and
  `rnd digest` parse in memory and write nothing anywhere (no temporary files,
  working-tree edits, git index changes or `rnd.db` writes).
- **Network:** none, except `rnd catalog sync`, `rnd probe` and `rnd watch`, which
  read public metadata or call the GitHub API through the user's own `gh` CLI login
  when run.
- **No secrets handling:** it does not read, store or transmit credentials.
- **Local-only usage log:** nothing is collected or sent anywhere. When `rnd search`
  returns no matches, it appends one line (UTC time and query) to `rnd.misses.jsonl`
  beside `rnd.db` (git-ignored in the repo; with `--db foo.db`, `foo.misses.jsonl`
  beside it, not `foo.db.misses.jsonl`, and likewise for `$RND_DB`). Set
  `RND_NO_USAGE=1` to turn it off, and delete the `.misses.jsonl` file
  at any time to clear it. No other usage data is recorded.

Also in scope: content in this public repo that should not be public, such as a
home-directory path, a credential, or text we have no right to publish. Report it
the same way.
