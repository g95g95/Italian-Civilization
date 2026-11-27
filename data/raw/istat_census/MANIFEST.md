# ISTAT – Censimento permanente della popolazione (comune / census-section level)

Download date: 2026-11-27 (all files saved unmodified).
Publisher: ISTAT. Licence: Creative Commons Attribution 4.0 (CC BY 4.0), per https://www.istat.it/note-legali/ ("Licenza CC-by Creative Commons 4.0").
Landing page for the section files: https://www.istat.it/notizia/basi-territoriali-e-variabili-censuarie/ (section "Variabili censuarie (1991-2021)").
Bulk files are those attached to IstatData dataflows (annotation ATTACHED_DATA_FILES of DF_BULK_SUBREG2021, DF_BULK_SUBREG2023, DCSS_BULK_ISTR_LAV_PEN_2).

## Files

| File | Size (bytes) | SHA-256 | Vintage |
|---|---|---|---|
| `Dati_regionali_2023.zip` | 261,295,722 | 05661a6e248d4241c9fdd1b1fa1e740eae0706dd3fcfdbeb366f608269bfeb45 | Census 2023 (pop. at 31 Dec 2023), by 2021 census section, 20 regions |
| `Dati_regionali_2021.zip` | 254,534,430 | 000a0d7b612eb3af655b0c979542b17495f38d2c8d6c48699d400e5611e22394 | Census 2021 (pop. at 31 Dec 2021), by 2021 census section, 20 regions |
| `DCSS_ISTR_LAV_PEN_2 - Education, work, commuting for studying or working - full dataset.csv.zip` | 188,598,935 | ae8cfc9c886ea16aa36d94a563abcce26f65351ab2adaf2b9a809eb6a77474c0 | Census 2018–2024, comune level (education, activity status, commuting) |
| `Descrizione-dei-dati-Basi-territoriali.pdf` | 820,709 | eecfde8eb1b0e3e3fa1f25f7adfa69f06bc06265e91a2d07c17615bc2000452c | Documentation |
| `Nota-informativa-Basi-territoriali-2021-1.pdf` | 805,545 | 2d4904928e63bc3ce7c09278e3b57d73995646961812d5b711f52285390dd173 | Documentation |

Download URLs:
- `https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip` (Last-Modified 2026-06-08)
- `https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2021.zip` (Last-Modified 2025-04-04; linked from the istat.it landing page)
- `https://esploradati.istat.it/databrowser/DWL/PERMPOP/MUN/DCSS_ISTR_LAV_PEN_2%20-%20Education,%20work,%20commuting%20for%20studying%20or%20working%20-%20full%20dataset.csv.zip` (Last-Modified 2025-12-17)
- `https://www.istat.it/wp-content/uploads/2024/07/Descrizione-dei-dati-Basi-territoriali.pdf`
- `https://www.istat.it/wp-content/uploads/2024/07/Nota-informativa-Basi-territoriali-2021-1.pdf`

---

## A. `Dati_regionali_2023.zip` / `Dati_regionali_2021.zip` (variabili censuarie per sezione di censimento)

Contents: one xlsx per region (one sheet each, header in row 1, one row per 2021 census section) plus `TRACCIATO FILE REGIONALI.xlsx` (variable dictionary).
- 2023: `Dati_regionali_2023/R01_Piemonte_2023_sezioni.xlsx` … `R20_Sardegna_2023_sezioni.xlsx` (inside a folder; names contain spaces/apostrophes, e.g. `R02_Valle d'Aosta_2023_sezioni.xlsx`), 138 columns.
- 2021: `R01_indicatori_2021_sezioni.xlsx` … `R20_indicatori_2021_sezioni.xlsx` (zip root), 130 columns.
Uncompressed ~275–280 MB each. Aggregate sections to comune by `PROCOM`.

### Comune code
`PROCOM` = 6-digit ISTAT comune code, but encoded differently per vintage:
- 2023: text, zero-padded (`'007001'`) — matches PRO_COM_T directly.
- 2021: text **without** leading zeros (`'7001'`) — apply `zfill(6)`.
Other id columns: CODREG, REGIONE, CODPRO, PROVINCIA, CODCOM (3-digit within province), COMUNE, SEZ21_ID (section id), COM_ASC1..3 (sub-municipal areas). In 2023 CODREG/CODPRO/CODCOM/SEZ21_ID are numeric; in 2021 they are text. Comuni present: 2021 = 7,904; 2023 = 7,900 (boundaries as at the reference date).

### Variables (from TRACCIATO; identical in both vintages unless noted)
- P1 total resident population; P2 males; P3 females
- P14–P29 population by 5-year age class: <5, 5–9, 10–14, 15–19, 20–24, 25–29, 30–34, 35–39, 40–44, 45–49, 50–54, 55–59, 60–64, 65–69, 70–74, >74 (P30–P45 males, P67–P82 females, same classes)
- P83 population aged 9+ (P84 M, P85 F)
- Education, population 9+: P86 no qualification; P87 primary (licenza elementare); P88 lower secondary (licenza media); P89 upper secondary diploma incl. professional qualifications; **P90 tertiary first or second level incl. PhD (laurea)**. Males P91–P95, females P96–P100 (same order).
- **P101 employed aged 15–64** (P102 M, P103 F). Note: unemployed / labour force are NOT in these files — use file B.
- IT1–IT9 Italians by age 0–14 / 15–64 / 65+ (total, M, F); IT10–IT12 employed Italians 15–64
- **ST1 foreign + stateless residents total**; ST2 M; ST2_B F; ST3–ST5 by age 0–29/30–54/55+; ST16–ST18 EU citizens (T/M/F); ST19–ST21 non-EU (T/M/F); ST22–ST30 by age 0–14/15–64/65+ (T/M/F); ST31–ST33 employed foreigners 15–64 (T/M/F)
- PF1 households; PF3–PF8 households by size 1…6+
- A2 dwellings occupied by residents; A3 empty/non-resident dwellings; A8 total dwellings
- 2021 only: E3 residential buildings. 2023 only: EM1–EM6 (Italians by birth born in Italy/abroad, naturalised Italians born in Italy/abroad, foreigners born in Italy/abroad), PF9 cohabiting households, NA1 cars owned, A5 other occupied housing units.

### National totals (sum over all sections, computed)
| Var | 2021 | 2023 |
|---|---|---|
| P1 population | 59,030,133 | 58,971,230 |
| P83 pop 9+ | 54,899,241 | 55,040,469 |
| P90 tertiary | 8,494,314 (15.47 % of 9+) | 9,027,576 (16.40 % of 9+) |
| P101 employed 15–64 | 22,717,716 | 23,427,096 |
| ST1 foreigners | 5,030,716 (8.52 %) | 5,253,658 (8.91 %) |
P1 equals the ISTAT population at 1 Jan 2022 / 1 Jan 2024 in DCIS_POPRES1 (see ../istat_pop).

---

## B. `DCSS_ISTR_LAV_PEN_2 - … full dataset.csv.zip` (comune level, years 2018–2024)

One CSV inside, **4,391,391,518 bytes uncompressed (17,683,842 rows)** — stream it (e.g. `unzip -p … | …` or Python `zipfile` + `csv`), do not extract to memory.
Format: UTF-8 with BOM, separator `|`, all fields double-quoted except Value; code/label pairs.

Header: `ITTER107|Territory|TIPO_DATO_CENS_POP|Data type|SEXISTAT1|Gender|ETA1|Age|CITTADINANZA|Citizenship|TITOLO_STUDIO|Educational attainment|FORZE_LAV|Current activity status|PROV_DEST_Z|Location of place of work, school or university|MOTIVOPS1|Reason for commuting|TIME|Select time|Value|Flag Codes|Flags`

- `ITTER107`: comune = 6-digit zero-padded code (e.g. `001272`); also aggregates (`IT`, NUTS codes …). Comuni per year: 2018 7,954; 2019 7,914; 2020 7,903; 2021 7,904; 2022 7,904; 2023 7,900; 2024 7,896.
- `TIPO_DATO_CENS_POP`: `RESPOP_AV` resident population on 31 Dec; `RP_COM_DAY` resident population commuting daily.
- `SEXISTAT1`: `T` total, `M`, `F`.
- `ETA1`: `TOTAL`, `Y_GE9`, `Y_GE15`, `Y_GE65`, `Y9-24`, `Y15-24`, `Y25-49`, `Y50-64`.
- `CITTADINANZA`: `TOTAL`, `ITL` Italian, `FRGAPO` foreign/stateless.
- `TITOLO_STUDIO`: `ALL` total; `IL` illiterate; `LBNA` literate no qualification; `NED` no educational degree (= IL+LBNA); `PSE` primary; `LSE` lower secondary; `USE_IF` upper secondary + IFTS; `BL` bachelor / 1st-level academic diploma / ITS / old university diploma; `ML` master / 2nd-level; `RDD` PhD; `ML_RDD` = ML+RDD. Non-overlapping set summing to ALL: NED, PSE, LSE, USE_IF, BL, ML_RDD. **Tertiary = BL + ML_RDD.**
- `FORZE_LAV`: `99` total; `1` employed; `12` unemployed; `22` economically active (= 1 + 12, labour force); `23` not economically active (= 24+4+5+7); `24` pensioner/capital-income recipient; `4` housewife; `5` student; `7` other.
- `PROV_DEST_Z`: `ALL`, `SMPUR` same comune, `OMPUR` other comune. `MOTIVOPS1`: `ALL`, `STD` study, `WK` work.
- `TIME`: year (reference date 31 December). `Value`: count; estimates from the sample component are non-integer (e.g. unemployed). Flags empty throughout.
- Availability caveat: for **2024**, `FORZE_LAV` has only `1` (employed) and `99` (total) — unemployed / active / inactive are published up to **2023**. Education by attainment (ETA1=`Y_GE9`, FORZE_LAV=`99`) is available for 2018–2024.

Useful series (filter other dims to `T`, `TOTAL`, `ALL`):
- Graduates: ETA1=`Y_GE9`, FORZE_LAV=`99`, TITOLO_STUDIO in (`BL`,`ML_RDD`) vs `ALL`.
- Labour: ETA1=`Y_GE15`, TITOLO_STUDIO=`ALL`, FORZE_LAV in (`1`,`12`,`22`,`99`).

National values (ITTER107=`IT`):
| Year | Pop 9+ | BL | ML_RDD | Tertiary share 9+ | Employed 15+ | Unemployed | Labour force | Pop 15+ |
|---|---|---|---|---|---|---|---|---|
| 2021 | 54,899,241 | 2,245,986 | 6,248,328 | 15.47 % | 23,632,617 | 2,396,496 | 26,029,113 | 51,540,338 |
| 2023 | 55,040,469 | 2,534,149 | 6,493,427 | 16.40 % | 24,500,649 | 2,064,493 | 26,565,142 (unemp. rate 7.77 %) | 51,784,963 |
| 2024 | 55,115,514 | 2,656,549 | 6,625,484 | 16.84 % | 24,837,842 | n/a | n/a | 51,923,415 |

Torino (001272) 2024: pop 9+ 801,900; BL 47,806; ML_RDD 141,615; employed 15+ 379,382. 2023: unemployed 33,551.34; labour force 407,575.34.

---

## Not downloaded (available if needed)
- `DCSS_POP_DEMCITMIG - Demographic characteristics and citizenship - full dataset.csv.zip` (310 MB zip, multi-GB CSV; age × sex × citizenship by comune incl. 2024): `https://esploradati.istat.it/databrowser/DWL/PERMPOP/MUN/DCSS_POP_DEMCITMIG%20-%20Demographic%20characteristics%20and%20citizenship%20-%20full%20dataset.csv.zip`. The 2023 section files above already provide age classes and foreigners. The SDMX API query for the same data (DF_DCSS_POP_DEMCITMIG_TV_2) timed out after 300 s.
- `Comuni_2023.zip` / `Comuni_2021.zip` under the same DWL/PERMPOP/SUBCOM path contain only the 14 large cities (sub-municipal sections), not all comuni.
