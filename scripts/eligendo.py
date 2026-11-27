"""Readers for the Interior Ministry (Eligendo) open-data files.

Each reader returns two DataFrames keyed by the ministry's own place labels:
  scr:  region, province, comune, electors, voters, blank, valid       (one row per comune)
  vot:  region, province, comune, list, votes                          (one row per comune x list)
For referendums `vot` has one row per comune x question with columns yes, no.
The labels are resolved to ISTAT codes in names.py; nothing here joins on names.
"""
from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd

from common import RAW

E = RAW / "eligendo"


def _zread(zname: str, member: str, **kw) -> pd.DataFrame:
    z = zipfile.ZipFile(E / zname)
    names = [n for n in z.namelist() if n.endswith(member)]
    assert len(names) == 1, (zname, member, names)
    raw = z.read(names[0])
    enc = "utf-8-sig" if raw[:3] == b"\xef\xbb\xbf" else "latin1"
    return pd.read_csv(io.BytesIO(raw), sep=";", encoding=enc, dtype=str, **kw)


def num(s: pd.Series) -> pd.Series:
    """Eligendo numbers: '1234', '1234,00', '' -> float."""
    return pd.to_numeric(s.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                         .replace({"nan": np.nan, "": np.nan}), errors="coerce")


def _circ_region(c: str) -> str:
    c = c.strip()
    if c == "AOSTA":
        return "VALLE D'AOSTA"
    return c.rstrip("0123456789 ").strip()


# ---------------------------------------------------------------- Camera (2018, 2022)

def _camera(df: pd.DataFrame, circ, coll, comune, ele, vot, blank, cand_key, cand_votes, lst, lst_votes):
    df = df.copy()
    df["region"] = df[circ].map(_circ_region)
    df["province"] = None
    df["comune"] = df[comune].str.strip()
    df["coll"] = df[coll].fillna("").str.strip()
    for c in (ele, vot, blank, cand_votes, lst_votes):
        df[c] = num(df[c])
    df["cand"] = df[cand_key].fillna("").agg("|".join, axis=1)
    key = ["region", "comune", "coll"]
    # one turnout record per comune x single-member constituency
    s = df.groupby(key, as_index=False).agg(electors=(ele, "first"), voters=(vot, "first"), blank=(blank, "first"))
    # candidate votes include votes cast for the candidate only; list votes do not
    c = df.groupby(key + ["cand"], as_index=False).agg(cand_votes=(cand_votes, "first"), list_votes=(lst_votes, "sum"))
    c["cand_only"] = (c.cand_votes - c.list_votes).clip(lower=0)
    lv = df.groupby(key + ["cand", lst], as_index=False)[lst_votes].sum().rename(columns={lst: "list", lst_votes: "votes"})
    # law: candidate-only votes are shared among the candidate's lists in proportion to their votes
    # in the single-member constituency (collegio uninominale)
    tot = lv.groupby(["region", "coll", "cand", "list"], as_index=False).votes.sum()
    tot["share"] = tot.votes / tot.groupby(["region", "coll", "cand"]).votes.transform("sum")
    lv = lv.merge(tot[["region", "coll", "cand", "list", "share"]], on=["region", "coll", "cand", "list"], how="left")
    lv = lv.merge(c[key + ["cand", "cand_only"]], on=key + ["cand"], how="left")
    lv["votes_alloc"] = lv.votes + lv.cand_only * lv.share.fillna(0)
    v = lv.groupby(["region", "comune", "list"], as_index=False).agg(votes_raw=("votes", "sum"), votes=("votes_alloc", "sum"))
    s = s.groupby(["region", "comune"], as_index=False)[["electors", "voters", "blank"]].sum()
    valid = v.groupby(["region", "comune"]).votes.sum().rename("valid")
    s = s.merge(valid, on=["region", "comune"], how="left")
    s["province"] = None
    v["province"] = None
    unalloc = (c.groupby(key).cand_only.sum() > 0) & (c.groupby(key).list_votes.sum() == 0)
    return s, v, unalloc


def camera2018():
    df = _zread("camera-20180304.zip", "Camera2018_livComune.txt")
    vda = df[df.CIRCOSCRIZIONE.str.strip() == "AOSTA"]
    df = df[df.CIRCOSCRIZIONE.str.strip() != "AOSTA"]
    s, v, _ = _camera(df, "CIRCOSCRIZIONE", "COLLEGIOUNINOMINALE", "COMUNE", "ELETTORI", "VOTANTI", "SCHEDE_BIANCHE",
                      ["COGNOME", "NOME", "DATA_NASCITA"], "VOTI_CANDIDATO", "LISTA", "VOTI_LISTA")
    return s, v, vda


def camera2022():
    df = _zread("camera-20220925.zip", "camera2022_Italia_LivComune.csv")
    s, v, _ = _camera(df, "CIRC-REG", "COLLUNINOM", "COMUNE", "ELETTORITOT", "VOTANTITOT", "SKBIANCHE",
                      ["COGNOME", "NOME", "DATANASCITA"], "VOTICANDIDATO", "DESCRLISTA", "VOTILISTA")
    return s, v


def camera2022_vda():
    """Valle d'Aosta, single-member contest: candidates with their symbol, by comune."""
    c = _zread("camera-20220925.zip", "camera2022_VAosta_LivComune.csv")
    s = _zread("camera-20220925.zip", "camera2022_VAosta_LivComune_Scrutini.csv")
    v = pd.DataFrame({"region": "VALLE D'AOSTA", "province": None, "comune": c.COMUNE.str.strip(),
                      "list": c.CONTRASSEGNO.str.strip(), "votes": num(c.TOTVOTI)})
    v = v.groupby(["region", "province", "comune", "list"], dropna=False, as_index=False).votes.sum()
    v["votes_raw"] = v.votes
    s = pd.DataFrame({"region": "VALLE D'AOSTA", "province": None, "comune": s.DENOMINAZIONE.str.strip(),
                      "electors": num(s.ELETTORITOTALI), "voters": num(s.VOTANTITOTALI), "blank": num(s.SKBIANCHE)})
    s = s.merge(v.groupby("comune").votes.sum().rename("valid"), on="comune", how="left")
    return s, v


# ---------------------------------------------------------------- European Parliament

def europee2019():
    df = _zread("europee-20190526.zip", "europee-20190526.txt")
    return _euro(df, "REGIONE", "PROVINCIA", "COMUNE", "ELETTORI", "VOTANTI", "SCHEDEBIANCHE", "LISTA", "VOTI_LISTA")


def europee2024():
    raw = (E / "europee-2024-italia-livcomune.csv").read_bytes()
    df = pd.read_csv(io.BytesIO(raw), sep=";", encoding="latin1", dtype=str)
    return _euro(df, "DESCREGIONE", "DESCPROVINCIA", "DESCCOMUNE", "ELETTORI", "VOTANTI", "NUMSCHEDEBIANCHE", "DESCLISTA", "NUMVOTI")


def _euro(df, reg, prov, com, ele, vot, blank, lst, votes):
    df = df.copy()
    for c in (ele, vot, blank, votes):
        df[c] = num(df[c])
    df["region"] = df[reg].str.strip()
    df["province"] = df[prov].str.strip()
    df["comune"] = df[com].str.strip()
    key = ["region", "province", "comune"]
    s = df.groupby(key, as_index=False).agg(electors=(ele, "first"), voters=(vot, "first"), blank=(blank, "first"))
    v = df.groupby(key + [lst], as_index=False)[votes].sum().rename(columns={lst: "list", votes: "votes"})
    v["list"] = v["list"].str.strip()
    v["votes_raw"] = v.votes
    s = s.merge(v.groupby(key).votes.sum().rename("valid"), on=key, how="left")
    return s, v


# ---------------------------------------------------------------- Referendums
# Output: region, province, comune, question, electors, voters, blank, yes, no

def _ref_txt(zname, member):
    df = _zread(zname, member)
    return pd.DataFrame({
        "region": df.REGIONE.str.strip(), "province": df.PROVINCIA.str.strip(), "comune": df.COMUNE.str.strip(),
        "question": num(df.NUM_REFERENDUM).astype(int), "question_text": df.QUESITO.str.strip(),
        "electors": num(df.ELETTORI), "voters": num(df.VOTANTI), "blank": num(df.SCHEDE_BIANCHE),
        "yes": num(df.NUMVOTISI), "no": num(df.NUMVOTINO)})


def ref2016a():
    return _ref_txt("referendum-20160417.zip", "referendum-20160417.txt")


def ref2016c():
    return _ref_txt("referendum-20161204.zip", "referendum-20161204.txt")


def ref2020():
    return _ref_txt("referendum-20200920.zip", "referendum-20200920.txt")


REF2022_Q = {1: "Incandidabilità dopo condanna (legge Severino)", 2: "Limitazione delle misure cautelari",
             3: "Separazione delle funzioni dei magistrati", 4: "Valutazione dei magistrati da parte di avvocati e professori",
             5: "Elezione dei componenti togati del CSM"}


def ref2022():
    out = []
    for q in range(1, 6):
        df = _zread("referendum-20220612.zip", f"Scrutini_quesito{q}.csv")
        out.append(pd.DataFrame({
            "region": df.REGIONE.str.strip(), "province": df.PROVINCIA.str.strip(), "comune": df.COMUNE.str.strip(),
            "question": q, "question_text": REF2022_Q[q], "electors": num(df.ELETTORI), "voters": num(df.VOTANTI),
            "blank": num(df.SCHEDE_BIANCHE), "yes": num(df.VOTI_SI), "no": num(df.VOTI_NO)}))
    return pd.concat(out, ignore_index=True)


def ref2025():
    df = _zread("referendum-20250608.zip", "Referendum_LivComune.csv")
    valid, yes = num(df.VOTIVALIDI), num(df.VOTIVALIDI_SI)
    return pd.DataFrame({
        "region": df.REGIONE.str.strip(), "province": df.PROVINCIA.str.strip(), "comune": df.COMUNE.str.strip(),
        "question": num(df.NUMQUESITO).astype(int), "question_text": df.QUESITOREFERENDUM.str.strip(),
        "electors": num(df.ELETTORITOT), "voters": num(df.VOTANTITOT), "blank": num(df.SKBIANCHE),
        "yes": yes, "no": valid - yes})


def ref2026():
    df = _zread("referendum-20260322.zip", "Referendum2026_OpenData_LivComune.csv", skiprows=1)
    valid, yes = num(df.VOTIVALIDI), num(df.VOTISI)
    return pd.DataFrame({
        "region": df.REG.str.strip(), "province": df.PROV.str.strip(), "comune": df.COM.str.strip(),
        "question": 1, "question_text": "Ordinamento giurisdizionale e istituzione della Corte disciplinare",
        "electors": num(df.ELETTORITOTALI), "voters": num(df.NUMVOTANTITOTALI), "blank": num(df.SKBIANCHE),
        "yes": yes, "no": valid - yes})


READERS = {"ref2016a": ref2016a, "ref2016c": ref2016c, "ref2020": ref2020, "ref2022": ref2022,
           "ref2025": ref2025, "ref2026": ref2026}
