"""Phase 5: socio-economic layers, as counts on current comuni and on tiles.

Columns (all counts; the app divides afterwards):
  pop_res       residents on 1 Jan 2025 (ISTAT DCIS_POPRES1, final)
  taxpayers     IRPEF taxpayers, tax year 2024 (MEF)
  income        reddito imponibile, euro, tax year 2024 (MEF)  -> Gold
  pop_cens      census residents, 31 Dec 2023 (ISTAT basi territoriali 2023, P1)
  pop65         census residents aged 65+ (P27+P28+P29)
  foreign       census residents with foreign citizenship or stateless (ST1)
  pop25, grad   census residents aged 25+, and those with a tertiary degree (BL + ML_RDD), 2023
  pop15, employed, unemployed, labour   census residents 15+, by activity status, 2023
  jobs_total, jobs_<section>, jobs_ind  persons employed in local units of firms, 2024 (ASIA);
                jobs_ind = manufacturing (C) + construction (F)  -> Production
Each source keeps the comune codes of its own date; they are moved to current comuni through
the crosswalk (merged comuni are summed), then spread to tiles by residents.

Writes comuni_socio.csv, tiles_socio.csv and socio_national.json (the national figure each
column is tested against, taken from the source's own Italy row where it has one).
"""
from __future__ import annotations

import io
import json
import subprocess
import zipfile

import pandas as pd

import spread
from common import PROC, RAW, log
from layers import _register_for, to_current

CACHE = PROC / "cache"
CACHE.mkdir(exist_ok=True)
SECTIONS = list("BCDEFGHIJKLMNPQRS")


def is_comune(s: pd.Series) -> pd.Series:
    return s.astype(str).str.fullmatch(r"\d{6}")


def population():
    d = pd.read_csv(RAW / "istat_pop" / "DCIS_POPRES1_all_comuni_JAN_total.csv", dtype={"REF_AREA": str})
    d = d[d.TIME_PERIOD == 2025]
    it = d[d.REF_AREA == "IT"].OBS_VALUE.iloc[0]
    c = d[is_comune(d.REF_AREA)].rename(columns={"REF_AREA": "code", "OBS_VALUE": "pop_res"})[["code", "pop_res"]]
    p24 = pd.read_csv(RAW / "istat_pop" / "DCIS_POPRES1_all_comuni_JAN_total.csv", dtype={"REF_AREA": str})
    it24 = p24[(p24.TIME_PERIOD == 2024) & (p24.REF_AREA == "IT")].OBS_VALUE.iloc[0]
    return c, {"population": {"value": float(it), "tile_column": "pop_res", "source": "istat_pop", "note": "ISTAT, Italy, 1 Jan 2025"},
               "pop_cens_ref": {"value": float(it24), "note": "ISTAT, Italy, 1 Jan 2024 (= census 31 Dec 2023)"}}


def mef():
    z = zipfile.ZipFile(RAW / "mef" / "Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip")
    raw = z.read(z.namelist()[0])
    d = pd.read_csv(io.BytesIO(raw), sep=";", encoding="latin1", dtype=str, index_col=False)
    d.columns = [c.strip() for c in d.columns]
    num = lambda s: pd.to_numeric(s, errors="coerce")
    d["taxpayers"] = num(d["Numero contribuenti"])
    d["income"] = num(d["Reddito imponibile - Ammontare in euro"])
    tot = {"taxpayers": d.taxpayers.sum(), "income": d.income.sum()}
    c = d[is_comune(d["Codice Istat Comune"])].rename(columns={"Codice Istat Comune": "code"})[["code", "taxpayers", "income"]]
    resid = {k: tot[k] - c[k].sum() for k in tot}
    log("MEF rows without a valid comune (left out):", resid)
    return c, {"income": {"value": float(tot["income"]), "tile_column": "income", "source": "mef", "note": "MEF national total incl. the row with no valid comune"},
               "taxpayers": {"value": float(tot["taxpayers"]), "tile_column": "taxpayers", "source": "mef"}}


def asia():
    d = pd.read_csv(RAW / "istat_asia" / "DICA_ASIAULP_TERRIFDATA_3_LUEMPDAA_sections_2024.csv", dtype={"REF_AREA": str})
    d = d[d.DATA_TYPE == "LUEMPDAA"]
    w = d.pivot_table(index="REF_AREA", columns="ECON_ACTIVITY_NACE_2007", values="OBS_VALUE", aggfunc="sum").fillna(0)
    w = w.rename(columns={"0010": "jobs_total", **{s: f"jobs_{s}" for s in SECTIONS}})
    w["jobs_ind"] = w.jobs_C + w.jobs_F
    it = w.loc["IT"]
    c = w[is_comune(w.index.to_series())].reset_index().rename(columns={"REF_AREA": "code"})
    nat = {"jobs_total": {"value": float(it.jobs_total), "tile_column": "jobs_total", "source": "asia"},
           "jobs_ind": {"value": float(it.jobs_ind), "tile_column": "jobs_ind", "source": "asia"}}
    for s in SECTIONS:
        nat[f"jobs_{s}"] = {"value": float(it[f"jobs_{s}"]), "tile_column": f"jobs_{s}", "source": "asia"}
    return c, nat


CENSUS_ZIP = RAW / "istat_census" / "DCSS_ISTR_LAV_PEN_2 - Education, work, commuting for studying or working - full dataset.csv.zip"


def census_dcss():
    cache = CACHE / "dcss_2023.psv"
    if not cache.exists():
        # stream the 4.4 GB file once; keep 2023, both sexes, no commuting breakdown
        cmd = f"""unzip -p "{CENSUS_ZIP}" | awk -F'|' 'NR==1 || ($19=="\\"2023\\"" && $5=="\\"T\\"" && $15=="\\"ALL\\"" && $17=="\\"ALL\\"")' > "{cache}" """
        subprocess.run(cmd, shell=True, check=True)
    d = pd.read_csv(cache, sep="|", dtype=str)
    d["v"] = pd.to_numeric(d.Value, errors="coerce")
    k = lambda eta, cit, tit, fl: d[(d.ETA1 == eta) & (d.CITTADINANZA == cit) & (d.TITOLO_STUDIO == tit) & (d.FORZE_LAV == fl)].groupby("ITTER107").v.sum()
    a25 = ["Y25-49", "Y50-64", "Y_GE65"]
    cols = {
        "pop25": sum(k(a, "TOTAL", "ALL", "99") for a in a25),
        "grad": sum(k(a, "TOTAL", t, "99").reindex(k(a, "TOTAL", "ALL", "99").index, fill_value=0) for a in a25 for t in ("BL", "ML_RDD")),
        "pop15": k("Y_GE15", "TOTAL", "ALL", "99"),
        "employed": k("Y_GE15", "TOTAL", "ALL", "1"),
        "unemployed": k("Y_GE15", "TOTAL", "ALL", "12"),
        "labour": k("Y_GE15", "TOTAL", "ALL", "22"),
    }
    pop65_it = float(k("Y_GE65", "TOTAL", "ALL", "99").get("IT"))
    w = pd.DataFrame(cols).fillna(0)
    it = w.loc["IT"]
    c = w[is_comune(w.index.to_series())].reset_index().rename(columns={"ITTER107": "code"})
    nat = {k_: {"value": float(it[k_]), "tile_column": k_, "source": "census", "note": "ISTAT census 2023, Italy row"} for k_ in cols}
    nat["pop65_ref"] = {"value": pop65_it}
    return c, nat


def census_sections():
    cache = CACHE / "sections_2023.csv"
    if not cache.exists():
        z = zipfile.ZipFile(RAW / "istat_census" / "Dati_regionali_2023.zip")
        out = []
        for n in sorted(z.namelist()):
            if not n.endswith("_sezioni.xlsx"):
                continue
            x = pd.read_excel(io.BytesIO(z.read(n)), usecols=lambda c: c in {"PROCOM", "P1", "P27", "P28", "P29", "ST1"}, dtype={"PROCOM": str})
            x = x.groupby("PROCOM", as_index=False).sum(numeric_only=True)
            out.append(x)
            log("section file", n.split("/")[-1], len(x), "comuni")
        pd.concat(out).to_csv(cache, index=False)
    d = pd.read_csv(cache, dtype={"PROCOM": str})
    d["code"] = d.PROCOM.str.zfill(6)
    d["pop_cens"] = d.P1
    d["pop65"] = d.P27 + d.P28 + d.P29
    d["foreign"] = d.ST1
    return d.groupby("code", as_index=False)[["pop_cens", "pop65", "foreign"]].sum()


def rekey(df: pd.DataFrame, cols: list[str], name: str) -> pd.DataFrame:
    date = _register_for(set(df.code))
    log(name, "codes of register", date, len(df), "comuni")
    df = to_current(df, date)
    return df.groupby("unit", as_index=False)[cols].sum()


def main():
    parts, nat = [], {}
    for name, f in (("population", population), ("mef", mef), ("asia", asia), ("census", census_dcss)):
        c, n = f()
        nat.update(n)
        parts.append(rekey(c, [x for x in c.columns if x != "code"], name))
    sec = census_sections()
    parts.append(rekey(sec, ["pop_cens", "pop65", "foreign"], "census sections"))
    nat["pop_cens"] = {"value": nat.pop("pop_cens_ref")["value"], "tile_column": "pop_cens", "source": "census",
                       "note": "census P1 summed over sections must equal ISTAT's 1 Jan 2024 population"}
    nat["pop65"] = {"value": nat.pop("pop65_ref")["value"], "tile_column": "pop65", "source": "census",
                    "note": "census sections summed must equal the Italy row (age 65+) of the comune-level census table"}
    nat["foreign"] = {"value": float(sec.foreign.sum()), "tile_column": "foreign", "source": "census",
                      "note": "sum of census sections (no separate Italy row in the file): checks conservation only"}

    # comune table: units -> current comuni (a unit covering several current comuni is split by residents, flagged)
    from political import comuni_from_units
    com = None
    tiles = None
    for p in parts:
        cols = [c for c in p.columns if c != "unit"]
        cc = comuni_from_units(p, cols).drop(columns="shared")
        tt = spread.to_tiles(p, cols)
        com = cc if com is None else com.merge(cc, on="code", how="outer")
        tiles = tt if tiles is None else tiles.merge(tt, on="tile", how="outer")
    com.to_csv(PROC / "comuni_socio.csv", index=False)
    tiles.to_csv(PROC / "tiles_socio.csv", index=False)
    (PROC / "socio_national.json").write_text(json.dumps(nat, indent=1))
    for k, v in nat.items():
        if "tile_column" in v:
            t = tiles[v["tile_column"]].sum()
            log(f"{k:12s} source {v['value']:>18,.0f}  tiles {t:>18,.0f}  diff {(t / v['value'] - 1) * 100:+.4f}%")


if __name__ == "__main__":
    main()
