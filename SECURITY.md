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

- **Data touched:** files inside this repo (`entries/`, `instruments/`, `catalogs/`,
  `experiments/`) and the generated index `rnd.db`. The readouts knowledge bases are
  opened read-only. `rnd sql` uses a read-only connection.
- **Network:** none, except `rnd catalog sync`, which calls the GitHub API through
  the user's own `gh` CLI login when run.
- **No secrets handling:** it does not read, store or transmit credentials.
- **No telemetry** is collected or sent.

Also in scope: content in this public repo that should not be public, such as a
home-directory path, a credential, or text we have no right to publish. Report it
the same way.
