#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copy generated static pages into the public release directory."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "release"
SOURCE_DIR = ROOT / "double"
PAGE_NAMES = (
    "ssq_analyzer.html",
    "index.html",
    "ssq.html",
    "dlt.html",
    "fc3d.html",
    "pl3.html",
    "pl5.html",
    "qxc.html",
    "qlc.html",
)


def main() -> None:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    for page_name in PAGE_NAMES:
        source = SOURCE_DIR / page_name
        if not source.exists():
            raise FileNotFoundError(f"Generated page not found: {source}")
        target_name = "index.html" if page_name == "ssq_analyzer.html" else page_name
        target = RELEASE_DIR / target_name
        shutil.copy2(source, target)
        print(f"Synced {source} -> {target}")


if __name__ == "__main__":
    main()
