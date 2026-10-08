#!/usr/bin/env python3
"""Inspect hosted bottle cutouts and build a contact sheet.

Usage: inspect_bottles.py [repo_root] [--sheet contact_sheet.png]
Exit 1 if any image FAILs. WARN rows need a human look at the contact sheet.
Checks (alpha > 40 counts as solid):
  size/mode   1200x800 RGBA
  corners     all four corner pixels transparent
  edge        no solid pixel within 2 px of any canvas edge (clipped by canvas)
  center      horizontal centre within 10 px
  height      bottle height 80-95% of canvas
  top-gap     transparent pixels enclosed between solid pixels in the top 6% of the
              bottle (a lost cap plate/lid shows up here); WARN above 40 px
"""
import sys, glob, os
import numpy as np
from PIL import Image, ImageDraw

root = next((a for a in sys.argv[1:] if not a.startswith("--") and os.path.isdir(a)), ".")
sheet = "contact_sheet.png"
if "--sheet" in sys.argv:
    sheet = sys.argv[sys.argv.index("--sheet") + 1]

def inspect(path):
    im = Image.open(path)
    fails, warns = [], []
    if im.size != (1200, 800) or im.mode != "RGBA":
        return ["size/mode %s %s" % (im.size, im.mode)], warns
    a = np.array(im)[..., 3]
    solid = a > 40
    if any(a[y, x] > 0 for y, x in ((0, 0), (0, -1), (-1, 0), (-1, -1))):
        fails.append("corner not transparent")
    if solid[:2].any() or solid[-2:].any() or solid[:, :2].any() or solid[:, -2:].any():
        fails.append("solid pixels touch canvas edge")
    ys, xs = np.where(solid)
    if not len(ys):
        return ["empty"], warns
    cx = (xs.min() + xs.max()) / 2
    h = (ys.max() - ys.min() + 1) / 800
    if abs(cx - 600) > 10: fails.append("off-centre %.0fpx" % (cx - 600))
    if not .80 <= h <= .95: fails.append("height %.0f%%" % (h * 100))
    top = solid[ys.min(): ys.min() + int((ys.max() - ys.min()) * .06)]
    gap = 0
    for r in top:
        i = np.where(r)[0]
        if len(i): gap += int((~r[i[0]:i[-1]]).sum())
    if gap > 40: warns.append("top-gap %dpx (lost cap/plate? check sheet)" % gap)
    return fails, warns

files = sorted(glob.glob(os.path.join(root, "*", "*", "*.png")))
bad = 0
thumbs = []
for f in files:
    fails, warns = inspect(f)
    name = os.path.relpath(f, root)
    status = "FAIL" if fails else ("WARN" if warns else "ok")
    bad += bool(fails)
    print("%-4s %-70s %s" % (status, name, "; ".join(fails + warns)))
    thumbs.append((name, status, Image.open(f).convert("RGBA")))

cols, tw, th = 6, 240, 190
rows = (len(thumbs) + cols - 1) // cols
cs = Image.new("RGB", (cols * tw, rows * th), (128, 140, 160))
d = ImageDraw.Draw(cs)
for i, (name, status, im) in enumerate(thumbs):
    t = im.resize((tw - 8, int((tw - 8) * 2 / 3)))
    x, y = (i % cols) * tw, (i // cols) * th
    cs.paste(t, (x + 4, y + 2), t)
    d.text((x + 4, y + th - 18), "%s %s" % (status, name.split("/", 1)[1][:34]), fill=(255, 255, 255) if status == "ok" else (255, 220, 0))
cs.save(os.path.join(root, sheet))
print("contact sheet:", os.path.join(root, sheet), "| files:", len(files), "| FAIL:", bad)
sys.exit(1 if bad else 0)
