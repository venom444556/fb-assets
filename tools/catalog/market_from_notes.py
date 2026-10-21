#!/usr/bin/env python3
"""Fold the house-notes check results into market-status.tsv.

Usage: market_from_notes.py <assets_dir> <notes_work_dir>

Reads every shard*.jsonl / retry*.jsonl in the notes work folder (one JSON object per fragrance, keyed by
Fragrantica id) and turns what the checker found into market evidence:
  - the note says the fragrance is discontinued      -> discontinued
  - the note only guesses ("likely", "or not indexed") -> likely_discontinued
  - a house or authorized-retailer page was found    -> active
Rows written by this script carry source_type notes_check and are replaced on every run. Rows from any other
source (house_site, retailer_feed, owner, ...) are never touched, and an existing non-notes_check row for the
same fragrance wins over what this script would write.
"""
import csv, datetime, glob, json, os, re, sys

assets, work = sys.argv[1], sys.argv[2]
COLS = ['fragrantica_url', 'house', 'fragrance', 'status', 'source_type', 'source_url', 'checked_on', 'note']

def read(path):
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path, encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))

by_id = {}
for r in read(os.path.join(assets, 'lookup.tsv')):
    m = re.search(r'-(\d+)\.html$', r['fragrantica_url'])
    if m:
        by_id[m.group(1)] = r

NEG = re.compile(r"not (been )?discontinu|isn.t discontinu|still (sold|available|made|in production|listed)", re.I)
HEDGE = re.compile(r"likely|possibly|probably|may be|maybe|perhaps|appears|seems|unclear|or not (indexed|surfaced|listed|found)"
                   r"|discontinued or|discontinued\s*/\s*not|\?", re.I)

found = {}
files = sorted(glob.glob(os.path.join(work, 'shard*.jsonl')) + glob.glob(os.path.join(work, 'retry*.jsonl')))
for f in files:
    day = datetime.date.fromtimestamp(os.path.getmtime(f)).isoformat()
    for line in open(f, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            j = json.loads(line)
        except ValueError:
            continue
        row = by_id.get(str(j.get('id', '')))
        if not row:
            continue
        note = (j.get('note') or '').replace('\t', ' ').replace('\n', ' ').strip()
        src = (j.get('source_url') or '').strip()
        if re.search('discontinu', note, re.I) and not NEG.search(note):
            status = 'likely_discontinued' if HEDGE.search(note) else 'discontinued'
        elif j.get('status') == 'verified' and j.get('source_type') in ('house_site', 'authorized_retailer') and src:
            status = 'active'
        else:
            continue
        # later files (retries) override earlier shards for the same fragrance
        found[row['fragrantica_url']] = {
            'fragrantica_url': row['fragrantica_url'], 'house': row['house'], 'fragrance': row['fragrance'],
            'status': status, 'source_type': 'notes_check', 'source_url': src,
            'checked_on': j.get('checked_on') or day, 'note': note[:300]}

path = os.path.join(assets, 'market-status.tsv')
keep = [r for r in read(path) if r['source_type'] != 'notes_check']
kept = {r['fragrantica_url'] for r in keep}
out = keep + [v for k, v in found.items() if k not in kept]
out.sort(key=lambda r: (r['house'].lower(), r['fragrance'].lower(), r['fragrantica_url']))
with open(path, 'w', encoding='utf-8', newline='') as fh:
    w = csv.DictWriter(fh, COLS, delimiter='\t', quoting=csv.QUOTE_NONE, quotechar=None, lineterminator='\n')
    w.writeheader()
    for r in out:
        w.writerow({c: r.get(c, '') for c in COLS})
counts = {}
for r in out:
    counts[r['status']] = counts.get(r['status'], 0) + 1
print('market-status.tsv:', len(out), 'rows', counts)
