#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lottery definitions used by fetchers, rules, and dashboard rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NumberArea:
    key: str
    label: str
    count: int
    min_number: int
    max_number: int
    color: str
    ordered: bool = False
    unique: bool = True


@dataclass(frozen=True)
class LotteryConfig:
    lottery_id: str
    name: str
    short_name: str
    official_source: str
    source_url: str
    data_file: str
    areas: tuple[NumberArea, ...]
    draw_days: str
    enabled: bool = True


LOTTERIES: dict[str, LotteryConfig] = {
    "ssq": LotteryConfig(
        lottery_id="ssq",
        name="中国福利彩票双色球",
        short_name="双色球",
        official_source="中国福彩网",
        source_url="https://www.cwl.gov.cn/",
        data_file="ssq_data.json",
        draw_days="每周二、四、日开奖",
        areas=(
            NumberArea("red", "红球", 6, 1, 33, "warm"),
            NumberArea("blue", "蓝球", 1, 1, 16, "cool"),
        ),
    ),
    "dlt": LotteryConfig(
        lottery_id="dlt",
        name="中国体育彩票超级大乐透",
        short_name="大乐透",
        official_source="中国体彩网",
        source_url="https://www.lottery.gov.cn/",
        data_file="dlt_data.json",
        draw_days="每周一、三、六开奖",
        areas=(
            NumberArea("front", "前区", 5, 1, 35, "warm"),
            NumberArea("back", "后区", 2, 1, 12, "cool"),
        ),
    ),
    "fc3d": LotteryConfig(
        lottery_id="fc3d",
        name="中国福利彩票3D",
        short_name="福彩3D",
        official_source="中国福彩网",
        source_url="https://www.cwl.gov.cn/",
        data_file="fc3d_data.json",
        draw_days="每天开奖",
        areas=(NumberArea("digit", "开奖号码", 3, 0, 9, "neutral", ordered=True, unique=False),),
    ),
    "pl3": LotteryConfig(
        lottery_id="pl3",
        name="中国体育彩票排列3",
        short_name="排列3",
        official_source="中国体彩网",
        source_url="https://www.lottery.gov.cn/",
        data_file="pl3_data.json",
        draw_days="每天开奖",
        areas=(NumberArea("digit", "开奖号码", 3, 0, 9, "neutral", ordered=True, unique=False),),
    ),
    "pl5": LotteryConfig(
        lottery_id="pl5",
        name="中国体育彩票排列5",
        short_name="排列5",
        official_source="中国体彩网",
        source_url="https://www.lottery.gov.cn/",
        data_file="pl5_data.json",
        draw_days="每天开奖",
        areas=(NumberArea("digit", "开奖号码", 5, 0, 9, "neutral", ordered=True, unique=False),),
    ),
    "qxc": LotteryConfig(
        lottery_id="qxc",
        name="中国体育彩票七星彩",
        short_name="七星彩",
        official_source="中国体彩网",
        source_url="https://www.lottery.gov.cn/",
        data_file="qxc_data.json",
        draw_days="每周二、五、日开奖",
        areas=(NumberArea("digit", "开奖号码", 7, 0, 9, "neutral", ordered=True, unique=False),),
    ),
    "qlc": LotteryConfig(
        lottery_id="qlc",
        name="中国福利彩票七乐彩",
        short_name="七乐彩",
        official_source="中国福彩网",
        source_url="https://www.cwl.gov.cn/",
        data_file="qlc_data.json",
        draw_days="每周一、三、五开奖",
        areas=(
            NumberArea("main", "基本号", 7, 1, 30, "warm"),
            NumberArea("special", "特别号", 1, 1, 30, "cool"),
        ),
    ),
}


DISCLAIMER = (
    "本工具仅基于公开开奖数据进行整理、查询、核验和统计展示，不销售彩票，不提供代购服务，"
    "不构成任何中奖承诺或投资建议。开奖结果以中国福彩网、中国体彩网等官方发布为准，请理性购彩。"
)


FORBIDDEN_PROMISE_WORDS = ("必中", "稳赚", "保证中奖", "预测准确")
