#!/usr/bin/env python3
"""Copy house-sourced notes from notes.tsv into the notes_* columns of lookup.tsv.

notes.tsv stays the feed (one row per checked fragrance, with source URL). lookup.tsv gets the same
seven columns next to image_path so one file carries picture and notes. Rows are matched by
fragrantica_url; rows without house notes get empty columns. Every other column and the row order
are kept as they are. Run from the repo root after notes.tsv changes: python3 tools/catalog/notes_to_lookup.py
"""
import csv, sys
csv.field_size_limit(10**9)
NOTE_COLS = ['notes_top', 'notes_heart', 'notes_base', 'notes_unlayered',
             'notes_source_type', 'notes_source_url', 'notes_checked_on']
clean = lambda v: ' '.join((v or '').split())   # no tabs or newlines inside a TSV cell

notes = {r['fragrantica_url']: r for r in csv.DictReader(open('notes.tsv', encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE)}
rd = csv.DictReader(open('lookup.tsv', encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE)
hdr = [c for c in rd.fieldnames if c not in NOTE_COLS] + NOTE_COLS
rows = list(rd); filled = 0
for r in rows:
    n = notes.get(r['fragrantica_url'])
    for c in NOTE_COLS: r[c] = clean(n[c]) if n else ''
    filled += bool(n)
with open('lookup.tsv', 'w', encoding='utf-8', newline='') as f:
    f.write('\t'.join(hdr) + '\n')   # plain join: cells hold no tabs, and quotes stay exactly as written
    for r in rows: f.write('\t'.join(r[c] or '' for c in hdr) + '\n')
missing = len(set(notes) - {r['fragrantica_url'] for r in rows})
print('rows', len(rows), 'with house notes', filled, 'notes rows not in lookup', missing)
sys.exit(1 if missing else 0)
