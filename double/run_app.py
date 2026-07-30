#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""User-friendly launcher for the 双色球 dashboard."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import webbrowser


ROOT = os.path.dirname(os.path.abspath(__file__))
DASHBOARD = os.path.join(ROOT, "ssq_analyzer.html")


def run(script: str) -> None:
    subprocess.check_call([sys.executable, os.path.join(ROOT, script)], cwd=ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="打开双色球历史数据分析工具")
    parser.add_argument("--update", action="store_true", help="联网刷新开奖数据后再打开")
    parser.add_argument("--no-open", action="store_true", help="只生成网页，不自动打开浏览器")
    args = parser.parse_args()

    if args.update:
        run("fetch_data.py")

    run("build_dashboard.py")

    if not args.no_open:
        webbrowser.open(os.path.abspath(DASHBOARD))
        print(f"Dashboard opened: {DASHBOARD}")
    else:
        print(f"Dashboard built: {DASHBOARD}")


if __name__ == "__main__":
    main()
