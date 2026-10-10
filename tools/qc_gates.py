#!/usr/bin/env python3
"""Extra QC gates for bottle cutouts (run beside inspect_bottles.py).

Usage: qc_gates.py [repo_root] [paths...]   (no paths = every PNG in the repo)
Exit 1 on any REJECT. Gates:
  PLACEHOLDER  pixel md5 starts 532b4d (ScentSplit "No image is available") or, flattened on white at 24x16 grey,
               within 1.5 mean grey levels of it (real bottles sit at 3.6+)
  DUP          exact RGBA pixel hash already used by a different fragrance (known same-product pairs are allowed)
  BOX          the cutout is wider than tall or has more than one object (REJECT); WARN when it fills >88% of its
               bounding box (a boxed bottle does, so does a slim flat flask: look at the sheet). Packaging
               beside the bottle still needs the eye.
"""
import sys, os, glob, hashlib, collections, base64
import numpy as np
from PIL import Image

PLACEHOLDER_MD5 = "532b4d"
PLACEHOLDER_REF = np.frombuffer(base64.b64decode(
    "//////////////Tp5vL//////////////////////////b2ShK/9/////////////////////////LSHd6P9/////////////////////////LSHd6T9"
    "///////////////////////69c+1p8T2+f/////////////////////o2tXPzNPX4/7////////////////////n2bSMibXV4f7/////////////////"
    "///o2rWHirPV4f7////////////////////o2rWJlLfV4v7////////////////////o2NbS0dTV4/7////////////////////ozsnJysfL4v7/////"
    "///////////////p1s/Ozc/V4/7////////////////////p1tDQ0M/U4//////////////////////p18nFyMvV4/7////////////////////r29fX"
    "19jZ5f7////////////////////79/f39/f3+v//////////"), dtype=np.uint8).reshape(16, 24).astype(np.int16)
SAME_PRODUCT = [{"burberry/female/burberry-her.png", "burberry/female/burberry-women.png"},
                {"gucci/female/flora-by-gucci-gorgeous-gardenia.png", "gucci/female/flora-gorgeous-gardenia.png"},
                {"gucci/male/gucci-guilty-eau-de-toilette-intense-pour-homme.png", "gucci/male/gucci-guilty-intense-pour-homme.png"},
                {"mercedes-benz/male/mercedes-benz-intense.png", "mercedes-benz/male/mercedes-benz-man-intense.png"},
                {"adidas/female/adidas-floral-dream.png", "adidas/female/floral-dream.png"}]

def looks_like_placeholder(im):
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    g = np.array(bg.convert("L").resize((24, 16), Image.BILINEAR), dtype=np.int16)
    return np.abs(g - PLACEHOLDER_REF).mean() <= 1.5

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
    only = [os.path.relpath(os.path.abspath(a), os.path.abspath(root)) for a in sys.argv[1:] if not os.path.isdir(a)]
    files = sorted(os.path.relpath(p, root) for p in glob.glob(os.path.join(root, "**/*.png"), recursive=True))
    files = [f for f in files if "/" in f]   # house/gender/slug.png only
    md5 = {}   # hashes only; images are reopened one at a time below
    for f in files:
        with Image.open(os.path.join(root, f)) as im: md5[f] = hashlib.md5(im.convert("RGBA").tobytes()).hexdigest()
    by = collections.defaultdict(set)
    for f, m in md5.items(): by[m].add(f)
    bad = 0
    for f in (only or files):
        if f not in md5: bad += 1; print("REJECT", f, "not a house/gender/slug.png under", root); continue
        m = md5[f]; why = []
        with Image.open(os.path.join(root, f)) as src: im = src.convert("RGBA")
        if m.startswith(PLACEHOLDER_MD5) or looks_like_placeholder(im): why.append("PLACEHOLDER")
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
