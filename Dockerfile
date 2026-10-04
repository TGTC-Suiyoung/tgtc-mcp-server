# tgtc-mcp-server hosted 远程版镜像
# 独立容器运行，内存上限由 compose 控制（mem_limit: 200m）
FROM python:3.11-slim

# 固定版本：避免 Docker 层缓存让容器停在旧版（pip install 不带版本 → 缓存命中永不更新）
RUN pip install --no-cache-dir tgtc-mcp-server==0.1.8 && \
    useradd --create-home --uid 10001 mcpuser

USER mcpuser

ENV TGTC_API_KEY="" \
    PORT=8765

EXPOSE 8765

# streamable-http 模式（默认 0.0.0.0:8765，/mcp 路径 + Bearer 鉴权）
CMD ["tgtc-mcp-server-http"]
