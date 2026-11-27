# Civ Italia — build spec

Nov 27, 2026 · @Giulio bonelli

## Goal and scope

Build a Civilization-style hex map of Italy where every tile, city and yield is computed from public data, with the political spectrum as the main lens.

The finished product is one static web app (no server) that opens on the political map and lets the reader switch lenses, open a city, and plot any column against any other.

**In scope**

- All 20 regions, on one hex grid, from open data only.
- National elections for the Camera (lower house) 2018 and 2022, European elections 2019 and 2024, and national referendums from 2016 onward.
- Socio-economic layers that help explain the vote: income, education, age, employment, foreign residents, terrain.
- Every number traceable to a named source file and a published rule.

**Out of scope**

- Predictions, polls, or any opinion on parties. The map describes votes cast, nothing else.
- Municipal and regional elections (different party systems, too many local lists) in the first version.
- Gameplay. It looks like Civilization; nobody takes turns.

## Data sources

The comune (municipality, about 7,900 of them) is the base unit; every dataset joins on the six-digit ISTAT comune code.

Sources marked *used* were downloaded and checked for the prototype. The others are named from general knowledge: confirm each URL, licence and vintage before building on it.

| Layer | Source | Unit | Status and quirks |
| --- | --- | --- | --- |
| Camera 2022 results | [onData, elezioni-politiche-2022](https://github.com/ondata/elezioni-politiche-2022) (scraped from Eligendo, the Interior Ministry archive) | comune × list | Used. Valle d'Aosta is absent. Candidate-only votes sit in a separate column. |
| Comune boundaries | [openpolis, geojson-italy](https://github.com/openpolis/geojson-italy) (from ISTAT) | comune polygon | Used. Current boundaries, so 2022 codes need a crosswalk. |
| Party positions | [Chapel Hill Expert Survey 2024](https://www.chesdata.eu/ches-europe/) | party | Used. Column `lrgen`, 0 = far left, 10 = far right. Ten Italian parties. |
| Other elections | Eligendo open data | comune × list | To confirm. Camera 2018, European 2019 and 2024, referendums. |
| Population, age, education, jobs | ISTAT permanent census | comune | To confirm. |
| Income | MEF (finance ministry) tax-return statistics | comune | To confirm. Declared income only. |
| Population grid | ISTAT 1 km grid or GHSL (EU settlement layer) | 1 km cell | To confirm. Needed to place votes where people live. |
| Elevation | Tinitaly digital elevation model | 10 m raster | To confirm. |
| Land cover | Copernicus CORINE | 100 m raster | To confirm. |
| Hazards | INGV (earthquakes), ISPRA (floods, landslides) | point, polygon | To confirm. |
| Labour-market areas | ISTAT sistemi locali del lavoro | group of comuni | To confirm. These are the "cities". |
| Infrastructure | OpenStreetMap, MIUR (universities) | point | To confirm. |

## Grid and reconciliation

Everything lands on one pointy-top hex grid, 10 km flat to flat, in UTM zone 32N (EPSG:32632, a metric projection). That gives about 3,700 land tiles. A 25 km grid would give Italy only about 500.

1. **Crosswalk first.** Build one table mapping every historical comune code to the current boundary set, and run every dataset through it before any join. The prototype needed it for 391 of 7,842 comuni: 377 in Sardinia, whose provinces were redrawn, and 14 that merged into 7 new comuni.
2. **Bridge with the cadastral code.** The four-character Belfiore code survives province changes, so it resolves Sardinia without manual work. Mergers need an explicit old-to-new list; take it from ISTAT's published list of administrative changes.
3. **Spread counts by population, not area.** The prototype splits a comune's votes over tiles by area overlap, which smears Rome evenly over 1,287 km². The full build weights by a 1 km population grid.
4. **Rates are recomputed, never averaged.** Carry counts (votes, electors, residents, euros) onto tiles and divide afterwards.
5. **Keep a tile if at least 15% of it is land.** Tiles with no data are drawn as such, never interpolated.
6. **Rasters** (elevation, land cover) are summarised per tile: mean elevation, dominant land-cover class.

## Political layer

A tile's ideology is the vote-weighted average of an external expert score for each list. No party position is ever set by hand.

**Scale.** Chapel Hill Expert Survey 2024, column `lrgen` (general left–right, 0 to 10). The same file gives two more axes for later lenses: `lrecon` (economic left–right) and `galtan` (social: green-alternative-libertarian against traditional-authoritarian-nationalist).

| 2022 list | Survey party | lrgen |
| --- | --- | --- |
| Alleanza Verdi e Sinistra | SI 1.23 and EV 2.14, simple mean | 1.69 |
| Partito Democratico | PD | 2.93 |
| Movimento 5 Stelle | M5S | 3.33 |
| +Europa | +E | 4.33 |
| Azione – Italia Viva | A (Italia Viva has no score) | 4.43 |
| SVP – PATT | SVP | 4.92 |
| Forza Italia | FI | 6.73 |
| Fratelli d'Italia | FdI | 8.47 |
| Lega | Lega | 8.67 |

**Rules**

- Lists without a survey score are left out of the average, and each tile reports its coverage (share of valid votes that had a score). National coverage in 2022 is 92.0%.
- A joint list takes the simple mean of its member parties' scores, and the rule is printed next to the number.
- Each election uses the survey wave closest to it: 2019 wave for 2018 and 2019 votes, 2024 wave for 2022 and 2024.
- Votes cast for a candidate only are shared among that candidate's lists in proportion to list votes, as the electoral law does.
- Coalitions are a separate lens (centre-right minus centre-left, in points). They never replace list-level scores.
- Valle d'Aosta (single-seat contest, local lists) and Alto Adige (SVP dominates and sits near the middle of the scale) get a visible note rather than a forced fit.

**Lenses.** Ideology, leading list, coalition margin, turnout, share of any list, swing between two elections, each referendum, and the economic and social axes separately.

## Civilization translation

Every game term maps to one measured quantity through a rule written in the app's help panel. If a rule cannot be stated in one sentence, the feature is dropped.

| Game term | Real quantity | Rule |
| --- | --- | --- |
| Ideology (religion layer) | Left–right score | Vote-weighted expert score, as in the political layer |
| Loyalty | Turnout | Voters divided by electors |
| Gold | Declared income | Total taxable income on the tile |
| Science | Graduates | Residents with a university degree |
| Production | Industrial employment | Jobs in manufacturing and construction |
| Food | Farmland | Agricultural land-cover share |
| Terrain | Elevation and land cover | Plains under 300 m, hills to 600 m, mountains above; forest, marsh and coast from land cover |
| City | Labour-market area | One city per ISTAT labour-market area, placed on its main comune |
| Districts | Industry specialisation | A sector whose local job share is at least 1.5 times the national share |
| Citizens | Workforce | Jobs by sector, one citizen icon per fixed number of jobs |
| Wonders | Landmarks | UNESCO sites, universities ranked by enrolment, ports ranked by tonnage |
| Government | Winning coalition | Coalition with most votes in the city at the latest national election |

Thresholds above are starting values. Tune them once on real data, then freeze and publish them.

## Interface

One static page that works on a phone first: map on top, detail sheet below, no server.

- **Map.** Canvas hex map with pan, pinch and wheel zoom. Region borders drawn over the tiles. More city labels appear as the reader zooms in.
- **Lens bar.** One lens at a time, with a legend that states the measure and its scale. Diverging lenses centre on the national value.
- **Tile sheet.** Main comune, region, the yields, every list's share, and the coverage figure.
- **City view.** Districts, citizens, wonders, election history as a small line chart per list.
- **Explorer.** Pick any two columns for all comuni: a sortable table and a scatter plot, both linked to the map.
- **Advisors.** Short computed paragraphs per city (politics, economy, demography). Templates filled from data, no free text and no adjectives about parties.
- **Colour.** Red for left and blue for right, the Italian convention, with a neutral grey midpoint. Party colours for the leading-list lens. Light and dark themes.
- **Access.** Everything on the map is also reachable as a table. Text never relies on colour alone.

## Build phases

Six phases, each closed by a check that must pass before the next one starts.

| Phase | Delivers | Gate |
| --- | --- | --- |
| 1. Skeleton | Repo layout, `data/raw`, `data/processed`, one `make all`, the comune crosswalk | Every 2018–2024 comune code resolves to a current polygon; zero unmatched |
| 2. Grid | Hex grid, population weights, tile table | Tile populations sum to the national total within 0.1% |
| 3. Elections | Camera 2018 and 2022, European 2019 and 2024, referendums | National totals per list match the Interior Ministry figures within 0.1% |
| 4. Political layer | Scores, coverage, swing, all political lenses | Coverage reported per tile; no list scored by hand |
| 5. Socio-economic layers | Income, education, age, jobs, terrain, hazards | Each column's national total or mean matches the source's published figure |
| 6. Interface | Map, lenses, city view, explorer, advisors | Loads in under 3 seconds on a mid-range phone; every number has a source link |

Phase 3 can reuse the prototype's code for 2022 as it stands.

## Working rules for Claude Code

Paste this section into the project's `CLAUDE.md` so every session starts with it.

- Never skip a region, election or dataset silently. If something cannot be done, stop and write it in `GAPS.md` with the reason.
- Never invent, estimate or hand-tune a number. A missing value stays missing and is drawn as missing.
- Every processed file has a row in `SOURCES.md`: URL, download date, licence, and the script that produced it.
- Every phase ends by running its gate as an automated test. A failing gate blocks the next phase.
- Raw downloads are read-only. All transformations are scripts, so the whole build reruns from scratch.
- Joins are on ISTAT codes through the crosswalk, never on comune names.
- Political neutrality: the app describes votes and expert scores. No labels such as "extreme" or "moderate" unless they are the survey's own category names.
- Ask before any choice that changes what a number means (a new scale, a new weighting, dropping a list).

## What the prototype proved

The [prototype map](https://claude.ai/artifact/XsKa5tkWU92VgheSq4VN6G) runs the 2022 Camera vote end to end on 3,674 tiles, so phases 1 to 4 are feasible with the sources listed.

**Checked**

- Rebuilt national list totals sit within 0.01% of the figures published on election night: Fratelli d'Italia 7,300,868 against 7,300,628, Movimento 5 Stelle 4,333,748 against 4,333,748 ([Il Fatto Quotidiano results page](https://www.ilfattoquotidiano.it/elezioni-2022/elezioni-camera-2022/risultati/italia.html)).
- All 7,842 comuni in the results file map to a current polygon after the crosswalk.
- The national ideology score is 5.57 on the 0–10 scale; tiles range from 4.0 to 7.4.

**Left open**

- Area weighting instead of population weighting. About 0.6% of votes fall on coastal slivers that were dropped.
- Lists grouped as "Other" (Italexit, Unione Popolare, Sud chiama Nord and smaller ones) cannot lead a tile, which is wrong wherever one of them came first.
- Valle d'Aosta and the vote from abroad are missing.
- Italia Viva has no survey score; the joint list uses Azione's.
- One election only, so no swing lens yet.
- The check above uses a newspaper's copy of the official count. The full build should test against the Interior Ministry's own final figures.
