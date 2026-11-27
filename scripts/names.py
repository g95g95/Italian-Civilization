"""Resolve the Interior Ministry's place labels to ISTAT comune codes.

The ministry's open-data files identify comuni by name only (region or constituency,
province, comune), so this module is the single, explicit bridge from those labels to
ISTAT codes. It is an exact lookup, not a fuzzy match:

  1. take ISTAT's own list of comuni in force on the election day (SITUAS);
  2. normalise both sides (accents, apostrophes, case, spaces) and look the label up
     within its region, using the province only when a name repeats inside a region;
  3. labels that still do not resolve must be listed in config/name_aliases.csv,
     each with the ISTAT code it stands for; anything else stops the build.

The resolved table is written to data/processed/names_<election>.csv so every
match can be audited.
"""
from __future__ import annotations

import io
import re
from collections import defaultdict

import pandas as pd

from common import CONFIG, PROC, norm, read_situas, write_csv


def _reg_key(s: str) -> str:
    s = norm(str(s).split("/")[0])
    return s[:8]


def _aliases() -> pd.DataFrame:
    lines = [l for l in (CONFIG / "name_aliases.csv").read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    return pd.read_csv(io.StringIO("\n".join(lines)), dtype=str)


def _index(lst):
    idx = defaultdict(list)  # (regionkey, namekey) -> [rows]
    for r in lst:
        names = {r["COMUNE"], r["COMUNE_IT"], r.get("COMUNE_A") or ""} | set(r["COMUNE"].split("/"))
        for n in names:
            if n:
                idx[(_reg_key(r["DEN_REG"]), norm(n))].append(r)
    return idx


# Some ministry files lost non-ASCII letters in an encoding step ('L_SEN' for Lüsen,
# 'EMAR+SE' for Emarèse). Those placeholder characters match exactly one letter.
_PLACEHOLDER = "+_\u00cd"


def _lookup(idx, region, comune):
    rk = _reg_key(region)
    keys = [comune]
    if "/" in comune:  # bilingual label, possibly truncated: use the Italian half
        keys.append(comune.split("/")[0])
    for k in keys:
        if any(ch in k for ch in _PLACEHOLDER):
            pat = re.compile("^" + "".join("[A-Z]" if ch in _PLACEHOLDER else re.escape(c)
                                           for ch in k for c in [norm(ch)] if c or ch in _PLACEHOLDER) + "$")
            hits = [r for (rr, n), rows in idx.items() if rr == rk and pat.match(n) for r in rows]
        else:
            hits = idx.get((rk, norm(k)), [])
        if hits:
            return hits
    return []


def resolve(eid: str, date: str, labels: pd.DataFrame, tag: str = "") -> pd.DataFrame:
    """labels: DataFrame with region, province (may be None), comune.

    Returns one row per distinct label with the ISTAT `code` and the register date `code_date`
    on which that code was in force. When a merger took effect shortly before polling day
    but the ministry still reported the old comuni, the label is looked up in the previous
    ISTAT register date instead (the crosswalk then carries it forward).
    """
    from crosswalk import DATES
    earlier = [d for d in DATES if d <= date][::-1]
    lists = {d: read_situas(d) for d in earlier[:3]}
    idxs = {d: _index(l) for d, l in lists.items()}
    lst = lists[date]
    al = _aliases()
    al = al[al.election == eid]
    amap = {(a.region, a.province if isinstance(a.province, str) else "", a.comune): a.code for a in al.itertuples()}
    by_code = {d: {r["PRO_COM_T"]: r for r in l} for d, l in lists.items()}

    out, bad = [], []
    for row in labels[["region", "province", "comune"]].drop_duplicates().itertuples(index=False):
        prov = row.province if isinstance(row.province, str) else ""
        k = (row.region, prov, row.comune)
        if k in amap:
            code, how, cdate = amap[k], "alias", date
            assert code in by_code[date], f"alias code {code} not in force on {date}"
        else:
            for cdate in idxs:
                cands = {r["PRO_COM_T"]: r for r in _lookup(idxs[cdate], row.region, row.comune)}
                if len(cands) > 1 and prov:
                    cands = {c: r for c, r in cands.items() if norm(r["DEN_UTS"].split("/")[0]).startswith(norm(prov)[:5])
                             or norm(prov).startswith(norm(r["DEN_UTS"].split("/")[0])[:5])}
                if cands:
                    break
            if len(cands) != 1:
                bad.append((row.region, prov, row.comune, list(cands)))
                continue
            code = next(iter(cands))
            how = "exact" if cdate == date else "previous_register"
        out.append({"election": eid, "region": row.region, "province": prov, "comune": row.comune,
                    "code": code, "code_date": cdate, "istat_name": by_code[cdate][code]["COMUNE"], "how": how})
    if bad:
        msg = "\n".join(map(str, bad[:50]))
        raise SystemExit(f"{eid}: {len(bad)} ministry labels do not resolve to an ISTAT code on {date}:\n{msg}")
    res = pd.DataFrame(out)
    dup = res[res.duplicated(["code", "code_date"], keep=False)]
    if len(dup):
        raise SystemExit(f"{eid}: two labels resolve to the same code:\n{dup}")
    write_csv(PROC / "names" / f"names_{eid}{tag}.csv", out)
    return res
