# Civ Italia

Italy as a Civilization-style hex map, where every tile, city and yield is computed from public
data and a published rule, with the political spectrum as the main lens. It describes votes cast
and expert scores; it makes no predictions and takes no position on parties.

- **App:** https://g95g95.github.io/Italian-Civilization/ (GitHub Pages, published from `web/` by `.github/workflows/pages.yml`). Locally: `make serve` and open http://localhost:8000.
- **Languages:** Italian and English. The app opens in the browser's language; the Italiano / English button switches. English is the source; Italian lives in `config/i18n/` (`python scripts/i18n.py extract|merge|check`).
- **Spec:** [`docs/build_spec.md`](docs/build_spec.md). **Gaps:** [`GAPS.md`](GAPS.md). **Sources:** [`SOURCES.md`](SOURCES.md).

## What is on the map

- 3,716 hexagonal tiles, 10 km across, over all 20 regions; 610 cities (ISTAT labour-market areas).
- Ten votes at comune level: Camera 2018 and 2022, European Parliament 2019 and 2024, and the
  referendums of 2016 (April and December), 2020, 2022, 2025 and 2026.
- Political lenses: ideology (Chapel Hill Expert Survey left–right, vote-weighted), economic and
  social axes, leading list, coalition margin, turnout, any list's share, swing between two votes,
  referendum Yes share and turnout.
- Land and people: income (Gold), graduates (Science), industrial jobs (Production), farmland
  (Food), terrain, age, foreign residents, employment, density, earthquakes, landslide and flood hazard.
- City view: government, districts, citizens, wonders, election history, advisors.
- Explorer: any two columns for all 7,894 comuni, as a scatter plot and a sortable table linked to the map.

## Build

```bash
pip install -r requirements.txt
make all        # download -> crosswalk -> grid -> elections -> political layer -> socio-economic -> web export
make test       # the six phase gates
```

Each phase ends with its gate in `tests/test_gates.py`:

| Phase | Gate | Status |
|---|---|---|
| 1 Skeleton | every 2016–2026 comune code resolves to a current polygon, zero unmatched | passes |
| 2 Grid | tile residents sum to the ISTAT national total within 0.1% | passes (exact) |
| 3 Elections | national list totals match the Interior Ministry within 0.1% | passes; Camera 2022 has two small lists outside 0.1% (GAPS.md) |
| 4 Political layer | coverage reported per tile, no list scored by hand | passes |
| 5 Socio-economic | each column's national total matches the source's published figure | passes |
| 6 Interface | loads in under 3 s on an emulated mid-range phone; every number has a source | passes (≈2.3 s) |

Raw downloads (about 1.5 GB) are not in git: `scripts/download.py` fetches them from the URLs in
`config/downloads.tsv` and records a SHA-256 for each in `data/raw/MANIFEST.csv`.
