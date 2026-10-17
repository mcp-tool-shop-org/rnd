# Dataset releases with verifiable provenance: design note (draft)

**Status:** draft for the maintainer, 2026-10-16. Nothing is built. **Aim:** every studio dataset release can be
verified by anyone. Each row traces to its writer and licence; the files are exactly what the studio released; and
the maintainer approved the release himself.

## The mechanism: npm-launcher, as the studio already uses it

`@mcptoolshop/npm-launcher` already does most of this for binaries:
- it downloads assets from a GitHub Release;
- it checks each one against `checksums-<version>.txt` from the same release;
- it caches them;
- its `release.yml` publishes to npm through OIDC trusted publishing (`npm publish --provenance`, no token). That
  gives a Sigstore-signed provenance statement, in a public log, tying the package to the repo, the commit and the
  workflow.

A dataset release reuses all of it.

## The release

1. **The data repo's GitHub Release** carries the data files plus `checksums-<version>.txt`, and a `manifest.json`
   with:
   - every file's sha256 and row count;
   - the recipe card;
   - for each writer and critic: its `licences/registry.json` id, model revision and GGUF sha256;
   - the role-set and gates versions, and the plan seeds;
   - the exclusion-state sha256.
2. **A thin npm package** under the dataset org (for example `@<dataset-org>/stage1-data`) pins that release's version and tag, plus the
   manifest's sha256. It's published by the repo's `release.yml` with `--provenance`, bound as a trusted publisher
   to that workflow file.
3. **The maintainer's approval is the human step.** `release.yml`'s publish job runs in a protected GitHub
   environment (`dataset-release`) with the maintainer as its required reviewer.
   - GitHub records his approval: who and when.
   - No seat can approve it.
   - The workflow writes the approval's run id into the release notes.

## The npm org and a new dataset's first publish

- **A dedicated npm org for datasets** (the maintainer creates it; name to be decided) holds every dataset package,
  apart from the `@mcptoolshop` tools.
- **Each new dataset package follows the studio's placeholder bootstrap** (memory: npm-placeholder-bootstrap):
  1. The maintainer publishes a `0.0.0` placeholder under the org, to create the name. npm needs the package to
     exist before a trusted publisher can be set. A placeholder only reserves the name; the first real release
     ships the data package.
  2. He configures the trusted publisher on npmjs.com: the data repo, `release.yml`, **and the environment
     `dataset-release`.** Because the publish job declares that environment, GitHub's OIDC subject includes it, and
     npm's trusted publisher must name the same one.
  3. From then on, a tag fires `release.yml`. It waits for his approval, then publishes with `--provenance`.
- **Never read a fresh registry 404 as "unpublished".** The registry lags a publish by a few minutes; check
  `npm view <pkg> time --json`.

## What npm-launcher needs

**A fetch mode:**
- download and verify the assets into the cache, or into a directory named by the user;
- **never execute them;**
- verify the manifest against the sha256 pinned in the package, then each file against the manifest.

For example: `npx @mcptoolshop/stage1-data fetch <dir>`.

It's a small addition beside `ensureBinary`, with tests. It's a minor version, because the binary path is unchanged.

## How anyone verifies

- `npm audit signatures` (or the npm page's provenance panel): the package came from the data repo's
  `release.yml` at the release commit.
- `fetch` checks every file against the manifest the package pins.
- The manifest names each writer's registry id, so the licence for every row can be looked up in rnd.
- The release notes link the approval run.

## Rules this has to meet

- **GitHub Actions rules:**
  - `release.yml` fires on a tag or release only, so it doesn't count against the two-workflow cap;
  - it carries the concurrency block and `ubuntu-latest`;
  - it carries `workflow_dispatch`.
- **NAMED_COMPENSATORS:**
  - **npm publish:** `npm deprecate` (unpublish only within npm's window, before anything depends on it).
  - **The GitHub Release:** mark it superseded, and keep the tag so provenance still verifies.
  - Both are owned by the maintainer.
- **The licence registry** gets an entry for the data repo's own licence once one is chosen.

## Open for the maintainer

- The dataset org's name (he creates it on npm).
- Which repo holds the data, and whether it's public.
- Whether the release also goes to Hugging Face, with its dataset card linking the npm provenance.
- The data's licence, for anyone outside the studio.
