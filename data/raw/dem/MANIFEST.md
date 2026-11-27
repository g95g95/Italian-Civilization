# dem — elevation

Download date: 2026-11-27

## 1. Copernicus DEM GLO-90 (primary): `tiles/`

- Bucket: `s3://copernicus-dem-90m` (AWS Open Data, public). Readme: https://copernicus-dem-90m.s3.amazonaws.com/readme.html
- URL pattern: `https://copernicus-dem-90m.s3.amazonaws.com/{name}/{name}.tif`, where `name = Copernicus_DSM_COG_30_N{lat:02}_00_E{lon:03}_00_DEM`
- Tile index used for selection: https://copernicus-dem-90m.s3.amazonaws.com/tileList.txt
- Selection: every tile that exists for lat N35–N46 and lon E006–E018, plus N47 E010/E011/E012. The extra N47 tiles cover the Alto Adige strip north of 47°N (Vetta d'Italia, 47.09°N). Missing tiles are open sea.
- 126 tiles, 378 MB in total. `tile_list.txt` lists them and `download_log.txt` records the HTTP status and bytes for each tile (all 200).
- The selection also includes neighbouring land: Corsica, the Swiss and Austrian Alps, Slovenia, Croatia, Bosnia, Montenegro, Albania, NE Tunisia and Malta.
- Format: Cloud-Optimized GeoTIFF, float32, DEFLATE with predictor 3, internal overviews ×2 and ×4. There is no nodata value; sea has no tile, and the readme says to "assume height values equal to zero".
- CRS: EPSG:4326 (WGS84 horizontal). Heights are metres above the EGM2008 geoid.
- Resolution: 3 arc-seconds (1/1200°, ≈ 90 m N–S and ≈ 65 m E–W at 45°N). Tiles are 1200 × 1200 px, 1° × 1°. AWS removed the shared south/east row and column; `AREA_OR_POINT=Point`.
- Values: elevation in metres. This is a **DSM**: it includes buildings and vegetation.
- Source product: COP-DEM_GLO-90-DGED (TanDEM-X based). The bucket readme does not give the release; the AWS buckets carry the 2021 public release. Acquisitions date from 2011–2015.
- Licence: GLO-90 is "available on a free basis for the general public" under the Copernicus DEM licence (https://spacedata.copernicus.eu/en/web/guest/collections/copernicus-digital-elevation-model/#Licencing). It is free worldwide for any use. Required attribution: "© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved".

## 2. TINITALY 1.1 at 250 m (supplementary, bare-earth DTM): `tinitaly_wcs/tinitaly_1_1_dem_250m_epsg32632.tif`

The spec's first choice is TINITALY 10 m, which is about 193 zipped tiles and many GB; I did not download it. INGV also serves the DEM through an OGC WCS 2.0.1 (GeoServer):
`https://tinitaly.pi.ingv.it/TINItaly_1_1/wcs?service=WCS&request=GetCapabilities`, coverage `TINItaly_1_1__tinitaly_dem`. The native grid is 10 m, EPSG:32632, x 312,500–1,320,000 and y 3,930,000–5,222,500.

- Retrieval: 30 chunks of 250 km × 250 km, each fetched as
  `...&version=2.0.1&request=GetCoverage&coverageId=TINItaly_1_1__tinitaly_dem&format=image/tiff&SCALEFACTOR=0.04&subset=E(x0,x1)&subset=N(y0,y1)`.
  The chunks were mosaicked unchanged onto the native grid origin. A single full-extent request timed out with HTTP 504.
- Server quirk: chunks with no source granules came back filled with 0 instead of -9999. Those all-zero chunks, which lie wholly outside Italy, were set to nodata. One empty chunk with a 50 m offset (sea east of Salento) was dropped.
- CRS: **EPSG:32632**, the project CRS. Resolution: 250 m. Size: 4030 × 5170 px, float32, nodata -9999, 15 MB.
- Values: bare-ground elevation in metres. Valid pixels: 4,818,294 (≈ 301,000 km²), range -40 to 4763 m, mean 536 m.
- Decimation: GeoServer subsampled the 10 m grid with its default interpolation, which is nearest neighbour. Each pixel is therefore a point sample, not a 250 m block mean, so peaks are underestimated (max 4763 m against Mont Blanc's 4808 m).
- Vintage: TINITALY/1.1, released January 2023.
- Licence: **CC BY 4.0**. Required citation: Tarquini S., I. Isola, M. Favalli, A. Battistini, G. Dotta (2023). TINITALY, a digital elevation model of Italy with a 10 meters cell size (Version 1.1). INGV. https://doi.org/10.13127/tinitaly/1.1
- Also on offer but not downloaded: a 17 MB "colour-shaded image of Italy from a 100 m DEM" (https://tinitaly.pi.ingv.it/AJK764GHJ0987NBV/TINITALY_image.zip). It is a picture and holds no elevation values. The WCS could deliver 100 m in the same way, about 10075 × 12925 px.
