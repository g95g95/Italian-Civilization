"""Copy web/ into an output folder in the shape a hosted page wrapper expects: the page body and
its head elements without the <!DOCTYPE>/<html>/<head>/<body> tags, plus app.js and data/.
Usage: python scripts/build_artifact.py OUTDIR"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from common import WEB


def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    html = (WEB / "index.html").read_text(encoding="utf-8")
    head = re.search(r"<head>(.*?)</head>", html, re.S).group(1)
    body = re.search(r"<body>(.*?)</body>", html, re.S).group(1)
    head = re.sub(r'<meta charset="utf-8">\s*|<meta name="viewport"[^>]*>\s*', "", head)
    (out / "index.html").write_text(head.strip() + "\n" + body.strip() + "\n", encoding="utf-8")
    shutil.copy(WEB / "app.js", out / "app.js")
    if (out / "data").exists():
        shutil.rmtree(out / "data")
    shutil.copytree(WEB / "data", out / "data")
    print("[civ] artifact files in", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
