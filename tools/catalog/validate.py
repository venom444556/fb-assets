"""validate.py SEED.tsv RAW.tsv SEGMENT -> prints one-line verdict and writes RAW.ok.tsv (house,fragrance,gender,fragrantica_url)
RAW columns: fragrance<TAB>gender<TAB>url (gender as Fragrantica words or male/female/unisex)."""
import csv, sys, re, difflib, unicodedata
seed, raw, seg = sys.argv[1:4]
import os
LENIENT = os.path.exists(os.path.join(os.path.dirname(raw), '..', 'names', seg + '.tsv'))  # search-matched names: slugs often drop collection prefixes
URL = re.compile(r'^https://www\.fragrantica\.com/perfume/([^/]+)/([^/]+)-(\d+)\.html$')
G = {'for women':'female','for men':'male','for women and men':'unisex','female':'female','male':'male','unisex':'unisex','women':'female','men':'male'}
def norm(s): return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
known = {}; house = None
for r in csv.DictReader(open(seed, encoding='utf-8'), delimiter='\t'):
    m = URL.match(r['fragrantica_url'])
    if m and m.group(1) == seg: known[m.group(3)] = r; house = r['house']
rows, bad = [], 0
for line in open(raw, encoding='utf-8'):
    p = [x.strip() for x in line.rstrip('\n').split('\t')]
    if len(p) < 3 or p[0].lower() in ('fragrance','name'): continue
    name, g, u = p[0], G.get(p[1].lower()), p[2]
    m = URL.match(u)
    if not (m and g and name and m.group(1) == seg): bad += 1; continue
    # name must resemble the url slug (guards against invented urls)
    if difflib.SequenceMatcher(None, norm(name), norm(m.group(2))).ratio() < 0.6: bad += 1; continue
    rows.append((name, g, u, m.group(3)))
ids = {}
for r in rows: ids.setdefault(r[3], r)
overlap = [r for i, r in ids.items() if i in known]
agree = sum(1 for r in overlap if known[r[3]]['gender'] == r[1])
new = [r for i, r in ids.items() if i not in known]
missing = len(set(known) - set(ids))
house = house or (sys.argv[4] if len(sys.argv) > 4 else seg.replace('-', ' '))
with open(raw.replace('.tsv', '.ok.tsv'), 'w', encoding='utf-8') as f:
    f.write('house\tfragrance\tgender\tfragrantica_url\n')
    for r in new: f.write(f'{house}\t{r[0]}\t{r[1]}\t{r[2]}\n')
rate = agree / len(overlap) if overlap else None
print(f'{seg}\tlisted={len(ids)}\tbad={bad}\tknown={len(known)}\toverlap={len(overlap)}\tagree={agree}\tnew={len(new)}\tseed_not_listed={missing}\t' +
      ('OK' if (rate is None or rate >= (0.9 if LENIENT else 0.95)) and (LENIENT or bad <= max(2, len(rows)//20)) else 'REJECT'))
