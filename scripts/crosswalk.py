"""Phase 1: comune crosswalk and current boundary set.

Builds
  data/processed/crosswalk.csv  every comune code in force on any election date -> current comune(s)
  data/processed/comuni.gpkg    current comuni (in force on TARGET_DATE) with polygons, EPSG:32632

Rules (spec, "Grid and reconciliation" 1-2):
  * identity across time is the four-character cadastral (Belfiore) code, which survives
    province changes (Sardinia 2016 and 2026);
  * a comune whose Belfiore code no longer exists was suppressed: its successor is taken from
    ISTAT's published list of suppressed comuni, plus config/istat_changes_after_soppressi.csv
    for events after that list was last updated;
  * a comune that later lost territory to a new comune (config/istat_splits.csv) maps to both.
"""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime

import geopandas as gpd
import pandas as pd

from common import BOUNDARY_DATE, BOUNDARY_ZIP, CRS, PROC, RAW, CONFIG, TARGET_DATE, log, read_situas, write_csv

DATES = sorted(p.stem.split("_")[1] for p in (RAW / "istat_situas").glob("comuni_*.json"))


def d8(s: str) -> str:
    """dd/mm/yyyy -> yyyymmdd"""
    return datetime.strptime(s.strip(), "%d/%m/%Y").strftime("%Y%m%d")


def read_cfg(name: str) -> pd.DataFrame:
    lines = [l for l in (CONFIG / name).read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    return pd.read_csv(io.StringIO("\n".join(lines)), dtype=str)


def load_suppressions() -> pd.DataFrame:
    z = zipfile.ZipFile(RAW / "istat_codes" / "Elenco-comuni-soppressi.zip")
    name = [n for n in z.namelist() if n.endswith(".csv")][0]
    s = pd.read_csv(z.open(name), sep=";", encoding="latin1", dtype=str)
    s = s.rename(columns={
        "Codice Comune": "old_code", "Denominazione Comune": "old_name", "Data evento": "event_date",
        "Codice del Comune associato alla variazione": "new_code",
        "Denominazione Comune associato alla variazione": "new_name",
    })[["old_code", "old_name", "event_date", "new_code", "new_name"]]
    s = pd.concat([s, read_cfg("istat_changes_after_soppressi.csv")[s.columns]], ignore_index=True)
    s["event"] = s.event_date.map(d8)
    s = s[s.event >= "20150101"].copy()
    return s


def main():
    lists = {d: read_situas(d) for d in DATES}
    by_code = {d: {r["PRO_COM_T"]: r for r in lists[d]} for d in DATES}
    target = {r["COD_CATASTO"]: r for r in lists[TARGET_DATE]}
    sup = load_suppressions()
    splits = read_cfg("istat_splits.csv")
    splits["event"] = splits.event_date.map(d8)

    def belfiore_at(code: str, date: str) -> tuple[str, str] | None:
        """Belfiore of `code` on the first sampled date >= date where it exists."""
        for d in DATES:
            if d >= date and code in by_code[d]:
                return by_code[d][code]["COD_CATASTO"], d
        return None

    def resolve(code: str, date: str, depth=0) -> tuple[set[str], str]:
        assert depth < 10, (code, date)
        bd = belfiore_at(code, date)
        if bd is None:
            raise KeyError(f"code {code} not found on or after {date}")
        bel, seen = bd
        if bel in target:
            out = {target[bel]["PRO_COM_T"]}
            method = "belfiore"
            sp = splits[(splits.parent_code == by_code[seen][code]["PRO_COM_T"]) & (splits.event > date)]
            for _, r in sp.iterrows():
                cb = belfiore_at(r.child_code, r.event)
                out.add(target[cb[0]]["PRO_COM_T"])
                method = "split"
            return out, method
        ev = sup[(sup.old_code == code) & (sup.event > date)].sort_values("event")
        if ev.empty:
            raise KeyError(f"code {code} ({by_code[seen][code]['COMUNE']}) vanished after {date} with no ISTAT change record")
        first = ev.event.iloc[0]
        out = set()
        for _, r in ev[ev.event == first].iterrows():
            t, _ = resolve(r.new_code, r.event, depth + 1)
            out |= t
        return out, "merger"

    rows = []
    for d in DATES:
        for r in lists[d]:
            t, m = resolve(r["PRO_COM_T"], d)
            rows.append({"date": d, "code": r["PRO_COM_T"], "name": r["COMUNE"], "sigla": r["SIGLA_AUTOMOBILISTICA"],
                         "region_code": r["COD_REG"], "belfiore": r["COD_CATASTO"], "targets": "|".join(sorted(t)), "method": m})
    write_csv(PROC / "crosswalk.csv", rows)
    xw = pd.DataFrame(rows)
    log("crosswalk rows", len(xw), "methods", xw.groupby("method").code.nunique().to_dict())

    # current boundaries: ISTAT 1 Jan 2026 polygons, dissolved onto the comuni in force on TARGET_DATE
    g = gpd.read_file(f"zip://{BOUNDARY_ZIP}!Com01012026_g/Com01012026_g_WGS84.shp")
    g = g.to_crs(CRS)
    m = xw[xw.date == BOUNDARY_DATE].set_index("code").targets
    assert not m.str.contains(r"\|").any(), "a 2026 boundary polygon would be split"
    g["PRO_COM_T"] = g["PRO_COM_T"].map(m)
    g = g.dissolve(by="PRO_COM_T", as_index=False)[["PRO_COM_T", "geometry"]]
    info = pd.DataFrame(lists[TARGET_DATE])
    g = g.merge(info[["PRO_COM_T", "COMUNE", "COMUNE_IT", "COD_REG", "DEN_REG", "COD_UTS", "DEN_UTS", "SIGLA_AUTOMOBILISTICA", "COD_CATASTO"]],
                on="PRO_COM_T", how="outer", indicator=True)
    assert (g._merge == "both").all(), g[g._merge != "both"]
    g = g.drop(columns="_merge").rename(columns={
        "PRO_COM_T": "code", "COMUNE": "name", "COMUNE_IT": "name_it", "COD_REG": "region_code", "DEN_REG": "region",
        "COD_UTS": "uts_code", "DEN_UTS": "uts", "SIGLA_AUTOMOBILISTICA": "sigla", "COD_CATASTO": "belfiore"})
    g["area_km2"] = g.geometry.area / 1e6
    g = gpd.GeoDataFrame(g, geometry="geometry", crs=CRS)
    g.to_file(PROC / "comuni.gpkg", driver="GPKG")
    pd.DataFrame(g.drop(columns="geometry")).to_csv(PROC / "comuni_attributes.csv", index=False)
    log("current comuni", len(g), "area km2", round(g.area_km2.sum()))


if __name__ == "__main__":
    main()
