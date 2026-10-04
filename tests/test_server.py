# -*- coding: utf-8 -*-
"""tgtc-mcp-server 测试：mock SDK 客户端，验证 9 工具调用 + 统一输出尾巴 + 无 Key 提示。

运行：python -m pytest tests/ -v（或 python tests/test_server.py）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from types import SimpleNamespace
from unittest.mock import patch

from tgtc import Result

import tgtc_mcp_server.core as core
import tgtc_mcp_server.server as srv


def _fake_result(data):
    return Result(data=data, remaining="9800", used="1", cache_hit=False)


def _fake_client():
    """假 SDK 客户端：9 个方法各返回接近真实结构的组装卡数据。"""
    return SimpleNamespace(
        token=lambda ca, **k: _fake_result({
            "symbol": "TEST", "name": "Test Token", "price": 0.0012,
            "mcap": 1200000, "liquidity": 340000, "honeypot": False,
            "mint_renounced": True, "lp_burned_ratio": 0.5, "buy_tax": 5,
            "sell_tax": 5, "holder_count": 1234, "top10_holder_pct": 0.45,
            "traders": {"smart_buy": 5, "smart_sell": 2}}),
        trending=lambda **k: _fake_result({"items": [
            {"symbol": "AAA", "price": 0.01, "mcap": 500000},
            {"symbol": "BBB", "price": 0.02, "mcap": 800000}]}),
        hot=lambda **k: _fake_result({"items": [
            {"symbol": "CCC", "price": 0.03, "mcap": 300000}]}),
        trades=lambda **k: _fake_result({"items": [
            {"side": "buy", "symbol": "DDD", "price": 0.001, "amount_usd": 12000}]}),
        signals=lambda **k: _fake_result({"items": [
            {"signal_name": "新币异动", "symbol": "EEE", "trigger_mcap": 400000}]}),
        wallet=lambda *a, **k: _fake_result({
            "wallet": "0x1234567890abcdef1234567890abcdef12345678",
            "period": "7d", "pnl_7d": 1234.5, "win_rate": 0.6, "trade_count": 88}),
        twitter=lambda *a, **k: _fake_result({
            "username": "elon", "name": "Elon", "followers": 100,
            "following": 20, "tweets_count": 500, "blue_verified": True,
            "description": "CEO"}),
        sentiment=lambda ca, **k: _fake_result({
            "ca": ca, "tweets_count": 12, "total_views": 5000,
            "max_views": 3000,
            "ai_text": "热度评级：中。理由：提及量达 12 条且总阅读 5000。"}),
        translate=lambda *a, **k: _fake_result({"text": "你好，世界"}),
    )


def _client_of(fn):
    """把 fake client 注入 core._get_client 后调用工具函数。"""
    with patch.object(core, "_get_client", return_value=_fake_client()):
        return fn()


def test_all_nine_tools():
    """9 个工具都能调用并返回组装卡 + 计费尾巴。"""
    calls = [
        ("tgtc_token", dict(ca="0x" + "a" * 40), "TEST"),
        ("tgtc_trending", dict(kind="launch"), "榜单"),
        ("tgtc_hot", dict(interval="5m"), "热门"),
        ("tgtc_trades", dict(actor="kol", side="buy"), "交易流"),
        ("tgtc_signals", dict(signal_types=[20]), "信号"),
        ("tgtc_wallet", dict(action="profile", wallet="0x" + "b" * 40), "钱包"),
        ("tgtc_twitter", dict(action="user.info", username="elon"), "推特"),
        ("tgtc_sentiment", dict(ca="0x" + "a" * 40), "舆情"),
        ("tgtc_translate", dict(action="translate", text="hello"), "你好"),
    ]
    for name, kwargs, marker in calls:
        fn = getattr(srv, name)
        with patch.object(core, "_get_client", return_value=_fake_client()):
            text = fn(**kwargs)
        assert marker in text, (name, text[:120])
        assert "remaining=9800" in text, (name, "缺计费尾巴")
        assert "used=1" in text, (name, "缺扣次")
        assert "非投资建议" in text, (name, "缺免责")
        assert text.count("\n· ") >= 1, (name, "缺组装行")
        print(f"PASS {name}")
    print(f"PASS all 9 tools (组装卡 + 尾巴)")


def test_token_card_fields():
    """组装卡应含关键指标（价格/市值/安全/持有人/聪明钱），且不丢免责语义。"""
    with patch.object(core, "_get_client", return_value=_fake_client()):
        text = srv.tgtc_token(ca="0x" + "a" * 40)
    for frag in ("$1.20M", "$340K", "非貔貅", "铸币已放弃", "持有人 1234",
                 "聪明钱 24h：买入 5 钱包 / 卖出 2 钱包", "静态检查"):
        assert frag in text, (frag, text)
    print("PASS token card fields")


def test_list_tools_count():
    """MCP server 注册了 9 个工具。"""
    import asyncio
    tools = asyncio.run(srv.server.list_tools())
    names = [t.name for t in tools]
    assert len(names) == 9, names
    expect = {"tgtc_token", "tgtc_trending", "tgtc_hot", "tgtc_trades",
              "tgtc_signals", "tgtc_wallet", "tgtc_twitter",
              "tgtc_sentiment", "tgtc_translate"}
    assert set(names) == expect, set(names) ^ expect
    # 每个工具 description 非空（AI 精确路由的前提）
    for t in tools:
        assert t.description and len(t.description) > 30, (t.name, "description 太短")
    print(f"PASS registered 9 tools with rich descriptions")


def test_no_key_friendly_error():
    """未配置 Key：工具应给出友好引导而非裸异常。"""
    env_backup = dict(os.environ)
    os.environ.pop("TGTC_API_KEY", None)
    os.environ.pop("API_KEY", None)
    try:
        core._client = None  # 重置单例
        try:
            core._get_client()
        except Exception as e:
            msg = str(e)
            assert "TGTC_API_KEY" in msg and "tgtcbot.com" in msg, msg
        else:
            raise AssertionError("无 Key 应报错")
    finally:
        os.environ.clear()
        os.environ.update(env_backup)
        core._client = None
    print("PASS no-key friendly guidance")


def test_dump_truncation():
    """超长数据截断并提示 fields。"""
    big = {"data": "x" * 9000}
    out = core._dump(big)
    assert "已截断" in out and "fields" in out
    assert len(out) < 4500
    print("PASS dump truncation")


if __name__ == "__main__":
    test_all_nine_tools()
    test_token_card_fields()
    test_list_tools_count()
    test_no_key_friendly_error()
    test_dump_truncation()
    print("ALL_TESTS_PASSED")
