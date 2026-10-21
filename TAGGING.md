# Catalog tagging rule

The standing rule for tagging every fragrance in the catalog, and for adding fragrances as they launch or
leave the market. FragranceBroker follows it today on these files; the Scentible server takes it over unchanged
when the catalog moves into its database (the `fragrance` table gets the same four fields).

## The four tags

Every catalog row carries exactly one value of each.

| Tag | Values | Comes from |
| --- | --- | --- |
| `house_tier` | `designer`, `niche`, `ultra_niche`, `indie`, `mass`, `unrated` | `house-tiers.tsv`, by house |
| `market_status` | `active`, `upcoming`, `discontinued`, `likely_discontinued`, `unknown` | `market-status.tsv`, by fragrance |
| `photo` | `real`, `none` | `lookup.tsv` image_path and `accepted-gaps.tsv` |
| `tags` | comma list of the flags that are not the default: `upcoming`, `discontinued`, `likely_discontinued`, `no_photo` | derived |

`tags.tsv` holds the result, one row per `lookup.tsv` row. It is generated, never edited by hand:
`python3 -I tools/catalog/tags.py .` writes it and `--check` fails when it is stale or an input breaks a rule.
Seller tiers (house, authorized, grey, membership) are a different thing and stay in `retailers.tsv`.

## Market status

One row per fragrance in `market-status.tsv`: `fragrantica_url, house, fragrance, status, source_type,
source_url, checked_on, note`. A fragrance with no row is `unknown`. Every row must name its evidence.

| Status | Means | Evidence needed |
| --- | --- | --- |
| `active` | On sale now | A house page or an authorized-seller listing for this exact fragrance and concentration, seen on `checked_on` |
| `upcoming` | Announced, not yet sold | House or trade-press announcement with a launch date |
| `discontinued` | No longer made | The house says so, or it is gone from the house site and the house sells a successor or other editions only, or a dated limited edition whose run ended |
| `likely_discontinued` | Probably gone, not proven | Missing from the house site with no explicit confirmation, or no in-stock offer at any house or authorized seller for 180 days |
| `unknown` | Not checked yet | none |

Rules:
1. Evidence order, strongest first: `owner` (the owner's ruling), `house_site`, `retailer_feed` (house or
   authorized sellers in `retailers.tsv`), `notes_check` (the house-notes research), `press`. A stronger source
   replaces a weaker one; between equals the newer `checked_on` wins.
2. Grey and membership sellers never prove a fragrance is active (grey stock outlives production).
3. Discontinued is per concentration. Sauvage Elixir going off market says nothing about Sauvage EDT.
4. A reformulation or rebottling is not discontinuation. A re-release under the same name is `active` and shows
   the current bottle; when the house gives it a new name or year, it is a new catalog row.
5. A discontinued fragrance stays in the catalog forever. Watchlists, collections and price history keep pointing
   at it.
6. `likely_discontinued` turns into `discontinued` only with evidence from the table above, and back into
   `active` the moment a house or authorized offer is in stock again.
7. Never delete a row from `market-status.tsv` to change a status; overwrite the row with the newer evidence.

## Photo

`photo=real` when `image_path` points at a passed cutout. `photo=none` when `image_path` is empty, is
`placeholders/no-image-available.png`, or the row is in `accepted-gaps.tsv`. Cards and the app show the
placeholder for `none`; they never borrow another concentration's picture. A row leaves `accepted-gaps.tsv` only
when a real cutout passes the bottle QA workflow; `tags.py` then flips it to `real` on the next run.

## House tier

Every house in `lookup.tsv` has exactly one row in `house-tiers.tsv`. A house that appears for the first time gets
`unrated` until someone assigns it; `tags.py` prints the `unrated` count. Tiers describe the house, not the price of one bottle.

## Ingest: a new fragrance launches

1. Add the row to `lookup.tsv` (house, fragrance, concentration, gender, source URL; image_path empty). Never
   rebuild the file with `build.py`; append and keep existing rows verbatim.
2. New house: add it to `house-tiers.tsv` (or leave it `unrated` for review).
3. `market-status.tsv`: `upcoming` with the announced date, or `active` once a house or authorized seller lists it.
4. Photo: the row starts as `photo=none` and goes through the normal bottle pass and QA.
5. Run `tools/catalog/tags.py .`, then `--check`, and commit the inputs and `tags.tsv` together.

## Ingest: a fragrance goes off market

1. Write or overwrite its `market-status.tsv` row with `discontinued` or `likely_discontinued`, the source and the date.
2. Change nothing else: the catalog row, picture, notes and price history stay.
3. Run `tags.py`, then `--check`, and commit.

## Weekly sweep (the server's job once Scentible runs)

- Launches: read the house sites and authorized-seller feeds for products not in the catalog; add them per above.
- Off market: for every `active` fragrance, if no house or authorized seller has listed it in stock for 180 days,
  set `likely_discontinued` (source `retailer_feed`). Recheck `likely_discontinued` rows against the house site
  once a month.
- `upcoming` rows past their launch date with a live listing become `active`.
- Every change keeps its source and date, so any tag can be traced back.

## Where the first pass came from (2026-10-21)

- `photo`: 14,060 rows have no real photo (all of them in `accepted-gaps.tsv`); 113,402 have one.
- `market_status`: seeded from the house-notes check (most popular first, about 20,000 fragrances so far) with
  `tools/catalog/market_from_notes.py . <notes work folder>`: 2,414 discontinued, 444 likely discontinued, 8,721
  active, the rest unknown. Rerun it as the notes check moves down the list; it only replaces its own rows.
- The catalog key is still the Fragrantica URL. When our own IDs replace it, the key column in `market-status.tsv`
  and `tags.tsv` changes with the same mapping and nothing else does.
