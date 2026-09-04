#!/usr/bin/env python3
"""Composite 2+ images side by side into ONE labelled PNG, path on stdout.

Comparisons must be a single image, not several placements: separate images
cannot be aligned to a common baseline, and each extra id is another thing to
clean up. One composite under one id sidesteps both.

    compare.py OUT.png "label:image" "label:image" [...]
"""
import sys
from PIL import Image, ImageDraw

HEIGHT, GAP, BAR = 900, 30, 34


def load(p):
    """Flatten onto white — convert('RGB') would render alpha=0 as BLACK."""
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, im).convert("RGB")


out_path, items = sys.argv[1], sys.argv[2:]
panels = []
for it in items:
    label, _, path = it.partition(":")
    im = load(path)
    panels.append((label, im.resize((int(im.width * HEIGHT / im.height), HEIGHT),
                                    Image.LANCZOS)))

W = sum(p.width for _, p in panels) + GAP * (len(panels) - 1)
canvas = Image.new("RGB", (W, HEIGHT + BAR), (250, 250, 250))
d = ImageDraw.Draw(canvas)
x = 0
for label, p in panels:
    canvas.paste(p, (x, BAR))
    d.text((x + 8, 12), label, fill=(0, 0, 0))
    d.rectangle([x, BAR, x + p.width - 1, HEIGHT + BAR - 1], outline=(200, 200, 200))
    x += p.width + GAP
canvas.save(out_path)
print(out_path)
