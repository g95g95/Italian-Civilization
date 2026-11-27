"""Interface translation: English is the source, Italian is a lookup.

  python scripts/i18n.py extract   writes config/i18n/strings_en.json (every interface string in
                                   web/app.js and web/index.html) and config/i18n/meta_en.json
                                   (rules, method, column names, sectors, gaps, election labels,
                                   list notes), the texts to translate
  python scripts/i18n.py check     lists what config/i18n/it_ui.json and it_meta.json still miss
  build()                          (called by export.py) writes web/data/i18n_it.json

Translations never touch numbers: placeholders such as {v} must survive unchanged.
"""
from __future__ import annotations

import io
import json
import re
import sys

import pandas as pd

from common import CONFIG, ELECTIONS, PROC, ROOT, WEB

I18N = CONFIG / "i18n"
I18N.mkdir(exist_ok=True)
Q = r"""(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")"""


def _lit(m, a=1):
    return (m.group(a) if m.group(a) is not None else m.group(a + 1)).replace("\\'", "'").replace('\\"', '"')


def ui_strings() -> list[str]:
    js = (WEB / "app.js").read_text(encoding="utf-8")
    out = set()
    for m in re.finditer(r"\btr\(\s*" + Q, js):  # tr('...')
        out.add(_lit(m))
    for m in re.finditer(r"\btr\(\s*[^'\"(),]*\?\s*" + Q + r"\s*:\s*" + Q, js):  # tr(c ? 'a' : 'b')
        out.add(_lit(m, 1))
        out.add(_lit(m, 3))
    # strings translated through a variable: lens labels and groups, terrain names, explorer bases
    for m in re.finditer(r"label: " + Q + r", grp: " + Q, js):
        out.add(_lit(m, 1))
        out.add(_lit(m, 3))
    for block in re.findall(r"const CAP = \{(.*?)\};", js) + re.findall(r"const base = \{(.*?)\}\[", js):
        for m in re.finditer(r":\s*" + Q, block):
            out.add(_lit(m))
    for m in re.finditer(r"\[('Plains'[^\]]*)\]\.map", js):
        out |= set(re.findall(r"'([^']+)'", m.group(1)))
    html = (WEB / "index.html").read_text(encoding="utf-8")
    for m in re.finditer(r'data-i18n(?:-aria|-ph)?="([^"]+)"', html):
        out.add(m.group(1).replace("&amp;", "&"))
    return sorted(s for s in out if re.search("[A-Za-z]", s))


def meta_texts() -> dict:
    c = json.loads((CONFIG / "columns.json").read_text(encoding="utf-8"))
    gaps = (ROOT / "GAPS.md").read_text(encoding="utf-8").split("## Open", 1)[1]
    notes = {}
    lp = PROC / "politics" / "lists.csv"
    if lp.exists():
        L = pd.read_csv(lp)
        notes = {n: n for n in sorted(set(L.note.dropna())) if n}
    return {
        "method": c["method"],
        "rules": [{k: r[k] for k in ("term", "quantity", "rule")} for r in c["rules"]],
        "columns": {k: {"label": v["label"], "rule": v["rule"]} for k, v in c["columns"].items()},
        "sectors": c["sectors"],
        "gaps": [l[2:].strip() for l in gaps.splitlines() if l.startswith("- ")],
        "elections": {k: v[2] for k, v in ELECTIONS.items()},
        "notes": notes,
        "sources": {k: v.get("short", k) for k, v in json.loads((CONFIG / "sources.json").read_text(encoding="utf-8")).items()},
    }


def extract():
    (I18N / "strings_en.json").write_text(json.dumps(ui_strings(), indent=1, ensure_ascii=False), encoding="utf-8")
    (I18N / "meta_en.json").write_text(json.dumps(meta_texts(), indent=1, ensure_ascii=False), encoding="utf-8")
    print("[civ] strings to translate:", len(ui_strings()))


def _shape_missing(en, it, path=""):
    miss = []
    if isinstance(en, dict):
        for k, v in en.items():
            if not isinstance(it, dict) or k not in it:
                miss.append(path + "/" + k)
            else:
                miss += _shape_missing(v, it[k], path + "/" + k)
    elif isinstance(en, list):
        if not isinstance(it, list) or len(it) != len(en):
            miss.append(path + " (list length)")
        else:
            for i, (a, b) in enumerate(zip(en, it)):
                miss += _shape_missing(a, b, f"{path}[{i}]")
    elif isinstance(en, str):
        if not isinstance(it, str) or not it.strip():
            miss.append(path)
        elif set(re.findall(r"\{\w+\}", en)) != set(re.findall(r"\{\w+\}", it)):
            miss.append(path + " (placeholders differ)")
    return miss


def missing() -> list[str]:
    ui = json.loads((I18N / "it_ui.json").read_text(encoding="utf-8")) if (I18N / "it_ui.json").exists() else {}
    meta = json.loads((I18N / "it_meta.json").read_text(encoding="utf-8")) if (I18N / "it_meta.json").exists() else {}
    out = []
    for s in ui_strings():
        t = ui.get(s)
        if not t:
            out.append("ui: " + s)
        elif set(re.findall(r"\{\w+\}", s)) != set(re.findall(r"\{\w+\}", t)):
            out.append("ui (placeholders differ): " + s)
    out += ["meta" + m for m in _shape_missing(meta_texts(), meta)]
    return out


def build():
    ui = json.loads((I18N / "it_ui.json").read_text(encoding="utf-8"))
    meta = json.loads((I18N / "it_meta.json").read_text(encoding="utf-8"))
    keep = set(ui_strings())
    (WEB / "data" / "i18n_it.json").write_text(json.dumps({"ui": {k: v for k, v in ui.items() if k in keep}, "meta": meta},
                                                          ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _it_numbers(o):
    """Italian number style in translated prose: 7,894 -> 7.894 and 0.1% -> 0,1% (versions such as
    TINITALY 1.1 and dates are left alone)."""
    if isinstance(o, dict):
        return {k: _it_numbers(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_it_numbers(v) for v in o]
    if not isinstance(o, str):
        return o
    s = re.sub(r"(?<![\w.])(\d{1,3}),(\d{3})(?!\d)", "\\1\u2009\\2", o)      # thousands: mark
    s = re.sub(r"(?<!TINITALY )(?<![\w/])(\d+)\.(\d+)(?=\s*(?:%|km|m\b|times|volte|\)|,|\s|$))", "\\1,\\2", s)
    return s.replace("\u2009", ".")


def merge():
    """Join the translated chunks in config/i18n/parts/ into it_ui.json and it_meta.json."""
    P = I18N / "parts"
    ui = {}
    for f in sorted(P.glob("ui_*_it.json")):
        ui.update(json.loads(f.read_text(encoding="utf-8")))
    old = json.loads((I18N / "it_ui.json").read_text(encoding="utf-8")) if (I18N / "it_ui.json").exists() else {}
    (I18N / "it_ui.json").write_text(json.dumps({**old, **ui}, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    meta = {}
    for f in sorted(P.glob("meta_*_it.json")):
        meta.update(json.loads(f.read_text(encoding="utf-8")))
    meta = _it_numbers(meta)
    (I18N / "it_meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1:] == ["merge"]:
        merge()
    elif sys.argv[1:] == ["extract"]:
        extract()
    elif sys.argv[1:] == ["check"]:
        m = missing()
        print("\n".join(m) if m else "[civ] Italian translation complete")
