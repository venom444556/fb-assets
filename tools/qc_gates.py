#!/usr/bin/env python3
"""Extra QC gates for bottle cutouts (run beside inspect_bottles.py).

Usage: qc_gates.py [repo_root] [paths...]   (no paths = every PNG in the repo)
Exit 1 on any REJECT. Gates:
  PLACEHOLDER  pixel md5 starts 532b4d (ScentSplit "No image is available") or the 8x8 gradient hash is within 3 bits of it
  DUP          exact RGBA pixel hash already used by a different fragrance (known same-product pairs are allowed)
  BOX          the cutout is wider than tall or has more than one object (REJECT); WARN when it fills >88% of its
               bounding box (a boxed bottle does, so does a slim flat flask: look at the sheet). Packaging
               beside the bottle still needs the eye.
"""
import sys, os, glob, hashlib, collections
import numpy as np
from PIL import Image

PLACEHOLDER_MD5 = "532b4d"
SAME_PRODUCT = [{"burberry/female/burberry-her.png", "burberry/female/burberry-women.png"},
                {"gucci/female/flora-by-gucci-gorgeous-gardenia.png", "gucci/female/flora-gorgeous-gardenia.png"},
                {"gucci/male/gucci-guilty-eau-de-toilette-intense-pour-homme.png", "gucci/male/gucci-guilty-intense-pour-homme.png"},
                {"mercedes-benz/male/mercedes-benz-intense.png", "mercedes-benz/male/mercedes-benz-man-intense.png"},
                {"adidas/female/adidas-floral-dream.png", "adidas/female/floral-dream.png"}]

def dhash(im):
    g = np.array(im.convert("L").resize((9, 8), Image.BILINEAR), dtype=float)
    return "".join("1" if x else "0" for x in (g[:, 1:] > g[:, :-1]).flatten())

def box_reasons(im):
    a = np.array(im.getchannel("A")) > 40
    ys, xs = np.where(a)
    if not len(ys): return ["empty"]
    out = []
    w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    if w > h: out.append("wider than tall")
    cols = a.any(axis=0)[xs.min():xs.max() + 1]; gap = mx = 0
    for v in cols:
        gap = 0 if v else gap + 1; mx = max(mx, gap)
    if mx > 0.04 * len(cols): out.append("more than one object")
    if a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].mean() > 0.88: out.append("fills its bounding box")
    return out

def main():
    root = next((a for a in sys.argv[1:] if os.path.isdir(a)), ".")
    only = [a for a in sys.argv[1:] if not os.path.isdir(a)]
    files = sorted(os.path.relpath(p, root) for p in glob.glob(os.path.join(root, "**/*.png"), recursive=True))
    files = [f for f in files if "/" in f]   # house/gender/slug.png only
    pix = {}
    for f in files:
        im = Image.open(os.path.join(root, f)).convert("RGBA"); pix[f] = (hashlib.md5(im.tobytes()).hexdigest(), im)
    by = collections.defaultdict(set)
    for f, (m, _) in pix.items(): by[m].add(f)
    ph = next((dhash(im) for m, im in pix.values() if m.startswith(PLACEHOLDER_MD5)), None)
    bad = 0
    for f in (only or files):
        m, im = pix[f]; why = []
        if m.startswith(PLACEHOLDER_MD5) or (ph and sum(a != b for a, b in zip(dhash(im), ph)) <= 3): why.append("PLACEHOLDER")
        twins = by[m] - {f}
        if twins and not any({f} | twins <= s for s in SAME_PRODUCT): why.append("DUP of " + sorted(twins)[0])
        for r in box_reasons(im):
            if r.startswith("fills"): print("WARN", f, "fills its bounding box (box?)")
            else: why.append("BOX: " + r)
        if why: bad += 1; print("REJECT", f, "; ".join(why))
    print("checked", len(only or files), "rejected", bad)
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
