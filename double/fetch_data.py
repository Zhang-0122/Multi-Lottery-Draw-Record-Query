#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双色球历史数据采集 (Python版) — python fetch_data.py"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import requests, json, re, os, shutil, time
from datetime import datetime

from lottery_sources import (
    fetch_cwl_digit_history,
    fetch_dlt_history,
    fetch_qlc_history,
    fetch_sporttery_digit_history,
    load_json_records,
    save_json_records,
    validate_digit_record,
    validate_dlt_record,
    validate_qlc_record,
)

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
CACHE_DIR = os.path.join(PROJECT_ROOT, "cashe")
LOG_DIR = os.path.join(CACHE_DIR, "logs")
OUT = os.path.join(DIR, "ssq_data.json")
DLT_OUT = os.path.join(DIR, "dlt_data.json")
EXTRA_LOTTERIES = {
    "fc3d": {
        "label": "福彩3D",
        "out": os.path.join(DIR, "fc3d_data.json"),
        "fetch": lambda: fetch_cwl_digit_history("3d", 3, issue_count=10000),
        "validate": lambda record: validate_digit_record(record, 3),
    },
    "pl3": {
        "label": "排列3",
        "out": os.path.join(DIR, "pl3_data.json"),
        "fetch": lambda: fetch_sporttery_digit_history("35", 3, max_pages=100),
        "validate": lambda record: validate_digit_record(record, 3),
    },
    "pl5": {
        "label": "排列5",
        "out": os.path.join(DIR, "pl5_data.json"),
        "fetch": lambda: fetch_sporttery_digit_history("350133", 5, max_pages=100),
        "validate": lambda record: validate_digit_record(record, 5),
    },
    "qxc": {
        "label": "七星彩",
        "out": os.path.join(DIR, "qxc_data.json"),
        "fetch": lambda: fetch_sporttery_digit_history("04", 7, max_pages=100),
        "validate": lambda record: validate_digit_record(record, 7),
    },
    "qlc": {
        "label": "七乐彩",
        "out": os.path.join(DIR, "qlc_data.json"),
        "fetch": lambda: fetch_qlc_history(issue_count=10000),
        "validate": validate_qlc_record,
    },
}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
TIMEOUT = 20

os.makedirs(LOG_DIR, exist_ok=True)


def log(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(LOG_DIR, "fetch_data.log"), "a", encoding="utf-8") as file:
        file.write(f"[{stamp}] {message}\n")


def normalize_red(red):
    return ",".join(f"{int(value):02d}" for value in str(red).replace("，", ",").split(",") if value.strip())


def normalize_blue(blue):
    return f"{int(str(blue).strip()):02d}"


def validate_record(record):
    try:
        reds = [int(value) for value in record["Red"].split(",")]
        blue = int(record["Blue"])
        datetime.strptime(record["Date"], "%Y-%m-%d")
    except (KeyError, TypeError, ValueError):
        return False
    return len(reds) == 6 and len(set(reds)) == 6 and reds == sorted(reds) and all(1 <= value <= 33 for value in reds) and 1 <= blue <= 16


def load_existing():
    if not os.path.exists(OUT):
        return []
    with open(OUT, "r", encoding="utf-8-sig") as file:
        data = json.load(file)
    return data if isinstance(data, list) else []

def fetch_500(start, end):
    print(f"[1/3] 500.com {start}~{end} ...", end=" ")
    url = f"https://datachart.500.com/ssq/history/newinc/history.php?start={start}&end={end}"
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    resp.raise_for_status()
    resp.encoding = "gb2312"
    html = resp.text
    # 必须先删掉 HTML 注释，否则 <!--<td>2</td>--> 里的行号会被误当作期号
    html = re.sub(r"<!--.*?-->", "", html)
    rows = re.findall(r'<tr class="t_tr1">.*?<td>(\d+)</td>(.*?)</tr>', html, re.DOTALL)
    recs = []
    for issue, row in rows:
        reds = re.findall(r't_cfont2">(\d+)</td>', row)
        blue = re.search(r't_cfont4">(\d+)</td>', row)
        date = re.search(r'(\d{4}-\d{2}-\d{2})', row)
        if len(reds) >= 6 and blue and date:
            recs.append({"Issue": issue, "Date": date.group(1),
                         "Red": normalize_red(",".join(reds[:6])), "Blue": normalize_blue(blue.group(1))})
    print(f"OK {len(recs)} records")
    return recs

def fetch_cwl():
    print("[2/3] cwl.gov.cn ...", end=" ")
    url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount=300"
    try:
        resp = requests.get(url, headers={"User-Agent": UA, "Referer": "https://www.cwl.gov.cn/"}, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"FAIL {exc}")
        log(f"cwl.gov.cn 300期接口不可用: {exc}")
        return []
    recs = []
    if data.get("state") == 0:
        for item in data["result"]:
            issue = item["code"][-5:]
            recs.append({"Issue": issue,
                         "Date": item["date"].split("(")[0],
                         "Red": normalize_red(item["red"]), "Blue": normalize_blue(item["blue"])})
    else:
        print(f"FAIL {data.get('message', '未知错误')}")
        log(f"cwl.gov.cn 300期接口返回异常: {data.get('message', '未知错误')}")
        return []
    print(f"OK {len(recs)} records")
    return recs


def fetch_cwl_latest():
    print("[0/3] cwl.gov.cn latest ...", end=" ")
    url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount=1"
    try:
        resp = requests.get(url, headers={"User-Agent": UA, "Referer": "https://www.cwl.gov.cn/"}, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"FAIL {exc}")
        log(f"cwl.gov.cn latest 接口不可用: {exc}")
        return None
    if data.get("state") != 0 or not data.get("result"):
        print(f"FAIL {data.get('message', '未知错误')}")
        log(f"cwl.gov.cn latest 返回异常: {data.get('message', '未知错误')}")
        return None
    item = data["result"][0]
    latest = {
        "Issue": item["code"][-5:],
        "Date": item["date"].split("(")[0],
        "Red": normalize_red(item["red"]),
        "Blue": normalize_blue(item["blue"]),
    }
    print(f"OK {latest['Issue']} {latest['Date']}")
    return latest


def save_records(records):
    valid = [record for record in records if validate_record(record)]
    if len(valid) != len(records):
        print(f"  注意：过滤无效记录 {len(records) - len(valid)} 条")
    if not valid:
        raise RuntimeError("没有拿到有效开奖记录，已保留原数据")
    valid = sorted(valid, key=lambda x: x["Date"])
    if os.path.exists(OUT):
        backup = os.path.join(CACHE_DIR, f"ssq_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy2(OUT, backup)
        log(f"已备份旧数据: {backup}")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(valid, f, ensure_ascii=False)
    return valid


def sync_dlt():
    print("[DLT] sporttery.cn ...", end=" ")
    try:
        fetched = fetch_dlt_history()
        valid = [record for record in fetched if validate_dlt_record(record)]
        if not valid:
            raise RuntimeError("大乐透官方接口没有返回有效记录")
        existing = load_json_records(DLT_OUT)
        if existing:
            current_latest = sorted(existing, key=lambda item: item["Date"])[-1]
            fetched_latest = sorted(valid, key=lambda item: item["Date"])[-1]
            if current_latest == fetched_latest and len(existing) == len(valid):
                print(f"无需同步，当前已到 {current_latest['Date']} 第 {current_latest['Issue']} 期")
                log(f"大乐透无需同步: {current_latest['Date']} 第 {current_latest['Issue']} 期")
                return existing
        saved = save_json_records(DLT_OUT, valid, "大乐透")
        latest = saved[-1]
        print(f"OK {len(saved)} records，已到 {latest['Date']} 第 {latest['Issue']} 期")
        log(f"大乐透刷新成功: {saved[0]['Date']} ~ {latest['Date']} 共 {len(saved)} 期")
        return saved
    except Exception as exc:
        existing = load_json_records(DLT_OUT)
        print(f"FAIL {exc}")
        if existing:
            latest = sorted(existing, key=lambda item: item["Date"])[-1]
            print(f"  大乐透保留旧数据: {latest['Date']} 第 {latest['Issue']} 期，共 {len(existing)} 期")
            log(f"大乐透刷新失败但保留旧数据: {exc}")
            return existing
        log(f"大乐透刷新失败且无旧数据: {exc}")
        return []


def sync_extra_lottery(key, info):
    label = info["label"]
    out = info["out"]
    print(f"[{key.upper()}] {label} ...", end=" ")
    try:
        fetched = info["fetch"]()
        valid = [record for record in fetched if info["validate"](record)]
        if not valid:
            raise RuntimeError(f"{label} 官方接口没有返回有效记录")
        existing = load_json_records(out)
        if existing:
            current_latest = sorted(existing, key=lambda item: item["Date"])[-1]
            fetched_latest = sorted(valid, key=lambda item: item["Date"])[-1]
            if current_latest == fetched_latest and len(existing) == len(valid):
                print(f"无需同步，当前已到 {current_latest['Date']} 第 {current_latest['Issue']} 期")
                log(f"{label}无需同步: {current_latest['Date']} 第 {current_latest['Issue']} 期")
                return existing
        saved = save_json_records(out, valid, label)
        latest = saved[-1]
        print(f"OK {len(saved)} records，已到 {latest['Date']} 第 {latest['Issue']} 期")
        log(f"{label}刷新成功: {saved[0]['Date']} ~ {latest['Date']} 共 {len(saved)} 期")
        return saved
    except Exception as exc:
        existing = load_json_records(out)
        print(f"FAIL {exc}")
        if existing:
            latest = sorted(existing, key=lambda item: item["Date"])[-1]
            print(f"  {label}保留旧数据: {latest['Date']} 第 {latest['Issue']} 期，共 {len(existing)} 期")
            log(f"{label}刷新失败但保留旧数据: {exc}")
            return existing
        log(f"{label}刷新失败且无旧数据: {exc}")
        return []

def main():
    t0 = time.time()
    print("=" * 50)
    print("  双色球数据采集 v2.0 (Python)")
    print("=" * 50)
    try:
        current_year = datetime.now().year % 100
        end_issue = f"{current_year:02d}200"
        a = fetch_500("03001", end_issue)
        time.sleep(0.5)
        b = fetch_cwl()
        existing = load_existing()
        # 以期号为键去重
        seen = {}
        for r in a + b:
            seen[r["Issue"]] = r
        merged = sorted(seen.values(), key=lambda x: x["Date"])
        if existing:
            current_latest = existing[-1]
            merged_latest = merged[-1]
            if (
                current_latest.get("Issue") == merged_latest["Issue"]
                and current_latest.get("Date") == merged_latest["Date"]
                and current_latest.get("Red") == merged_latest["Red"]
                and current_latest.get("Blue") == merged_latest["Blue"]
            ):
                print("[3/3] 官方最新开奖未变化，跳过同步。")
                print(f"  当前已同步到: {current_latest['Issue']}期 {current_latest['Date']}")
                log(f"无需同步: 当前已是最新 {current_latest['Issue']}期 {current_latest['Date']}")
                return
        merged = save_records(seen.values())
        print(f"[3/3] 合并保存: {len(merged)} records -> {OUT}")
        print("=" * 50)
        print(f"  {merged[0]['Date']} ~ {merged[-1]['Date']}  共 {len(merged)} 期")
        print(f"  耗时 {time.time()-t0:.1f}s")
        print("=" * 50)
        log(f"刷新成功: {merged[0]['Date']} ~ {merged[-1]['Date']} 共 {len(merged)} 期")
    except Exception as exc:
        existing = load_existing()
        print("")
        print("刷新失败，但原有数据已保留，不影响继续使用。")
        if existing:
            print(f"当前仍可使用本地数据: {existing[0]['Date']} ~ {existing[-1]['Date']} 共 {len(existing)} 期")
            print("已有本地数据可用，本次自动任务按保留旧数据处理。")
            log(f"刷新失败但保留旧数据继续: {exc}")
            return
        print(f"失败原因: {exc}")
        print(f"日志位置: {os.path.join(LOG_DIR, 'fetch_data.log')}")
        log(f"刷新失败: {exc}")
        raise SystemExit(1)
    finally:
        sync_dlt()
        for key, info in EXTRA_LOTTERIES.items():
            sync_extra_lottery(key, info)

if __name__ == "__main__":
    main()
