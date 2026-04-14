#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENTRY="$SCRIPT_DIR/analyze_repo.py"

if command -v python3 >/dev/null 2>&1; then
  exec python3 -B "$ENTRY" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python -B "$ENTRY" "$@"
fi

echo "Python was not found in PATH." >&2
exit 1

