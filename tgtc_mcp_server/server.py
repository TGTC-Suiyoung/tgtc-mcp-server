# -*- coding: utf-8 -*-
"""tgtc-mcp-server：让 Claude / Cursor 一句话查 BSC 代币数据。

完整 9 工具版——SDK 有什么能力，AI 就有什么能力。
每个工具的 description 写清：查什么 / 参数含义 / 限制条件，AI 才能精确路由。

运行（stdio 本地模式）：
    uvx tgtc-mcp-server       # 需要 TGTC_API_KEY 环境变量
"""

from __future__ import annotations

import functools
from typing import Literal, List, Optional

from mcp.server.mcpserver import MCPServer

from . import core

server = MCPServer(
    name="tgtc-mcp-server",
    version="0.1.1",
    description="TGTC BSC 代币数据查询：链上安全/行情/持仓/聪明钱/推特舆情/翻译",
)

# 异常兜底尾巴（错误时无计费数字，给可行动的引导）
_ERR_FOOTER = "\n[TGTC] 不是投资建议 · 请检查 Key / 稍后重试 · tgtcbot.com"


def _safe(fn):
    """工具包装：异常 → 友好文本返回（不冒泡到 MCP 框架，跨版本稳定）。"""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return f"查询失败：{e}{_ERR_FOOTER}"

    return wrapper


# ══════════════════════════════════════════════════════════════
#  代币聚合
# ══════════════════════════════════════════════════════════════
@server.tool(
    name="tgtc_token",
    description=(
        "查一个 BSC 代币合约的完整链上情报：行情（价格/市值/涨跌）、持仓结构、"
        "安全审计（honeypot/权限/税率）、持有人、社交信息、聪明钱动向。"
        "参数 ca 必须是 0x 开头的 40 位十六进制合约地址；categories 可选值："
        "basic(行情)/structure(持仓)/holders(持有人)/security(安全)/social(社交)/traders(聪明钱)，"
        "缺省返回全部；categories 与 fields 互斥，二选一，fields 用于精确裁剪响应字段。"
        "安全字段是静态检查，不代表可卖出。"
    ),
)
@_safe
def tgtc_token(ca: str, chain: str = "bsc",
               categories: Optional[List[str]] = None,
               fields: Optional[List[str]] = None) -> str:
    res = core._get_client().token(ca, chain=chain,
                                   categories=categories, fields=fields)
    return core._answer(res)


# ══════════════════════════════════════════════════════════════
#  榜单
# ══════════════════════════════════════════════════════════════
@server.tool(
    name="tgtc_trending",
    description=(
        "BSC 代币榜单。kind 可选：new(新创建)/launch(新发射)/graduating(即将毕业)，"
        "默认 new；limit 1~100，默认 20。返回条目数组，可用于发现新币。"
        "支持 fields 参数精确裁剪响应字段（可选）。"
    ),
)
@_safe
def tgtc_trending(chain: str = "bsc",
                  kind: Literal["new", "launch", "graduating"] = "new",
                  limit: int = 20,
                  fields: Optional[List[str]] = None) -> str:
    res = core._get_client().trending(chain=chain, kind=kind,
                                      limit=limit, fields=fields)
    return core._answer(res)


@server.tool(
    name="tgtc_hot",
    description=(
        "BSC 热门搜索榜单。interval 可选：1m/5m/1h/6h/24h（统计区间），默认 1h；"
        "limit 1~100，默认 50。返回条目数组，可用于发现社区正在关注的项目。"
        "支持 fields 参数精确裁剪响应字段（可选）。"
    ),
)
@_safe
def tgtc_hot(chain: str = "bsc",
             interval: Literal["1m", "5m", "1h", "6h", "24h"] = "1h",
             limit: int = 50,
             fields: Optional[List[str]] = None) -> str:
    res = core._get_client().hot(chain=chain, interval=interval,
                                 limit=limit, fields=fields)
    return core._answer(res)


# ══════════════════════════════════════════════════════════════
#  交易流 / 信号流
# ══════════════════════════════════════════════════════════════
@server.tool(
    name="tgtc_trades",
    description=(
        "聪明钱 / KOL 实时交易流。actor 可选 smartmoney(聪明钱)/kol(KOL)，默认 smartmoney；"
        "side 可选 buy/sell 过滤方向；limit 1~200，默认 20（防烧次数，建议保持默认）。"
        "支持 fields 参数精确裁剪响应字段（可选）。"
    ),
)
@_safe
def tgtc_trades(chain: str = "bsc",
                actor: Literal["smartmoney", "kol"] = "smartmoney",
                side: Optional[Literal["buy", "sell"]] = None,
                limit: int = 20,
                fields: Optional[List[str]] = None) -> str:
    res = core._get_client().trades(chain=chain, actor=actor, side=side,
                                    limit=limit, fields=fields)
    return core._answer(res)


@server.tool(
    name="tgtc_signals",
    description=(
        "BSC 市场信号流：新币异动/聪明钱行为等信号，缺省返回全部支持类型。"
        "signal_types 可选传数字 ID 列表（如 [20]）缩小范围；limit 1~200，默认 20。"
        "每条信号带触发时刻快照。支持 fields 参数精确裁剪响应字段（可选）。"
    ),
)
@_safe
def tgtc_signals(chain: str = "bsc",
                 signal_types: Optional[List[int]] = None,
                 limit: int = 20,
                 fields: Optional[List[str]] = None) -> str:
    res = core._get_client().signals(chain=chain, signal_types=signal_types,
                                     limit=limit, fields=fields)
    return core._answer(res)


# ══════════════════════════════════════════════════════════════
#  钱包
# ══════════════════════════════════════════════════════════════
@server.tool(
    name="tgtc_wallet",
    description=(
        "BSC 钱包分析。action 可选：profile(画像)/stats(统计)/profits(盈亏)/"
        "activity(活动记录，支持 cursor 翻页)/created(创建过的代币)/balance(持仓余额)。"
        "wallet 必须是 0x 开头的 40 位十六进制地址；period 可选 1d/7d/30d，默认 7d；"
        "action=balance 时必填 token（持仓代币地址）；limit 1~100，默认 10。"
        "支持 fields 参数精确裁剪响应字段（可选）。"
    ),
)
@_safe
def tgtc_wallet(action: Literal["profile", "stats", "profits", "activity", "created", "balance"],
                 wallet: str, chain: str = "bsc",
                 period: Literal["1d", "7d", "30d"] = "7d",
                 token: Optional[str] = None,
                 limit: int = 10,
                 cursor: Optional[str] = None,
                 fields: Optional[List[str]] = None) -> str:
    res = core._get_client().wallet(action, wallet, chain=chain, period=period,
                                    token=token, limit=limit, cursor=cursor,
                                    fields=fields)
    return core._answer(res)


# ══════════════════════════════════════════════════════════════
#  推特
# ══════════════════════════════════════════════════════════════
@server.tool(
    name="tgtc_twitter",
    description=(
        "X（推特）检测。action 可选：user.info(账号信息)/user.tweets(推文)/"
        "user.timeline(时间线)/user.followers(粉丝)/user.followings(关注)/"
        "user.search(按用户名搜索)/tweet.search(搜索推文)/tweet.detail(推文详情)/"
        "tweet.replies(回复)/tweet.quotes(引用)/tweet.retweets(转推)/tweet.thread(串)。"
        "参数规则：user.* 需 username 或 user_id；user.search/tweet.search 需 query；"
        "tweet.* 需 tweet_id（tweet.detail 也支持 tweet_ids 列表）；count 1~100。"
        "支持 fields 参数精确裁剪响应字段（可选）。"
    ),
)
@_safe
def tgtc_twitter(action: Literal[
        "user.info", "user.tweets", "user.timeline", "user.followers",
        "user.followings", "user.search", "tweet.search", "tweet.detail",
        "tweet.replies", "tweet.quotes", "tweet.retweets", "tweet.thread"],
        username: Optional[str] = None, user_id: Optional[str] = None,
        query: Optional[str] = None, count: Optional[int] = None,
        cursor: Optional[str] = None, tweet_id: Optional[str] = None,
        tweet_ids: Optional[List[str]] = None, include_replies: bool = False,
        sort: Optional[str] = None) -> str:
    res = core._get_client().twitter(action, username=username, user_id=user_id,
                                     query=query, count=count, cursor=cursor,
                                     tweet_id=tweet_id, tweet_ids=tweet_ids,
                                     include_replies=include_replies, sort=sort)
    return core._answer(res)


# ══════════════════════════════════════════════════════════════
#  CA 舆情
# ══════════════════════════════════════════════════════════════
@server.tool(
    name="tgtc_sentiment",
    description=(
        "BSC 代币合约的 X 舆情分析：热度评级（数据规则判定）+ AI 解读 + 提及推文数据。"
        "ca 必须是 0x 开头的 40 位十六进制合约地址。只描述讨论热度与情绪，不是投资建议。"
    ),
)
@_safe
def tgtc_sentiment(ca: str, chain: str = "bsc") -> str:
    res = core._get_client().sentiment(ca, chain=chain)
    return core._answer(res)


# ══════════════════════════════════════════════════════════════
#  翻译
# ══════════════════════════════════════════════════════════════
@server.tool(
    name="tgtc_translate",
    description=(
        "AI 翻译 / 长文本摘要（输出固定中文）。action 可选 translate(翻译)/summarize(摘要)；"
        "text 最长 2000 字符，超长会被拒绝且不扣次。"
    ),
)
@_safe
def tgtc_translate(action: Literal["translate", "summarize"], text: str) -> str:
    res = core._get_client().translate(action, text)
    return core._answer(res)


def main() -> None:
    """stdio 入口（Claude Desktop / Cursor 本地 MCP 配置用）。"""
    server.run()


if __name__ == "__main__":
    main()
