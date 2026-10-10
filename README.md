# fb-assets
Bottle-only transparent PNG cutouts used by the FragranceBroker Discord cards.

## Catalog layout (pilot)
`catalog.tsv` lists houses. Each house has `<house-slug>/index.tsv` with one row per fragrance
(slug, fragrance, concentration, gender, fragrantica_url, image_path, source_url, hosted_raw_url, qc_status).
Planned image path: `<house-slug>/<male|female|unisex>/<slug>.png`. House, name and gender come from a light
Fragrantica check. Images may come from any source: fimgs.net (Fragrantica's image host, keyed by Fragrantica ID), Luckyscent brand pages and retailer product feeds. `qc_status`: `pending` (no image yet), `legacy-flat-live`
(passed host QC, still served from the flat path), later `passed`/`failed`.

## Inspection
`python3 -I tools/inspect_bottles.py . --sheet contact_sheet.png` checks every nested cutout (size/mode, transparent
corners, no solid pixels on a canvas edge, centering, 80-95% height, lost-cap "top-gap") and rebuilds
`contact_sheet.png`. FAIL exits non-zero. WARN means look at the sheet; top-gap also fires on natural shapes
(antlers, bevelled caps). Rerun after every image change and eyeball the sheet.

## Fragrantica lookup table (2026-10-08)
Every house in Fragrantica's catalog that we have seen gets a `<house-slug>/index.tsv`; new rows are `qc_status=pending`
with empty image columns. `lookup.tsv` is the same data as one flat file (house, fragrance, concentration, gender, fragrantica_url,
image_path). Fragrantica has no concentration field, so concentration is filled only where the name states it. Sources, merged by Fragrantica ID: a Fragrantica export dated 2026-09-26
(github.com/aStyxxx/dataset_Fragrantica_perfumes), the Kaggle "Fragrantica.com Fragrance Dataset" (2024), and live
Fragrantica designer listings, which are logged per house in `crawl/progress.tsv` so a crawl can resume.
