#!/bin/sh
# POSIX wrapper: run the rnd CLI from any directory.
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here" && exec python -m rnd "$@"
