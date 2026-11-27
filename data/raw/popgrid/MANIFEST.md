# popgrid — ISTAT Census 2021 population on the 1 km Eurostat/INSPIRE grid

Download date: 2026-11-27

## Source
Publisher: ISTAT — Istituto Nazionale di Statistica.
Landing page: https://www.istat.it/notizia/statistiche-sulla-popolazione-per-griglia-regolare/

| File | URL | Size |
|---|---|---|
| `GrigliaPop2021_Ind_ITA.zip` (ESRI shapefile, 1 km² polygons) | https://www.istat.it/wp-content/uploads/2023/07/GrigliaPop2021_Ind_ITA.zip | 12.5 MB |
| `GrigliaPop2021_Ind_ITA_CSV.zip` (same data as `;`-separated text, UTF-8 with BOM) | https://www.istat.it/wp-content/uploads/2023/07/GrigliaPop2021_Ind_ITA_CSV.zip | 3.7 MB |
| `NotaMetodologicaGriglia2021-Ind.pdf` (methodology note, 9 Sep 2024) | https://www.istat.it/wp-content/uploads/2023/07/NotaMetodologicaGriglia2021-Ind.pdf | 0.6 MB |

`extracted/` holds the unzipped contents of both zips (unchanged).

## Licence
CC BY 4.0. ISTAT's site-wide legal notice (https://www.istat.it/note-legali/) says: "Salvo diversa indicazione, tutti i contenuti pubblicati su questo sito sono soggetti alla licenza Creative Commons – Attribuzione – versione 4.0". Suggested attribution: "Fonte: Istat, Censimento permanente della popolazione 2021 – griglia regolare 1 km²".

## Vintage
The data is the legal population of the 2021 permanent census (reference date 2021). It was produced under EU Implementing Regulation 2018/1799. The final release is from 2024: the files are dated 2024-04/2024-09.

## Spatial reference
- CRS: EPSG:3035 (ETRS89-LAEA Europe). The `.prj` contains the ESRI WKT "ETRS_1989_LAEA".
- Resolution: 1 km × 1 km cells on the Eurostat GEOSTAT/INSPIRE grid. The cell ID is `GRD_ID` = `CRS3035RES1000mN{northing}E{easting}`, and the coordinates are those of the cell's lower-left corner.
- Extent (EPSG:3035): x 4,053,000–5,052,000; y 1,384,000–2,669,000.
- Rows: 319,154 cells. The files are vector polygons, not a raster, and include cells with zero population. 171,917 cells have population > 0.

## Fields (shapefile name / CSV name — meaning, persons)
| SHP | CSV | Meaning |
|---|---|---|
| GRD_ID | GRD_ID | INSPIRE grid cell code |
| CNTR_ID | CNTR_ID | Country code(s). `IT` for Italian cells. Border cells are shared, e.g. `CH-IT`, `FR-IT`, `AT-IT`, `IT-SI`, `IT-SM`, `IT-VA`, `AT-CH-IT`. In shared cells the value counts only Italian residents. |
| T | Pop_Tot | Total resident population |
| M / F | Pop_Tot_M / Pop_Tot_F | Males / females |
| Y_LT15 | Pop_0_15 | Aged under 15 |
| Y1564 | Pop_15_64 | Aged 15–64 |
| Y_GE65 | Pop_oltre_65 | Aged 65 and over |
| NAT | Nati_Ita | Born in Italy |
| EU_OTH | Nati_EU | Born in another EU country |
| OTH | Nati_Extra_EU | Born outside the EU |
| EMP | Occupati | Employed persons |
| SAME | Stessa_dimora_1_anno_prima | Same usual residence one year before |
| CHG_IN | Altra_dimora_anno_prima_italia | Residence one year before was elsewhere in Italy |
| CHG_OUT | Altra_dimora_anno_prima_estero | Residence one year before was abroad |
| Shape_Leng, Shape_Area | — | 4000 m / 1,000,000 m² |

## Checks
- The sum of `T` over all cells is **58,933,936**. Of this, 58,583,623 is in pure `IT` cells and the rest is in shared border cells. For example, `IT-VA` holds 207,676 people: Rome's residents in cells that overlap Vatican City.
- The methodology note gives 58,933,908 geocoded to the grid (99.8%), plus 96,225 people (homeless, "senza fissa dimora") placed in a virtual cell that is **not** in these files. The grid total plus the virtual cell is ≈ 59.03 M, which matches the 2021 census legal population.
- The CSV and the shapefile carry identical values.

## Not used
The fallback, GHSL GHS-POP (JRC), was not downloaded because the ISTAT grid was available.
