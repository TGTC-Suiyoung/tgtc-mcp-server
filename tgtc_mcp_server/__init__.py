# -*- coding: utf-8 -*-
"""tgtc-mcp-server：TGTC 数据 API 的 MCP Server（完整 9 工具版）。

让 Claude / Cursor 在对话里直接查 BSC 代币：链上安全 / 行情 / 持仓 / 聪明钱 /
钱包 / 推特 / 舆情 / 翻译——SDK 有什么能力，AI 就有什么能力。
每个工具返回「组装卡」：关键字段精选 + 格式化 + 计费透明尾巴。
"""

from .core import _card, _dump, _get_client

__version__ = "0.1.5"
__all__ = ["_card", "_dump", "_get_client", "__version__"]
