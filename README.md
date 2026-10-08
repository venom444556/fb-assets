# fb-assets
Bottle-only transparent PNG cutouts used by the FragranceBroker Discord cards.

## Catalog layout (pilot)
`catalog.tsv` lists houses. Each house has `<house-slug>/index.tsv` with one row per fragrance
(slug, fragrance, concentration, gender, list, fragrantica_url, image_path, source_url, hosted_raw_url, qc_status).
Planned image path: `<house-slug>/<male|female|unisex>/<slug>.png`. House, name and gender come from a light
Fragrantica check; no Fragrantica images are used. `qc_status`: `pending` (no image yet), `legacy-flat-live`
(passed host QC, still served from the flat path), later `passed`/`failed`.
