import csv, sys
csv.field_size_limit(10**9)
w = csv.writer(sys.stdout, delimiter='\t', lineterminator='\n')
w.writerow(['house','fragrance','gender','fragrantica_url'])
for r in csv.DictReader(open(sys.argv[1], encoding='utf-8')):
    w.writerow([r['brand'], r['name'], r['gender'], r['url']])
