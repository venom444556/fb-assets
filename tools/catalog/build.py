"""Merge Fragrantica rows into fb-assets house indexes.
usage: build.py REPO SOURCE.tsv[...]   source cols: house, fragrance, gender, fragrantica_url
Existing index rows are kept untouched; new rows are appended as pending."""
import csv, sys, os, re, unicodedata, collections
repo = sys.argv[1]
COLS = ['slug','fragrance','concentration','gender','fragrantica_url','image_path','source_url','hosted_raw_url','qc_status']
# Fragrantica has no concentration field; it is only known when the name (or URL slug) states it.
CONC = [(r'\bextrait(?: de parfum)?\b', 'Extrait de Parfum'), (r'\b(?:eau de parfum|edp)\b', 'Eau de Parfum'),
        (r'\b(?:eau de toilette|edt)\b', 'Eau de Toilette'), (r'\b(?:eau de cologne|edc)\b', 'Eau de Cologne'),
        (r'\beau fra[iî]che\b', 'Eau Fraiche'), (r'\b(?:body|hair) mist\b', None), (r'\b(?:perfume oil|attar)\b', 'Perfume Oil'),
        (r'(?<!\ble )(?<!\bla )(?<!\bmon )(?<!\bun )\bparfum$', 'Parfum'), (r'\bcologne$', 'Cologne')]
def concentration(name, url):
    for text in (name, re.sub(r'-\d+\.html$', '', url.rsplit('/', 1)[-1]).replace('-', ' ')):
        t = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower().strip()
        for pat, val in CONC:
            m = re.search(pat, t)
            if m: return val or m.group(0).title()
    return ''
URL = re.compile(r'^https://www\.fragrantica\.com/perfume/([^/]+)/[^/]+-(\d+)\.html$')
def ascii_slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode().lower()
    s = re.sub(r"['’`]", '', s).replace('&', ' and ')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')
def fid(u):
    m = URL.match(u or ''); return m.group(2) if m else None
# existing catalog
cat = {}
with open(os.path.join(repo,'catalog.tsv'), encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'): cat[r['house_slug']] = r['house']
# Fragrantica renamed these designer URLs; fold the old segment into the current house
ALIAS = {'Paco-Rabanne': 'rabanne', 'Frederic-Malle': 'frederic-malle-editions-de-parfums'}
seg2slug = dict(ALIAS)   # fragrantica designer segment -> house slug, learned from existing rows
idx = {}
for hs in cat:
    p = os.path.join(repo, hs, 'index.tsv'); rows = []
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f: rows = list(csv.DictReader(f, delimiter='\t'))
    idx[hs] = rows
    for r in rows:
        m = URL.match(r['fragrantica_url'])
        if m: seg2slug[m.group(1)] = hs
added = collections.Counter(); skipped = collections.Counter()
seen = {fid(x['fragrantica_url']) for rows in idx.values() for x in rows}
for src in sys.argv[2:]:
    with open(src, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            u = r['fragrantica_url'].strip(); m = URL.match(u)
            g = r['gender'].strip().lower()
            name = ' '.join(r['fragrance'].split()); house = ' '.join(r['house'].split())
            if not m or g not in ('male','female','unisex') or not name or not house:
                skipped['invalid'] += 1; continue
            seg = m.group(1)
            hs = seg2slug.get(seg) or seg.lower()
            seg2slug[seg] = hs
            if hs not in cat: cat[hs] = house; idx[hs] = []
            rows = idx[hs]
            if m.group(2) in seen:
                skipped['dup'] += 1; continue
            seen.add(m.group(2))
            slug = ascii_slug(name) or 'f'
            if any(x['slug'] == slug for x in rows): slug = f'{slug}-{m.group(2)}'
            rows.append(dict(slug=slug, fragrance=name, concentration='', gender=g, fragrantica_url=u,
                             image_path='', source_url='', hosted_raw_url='', qc_status='pending'))
            added[hs] += 1
# write
lookup = []
for hs, rows in idx.items():
    os.makedirs(os.path.join(repo, hs), exist_ok=True)
    for r in rows:
        r.pop('list', None)
        r['concentration'] = {'EDP': 'Eau de Parfum', 'EDT': 'Eau de Toilette', 'EDC': 'Eau de Cologne'}.get(r.get('concentration', ''), r.get('concentration', ''))
        if not r.get('concentration'): r['concentration'] = concentration(r['fragrance'], r['fragrantica_url'])
    keep = rows[:len(rows)-added[hs]]; new = sorted(rows[len(keep):], key=lambda x: x['fragrance'].lower())
    rows = keep + new; idx[hs] = rows
    with open(os.path.join(repo, hs, 'index.tsv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, COLS, delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(rows)
    for r in rows: lookup.append((cat[hs], r['fragrance'], r['concentration'], r['gender'], r['fragrantica_url'], r['image_path']))
with open(os.path.join(repo,'catalog.tsv'), 'w', encoding='utf-8', newline='') as f:
    f.write('house\thouse_slug\tfragrances\tmale\tfemale\tunisex\n')
    for hs, rows in sorted(idx.items(), key=lambda kv: cat[kv[0]].lower()):
        c = collections.Counter(r['gender'] for r in rows)
        f.write(f"{cat[hs]}\t{hs}\t{len(rows)}\t{c['male']}\t{c['female']}\t{c['unisex']}\n")
lookup.sort(key=lambda t: (t[0].lower(), t[1].lower()))
with open(os.path.join(repo,'lookup.tsv'), 'w', encoding='utf-8', newline='') as f:
    f.write('house\tfragrance\tconcentration\tgender\tfragrantica_url\timage_path\n')
    for t in lookup: f.write('\t'.join(t) + '\n')
print('houses', len(idx), 'rows', len(lookup), 'added', sum(added.values()), dict(skipped))
