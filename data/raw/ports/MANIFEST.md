# Ports – cargo tonnage (Eurostat) and port locations (GISCO)

Download date: 2026-11-27. Publisher: Eurostat / GISCO (European Commission). Licence: Eurostat reuse policy, free reuse with attribution ("© European Union, 1995–2026", Commission Decision 2011/833/EU, equivalent to CC BY 4.0). GISCO data additionally carries "© EuroGeographics for the administrative boundaries".

## Files
| File | URL | Vintage | Content |
|---|---|---|---|
| `eurostat_mar_go_am_it_2015plus.sdmx.csv` (750 KB) | https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/MAR_GO_AM_IT/A.TOTAL+IN+OUT.TOTAL+LBK+DBK+LCNT+RO_MSP+RO_MNSP+OTH+UNK.TOTAL.THS_T.TOTAL.?format=SDMX-CSV&startPeriod=2015&compressed=false | Dataset `mar_go_am_it` "Gross weight of goods transported to/from main ports – Italy", last update 2026-08-03, **years 2015–2025** | 8,014 observations |
| `eurostat_mar_go_am_it_2015plus.json` (100 KB) | https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/mar_go_am_it?format=JSON&lang=EN&freq=A&natvessr=TOTAL&par_mar=TOTAL&unit=THS_T&sinceTimePeriod=2015 | same | JSON-stat with **port labels** (`dimension.rep_mar.category.label`) |
| `eurostat_mar_go_am_it_structure.sdmx.xml` (343 KB) | https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/dataflow/ESTAT/MAR_GO_AM_IT/latest?references=descendants&detail=referencepartial | – | Dataflow, DSD and codelists (78 REP_MAR codes with names) |
| `GISCO_PORT_2013_SH.zip` (540 KB) | https://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/PORT_2013_SH.zip | GISCO Ports 2013 (files dated 2015) | Shapefile of port points (`PORT_PT_2013`, ETRS89 geographic lon/lat) and attribute table `PORT_AT_2013.dbf` (2,440 ports, 140 in IT) |

`mar_mg_am_pwhd` is not disseminated (HTTP 404). The unfiltered `mar_go_am_it` is too large (HTTP 413), so it was filtered: freq=A, natvessr=TOTAL (all flags), par_mar=TOTAL (all partners), unit=THS_T.

## Eurostat columns (SDMX-CSV)
- `direct`: TOTAL / IN / OUT
- `cargo`: TOTAL, LBK (liquid bulk), DBK (dry bulk), LCNT (large containers), RO_MSP / RO_MNSP (Ro-Ro), OTH, UNK
- `natvessr`, `par_mar`: both TOTAL
- `unit`: THS_T (thousand tonnes)
- `rep_mar`: reporting port, e.g. **`IT_0ITGOA`** (Genova). Stripping the `IT_0` prefix gives the UN/LOCODE (`ITGOA`)
- `TIME_PERIOD`, `OBS_VALUE`, `OBS_FLAG`, `CONF_STATUS`

Coverage for TOTAL/TOTAL: 38 ports have values in 2023 and 2024, and 40 in 2025. `rep_mar=IT` is the national total. The sum over ports exceeds it because domestic traffic is counted at both ends.

Aggregate codes that have no location: `IT_0IT888` (Italy – other ports), `IT_0IT88P` (offshore installations – other ports), `IT_0IT004` (Eolie, an island group).

## Locating ports
`PORT_AT_2013.dbf` has these fields:
- `PORT_ID` (UN/LOCODE, e.g. ITGOA; matches the Eurostat code minus `IT_0`)
- `CNTR_CODE`, `PORT_NAME`
- `STAT_PORT_` (Eurostat statistical port code)
- `NUTS_CODE` (NUTS3 2010)
- `LOCD_STTS_`, `PORT_HIER_`, `TEN_CODE`

`PORT_PT_2013.shp` holds the point geometry (lon/lat, ETRS89), linked by `PORT_ID`.

**All 48 Eurostat Italian port codes, excluding the 3 aggregates above, match a GISCO PORT_ID.**

The newer GISCO distribution (ec.europa.eu/eurostat/cache/GISCO/distribution/v2/ports/) answers with a 301 redirect to another host, which I did not follow.

OpenStreetMap / Overpass (overpass-api.de) was **not reachable**: the TLS handshake was reset through the egress proxy on 3 attempts. No OSM data was downloaded.
