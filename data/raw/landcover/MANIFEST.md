# landcover — land cover / land use

Download date: 2026-11-27

## CORINE Land Cover 2018 (requested): NOT OBTAINED

None of the EEA or Copernicus Land routes could be reached from this environment:
- `https://image.discomap.eea.europa.eu/arcgis/rest/services/Corine/CLC2018_WM/MapServer` (and `/arcgis/rest/services`): the TLS handshake was reset. The agent proxy reported `ws_closed_mid_exchange` (the tunnel to the egress proxy closed). Tried several times.
- `https://sdi.eea.europa.eu/data/` and the catalogue API: same failure (`ws_closed_mid_exchange`).
- `https://discomap.eea.europa.eu/` and `https://www.eea.europa.eu/`: same failure.
- `https://land.copernicus.eu/`: HTTP 403 from the egress proxy (host not allowed).

I therefore saved two substitutes. **(A) is closest to CORINE** and keeps the CLC nomenclature. (B) is the fallback named in the task.

---

## A. LUISA Base Map 2018 (JRC): a CLC 2018 refinement at 100 m: `luisa_basemap_2018/`

LUISA is the JRC's "refined CORINE". It takes CLC 2018 as its starting layer and refines it with higher-resolution sources such as Copernicus HRLs, Urban Atlas, OSM/TomTom roads and rail, and settlement data. It keeps the CLC level-3 classes and adds a 4th digit where a class is subdivided. Reference: Pigaiani C., Batista e Silva F. (2021), *The LUISA Base Map 2018*, JRC Technical Report (EUR 30663 EN). This citation is from memory; verify it before publishing.

| File | URL / note | Size |
|---|---|---|
| `original/LUISA_basemap_020321_100m.tif` | https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/LUISA/EUROPE/Basemaps/2018/VER2021-03-24/LUISA_basemap_020321_100m.tif (identical to `.../2018/LATEST/`) | 327 MB |
| `original/Legend_Base_Map_2018.xlsx` | same folder | 11 kB |
| `original/QGIS_legend_Base_Map_2018.qml` | same folder | 6 kB |
| `original/copyright.txt` | same folder | <1 kB |
| `luisa_basemap_2018_100m_italy_epsg3035.tif` | **Italy crop** made here, see below | 16 MB |

- Vintage: reference year 2018. File version 2021-03-24.
- Original file: EPSG:3035, 100 m, 65000 × 46000 px, int32, nodata 0, covering the whole of Europe.
- Italy crop: EPSG:3035, 100 m, window x 4,040,000–5,070,000 and y 1,370,000–2,690,000. That window is the ISTAT grid extent plus a margin of about 13 km. Size 10300 × 13200 px. Values were cast to **uint16** without loss, nodata 0, DEFLATE. The values themselves are unchanged.
- Licence: **CC BY 4.0**. From `copyright.txt`: "(c) European Union, 1995-2026 … licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) licence. Reuse is allowed provided appropriate credit is given and any changes are indicated." CLC 2018 itself is © EEA / Copernicus Land Monitoring Service.

### Value legend (LUISA code → CLC 2018 code)
For every class except 4000, `CLC code = LUISA code // 10`. The 4th digit only subdivides a CLC class. Values present in the Italy crop:

| LUISA | Label | CLC |
|---|---|---|
| 1111 | High density urban fabric | 111 |
| 1121 / 1122 / 1123 | Medium / low / isolated-very-low density urban fabric | 112 |
| 1130 | Urban vegetation | (LUISA-specific; no CLC equivalent, from 11x) |
| 1210 | Industrial or commercial units | 121 |
| 1221 / 1222 | Road and rail networks / major stations | 122 |
| 1230 | Port areas | 123 |
| 1241 / 1242 | Airport areas / airport terminals | 124 |
| 1310 / 1320 / 1330 | Mineral extraction / dump / construction sites | 131 / 132 / 133 |
| 1410 | Green urban areas | 141 |
| 1421 / 1422 | Sport and leisure, green / built-up | 142 |
| 2110 / 2120 / 2130 | Non-irrigated arable / permanently irrigated / rice fields | 211 / 212 / 213 |
| 2210 / 2220 / 2230 | Vineyards / fruit trees and berries / olive groves | 221 / 222 / 223 |
| 2310 | Pastures | 231 |
| 2410 / 2420 / 2430 / 2440 | Annual + permanent crops / complex cultivation / agriculture with natural vegetation / agro-forestry | 241 / 242 / 243 / 244 |
| 3110 / 3120 / 3130 | Broad-leaved / coniferous / mixed forest | 311 / 312 / 313 |
| 3210 / 3220 / 3230 / 3240 | Natural grassland / moors and heathland / sclerophyllous vegetation / transitional woodland-shrub | 321 / 322 / 323 / 324 |
| 3310 / 3320 / 3330 / 3340 / 3350 | Beaches-dunes-sand / bare rock / sparsely vegetated / burnt areas / glaciers and perpetual snow | 331 / 332 / 333 / 334 / 335 |
| 4000 | Wetlands (all wetlands merged) | 411–423 |
| 5110 / 5120 | Water courses / water bodies | 511 / 512 |
| 5210 / 5220 / 5230 | Coastal lagoons / estuaries / sea and ocean | 521 / 522 / 523 |
| 0 | NoData (outside the mapped countries) | — |

The full legend is in `original/Legend_Base_Map_2018.xlsx`. Note that the class codes are CLC **3-digit codes ×10** (plus subdivisions), not the CLC raster "grid codes" 1–44.

---

## B. ESA WorldCover 2021 v200 (the specified fallback): `esa_worldcover_2021/esa_worldcover_2021_v200_ov8_italy_epsg4326.tif`

- Source: AWS bucket `esa-worldcover`. URL pattern `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif`. I used 23 tiles: N33/N36/N39/N42/N45 × E006/E009/E012/E015/E018. N33E015 and N33E018 do not exist.
- Method: each COG's **internal overview level 2 (1/8 decimation)** was read over HTTP range requests and the tiles were mosaicked unchanged. The publisher's overview resampling method is not stated in the tile metadata, so these are publisher overviews, not a mode or majority aggregate made here.
- Extent: lon 6–19°E, lat 35–48°N. CRS: **EPSG:4326**. Pixel size: 1/1500° (≈ 74 m N–S, ≈ 52 m E–W at 45°N). Size 19500 × 19500 px, uint8, nodata 0, 30 MB.
- Vintage: 2021, product version V2.0.0, created 2022-10-21.
- Licence: **CC BY 4.0** (from the tile metadata). Attribution: "ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium". Docs: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf
- Legend: 10 Tree cover, 20 Shrubland, 30 Grassland, 40 Cropland, 50 Built-up, 60 Bare/sparse vegetation, 70 Snow and ice, 80 Permanent water bodies, 90 Herbaceous wetland, 95 Mangroves, 100 Moss and lichen, 0 No data.
