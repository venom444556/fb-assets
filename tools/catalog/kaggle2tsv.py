"""kaggle2tsv.py LOOKUP.tsv fra_perfumes.csv > rows (house,fragrance,gender,fragrantica_url) for ids not in LOOKUP"""
import csv, sys, re, unicodedata, collections
csv.field_size_limit(10**9)
U = re.compile(r'https://www\.fragrantica\.com/perfume/([^/]+)/([^/]+)-(\d+)\.html')
G = [('for women and men','unisex'),('for women','female'),('for men','male')]
def norm(s): return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
have = set(); segname = {}
for r in csv.DictReader(open(sys.argv[1], encoding='utf-8'), delimiter='\t'):
    have.add(r['fragrantica_id']); m = U.match(r['fragrantica_url'])
    if m: segname.setdefault(m.group(1), r['house'])
out = csv.writer(sys.stdout, delimiter='\t', lineterminator='\n'); out.writerow(['house','fragrance','gender','fragrantica_url'])
stats = collections.Counter(); brands = collections.defaultdict(collections.Counter); pending = []
for r in csv.DictReader(open(sys.argv[2], encoding='utf-8')):
    u = r['url'].strip(); m = U.match(u)
    if not m or m.group(3) in have: continue
    have.add(m.group(3))
    name = ' '.join(r['Name'].split()); g = None
    for suf, gg in G:
        if name.endswith(suf) and r['Gender'].strip() == suf: name = name[:-len(suf)].strip(); g = gg; break
    if not g: stats['nogender'] += 1; continue
    words = name.split(' '); target = norm(m.group(2)); fr = br = None
    for k in range(1, len(words)):
        if norm(' '.join(words[:k])) == target: fr, br = ' '.join(words[:k]), ' '.join(words[k:]); break
    if fr: stats['parsed'] += 1; brands[m.group(1)][br] += 1
    else: stats['fallback'] += 1; fr = m.group(2).replace('-', ' ')
    pending.append((m.group(1), fr, g, u))
for seg, fr, g, u in pending:
    house = segname.get(seg) or (brands[seg].most_common(1)[0][0] if brands[seg] else seg.replace('-', ' '))
    out.writerow([house, fr, g, u])
print(dict(stats), file=sys.stderr)
