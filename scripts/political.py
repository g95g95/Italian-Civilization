"""Phase 4: political layer.

Inputs: data/processed/elections/*, config/list_map.csv, CHES 1999-2024 trend file.
Outputs under data/processed/politics/:
  lists.csv                 one row per election x list: label, short, national votes, scores, rule
  <eid>_tiles.csv           tile counts (electors, voters, valid, scored votes, score sums, coalitions)
  <eid>_tile_lists.csv      tile x list votes
  <eid>_comuni.csv / <eid>_comune_lists.csv   the same on current comuni
  <eid>_ref_tiles.csv / <eid>_ref_comuni.csv  referendums: electors, voters, yes, no per question

Rules (spec, "Political layer"): a list's score is its CHES score from the wave closest to
the vote; a joint list takes the simple mean of its scored member parties; lists without a
score are left out of the average and the share of valid votes that had a score is kept
as `scored` (coverage). No score is set by hand: config/list_map.csv only says which
survey parties sit on a list.
"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd

import spread
from common import CONFIG, ELECTIONS, PROC, RAW, log

OUT = PROC / "politics"
OUT.mkdir(parents=True, exist_ok=True)
AXES = ["lrgen", "lrecon", "galtan"]


def cfg(name):
    t = (CONFIG / name).read_text(encoding="utf-8").splitlines()
    return pd.read_csv(io.StringIO("\n".join(l for l in t if l and not l.startswith("#"))), dtype=str)


def ches() -> pd.DataFrame:
    d = pd.read_csv(RAW / "ches" / "1999-2024_CHES_dataset_meansV2.csv")
    d = d[d.country == 8][["year", "party_id", "party"] + AXES]
    return d


def list_scores(eid: str, lists: pd.DataFrame, ch: pd.DataFrame, lm: pd.DataFrame) -> pd.DataFrame:
    m = lm[lm.election == eid].set_index("list")
    out = []
    for r in lists.itertuples():
        row = {"election": eid, "list": r.list, "contest": r.contest, "votes": r.votes}
        if r.contest == "national" and r.list in m.index:
            e = m.loc[r.list]
            row.update(short=e.short, coalition=e.coalition if isinstance(e.coalition, str) else "",
                       wave=int(e.wave), note=e.note if isinstance(e.note, str) else "")
            ids = [int(x) for x in e.ches.split(";")] if isinstance(e.ches, str) else []
            sub = ch[(ch.year == int(e.wave)) & ch.party_id.isin(ids)]
            assert len(sub) == len(ids), (eid, r.list, ids, sub)
            row["members"] = ";".join(sub.party.tolist())
            for a in AXES:
                row[a] = sub[a].mean() if len(sub) else np.nan
            row["rule"] = ("" if not ids else "CHES " + sub.party.iloc[0] if len(ids) == 1
                           else "simple mean of CHES " + " and ".join(sub.party))
        else:
            row.update(short="", coalition="", wave=np.nan, note="not scored" if r.contest == "national"
                       else "Valle d'Aosta single-member contest: not scored", members="", rule="")
            for a in AXES:
                row[a] = np.nan
        out.append(row)
    return pd.DataFrame(out)


def summarise(cnt: pd.DataFrame, lv: pd.DataFrame, sc: pd.DataFrame, key: str) -> pd.DataFrame:
    """cnt: key, electors, voters, valid ; lv: key, list, votes ; sc: list scores."""
    s = sc.set_index("list")
    lv = lv.join(s[AXES + ["coalition"]], on="list")
    scored = lv[lv.lrgen.notna()]
    agg = scored.groupby(key).votes.sum().rename("scored_votes").to_frame()
    for a in AXES:
        agg[a + "_sum"] = (scored.votes * scored[a]).groupby(scored[key]).sum()
    for c in ("cdx", "csx"):
        agg[c] = lv[lv.coalition == c].groupby(key).votes.sum()
    lead = lv.sort_values("votes", ascending=False).drop_duplicates(key).set_index(key)
    agg["lead"] = lead.list
    out = cnt.set_index(key).join(agg).reset_index()
    out[["scored_votes", "cdx", "csx"] + [a + "_sum" for a in AXES]] = out[["scored_votes", "cdx", "csx"] + [a + "_sum" for a in AXES]].fillna(0)
    return out


def main():
    ch, lm = ches(), cfg("list_map.csv")
    allscores = []
    for eid, (date, kind, label) in ELECTIONS.items():
        if kind == "referendum":
            r = pd.read_csv(PROC / "elections" / f"{eid}_ref.csv", dtype={"unit": str})
            cols = ["electors", "voters", "blank", "yes", "no"]
            rt = spread.to_tiles(r, cols, by=["question"])
            rt.to_csv(OUT / f"{eid}_ref_tiles.csv", index=False)
            rc = comuni_from_units(r, cols, ["question"])
            rc.to_csv(OUT / f"{eid}_ref_comuni.csv", index=False)
            continue
        t = pd.read_csv(PROC / "elections" / f"{eid}_turnout.csv", dtype={"unit": str})
        v = pd.read_csv(PROC / "elections" / f"{eid}_lists.csv", dtype={"unit": str})
        nat = v.groupby(["list", "contest"], as_index=False).votes.sum().sort_values("votes", ascending=False)
        sc = list_scores(eid, nat, ch, lm)
        valid_nat = v[v.contest == "national"].votes.sum()
        sc["share"] = sc.votes / valid_nat * 100
        allscores.append(sc)
        if eid.startswith("cam"):
            # VdA contest is not scored: it carries a note instead (spec)
            pass
        tl = spread.to_tiles(v, ["votes"], by=["list"])
        tc = spread.to_tiles(t, ["electors", "voters", "valid"])
        ts = summarise(tc, tl, sc, "tile")
        ts.to_csv(OUT / f"{eid}_tiles.csv", index=False)
        tl.to_csv(OUT / f"{eid}_tile_lists.csv", index=False)
        cc = comuni_from_units(t, ["electors", "voters", "valid"])
        cl = comuni_from_units(v, ["votes"], ["list"])
        cs = summarise(cc, cl, sc, "code")
        cs.to_csv(OUT / f"{eid}_comuni.csv", index=False)
        cl.to_csv(OUT / f"{eid}_comune_lists.csv", index=False)
        cov = sc[sc.lrgen.notna()].votes.sum() / valid_nat
        lr = (sc.lrgen * sc.votes).sum() / sc[sc.lrgen.notna()].votes.sum()
        log(eid, f"coverage {cov*100:.1f}%  national lrgen {lr:.2f}  tiles lr range "
                 f"{(ts.lrgen_sum/ts.scored_votes).min():.2f}-{(ts.lrgen_sum/ts.scored_votes).max():.2f}")
    pd.concat(allscores).to_csv(OUT / "lists.csv", index=False)


def comuni_from_units(df: pd.DataFrame, cols: list[str], by: list[str] | None = None) -> pd.DataFrame:
    """Counts by current comune. A unit covering several comuni (Trapani before 2021) gives each
    comune the unit's counts scaled by the comune's share of the unit's residents, and is flagged."""
    by = by or []
    df = df.copy()
    df["code"] = df.unit.str.split("|")
    df["shared"] = df.code.str.len() > 1
    df = df.explode("code")
    w = spread.weights().groupby("code").grid_pop.sum()
    df["w"] = df.code.map(w)
    df["w"] = df.w / df.groupby(["unit"] + by).w.transform("sum")
    for c in cols:
        df[c] = df[c] * df.w
    return df.groupby(["code"] + by, as_index=False).agg({**{c: "sum" for c in cols}, "shared": "max"})


if __name__ == "__main__":
    main()
