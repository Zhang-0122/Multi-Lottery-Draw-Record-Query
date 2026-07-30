#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check whether the public Netlify site is usable for regular visitors."""

from __future__ import annotations

import os
import sys

import requests


DEFAULT_URL = "https://fanciful-unicorn-343425.netlify.app"
SITE_URL = os.environ.get("SITE_URL", DEFAULT_URL).rstrip("/")
TIMEOUT = 20


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    print(f"Checking live site: {SITE_URL}")
    try:
        response = requests.get(SITE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        fail(f"site request failed: {exc}")

    print(f"HTTP {response.status_code}")
    if response.status_code != 200:
        fail(f"expected HTTP 200, got {response.status_code}")

    response.encoding = "utf-8"
    page = response.text
    checks = {
        "not password protected": "Password Protection" not in page,
        "has sync status": "已同步到" in page,
        "has official source": "官方来源" in page and "中国福彩网" in page and "中国体彩网" in page,
        "has disclaimer": "权威免责声明" in page and "不销售彩票" in page and "不提供代购服务" in page,
        "has lottery title": "彩票开奖数据中心" in page,
        "has ssq": "双色球" in page,
        "has dlt": "大乐透" in page,
        "has fc3d": "福彩3D" in page,
        "has pl3": "排列3" in page,
        "has pl5": "排列5" in page,
        "has qxc": "七星彩" in page,
        "has qlc": "七乐彩" in page,
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"{'OK' if ok else 'FAIL'} {name}")
    if failed:
        fail("live site content check failed: " + ", ".join(failed))

    print("Live site check passed.")


if __name__ == "__main__":
    sys.exit(main())
