# ISTAT – ASIA Unità locali (local units of active enterprises), by comune and ATECO 2007 section

Download date: 2026-11-27 (files saved unmodified, exactly as returned by the server).
Publisher: ISTAT. Licence: Creative Commons Attribution 4.0 (CC BY 4.0), per https://www.istat.it/note-legali/ ("Licenza CC-by Creative Commons 4.0").
Source register: Registro statistico delle Unità Locali (ASIA-UL). Workplace-based: persons employed are counted at the comune where the local unit is located. Coverage: active enterprises in industry and services, ATECO sections B–S **excluding O** (public administration); agriculture (A), households (T) and extraterritorial bodies (U) are not covered. Public institutions and non-profits are not included.

## Files

| File | Size (bytes) | SHA-256 | Content |
|---|---|---|---|
| `DICA_ASIAULP_TERRIFDATA_3_LUEMPDAA_sections_2024.csv` | 11,883,542 | 59d1c08a1c6fc94dc9b3d317e94746aca9b57897a741926133f9afb13ac4f8b6 | Persons employed (addetti, annual average), 2024 |
| `DICA_ASIAULP_TERRIFDATA_3_LU_sections_2024.csv` | 13,261,005 | 57de151d803f475453214af5a94f43a48c21b90c22065cce1c42ac6f640550cf | Number of local units, 2024 |
| `UNITA_LOCALI - OCCUPAZIONE_2018_2024.zip` | 764,752 | 533cce68f3c13233a831ee1f05fffaa01e320ca56708d06783d85f6965a53c01 | Ancillary: ASIA-Occupazione xlsx tables 2018–2024 (employee positions by region / ripartizione / ATECO section; NOT comune level) |

### Download URLs

- LUEMPDAA: `https://esploradati.istat.it/SDMXWS/rest/data/183_1163_DF_DICA_ASIAULP_TERRIFDATA_3/A..LUEMPDAA.0010+B+C+D+E+F+G+H+I+J+K+L+M+N+P+Q+R+S.TOTAL?startPeriod=2024&endPeriod=2024`
- LU: `https://esploradati.istat.it/SDMXWS/rest/data/183_1163_DF_DICA_ASIAULP_TERRIFDATA_3/A..LU.0010+B+C+D+E+F+G+H+I+J+K+L+M+N+P+Q+R+S.TOTAL?startPeriod=2024&endPeriod=2024`
  (both requested with HTTP header `Accept: application/vnd.sdmx.data+csv;version=1.0.0`; each call takes ~60 s)
- Ancillary zip: `https://esploradati.istat.it/databrowser/DWL/Imprese/UNITA_LOCALI%20-%20OCCUPAZIONE_2018_2024.zip` (bulk file attached to dataflow DF_BULK_LOCALUNITS)

## Dataflow / vintage

- Dataflow `183_1163_DF_DICA_ASIAULP_TERRIFDATA_3` (IT1, v1.0) "Unità locali e addetti – Territorio anno riferimento dati – Settori economici (Ateco 3 cifre) – com.", DSD `DICA_ASIAULP_TERRIFDATA`.
- Reference year **2024** (latest available; the flow covers 2018–2024). "TERRIFDATA" = territory as at the data reference year, so comune codes are those valid in 2024 (7,896 comuni; same set as MEF a.i. 2024).
- The flow also has ATECO 2/3-digit codes; only the section-level codes listed below were requested.

## Format and columns (SDMX-CSV 1.0, comma-separated, header row)

`DATAFLOW, FREQ, REF_AREA, DATA_TYPE, ECON_ACTIVITY_NACE_2007, PERS_EMPL_SIZE_CLASS, TIME_PERIOD, OBS_VALUE, OBS_STATUS, NOTE_DS, NOTE_REF_AREA, NOTE_DATA_TYPE, NOTE_ECON_ACTIVITY_NACE_2007, NOTE_PERS_EMPL_SIZE_CLASS, NOTE_TIME_PERIOD, BASE_PER, UNIT_MEAS, UNIT_MULT`

- `REF_AREA` (codelist CL_ITTER107): **comuni are the 6-digit numeric codes, zero-padded** (e.g. `001272` = Torino) = PRO_COM_T. The file also contains aggregate areas you must filter out: `IT` (Italy), NUTS codes (`ITC`, `ITC1`, `ITC11`, …), `IT108`–`IT111` (new provinces), and population-size classes `INH_UN1000`, `INH1001-5000`, …, `INH_GE250001`. Filter: `len(code)==6 and code.isdigit()`.
- `DATA_TYPE` (CL_TIPO_DATO_CIS): `LUEMPDAA` = numero addetti delle unità locali delle imprese attive (valori medi annui) – decimals; `LU` = numero di unità locali delle imprese attive – integers.
- `ECON_ACTIVITY_NACE_2007` (CL_ATECO_2007): `0010` = TOTAL; `B` mining; `C` manufacturing; `D` electricity/gas; `E` water/waste; `F` construction; `G` trade; `H` transport/storage; `I` accommodation/food; `J` information/communication; `K` finance/insurance; `L` real estate; `M` professional/scientific/technical; `N` administrative/support; `P` education; `Q` health/social work; `R` arts/entertainment; `S` other services. (O, A, T, U not present.)
- `PERS_EMPL_SIZE_CLASS` (CL_CLLVT): `TOTAL` only.
- `FREQ` = `A`; `TIME_PERIOD` = `2024`; `OBS_STATUS` empty for all rows; `NOTE_DATA_TYPE` carries a footnote id (e.g. `TIPO_DATO_CIS__LU_N1`).
- Comune × section combinations with no local units are **absent** (not zero rows): 124,220 data rows in each file. Treat missing as 0. All 7,896 comuni have a `0010` row.

## Reference totals (2024, Italy, `REF_AREA=IT`; the sum over the 7,896 comuni equals these exactly)

| Section | Addetti (LUEMPDAA) | Local units (LU) |
|---|---|---|
| 0010 Total | 18,845,823.94 | 5,157,564 |
| C Manufacturing | 3,886,453.58 | 406,695 |
| F Construction | 1,614,674.10 | 577,830 |
| C+F | 5,501,127.68 (29.19 % of total) | 984,525 |
| G Trade | 3,439,162.12 | 1,102,281 |

Torino (001272), manufacturing addetti 2024: 43,018.62.
