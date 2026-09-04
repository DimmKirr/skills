#!/usr/bin/env bash
# Display an image in the user's terminal from inside a devcell container.
#
#   show.sh <image> [max_cols] [max_rows] [label]
#
# When max_cols/max_rows are omitted, auto-scales to 1/3 of terminal width.
# Pre-scales the image to the target cell size (saves to $TMPDIR), then
# encodes and writes to the pty as root.
#
# The harness (Claude Code TUI) renders its own text at the same screen
# position as the grid. To prevent overlap, this script writes blank lines
# directly to the PTY before the grid, pushing it below the harness area.
set -uo pipefail
export LC_ALL=C.UTF-8 LANG=C.UTF-8
here=$(cd "$(dirname "$0")" && pwd)

image="$1"
label="${image##*/}"

# Detect whether explicit cols/rows were passed (numeric 2nd arg)
if [ "${2:-}" ] && [ "$2" -eq "$2" ] 2>/dev/null; then
  max_cols="$2"
  max_rows="${3:-40}"
  label="${4:-$label}"
  scale_out=$(uv run --with pillow python "$here/scale.py" "$image" "$max_cols" "$max_rows")
else
  label="${2:-$label}"
  scale_out=$(uv run --with pillow python "$here/scale.py" "$image")
fi

scaled_path=$(echo "$scale_out" | sed -n '1p')
cols=$(echo "$scale_out" | sed -n '2p')
rows=$(echo "$scale_out" | sed -n '3p')

# Target pty: explicit override, else the nearest ancestor process that has one.
if [ -z "${TTY_IMAGE_DEV:-}" ]; then
  pid=$$
  while [ "$pid" -gt 1 ]; do
    t=$(ps -o tty= -p "$pid" 2>/dev/null | tr -d ' ')
    case "$t" in
      pts/*) TTY_IMAGE_DEV="/dev/$t"; break ;;
    esac
    pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ') || break
    [ -z "$pid" ] && break
  done
fi
TTY_IMAGE_DEV=${TTY_IMAGE_DEV:-/dev/pts/0}
export TTY_IMAGE_DEV

tmpf=$(mktemp /tmp/ttyimg.XXXXXX)
trap 'rm -f "$tmpf"' EXIT
uv run --with pillow python "$here/encode.py" "$scaled_path" "$cols" "$rows" "$label" > "$tmpf" || exit 1

# Write padding directly to the PTY (not stdout) so the grid doesn't overlap
# with the harness text. Pre-padding pushes the grid below the harness area;
# post-padding pushes the PTY cursor below the grid so the next harness render
# (the assistant's text response) doesn't overwrite the image.
PRE_PAD=${TTY_IMAGE_PRE_PAD:-0}
POST_PAD=${TTY_IMAGE_POST_PAD:-10}
pre=$(printf '\r\n%.0s' $(seq 1 "$PRE_PAD"))
post=$(printf '\r\n%.0s' $(seq 1 "$POST_PAD"))
sudo sh -c "printf '%s' '$pre' > '$TTY_IMAGE_DEV'; cat '$tmpf' > '$TTY_IMAGE_DEV'; printf '%s' '$post' > '$TTY_IMAGE_DEV'"
