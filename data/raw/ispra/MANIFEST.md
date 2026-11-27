# ISPRA IdroGEO – Indicatori di rischio idrogeologico (PIR), per comune

Download date: 2026-11-27. Publisher: ISPRA, IdroGEO platform. Licence: **CC BY 4.0**, as stated on https://idrogeo.isprambiente.it/app/page/open-data ("Indicatori di rischio idrogeologico … Licenza: CC BY 4.0"). The hazard mosaic shapefiles on that page are under CC BY-SA 4.0 and were not downloaded.

## Files
| File | URL | Content |
|---|---|---|
| `pir_comuni.csv` (3.7 MB) | https://idrogeo.isprambiente.it/api/pir/comuni/export?outputFormat=csv | 7,898 comuni × 129 columns, UTF-8, comma-separated, quoted header |
| `Metadati_PIR.csv` | https://idrogeo.isprambiente.it/cms/wp-content/uploads/2025/07/Metadati_PIR.csv | Definition, source and reference year for every column |
| `Metadati_open_data_PIR.xlsx` | https://idrogeo.isprambiente.it/cms/wp-content/uploads/2025/07/Metadati_open_data_PIR.xlsx | Same metadata as XLSX |

The same table is also available as XLSX (`...export?outputFormat=excel`, 28 MB, same 129 columns) and as JSON (`/api/pir/comuni/export`). Neither was kept. Per-comune detail is also available at `/api/pir/comuni/{pro_com}`.

## Vintage
- Landslide indicators: Mosaicatura ISPRA **2024** (PAI hazard)
- Flood indicators: Mosaicatura ISPRA **2020** (D.Lgs. 49/2010 scenarios)
- All values are reported on the 2024 administrative boundaries
- Population figures come from the 2021 Census (and 2011 for exposure)

The value **-1 means data not available**.

## Key columns
- `pro_com`: ISTAT comune code, **numeric without leading zeros** (Roma = 58091). Zero-pad to 6 digits to join.
- `cod_reg`, `cod_prov`, `comune`
- `ar_kmq`: comune area (km²)
- `ar_fr_p3p4` / `ar_frp3p4p`: landslide hazard P3+P4 area (km² / % of the comune)
- `ar_fr_p4`, `ar_fr_p3`, `ar_fr_p2`, `ar_fr_p1`, `ar_fr_aa`: landslide hazard area by class, including attention areas (AA), with `_p` % variants
- `ar_id_p2` / `aridp2_p`: flood hazard medium (P2) area (km² / %); `ar_id_p3`/`aridp3_p` (high) and `ar_id_p1`/`aridp1_p` (low)
- Exposure columns use the prefixes `pop_*`, `fam_*`, `ed_*` (buildings), `im_*` (businesses) and `bbcc_*` (cultural heritage), each split by hazard class, e.g. `pop_fr_p3p4`, `pop_idr_p2`. Full definitions are in `Metadati_PIR.csv`.
