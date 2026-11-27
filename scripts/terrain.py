"""Phase 5 (part): terrain from rasters, per tile and per comune.

Elevation: TINITALY 1.1 (INGV), 250 m resampling of the 10 m DEM, EPSG:32632.
Land cover: LUISA Base Map 2018 (JRC), the 100 m refinement of CORINE Land Cover 2018,
CLC level-3 code = LUISA code // 10 (4000 = all wetlands).

Writes data/processed/terrain_tiles.csv and terrain_comuni.csv with:
  elev_mean        mean elevation of land pixels, m
  terrain          plains (< 300 m), hills (300-600 m), mountains (>= 600 m), from elev_mean
  lc_<group>       share of land pixels in each land-cover group
  farmland         = lc_farm (CLC 2xx) -> the Food yield
  feature          forest when forest covers at least half the land; marsh when wetlands
                   and lagoons cover at least 5% of the tile; else none
  coast            sea (CLC 523) covers at least 1% of the tile
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize

from common import PROC, RAW, log

DEM = RAW / "dem" / "tinitaly_wcs" / "tinitaly_1_1_dem_250m_epsg32632.tif"
LC = RAW / "landcover" / "luisa_basemap_2018" / "luisa_basemap_2018_100m_italy_epsg3035.tif"

GROUPS = {  # CLC level-1/2 groups, by LUISA code range
    "urban": (1000, 2000), "farm": (2000, 3000), "forest": (3100, 3200), "open": (3200, 3400),
    "wetland": (4000, 4001), "water": (5100, 5200), "lagoon": (5210, 5230),
}
SEA = 5230


def zone_ids(shapes, ids, ref):
    return rasterize(zip(shapes, ids), out_shape=ref.shape, transform=ref.transform, fill=-1, dtype="int32")


def elevation(tiles, com):
    with rasterio.open(DEM) as r:
        z = r.read(1)
        valid = z != r.nodata
        tz = zone_ids(tiles.geometry, tiles.tile, r)
        cz = zone_ids(com.geometry, np.arange(len(com)), r)
    land = cz >= 0
    out = {}
    for name, zid, n in (("tile", tz, tiles.tile.max() + 1), ("comune", cz, len(com))):
        m = valid & land & (zid >= 0)
        s = np.bincount(zid[m], weights=z[m], minlength=n)
        c = np.bincount(zid[m], minlength=n)
        mx = pd.Series(z[m]).groupby(zid[m]).max().reindex(range(n))
        out[name] = pd.DataFrame({"elev_mean": np.where(c > 0, s / np.maximum(c, 1), np.nan),
                                  "elev_max": mx.values, "elev_px": c})
    return out


def landcover(tiles, com):
    with rasterio.open(LC) as r:
        a = r.read(1)
        crs = r.crs
        t3 = tiles.to_crs(crs)
        c3 = com.to_crs(crs)
        tz = zone_ids(t3.geometry, t3.tile, r)
        cz = zone_ids(c3.geometry, np.arange(len(c3)), r)
    out = {}
    for name, zid, n in (("tile", tz, tiles.tile.max() + 1), ("comune", cz, len(com))):
        inz = zid >= 0
        df = {}
        total = np.bincount(zid[inz], minlength=n)
        sea = np.bincount(zid[inz & (a == SEA)], minlength=n)
        landpx = np.bincount(zid[inz & (a > 0) & (a != SEA)], minlength=n)
        for g, (lo, hi) in GROUPS.items():
            m = inz & (a >= lo) & (a < hi)
            df["lc_" + g] = np.bincount(zid[m], minlength=n) / np.maximum(landpx, 1)
        df = pd.DataFrame(df)
        df["sea_share"] = sea / np.maximum(total, 1)
        df["lc_px"] = landpx
        out[name] = df
    return out


def classify(df):
    df["terrain"] = np.select([df.elev_mean < 300, df.elev_mean < 600, df.elev_mean >= 600],
                              ["plains", "hills", "mountains"], default="")
    df["farmland"] = df.lc_farm
    wet = df.lc_wetland + df.lc_lagoon
    df["feature"] = np.select([df.lc_forest >= 0.5, wet >= 0.05], ["forest", "marsh"], default="")
    df["coast"] = df.sea_share >= 0.01
    df.loc[df.lc_px == 0, ["farmland", "feature"]] = [np.nan, ""]
    return df


def main():
    tiles = gpd.read_file(PROC / "tiles.gpkg")
    com = gpd.read_file(PROC / "comuni.gpkg")
    e, l = elevation(tiles, com), landcover(tiles, com)
    t = classify(pd.concat([e["tile"], l["tile"]], axis=1).loc[tiles.tile].reset_index(names="tile"))
    c = classify(pd.concat([e["comune"], l["comune"]], axis=1))
    c.insert(0, "code", com.code.values)
    t.to_csv(PROC / "terrain_tiles.csv", index=False)
    c.to_csv(PROC / "terrain_comuni.csv", index=False)
    log("tiles terrain", t.terrain.value_counts().to_dict(), "features", t.feature.value_counts().to_dict(), "coast", int(t.coast.sum()))
    log("comuni without DEM pixel", int(c.elev_mean.isna().sum()), "without land-cover pixel", int((c.lc_px == 0).sum()))


if __name__ == "__main__":
    main()
