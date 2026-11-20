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
  `instruments/`, `catalogs/`, `experiments/`), the generated index `rnd.db` and its
  sibling local miss log `rnd.misses.jsonl`. The readouts knowledge bases are opened
  read-only. `rnd sql` uses a read-only connection, and `rnd similar` and
  `rnd digest` are read-only (never modifying the working tree, git index or
  `rnd.db`).
- **Network:** none, except `rnd catalog sync`, `rnd probe` and `rnd watch`, which
  read public metadata or call the GitHub API through the user's own `gh` CLI login
  when run.
- **No secrets handling:** it does not read, store or transmit credentials.
- **Local-only usage log:** nothing is collected or sent anywhere. When `rnd search`
  returns no matches, it appends one line (UTC time and query) to `rnd.misses.jsonl`
  beside `rnd.db` (git-ignored in the repo, or `<db>.misses.jsonl` beside `--db` /
  `$RND_DB`). Set `RND_NO_USAGE=1` to turn it off, and delete the `.misses.jsonl` file
  at any time to clear it. No other usage data is recorded.

Also in scope: content in this public repo that should not be public, such as a
home-directory path, a credential, or text we have no right to publish. Report it
the same way.
