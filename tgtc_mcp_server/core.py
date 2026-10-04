# -*- coding: utf-8 -*-
"""核心逻辑：TGTC SDK 客户端管理 + 统一文本输出（与 MCP 框架解耦，便于测试）。

每个工具最终返回一段文本给 AI：数据 JSON + 计费尾巴。
尾巴 = 剩余次数/本次扣次/缓存命中 + 免责 + 官网 —— AI 会把它带进回答，计费透明变成活广告。
"""

from __future__ import annotations

import json
import os
from typing import Optional

from tgtc import TGTC, TGTCError, Result

# 输出尾巴模板（所有工具统一）
_FOOTER = "\n[TGTC] remaining={remaining} used={used} cache_hit={cache_hit} · 不是投资建议 · Key: tgtcbot.com"

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


def _answer(res: Result, extra: Optional[dict] = None) -> str:
    """Result → 数据文本 + 计费尾巴。"""
    body = dict(res.data)
    if extra:
        body.update(extra)
    out = _dump(body)
    out += _FOOTER.format(remaining=res.remaining, used=res.used,
                          cache_hit=res.cache_hit)
    return out
