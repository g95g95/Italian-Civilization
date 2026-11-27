"""Phase 3: election results by comune, on the current comune set.

For every election in common.ELECTIONS this writes, under data/processed/elections/:
  <eid>_turnout.csv  unit, electors, voters, blank, valid           (party elections and referendums)
  <eid>_lists.csv    unit, list, votes, votes_raw                   (party elections)
  <eid>_ref.csv      unit, question, electors, voters, blank, yes, no  (referendums)
  units.csv          election, unit, codes                           (which current comuni a unit covers)

A "unit" is the set of current comuni that a ministry record covers: one comune in
almost every case, two for Trapani before Misiliscemi split off in 2021, one merged
comune for every group of comuni that later fused.

Valid votes for the Camera are list votes after sharing out candidate-only votes
(eligendo._camera). The vote from abroad is not included: it has no place on the map.
"""
from __future__ import annotations

import pandas as pd

import eligendo as E
import names
from common import ELECTIONS, PROC, log

OUT = PROC / "elections"
OUT.mkdir(parents=True, exist_ok=True)


def _xwalk() -> pd.DataFrame:
    x = pd.read_csv(PROC / "crosswalk.csv", dtype=str)
    return x[["date", "code", "targets"]]


XW = None


def attach_units(eid: str, df: pd.DataFrame, labels: pd.DataFrame, tag: str = "") -> pd.DataFrame:
    """Resolve ministry labels -> ISTAT code at that date -> current comuni (unit)."""
    global XW
    if XW is None:
        XW = _xwalk()
    date = ELECTIONS[eid][0]
    res = names.resolve(eid, date, labels, tag)
    res = res.merge(XW, left_on=["code_date", "code"], right_on=["date", "code"], how="left")
    assert res.targets.notna().all(), res[res.targets.isna()]
    key = ["region", "province", "comune"]
    df = df.copy()
    df["province"] = df["province"].fillna("")
    res["province"] = res["province"].fillna("")
    out = df.merge(res[key + ["targets"]], on=key, how="left")
    assert out.targets.notna().all()
    return out.rename(columns={"targets": "unit"})


def party_election(eid: str, s: pd.DataFrame, v: pd.DataFrame, vda: tuple | None = None):
    s = attach_units(eid, s, s)
    v = attach_units(eid, v, s if "province" in s else s)
    sc = s.groupby("unit", as_index=False)[["electors", "voters", "blank", "valid"]].sum()
    lv = v.groupby(["unit", "list"], as_index=False)[["votes", "votes_raw"]].sum()
    lv["contest"] = "national"
    if vda is not None:
        vs, vv = vda
        vs = attach_units(eid, vs, vs, "_vda")
        vv = attach_units(eid, vv, vs, "_vda")
        sc = pd.concat([sc, vs.groupby("unit", as_index=False)[["electors", "voters", "blank", "valid"]].sum()])
        vv = vv.groupby(["unit", "list"], as_index=False)[["votes", "votes_raw"]].sum()
        # a separate contest: candidate votes under each candidate's symbol, kept apart from the national lists
        vv["list"] = "VDA: " + vv["list"]
        vv["contest"] = "vda_single_member"
        lv = pd.concat([lv, vv])
    sc.to_csv(OUT / f"{eid}_turnout.csv", index=False)
    lv.to_csv(OUT / f"{eid}_lists.csv", index=False)
    log(eid, "units", len(sc), "electors", int(sc.electors.sum()), "valid", int(sc.valid.sum()), "lists", lv.list.nunique())
    return sc


def referendum(eid: str, df: pd.DataFrame):
    df = attach_units(eid, df, df)
    r = df.groupby(["unit", "question"], as_index=False)[["electors", "voters", "blank", "yes", "no"]].sum()
    qt = df.groupby("question").question_text.first()
    r["question_text"] = r.question.map(qt)
    r.to_csv(OUT / f"{eid}_ref.csv", index=False)
    log(eid, "units", r.unit.nunique(), "questions", r.question.nunique(), "electors(q1)",
        int(r[r.question == r.question.min()].electors.sum()))
    return r


def vda2018():
    d = E.camera2018()[2]
    d = d.assign(region="VALLE D'AOSTA", province="", comune=d.COMUNE.str.strip())
    s = d.groupby(["region", "province", "comune"], as_index=False).agg(
        electors=("ELETTORI", "first"), voters=("VOTANTI", "first"), blank=("SCHEDE_BIANCHE", "first"))
    for c in ("electors", "voters", "blank"):
        s[c] = E.num(s[c])
    v = d.assign(list=d.LISTA.str.strip(), votes=E.num(d.VOTI_CANDIDATO))
    v = v.groupby(["region", "province", "comune", "list"], as_index=False).votes.sum()
    v["votes_raw"] = v.votes
    s = s.merge(v.groupby("comune").votes.sum().rename("valid"), on="comune")
    return s, v


def main():
    s, v, _ = E.camera2018()
    party_election("cam2018", s, v, vda2018())
    s, v = E.camera2022()
    party_election("cam2022", s, v, E.camera2022_vda())
    party_election("eu2019", *E.europee2019())
    party_election("eu2024", *E.europee2024())
    for eid, f in E.READERS.items():
        referendum(eid, f())


if __name__ == "__main__":
    main()
