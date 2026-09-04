#!/usr/bin/env python3
"""Encode an image for display in the user's pane, via Kitty Unicode placeholders.

Companion to show.sh, which pipes this to /dev/pts/0 as root (the pty is
root:tty 0620 and we run as uid 30033, but PIL lives in the user's uv env —
hence the split).

Two parts go down the wire, and the split is the whole point:

  1. The image bytes, transmitted as a VIRTUAL placement (`U=1`) inside a tmux
     DCS passthrough. tmux forwards these to ghostty untracked; ghostty stores
     the image under `i=ID` but draws nothing yet.
  2. A rows x cols grid of U+10EEEE placeholder characters, written as ORDINARY
     TEXT — deliberately not wrapped. tmux therefore parses it into its own
     screen model like any other pane output, and ghostty overlays the stored
     image onto those cells.

Why bother: an `a=T` placement is anchored to physical screen cells that tmux
knows nothing about, so it floats on top of every session and window until
explicitly deleted. Placeholders live in the text grid, so the picture is
scoped to this pane and vanishes when its cells are overwritten or scrolled —
the behaviour you'd expect from any other output.

The image id is fixed: re-transmitting the same `i=ID` REPLACES the stored
image, so successive calls swap the picture instead of stacking placements.

    encode.py IMAGE [max_cols] [max_rows] [label]

Modelled on DimmKirr/addiplay internal/fanart/placeholder.go.
"""
import base64
import io
import os
import subprocess
import sys

from PIL import Image

IMAGE_ID = 1          # stable: a re-transmit replaces, never stacks
CELL_ASPECT = 0.5     # cell width/height (~8x16), to keep the image square-ish
ESC, ST = b"\x1b", b"\x1b\\"

# Kitty's row/column diacritics: each placeholder cell carries its own (row,
# col) index so the terminal never has to guess which image cell it shows.
# Without them a newline between rows breaks the "contiguous run" heuristic
# and the image tiles once per row.
#
# The canonical 297-entry table ships beside this script; the inline head is a
# fallback so the script still works if that file goes missing. The table's
# length is the hard cap on grid size — one diacritic per row and per column.
_FALLBACK = [
    0x0305, 0x030D, 0x030E, 0x0310, 0x0312, 0x033D, 0x033E, 0x033F,
    0x0346, 0x034A, 0x034B, 0x034C, 0x0350, 0x0351, 0x0352, 0x0357,
    0x035B, 0x0363, 0x0364, 0x0365, 0x0366, 0x0367, 0x0368, 0x0369,
    0x036A, 0x036B, 0x036C, 0x036D, 0x036E, 0x036F, 0x0483, 0x0484,
]


def _load_diacritics():
    import pathlib
    f = pathlib.Path(__file__).with_name("rowcolumn-diacritics.txt")
    try:
        return [int(line, 16) for line in f.read_text().split() if line.strip()]
    except Exception:
        return _FALLBACK


DIACRITICS = _load_diacritics()
MAX_CELLS = len(DIACRITICS)

def term_size(default=(55, 224)):
    """Rows/cols of the pty, read as root — tmux keeps the pty's winsize in
    step with the pane and nothing here can query the terminal directly."""
    try:
        out = subprocess.run(["sudo", "stty", "-F", os.environ.get("TTY_IMAGE_DEV", "/dev/pts/0"),
                              "size"], capture_output=True, text=True, check=True)
        r, c = out.stdout.split()
        return int(r), int(c)
    except Exception:
        return default


TERM_ROWS, TERM_COLS = term_size()
# The grid is written inline, so anything taller than the viewport scrolls off
# and the user sees only the tail of the picture. Leave room for the prompt and
# whatever the harness redraws under it.
VIEWPORT_ROWS = max(8, TERM_ROWS - 12)

path = sys.argv[1]
max_cols = min(int(sys.argv[2]) if len(sys.argv) > 2 else 60, MAX_CELLS, TERM_COLS - 2)
max_rows = min(int(sys.argv[3]) if len(sys.argv) > 3 else 40, MAX_CELLS, VIEWPORT_ROWS)
label = sys.argv[4] if len(sys.argv) > 4 else path.rsplit("/", 1)[-1]

im = Image.open(path).convert("RGBA")
if os.environ.get("TTY_IMAGE_KEEP_ALPHA") != "1":
    # Flatten onto white. Transparent artwork (illustrations, logos, anything
    # cut out) otherwise shows the terminal's own background through it, which
    # on a dark theme renders black-on-black. White also matches how print
    # artwork is actually viewed. Note PIL's convert("RGB") maps alpha=0 to
    # BLACK, not white — always composite, never convert.
    im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
im = im.convert("RGB")

cols = max_cols
rows = round(cols * (im.height / im.width) * CELL_ASPECT)
if rows > max_rows:
    rows = max_rows
    cols = round(rows / ((im.height / im.width) * CELL_ASPECT))
cols, rows = max(1, min(cols, MAX_CELLS)), max(1, min(rows, MAX_CELLS))

im.thumbnail((cols * 16, rows * 32), Image.LANCZOS)   # no point shipping 4K
buf = io.BytesIO()
im.save(buf, "PNG", optimize=True)
b64 = base64.b64encode(buf.getvalue()).decode()

# --- 1. virtual transmit, through tmux passthrough (ESC doubled) ------------
xmit, first, data = b"", True, b64
while data:                                            # protocol caps at 4096
    chunk, data = data[:4096], data[4096:]
    m = b"1" if data else b"0"
    if first:
        xmit += (ESC + b"_Ga=T,U=1,f=100,i=%d,c=%d,r=%d,q=2,m=%s;"
                 % (IMAGE_ID, cols, rows, m) + chunk.encode() + ST)
        first = False
    else:
        xmit += ESC + b"_Gm=%s;" % m + chunk.encode() + ST
out = ESC + b"Ptmux;" + xmit.replace(ESC, ESC + ESC) + ESC + b"\\"

# --- 2. placeholder grid, as plain text so tmux owns it --------------------
# The 24-bit foreground colour carries the image id: R=high, G=mid, B=low.
fg = ESC + b"[38;2;%d;%d;%dm" % ((IMAGE_ID >> 16) & 0xFF,
                                 (IMAGE_ID >> 8) & 0xFF,
                                 IMAGE_ID & 0xFF)


# Right-align by padding with spaces rather than moving the cursor: an
# absolute CUP would target physical screen cells outside tmux's model, which
# is exactly the floating-over-everything behaviour this design avoids.
pad = b" " * max(0, TERM_COLS - cols - 1)

out += b"\r\n"
for r in range(rows):
    out += pad + fg
    for c in range(cols):
        cell = "\U0010EEEE" + chr(DIACRITICS[r]) + chr(DIACRITICS[c])
        out += cell.encode()
    out += ESC + b"[0m\r\n"
out += pad + f"{label[:cols]}\r\n".encode()

sys.stdout.buffer.write(out)
sys.stderr.write(f"{label}: {im.width}x{im.height}px in {cols}x{rows} cells "
                 f"(placeholder-bound, id={IMAGE_ID})\n")
