"""Fetch every raw file listed in config/downloads.tsv into data/raw/ (skips files already present).

Raw files are never edited after download. Two entries are derived, by script, from other
raw downloads and documented as such:
  tinitaly    the INGV coverage service (WCS) is asked for 250 km chunks at 1/25 of the 10 m
              resolution (250 m); chunks are mosaicked on the native grid, empty chunks set to nodata
  luisa_crop  a window over Italy cut from the EU-wide LUISA raster, values unchanged

Writes data/raw/MANIFEST.csv: path, size, sha256, url, download date.
Usage: python scripts/download.py [--force]
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

from common import CONFIG, RAW, log

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) civ-italia-build"}


def fetch(url: str, headers: dict | None = None, tries: int = 4) -> bytes:
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read()
        except Exception as e:  # network hiccup: back off and retry
            if k == tries - 1:
                raise
            log("retry", url, e)
            time.sleep(2 ** k * 3)


def tinitaly(dest: Path, base: str):
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    x0, x1, y0, y1, res, step = 312_500, 1_320_000, 3_930_000, 5_222_500, 250, 250_000
    W, H = (x1 - x0) // res, (y1 - y0) // res
    out = np.full((H, W), -9999, dtype="float32")
    for xa in range(x0, x1, step):
        for ya in range(y0, y1, step):
            xb, yb = min(xa + step, x1), min(ya + step, y1)
            url = (f"{base}?service=WCS&version=2.0.1&request=GetCoverage&coverageId=TINItaly_1_1__tinitaly_dem"
                   f"&format=image/tiff&SCALEFACTOR=0.04&subset=E({xa},{xb})&subset=N({ya},{yb})")
            try:
                b = fetch(url)
            except Exception as e:
                log("tinitaly chunk failed (outside coverage?)", xa, ya, e)
                continue
            with rasterio.MemoryFile(b) as mf, mf.open() as r:
                a = r.read(1).astype("float32")
                if not np.any(a != 0):
                    continue  # the server fills chunks with no source data with 0
                if r.nodata is not None:
                    a[a == r.nodata] = -9999
                col = int(round((r.bounds.left - x0) / res))
                row = int(round((y1 - r.bounds.top) / res))
                h, w = a.shape
                h, w = min(h, H - row), min(w, W - col)
                if h > 0 and w > 0 and row >= 0 and col >= 0:
                    out[row:row + h, col:col + w] = a[:h, :w]
    dest.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dest, "w", driver="GTiff", height=H, width=W, count=1, dtype="float32", crs="EPSG:32632",
                       transform=from_origin(x0, y1, res, res), nodata=-9999, compress="deflate") as d:
        d.write(out, 1)


def luisa_crop(dest: Path, src: Path):
    import rasterio
    from rasterio.windows import from_bounds
    with rasterio.open(src) as r:
        win = from_bounds(4_040_000, 1_370_000, 5_070_000, 2_690_000, r.transform)
        a = r.read(1, window=win).astype("uint16")
        prof = r.profile | {"height": a.shape[0], "width": a.shape[1], "transform": r.window_transform(win),
                            "dtype": "uint16", "nodata": 0, "compress": "deflate"}
    with rasterio.open(dest, "w", **prof) as d:
        d.write(a, 1)


def main(force=False):
    rows = list(csv.DictReader(open(CONFIG / "downloads.tsv", encoding="utf-8"), delimiter="\t"))
    man = []
    for r in rows:
        if r["kind"] == "situas":
            for d in r["url"].split():
                p = RAW / r["dest"] / f"comuni_{d}.json"
                url = f"https://situas-servizi.istat.it/publish/reportspooljson?pfun=61&pdata={d[6:]}/{d[4:6]}/{d[:4]}"
                if force or not p.exists():
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(fetch(url))
                man.append((p, url))
            continue
        p = RAW / r["dest"]
        if force or not p.exists():
            log("downloading", r["dest"])
            p.parent.mkdir(parents=True, exist_ok=True)
            if r["kind"] == "get":
                p.write_bytes(fetch(r["url"]))
            elif r["kind"] == "sdmx":
                p.write_bytes(fetch(r["url"], {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"}))
            elif r["kind"] == "tinitaly":
                tinitaly(p, r["url"])
            elif r["kind"] == "luisa_crop":
                luisa_crop(p, RAW / r["url"])
        man.append((p, r["url"]))
    today = dt.date.today().isoformat()
    old = {}
    mf = RAW / "MANIFEST.csv"
    if mf.exists():
        old = {x["path"]: x for x in csv.DictReader(open(mf))}
    with open(mf, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path", "bytes", "sha256", "url", "downloaded"])
        for p, url in man:
            rel = str(p.relative_to(RAW))
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            date = old.get(rel, {}).get("downloaded") if old.get(rel, {}).get("sha256") == h else today
            w.writerow([rel, p.stat().st_size, h, url, date or today])
    log("manifest", len(man), "files")


if __name__ == "__main__":
    main("--force" in sys.argv)
