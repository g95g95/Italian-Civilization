# ISTAT – Popolazione residente al 1° gennaio (DCIS_POPRES1)

Download date: 2026-11-27 (files saved unmodified, exactly as returned by the server).
Publisher: ISTAT. Licence: Creative Commons Attribution 4.0 (CC BY 4.0), per https://www.istat.it/note-legali/.
(demo.istat.it is blocked by this environment's proxy (HTTP 403), so the IstatData SDMX API was used instead.)

## Files

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `DCIS_POPRES1_all_comuni_JAN_total.csv` | 6,181,243 | f608b3b87d490a49ea25987c5a315836b251c0695dac4932284a3c7e036f91e9 |
| `DCIS_POPRES1_Italy_regions_provinces_JAN_total.csv` | 100,336 | ef5e65e1ba9c24b86e87ff4ff85370935260c3cddc5ffce8611bc5b011f6f78d |

### Download URLs (header `Accept: application/vnd.sdmx.data+csv;version=1.0.0`)

- Comuni: `https://esploradati.istat.it/SDMXWS/rest/data/22_289_DF_DASH_DCIS_POPRES1_1/A..JAN.9.TOTAL.99`
  (dataflow "Dashboard – Tutti i comuni"; note: adding `startPeriod=` to this query makes the server fail with HTTP 500, so all years are downloaded)
- Italy/regions/provinces: `https://esploradati.istat.it/SDMXWS/rest/data/22_289_DF_DCIS_POPRES1_1/A..JAN.9.TOTAL.99`

## Vintage

Years 2019–2026 (population at 1 January of each year, post-census reconstructed series).
- **1 Jan 2026**: `OBS_STATUS = e` (CL_FLAG: "dato stimato", estimate/provisional) for every row.
- **1 Jan 2025**: final (empty OBS_STATUS). Use 2025 when a final figure is required, 2026 for the latest figure.
Comune codes: each year uses the comuni existing at that date (2025 and 2026: 7,896 comuni each). The comuni file also contains aggregate rows (IT, NUTS ITC/ITC1/ITC11…, IT108–IT111).

## Columns (SDMX-CSV 1.0)

`DATAFLOW, FREQ, REF_AREA, DATA_TYPE, SEX, AGE, MARITAL_STATUS, TIME_PERIOD, OBS_VALUE, OBS_STATUS, NOTE_DS, NOTE_REF_AREA, NOTE_DATA_TYPE, NOTE_SEX, NOTE_AGE, NOTE_MARITAL_STATUS, BASE_PER, UNIT_MEAS, UNIT_MULT`

Dimension codes used (DSD DCIS_POPRES1):
- `FREQ` = `A` (annual)
- `REF_AREA` (CL_ITTER107): comune = 6-digit zero-padded ISTAT code (e.g. `001272` Torino) = PRO_COM_T; filter `len==6 and isdigit()`. `IT` = Italy; NUTS-style codes = regions/provinces.
- `DATA_TYPE` (CL_TIPO_DATO15): `JAN` = popolazione al 1º gennaio
- `SEX` (CL_SEXISTAT1): `9` = totale
- `AGE` (CL_ETA1): `TOTAL` = totale
- `MARITAL_STATUS` (CL_STATCIV2): `99` = totale
- `OBS_VALUE`: persons (integer). `NOTE_REF_AREA` contains a filter tag such as `FILTER__ITC1`.

## Reference totals (sum of comuni equals the `IT` row exactly)

| 1 January | Italy | Torino (001272) | Status |
|---|---|---|---|
| 2025 | 58,943,464 | 853,196 | final |
| 2026 | 58,942,828 | 855,654 | estimate (e) |
| 2022 (= census 31 Dec 2021) | 59,030,133 | | final |
