#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a static multi-page lottery dashboard."""

from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from statistics import mean

from lottery_config import DISCLAIMER, LOTTERIES, LotteryConfig


ROOT = Path(__file__).resolve().parent
HOME_FILE = ROOT / "ssq_analyzer.html"
PAGE_IDS = ("ssq", "dlt", "fc3d", "pl3", "pl5", "qxc", "qlc")


def load_records(config: LotteryConfig) -> list[dict[str, str]]:
    path = ROOT / config.data_file
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)
    records = data if isinstance(data, list) else []
    return sorted(records, key=lambda item: (item.get("Date", ""), item.get("Issue", "")))


def split_numbers(value: str) -> list[int]:
    return [int(item) for item in str(value).replace("，", ",").split(",") if item.strip()]


def number(value: int | str) -> str:
    return f"{int(value):02d}"


def latest_text(records: list[dict[str, str]]) -> str:
    if not records:
        return "等待同步"
    latest = records[-1]
    return f"已同步到 {latest['Date']} 第 {latest['Issue']} 期"


def record_groups(lottery_id: str, record: dict[str, str]) -> list[list[int]]:
    if lottery_id == "ssq":
        return [split_numbers(record["Red"]), split_numbers(record["Blue"])]
    if lottery_id == "dlt":
        return [split_numbers(record["Front"]), split_numbers(record["Back"])]
    if lottery_id == "qlc":
        return [split_numbers(record["Main"]), split_numbers(record["Special"])]
    return [split_numbers(record["Digit"])]


def area_class(color: str) -> str:
    if color == "cool":
        return "cool"
    if color == "neutral":
        return "neutral"
    return "warm"


def balls_html(lottery_id: str, record: dict[str, str]) -> str:
    config = LOTTERIES[lottery_id]
    parts: list[str] = []
    for index, group in enumerate(record_groups(lottery_id, record)):
        css = area_class(config.areas[index].color)
        parts.extend(f'<span class="ball {css}">{number(value)}</span>' for value in group)
    return "".join(parts)


def group_balls_html(values: list[int], color: str) -> str:
    css = area_class(color)
    return "".join(f'<span class="ball {css}">{number(value)}</span>' for value in values)


def all_payload() -> dict[str, dict[str, object]]:
    payload: dict[str, dict[str, object]] = {}
    for lottery_id in PAGE_IDS:
        config = LOTTERIES[lottery_id]
        records = load_records(config)
        payload[lottery_id] = {
            "id": lottery_id,
            "name": config.short_name,
            "full_name": config.name,
            "source": config.official_source,
            "source_url": config.source_url,
            "draw_days": config.draw_days,
            "records": records,
            "latest_text": latest_text(records),
        }
    return payload


def render_home(payload: dict[str, dict[str, object]]) -> str:
    cards = []
    status_rows = []
    for lottery_id in PAGE_IDS:
        item = payload[lottery_id]
        records = item["records"]
        latest = records[-1] if records else {}
        card_balls = balls_html(lottery_id, latest) if records else '<span class="muted">等待同步</span>'
        cards.append(
            f"""
            <a class="lottery-card" href="{lottery_id}.html">
              <span class="lottery-top"><strong>{html.escape(str(item["name"]))}</strong><small>{html.escape(str(item["source"]))}</small></span>
              <span class="balls">{card_balls}</span>
              <span class="lottery-meta">{html.escape(str(item["latest_text"]))}<br>{html.escape(str(item["draw_days"]))}</span>
            </a>
            """
        )
        status_rows.append(
            f'<div class="status-row"><span>{html.escape(str(item["name"]))}</span><strong>{html.escape(str(item["latest_text"]))}</strong></div>'
        )

    search_index = json.dumps(
        [
            {"id": lottery_id, "name": payload[lottery_id]["name"], "url": f"{lottery_id}.html"}
            for lottery_id in PAGE_IDS
        ],
        ensure_ascii=False,
    )
    return page_shell(
        title="彩票开奖数据中心",
        body=f"""
        <header class="home-hero">
          <section class="hero-main">
            <div class="hero-title">
              <div>
                <h1>彩票开奖数据中心</h1>
                <p class="muted">公开开奖记录查询、中奖核验、号码统计和同步说明。选择一个彩种，进入它的独立详情页。</p>
              </div>
              <span class="badge">官方数据 · 自动同步 · 合规展示</span>
            </div>
            <div class="search-row">
              <input id="homeSearch" type="search" placeholder="输入彩种名、期号、日期或完整号码，例如：大乐透 26084">
              <button class="btn primary" id="homeSearchBtn" type="button">进入查询</button>
            </div>
          </section>
          <aside class="panel sync-panel">
            <div class="panel-title"><h2>同步与来源</h2><span class="ok">自动检查</span></div>
            <div class="status-list">{''.join(status_rows)}</div>
            <div class="status-row source-row"><span>官方来源</span><strong>中国福彩网 / 中国体彩网</strong></div>
          </aside>
        </header>
        <section class="lottery-grid">{''.join(cards)}</section>
        <section class="notice">
          <strong>权威免责声明</strong>
          <p>{html.escape(DISCLAIMER)}</p>
        </section>
        <script>
          const SEARCH_INDEX = {search_index};
          function goSearch() {{
            const raw = document.getElementById("homeSearch").value.trim().toLowerCase();
            const match = SEARCH_INDEX.find(item => raw.includes(String(item.name).toLowerCase()) || String(item.name).toLowerCase().includes(raw));
            window.location.href = match ? match.url : "ssq.html";
          }}
          document.getElementById("homeSearchBtn").addEventListener("click", goSearch);
          document.getElementById("homeSearch").addEventListener("keydown", event => {{ if (event.key === "Enter") goSearch(); }});
        </script>
        """,
    )


def render_detail(lottery_id: str, payload: dict[str, dict[str, object]]) -> str:
    config = LOTTERIES[lottery_id]
    item = payload[lottery_id]
    records: list[dict[str, str]] = item["records"]  # type: ignore[assignment]
    latest = records[-1] if records else {}
    nav = "".join(
        f'<a class="nav-pill {"active" if page_id == lottery_id else ""}" href="{page_id}.html">{html.escape(LOTTERIES[page_id].short_name)}</a>'
        for page_id in PAGE_IDS
    )
    data_json = json.dumps(
        {
            "id": lottery_id,
            "name": config.short_name,
            "areas": [area.__dict__ for area in config.areas],
            "latest": latest,
            "records": records,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return page_shell(
        title=f"{config.short_name}详情页",
        body=f"""
        <header class="detail-hero">
          <a class="back-link" href="index.html">← 返回首页</a>
          <div class="detail-title">
            <div>
              <h1>{html.escape(config.short_name)}详情页</h1>
              <p class="muted">{html.escape(config.name)} · {html.escape(config.draw_days)} · {html.escape(config.official_source)}</p>
            </div>
            <span class="badge">{html.escape(latest_text(records))}</span>
          </div>
          <nav class="nav-row">{nav}</nav>
        </header>
        <main class="detail-layout">
          <aside class="left-panel">
            <section class="panel">
              <h2>最新开奖</h2>
              <div class="balls latest-balls">{balls_html(lottery_id, latest) if records else '<span class="muted">等待同步</span>'}</div>
              <p class="muted">{html.escape(latest_text(records))}</p>
            </section>
            <section class="panel">
              <h2>彩种规则</h2>
              <p class="muted">{html.escape(rule_text(config))}</p>
            </section>
            <section class="panel">
              <h2>快捷操作</h2>
              <div class="quick-grid">
                <a href="#checker">中奖核验</a>
                <a href="#stats">号码统计</a>
                <a href="#history">历史记录</a>
                <a href="#trend">走势分析</a>
              </div>
            </section>
          </aside>
          <section class="right-panel">
            {render_summary(config, records)}
            {render_checker(config, lottery_id)}
            {render_stats(config, lottery_id, records)}
            {render_trend(config, lottery_id, records)}
            {render_history(config, lottery_id, records)}
            {render_recommend(config, lottery_id, records)}
            <section class="notice">
              <strong>权威免责声明</strong>
              <p>{html.escape(DISCLAIMER)}</p>
            </section>
          </section>
        </main>
        <script>
          const GAME = {data_json};
          {detail_script()}
        </script>
        """,
    )


def rule_text(config: LotteryConfig) -> str:
    return "；".join(
        f"{area.label}{area.count}个，范围{area.min_number}-{area.max_number}{'，按顺序' if area.ordered else ''}"
        for area in config.areas
    ) + "。"


def render_summary(config: LotteryConfig, records: list[dict[str, str]]) -> str:
    total = len(records)
    latest = records[-1] if records else {}
    latest_date = latest.get("Date", "等待同步")
    latest_issue = latest.get("Issue", "等待同步")
    return f"""
    <section class="panel">
      <div class="panel-title"><h2>{html.escape(config.short_name)}总览</h2><span class="muted">专属分析区</span></div>
      <div class="summary-grid">
        <div class="summary-card"><strong>{total}</strong><span>历史期数</span></div>
        <div class="summary-card"><strong>{html.escape(str(latest_issue))}</strong><span>最新期号</span></div>
        <div class="summary-card"><strong>{html.escape(str(latest_date))}</strong><span>最新日期</span></div>
      </div>
      <p class="muted summary-text">本页只围绕{html.escape(config.short_name)}展示：最新开奖、中奖核验、历史记录、频率统计、走势分析和统计参考。</p>
    </section>
    """


def render_checker(config: LotteryConfig, lottery_id: str) -> str:
    main = config.areas[0]
    special = config.areas[1] if len(config.areas) > 1 else None
    special_text = f"第二栏填写{special.label}。" if special else "本彩种没有第二栏，留空即可。"
    return f"""
    <section class="panel" id="checker">
      <div class="panel-title"><h2>中奖核验</h2><span class="muted">以官方规则为准</span></div>
      <div class="checker-help">
        <strong>中奖核验是做什么的？</strong>
        <p class="muted">它是一个“开奖后对号工具”：你把自己手里的号码填进来，页面会按本彩种规则和最新一期开奖结果比对，显示命中数量与参考奖级，方便你快速核对。</p>
        <p class="muted">填写方法：第一栏填写{html.escape(main.label)}，{html.escape(special_text)}如果有多注号码，可以粘贴到批量核验框里，一行一注。核验结果仅供参考，最终以官方公告和兑奖规则为准。</p>
        <p class="muted">关于倍率：如果用户实际购买时选择了多倍投注，倍率只用于开奖后按实际投注倍数估算参考奖金；增加倍率不会提高单注中奖概率，也不应被理解为推荐倍投或收益方案。请按个人情况理性参与。</p>
      </div>
      <div class="form-grid">
        <label>{html.escape(main.label)}<input id="mainNumbers" placeholder="{main.count}个号码，范围{main.min_number}-{main.max_number}"></label>
        <label>{html.escape(special.label if special else "二区号码")}<input id="specialNumbers" placeholder="{f'{special.count}个号码，范围{special.min_number}-{special.max_number}' if special else '数字彩留空'}"></label>
      </div>
      <div class="actions">
        <button class="btn primary" id="checkSingle" type="button">核验当前号码</button>
        <button class="btn" id="fillExample" type="button">示例填入</button>
        <button class="btn" id="clearResult" type="button">清空结果</button>
      </div>
      <label class="batch-label">批量核验（一行一注，前后区可用 + 分隔）</label>
      <textarea id="batchNumbers"></textarea>
      <div class="actions">
        <button class="btn" id="checkBatch" type="button">批量核验</button>
        <button class="btn" id="exportCsv" type="button">导出 CSV</button>
      </div>
      <div class="result" id="checkResult">这里用于开奖后核对号码：输入你持有的号码，再点击“核验当前号码”或“批量核验”。</div>
    </section>
    """


def render_stats(config: LotteryConfig, lottery_id: str, records: list[dict[str, str]]) -> str:
    blocks = []
    for area_index, area in enumerate(config.areas):
        counter: Counter[int] = Counter()
        for record in records:
            for value in record_groups(lottery_id, record)[area_index]:
                counter[value] += 1
        max_count = max(counter.values(), default=1)
        expected = len(records) * area.count / (area.max_number - area.min_number + 1) if records else 0
        rows = []
        for value in range(area.min_number, area.max_number + 1):
            count = counter[value]
            width = round(count / max_count * 100, 2) if max_count else 0
            tag = "热" if expected and count >= expected * 1.08 else "冷" if expected and count <= expected * 0.92 else "中"
            fill = "cool-fill" if area.color == "cool" else ""
            rows.append(
                f'<div class="freq-row"><span class="mini-ball {area_class(area.color)}">{number(value)}</span><span class="track"><span class="fill {fill}" style="width:{width}%"></span></span><span>{count}次</span><span>{tag}</span></div>'
            )
        blocks.append(
            f"""
            <div class="mini-panel">
              <div class="panel-title"><h3>{html.escape(config.short_name)}{html.escape(area.label)}频率</h3><span class="muted">{area.min_number}-{area.max_number}</span></div>
              <div class="freq-list">{''.join(rows)}</div>
            </div>
            """
        )
    return f'<section class="panel" id="stats"><div class="panel-title"><h2>号码统计</h2><span class="muted">日期切换功能</span></div><div class="freq-grid">{"".join(blocks)}</div></section>'


def render_trend(config: LotteryConfig, lottery_id: str, records: list[dict[str, str]]) -> str:
    recent = records[-50:]
    area = config.areas[0]
    metric_name = f"{area.label}和值"
    if len(recent) < 2:
        chart = '<p class="muted">暂无走势数据。</p>'
    else:
        values = [sum(record_groups(lottery_id, record)[0]) for record in recent]
        width, height = 860, 260
        left, right, top, bottom = 48, 18, 18, 36
        low, high = min(values) - 5, max(values) + 5
        span = high - low or 1

        def x(index: int) -> float:
            return left + index / max(1, len(values) - 1) * (width - left - right)

        def y(value: float) -> float:
            return top + (high - value) / span * (height - top - bottom)

        path = " ".join(("M" if index == 0 else "L") + f"{x(index):.1f},{y(value):.1f}" for index, value in enumerate(values))
        avg = round(mean(values), 1)
        grid = []
        for step in range(5):
            value = round(low + (high - low) * step / 4)
            grid.append(f'<line class="grid-line" x1="{left}" y1="{y(value):.1f}" x2="{width-right}" y2="{y(value):.1f}"></line>')
            grid.append(f'<text class="axis" x="{left-8}" y="{y(value)+4:.1f}" text-anchor="end">{value}</text>')
        dots = "".join(
            f'<circle class="trend-dot" cx="{x(index):.1f}" cy="{y(value):.1f}" r="3"><title>{html.escape(recent[index]["Issue"])}期 {html.escape(recent[index]["Date"])}：{value}</title></circle>'
            for index, value in enumerate(values)
        )
        latest_value = values[-1]
        previous_value = values[-2]
        direction = "上升" if latest_value > previous_value else "下降" if latest_value < previous_value else "持平"
        trend_note = f"""
        <div class="trend-note">
          <strong>这张图怎么看？</strong>
          <p class="muted">每个点代表一期，把当期{html.escape(area.label)}的号码相加，得到一个“{html.escape(metric_name)}”。横向从旧到新，纵向越高表示和值越大；灰色虚线是近50期平均值。</p>
          <p class="muted">它只能帮助观察历史波动，比如近期和值偏高还是偏低；不能说明下一期会开大或开小，更不能作为中奖承诺。</p>
        </div>
        <div class="trend-metrics">
          <div><strong>{latest_value}</strong><span>最新和值</span></div>
          <div><strong>{avg}</strong><span>近50期均值</span></div>
          <div><strong>{max(values)}</strong><span>近50期最高</span></div>
          <div><strong>{min(values)}</strong><span>近50期最低</span></div>
          <div><strong>{direction}</strong><span>较上一期</span></div>
        </div>
        """
        chart = f"""
        {trend_note}
        <svg class="trend-svg" viewBox="0 0 {width} {height}" role="img" aria-label="近50期{html.escape(metric_name)}走势">
          {''.join(grid)}
          <line class="avg-line" x1="{left}" y1="{y(avg):.1f}" x2="{width-right}" y2="{y(avg):.1f}"></line>
          <text class="axis" x="{width-right-6}" y="{y(avg)-8:.1f}" text-anchor="end">均值 {avg}</text>
          <path class="trend-line" d="{path}"></path>{dots}
        </svg>
        """
    return f'<section class="panel" id="trend"><div class="panel-title"><h2>近50期和值走势</h2><span class="muted">说明历史波动，不预测未来</span></div>{chart}</section>'


def render_history(config: LotteryConfig, lottery_id: str, records: list[dict[str, str]]) -> str:
    rows = []
    years = sorted({record["Date"][:4] for record in records}, reverse=True)
    latest_year = years[0] if years else ""
    options = '<option value="all">全部年份</option>' + "".join(f'<option value="{year}">{year}年</option>' for year in years)
    for record in reversed(records):
        groups = record_groups(lottery_id, record)
        first = group_balls_html(groups[0], config.areas[0].color)
        second = group_balls_html(groups[1], config.areas[1].color) if len(groups) > 1 else '<span class="muted">无</span>'
        rows.append(
            f'<tr data-year="{html.escape(record["Date"][:4])}"><td>{html.escape(record["Issue"])}</td><td>{html.escape(record["Date"])}</td><td>{first}</td><td>{second}</td></tr>'
        )
    return f"""
    <section class="panel" id="history">
      <div class="panel-title"><h2>历史记录</h2><span class="muted">完整数据：{html.escape(years[-1] if years else "")}年至{html.escape(latest_year)}年</span></div>
      <div class="year-tools">
        <label>按年份查看：
          <select id="yearSelect">{options}</select>
        </label>
        <span class="muted" id="yearSummary">完整数据共 {len(records)} 期，可切换到某一年单独查看。</span>
      </div>
      <div class="table-wrap"><table><thead><tr><th>期号</th><th>日期</th><th>一区/开奖号码</th><th>二区/特别号</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
    </section>
    """


def render_recommend(config: LotteryConfig, lottery_id: str, records: list[dict[str, str]]) -> str:
    parts = []
    for area_index, area in enumerate(config.areas):
        counter: Counter[int] = Counter()
        for record in records:
            for value in record_groups(lottery_id, record)[area_index]:
                counter[value] += 1
        numbers = " ".join(number(value) for value, _ in counter.most_common(area.count))
        parts.append(f"{area.label}：{numbers}")
    return f"""
    <section class="panel" id="recommend">
      <div class="panel-title"><h2>统计参考</h2><span class="muted">不是预测</span></div>
      <div class="feature-grid">
        <div class="feature"><strong>参考组合</strong><p>{html.escape('　'.join(parts))}</p><small>依据：历史频率观察。</small></div>
        <div class="feature"><strong>使用建议</strong><p class="muted">适合做数据观察和娱乐参考，不建议过度投入。</p></div>
        <div class="feature"><strong>风险提示</strong><p class="muted">彩票开奖结果具有随机性，历史频率不能推出未来开奖号码。</p></div>
      </div>
    </section>
    """


def detail_script() -> str:
    return r"""
    let lastBatchRows = [];
    const parseNums = value => (value || "").replace(/，/g, " ").replace(/,/g, " ").replace(/\+/g, " + ").trim().split(/\s+/).filter(Boolean).filter(item => item !== "+").map(Number);
    const fmt = value => String(value).padStart(2, "0");
    function groupsFromDraw(draw) {
      if (!draw) return [[], []];
      if (GAME.id === "ssq") return [parseNums(draw.Red), parseNums(draw.Blue)];
      if (GAME.id === "dlt") return [parseNums(draw.Front), parseNums(draw.Back)];
      if (GAME.id === "qlc") return [parseNums(draw.Main), parseNums(draw.Special)];
      return [parseNums(draw.Digit)];
    }
    function validateTicket(mainNums, specialNums) {
      const main = GAME.areas[0], special = GAME.areas[1];
      if (mainNums.length !== main.count) return `${main.label}需要${main.count}个号码。`;
      if (special && specialNums.length !== special.count) return `${special.label}需要${special.count}个号码。`;
      if (!special && specialNums.length) return "这个彩种没有二区号码，第二栏请留空。";
      if (main.unique && new Set(mainNums).size !== mainNums.length) return `${main.label}不能重复。`;
      if (special && special.unique && new Set(specialNums).size !== specialNums.length) return `${special.label}不能重复。`;
      if (mainNums.some(value => value < main.min_number || value > main.max_number)) return `${main.label}超出范围。`;
      if (special && specialNums.some(value => value < special.min_number || value > special.max_number)) return `${special.label}超出范围。`;
      return "";
    }
    function checkSsq(redHits, blueHits) {
      if (redHits === 6 && blueHits === 1) return "一等奖";
      if (redHits === 6) return "二等奖";
      if (redHits === 5 && blueHits === 1) return "三等奖";
      if (redHits === 5 || (redHits === 4 && blueHits === 1)) return "四等奖";
      if ((redHits === 4) || (redHits === 3 && blueHits === 1)) return "五等奖";
      if (blueHits === 1) return "六等奖";
      return "未中奖";
    }
    function checkDlt(frontHits, backHits) {
      if (frontHits === 5 && backHits === 2) return "一等奖";
      if (frontHits === 5 && backHits === 1) return "二等奖";
      if (frontHits === 5) return "三等奖";
      if (frontHits === 4 && backHits === 2) return "四等奖";
      if (frontHits === 4 && backHits === 1) return "五等奖";
      if (frontHits === 3 && backHits === 2) return "六等奖";
      if (frontHits === 4) return "七等奖";
      if ((frontHits === 3 && backHits === 1) || (frontHits === 2 && backHits === 2)) return "八等奖";
      if ((frontHits === 3) || (frontHits === 2 && backHits === 1) || (frontHits === 1 && backHits === 2) || (frontHits === 0 && backHits === 2)) return "九等奖";
      return "未中奖";
    }
    function checkQlc(mainHits, specialHits) {
      if (mainHits === 7 && specialHits === 1) return "一等奖";
      if (mainHits === 7) return "二等奖";
      if (mainHits === 6 && specialHits === 1) return "三等奖";
      if (mainHits === 6) return "四等奖";
      if (mainHits === 5 && specialHits === 1) return "五等奖";
      if ((mainHits === 5) || (mainHits === 4 && specialHits === 1)) return "六等奖";
      if (mainHits === 4) return "七等奖";
      return "未中奖";
    }
    function checkTicket(mainNums, specialNums) {
      const drawGroups = groupsFromDraw(GAME.latest);
      if (GAME.areas.length === 1) {
        const exact = drawGroups[0].length === mainNums.length && drawGroups[0].every((value, index) => value === mainNums[index]);
        const orderedHits = mainNums.filter((value, index) => drawGroups[0][index] === value).length;
        if (exact) return { level: GAME.id === "fc3d" || GAME.id === "pl3" ? "直选命中" : "命中开奖号码", mainHits: orderedHits, specialHits: 0 };
        if ((GAME.id === "fc3d" || GAME.id === "pl3") && [...drawGroups[0]].sort().join(",") === [...mainNums].sort().join(",")) return { level:"组选参考命中", mainHits: orderedHits, specialHits: 0 };
        return { level:"未中奖", mainHits: orderedHits, specialHits: 0 };
      }
      const mainHits = mainNums.filter(value => drawGroups[0].includes(value)).length;
      const specialHits = specialNums.filter(value => drawGroups[1].includes(value)).length;
      const level = GAME.id === "ssq" ? checkSsq(mainHits, specialHits) : GAME.id === "dlt" ? checkDlt(mainHits, specialHits) : checkQlc(mainHits, specialHits);
      return { level, mainHits, specialHits };
    }
    function runSingleCheck() {
      const mainNums = parseNums(document.getElementById("mainNumbers").value);
      const specialNums = parseNums(document.getElementById("specialNumbers").value);
      const error = validateTicket(mainNums, specialNums);
      if (error) { document.getElementById("checkResult").textContent = error; return; }
      const result = checkTicket(mainNums, specialNums);
      document.getElementById("checkResult").textContent = `${GAME.name} ${GAME.latest.Issue}期：${result.level}\n一区/开奖号码命中 ${result.mainHits} 个${GAME.areas[1] ? `，二区命中 ${result.specialHits} 个` : ""}。\n提示：核验结果仅供参考，最终以官方兑奖规则为准。`;
    }
    function parseBatchLine(line) {
      const parts = line.split("+");
      if (parts.length === 2) return [parseNums(parts[0]), parseNums(parts[1])];
      const nums = parseNums(line);
      const mainCount = GAME.areas[0].count;
      return [nums.slice(0, mainCount), nums.slice(mainCount)];
    }
    function runBatchCheck() {
      const lines = document.getElementById("batchNumbers").value.split(/\n+/).map(line => line.trim()).filter(Boolean);
      if (!lines.length) { document.getElementById("checkResult").textContent = "请先粘贴要批量核验的号码。"; return; }
      lastBatchRows = [];
      const output = lines.map((line, index) => {
        const [mainNums, specialNums] = parseBatchLine(line);
        const error = validateTicket(mainNums, specialNums);
        if (error) {
          lastBatchRows.push([index + 1, line, "格式错误", error]);
          return `${index + 1}. 格式错误：${error}`;
        }
        const result = checkTicket(mainNums, specialNums);
        const hitText = GAME.areas[1] ? `一区${result.mainHits} 二区${result.specialHits}` : `按位命中${result.mainHits}`;
        lastBatchRows.push([index + 1, line, result.level, hitText]);
        return `${index + 1}. ${result.level}（${hitText}）`;
      });
      document.getElementById("checkResult").textContent = output.join("\n");
    }
    function fillExample() {
      const groups = groupsFromDraw(GAME.latest);
      document.getElementById("mainNumbers").value = groups[0].map(fmt).join(" ");
      document.getElementById("specialNumbers").value = groups[1] ? groups[1].map(fmt).join(" ") : "";
      document.getElementById("batchNumbers").value = groups[1] ? `${groups[0].map(fmt).join(" ")} + ${groups[1].map(fmt).join(" ")}` : groups[0].map(fmt).join(" ");
      document.getElementById("checkResult").textContent = "已填入最新开奖号作为示例。";
    }
    function exportCsv() {
      if (!lastBatchRows.length) runBatchCheck();
      if (!lastBatchRows.length) return;
      const csv = "序号,号码,结果,命中\n" + lastBatchRows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n");
      const blob = new Blob(["\ufeff" + csv], { type:"text/csv;charset=utf-8" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${GAME.name}批量核验.csv`;
      link.click();
      URL.revokeObjectURL(link.href);
    }
    document.getElementById("checkSingle").addEventListener("click", runSingleCheck);
    document.getElementById("checkBatch").addEventListener("click", runBatchCheck);
    document.getElementById("exportCsv").addEventListener("click", exportCsv);
    document.getElementById("fillExample").addEventListener("click", fillExample);
    document.getElementById("clearResult").addEventListener("click", () => {
      document.getElementById("mainNumbers").value = "";
      document.getElementById("specialNumbers").value = "";
      document.getElementById("batchNumbers").value = "";
      document.getElementById("checkResult").textContent = "已清空。";
      lastBatchRows = [];
    });
    function applyYearFilter() {
      const select = document.getElementById("yearSelect");
      const summary = document.getElementById("yearSummary");
      if (!select) return;
      const year = select.value;
      let count = 0;
      document.querySelectorAll("#history tbody tr").forEach(row => {
        const visible = year === "all" || row.dataset.year === year;
        row.style.display = visible ? "" : "none";
        if (visible) count += 1;
      });
      if (summary) summary.textContent = year === "all" ? `当前显示全部年份，共 ${count} 期` : `当前显示 ${year} 年，共 ${count} 期`;
    }
    const yearSelect = document.getElementById("yearSelect");
    if (yearSelect) {
      yearSelect.addEventListener("change", applyYearFilter);
      applyYearFilter();
    }
    """


def page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>
  <div class="page">{body}</div>
</body>
</html>
"""


STYLE = r"""
:root{--page:#f5f7fb;--card:#fff;--ink:#1f2937;--muted:#667085;--line:#e4e7ec;--warm:#f26b35;--warm-mid:#ff9a4d;--warm-soft:#ffd5c2;--cool:#2f8fe8;--cool-mid:#6ab5ff;--cool-soft:#d9ecff;--neutral:#d9e0ea;--green:#14835b;--shadow:0 20px 48px rgba(31,41,55,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.6}a{color:inherit;text-decoration:none}button,input,textarea,select{font:inherit}.page{max-width:1240px;margin:0 auto;padding:24px}.home-hero{display:grid;grid-template-columns:1.05fr .95fr;gap:16px}.hero-main,.panel,.sync-panel{background:var(--card);border:1px solid var(--line);border-radius:26px;padding:20px;box-shadow:var(--shadow)}.hero-main{background:linear-gradient(135deg,#fff3ec,#eef6ff)}.hero-title,.panel-title,.detail-title,.lottery-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap}h1{margin:0 0 8px;font-size:36px;letter-spacing:-.04em}h2,h3,p{margin:0}.muted,small{color:var(--muted)}.badge,.nav-pill{border:1px solid var(--line);border-radius:999px;padding:7px 12px;background:#f8fafc}.ok{color:var(--green);font-weight:700}.search-row{display:grid;grid-template-columns:1fr auto;gap:10px;margin-top:18px}input,textarea,select{width:100%;border:1px solid var(--line);border-radius:16px;padding:12px 14px;background:#fff;color:var(--ink)}textarea{min-height:112px;resize:vertical}.btn{border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:999px;padding:10px 16px;cursor:pointer}.btn.primary{background:var(--ink);color:#fff;border-color:var(--ink)}.status-list{display:grid;gap:10px;margin-top:12px}.status-row{display:flex;justify-content:space-between;gap:14px;border-bottom:1px dashed var(--line);padding-bottom:9px}.status-row:last-child{border-bottom:0}.source-row{margin-top:10px}.lottery-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:12px;margin:18px 0}.lottery-card{min-height:164px;display:grid;gap:9px;text-align:left;border:1px solid var(--line);border-radius:22px;padding:14px;background:#fff;transition:.16s ease}.lottery-card:hover{transform:translateY(-2px);border-color:#98a2b3}.lottery-card strong{font-size:18px}.lottery-card small{white-space:nowrap}.lottery-meta{color:var(--muted);font-size:13px;border-top:1px dashed var(--line);padding-top:8px}.balls{display:flex;flex-wrap:wrap;gap:5px;align-items:center}.ball,.mini-ball{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;font-weight:700;font-variant-numeric:tabular-nums}.ball{width:32px;height:32px}.mini-ball{width:30px;height:30px}.warm{background:linear-gradient(145deg,var(--warm-mid),var(--warm));color:#fff8f2}.cool{background:linear-gradient(145deg,var(--cool-mid),var(--cool));color:#eef7ff}.neutral{background:linear-gradient(145deg,#eef1f6,var(--neutral));color:#344054}.notice{border:1px solid #f0d7ad;border-radius:20px;padding:16px;background:#fff8ed}.detail-hero{display:grid;gap:14px;margin-bottom:16px}.back-link{color:var(--muted)}.nav-row{display:flex;flex-wrap:wrap;gap:8px}.nav-pill.active{background:var(--ink);color:#fff;border-color:var(--ink)}.detail-layout{display:grid;grid-template-columns:300px 1fr;gap:16px;align-items:start}.left-panel,.right-panel{display:grid;gap:16px}.latest-balls{margin:12px 0}.quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.quick-grid a{border:1px solid var(--line);border-radius:14px;padding:10px;text-align:center;background:#fbfcff}.summary-grid,.feature-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.summary-card,.feature,.mini-panel{border:1px solid var(--line);border-radius:18px;padding:14px;background:#fbfcff}.summary-card strong{display:block;font-size:26px}.summary-card span{color:var(--muted)}.summary-text{margin-top:12px}.checker-help,.trend-note{border:1px solid var(--line);border-radius:18px;padding:14px;background:#fbfcff;margin-bottom:14px}.checker-help p,.trend-note p{margin-top:6px}.trend-metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:0 0 10px}.trend-metrics div{border:1px solid var(--line);border-radius:16px;padding:10px 12px;background:#fff}.trend-metrics strong{display:block;font-size:22px}.trend-metrics span{color:var(--muted);font-size:13px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.batch-label{display:block;margin-top:14px}.result{margin-top:12px;border:1px solid var(--line);border-radius:16px;padding:12px;background:#f8fafc;white-space:pre-wrap}.freq-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.freq-list{display:grid;gap:8px;margin-top:12px}.freq-row{display:grid;grid-template-columns:36px 1fr 58px 36px;gap:8px;align-items:center}.track{height:10px;border-radius:999px;background:#edf0f5;overflow:hidden}.fill{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--warm-soft),var(--warm))}.cool-fill{background:linear-gradient(90deg,var(--cool-soft),var(--cool))}.trend-svg{width:100%;height:auto;display:block}.grid-line{stroke:#e4e7ec;stroke-width:1}.axis{fill:#667085;font-size:12px}.trend-line{fill:none;stroke:var(--warm);stroke-width:3}.trend-dot{fill:var(--cool)}.avg-line{stroke:#98a2b3;stroke-dasharray:6 6}.year-tools{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:0 0 12px}.year-tools label{display:flex;align-items:center;gap:8px}.year-tools select{width:auto;min-width:130px}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid var(--line);padding:10px 8px;text-align:left;vertical-align:middle}th{color:var(--muted)}
@media(max-width:1100px){.home-hero,.detail-layout{grid-template-columns:1fr}.lottery-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.trend-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:720px){.page{padding:14px}h1{font-size:28px}.lottery-grid,.summary-grid,.feature-grid,.freq-grid,.form-grid,.search-row,.trend-metrics{grid-template-columns:1fr}}
"""


def main() -> None:
    payload = all_payload()
    HOME_FILE.write_text(render_home(payload), encoding="utf-8")
    (ROOT / "index.html").write_text(render_home(payload), encoding="utf-8")
    for lottery_id in PAGE_IDS:
        (ROOT / f"{lottery_id}.html").write_text(render_detail(lottery_id, payload), encoding="utf-8")
    print(f"Generated home and {len(PAGE_IDS)} detail pages in {ROOT}")


if __name__ == "__main__":
    main()
