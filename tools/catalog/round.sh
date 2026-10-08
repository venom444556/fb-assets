#!/bin/bash
# Validate every live listing in RAW_DIR, merge the good ones, rewrite crawl/progress.tsv.
# usage: tools/catalog/round.sh REPO DATA_DIR RAW_DIR
#   DATA_DIR/seed.tsv        export rows   (ds2tsv.py perfumes_actual.csv)
#   DATA_DIR/kaggle-new.tsv  Kaggle rows   (kaggle2tsv.py lookup.tsv fra_perfumes.csv)
#   DATA_DIR/base.tsv        seed.tsv + kaggle-new.tsv rows (what live listings are diffed against)
#   RAW_DIR/<Segment>.tsv    live listing: name<TAB>gender<TAB>url, one file per Fragrantica designer segment
set -e
R=$1; D=$2; W=$3; T=$(dirname "$0")
mkdir -p "$R/crawl"; P=$R/crawl/progress.tsv
echo -e "segment\tdesigner_url\tstatus\tlisted\tseed_known\tseed_agree\tnew_added\tseed_not_listed\tchecked" > "$P"
oks=()
for f in "$W"/*.tsv; do case $f in *.ok.tsv) continue;; esac; seg=$(basename "$f" .tsv)
  v=$(python3 -I "$T/validate.py" "$D/base.tsv" "$f" "$seg") || continue
  st=$(echo "$v"|awk -F'\t' '{print $NF}'); g(){ echo "$v"|tr '\t' '\n'|grep "^$1="|cut -d= -f2; }
  [ "$st" = OK ] && oks+=("${f%.tsv}.ok.tsv") && st=done || st=rejected
  echo -e "$seg\thttps://www.fragrantica.com/designers/$seg.html\t$st\t$(g listed)\t$(g known)\t$(g agree)\t$(g new)\t$(g seed_not_listed)\t$(date -r "$f" +%F)" >> "$P"
done
python3 -I "$T/build.py" "$R" "$D/seed.tsv" "${oks[@]}" "$D/kaggle-new.tsv"
