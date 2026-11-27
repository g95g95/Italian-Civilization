"""Phase 6 data: pack processed tables into the JSON files the static app reads (web/data/).

  tiles.json        geometry-free tile table: position (km), names, region, city, terrain, yields
  borders.json      region outlines, simplified, in the same km coordinates
  cities.json       610 cities (labour-market areas): position, members, yields, districts, citizens, wonders
  e_<eid>.json      one per election: lists with scores and rules, counts per tile / city / Italy
  comuni.json       every comune with every explorer column (loaded only when the explorer opens)
  meta.json         sources, column definitions, game rules, notes
"""
from __future__ import annotations

import json
import math

import geopandas as gpd
import numpy as np
import pandas as pd

from common import ELECTIONS, PROC, WEB, log

OUT = WEB / "data"
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = json.loads((PROC.parent.parent / "config" / "sources.json").read_text())


def dump(name, obj):
    s = json.dumps(obj, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    (OUT / name).write_text(s, encoding="utf-8")
    log("wrote", name, f"{len(s)/1024:.0f} KB")


def clean(a, nd=None):
    """list of numbers with NaN -> None, optionally rounded."""
    out = []
    for v in a:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            out.append(None)
        elif nd is None:
            out.append(int(round(float(v))))
        else:
            out.append(round(float(v), nd))
    return out


def load(name, **kw):
    return pd.read_csv(PROC / name, dtype={"code": str, "main_code": str, "unit": str, "sll": str}, **kw)


def main():
    tiles = gpd.read_file(PROC / "tiles.gpkg").sort_values("tile").reset_index(drop=True)
    assert (tiles.tile.values == np.arange(len(tiles))).all()
    minx, maxy = tiles.x.min(), tiles.y.max()
    tx = ((tiles.x - minx) / 1000).round(3)
    ty = ((maxy - tiles.y) / 1000).round(3)
    com = gpd.read_file(PROC / "comuni.gpkg")
    w = load("weights.csv")
    regions = sorted(com.region.unique())
    rid = {r: i for i, r in enumerate(regions)}
    csll = load("comune_sll.csv").set_index("code").sll
    cities = load("cities.csv").reset_index(drop=True)
    city_idx = {s: i for i, s in enumerate(cities.sll)}

    # other comuni on each tile, by residents
    names = com.set_index("code").name
    wt = w.sort_values("grid_pop", ascending=False)
    others = wt.groupby("tile").code.apply(lambda s: [names[c] for c in s.iloc[1:3]])
    ncom = wt.groupby("tile").code.size()

    terr = load("terrain_tiles.csv").set_index("tile").loc[tiles.tile]
    haz = load("hazards_tiles.csv").set_index("tile").reindex(tiles.tile)
    land_km2 = (w.assign(a=w.area_w * w.code.map(com.set_index("code").area_km2)).groupby("tile").a.sum()).reindex(tiles.tile)
    socio_t = load("tiles_socio.csv").set_index("tile").reindex(tiles.tile) if (PROC / "tiles_socio.csv").exists() else None

    cols = {
        "land_km2": clean(land_km2, 1),
        "elev": clean(terr.elev_mean), "terrain": terr.terrain.fillna("").str[:1].tolist(), "feature": terr.feature.fillna("").str[:1].tolist(),
        "coast": [int(bool(v)) for v in terr.coast], "farmland": clean(terr.farmland, 3), "forest": clean(terr.lc_forest, 2),
        "quakes": clean(haz.quakes_m4.fillna(0)), "landslide_km2": clean(haz.landslide_km2, 1), "flood_km2": clean(haz.flood_km2, 1),
        "flood_pop": clean(haz.flood_pop),
    }
    if socio_t is not None:
        for c in socio_t.columns:
            if c.startswith("jobs_") and c not in ("jobs_total", "jobs_ind"):
                continue  # sector detail is shown per city only
            cols[c] = clean(socio_t[c])
    tile_city = tiles.main_code.map(csll).map(city_idx)
    dump("tiles.json", {
        "d": 10, "n": len(tiles), "x": tx.tolist(), "y": ty.tolist(),
        "name": tiles.main_name.tolist(), "others": [others.get(t, []) for t in tiles.tile],
        "ncom": [int(ncom.get(t, 0)) for t in tiles.tile],
        "reg": [rid[r] for r in tiles.region], "regions": regions, "city": clean(tile_city),
        "land": clean(tiles.land, 3),
    })
    dump("tile_cols.json", cols)  # loaded after the first paint

    # region borders
    reg = com.dissolve(by="region")[["geometry"]]
    reg["geometry"] = reg.geometry.simplify(800)
    lines = []
    for geom in reg.geometry:
        polys = getattr(geom, "geoms", [geom])
        for p in polys:
            if p.area < 30e6:
                continue
            xy = np.asarray(p.exterior.coords)
            lines.append([round(v, 2) for x, y in xy for v in ((x - minx) / 1000, (maxy - y) / 1000)])
    dump("borders.json", lines)

    # cities
    socio_c = load("comuni_socio.csv").set_index("code") if (PROC / "comuni_socio.csv").exists() else None
    members = csll.reset_index().groupby("sll").code.apply(list)
    wonders = load("wonders.csv")
    wonders["city"] = wonders.code.map(csll).map(city_idx)
    cjson, cstats = [], []
    for i, c in cities.iterrows():
        mem = members[c.sll]
        d = {"sll": c.sll, "name": c["name"], "main": c.main_name, "main_code": c.main_code,
             "x": round((c.x - minx) / 1000, 2), "y": round((maxy - c.y) / 1000, 2), "ncom": len(mem),
             "tiles": sorted(int(t) for t in tiles.tile[tile_city == i])}
        st = {}
        if socio_c is not None:
            s = socio_c.loc[[m for m in mem if m in socio_c.index]]
            for k in s.columns:
                if k.startswith("jobs_") or k in SUM_COLS:
                    st[k] = int(round(float(s[k].sum())))
        cjson.append(d)
        cstats.append(st)
    wl = []
    for r in wonders.itertuples():
        wl.append({"kind": r.kind, "id": r.id, "name": r.name, "rank": float(r.rank_value), "label": r.rank_label,
                   "cat": r.category if isinstance(r.category, str) else "",
                   "tile": None if pd.isna(r.tile) else int(r.tile), "city": None if pd.isna(r.city) else int(r.city),
                   "comune": None if pd.isna(r.code) else names.get(str(r.code).zfill(6), None)})
    dump("cities.json", {"cities": cjson, "wonders": wl})
    dump("city_stats.json", cstats)  # loaded after the first paint

    # elections
    elist = []
    for eid, (date, kind, label) in ELECTIONS.items():
        elist.append({"id": eid, "date": date, "kind": kind, "label": label})
        if kind == "referendum":
            export_ref(eid, date, label, csll, city_idx, len(cities), len(tiles))
        else:
            export_party(eid, date, label, kind, csll, city_idx, len(cities), len(tiles))

    comuni_table(com, csll, cities, regions)
    meta(elist)
    import i18n
    i18n.build()
    log("wrote i18n_it.json")


SUM_COLS = {"pop_res", "pop_cens", "taxpayers", "income", "grad", "pop25", "pop65", "foreign", "employed", "unemployed", "labour", "pop15", "jobs_total", "jobs_ind"}


def _cities_from_comuni(df, cols, csll, city_idx, by=None):
    df = df.copy()
    df["city"] = df.code.map(csll).map(city_idx)
    assert df.city.notna().all()
    return df.groupby(["city"] + (by or []))[cols].sum()


def export_party(eid, date, label, kind, csll, city_idx, ncity, ntile):
    P = PROC / "politics"
    L = pd.read_csv(P / "lists.csv")
    L = L[L.election == eid].copy()
    tl = pd.read_csv(P / f"{eid}_tile_lists.csv")
    tt = pd.read_csv(P / f"{eid}_tiles.csv").set_index("tile").reindex(range(ntile))
    cl = pd.read_csv(P / f"{eid}_comune_lists.csv", dtype={"code": str})
    cc = pd.read_csv(P / f"{eid}_comuni.csv", dtype={"code": str})
    # keep lists that matter on the map: >= 0.5% nationally, or first anywhere; the rest -> other
    lead_any = set(tt.lead.dropna()) | set(cc.lead.dropna())
    keep = L[(L.share >= 0.5) | L.list.isin(lead_any) | (L.contest != "national") | L.lrgen.notna()].copy()
    keep = keep.sort_values(["contest", "votes"], ascending=[True, False])
    other = "__other__"
    m = {l: l for l in keep.list}
    tl["k"] = tl.list.map(m).fillna(other)
    cl["k"] = cl.list.map(m).fillna(other)
    order = keep.list.tolist() + ([other] if (~L.list.isin(keep.list)).any() else [])
    lists = []
    for r in keep.itertuples():
        lists.append({"id": r.list, "label": pretty(r.list), "short": r.short if isinstance(r.short, str) and r.short else pretty(r.list, short=True),
                      "contest": r.contest, "share": round(r.share, 2) if r.contest == "national" else None,
                      "votes": int(round(r.votes)),
                      "lr": none(r.lrgen), "econ": none(r.lrecon), "gal": none(r.galtan), "rule": r.rule if isinstance(r.rule, str) else "",
                      "coal": r.coalition if isinstance(r.coalition, str) else "", "note": r.note if isinstance(r.note, str) else ""})
    if other in order:
        rest = L[~L.list.isin(keep.list)]
        lists.append({"id": other, "label": f"Other lists ({len(rest)})", "short": "Other", "contest": "national",
                      "share": round(rest.share.sum(), 2), "votes": int(round(rest.votes.sum())), "lr": None, "econ": None, "gal": None,
                      "rule": "", "coal": "", "note": "lists under 0.5% nationally that lead no tile or comune: " + "; ".join(pretty(x) for x in rest.list)})
    tv = tl.groupby(["k", "tile"]).votes.sum().unstack(fill_value=0).reindex(index=order, columns=range(ntile), fill_value=0)
    cl2 = cl.copy()
    cv = _cities_from_comuni(cl2, ["votes"], csll, city_idx, ["k"]).votes.unstack(0, fill_value=0).reindex(index=order, columns=range(ncity), fill_value=0)
    ccount = _cities_from_comuni(cc, ["electors", "voters", "valid"], csll, city_idx).reindex(range(ncity))
    nat_v = L.groupby(L.list.map(m).fillna(other)).votes.sum().reindex(order)
    t = pd.read_csv(PROC / "elections" / f"{eid}_turnout.csv")
    dump(f"e_{eid}.json", {
        "id": eid, "date": date, "label": label, "kind": kind, "lists": lists,
        "tiles": {"electors": clean(tt.electors.fillna(0)), "voters": clean(tt.voters.fillna(0)), "valid": clean(tt.valid.fillna(0)),
                  "v": [clean(tv.loc[k]) for k in order]},
        "cities": {"electors": clean(ccount.electors), "voters": clean(ccount.voters), "valid": clean(ccount.valid),
                   "v": [clean(cv.loc[k]) for k in order]},
        "nat": {"electors": int(t.electors.sum()), "voters": int(t.voters.sum()), "valid": int(round(t.valid.sum())),
                "v": clean(nat_v.fillna(0))},
    })


def export_ref(eid, date, label, csll, city_idx, ncity, ntile):
    P = PROC / "politics"
    rt = pd.read_csv(P / f"{eid}_ref_tiles.csv")
    rc = pd.read_csv(P / f"{eid}_ref_comuni.csv", dtype={"code": str})
    r = pd.read_csv(PROC / "elections" / f"{eid}_ref.csv")
    qs = sorted(r.question.unique())
    qtext = r.groupby("question").question_text.first()
    cols = ["electors", "voters", "yes", "no"]

    def block(df, n, idx):
        out = {c: [] for c in cols}
        for q in qs:
            s = df[df.question == q].set_index(idx).reindex(range(n)).fillna(0)
            for c in cols:
                out[c].append(clean(s[c]))
        return out

    cty = _cities_from_comuni(rc, cols, csll, city_idx, ["question"]).reset_index()
    nat = r.groupby("question")[cols].sum()
    dump(f"e_{eid}.json", {
        "id": eid, "date": date, "label": label, "kind": "referendum",
        "questions": [{"q": int(q), "text": qtext[q].capitalize() if qtext[q].isupper() else qtext[q]} for q in qs],
        "tiles": block(rt, ntile, "tile"), "cities": block(cty, ncity, "city"),
        "nat": {c: [int(nat.loc[q, c]) for q in qs] for c in cols},
    })


def none(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), 3)


SMALL = {"DI", "DE", "DEL", "DELLA", "E", "PER", "CON", "IL", "LA", "L'", "D'", "IN", "AL"}
KEEPUP = {"PD", "M5S", "UDC", "SVP", "PATT", "PPE", "UV", "UVP", "EPAV", "PDE", "FI", "UCDL", "ALA", "MIR", "PCI"}


def pretty(label: str, short: bool = False) -> str:
    words = []
    vda = str(label).startswith("VDA: ")
    label = str(label)[5:] if vda else label
    import re as _re
    label = _re.sub(r"(?<=[A-Za-z])\?(?=[A-Za-z])", "'", str(label)).replace(" ? ", " – ")
    for wd in label.split():
        u = wd.upper()
        if u in KEEPUP or (len(u) <= 3 and u.startswith("+")):
            words.append(u)
        elif u in SMALL and words:
            words.append(u.lower())
        else:
            words.append(wd.capitalize() if not wd.startswith("(") else "(" + wd[1:].capitalize())
    s = " ".join(words).replace("D'italia", "d'Italia").replace("L'italia", "l'Italia")
    if short:
        s = s.split(" - ")[0]
        s = s if len(s) <= 22 else s[:20].rstrip() + "…"
    return ("VdA: " if vda else "") + s + (" (Valle d'Aosta candidate)" if vda and not short else "")


def comuni_table(com, csll, cities, regions):
    """Explorer table: every comune, every column (rates recomputed from counts)."""
    df = pd.DataFrame({"code": com.code, "name": com.name, "region": com.region, "area_km2": com.area_km2.round(2)})
    df["city"] = df.code.map(csll).map({s: n for s, n in zip(cities.sll, cities.name)})
    terr = load("terrain_comuni.csv").set_index("code")
    haz = load("hazards_comuni.csv").set_index("code")
    df = df.set_index("code")
    df["elev"] = terr.elev_mean.round(0)
    df["farmland"] = (terr.farmland * 100).round(1)
    df["forest"] = (terr.lc_forest * 100).round(1)
    df["quakes"] = haz.quakes_m4
    df["landslide_pct"] = (haz.landslide_km2 / df.area_km2 * 100).round(2)
    df["flood_pct"] = (haz.flood_km2 / df.area_km2 * 100).round(2)
    if (PROC / "comuni_socio.csv").exists():
        s = load("comuni_socio.csv").set_index("code")
        for c in RATE_COLS:
            num, den, scale = RATE_COLS[c]
            df[c] = (s[num] / s[den] * scale).round(2)
        df["pop_res"] = s.pop_res
        df["density"] = (s.pop_res / df.area_km2).round(1)
    shared = set()
    for eid, (date, kind, label) in ELECTIONS.items():
        P = PROC / "politics"
        if kind == "referendum":
            rc = pd.read_csv(P / f"{eid}_ref_comuni.csv", dtype={"code": str})
            for q, g in rc.groupby("question"):
                g = g.set_index("code")
                sfx = f"{eid}" if rc.question.nunique() == 1 else f"{eid}q{q}"
                df[f"yes_{sfx}"] = (g.yes / (g.yes + g.no) * 100).round(2)
                df[f"turnout_{sfx}"] = (g.voters / g.electors * 100).round(2)
            continue
        c = pd.read_csv(P / f"{eid}_comuni.csv", dtype={"code": str}).set_index("code")
        shared |= set(c.index[c.shared])
        df[f"turnout_{eid}"] = (c.voters / c.electors * 100).round(2)
        sv = c.scored_votes.where(c.scored_votes > 0)
        df[f"lr_{eid}"] = (c.lrgen_sum / sv).round(3)
        df[f"econ_{eid}"] = (c.lrecon_sum / sv).round(3)
        df[f"gal_{eid}"] = (c.galtan_sum / sv).round(3)
        df[f"cov_{eid}"] = (c.scored_votes / c.valid * 100).round(1)
        if eid.startswith("cam"):
            df[f"margin_{eid}"] = ((c.cdx - c.csx) / c.valid * 100).round(2)
        L = pd.read_csv(P / "lists.csv")
        L = L[(L.election == eid) & (L.contest == "national") & (L.share >= 2)]
        cl = pd.read_csv(P / f"{eid}_comune_lists.csv", dtype={"code": str})
        for r in L.itertuples():
            s = cl[cl.list == r.list].set_index("code").votes
            key = f"share_{eid}_{r.short}"
            df[key] = (s / c.valid * 100).round(2)
    df["shared_unit"] = df.index.isin(shared)
    w = load("weights.csv").sort_values("grid_pop", ascending=False).drop_duplicates("code").set_index("code").tile
    df["tile"] = w.reindex(df.index).astype(int)
    df = df.reset_index()
    cols = {k: (clean(df[k], 3) if df[k].dtype.kind == "f" else df[k].tolist()) for k in df.columns}
    dump("comuni.json", cols)


RATE_COLS = {
    "income_per_taxpayer": ("income", "taxpayers", 1),
    "income_per_resident": ("income", "pop_res", 1),
    "grad_pct": ("grad", "pop25", 100),
    "old_pct": ("pop65", "pop_cens", 100),
    "foreign_pct": ("foreign", "pop_cens", 100),
    "employment_pct": ("employed", "pop15", 100),
    "unemployment_pct": ("unemployed", "labour", 100),
    "ind_jobs_pct": ("jobs_ind", "jobs_total", 100),
    "jobs_per_resident": ("jobs_total", "pop_res", 1),
}


def meta(elist):
    m = json.loads((PROC.parent.parent / "config" / "columns.json").read_text())
    m["sources"] = SOURCES
    gaps = (PROC.parent.parent / "GAPS.md").read_text(encoding="utf-8").split("## Open", 1)[1]
    m["gaps"] = [l[2:].strip() for l in gaps.splitlines() if l.startswith("- ")]
    if (PROC / "socio_national.json").exists():
        m["national"] = {k: v["value"] for k, v in json.loads((PROC / "socio_national.json").read_text()).items()}
    m["elections"] = elist
    dump("meta.json", m)


if __name__ == "__main__":
    main()
