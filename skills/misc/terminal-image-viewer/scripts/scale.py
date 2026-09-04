#!/usr/bin/env python3
"""Pre-scale an image for terminal display. Part of terminal-image-viewer skill.

    scale.py <image> [max_cols] [max_rows]

When max_cols/max_rows are omitted, auto-computes 1/3 of terminal width.
Outputs three lines to stdout:
    1. path to the scaled image (in $TMPDIR)
    2. cols (cell count)
    3. rows (cell count)

Saves to $TMPDIR/<stem>-<hash>.<ext> so repeated calls hit the same file.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

CELL_ASPECT = 0.5  # cell width / cell height (~8x16 px)
SCALE_FRACTION = 1 / 3  # default: use 1/3 of terminal width


def term_size_from_pty(default=(55, 224)):
    try:
        dev = os.environ.get("TTY_IMAGE_DEV", "/dev/pts/0")
        out = subprocess.run(
            ["sudo", "stty", "-F", dev, "size"],
            capture_output=True, text=True, check=True,
        )
        r, c = out.stdout.split()
        return int(r), int(c)
    except Exception:
        return default


def main():
    path = sys.argv[1]
    im = Image.open(path)
    img_w, img_h = im.size

    term_rows, term_cols = term_size_from_pty()

    if len(sys.argv) > 2:
        max_cols = min(int(sys.argv[2]), term_cols - 2)
    else:
        max_cols = int(term_cols * SCALE_FRACTION)

    max_rows = max(8, term_rows - 12)
    if len(sys.argv) > 3:
        max_rows = min(int(sys.argv[3]), max_rows)

    cols = max_cols
    rows = round(cols * (img_h / img_w) * CELL_ASPECT)

    if rows > max_rows:
        rows = max_rows
        cols = round(rows / ((img_h / img_w) * CELL_ASPECT))

    cols, rows = max(1, cols), max(1, rows)

    px_w = cols * 8
    px_h = rows * 16

    im_scaled = im.copy()
    im_scaled.thumbnail((px_w, px_h), Image.LANCZOS)

    src = Path(path)
    content_hash = hashlib.md5(src.read_bytes()).hexdigest()[:8]
    tmp_dir = os.environ.get("TMPDIR", "/tmp")
    out_name = f"{src.stem}-{content_hash}-{cols}x{rows}{src.suffix}"
    out_path = Path(tmp_dir) / out_name

    im_scaled.save(str(out_path), optimize=True)

    # stdout: path, cols, rows (consumed by show.sh)
    print(out_path)
    print(cols)
    print(rows)

    print(
        f"Scaled {img_w}x{img_h} -> {im_scaled.width}x{im_scaled.height}px, "
        f"target {cols}x{rows} cells (term {term_cols}x{term_rows})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
