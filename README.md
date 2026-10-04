# tgtc-mcp-server

**让 AI 一句话查 BSC 代币数据。**

在 AI 客户端里直接查 BSC 链上安全 / 行情 / 持仓 / 聪明钱 / 钱包 / 推特舆情 / 翻译——SDK 有什么能力，AI 就有什么能力（完整 9 工具版）。

## 为什么用 MCP

MCP（Model Context Protocol）是 AI 领域的通用接入标准——**一次接入，所有支持本地 MCP 的 AI 客户端都能用你的数据**：Claude Desktop、Cursor、Qoder CN 等，不需要为每个 AI 单独写集成。开发者装好之后，在对话里说一句「查一下这个 CA」，AI 自己决定调用你的工具、拿真实数据回答。

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

每个工具的参数、可选值、限制条件都写在工具描述里——AI 能精确理解「查什么、怎么查、有什么约束」。

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
[TGTC] remaining=9800 used=1 cache_hit=false · 不是投资建议 · Key: tgtcbot.com
```

- 缓存命中不扣次
- 参数错误（422）不扣次
- 每次调用按你的 Key 扣次，消耗的是你自己的次数

## 安全

- 本地 stdio 模式，不暴露任何远程端口
- Key 只存在于你自己的环境变量，不进代码、不进日志
- 每个工具按你 Key 的扣次模型计费

## 开发

```bash
python -m pytest tests/ -v
```

## 相关

- Python SDK：[tgtc-sdk-python](https://github.com/TGTC-Suiyoung/tgtc-sdk-python)
- 开发者文档：[tgtc-api-docs](https://github.com/TGTC-Suiyoung/tgtc-api-docs)
- 官网：https://www.tgtcbot.com
