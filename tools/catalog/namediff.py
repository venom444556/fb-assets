import csv, sys, re, unicodedata, os
look, ndir = sys.argv[1:3]
U = re.compile(r'https://www\.fragrantica\.com/perfume/([^/]+)/([^/]+)-(\d+)\.html')
def n(s): return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
have = {}
for r in csv.DictReader(open(look, encoding='utf-8'), delimiter='\t'):
    m = U.match(r['fragrantica_url'])
    if m: have.setdefault(m.group(1), set()).update({n(r['fragrance']), n(m.group(2))})
out = open(os.path.join(ndir, 'missing.tsv'), 'w', encoding='utf-8')
for f in sorted(os.listdir(ndir)):
    if f == 'missing.tsv' or not f.endswith('.tsv'): continue
    seg = f[:-4]; H = have.get(seg, set()); miss = []
    for line in open(os.path.join(ndir, f), encoding='utf-8'):
        p = line.rstrip('\n').split('\t'); name = p[0].strip()
        if not name: continue
        if n(name) in H: continue
        miss.append((name, p[1].strip() if len(p) > 1 else ''))
    print(seg, 'listed', sum(1 for _ in open(os.path.join(ndir, f))), 'table', len(H)//1, 'missing', len(miss))
    for name, g in miss: out.write(f'{seg}\t{name}\t{g}\n')
