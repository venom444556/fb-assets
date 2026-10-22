#!/usr/bin/env python3
"""Fill the notes columns of lookup.tsv.

notes_*       house-sourced notes, copied from notes.tsv (the feed, with source URL per row).
seed_notes_*  the notes from the original seed dump (Fragrantica export), kept as a fallback for
              rows without house notes. House notes win when present.

Rows are matched by fragrantica_url; every other column and the row order are kept as they are.
Run from the repo root after notes.tsv changes:
  python3 tools/catalog/notes_to_lookup.py                    # house notes; seed columns kept as they are
  python3 tools/catalog/notes_to_lookup.py --seed DUMP.csv    # also (re)fill seed columns from a dump
DUMP.csv is the aStyxxx/dataset_Fragrantica_perfumes export (url, notes_top/middle/base/flat as Note:weight|...).
"""
import csv, re, sys
csv.field_size_limit(10**9)
NOTE_COLS = ['notes_top', 'notes_heart', 'notes_base', 'notes_unlayered',
             'notes_source_type', 'notes_source_url', 'notes_checked_on']
SEED_COLS = ['seed_notes_top', 'seed_notes_heart', 'seed_notes_base', 'seed_notes_unlayered', 'seed_notes_source']
clean = lambda v: ' '.join((v or '').split())   # no tabs or newlines inside a TSV cell
def seed_list(v):   # "Tobacco Leaf:100|Spicy Notes:47" -> "Tobacco Leaf, Spicy Notes"
    return ', '.join(clean(re.sub(r':-?[\d.]+$', '', x)) for x in (v or '').split('|') if x.strip())

notes = {r['fragrantica_url']: r for r in csv.DictReader(open('notes.tsv', encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE)}
seed = None
if '--seed' in sys.argv:
    seed = {}
    for r in csv.DictReader(open(sys.argv[sys.argv.index('--seed') + 1], encoding='utf-8')):
        m = re.search(r'-(\d+)\.html', r['url'] or '')
        if m and any(r[k] for k in ('notes_top', 'notes_middle', 'notes_base', 'notes_flat')):
            seed[m.group(1)] = [seed_list(r['notes_top']), seed_list(r['notes_middle']), seed_list(r['notes_base']),
                                seed_list(r['notes_flat']), 'fragrantica-dump-2026-09']
rd = csv.DictReader(open('lookup.tsv', encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE)
hdr = [c for c in rd.fieldnames if c not in NOTE_COLS + SEED_COLS] + NOTE_COLS + SEED_COLS
rows = list(rd); filled = seeded = 0
for r in rows:
    n = notes.get(r['fragrantica_url'])
    for c in NOTE_COLS: r[c] = clean(n[c]) if n else ''
    filled += bool(n)
    if seed is not None:
        m = re.search(r'-(\d+)\.html', r['fragrantica_url'] or '')
        s = seed.get(m.group(1)) if m else None
        for c, v in zip(SEED_COLS, s or [''] * len(SEED_COLS)): r[c] = v
    seeded += bool(r.get('seed_notes_source'))
with open('lookup.tsv', 'w', encoding='utf-8', newline='') as f:
    f.write('\t'.join(hdr) + '\n')   # plain join: cells hold no tabs, and quotes stay exactly as written
    for r in rows: f.write('\t'.join(r.get(c) or '' for c in hdr) + '\n')
missing = len(set(notes) - {r['fragrantica_url'] for r in rows})
print('rows', len(rows), 'house notes', filled, 'seed notes', seeded, 'notes rows not in lookup', missing)
sys.exit(1 if missing else 0)
