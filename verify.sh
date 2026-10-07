#!/usr/bin/env bash
# One command for test + build + smoke. Exits non-zero on the first failure.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python}"

echo "== tests";  "$PY" -m unittest discover -s tests -t .
echo "== check";  "$PY" -m rnd check
db="$(mktemp -d)/rnd.db"
echo "== build";  "$PY" -m rnd --db "$db" build
echo "== smoke"
"$PY" -m rnd --version
"$PY" -m rnd --db "$db" search cuda --limit 1 >/dev/null
"$PY" -m rnd --db "$db" tools --json | "$PY" -c "import json,sys; assert json.load(sys.stdin), 'no instruments'"
"$PY" -m rnd --db "$db" stats >/dev/null
echo "verify: ok"
