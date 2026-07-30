#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prize checking rules for supported lottery games."""

from __future__ import annotations

from typing import Iterable


def _to_set(values: Iterable[int | str]) -> set[int]:
    return {int(value) for value in values}


def _split_numbers(value: str) -> list[int]:
    return [int(item) for item in str(value).replace("，", ",").split(",") if item.strip()]


def _check_ssq(red_hits: int, blue_hits: int) -> str:
    if red_hits == 6 and blue_hits == 1:
        return "一等奖"
    if red_hits == 6 and blue_hits == 0:
        return "二等奖"
    if red_hits == 5 and blue_hits == 1:
        return "三等奖"
    if red_hits == 5 or (red_hits == 4 and blue_hits == 1):
        return "四等奖"
    if (red_hits == 4 and blue_hits == 0) or (red_hits == 3 and blue_hits == 1):
        return "五等奖"
    if blue_hits == 1:
        return "六等奖"
    return "未中奖"


def _check_dlt(front_hits: int, back_hits: int) -> str:
    if front_hits == 5 and back_hits == 2:
        return "一等奖"
    if front_hits == 5 and back_hits == 1:
        return "二等奖"
    if front_hits == 5 and back_hits == 0:
        return "三等奖"
    if front_hits == 4 and back_hits == 2:
        return "四等奖"
    if front_hits == 4 and back_hits == 1:
        return "五等奖"
    if front_hits == 3 and back_hits == 2:
        return "六等奖"
    if front_hits == 4 and back_hits == 0:
        return "七等奖"
    if (front_hits == 3 and back_hits == 1) or (front_hits == 2 and back_hits == 2):
        return "八等奖"
    if (
        (front_hits == 3 and back_hits == 0)
        or (front_hits == 2 and back_hits == 1)
        or (front_hits == 1 and back_hits == 2)
        or (front_hits == 0 and back_hits == 2)
    ):
        return "九等奖"
    return "未中奖"


def check_prize(lottery_id: str, draw: dict[str, str], ticket: list[list[int | str]]) -> dict[str, int | str]:
    """Check a ticket against one draw.

    The returned level is a convenience reference. Final prize and redemption
    details must still follow official announcements and local rules.
    """

    if lottery_id == "ssq":
        draw_red = _to_set(_split_numbers(draw["Red"]))
        draw_blue = _to_set([draw["Blue"]])
        ticket_red = _to_set(ticket[0])
        ticket_blue = _to_set(ticket[1])
        red_hits = len(draw_red & ticket_red)
        blue_hits = len(draw_blue & ticket_blue)
        return {"level": _check_ssq(red_hits, blue_hits), "main_hits": red_hits, "special_hits": blue_hits}

    if lottery_id == "dlt":
        draw_front = _to_set(_split_numbers(draw["Front"]))
        draw_back = _to_set(_split_numbers(draw["Back"]))
        ticket_front = _to_set(ticket[0])
        ticket_back = _to_set(ticket[1])
        front_hits = len(draw_front & ticket_front)
        back_hits = len(draw_back & ticket_back)
        return {"level": _check_dlt(front_hits, back_hits), "main_hits": front_hits, "special_hits": back_hits}

    raise ValueError(f"Unsupported lottery: {lottery_id}")
