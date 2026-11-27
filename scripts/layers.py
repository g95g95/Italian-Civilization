"""Phase 5 (part): cities, hazards and wonders.

Cities: ISTAT labour-market areas (sistemi locali del lavoro, SLL 2011, composition at
1 Jan 2023), one city per SLL, placed on the comune ISTAT flags as its main comune.
  -> data/processed/cities.csv (sll, name, main_code, x, y) and comune_sll.csv (code, sll)

Hazards:
  quakes_m4     INGV events of magnitude >= 4.0, 1985-01-01 to 2026-11-01, epicentre on the tile/comune
  landslide_km2 ISPRA area in landslide hazard classes P3+P4 (high, very high), mosaic 2024
  flood_km2     ISPRA area in flood hazard class P2 (medium probability), mosaic 2020
  flood_pop     ISPRA residents in flood hazard P2 areas (2021 census)
  areas are spread by area, residents by residents.
  -> data/processed/hazards_tiles.csv, hazards_comuni.csv

Wonders (data/processed/wonders.csv): UNESCO World Heritage sites (UNESCO 2023 export) and
the main ports by goods handled (Eurostat mar_go_am_it, latest year, located with GISCO
port points). Universities are added by wonders_mur() when the MUR data is present.
"""
from __future__ import annotations

import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd

import spread
from common import CRS, PROC, RAW, log, write_csv

XW = None


def to_current(df: pd.DataFrame, date: str, code_col: str = "code") -> pd.DataFrame:
    """Re-key a comune table from codes in force on `date` to current comuni (counts summed)."""
    global XW
    if XW is None:
        XW = pd.read_csv(PROC / "crosswalk.csv", dtype=str)
    x = XW[XW.date == date].set_index("code").targets
    df = df.copy()
    df["unit"] = df[code_col].map(x)
    miss = df[df.unit.isna()]
    assert miss.empty, f"{len(miss)} codes of {date} not in the crosswalk: {miss[code_col].tolist()[:10]}"
    return df


def cities():
    z = zipfile.ZipFile(RAW / "istat_sll" / "Composizione-SLL2011-01012023.zip")
    n = [x for x in z.namelist() if x.endswith(".csv")][0]
    s = pd.read_csv(z.open(n), sep=";", encoding="latin1", dtype=str)
    s.columns = [c.replace("\xa0", "").strip() for c in s.columns]
    s = s.rename(columns={"PRO_COM_T": "code", "COD_SLL_2011_2018_T": "sll", "DEN_SLL_2011_2018": "sll_name",
                          "CAPOL_SLL_2011_2018": "main"})
    s = to_current(s, "20230101")
    s["cur"] = s.unit.str.split("|")
    s = s.explode("cur")
    # a comune that absorbed a comune of another SLL keeps its own SLL (Lirio into Montalto
    # Pavese, 2026); any other cross-SLL merger stops the build
    cs = s.drop_duplicates(["cur", "sll"])
    multi = cs[cs.duplicated("cur", keep=False)]
    keep = multi[multi.code == multi.cur]
    assert set(keep.cur) == set(multi.cur), multi
    cs = pd.concat([cs[~cs.cur.isin(multi.cur)], keep])
    cs[["cur", "sll"]].rename(columns={"cur": "code"}).to_csv(PROC / "comune_sll.csv", index=False)
    mains = s[s.main.str.strip() == "1"].drop_duplicates("sll")
    assert set(mains.cur) <= set(cs.cur)
    assert len(mains) == s.sll.nunique() == 610
    com = gpd.read_file(PROC / "comuni.gpkg").set_index("code")
    pt = com.geometry.loc[mains.cur].representative_point()
    w = spread.weights().merge(com[["area_km2"]], left_on="code", right_index=True)
    pop_sll = cs.merge(w.groupby("code").grid_pop.sum().rename("p"), left_on="cur", right_index=True).groupby("sll").p.sum()
    out = pd.DataFrame({"sll": mains.sll.values, "name": mains.sll_name.str.strip().str.title().values,
                        "main_code": mains.cur.values, "main_name": com.loc[mains.cur, "name"].values,
                        "x": pt.x.values, "y": pt.y.values})
    out["grid_pop"] = out.sll.map(pop_sll)
    out = out.sort_values("grid_pop", ascending=False)
    out.to_csv(PROC / "cities.csv", index=False)
    log("cities", len(out), "largest", out.name.head(5).tolist())


def points_to_zones(lon, lat):
    tiles = gpd.read_file(PROC / "tiles.gpkg")
    com = gpd.read_file(PROC / "comuni.gpkg")
    p = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs="EPSG:4326").to_crs(CRS)
    t = gpd.sjoin(p, tiles[["tile", "geometry"]], how="left", predicate="within").groupby(level=0).tile.first()
    c = gpd.sjoin(p, com[["code", "geometry"]], how="left", predicate="within").groupby(level=0).code.first()
    return t, c, p


def hazards():
    q = pd.read_csv(RAW / "ingv" / "ingv_events_M4_1985-2026.txt", sep="|")
    q = q[(q.Magnitude >= 4.0) & (q.Time >= "1985-01-01") & (q.Time < "2026-11-01")]
    t, c, _ = points_to_zones(q.Longitude.values, q.Latitude.values)
    qt = t.dropna().astype(int).value_counts().rename("quakes_m4")
    qc = c.dropna().value_counts().rename("quakes_m4")
    log("earthquakes M4+", len(q), "on land tiles", int(qt.sum()), "in a comune", int(qc.sum()))

    p = pd.read_csv(RAW / "ispra" / "pir_comuni.csv", dtype={"pro_com": str})
    p = p.copy()
    p["code"] = p.pro_com.str.zfill(6)
    num = {"ar_fr_p3p4": "landslide_km2", "ar_id_p2": "flood_km2", "pop_idr_p2": "flood_pop"}
    for k in num:
        p[k] = pd.to_numeric(p[k], errors="coerce")
        p.loc[p[k] < 0, k] = np.nan  # -1 = not available
    date = _register_for(set(p.code))
    p = to_current(p, date)
    p = p.rename(columns=num)
    cols = list(num.values())
    # areas by area, residents by residents
    areas = spread.to_tiles(p[["unit", "landslide_km2", "flood_km2"]].fillna(0), ["landslide_km2", "flood_km2"], mode="area")
    pops = spread.to_tiles(p[["unit", "flood_pop"]], ["flood_pop"])
    ht = areas.merge(pops, on="tile", how="outer").set_index("tile")
    ht["quakes_m4"] = qt
    ht["quakes_m4"] = ht.quakes_m4.fillna(0)
    ht.reset_index().to_csv(PROC / "hazards_tiles.csv", index=False)
    hc = p.groupby("unit")[cols].sum(min_count=1).reset_index()
    hc = hc.assign(code=hc.unit.str.split("|")).explode("code")
    assert not hc.code.duplicated().any()
    hc = hc.set_index("code")[cols]
    hc["quakes_m4"] = qc
    hc["quakes_m4"] = hc.quakes_m4.fillna(0)
    hc.reset_index().to_csv(PROC / "hazards_comuni.csv", index=False)
    log("ISPRA register date", date, "landslide km2", round(p.landslide_km2.sum()), "flood km2", round(p.flood_km2.sum()))


def _register_for(codes: set[str]) -> str:
    """The ISTAT register date whose code set best matches a table's codes."""
    xw = pd.read_csv(PROC / "crosswalk.csv", dtype=str, usecols=["date", "code"])
    best = max(xw.date.unique(), key=lambda d: (len(codes & set(xw[xw.date == d].code)), d))
    missing = codes - set(xw[xw.date == best].code)
    assert len(missing) == 0, (best, sorted(missing)[:10])
    return best


def wonders():
    rows = []
    u = pd.read_csv(RAW / "unesco" / "whc-sites-2023_github-mirror.csv", encoding="utf-8-sig")
    u = u[u.iso_code.fillna("").str.split(",").apply(lambda xs: "it" in [x.strip() for x in xs])]
    t, c, _ = points_to_zones(u.longitude.values, u.latitude.values)
    for i, r in enumerate(u.itertuples()):
        rows.append({"kind": "unesco", "id": f"whc{r.id_no}", "name": r.name_en, "rank_value": int(str(r.date_inscribed)[:4]),
                     "rank_label": f"inscribed {str(r.date_inscribed)[:4]}", "category": r.category,
                     "lon": r.longitude, "lat": r.latitude, "tile": t.iloc[i], "code": c.iloc[i]})
    # ports: total gross weight of goods handled, latest year with data
    p = pd.read_csv(RAW / "ports" / "eurostat_mar_go_am_it_2015plus.sdmx.csv", dtype=str)
    p = p[(p.direct == "TOTAL") & (p.cargo == "TOTAL") & (p.rep_mar.str.startswith("IT_0"))]
    p["v"] = pd.to_numeric(p.OBS_VALUE, errors="coerce")
    yr = p.dropna(subset=["v"]).TIME_PERIOD.max()
    p = p[(p.TIME_PERIOD == yr) & p.v.notna()].copy()
    p["locode"] = p.rep_mar.str[4:]
    z = f"zip://{RAW / 'ports' / 'GISCO_PORT_2013_SH.zip'}"
    shp = [n for n in zipfile.ZipFile(RAW / "ports" / "GISCO_PORT_2013_SH.zip").namelist() if n.endswith(".shp") and "PT" in n.upper()]
    g = gpd.read_file(f"{z}!{shp[0]}").to_crs("EPSG:4326")
    idcol = [c for c in g.columns if c.upper() == "PORT_ID"][0]
    g = g.set_index(g[idcol].str.strip())
    p = p[p.locode.isin(g.index)]
    lon, lat = g.loc[p.locode].geometry.x.values, g.loc[p.locode].geometry.y.values
    t, c, _ = points_to_zones(lon, lat)
    at = gpd.read_file(f"{z}!PORT_2013_SH/Data/PORT_AT_2013.dbf")
    names = dict(zip(at.PORT_ID.str.strip(), at.PORT_NAME))
    for i, r in enumerate(p.itertuples()):
        rows.append({"kind": "port", "id": r.locode, "name": str(names.get(r.locode, r.locode)).title(), "rank_value": r.v,
                     "rank_label": f"{r.v/1000:,.1f} million t handled in {yr}", "category": "",
                     "lon": lon[i], "lat": lat[i], "tile": t.iloc[i], "code": c.iloc[i]})
    w = pd.DataFrame(rows)
    # ports on the shoreline can fall just outside the generalised comune polygon: nearest comune
    com = gpd.read_file(PROC / "comuni.gpkg")
    tiles = gpd.read_file(PROC / "tiles.gpkg")
    miss = w.code.isna() | w.tile.isna()
    if miss.any():
        pts = gpd.GeoDataFrame(w[miss], geometry=gpd.points_from_xy(w[miss].lon, w[miss].lat), crs="EPSG:4326").to_crs(CRS)
        nc = gpd.sjoin_nearest(pts, com[["code", "geometry"]], how="left", max_distance=3000)
        nt = gpd.sjoin_nearest(pts, tiles[["tile", "geometry"]], how="left", max_distance=3000)
        w.loc[miss, "code"] = w.loc[miss, "code"].fillna(nc.groupby(level=0).code_right.first() if "code_right" in nc else nc.groupby(level=0).code.first())
        w.loc[miss, "tile"] = w.loc[miss, "tile"].fillna(nt.groupby(level=0).tile_right.first() if "tile_right" in nt else nt.groupby(level=0).tile.first())
    w.to_csv(PROC / "wonders.csv", index=False)
    log("wonders", w.kind.value_counts().to_dict(), "unplaced (abroad or at sea)", int(w.tile.isna().sum()))


def main():
    cities()
    hazards()
    wonders()


if __name__ == "__main__":
    main()
