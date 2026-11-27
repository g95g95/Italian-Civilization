# MUR USTAT – University enrolment (NOT DOWNLOADED)

Attempt date: 2026-11-27.

## Status: blocked
- `https://dati.ustat.mur.gov.it/` (the host on the allowlist) returns **curl 000 / proxy HTTP 502 `connect_unreachable`**. The egress proxy could not connect, likely because the name does not resolve.
- The real host of the MUR USTAT CKAN portal is **`dati-ustat.mur.gov.it`** (hyphen, not dot), according to the GitHub project dataciviclab/open-mur. I did not contact it because it is not on this session's allowlist. **Adding `dati-ustat.mur.gov.it` to the allowlist should unblock this item.**

## Resources to fetch once the host is allowed (CKAN, from dataciviclab/open-mur, commit of 2026-11-24)
- Enrolled students by ateneo ("Iscritti per ateneo", series 2000–2025, 2009 missing; latest academic year 2025/26). CKAN resource id `32d26e28-a0b5-45f3-9152-6072164f3e63`:
  `https://dati-ustat.mur.gov.it/api/3/action/resource_show?id=32d26e28-a0b5-45f3-9152-6072164f3e63` gives the direct CSV URL. The CSV is latin-1 with columns AnnoA, AteneoNOME, AteneoCOD, SESSO, Isc.
- Atenei registry ("Atenei": code, name, type, city/sede, province, ISTAT province code, region). CKAN resource id `820aefe6-0662-4656-84ec-d8859a2a3b7e`. The cleaned columns are cod_ateneo, nome_esteso, nome_operativo, status, descrizione, tipo, citta, provincia, sigla_provincia, cod_provincia_istat, regione, macro_area.
- Licence as stated by MUR on the portal: not verified (portal unreachable). MUR open data is normally published under CC BY 4.0 / IODL 2.0.

## GitHub mirror search
- `dataciviclab/open-mur` (MIT, active) holds only pipeline configs. Its processed data is in Parquet on GCS, which is not reachable here, and no raw CSV is committed.
- No other GitHub repository mirroring the USTAT iscritti or atenei CSVs was found (gh repo and code search).

The atenei registry gives a city name and ISTAT province code but no comune code. Joining to the comune grid needs a name match of `citta` to the ISTAT comune list.
