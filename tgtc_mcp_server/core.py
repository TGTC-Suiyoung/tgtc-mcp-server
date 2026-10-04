# -*- coding: utf-8 -*-
"""核心逻辑：TGTC SDK 客户端管理 + 统一文本输出（与 MCP 框架解耦，便于测试）。

每个工具最终返回一段「组装卡」给 AI：关键字段精选 + 格式化 + 计费尾巴。
组装卡原则：
  · 精选 + 格式化，不替 AI 下结论（安全字段保留「静态检查」语义）
  · 计费透明——剩余次数/本次扣次/缓存命中 + 免责 + 官网，AI 会带进回答
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from tgtc import TGTC, TGTCError, Result

# 计费尾巴模板（所有工具统一）
_FOOTER = "\n[TGTC] remaining={remaining} used={used} cache_hit={cache_hit} · 非投资建议 · tgtcbot.com"

_client: Optional[TGTC] = None


def _get_client() -> TGTC:
    """懒加载 SDK 客户端（Key 从环境变量 TGTC_API_KEY 读取，未配置给友好提示）。"""
    global _client
    if _client is None:
        key = os.environ.get("TGTC_API_KEY") or os.environ.get("API_KEY") or ""
        if not key:
            raise TGTCError(
                "未配置 API Key：请在环境变量 TGTC_API_KEY 填入你的 Key "
                "（tgtcbot.com 免费领取试用次数）")
        _client = TGTC(api_key=key)
    return _client


def _dump(data: dict, cap: int = 4000) -> str:
    """JSON 序列化；超长截断，提示 AI 用 fields 缩小范围（防返回文本过大）。"""
    text = json.dumps(data, ensure_ascii=False, default=str)
    if len(text) > cap:
        text = text[:cap] + "…（数据过长已截断，可用 fields 参数缩小范围）"
    return text


# ══════════════════════════════════════════════════════════════
#  组装卡基础工具
# ══════════════════════════════════════════════════════════════

def _pick(data: dict, *keys, default=None):
    """取第一个非 None 的键值（兼容字段名与缺值 null）。"""
    for k in keys:
        v = data.get(k)
        if v is not None:
            return v
    return default


def _fmt_money(v) -> str:
    """金额格式化：$1.2M / $340K / $0.0012 / $0.00000453（极低价十进制，不用科学计数）。"""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v) if v is not None else "?"
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.2f}M"
    if v >= 1e3:
        x = v / 1e3
        return f"${x:.0f}K" if x == int(x) else f"${x:.1f}K"
    if v and v < 0.01:
        return f"${f'{v:.10f}'.rstrip('0').rstrip('.')}"
    return f"${v:.4g}"


def _fmt_pct(v, signed: bool = True) -> str:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v) if v is not None else "?"
    if signed:
        return f"{v:+.1f}%"
    return f"{v:.1f}%"


def _zh_bool(v) -> str:
    """安全/状态字段 → 中文（兼容 yes/no/1/0/true/false）。"""
    if v is None:
        return "?"
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, (int, float)):
        return "是" if v else "否"
    s = str(v).strip().lower()
    return "是" if s in ("yes", "true", "1", "y") else "否"


def _card(title: str, rows: list, res: Result) -> str:
    """组装卡：标题 + 行 + 计费尾巴。"""
    body = "\n".join(f"· {r}" for r in rows if r)
    out = f"{title}\n{body}" if body else title
    out += _FOOTER.format(remaining=res.remaining, used=res.used,
                          cache_hit=res.cache_hit)
    return out


def _items_of(data: dict) -> list:
    items = data.get("items")
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []


# ══════════════════════════════════════════════════════════════
#  9 工具组装卡
# ══════════════════════════════════════════════════════════════

def compose_token(res: Result) -> str:
    """代币聚合：行情 + 安全 + 持仓 + 聪明钱 精选卡。"""
    d = res.data
    rows = []
    sym = _pick(d, "symbol") or "?"
    name = _pick(d, "name")
    price = _fmt_money(_pick(d, "price"))
    chg = _fmt_pct(_pick(d, "chg_24h_pct", "chg_1h_pct"))
    head = f"{sym} {name or ''} · 价格 {price}（24h {chg}）"
    mcap = _fmt_money(_pick(d, "mcap"))
    liq = _fmt_money(_pick(d, "liquidity", "pool_liquidity"))
    rows.append(f"{head} | 市值 {mcap} | 流动性 {liq}")
    # 安全审计（静态检查语义）
    sec = []
    hp = _pick(d, "honeypot")
    mr = _pick(d, "mint_renounced", "renounced")
    lp = _pick(d, "lp_burned_ratio")
    bt = _pick(d, "buy_tax")
    st = _pick(d, "sell_tax")
    if hp is not None:
        sec.append(f"非貔貅" if hp in (False, 0, "no", "false", "No", "0") else "疑似貔貅")
    if mr is not None:
        sec.append("铸币已放弃" if _zh_bool(mr) == "是" else "铸币未放弃")
    if lp is not None:
        try:
            sec.append(f"LP 销毁 {float(lp):.0%}")
        except (TypeError, ValueError):
            sec.append(f"LP 销毁 {lp}")
    if bt is not None:
        sec.append(f"交易税 {bt}/{st or bt}")
    if sec:
        rows.append(f"安全（静态检查）：{' · '.join(sec)}")
    # 持仓结构
    hc = _pick(d, "holder_count")
    top = _pick(d, "top10_holder_pct")
    if hc is not None:
        t = f" · Top10 集中度 {float(top):.0%}" if top is not None else ""
        rows.append(f"持有人 {hc}{t}")
    # 聪明钱动向
    tr = d.get("traders") if isinstance(d.get("traders"), dict) else {}
    sb = tr.get("smart_buy")
    ss = tr.get("smart_sell")
    if sb is not None or ss is not None:
        rows.append(f"聪明钱 24h：买入 {sb or 0} 钱包 / 卖出 {ss or 0} 钱包")
    return _card("TGTC 代币快报", rows, res)


def compose_trending(res: Result) -> str:
    """榜单（新创建/新发射/即将毕业）→ 前 10 条精选。"""
    items = _items_of(res.data)
    rows = []
    for it in items[:10]:
        sym = _pick(it, "symbol") or "?"
        price = _fmt_money(_pick(it, "price"))
        mcap = _fmt_money(_pick(it, "mcap", "market_cap"))
        chg = _fmt_pct(_pick(it, "chg_24h_pct", "chg_1h_pct"))
        row = f"{sym} · {price} · 市值 {mcap}"
        if "?" not in chg:
            row += f" · 24h {chg}"
        rows.append(row)
    rows.append(f"共 {len(items)} 条，以上为前 {min(len(items), 10)} 条")
    return _card("TGTC 代币榜单", rows, res)


def compose_hot(res: Result) -> str:
    """热门搜索榜 → 前 10 条精选。"""
    items = _items_of(res.data)
    rows = []
    for it in items[:10]:
        sym = _pick(it, "symbol") or "?"
        price = _fmt_money(_pick(it, "price"))
        mcap = _fmt_money(_pick(it, "mcap", "market_cap"))
        chg = _fmt_pct(_pick(it, "chg_1h_pct", "chg_5m_pct"))
        row = f"{sym} · {price} · 市值 {mcap}"
        if "?" not in chg:
            row += f" · 1h {chg}"
        rows.append(row)
    rows.append(f"共 {len(items)} 条，以上为前 {min(len(items), 10)} 条")
    return _card("TGTC 热门搜索榜", rows, res)


def compose_trades(res: Result) -> str:
    """聪明钱/KOL 交易流 → 前 10 条精选。"""
    items = _items_of(res.data)
    rows = []
    for it in items[:10]:
        sym = _pick(it, "symbol") or _pick(it, "token") or "?"
        side = _pick(it, "side") or "?"
        price = _fmt_money(_pick(it, "price"))
        amt = _fmt_money(_pick(it, "amount_usd", "cost_usd"))
        rows.append(f"{side.upper()} {sym} @ {price}（{amt}）")
    rows.append(f"共 {len(items)} 条交易记录")
    return _card("TGTC 聪明钱交易流", rows, res)


def compose_signals(res: Result) -> str:
    """市场信号流 → 前 10 条精选。"""
    items = _items_of(res.data)
    rows = []
    for it in items[:10]:
        sname = _pick(it, "signal_name") or f"信号{_pick(it, 'signal_type')}"
        sym = _pick(it, "symbol") or "?"
        mcap = _fmt_money(_pick(it, "trigger_mcap", "mcap"))
        rows.append(f"{sname} · {sym} · 触发市值 {mcap}")
    rows.append(f"共 {len(items)} 条信号")
    return _card("TGTC 市场信号", rows, res)


def compose_wallet(res: Result, action: str) -> str:
    """钱包分析：地址 + 主要指标精选（按 action 输出通用卡）。"""
    d = res.data
    rows = []
    w = _pick(d, "wallet", "wallet_address")
    if w:
        short = str(w)[:10] + "…" + str(w)[-4:]
        rows.append(f"钱包 {short}（{_pick(d, 'period') or '7d'}）")
    # 取主要数值字段（非空、非钱包标识），最多 6 条
    skip = {"wallet", "wallet_address", "period", "action", "chain",
            "disclaimer", "data_delay_sec", "degraded_sources"}
    shown = 0
    for k, v in d.items():
        if k in skip or v is None or isinstance(v, (dict, list)):
            continue
        if isinstance(v, bool) or str(v).replace(".", "").replace("-", "").isdigit():
            if "profit" in k or "pnl" in k:
                v = _fmt_money(v)
            elif str(v).replace(".", "").replace("-", "").isdigit() and float(v) > 1000:
                v = _fmt_money(v)
            rows.append(f"{k}: {v}")
            shown += 1
            if shown >= 6:
                break
    if not rows:
        rows.append(f"action={action}，返回字段见原始数据")
    return _card("TGTC 钱包分析", rows, res)


def compose_twitter(res: Result, action: str) -> str:
    """推特检测：user.* 出账号卡；tweet.* 出推文卡。"""
    d = res.data
    items = _items_of(d)
    rows = []
    if action.startswith("user.") and not items and _pick(d, "username"):
        u = d
        rows.append(f"@{_pick(u, 'username')}（{_pick(u, 'name') or '?'}）")
        rows.append(f"粉丝 {_pick(u, 'followers') or 0} · 关注 {_pick(u, 'following') or 0}"
                    f" · 推文 {_pick(u, 'tweets_count') or 0} · 蓝V {'是' if _pick(u, 'blue_verified') else '否'}")
        desc = _pick(u, "description")
        if desc:
            rows.append(f"简介：{desc}")
    for it in items[:8]:
        text = str(_pick(it, "text") or "").strip()
        author = _pick(it, "username") or _pick(it, "userName") or ""
        views = _pick(it, "views", "view_count")
        if text:
            rows.append(f"{'@' + author + ' ' if author else ''}{text[:120]}"
                        f"{'（阅读 ' + str(views) + '）' if views is not None else ''}")
    rows.append(f"共 {len(items)} 条")
    return _card(f"TGTC 推特（{action}）", rows, res)


def compose_sentiment(res: Result) -> str:
    """CA 舆情：AI 解读 + 提及热度数据。"""
    d = res.data
    ai = str(d.get("ai_text") or "").strip()
    rows = []
    if ai:
        rows.append(ai[:800])
    rows.append(f"提及推文 {_pick(d, 'tweets_count') or 0} 条 · "
                f"总阅读 {_pick(d, 'total_views') or 0} · 最高单条 {_pick(d, 'max_views') or 0}")
    return _card("TGTC CA 舆情", rows, res)


def compose_translate(res: Result) -> str:
    """AI 翻译/摘要：直接输出结果文本。"""
    text = str(res.data.get("text") or "").strip()
    rows = [text] if text else ["（无输出）"]
    return _card("TGTC 翻译结果", rows, res)
