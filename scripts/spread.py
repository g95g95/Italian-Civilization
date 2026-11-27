"""Move counts from comuni (or multi-comune election units) onto tiles.

Counts are spread by where people live (ISTAT 2021 1 km grid), never by area, unless a
unit has no resident in the grid. Rates are never spread: callers carry counts and divide
afterwards (spec, "Grid and reconciliation" 3-4).
"""
from __future__ import annotations

import pandas as pd

from common import PROC

_W = None


def weights() -> pd.DataFrame:
    global _W
    if _W is None:
        _W = pd.read_csv(PROC / "weights.csv", dtype={"code": str})
    return _W


def unit_weights(units: pd.Series, mode: str = "pop") -> pd.DataFrame:
    """unit ('code' or 'code|code') -> rows (unit, tile, w) with w summing to 1 per unit.

    mode='pop' spreads by residents (default); mode='area' by land area, for counts that are
    themselves areas (hazard zones)."""
    w = weights()
    u = pd.DataFrame({"unit": pd.Series(units).astype(str).unique()})
    u["code"] = u.unit.str.split("|")
    u = u.explode("code")
    m = u.merge(w, on="code", how="left")
    assert m.tile.notna().all(), m[m.tile.isna()].unit.unique()[:10]
    m["area"] = m.area_w * m.code.map(_areas())
    g = m.groupby(["unit", "tile"], as_index=False).agg(grid_pop=("grid_pop", "sum"), area=("area", "sum"))
    tot = g.groupby("unit").grid_pop.transform("sum")
    atot = g.groupby("unit").area.transform("sum")
    g["w"] = g.area / atot if mode == "area" else (g.grid_pop / tot).where(tot > 0, g.area / atot)
    return g[["unit", "tile", "w"]]


_A = None


def _areas() -> pd.Series:
    global _A
    if _A is None:
        _A = pd.read_csv(PROC / "comuni_attributes.csv", dtype={"code": str}).set_index("code").area_km2
    return _A


def to_tiles(df: pd.DataFrame, cols: list[str], by: list[str] | None = None, unit_col: str = "unit",
             mode: str = "pop") -> pd.DataFrame:
    """Spread count columns of df (one row per unit [x by]) onto tiles."""
    by = by or []
    df = df.copy()
    df[unit_col] = df[unit_col].astype(str)
    uw = unit_weights(df[unit_col], mode)
    m = df.merge(uw, left_on=unit_col, right_on="unit", how="inner", suffixes=("", "_w"))
    assert len(m.drop_duplicates([unit_col] + by)) == len(df.drop_duplicates([unit_col] + by))
    for c in cols:
        m[c] = m[c] * m.w
    out = m.groupby(["tile"] + by, as_index=False)[cols].sum()
    out["tile"] = out.tile.astype(int)
    return out
