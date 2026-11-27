# UNESCO World Heritage List

Download date: 2026-11-27. Publisher: UNESCO World Heritage Centre. Licence: the feed states "Copyright 2026 UNESCO World Heritage Centre". UNESCO WHC allows dataset reuse with attribution for non-commercial use (see https://whc.unesco.org/en/syndication), but I could not re-check that page because it is behind a Cloudflare challenge.

## Access problems
`https://whc.unesco.org/en/list/xml/`, `/en/list/json/`, `/en/list/xls/`, `/en/list/kml/` and `/en/syndication/` all return **HTTP 403 with a Cloudflare "Just a moment…" challenge**, whatever User-Agent is sent. Only the RSS and GeoRSS feeds respond.

## Files
| File | URL | Vintage | Notes |
|---|---|---|---|
| `whc_list_georss.xml` (1.4 MB) | https://whc.unesco.org/en/list/georss/ | Live list, lastBuildDate 26 Nov 2026, **1,273 properties** | Fields: `title`, `description` (HTML with short description), `link` (https://whc.unesco.org/en/list/{id_no}), and `georss:where` (MultiPoint, "lat lon"). **There is no country field. The coordinates are broken in the feed: every item has the same point (19.3639 45.5983).** Use the file only for the current list of ids and names. |
| `whc-sites-2023_github-mirror.csv` (6.0 MB) | https://github.com/alfonsoledesmaa/whc-sites, file `src/handlers/whc-sites.csv`, commit b10b161c8212d68e523491566140a1d4025d92e5 (2024-11-20) | Official UNESCO "whc-sites" export, **vintage 2023** (1,199 sites, latest inscription 2023) | A mirror of UNESCO's own export (whc-sites-2023.xls/csv). **59 Italian sites** (`iso_code` contains `it`). |

## Columns of the mirror CSV (UTF-8 with BOM)
- `unique_number`, `id_no` (the WHC id; joins to the georss link), `rev_bis`
- `name_en` (and the other languages), `short_description_*`, `justification_*`
- `date_inscribed`, `secondary_dates`, `danger`, `date_end`, `danger_list`
- **`longitude`, `latitude`**: one representative point, WGS84
- `area_hectares`
- `C1`..`C6`, `N7`..`N10`, `criteria_txt`
- `category` (Cultural/Natural/Mixed), `category_short`
- `states_name_*`, `region_*`
- `iso_code`: comma-separated ISO2 codes. Transboundary sites list several, e.g. `it,ch`
- `udnp_code`, `transboundary` (0/1)

## Italian sites missing from the 2023 mirror (present in the live georss, without usable coordinates)
- 1708 Via Appia. Regina Viarum (2024)
- 1730 Funerary Tradition in the Prehistory of Sardinia – The domus de janas (2025)
- 1762 The system of Italian-style condominio theatres of the 18th and 19th centuries in Central Italy (2026)

These need coordinates from another source, e.g. OSM `ref:whc` or a manual lookup. overpass-api.de was unreachable during this session.

Places are located by coordinates (one point per site). Serial sites such as Longobards, Dolomites or Via Appia have one representative point only.
