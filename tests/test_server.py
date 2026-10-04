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
    """假 SDK 客户端：9 个方法各返回一个带标识的数据体。"""
    return SimpleNamespace(
        token=lambda ca, **k: _fake_result({"symbol": "TEST", "price": 0.1, **k}),
        trending=lambda **k: _fake_result({"items": [{"symbol": "A", **k}]}),
        hot=lambda **k: _fake_result({"items": [{"symbol": "B", **k}]}),
        trades=lambda **k: _fake_result({"items": [{"token": "0x1", **k}]}),
        signals=lambda **k: _fake_result({"items": [{"type": 20, **k}]}),
        wallet=lambda *a, **k: _fake_result({"wallet": a[1] if len(a) > 1 else "0x", **k}),
        twitter=lambda *a, **k: _fake_result({"username": "elon", **k}),
        sentiment=lambda ca, **k: _fake_result({"heat_tier": "低", **k}),
        translate=lambda *a, **k: _fake_result({"text": "你好", **k}),
    )


def _client_of(fn):
    """把 fake client 注入 core._get_client 后调用工具函数。"""
    with patch.object(core, "_get_client", return_value=_fake_client()):
        return fn()


def test_all_nine_tools():
    """9 个工具都能调用并返回数据 + 计费尾巴。"""
    calls = [
        (_client_of, "tgtc_token", dict(ca="0x" + "a" * 40), "symbol"),
        (_client_of, "tgtc_trending", dict(kind="launch"), "items"),
        (_client_of, "tgtc_hot", dict(interval="5m"), "items"),
        (_client_of, "tgtc_trades", dict(actor="kol", side="buy"), "items"),
        (_client_of, "tgtc_signals", dict(signal_types=[20]), "items"),
        (_client_of, "tgtc_wallet", dict(action="profile", wallet="0x" + "b" * 40), "wallet"),
        (_client_of, "tgtc_twitter", dict(action="user.info", username="elon"), "username"),
        (_client_of, "tgtc_sentiment", dict(ca="0x" + "a" * 40), "heat_tier"),
        (_client_of, "tgtc_translate", dict(action="translate", text="hello"), "text"),
    ]
    for setup, name, kwargs, marker in calls:
        fn = getattr(srv, name)
        with patch.object(core, "_get_client", return_value=_fake_client()):
            text = fn(**kwargs)
        assert marker in text, (name, text[:100])
        assert "remaining=9800" in text, (name, "缺计费尾巴")
        assert "used=1" in text, (name, "缺扣次")
        assert "不是投资建议" in text, (name, "缺免责")
        print(f"PASS {name}")
    print(f"PASS all 9 tools (尾巴: remaining/used/免责)")


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
    test_list_tools_count()
    test_no_key_friendly_error()
    test_dump_truncation()
    print("ALL_TESTS_PASSED")
