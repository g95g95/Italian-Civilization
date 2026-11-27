# INGV – Earthquakes M ≥ 4.0 (FDSN event web service)

Download date: 2026-11-27. Publisher: INGV, Istituto Nazionale di Geofisica e Vulcanologia (service version 1.109.0).
Licence: INGV publishes its seismic data under CC BY 4.0 (INGV data policy; cite "ISIDe Working Group, INGV"). I did not re-check the licence text in this session.

## File
`ingv_events_M4_1985-2026.txt` (108 KB): 911 events plus a header line, pipe-separated (`|`).

URL:
```
https://webservices.ingv.it/fdsnws/event/1/query?starttime=1985-01-01T00:00:00&endtime=2026-11-01T00:00:00&minmag=4.0&minlat=35&maxlat=48&minlon=6&maxlon=19.5&format=text&orderby=time-asc&limit=20000
```
Vintage: the live catalogue as of the download date. The first event is 1985-01-23 and the last is 2026-10-23. The limit was not reached.

## Columns
`#EventID`, `Time` (UTC ISO 8601), `Latitude`, `Longitude` (WGS84 decimal degrees), `Depth/Km`, `Author` (locating body, e.g. BULLETIN-VAX or SURVEY-INGV), `Catalog`, `Contributor`, `ContributorID`, `MagType` (ML, Mw, Md, mb, M, Mwp), `Magnitude`, `MagAuthor`, `EventLocationName` (free text, e.g. "7 km W Abetone (PT)" or "Tirreno Meridionale [Mare]"), `EventType`.

Places are located by coordinates. The bbox includes events offshore and in neighbouring countries, so filter by the Italian boundary or the hex grid. Magnitude types are mixed across the period.
