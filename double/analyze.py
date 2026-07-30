#!/usr/bin/env python3
"""
双色球深度统计分析脚本
基于 pandas + numpy + scipy 进行多维统计分析
用法: python analyze.py
"""

import json
import os
import numpy as np
import pandas as pd
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import Counter
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "ssq_data.json")


def load_data():
    """加载历史数据"""
    with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
        records = json.load(f)
    
    # 展开数据
    rows = []
    for r in records:
        reds = [int(x) for x in r["Red"].split(",")]
        row = {
            "issue": r["Issue"],
            "date": r["Date"],
            "blue": int(r["Blue"]),
            "red_sum": sum(reds),
        }
        for i, v in enumerate(reds):
            row[f"r{i+1}"] = v
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df, records


def analyze_red_frequency(df):
    """红球频率统计分析"""
    print("\n" + "=" * 60)
    print("  🔴 红球频率分析 (1-33)")
    print("=" * 60)
    
    # 统计每个号码出现次数
    all_reds = []
    for col in ["r1", "r2", "r3", "r4", "r5", "r6"]:
        all_reds.extend(df[col].tolist())
    
    counter = Counter(all_reds)
    total_draws = len(df)
    expected = total_draws * 6 / 33  # 理论期望次数
    
    print(f"{'号码':<6} {'次数':<6} {'占比':<8} {'偏离':<8} {'Z-Score':<10} {'评级'}")
    print("-" * 60)
    
    results = []
    for num in range(1, 34):
        actual = counter.get(num, 0)
        pct = actual / (total_draws * 6) * 100
        diff = actual - expected
        # Z-score: 偏离 / 标准差 (二项分布近似)
        p = 6/33
        std = np.sqrt(total_draws * p * (1-p))
        z = diff / std
        
        if z > 2.0:
            grade = "🔥🔥 热号"
        elif z > 1.0:
            grade = "🔥 偏热"
        elif z < -2.0:
            grade = "❄️❄️ 冷号"
        elif z < -1.0:
            grade = "❄️ 偏冷"
        else:
            grade = "正常"
        
        print(f"  {num:>2}    {actual:<6} {pct:>5.2f}%  {diff:>+6.0f}   {z:>+7.2f}     {grade}")
        results.append({"num": num, "count": actual, "z_score": round(z, 2), "grade": grade})
    
    # Top/Bottom 5
    results.sort(key=lambda x: x["count"], reverse=True)
    print(f"\n  🏆 热号 Top5: {', '.join(str(r['num']) for r in results[:5])}")
    results.sort(key=lambda x: x["count"])
    print(f"  🥶 冷号 Top5: {', '.join(str(r['num']) for r in results[:5])}")
    
    return results


def analyze_blue_frequency(df):
    """蓝球频率分析"""
    print("\n" + "=" * 60)
    print("  🔵 蓝球频率分析 (1-16)")
    print("=" * 60)
    
    counter = Counter(df["blue"].tolist())
    total_draws = len(df)
    expected = total_draws / 16
    
    print(f"{'号码':<6} {'次数':<6} {'占比':<8} {'偏离':<8} {'评级'}")
    print("-" * 60)
    
    for num in range(1, 17):
        actual = counter.get(num, 0)
        pct = actual / total_draws * 100
        diff = actual - expected
        
        if diff > 15:
            grade = "🔥 热号"
        elif diff > 5:
            grade = "偏热"
        elif diff < -15:
            grade = "❄️ 冷号"
        elif diff < -5:
            grade = "偏冷"
        else:
            grade = "正常"
        
        print(f"  {num:>2}    {actual:<6} {pct:>5.2f}%  {diff:>+6.0f}    {grade}")
    
    sorted_blue = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  🏆 热门蓝球: {', '.join(str(x[0]) for x in sorted_blue[:3])}")
    print(f"  🥶 冷门蓝球: {', '.join(str(x[0]) for x in sorted_blue[-3:])}")


def analyze_sum_distribution(df):
    """红球和值分布统计"""
    print("\n" + "=" * 60)
    print("  📊 红球和值分布")
    print("=" * 60)
    
    sums = df["red_sum"]
    
    stats = {
        "最低": sums.min(),
        "最高": sums.max(),
        "均值": round(sums.mean(), 1),
        "中位数": sums.median(),
        "标准差": round(sums.std(), 1),
        "理论均值": 102,
    }
    
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # 区间分布
    print(f"\n  {'区间':<12} {'期数':<8} {'占比':<8} 分布")
    print("  " + "-" * 50)
    
    buckets = {}
    for s in sums:
        b = (s // 10) * 10
        buckets[b] = buckets.get(b, 0) + 1
    
    for b in sorted(buckets.keys()):
        cnt = buckets[b]
        pct = cnt / len(df) * 100
        bar = "█" * int(pct)
        print(f"  {b:>3}-{b+9:<3}    {cnt:<8} {pct:>5.1f}%   {bar}")


def analyze_consecutive(df):
    """连号分析"""
    print("\n" + "=" * 60)
    print("  🔗 连号分析 (相邻号码同时出现)")
    print("=" * 60)
    
    pairs = Counter()
    for _, row in df.iterrows():
        reds = sorted([row[f"r{i}"] for i in range(1, 7)])
        for i in range(len(reds) - 1):
            if reds[i+1] - reds[i] == 1:
                pairs[f"{reds[i]}-{reds[i+1]}"] += 1
    
    print(f"  {'连号组合':<10} {'次数':<8} 占比")
    print("  " + "-" * 40)
    for pair, cnt in pairs.most_common(10):
        bar = "█" * int(cnt / 10)
        print(f"  {pair:<10} {cnt:<8} {bar}")
    
    # 有连号的期数占比
    has_pair_count = sum(1 for _, row in df.iterrows()
                         if any(row[f"r{i+1}"] - row[f"r{i}"] == 1
                                for i in range(1, 6)
                                for reds in [sorted([row[f"r{j}"] for j in range(1, 7)])]))
    print(f"\n  含连号的期数: {has_pair_count}/{len(df)} ({has_pair_count/len(df)*100:.1f}%)")


def analyze_odd_even(df):
    """奇偶分布分析"""
    print("\n" + "=" * 60)
    print("  ⚖️  奇偶分布")
    print("=" * 60)
    
    odd_count = 0
    even_count = 0
    ratio_counter = Counter()
    
    for _, row in df.iterrows():
        reds = [row[f"r{i}"] for i in range(1, 7)]
        odd = sum(1 for r in reds if r % 2 == 1)
        even = 6 - odd
        odd_count += odd
        even_count += even
        ratio_counter[f"{odd}:{even}"] += 1
    
    total = odd_count + even_count
    print(f"  奇数总次数: {odd_count} ({odd_count/total*100:.1f}%)")
    print(f"  偶数总次数: {even_count} ({even_count/total*100:.1f}%)")
    print(f"\n  奇偶比例分布 (Top 5):")
    for ratio, cnt in ratio_counter.most_common(5):
        bar = "█" * (cnt // 20)
        print(f"    {ratio} : {cnt:>5}期 ({cnt/len(df)*100:.1f}%) {bar}")


def generate_recommendation(df):
    """生成智能推荐"""
    print("\n" + "=" * 60)
    print("  🎯 智能选号参考建议")
    print("=" * 60)
    
    # 红球推荐
    all_reds = []
    for col in ["r1", "r2", "r3", "r4", "r5", "r6"]:
        all_reds.extend(df[col].tolist())
    counter = Counter(all_reds)
    expected = len(df) * 6 / 33
    
    sorted_reds = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    
    print("\n  🔴 红球建议:")
    print(f"     热号关注: {', '.join(str(x[0]) for x in sorted_reds[:8])}")
    print(f"     冷号回避: {', '.join(str(x[0]) for x in sorted_reds[-5:])}")
    
    # 蓝球推荐
    blue_counter = Counter(df["blue"].tolist())
    sorted_blues = sorted(blue_counter.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n  🔵 蓝球建议:")
    print(f"     重点关注: {', '.join(str(x[0]) for x in sorted_blues[:5])}")
    
    # 和值建议
    sums = df["red_sum"]
    low, high = np.percentile(sums, [15, 85])
    print(f"\n  📊 和值建议: {int(low)} ~ {int(high)} 区间 (覆盖70%历史)")
    
    # 奇偶建议
    print(f"  ⚖️  奇偶比建议: 3:3 或 4:2 (最常见)")
    
    print(f"\n  ⚠️  声明: 以上仅为统计规律，彩票开奖完全随机。")


def main():
    print("=" * 60)
    print("  双色球深度统计分析 v2.0 (Python)")
    print(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    df, _ = load_data()
    print(f"\n  数据加载: {len(df)} 期")
    print(f"  日期范围: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
    
    analyze_red_frequency(df)
    analyze_blue_frequency(df)
    analyze_sum_distribution(df)
    analyze_consecutive(df)
    analyze_odd_even(df)
    generate_recommendation(df)
    
    print("\n" + "=" * 60)
    print("  分析完成! 双击 ssq_analyzer.html 查看可视化")
    print("=" * 60)


if __name__ == "__main__":
    main()
