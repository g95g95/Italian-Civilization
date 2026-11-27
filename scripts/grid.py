"""Phase 2: hex grid and population weights.

Writes
  data/processed/tiles.gpkg        one row per kept tile (id, q, r, centre, land share, main comune)
  data/processed/weights.csv       comune x tile: pop_w (share of the comune's 2021 residents on
                                   the tile), area_w (share of the comune's area)

Grid: pointy-top hexagons, 10 km flat to flat, in EPSG:32632. Axial coordinates (q, r);
centre x = X0 + D*(q + r/2), y = Y0 - 1.5*R*r, with D = 10 km and R = D/sqrt(3).
A tile is kept when at least 15% of it is land (inside some current comune).

Population weights come from the ISTAT 2021 census 1 km grid. A cell that crosses comune
borders is split by area among the comuni it touches; each piece is placed on the tile
that holds its centroid. Pieces whose centroid falls on a dropped tile (coastal slivers)
move to the nearest kept tile, so every resident counted in the grid stays on the map.
A comune with no resident in the grid (none at present) would fall back to area weights.
"""
from __future__ import annotations

import math

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import Polygon

from common import CRS, PROC, RAW, log

D = 10_000.0
R = D / math.sqrt(3)
MIN_LAND = 0.15
X0, Y0 = 300_000.0, 5_300_000.0  # arbitrary origin, metres in EPSG:32632


def centre(q, r):
    return X0 + D * (q + r / 2.0), Y0 - 1.5 * R * r


def to_axial(x, y):
    """Nearest hex (q, r) for points, by cube rounding."""
    r = (Y0 - y) / (1.5 * R)
    q = (x - X0) / D - r / 2.0
    s = -q - r
    rq, rr, rs = np.round(q), np.round(r), np.round(s)
    dq, dr, ds = np.abs(rq - q), np.abs(rr - r), np.abs(rs - s)
    fix_q = (dq > dr) & (dq > ds)
    fix_r = ~fix_q & (dr > ds)
    rq = np.where(fix_q, -rr - rs, rq)
    rr = np.where(fix_r, -rq - rs, rr)
    return rq.astype(int), rr.astype(int)


def hexagon(cx, cy):
    return Polygon([(cx + R * math.cos(math.radians(60 * k + 30)), cy + R * math.sin(math.radians(60 * k + 30))) for k in range(6)])


def main():
    com = gpd.read_file(PROC / "comuni.gpkg")
    land = com.geometry.union_all()
    minx, miny, maxx, maxy = land.bounds
    rows = []
    for r in range(int((Y0 - maxy) / (1.5 * R)) - 2, int((Y0 - miny) / (1.5 * R)) + 3):
        for q in range(int((minx - X0) / D - r / 2) - 2, int((maxx - X0) / D - r / 2) + 3):
            cx, cy = centre(q, r)
            if minx - D <= cx <= maxx + D and miny - D <= cy <= maxy + D:
                rows.append((q, r, cx, cy))
    h = gpd.GeoDataFrame(rows, columns=["q", "r", "x", "y"], geometry=[hexagon(cx, cy) for _, _, cx, cy in rows], crs=CRS)
    h = h[h.intersects(land)].copy()
    hex_area = h.geometry.iloc[0].area

    # comune x hex area overlay
    ov = gpd.overlay(com[["code", "geometry"]], h[["q", "r", "geometry"]], how="intersection", keep_geom_type=True)
    ov["a"] = ov.geometry.area
    landshare = ov.groupby(["q", "r"]).a.sum() / hex_area
    h = h.set_index(["q", "r"])
    h["land"] = landshare
    h = h[h.land >= MIN_LAND].reset_index()
    h["tile"] = np.arange(len(h))
    kept = {(q, r): t for q, r, t in zip(h.q, h.r, h.tile)}
    log("tiles kept", len(h), "of", len(landshare), "touching land")

    # population pieces: ISTAT 2021 1 km grid split along comune borders
    pg = gpd.read_file(f"zip://{RAW / 'popgrid' / 'GrigliaPop2021_Ind_ITA.zip'}!GrigliaPop2021_Ind_ITA.shp", columns=["GRD_ID", "T"])
    pg = pg[pg["T"] > 0].to_crs(CRS)
    pg["cell"] = np.arange(len(pg))
    j = gpd.sjoin(pg[["cell", "T", "geometry"]], com[["code", "geometry"]], predicate="intersects", how="inner")
    n = j.groupby("cell").code.transform("size")
    single = j[n == 1]
    multi = pg[pg.cell.isin(j[n > 1].cell)]
    pieces = gpd.overlay(multi[["cell", "T", "geometry"]], com[["code", "geometry"]], how="intersection", keep_geom_type=True)
    pieces["a"] = pieces.geometry.area
    pieces = pieces[pieces.a > 0]
    pieces["T"] = pieces["T"] * pieces.a / pieces.groupby("cell").a.transform("sum")
    cs = single.geometry.centroid
    cp = pieces.geometry.centroid
    pts = pd.DataFrame({
        "code": np.r_[single.code.values, pieces.code.values],
        "pop": np.r_[single["T"].values, pieces["T"].values],
        "x": np.r_[cs.x.values, cp.x.values], "y": np.r_[cs.y.values, cp.y.values]})
    lost = pg["T"].sum() - pts["pop"].sum()
    log("grid residents", int(pg["T"].sum()), "placed in comuni", round(pts["pop"].sum()), "outside any comune", round(lost))

    tree = cKDTree(h[["x", "y"]].values)

    def place(x, y):
        q, r = to_axial(x, y)
        t = np.array([kept.get((a, b), -1) for a, b in zip(q, r)])
        miss = t < 0
        if miss.any():
            _, i = tree.query(np.c_[x[miss], y[miss]])
            t[miss] = h.tile.values[i]
        return t, miss

    pts["tile"], moved = place(pts.x.values, pts.y.values)
    log("population moved from dropped slivers to the nearest kept tile", round(pts["pop"][moved].sum()))
    pw = pts.groupby(["code", "tile"], as_index=False)["pop"].sum()
    pw["pop_w"] = pw["pop"] / pw.groupby("code")["pop"].transform("sum")

    # area weights (comune area on kept tiles; area on dropped tiles goes to the nearest kept tile)
    ovc = ov.copy()
    c = ovc.geometry.representative_point()
    ovc["tile"], _ = place(c.x.values, c.y.values)
    # pieces on kept tiles must stay on their own tile
    own = [kept.get((a, b), -1) for a, b in zip(ovc.q, ovc.r)]
    ovc["tile"] = np.where(np.array(own) >= 0, own, ovc.tile)
    aw = ovc.groupby(["code", "tile"], as_index=False).a.sum()
    aw["area_w"] = aw.a / aw.groupby("code").a.transform("sum")

    w = aw[["code", "tile", "area_w"]].merge(pw[["code", "tile", "pop", "pop_w"]], on=["code", "tile"], how="outer").fillna(0)
    nopop = set(com.code) - set(pw.code)
    if nopop:
        log("comuni with no residents in the grid -> area weights:", sorted(nopop))
        w.loc[w.code.isin(nopop), "pop_w"] = w.loc[w.code.isin(nopop), "area_w"]
    assert set(w.code) == set(com.code)
    w.rename(columns={"pop": "grid_pop"}).to_csv(PROC / "weights.csv", index=False)

    # tile attributes: main comune by residents, region of the main comune
    m = w.rename(columns={"pop": "grid_pop"}).merge(com[["code", "name", "region"]], on="code")
    m["k"] = m.grid_pop + m.area_w * 1e-6
    main = m.sort_values("k", ascending=False).drop_duplicates("tile").set_index("tile")
    h["main_code"] = h.tile.map(main.code)
    h["main_name"] = h.tile.map(main.name)
    h["region"] = h.tile.map(main.region)
    h["grid_pop"] = h.tile.map(w.groupby("tile")["pop"].sum()).fillna(0)
    h[["tile", "q", "r", "x", "y", "land", "main_code", "main_name", "region", "grid_pop", "geometry"]].to_file(PROC / "tiles.gpkg", driver="GPKG")
    log("tiles written", len(h), "grid residents on tiles", int(h.grid_pop.sum()))


if __name__ == "__main__":
    main()
