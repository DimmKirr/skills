#!/usr/bin/env bash
# Show 2+ images side by side in the user's terminal.
#   compare.sh "BEFORE:a.png" "AFTER:b.png" [...]
# Auto-scales the composite to ~2/3 terminal width (wider than single show
# because the panels share the space).
set -uo pipefail
export LC_ALL=C.UTF-8 LANG=C.UTF-8
here=$(cd "$(dirname "$0")" && pwd)
out=$(mktemp /tmp/ttycompare.XXXXXX).png
uv run --with pillow python "$here/compare.py" "$out" "$@" >/dev/null || exit 1
# compare.py produces a wide composite; let scale.py auto-size it.
# Use 2/3 terminal width since it's a side-by-side view.
"$here/show.sh" "$out" "$(echo "$*" | cut -c1-100)"
