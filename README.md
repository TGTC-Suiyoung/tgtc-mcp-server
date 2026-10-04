# tgtc-mcp-server

**让 AI 一句话查 BSC 代币数据。**

在 AI 客户端里直接查 BSC 链上安全 / 行情 / 持仓 / 聪明钱 / 钱包 / 推特舆情 / 翻译——SDK 有什么能力，AI 就有什么能力（完整 9 工具版）。

> **Hosted 版已上线**：https://www.tgtcbot.com/mcp —— 所有支持 MCP 的 AI 客户端可直接配置接入（URL + Bearer）。

## 为什么用 MCP

MCP（Model Context Protocol）是 AI 领域的通用接入标准——**一次接入，所有支持 MCP 的 AI 客户端都能用你的数据**：Claude Desktop、Cursor、Qoder CN 以及网页版 AI（经 hosted URL）。开发者装好之后，在对话里说一句「查一下这个 CA」，AI 自己决定调用你的工具、拿真实数据回答。

## 它能做什么

| 工具 | 干什么 |
| --- | --- |
| `tgtc_token` | 代币完整情报：行情 / 持仓结构 / 安全审计 / 持有人 / 社交 / 聪明钱 |
| `tgtc_trending` | 新创建 / 新发射 / 即将毕业 榜单 |
| `tgtc_hot` | 热门搜索榜单 |
| `tgtc_trades` | 聪明钱 / KOL 实时交易流 |
| `tgtc_signals` | 市场信号流（新币异动 / 聪明钱行为） |
| `tgtc_wallet` | 钱包分析：画像 / 统计 / 盈亏 / 活动 / 创建 / 余额 |
| `tgtc_twitter` | X 检测：账号 / 推文 / 搜索 / 回复 / 引用 / 转推 / 串 |
| `tgtc_sentiment` | CA 舆情：热度评级 + AI 解读 + 提及数据 |
| `tgtc_translate` | AI 翻译 / 摘要（输出中文） |

## 组装卡输出

每个工具返回**组装卡**——关键字段精选 + 格式化 + 计费尾巴，AI 拿到直接引用，不用解析原始 JSON。示例（`tgtc_sentiment` 真实输出）：

```
TGTC CA 舆情
· 热度评级：中（提及20条，互动率1%）
一句话理由：提及20条，总阅读10617，互动率1%，显示中等热度。
舆情摘要：讨论BSC代币合约0xcb975f...，社区关注其涨跌，部分推文涉及拉票活动。
关键信号：
⚠ 风险/异常：互动率低，可能存在拉票或刷量行为。
📉 数据信号：阅读量与互动量不成比例，需关注真实用户参与度。
🧐 观察：话题集中度较高，多围绕代币涨跌和拉票活动。
· 提及推文 20 条 · 总阅读 10617 · 最高单条 1559
[TGTC] remaining=490 used=10 cache_hit=False · 非投资建议 · tgtcbot.com
```

## 参数速查表

| 工具 | 必填 | 关键参数（可选） | limit 范围 |
| --- | --- | --- | --- |
| `tgtc_token` | ca | categories（basic/structure/holders/security/social/traders），与 fields 互斥 | — |
| `tgtc_trending` | — | kind（new/launch/graduating） | 1~100，默认 20 |
| `tgtc_hot` | — | interval（1m/5m/1h/6h/24h） | 1~100，默认 50 |
| `tgtc_trades` | — | actor（smartmoney/kol）、side（buy/sell） | 1~200，默认 20 |
| `tgtc_signals` | — | signal_types（数字 ID 列表） | 1~200，默认 20 |
| `tgtc_wallet` | action + wallet | period（1d/7d/30d）；balance 需 token | 1~100，默认 10 |
| `tgtc_twitter` | action | user.* 需 username/user_id；search 需 query；tweet.* 需 tweet_id | count 1~100 |
| `tgtc_sentiment` | ca | — | — |
| `tgtc_translate` | action + text | text 最长 2000 字符 | — |

## 安装与配置

```bash
uvx tgtc-mcp-server
```

需要 API Key（[TGTC Bot](https://t.me/TG_TC_BOT) 免费领取试用次数），配置为环境变量 `TGTC_API_KEY`。

### Claude Desktop

`claude_desktop_config.json` 的 `mcpServers` 里加：

```json
{
  "mcpServers": {
    "tgtc": {
      "command": "uvx",
      "args": ["tgtc-mcp-server"],
      "env": { "TGTC_API_KEY": "你的 Key" }
    }
  }
}
```

### Cursor

全局 `~/.cursor/mcp.json` 或项目 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "tgtc": {
      "command": "uvx",
      "args": ["tgtc-mcp-server"],
      "env": { "TGTC_API_KEY": "你的 Key" }
    }
  }
}
```

Cursor Agent 模式自动识别，敏感调用会先请求确认。

### 其他支持本地 MCP 的 AI 客户端

同样方式接入：添加 MCP 服务时选 **STDIO 类型**，命令填 `uvx`，参数填 `tgtc-mcp-server`，环境变量填 `TGTC_API_KEY`。

## 远程 hosted 版（网页 AI 接入）

本地 stdio 只服务桌面 AI 客户端；要在网页版 AI 里使用，用 hosted 版（已上线）。在支持 MCP 的 AI 客户端里配置：

| 配置项 | 值 |
| --- | --- |
| URL / 服务器地址 | `https://www.tgtcbot.com/mcp` |
| 鉴权类型 | Bearer Token（或 API Key / 自定义 Header） |
| Token / Key | `sk_live_...`（你的 API Key） |

按上表配置后，对话框输 CA 即可触发查询（会话初始化由 AI 客户端自动处理）。

**自托管（可选）**：想部署自己的实例，用仓库里的 `Dockerfile` + `docker-compose.mcp.yml`（独立容器，内存上限 200M）：

```bash
docker compose -f docker-compose.mcp.yml up -d --build
```

- 端口只绑 `127.0.0.1`，公网流量走 nginx 反代（见 `nginx.mcp.conf`）
- **nginx 必须固定 Host**：`proxy_set_header Host 127.0.0.1:8765;`（mcp 2.x 校验 Host 头，透传真实域名会返回 Invalid Host header）
- **内置防护**：Bearer 门禁、会话上限 200 / 空闲 600s（防会话洪泛）、非 root 容器、nginx 限流 10r/s（`limit_req`）

## 对话示例

> **用户**：这个 0xbbc9...7777 能碰吗？

> **AI**（自动调用 `tgtc_token` + `tgtc_sentiment`）：链上安全审计显示合约未开源、交易税 5%，X 舆情热度偏低、提及量不足……静态检查不代表可卖出。

> **用户**：最近聪明钱在买什么 BSC 币？

> **AI**（自动调用 `tgtc_trades`）：最近 24h 聪明钱买入较多的代币：……（附剩余次数）

> **用户**：把这句英文推特翻译成中文

> **AI**（自动调用 `tgtc_translate`）：……

## 计费透明

每次调用返回都带剩余次数与本次扣次——AI 会把它带进回答，余额一眼可见：

```
[TGTC] remaining=9800 used=1 cache_hit=false · 非投资建议 · Key: tgtcbot.com
```

- 缓存命中不扣次
- 参数错误（422）不扣次
- 每次调用按你的 Key 扣次，消耗的是你自己的次数

## 故障排查

| 现象 | 原因 | 解法 |
| --- | --- | --- |
| `401 Unauthorized` | Bearer 缺失/错误，或服务端未配置 Key | 检查 `TGTC_API_KEY` 与请求头 `Authorization: Bearer <Key>` |
| `Missing session ID` | streamable-http 会话机制 | 先 `initialize` 拿 `Mcp-Session-Id`（AI 客户端自动处理） |
| `Invalid Host header` | mcp 2.x 校验 Host 头 | nginx 固定 `Host 127.0.0.1:8765`（自托管时） |
| `503` | nginx 限流超限（10r/s） | 正常防护，稍后重试 |
| `429` | Key 余额不足 | 充值后再试 |

## 安全

- 本地 stdio 不暴露任何端口；hosted 版 Bearer 门禁 + 会话限制 + 非 root 容器 + nginx 限流
- Key 只存在于环境变量，不进代码、不进日志
- 9 个工具全只读查询，无 shell/exec/文件操作

## 开发

```bash
python -m pytest tests/ -v
```

## 相关

- Python SDK：[tgtc-sdk-python](https://github.com/TGTC-Suiyoung/tgtc-sdk-python)
- 开发者文档：[tgtc-api-docs](https://github.com/TGTC-Suiyoung/tgtc-api-docs)
- 官网：https://www.tgtcbot.com
