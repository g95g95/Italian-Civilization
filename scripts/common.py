"""Shared paths and helpers for the Civ Italia pipeline.

Every script reads from data/raw (read-only) and writes to data/processed or web/data.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
CONFIG = ROOT / "config"
WEB = ROOT / "web"
PROC.mkdir(parents=True, exist_ok=True)

# The target boundary set: ISTAT generalised boundaries at 1 Jan 2026, dissolved to the
# comuni in force on the date below (two mergers happened in early 2026).
TARGET_DATE = "20261127"
BOUNDARY_ZIP = RAW / "istat_boundaries" / "Limiti01012026_g.zip"
BOUNDARY_DATE = "20260101"

CRS = "EPSG:32632"  # UTM zone 32N, metres

# Elections in scope: id -> (date YYYYMMDD, kind, label)
ELECTIONS = {
    "ref2016a": ("20160417", "referendum", "Referendum 17 Apr 2016 (offshore drilling)"),
    "ref2016c": ("20161204", "referendum", "Constitutional referendum 4 Dec 2016"),
    "cam2018": ("20180304", "camera", "Camera 2018"),
    "eu2019": ("20190526", "europee", "European Parliament 2019"),
    "ref2020": ("20200920", "referendum", "Constitutional referendum 20–21 Sep 2020"),
    "ref2022": ("20220612", "referendum", "Referendums 12 Jun 2022 (justice)"),
    "cam2022": ("20220925", "camera", "Camera 2022"),
    "eu2024": ("20240609", "europee", "European Parliament 2024"),
    "ref2025": ("20250608", "referendum", "Referendums 8–9 Jun 2025 (work, citizenship)"),
    "ref2026": ("20260322", "referendum", "Constitutional referendum 22–23 Mar 2026 (judiciary)"),
}


def norm(s: str) -> str:
    """Normalise a place name for exact comparison: strip accents, apostrophes, spaces, case.

    Used only inside the explicit name crosswalk (see crosswalk.py), never as a join key
    between datasets.
    """
    if s is None:
        return ""
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.upper()
    return re.sub(r"[^A-Z0-9]", "", s)


def read_situas(date: str) -> list[dict]:
    """ISTAT SITUAS list of comuni in force on `date` (YYYYMMDD)."""
    p = RAW / "istat_situas" / f"comuni_{date}.json"
    return json.loads(p.read_text())["resultset"]


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def log(*a):
    print("[civ]", *a, flush=True)
