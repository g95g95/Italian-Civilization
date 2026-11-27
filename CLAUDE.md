# Civ Italia — working rules

A Civilization-style hex map of Italy computed entirely from public data, with the political
spectrum as the main lens. One static web app (`web/`), built by the Python pipeline in `scripts/`.
The spec is `docs/build_spec.md`.

## Working rules (from the spec)

- Never skip a region, election or dataset silently. If something cannot be done, stop and write it in `GAPS.md` with the reason.
- Never invent, estimate or hand-tune a number. A missing value stays missing and is drawn as missing.
- Every processed file has a row in `SOURCES.md`: URL, download date, licence, and the script that produced it (`make sources` regenerates it from `config/sources.json` and `data/raw/MANIFEST.csv`).
- Every phase ends by running its gate as an automated test. A failing gate blocks the next phase.
- Raw downloads are read-only. All transformations are scripts, so the whole build reruns from scratch.
- Joins are on ISTAT codes through the crosswalk, never on comune names. (The one documented exception is the ministry-label lookup in `scripts/names.py`; see GAPS.md.)
- Political neutrality: the app describes votes and expert scores. No labels such as "extreme" or "moderate" unless they are the survey's own category names.
- Ask before any choice that changes what a number means (a new scale, a new weighting, dropping a list).

## Layout

```
config/            hand-maintained inputs: list -> CHES parties, name aliases, ISTAT changes, sources, columns, downloads
data/raw/          downloads (not in git); MANIFEST.csv lists URL + SHA-256 for each
data/processed/    pipeline outputs (not in git, except what web/data needs)
scripts/           one script per step (see Makefile)
tests/test_gates.py  the six phase gates; tests/load_time.js the phone load test
web/               index.html + app.js + data/*.json (the deliverable)
```

## Commands

- `make all` — download what is missing, run every phase and its gate, export `web/data/`.
- `make test` — all gates.  `pytest -m phase3` — one gate.
- `make serve` — open the app at http://localhost:8000.

## Pipeline order

`download.py` → `crosswalk.py` (P1) → `grid.py`, `socio.py` (P2) → `elections.py`, `political.py` (P3–4)
→ `terrain.py`, `layers.py`, `socio.py` (P5) → `export.py` (P6).

## Conventions

- Comune codes are six-character strings (`"001272"`). Always read CSVs with `dtype={"code": str, "unit": str}`.
- Election results are keyed by *unit*: the `|`-joined set of current comuni a ministry record covers.
- Counts travel to tiles with `spread.to_tiles` (by residents; `mode="area"` for areas). Rates are computed after.
- Tile coordinates: EPSG:32632; the web app uses km from the north-west corner of the tile grid.
- Python reading downloaded files: run scripts from `scripts/`; nothing executes code from `data/raw/`.
