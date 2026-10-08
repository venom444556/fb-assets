# Catalog build (Fragrantica lookup table)

Rebuilds `catalog.tsv`, `<house>/index.tsv` and `lookup.tsv`. Rows are merged by Fragrantica ID; the first source
to supply an ID wins, and existing rows (the pilot rows with images) are never changed.

Sources, in merge order:
1. `seed.tsv`: a Fragrantica export dated 2026-09-26, `perfumes_actual.csv` from
   github.com/aStyxxx/dataset_Fragrantica_perfumes. Convert with `ds2tsv.py perfumes_actual.csv > seed.tsv`.
2. Live Fragrantica designer listings, one file per designer segment in a raw folder
   (`name<TAB>gender<TAB>url`), collected politely one page at a time. `validate.py` checks each one against
   the base: URL shape, a name that resembles the URL slug, and at least 95% gender agreement on rows already
   known. Houses whose page drops links are diffed by name (`namediff.py` over `names/<Segment>.tsv`), their
   links are found by search, and they are validated more leniently.
3. `kaggle-new.tsv`: the Kaggle "Fragrantica.com Fragrance Dataset" (2024), `fra_perfumes.csv`.
   Convert with `kaggle2tsv.py lookup.tsv fra_perfumes.csv > kaggle-new.tsv` (only IDs not already present).

`base.tsv` = `seed.tsv` plus the data rows of `kaggle-new.tsv`.

Run: `tools/catalog/round.sh . DATA_DIR RAW_DIR`. It rewrites `crawl/progress.tsv`, one row per house checked
live, so a crawl can resume with the houses that are missing from it. `build.py` folds renamed Fragrantica
houses (`ALIAS`) and never writes an ID twice.
