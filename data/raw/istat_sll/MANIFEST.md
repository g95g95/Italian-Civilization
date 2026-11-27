# ISTAT – Sistemi Locali del Lavoro (SLL)

Download date: 2026-11-27. Publisher: ISTAT (www.istat.it). Licence: Creative Commons Attribuzione 4.0 (CC BY 4.0), per https://www.istat.it/note-legali/

## Files

| File | URL | Vintage | Content |
|---|---|---|---|
| `Composizione-SLL2011-01012023.zip` | https://www.istat.it/wp-content/uploads/2021/01/Composizione-SLL2011-01012023.zip | SLL 2011 (2018 version, 610 SLL), on the comune boundaries in force at 01/01/2023 | **Comune → SLL table** (CSV `;` latin-1 + XLSX with Legenda sheet). 7,901 comuni |
| `SLL_2021.zip` | https://www.istat.it/wp-content/uploads/2025/09/SLL_2021.zip | **SLL 2021 (new delineation, 515 SLL)**, released 2 Oct 2025, comune geography at 31/12/2021 | Shapefile of SLL polygons (WGS84 / UTM 32N) + `metadati_SLL_2021.xlsx`. **One row per SLL; there is no comune list** |
| `auto_contenimento_SLL2021.zip` | https://www.istat.it/wp-content/uploads/2025/10/auto_contenimento_SLL2021.zip | SLL 2021 | CSV/XLSX: list of the 515 SLL 2021 (code, name) with demand/supply self-containment |
| `Tavole-di-dati-SLL-2021.xlsx` | https://www.istat.it/wp-content/uploads/2025/10/Tavole-di-dati-SLL-2021.xlsx | SLL 2021 | Summary tables from the press release (by region and size class), not per comune |
| `FocusSLL2021.pdf` | https://www.istat.it/wp-content/uploads/2025/10/FocusSLL2021.pdf | SLL 2021 | Full text and methodological note |

Source pages: https://www.istat.it/comunicato-stampa/la-nuova-geografia-dei-sistemi-locali-del-lavoro-anno-2021/ ,
https://www.istat.it/statistiche-per-temi/focus/informazioni-territoriali-e-cartografiche/statistiche-sul-territorio/sistemi-locali-del-lavoro-e-distretti-industriali/ ,
https://www.istat.it/notizia/composizione-dei-sistemi-locali-del-lavoro-2011-a-partire-dal-1-gennaio-2019/

## Columns: Composizione SLL 2011 al 01012023 (CSV `;`, ISO-8859-1, CRLF; some headers contain a trailing NBSP)
- `COD_REG _SLL`: region of the SLL, meaning the region of its main comune
- `COD_SLL_2011_2018`: numeric SLL code (e.g. 101)
- `COD_SLL_2011_2018_T`: 4-character SLL code (e.g. "0101"), made of the 2-digit region code plus a 2-digit progressive number
- `DEN_SLL_2011_2018`: SLL name, which is the name of its main comune
- `PRO_COM_T`: **6-digit ISTAT comune code** (the join key)
- `COMUNE`: comune name
- `CAPOL_SLL_2011_2018`: 1 marks the main comune of the SLL (the one with the most jobs, which gives the SLL its name). There are 610 flags, one per SLL
- `PRO_COM`: numeric comune code
- `Cod Uts`: code of the province or metropolitan city (UTS)

## SLL 2021 shapefile attributes (from metadati_SLL_2021.xlsx)
COD_SLL (4-character code), C_SLL_N (numeric code), SLL_2021 (name, which is the main comune's name), CREG_SLL and REG_SLL (region of the main comune), POP_2021, N_COM (number of comuni), SUP_Kmq.

## Caveat
I found no ISTAT comune → SLL 2021 composition table on www.istat.it, neither on the release page nor in the WordPress media library. ISTAT appears to publish it only in the SITUAS portal (situas.istat.it), which was not used here. To build a comune → SLL 2021 table you can:
(a) spatially join comune centroids to the SLL_2021 polygons, or
(b) get the SITUAS SLL 2021 composition report, if access to that host is approved.
The SLL 2011 table above is the authoritative comune-level table.
