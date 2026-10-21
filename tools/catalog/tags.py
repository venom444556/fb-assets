#!/usr/bin/env python3
"""Build tags.tsv: one row per lookup.tsv row with the catalog tags the deal cards and the app read.

Usage: tags.py <assets_dir> [--check] [--check-files]

Inputs (all side files; lookup.tsv is only read, never rewritten):
  lookup.tsv          the catalog (key: fragrantica_url until our own IDs replace it)
  house-tiers.tsv     house -> tier (house, authorized, ... see TAGGING.md)
  market-status.tsv   evidence that a fragrance is on or off the market (one row per fragrance)
  accepted-gaps.tsv   rows that show the placeholder picture by owner ruling

Output columns:
  fragrantica_url, house_tier, market_status, photo, tags
  market_status: active | discontinued | likely_discontinued | upcoming | unknown
  photo:         real | none
  tags:          comma list of the non-default flags (discontinued, likely_discontinued, upcoming, no_photo)

--check rebuilds in memory and exits 1 if tags.tsv is stale or any input breaks a rule in TAGGING.md.
--check-files also fails when a real image_path has no file (needs a full checkout, not a sparse one).
"""
import csv, os, sys

PLACEHOLDER = 'placeholders/no-image-available.png'
TIERS = {'designer', 'niche', 'ultra_niche', 'indie', 'mass', 'unrated'}
STATUSES = {'active', 'discontinued', 'likely_discontinued', 'upcoming', 'unknown'}
COLS = ['fragrantica_url', 'house_tier', 'market_status', 'photo', 'tags']

def read(path):
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))

def build(assets, check_files=False):
    errors = []
    rows = read(os.path.join(assets, 'lookup.tsv'))
    urls = {r['fragrantica_url'] for r in rows}
    tiers = {}
    for r in read(os.path.join(assets, 'house-tiers.tsv')):
        if r['tier'] not in TIERS:
            errors.append('house-tiers.tsv: unknown tier %r for %s' % (r['tier'], r['house']))
        tiers[r['house']] = r['tier']
    market = {}
    for r in read(os.path.join(assets, 'market-status.tsv')):
        if r['status'] not in STATUSES:
            errors.append('market-status.tsv: unknown status %r for %s' % (r['status'], r['fragrantica_url']))
        if r['fragrantica_url'] not in urls:
            errors.append('market-status.tsv: %s is not in lookup.tsv' % r['fragrantica_url'])
        if r['fragrantica_url'] in market:
            errors.append('market-status.tsv: %s listed twice' % r['fragrantica_url'])
        market[r['fragrantica_url']] = r['status']
    gaps = {r['fragrantica_url'] for r in read(os.path.join(assets, 'accepted-gaps.tsv'))}

    out = []
    for r in rows:
        url, img = r['fragrantica_url'], r['image_path'].strip()
        photo = 'none' if (not img or img == PLACEHOLDER or url in gaps) else 'real'
        if check_files and photo == 'real' and not os.path.exists(os.path.join(assets, img)):
            errors.append('lookup.tsv: %s points at missing file %s' % (url, img))
        status = market.get(url, 'unknown')
        tags = []
        if status in ('discontinued', 'likely_discontinued', 'upcoming'):
            tags.append(status)
        if photo == 'none':
            tags.append('no_photo')
        out.append({'fragrantica_url': url, 'house_tier': tiers.get(r['house'], 'unrated'),
                    'market_status': status, 'photo': photo, 'tags': ','.join(tags)})
    return out, errors

def render(out):
    lines = ['\t'.join(COLS)] + ['\t'.join(r[c] for c in COLS) for r in out]
    return '\n'.join(lines) + '\n'

def main():
    assets = sys.argv[1]
    check = '--check' in sys.argv[2:]
    out, errors = build(assets, '--check-files' in sys.argv[2:])
    text = render(out)
    path = os.path.join(assets, 'tags.tsv')
    if check:
        current = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
        if current != text:
            errors.append('tags.tsv is stale: run tools/catalog/tags.py %s' % assets)
    else:
        open(path, 'w', encoding='utf-8', newline='').write(text)
    for e in errors[:50]:
        print('ERROR', e, file=sys.stderr)
    counts = {}
    for r in out:
        for k in ('market_status', 'photo', 'house_tier'):
            counts[(k, r[k])] = counts.get((k, r[k]), 0) + 1
    print('tags.tsv: %d rows' % len(out))
    for k in sorted(counts):
        print('  %s=%s %d' % (k[0], k[1], counts[k]))
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
