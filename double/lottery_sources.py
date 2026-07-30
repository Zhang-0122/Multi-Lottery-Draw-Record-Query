#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Official/public lottery source fetchers and validation helpers."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
CACHE_DIR = PROJECT_ROOT / "cashe"
LOG_DIR = CACHE_DIR / "logs"
DEBUG_DIR = CACHE_DIR / "debug"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
TIMEOUT = 20

LOG_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def normalize_numbers(values: str | list[str], expected: int, *, sort_numbers: bool = True) -> str:
    if isinstance(values, str):
        parts = values.replace("，", ",").replace(" ", ",").split(",")
    else:
        parts = values
    nums = [int(value) for value in parts if str(value).strip()]
    if len(nums) != expected:
        raise ValueError(f"expected {expected} numbers, got {nums}")
    if sort_numbers:
        nums = sorted(nums)
    return ",".join(f"{value:02d}" for value in nums)


def log(message: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with (LOG_DIR / "lottery_sources.log").open("a", encoding="utf-8") as file:
        file.write(f"[{stamp}] {message}\n")


def load_json_records(path: str | os.PathLike[str]) -> list[dict[str, str]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)
    return data if isinstance(data, list) else []


def save_json_records(path: str | os.PathLike[str], records: list[dict[str, str]], label: str) -> list[dict[str, str]]:
    if not records:
        raise RuntimeError(f"{label} 没有有效数据，已保留旧数据")
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists():
        backup = CACHE_DIR / f"{file_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(file_path, backup)
        log(f"{label} 已备份旧数据: {backup}")
    sorted_records = sorted(records, key=lambda item: (item["Date"], item["Issue"]))
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(sorted_records, file, ensure_ascii=False)
    return sorted_records


def validate_dlt_record(record: dict[str, str]) -> bool:
    try:
        front = [int(value) for value in record["Front"].split(",")]
        back = [int(value) for value in record["Back"].split(",")]
        datetime.strptime(record["Date"], "%Y-%m-%d")
    except (KeyError, TypeError, ValueError):
        return False
    return (
        len(front) == 5
        and len(set(front)) == 5
        and front == sorted(front)
        and all(1 <= value <= 35 for value in front)
        and len(back) == 2
        and len(set(back)) == 2
        and back == sorted(back)
        and all(1 <= value <= 12 for value in back)
    )


def validate_digit_record(record: dict[str, str], count: int) -> bool:
    try:
        digits = [int(value) for value in record["Digit"].split(",")]
        datetime.strptime(record["Date"], "%Y-%m-%d")
    except (KeyError, TypeError, ValueError):
        return False
    return len(digits) == count and all(0 <= value <= 9 for value in digits)


def validate_qlc_record(record: dict[str, str]) -> bool:
    try:
        main = [int(value) for value in record["Main"].split(",")]
        special = int(record["Special"])
        datetime.strptime(record["Date"], "%Y-%m-%d")
    except (KeyError, TypeError, ValueError):
        return False
    return (
        len(main) == 7
        and len(set(main)) == 7
        and main == sorted(main)
        and all(1 <= value <= 30 for value in main)
        and 1 <= special <= 30
        and special not in main
    )


def fetch_dlt_history(page_size: int = 100, max_pages: int = 80) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
    headers = {"User-Agent": UA, "Referer": "https://www.lottery.gov.cn/"}
    for page_no in range(1, max_pages + 1):
        params = {
            "gameNo": "85",
            "provinceId": "0",
            "pageSize": str(page_size),
            "isVerify": "1",
            "pageNo": str(page_no),
        }
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            debug_path = DEBUG_DIR / f"dlt_fetch_failed_page_{page_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            debug_path.write_text(str(exc), encoding="utf-8")
            log(f"大乐透第 {page_no} 页抓取失败: {exc}")
            break

        items = payload.get("value", {}).get("list", [])
        if not items:
            break
        for item in items:
            result = str(item.get("lotteryDrawResult", "")).split()
            if len(result) != 7:
                continue
            record = {
                "Issue": str(item.get("lotteryDrawNum", "")).strip(),
                "Date": str(item.get("lotteryDrawTime", "")).strip()[:10],
                "Front": normalize_numbers(result[:5], 5),
                "Back": normalize_numbers(result[5:], 2),
            }
            if validate_dlt_record(record):
                records.append(record)
        total_pages = int(payload.get("value", {}).get("pages") or page_no)
        if page_no >= total_pages:
            break
    seen: dict[str, dict[str, str]] = {}
    for record in records:
        seen[record["Issue"]] = record
    return sorted(seen.values(), key=lambda item: (item["Date"], item["Issue"]))


def fetch_sporttery_digit_history(game_no: str, digit_count: int, page_size: int = 100, max_pages: int = 80) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
    headers = {"User-Agent": UA, "Referer": "https://www.lottery.gov.cn/"}
    for page_no in range(1, max_pages + 1):
        params = {
            "gameNo": game_no,
            "provinceId": "0",
            "pageSize": str(page_size),
            "isVerify": "1",
            "pageNo": str(page_no),
        }
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            debug_path = DEBUG_DIR / f"sporttery_{game_no}_failed_page_{page_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            debug_path.write_text(str(exc), encoding="utf-8")
            log(f"体彩 {game_no} 第 {page_no} 页抓取失败: {exc}")
            break
        items = payload.get("value", {}).get("list", [])
        if not items:
            break
        for item in items:
            result = str(item.get("lotteryDrawResult", "")).split()
            record = {
                "Issue": str(item.get("lotteryDrawNum", "")).strip(),
                "Date": str(item.get("lotteryDrawTime", "")).strip()[:10],
                "Digit": normalize_numbers(result, digit_count, sort_numbers=False),
            }
            if validate_digit_record(record, digit_count):
                records.append(record)
        total_pages = int(payload.get("value", {}).get("pages") or page_no)
        if page_no >= total_pages:
            break
    seen: dict[str, dict[str, str]] = {}
    for record in records:
        seen[record["Issue"]] = record
    return sorted(seen.values(), key=lambda item: (item["Date"], item["Issue"]))


def fetch_cwl_history(name: str, issue_count: int = 5000) -> list[dict[str, str]]:
    url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
    headers = {"User-Agent": UA, "Referer": "https://www.cwl.gov.cn/"}
    response = requests.get(url, params={"name": name, "issueCount": str(issue_count)}, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if data.get("state") != 0:
        raise RuntimeError(data.get("message", "中国福彩网接口返回异常"))
    return data.get("result") or []


def fetch_cwl_digit_history(name: str, digit_count: int, issue_count: int = 5000) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for item in fetch_cwl_history(name, issue_count):
        record = {
            "Issue": str(item.get("code", ""))[-5:],
            "Date": str(item.get("date", "")).split("(")[0],
            "Digit": normalize_numbers(str(item.get("red", "")), digit_count, sort_numbers=False),
        }
        if validate_digit_record(record, digit_count):
            records.append(record)
    seen: dict[str, dict[str, str]] = {}
    for record in records:
        seen[record["Issue"]] = record
    return sorted(seen.values(), key=lambda item: (item["Date"], item["Issue"]))


def fetch_qlc_history(issue_count: int = 5000) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for item in fetch_cwl_history("qlc", issue_count):
        record = {
            "Issue": str(item.get("code", ""))[-5:],
            "Date": str(item.get("date", "")).split("(")[0],
            "Main": normalize_numbers(str(item.get("red", "")), 7),
            "Special": normalize_numbers(str(item.get("blue", "")), 1),
        }
        if validate_qlc_record(record):
            records.append(record)
    seen: dict[str, dict[str, str]] = {}
    for record in records:
        seen[record["Issue"]] = record
    return sorted(seen.values(), key=lambda item: (item["Date"], item["Issue"]))
