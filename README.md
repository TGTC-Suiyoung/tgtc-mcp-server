# tgtc-mcp-server

**让 Claude / Cursor 一句话查 BSC 代币数据。**

在 AI 客户端里直接查 BSC 链上安全 / 行情 / 持仓 / 聪明钱 / 钱包 / 推特舆情 / 翻译——SDK 有什么能力，AI 就有什么能力（完整 9 工具版）。

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
| `tgtc_translate` | AI 翻译 / 摘要 |

每次调用返回都带 **剩余次数 / 本次扣次 / 缓存命中**——计费透明，AI 会把它带进回答。

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

## 对话示例

> 用户：这个 0xbbc9...7777 能碰吗？

> AI（自动调用 `tgtc_token` + `tgtc_sentiment`）：链上安全审计显示未开源、税率 5%，X 舆情热度低、提及量不足…… 静态检查不代表可卖出。

## 安全

- 本地 stdio 模式，不暴露任何远程端口
- Key 只存在于你自己的环境变量，不进代码、不进日志
- 每个工具按你 Key 的扣次模型计费，消耗的是你自己的次数

## 开发

```bash
python -m pytest tests/ -v
```

## 相关

- Python SDK：[tgtc-sdk-python](https://github.com/TGTC-Suiyoung/tgtc-sdk-python)
- 开发者文档：[tgtc-api-docs](https://github.com/TGTC-Suiyoung/tgtc-api-docs)
- 官网：https://www.tgtcbot.com
