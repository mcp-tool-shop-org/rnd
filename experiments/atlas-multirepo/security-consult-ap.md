# CONSULT | security review, different family, run by hand | testing-os #179, Atlas slice AP | from R&D | 2026-10-15

**For:** the Director runs this by hand on Grok or Gemini (Standing Rule 1: no cloud verifier seat). It is the "targeted security review before merge" that `docs/atlas-buildup.spec.md` requires for the first slice in which Atlas acts on another repository's data.

**Head under review:** `4904cf90` on dogfood-lab/testing-os#179. R&D has read every line below and found no defect in it. The review is meant to find what R&D missed. Answer only from the code shown here.

## What AP does, and who controls what

Atlas is a local, offline MCP server. It answers questions about a set of local git checkouts (the *roots*) that the operator configures at start. AP adds one answer to `atlas_reach`: for a file in one root (the *producer*), which other roots (*consumers*) declare an npm package that the producer publishes and that contains the file. For each link it gives the declared range, the resolved version, and whether the producer's map stands at the commit tagged for that version.

**Assume an attacker controls the full contents of any one root, consumer or producer.** That covers its `package.json` files, its lockfiles (`package-lock.json`, `pnpm-lock.yaml`), its `atlas/boundaries.yaml` (including the new `producers:` key), its committed `atlas/structure.json`, its git tags and branch names, and its `.git/config`. The attacker does **not** control the operator's other roots, the operator's global git config, the environment, or the Atlas binary.

Values that reach git or the model from attacker-controlled data:
- a version string from a consumer's lockfile, which goes into a tag name;
- a package name from a producer's manifest, which goes into a tag name;
- a repository name from a consumer's `producers:` entry, which is matched against the roots;
- the producer's `remote.origin.url`, which is read and compared, never printed;
- every name, range and version that the answer's sentences quote to the model.

## Questions

1. **Argument injection.** Can any attacker-controlled value make `git` read an option, run a command other than the allow-listed read commands, or run a program (hooks, fsmonitor, textconv, external diff, credential helpers, `core.sshCommand`, `protocol.*`, `uploadpack.*`)? Check `git.js` together with the repository's own `.git/config`. The sidecar sets `-c core.fsmonitor=false` and strips the location variables. Is anything else in a repository-local config still reachable through the commands used here (`rev-parse`, `check-ref-format`, `config --get`, `show`, `merge-base`, `cat-file`)?
2. **The tag lookup** (`tags.js`): can a lockfile version or a manifest name that passes `mayBeGivenToGit`, `VERSION` and `isValidPackageName` produce a ref that resolves to something other than the intended tag? Consider a branch named like a tag, `@{...}` reflog syntax, `^`, `~`, `:`, `..`, and names with non-ASCII lookalikes.
3. **Network.** Can any path here make git reach the network (lazy fetch in a partial clone, `remote.origin.url` with a helper, a submodule)? `GIT_NO_LAZY_FETCH=1` and `GIT_TERMINAL_PROMPT=0` are set.
4. **Text the model reads.** Can a name, range or version from the data make a sentence that reads as Atlas's own words, or inject instructions? Check `asName`'s rule ("quote when it has a space, quote, backslash or control character, or is over 200 characters"). Are there characters that rule misses, such as bidi marks or lookalike punctuation, that would let a name pass unquoted yet read as prose?
5. **The `producers:` key.** Can a consumer use it to make a false link appear (basis `manual`) to a producer it doesn't use, or suppress a true one? Is that within what "manual, declared by the consumer" should mean, or a problem?
6. **Resource use.** Can attacker data make an answer hang, or use unbounded memory or git calls? Consider many packages, many tags, huge lockfiles and deep directory nesting.
7. **Anything else** in the code below that a careful attacker could use.

**Reply** with one entry per question: a finding with its line and a concrete attack, or "no finding". Mark each finding **measured** (you traced it in the code shown) or **inferred** (it depends on git behaviour you are recalling).

## The code

### `packages/atlas/sidecar/git.js` (complete)

```js
import { spawnSync } from 'node:child_process';

/**
 * The only way the sidecar runs git. It reads and never writes: each call is
 * one of the read commands below, with GIT_OPTIONAL_LOCKS=0 so a status or a
 * diff does not refresh .git/index behind the caller's back (the fleet
 * service learned that on a mounted checkout), and with the filesystem
 * monitor off so no daemon is started and no cookie file is written under
 * .git. In a partial clone git would fetch a missing object from the remote
 * to answer a read; GIT_NO_LAZY_FETCH stops that, since the sidecar never
 * uses the network. A command outside the list throws: a write here is a
 * defect, not an option.
 */

const READ_COMMANDS = new Set(['cat-file', 'check-ref-format', 'config', 'diff', 'ls-files', 'ls-tree', 'merge-base', 'rev-list', 'rev-parse', 'show', 'status']);

// config reads only: with --get or --get-all it prints a value and writes nothing.
function readsOnly(args) {
  return args[0] !== 'config' || args[1] === '--get' || args[1] === '--get-all';
}

/**
 * A ref git reads: a commit, a branch, a tag, HEAD~3, origin/main; never an
 * option. Every ref an asker passes is held to it before git sees it.
 */
export const REF_PATTERN = '^[A-Za-z0-9._/~^@{}][A-Za-z0-9._/~^@{}-]*$';
const REF = new RegExp(REF_PATTERN);

/** Whether text has the shape of a ref git may be given. */
export function isRefShaped(text) {
  return typeof text === 'string' && text.length > 0 && text.length <= 200 && REF.test(text);
}

// A map is a few megabytes on a large repository, and git show returns it whole.
const MAX_BUFFER = 64 * 1024 * 1024;

export const READ_ONLY_ENV = Object.freeze({ GIT_NO_LAZY_FETCH: '1', GIT_OPTIONAL_LOCKS: '0', GIT_TERMINAL_PROMPT: '0' });

/**
 * The variables that tell git which repository to use instead of the
 * directory it runs in. The sidecar chooses a repository by its directory
 * alone (docs/atlas-buildup.spec.md, slice AN), so none of them reaches a
 * git it starts: a GIT_DIR in the environment the host started the server
 * with would answer every question from another repository.
 */
export const LOCATION_VARIABLES = Object.freeze(['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY',
  'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_COMMON_DIR', 'GIT_NAMESPACE']);

/** An environment without git's location variables, however Windows spells their case. */
export function withoutGitLocation(env) {
  const out = { ...env };
  for (const key of Object.keys(out)) if (LOCATION_VARIABLES.includes(key.toUpperCase())) delete out[key];
  return out;
}

// show and diff never run a program a repository's attributes name: no
// textconv filter and no external diff. A clone carries no driver, but a
// tree copied with its .git, or one the user's own configuration names, can.
const NO_DRIVERS = Object.freeze({ show: ['--no-textconv', '--no-ext-diff'], diff: ['--no-textconv', '--no-ext-diff'] });

/**
 * @param {string} cwd
 * @param {string[]} args the subcommand first
 * @param {{ encoding?: 'utf8' | 'buffer', input?: string }} [options]
 * @returns {{ ok: boolean, status: number|null, stdout: string|Buffer, stderr: string }}
 */
export function git(cwd, args, { encoding = 'utf8', input } = {}) {
  if (!READ_COMMANDS.has(args[0]) || !readsOnly(args)) throw new Error(`atlas sidecar: git ${args.slice(0, 2).join(' ')} is not a read command`);
  const result = spawnSync('git', ['-c', 'core.fsmonitor=false', args[0], ...(NO_DRIVERS[args[0]] ?? []), ...args.slice(1)], {
    cwd,
    encoding: encoding === 'buffer' ? 'buffer' : 'utf8',
    env: { ...withoutGitLocation(process.env), ...READ_ONLY_ENV },
    maxBuffer: MAX_BUFFER,
    windowsHide: true,
    // As bytes: spawnSync would read a string through the output encoding.
    ...(input == null ? {} : { input: Buffer.from(input, 'utf8') }),
  });
  const stderr = Buffer.isBuffer(result.stderr) ? result.stderr.toString('utf8') : String(result.stderr ?? '');
  return { ok: result.status === 0, status: result.status, stdout: result.stdout ?? '', stderr };
}

/** The top of the working tree that holds dir, or null when dir is in none. */
export function topLevel(dir) {
  let result;
  try {
    result = git(dir, ['rev-parse', '--show-toplevel']);
  } catch {
    return null;
  }
  return result.ok ? String(result.stdout).trim() : null;
}

/** The commit HEAD names, or null in a repository with no commit yet. */
export function head(root) {
  const result = git(root, ['rev-parse', '--verify', '--quiet', 'HEAD^{commit}']);
  return result.ok ? String(result.stdout).trim() : null;
}

/**
 * Whether commit is tip or an ancestor of it: by default HEAD, this
 * checkout's history; or the commit a ref names.
 */
export function inHistory(root, commit, tip = 'HEAD') {
  if (!/^[0-9a-f]{40}$/.test(String(commit))) return false;
  if (!git(root, ['cat-file', '-e', `${commit}^{commit}`]).ok) return false;
  return git(root, ['merge-base', '--is-ancestor', commit, tip]).ok;
}

/** The commit a ref names in this clone, or null when it names none. */
export function commitOf(root, ref) {
  if (!isRefShaped(ref)) return null;
  const result = git(root, ['rev-parse', '--verify', '--quiet', '--end-of-options', `${ref}^{commit}`]);
  return result.ok ? String(result.stdout).trim() : null;
}

/**
 * How far a commit is from this checkout's HEAD: the commits it holds that
 * the checkout does not (ahead) and those the checkout holds that it does
 * not (behind). Null when either side cannot be counted.
 *
 * @returns {{ ahead: number, behind: number } | null}
 */
export function distanceFromHead(root, commit) {
  const result = git(root, ['rev-list', '--left-right', '--count', `HEAD...${commit}`]);
  if (!result.ok) return null;
  const [behind, ahead] = String(result.stdout).trim().split(/\s+/).map(Number);
  return Number.isInteger(ahead) && Number.isInteger(behind) ? { ahead, behind } : null;
}

/**
 * The fetched upstream of this checkout, as this clone already holds it: the
 * current branch's upstream (@{u}), else the remote's default (origin/HEAD),
 * else none. Nothing is fetched, so it is as fresh as the last fetch.
 *
 * @returns {{ name: string, commit: string } | null}
 */
export function upstreamOf(root) {
  return upstreamsOf(root)[0] ?? null;
}

/** Each fetched upstream in that order, @{u} then origin/HEAD, the same ref once. */
export function upstreamsOf(root) {
  const out = [];
  for (const spec of ['@{u}', 'origin/HEAD']) {
    const named = git(root, ['rev-parse', '--abbrev-ref', '--symbolic-full-name', spec]);
    const name = named.ok ? String(named.stdout).trim() : '';
    if (!name || !isRefShaped(name) || out.some((entry) => entry.name === name)) continue;
    const commit = commitOf(root, name);
    if (commit) out.push({ name, commit });
  }
  return out;
}

/** The id git keeps a file under at a commit or ref, or null when it holds none there. */
export function blobAt(root, rev, path) {
  const result = git(root, ['rev-parse', '--verify', '--quiet', '--end-of-options', `${rev}:${path}`]);
  return result.ok ? String(result.stdout).trim() : null;
}

/**
 * The regular files a commit holds, as `git ls-files` lists a checkout's:
 * symlinks and submodules left out.
 *
 * @returns {string[] | null} null when git cannot list the commit
 */
export function trackedAt(root, commit) {
  const result = git(root, ['ls-tree', '-r', '-z', '--full-tree', commit]);
  if (!result.ok) return null;
  const out = [];
  for (const entry of String(result.stdout).split('\0')) {
    const tab = entry.indexOf('\t');
    if (tab === -1) continue;
    const [mode, type] = entry.slice(0, tab).split(' ');
    if (type === 'blob' && mode !== '120000') out.push(entry.slice(tab + 1));
  }
  return out;
}

/**
 * The bytes of files at a commit, read in one git process: a map from each
 * path to its content, a path the commit does not hold left out.
 *
 * @param {string} root
 * @param {string} commit
 * @param {string[]} paths
 * @returns {Map<string, Buffer>}
 */
export function filesAt(root, commit, paths) {
  const out = new Map();
  if (paths.length === 0) return out;
  const result = git(root, ['cat-file', '--batch'], { encoding: 'buffer', input: paths.map((path) => `${commit}:${path}`).join('\n') + '\n' });
  if (!result.ok) return out;
  const bytes = result.stdout;
  let at = 0;
  for (const path of paths) {
    const end = bytes.indexOf(0x0a, at);
    if (end === -1) break;
    const header = bytes.subarray(at, end).toString('utf8');
    at = end + 1;
    // "<object> <type> <size>" then the content and a newline; "<name>
    // missing" alone when the commit holds no such path.
    const match = /^[0-9a-f]+ (\w+) (\d+)$/.exec(header);
    if (!match) continue;
    const size = Number(match[2]);
    if (match[1] === 'blob') out.set(path, bytes.subarray(at, at + size));
    at += size + 1;
  }
  return out;
}

/** Whether the clone holds only part of its history (a shallow clone). */
export function isShallow(root) {
  const result = git(root, ['rev-parse', '--is-shallow-repository']);
  return result.ok && String(result.stdout).trim() === 'true';
}
```

### `packages/atlas/sidecar/tags.js` (complete)

```js
import { isValidPackageName } from '../core/package-facts.js';
import { git, isShallow } from './git.js';

/**
 * Which commit a package version was published from, as far as this clone's
 * own tags say (docs/atlas-buildup.spec.md, slice AP). The version is read
 * from a consumer's lockfile and the name from the producer's manifest, both
 * data from a repository the asker does not control, so each is held to a
 * strict shape before git sees it, a value that begins with "-" is refused
 * before git is started, the tag is named in full as refs/tags/<name> (a
 * branch of the same name cannot stand in for it) and checked with
 * `git check-ref-format`, and the ref is passed after --end-of-options.
 *
 * Only local tags are read. A shallow clone, or one whose tags were never
 * fetched, finds none, and the answer is unknown, never a match.
 */

// A release version: major.minor.patch, with a pre-release and build
// metadata when it has them. A lockfile can hold anything else (a range, a
// URL, a path), and none of those names a tag.
const VERSION = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?(?:\+[0-9A-Za-z][0-9A-Za-z.-]*)?$/;
const MAX_VALUE = 214;

/** The tag forms tried, in this order; the answer names them. */
export const TAG_FORM_NAMES = Object.freeze(['v<version>', '<version>', '<name>@<version>', '<name>-v<version>']);

/**
 * Whether a value read from another repository may be put into a git
 * command's arguments: non-empty, not long, no control character or space,
 * and never beginning with "-".
 */
export function mayBeGivenToGit(value) {
  return typeof value === 'string'
    && value.length > 0
    && value.length <= MAX_VALUE
    && !value.startsWith('-')
    // eslint-disable-next-line no-control-regex
    && !/[\u0000- \u007f]/.test(value);
}

/**
 * The tags to try for a name at a version, in order, each with its form
 * name; the name forms are left out when the name is no package name this
 * code will give git.
 *
 * @returns {{ forms: Array<{ form: string, tag: string }>, left: string[] }}
 */
export function tagsFor(name, version) {
  const forms = [{ form: TAG_FORM_NAMES[0], tag: `v${version}` }, { form: TAG_FORM_NAMES[1], tag: version }];
  const left = [];
  if (mayBeGivenToGit(name) && isValidPackageName(name)) {
    forms.push({ form: TAG_FORM_NAMES[2], tag: `${name}@${version}` }, { form: TAG_FORM_NAMES[3], tag: `${name}-v${version}` });
  } else {
    left.push(TAG_FORM_NAMES[2], TAG_FORM_NAMES[3]);
  }
  return { forms, left };
}

/**
 * The commit a version of a package was tagged at in this clone.
 *
 * @param {string} root the producer's checkout
 * @param {string} name the package, as its manifest names it
 * @param {string|null} version the version a consumer resolved, or null
 * @returns {{ state: 'found'|'none'|'unknown', tried: string[], tag?: string, form?: string, commit?: string, reason?: string }}
 */
export function publishedAt(root, name, version) {
  if (typeof version !== 'string' || version === '') return { state: 'unknown', tried: [], reason: 'the consumer\'s lock names no resolved version' };
  if (!mayBeGivenToGit(version) || !VERSION.test(version)) {
    return { state: 'unknown', tried: [], reason: 'the resolved version is not a release version a tag can name' };
  }
  const { forms, left } = tagsFor(name, version);
  const tried = [];
  for (const { form, tag } of forms) {
    tried.push(form);
    const ref = `refs/tags/${tag}`;
    // The tag is a ref git may name; anything else is skipped, not passed on.
    if (!git(root, ['check-ref-format', ref]).ok) continue;
    const found = git(root, ['rev-parse', '--verify', '--quiet', '--end-of-options', `${ref}^{commit}`]);
    if (found.ok) return { state: 'found', tried, tag, form, commit: String(found.stdout).trim(), ...(left.length > 0 ? { left } : {}) };
  }
  const shallow = isShallow(root);
  return {
    state: shallow ? 'unknown' : 'none',
    tried,
    ...(left.length > 0 ? { left } : {}),
    reason: shallow ? 'this clone is shallow, so its tags may be missing' : `no local tag for ${version}`,
  };
}
```

### `packages/atlas/adapter/diff.js`, the ref read (lines 1-45)

```js
import { spawnSync } from 'node:child_process';
import { compareStructures } from './changes.js';

/**
 * The structural delta between the map committed at a base ref and a fresh
 * map of the working tree: the page's "What changed since …" section, pointed
 * at the base of a pull request instead of at HEAD.
 *
 * Nothing here writes. The base side is read with `git show`, so a base ref
 * that exists only as a fetched remote-tracking branch is enough; the working
 * side is derived in memory by the caller.
 */

export const DIFF_HEADING = '## Atlas: what this change does to the map';

const STRUCTURE = 'atlas/structure.json';

function git(repo, args) {
  return spawnSync('git', args, { cwd: repo, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
}

/**
 * @param {string} repo
 * @param {string} ref
 * @returns {{ ok: true, commit: string, structure: object } | { ok: false, details: string[] }}
 */
export function readBaseMap(repo, ref) {
  // A ref may come from another repository's data (a lockfile, a tag): a value that begins with - is never a revision, and --end-of-options keeps git from reading it as one.
  if (typeof ref !== 'string' || ref.startsWith('-')) return { ok: false, details: [`${String(ref).slice(0, 80)} is not a revision`] };
  const resolved = git(repo, ['rev-parse', '--verify', '--quiet', '--end-of-options', `${ref}^{commit}`]);
  if (resolved.status !== 0) return { ok: false, details: [`${ref} is not a commit in this clone`] };
  const commit = resolved.stdout.trim();
  const shown = git(repo, ['show', '--no-textconv', `${commit}:${STRUCTURE}`]);
  if (shown.status !== 0) {
    return { ok: false, details: [`${ref} (${commit.slice(0, 7)}) has no ${STRUCTURE}`] };
  }
  try {
    return { ok: true, commit, structure: JSON.parse(shown.stdout) };
  } catch {
    return { ok: false, details: [`${STRUCTURE} at ${ref} (${commit.slice(0, 7)}) is not valid JSON`] };
  }
}

/**
 * @param {{ ref: string, commit: string, structure: object }} base
```

### `packages/atlas/adapter/boundary-file.js`, the `producers:` validation

```js
function producersProblem(producers) {
  if (producers == null) return null;
  if (!Array.isArray(producers)) return 'producers must be an array';
  const seen = new Set();
  for (let i = 0; i < producers.length; i += 1) {
    const entry = producers[i];
    const where = `producers[${i}]`;
    if (entry == null || typeof entry !== 'object' || Array.isArray(entry)) return `${where} must be a mapping`;
    for (const key of Object.keys(entry)) if (!PRODUCER_FIELDS.has(key)) return `${where}.${key} is not a producer field`;
    if (typeof entry.package !== 'string' || !isValidPackageName(entry.package)) return `${where}.package must be an npm package name`;
    if (typeof entry.repository !== 'string' || entry.repository.trim() === '' || entry.repository.length > 1024) return `${where}.repository must be the name of a repository Atlas answers for`;
    if (seen.has(entry.package)) return `${where}.package duplicates ${entry.package}`;
    seen.add(entry.package);
  }
  return null;
}
```

### `packages/atlas/sidecar/data.js`, the untrusted-text rules (lines 1-75)

```js
/**
 * Repository text is data (docs/atlas-sidecar.spec.md, "Safety"). Every
 * string an answer's structured content carries is capped in length. In the
 * text a model reads, a name taken from the repository cannot pass for
 * Atlas's own words: a name that could read as words of its own (one with a
 * space, a quote, a backslash or a control character) is quoted as a JSON
 * string wherever the text names it, and control, format and line-break
 * characters show as escapes, so no repository text starts a line of its
 * own or hides in one. A line break
 * left once the names are quoted is Atlas's own (the order of work explain
 * lists one step to a line), and is folded into a space, so every line of the
 * text is one sentence of Atlas's.
 *
 * Every step is idempotent: a quoted name is not quoted again, a folded line
 * has no break left, and an escape holds no control character, so the size
 * of an answer can be measured on its text as it will be sent.
 */

/** The most characters a string in an answer's structured content holds. */
export const DATA_CAP = 512;

// Characters that break a line, move the cursor, reorder the text or hide in it.
// Written as code points: a line separator typed into a pattern ends the line.
const CONTROL_RANGES = [[0x00, 0x1f], [0x7f, 0x9f], [0xad, 0xad], [0x61c, 0x61c], [0x180e, 0x180e], [0x200b, 0x200f],
  [0x2028, 0x202e], [0x2060, 0x206f], [0xfeff, 0xfeff], [0xfff9, 0xfffb]];
const CONTROL_CLASS = `[${CONTROL_RANGES.map(([from, to]) => `${String.fromCodePoint(from)}-${String.fromCodePoint(to)}`).join('')}]`;
const CONTROL = new RegExp(CONTROL_CLASS, 'gu');
// A name that could read as words of its own, or leave its place in a line:
// one with a space, a quote, a backslash or a control character. A glob's
// stars and brackets cannot, so a place spelled as a glob is shown as it is.
const WORDLIKE = new RegExp(`[\\s"'\`\\\\]|${CONTROL_CLASS}`, 'u');
const PLAIN_MAX = 200;
// The words a cut string ends with, counted into its cap.
const CUT_ROOM = 40;

/** A string cut to the cap, saying how many characters were cut. */
export function capped(text, max = DATA_CAP) {
  if (typeof text !== 'string' || text.length <= max) return text;
  let keep = max - CUT_ROOM;
  // Never half of a surrogate pair.
  if (/[\ud800-\udbff]/.test(text[keep - 1])) keep -= 1;
  return `${text.slice(0, keep)}… (${text.length - keep} more characters)`;
}

/** Every string in a value capped; the keys are Atlas's own. */
export function capStrings(value) {
  if (typeof value === 'string') return capped(value);
  if (Array.isArray(value)) return value.map(capStrings);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, capStrings(item)]));
  return value;
}

/**
 * A name as a sentence of Atlas's gives it: as it is when it reads as one
 * name, else quoted as a JSON string, as the text quotes the map's names.
 * For a name that is not the map's, such as a repository's folder.
 */
export function asName(name) {
  return unplain(name) ? JSON.stringify(capped(name)) : name;
}

/** A line with every control, format and line-break character shown as an escape. */
export function neutral(line) {
  return line.replace(CONTROL, (char) => {
    if (char === '\n') return '\\n';
    if (char === '\r') return '\\r';
    if (char === '\t') return '\\t';
    return `\\u${char.codePointAt(0).toString(16).padStart(4, '0')}`;
  });
}

function unplain(value) {
  return typeof value === 'string' && value !== '' && (WORDLIKE.test(value) || value.length > PLAIN_MAX);
}

```

### `packages/atlas/sidecar/consumers.js` (complete)

```js
import { parseBoundaryText } from '../adapter/boundary-file.js';
import { gitRepositoryUrl } from '../core/package-facts.js';
import { asName } from './data.js';
import { group } from './answer.js';
import { filesAt, git, inHistory } from './git.js';
import { readSnapshotAt } from './map.js';
import { publishedAt, TAG_FORM_NAMES } from './tags.js';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

/**
 * "Consumers in the workspace" (docs/atlas-buildup.spec.md, slice AP): for a
 * file in one repository, the other repositories Atlas answers for whose
 * maps declare a package that repository publishes and that contains the
 * file. The join is made here, at question time, from the facts each map
 * already holds (slice AO: what a repository publishes, what it declares);
 * nothing is stored in a map, so each map stays a fact about its own
 * repository.
 *
 * What it will not say: that a consumer "will break". It says which
 * repositories declare the package, at what range and resolved version, how
 * the link between the two was established, and how the producer's map
 * stands against the version the consumer resolved. A zero is never said
 * while Atlas cannot see everywhere the package could be used: it then says
 * the consumers are unverified, and what it could not read.
 */

// How a consumer is tied to the producer, firmest first. `attested` (a
// provenance attestation, SLSA) needs the registry and is unreachable here.
export const LINK_BASES = Object.freeze(['manual', 'repository', 'unverified']);

// Package ecosystems whose manifests Atlas does not extract: a file under
// one of these may be published in a package whose consumers cannot be read.
const UNREAD_ECOSYSTEMS = [
  { name: 'PyPI', files: ['pyproject.toml', 'setup.py', 'setup.cfg'] },
  { name: 'Cargo', files: ['Cargo.toml'] },
  { name: 'NuGet', files: ['Directory.Packages.props', 'packages.config'], suffixes: ['.csproj', '.fsproj'] },
];

function dirOf(path) {
  return path.includes('/') ? path.slice(0, path.lastIndexOf('/')) : '';
}

function contains(dir, file) {
  return dir === '' || file === dir || file.startsWith(`${dir}/`);
}

function normal(url) {
  return typeof url === 'string' && url !== '' ? gitRepositoryUrl(url).toLowerCase() : null;
}

// Whether a map says its package facts were computed. A repository with no
// package.json has none of the keys, and a map made before the facts existed
// has none either, so the keys cannot carry it: the engine writes the marker
// `packageFacts` whenever it computed them, and a map without it is "not read".
export function hasPackageFacts(structure) {
  return Number(structure?.packageFacts) >= 1;
}

const OLD_MAP = 'its map was made before package facts; remap it with this engine';

// The producer's own map predates package facts: which packages hold the files
// asked about is unknown, so the consumers are unverified and nothing is said
// of them (never "none declares it").
function unmarkedProducer(producer, snapshot) {
  const engine = snapshot.engine ?? null;
  return {
    facts: [group('consumerSearch', 'declared', [{
      packages: [], searched: [], declaring: [], notRead: [{ name: producer.name, kind: 'old-map', engine, why: OLD_MAP }], ecosystemsNotRead: [], complete: false, status: 'unverified',
    }])],
    cannotSee: [{
      basis: 'unresolved', what: 'consumer', grain: 'repository', count: 1, named: [producer.name],
      reason: 'the map of the repository asked about was made before package facts, so which packages hold these files is unknown and their consumers are unverified (remap it with this engine)',
    }],
    sentences: [`Atlas: the map of ${asName(producer.name)} was made before package facts (engine ${asName(engine ?? 'not recorded')}), so which packages hold these files is unknown and the consumers are unverified, not none; remap it with this engine.`],
  };
}

/** The producer root's origin, normalised; credentials in the URL never leave it. */
function originOf(root) {
  const read = git(root, ['config', '--get', 'remote.origin.url']);
  return read.ok ? normal(String(read.stdout).trim()) : null;
}

// The files of a mapped repository, from its structure.
function trackedPaths(structure) {
  return new Set([...(structure.boundaries ?? []).flatMap((boundary) => (boundary.files ?? []).map((file) => file.path)), ...(structure.unassigned ?? []).map((file) => file.path)]);
}

// The unextracted ecosystems whose manifests sit at or above a file.
function unreadEcosystemsAbove(paths, file) {
  const found = [];
  for (const ecosystem of UNREAD_ECOSYSTEMS) {
    let dir = dirOf(file);
    for (;;) {
      const names = [...paths].filter((path) => dirOf(path) === dir);
      const hit = names.some((path) => {
        const base = path.slice(path.lastIndexOf('/') + 1);
        return ecosystem.files.includes(base) || (ecosystem.suffixes ?? []).some((suffix) => base.endsWith(suffix));
      });
      if (hit) {
        found.push(ecosystem.name);
        break;
      }
      if (dir === '') break;
      dir = dirOf(dir);
    }
  }
  return found;
}

// The producers a consumer's boundary file names, as it was at the commit
// its map was made from; a tree exported without history is read from disk.
function manualProducers(consumer, snapshot) {
  let text = null;
  if (consumer.exported) {
    try {
      text = readFileSync(join(consumer.root, 'atlas', 'boundaries.yaml'), 'utf8');
    } catch {
      text = null;
    }
  } else {
    const read = filesAt(consumer.root, snapshot.commit, ['atlas/boundaries.yaml']).get('atlas/boundaries.yaml');
    text = read ? read.toString('utf8') : null;
  }
  if (text == null) return [];
  const parsed = parseBoundaryText(text);
  return parsed.ok ? parsed.producers : [];
}

function sameRepository(root, name) {
  return name === root.name || name === root.real || name === root.root;
}

// What the producer's map stands at against the version a consumer resolved.
function skewOf({ producer, snapshot, name, version }) {
  const published = publishedAt(producer.root, name, version);
  const base = { tried: published.tried, ...(published.left ? { notTried: published.left } : {}) };
  if (published.state !== 'found') return { state: 'unknown', reason: published.reason, ...base, published };
  const tag = { tag: published.tag, form: published.form, taggedCommit: published.commit };
  if (published.commit === snapshot.commit) return { state: 'match', ...base, ...tag, published };
  if (inHistory(producer.root, published.commit, snapshot.commit)) return { state: 'ahead', ...base, ...tag, published };
  if (inHistory(producer.root, snapshot.commit, published.commit)) return { state: 'behind', ...base, ...tag, published };
  return { state: 'unknown', reason: 'the tagged commit and the map\'s commit are on different lines of history', ...base, ...tag, published };
}

/**
 * @param {object} input
 * @param {{ name: string, root: string, real?: string, key?: string }} input.producer the repository asked about
 * @param {object} input.snapshot the producer's map
 * @param {string[]} input.files the files asked about
 * @param {{ roots: object[], snapshotOf: (root: object) => ({ ok: boolean, snapshot?: object, error?: object }) }} input.workspace
 * @returns {{ facts: object[], cannotSee: object[], sentences: string[] }}
 */
export function consumersFor({ producer, snapshot, files, workspace }) {
  const structure = snapshot.structure;
  // A map made before the package facts existed says nothing about what its
  // repository publishes or declares; the missing keys are not "none".
  if (!hasPackageFacts(structure)) return unmarkedProducer(producer, snapshot);
  const published = structure.packagesPublished ?? [];
  const tracked = trackedPaths(structure);
  const others = workspace.roots.filter((root) => root.key !== producer.key);

  // The published packages whose directory holds each file asked about.
  const packages = new Map();
  const unread = new Set();
  const inNoPackage = [];
  for (const file of files) {
    const holding = published.filter((entry) => contains(dirOf(entry.manifest), file));
    for (const entry of holding) packages.set(entry.manifest, { ...entry, files: [...(packages.get(entry.manifest)?.files ?? []), file] });
    for (const ecosystem of unreadEcosystemsAbove(tracked, file)) unread.add(ecosystem);
    if (holding.length === 0) inNoPackage.push(file);
  }

  const facts = [];
  const cannotSee = [];
  const sentences = [];
  const note = (reason, extra = {}) => cannotSee.push({ basis: 'outside', what: 'consumer', grain: 'repository', count: 0, named: [], reason, ...extra });

  if (packages.size === 0 && unread.size === 0) return { facts, cannotSee, sentences };

  const origin = originOf(producer.root);
  const mapped = [];
  const unmapped = [];
  for (const other of others) {
    const read = workspace.snapshotOf(other);
    if (!read.ok) unmapped.push({ name: other.name, kind: 'no-map', why: read.error?.code ?? 'no map' });
    // A consumer map made before package facts declares nothing it can be
    // read to declare: it is not read, and it is never counted as searched.
    else if (!hasPackageFacts(read.snapshot.structure)) unmapped.push({ name: other.name, kind: 'old-map', engine: read.snapshot.engine ?? null, why: OLD_MAP });
    else mapped.push({ root: other, snapshot: read.snapshot });
  }

  const links = [];
  const orphans = [];
  const taggedAt = new Map();
  for (const entry of [...packages.values()].sort((a, b) => (a.manifest < b.manifest ? -1 : 1))) {
    for (const { root, snapshot: theirs } of mapped) {
      const manual = manualProducers(root, theirs);
      const declared = (theirs.structure.packageDependencies ?? []).filter((dependency) => dependency.purl === entry.purl);
      const claim = manual.find((item) => item.package === entry.name);
      for (const dependency of declared) {
        // A consumer that names another repository as this package's producer
        // is not a consumer of this one.
        if (claim && !sameRepository(producer, claim.repository)) continue;
        let linkBasis;
        let why = null;
        if (claim) linkBasis = 'manual';
        else if (entry.repository && origin && normal(entry.repository) === origin) linkBasis = 'repository';
        else {
          linkBasis = 'unverified';
          why = !entry.repository ? 'the producer\'s manifest names no repository'
            : !origin ? 'the producer\'s clone has no origin remote to compare with'
              : 'the producer\'s manifest names a repository other than its clone\'s origin';
        }
        const key = `${entry.manifest}\0${dependency.version ?? ''}`;
        if (!taggedAt.has(key)) taggedAt.set(key, skewOf({ producer, snapshot, name: entry.name, version: dependency.version ?? null }));
        const skew = taggedAt.get(key);
        const atPublished = atPublishedCommit({ producer, skew, entry });
        links.push({
          linkBasis,
          item: {
            consumer: root.name,
            package: entry.name,
            purl: entry.purl,
            producerManifest: entry.manifest,
            files: entry.files,
            consumerManifest: dependency.manifest,
            field: dependency.field,
            range: dependency.range,
            kind: dependency.kind,
            resolvedVersion: dependency.version ?? null,
            ...(dependency.version == null && dependency.unknown ? { resolvedUnknown: dependency.unknown } : {}),
            ...(why ? { why } : {}),
            producerMap: { commit: snapshot.commit, engine: snapshot.engine ?? null },
            consumerMap: { commit: theirs.commit, engine: theirs.engine ?? null },
            skew: {
              state: skew.state,
              tried: skew.tried,
              ...(skew.reason ? { reason: skew.reason } : {}),
              ...(skew.tag ? { tag: skew.tag, taggedCommit: skew.taggedCommit } : {}),
              ...(atPublished ? { atPublishedCommit: atPublished } : {}),
            },
          },
        });
      }
    }
  }

  // A mapping a consumer states by hand for a producer Atlas has no map for.
  for (const { root, snapshot: theirs } of mapped) {
    for (const claim of manualProducers(root, theirs)) {
      const target = workspace.roots.find((other) => sameRepository(other, claim.repository));
      const producing = target ? workspace.snapshotOf(target) : null;
      if (!target) orphans.push({ consumer: root.name, package: claim.package, repository: claim.repository, why: 'the repository is not one Atlas answers for' });
      else if (!producing.ok) orphans.push({ consumer: root.name, package: claim.package, repository: target.name, why: 'the repository has no map Atlas can answer from' });
    }
  }

  for (const basis of LINK_BASES) {
    const items = links.filter((link) => link.linkBasis === basis).map((link) => link.item)
      .sort((a, b) => (a.consumer < b.consumer ? -1 : a.consumer > b.consumer ? 1 : a.consumerManifest < b.consumerManifest ? -1 : 1));
    if (items.length > 0) facts.push(group('consumers', 'declared', items, { linkBasis: basis }));
  }
  if (orphans.length > 0) facts.push(group('orphanProducers', 'declared', orphans));

  const consumerNames = [...new Set(links.map((link) => link.item.consumer))].sort();
  const complete = unread.size === 0 && unmapped.length === 0;
  facts.push(group('consumerSearch', 'declared', [{
    packages: [...packages.values()].map((entry) => ({ package: entry.name, purl: entry.purl, manifest: entry.manifest, version: entry.version ?? null })),
    searched: mapped.map((entry) => entry.root.name).sort(),
    declaring: consumerNames,
    notRead: unmapped,
    ecosystemsNotRead: [...unread].sort(),
    complete,
    status: complete ? 'searched' : 'unverified',
  }]));

  // What Atlas cannot see here, in the question's own terms.
  if (unread.size > 0) {
    cannotSee.push({
      basis: 'outside', what: 'consumer', grain: 'repository', count: unread.size, where: 'another-repository',
      named: [...unread].sort(), reason: 'a file asked about sits in a package of an ecosystem Atlas does not extract (PyPI and uv, Cargo, NuGet), so the repositories that depend on it are not readable',
    });
  }
  const noMap = unmapped.filter((entry) => entry.kind === 'no-map');
  const oldMap = unmapped.filter((entry) => entry.kind === 'old-map');
  if (noMap.length > 0) {
    cannotSee.push({
      basis: 'unresolved', what: 'consumer', grain: 'repository', count: noMap.length,
      named: noMap.map((entry) => entry.name), reason: 'repositories among the roots with no map Atlas can answer from, which may declare the package',
    });
  }
  if (oldMap.length > 0) {
    cannotSee.push({
      basis: 'unresolved', what: 'consumer', grain: 'repository', count: oldMap.length,
      named: oldMap.map((entry) => entry.name), reason: 'repositories among the roots whose maps were made before package facts and say nothing of what they declare (remap them with this engine)',
    });
  }
  note('provenance attestations (need the registry): a link is never called attested');
  note('which files a published package ships: a file counts as in a package when it is under the manifest\'s directory, and the package\'s files and exports lists are not read');
  note('tags may be stale: the producer\'s release tags are read from this clone only, and a shallow clone or one whose tags were never fetched gives unknown, never a match');
  note('consumers outside the roots Atlas answers for, private repositories it was not given, runtime loading, the version actually installed, and whether the consumers\' tests cover the call site');

  // Sentences, in Atlas's voice; every name taken from a repository is data.
  const named = (list, count = 6) => (list.length <= count ? list.map(asName).join(', ') : `${list.slice(0, count).map(asName).join(', ')} and ${list.length - count} more`);
  for (const entry of [...packages.values()]) {
    const mine = links.filter((link) => link.item.package === entry.name && link.item.producerManifest === entry.manifest);
    const who = [...new Set(mine.map((link) => link.item.consumer))].sort();
    const heard = mapped.length;
    sentences.push(`Atlas: ${named(entry.files)} ${entry.files.length === 1 ? 'is' : 'are'} in ${asName(entry.name)}, which this repository publishes (${asName(entry.manifest)}).`);
    if (who.length > 0) {
      sentences.push(`Atlas: ${who.length} of ${heard} other ${heard === 1 ? 'repository' : 'repositories'} among the roots ${who.length === 1 ? 'declares' : 'declare'} ${asName(entry.name)}: ${named(who)}.`);
    } else {
      sentences.push(complete
        ? `Atlas: none of the ${heard} other ${heard === 1 ? 'repository' : 'repositories'} among the roots declares ${asName(entry.name)}; consumers outside the roots stay unseen.`
        : `Atlas: no repository among the roots Atlas could read declares ${asName(entry.name)}; the consumers are unverified (see what Atlas cannot see).`);
    }
  }
  for (const link of links) {
    const item = link.item;
    const resolved = item.resolvedVersion ? `resolved ${asName(item.resolvedVersion)}` : `resolved version unknown (${asName(item.resolvedUnknown ?? 'not recorded')})`;
    const skew = item.skew.state === 'unknown'
      ? `unknown (${asName(item.skew.reason)}; tried ${item.skew.tried.length > 0 ? item.skew.tried.join(', ') : 'no tag'})`
      : `${item.skew.state} (tag ${asName(item.skew.tag)})`;
    const basis = link.linkBasis === 'unverified' ? `unverified: ${item.why}` : `${link.linkBasis} basis`;
    sentences.push(`Atlas: ${asName(item.consumer)} declares ${asName(item.package)} at ${asName(item.range)} in ${asName(item.consumerManifest)}, ${resolved}; the producer's map is ${skew}; link ${basis}.`);
  }
  for (const orphan of orphans) {
    sentences.push(`Atlas: ${asName(orphan.consumer)} names ${asName(orphan.repository)} as the producer of ${asName(orphan.package)}, but ${orphan.why}.`);
  }
  if (unread.size > 0) sentences.push(`Atlas: a file asked about is in a package of an ecosystem Atlas does not extract (${[...unread].sort().join(', ')}); its consumers are unverified, not none.`);
  if (noMap.length > 0) sentences.push(`Atlas: ${named(noMap.map((entry) => entry.name))} ${noMap.length === 1 ? 'has' : 'have'} no map Atlas can answer from, so ${noMap.length === 1 ? 'it was' : 'they were'} not searched.`);
  for (const entry of oldMap) {
    sentences.push(`Atlas: ${asName(entry.name)} was not read: its map was made before package facts (engine ${asName(entry.engine ?? 'not recorded')}), so what it declares is unknown, not none; remap it with this engine.`);
  }
  for (const link of links) {
    const at = link.item.skew.atPublishedCommit;
    if (at?.packageFacts === false) sentences.push(`Atlas: the producer's map at ${asName(link.item.skew.tag)} was made before package facts, so it cannot say whether that release held ${named(link.item.files)}.`);
    else if (at?.map === false) sentences.push(`Atlas: no map was committed at the producer's ${asName(link.item.skew.tag)}, so what that release held is not read.`);
  }
  if (links.some((link) => link.item.skew.state !== 'unknown') === false && links.length > 0) {
    sentences.push(`Atlas: the producer's tags were tried in the forms ${TAG_FORM_NAMES.join(', ')} and none matched a resolved version.`);
  }
  return { facts, cannotSee, sentences };
}

// When the version a consumer resolved was published from another commit, the
// map at that commit if the clone holds one: does it hold the file asked about,
// in the package, there? Null when the commit is the map's own or unknown.
const AT_PUBLISHED = new WeakMap();

function atPublishedCommit({ producer, skew, entry }) {
  if (skew.state !== 'ahead' && skew.state !== 'behind') return null;
  const key = skew.taggedCommit;
  const cache = AT_PUBLISHED.get(producer) ?? new Map();
  AT_PUBLISHED.set(producer, cache);
  if (!cache.has(key)) cache.set(key, readSnapshotAt(producer.root, key));
  const read = cache.get(key);
  if (!read.ok) return { map: false };
  // A map from before package facts cannot say what it published: not "no".
  if (!hasPackageFacts(read.snapshot.structure)) return { map: true, packageFacts: false };
  const there = (read.snapshot.structure.packagesPublished ?? []).find((item) => item.manifest === entry.manifest);
  if (!there) return { map: true, publishesPackage: false };
  const present = trackedPaths(read.snapshot.structure);
  return { map: true, publishesPackage: true, holdsFiles: entry.files.map((file) => ({ file, present: present.has(file) })) };
}
```

### `isValidPackageName` and `gitRepositoryUrl`, from `packages/atlas/core/package-facts.js`

```js
export function gitRepositoryUrl(spec) {
  let text = String(spec).trim().replace(/^git\+/, '').replace(/#.*$/, '');
  const host = /^(github|gitlab|bitbucket):(.+)$/.exec(text);
  if (host) text = `https://${{ github: 'github.com', gitlab: 'gitlab.com', bitbucket: 'bitbucket.org' }[host[1]]}/${host[2]}`;
  else if (/^gist:/.test(text)) text = `https://gist.github.com/${text.slice('gist:'.length)}`;
  else if (/^[^@./:\s][^/:\s]*\/[^/:\s]+$/.test(text)) text = `https://github.com/${text}`;
  else {
    const scp = /^(?:[^@/\s]+@)?([^/:\s]+):(?!\/\/)(.+)$/.exec(text);
    const url = /^(?:ssh|git|https?):\/\/(?:[^@/]+@)?([^/:]+)(?::\d+)?\/(.+)$/.exec(text);
    if (url) text = `https://${url[1]}/${url[2]}`;
    else if (scp) text = `https://${scp[1]}/${scp[2]}`;
  }
  return text.replace(/\.git$/, '').replace(/\/+$/, '');
}
export function isValidPackageName(name) {
  if (typeof name !== 'string' || name.length === 0) return false;
  if (name.startsWith('.') || name.startsWith('_')) return false;
  if (name.trim() !== name) return false;
  if (encodeURIComponent(name) === name) return true;
  const scoped = name.match(/^(?:@([^/]+?)[/])?([^/]+?)$/);
  if (!scoped || scoped[1] === undefined) return false;
  const [, scope, pkg] = scoped;
  if (pkg.startsWith('.')) return false;
  return encodeURIComponent(scope) === scope && encodeURIComponent(pkg) === pkg;
}
```
