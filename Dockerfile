# Prometheus v3.0 - Docker镜像
# 使用多阶段构建减小镜像体积

# 第一阶段：构建环境
FROM python:3.11-slim AS builder

# 标签信息
LABEL maintainer="Prometheus Trading Bot Team"
LABEL version="3.0"
LABEL description="Quantitative trading bot for cryptocurrency markets"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升级pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 第二阶段：运行环境
FROM python:3.11-slim

# 设置时区
RUN apt-get update && apt-get install -y \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 创建非root用户
RUN groupadd -r prometheus && useradd -r -g prometheus prometheus

# 设置环境变量（通过docker-compose或docker run传入）
ENV OKX_API_KEY=""
ENV OKX_SECRET_KEY=""
ENV OKX_PASSPHRASE=""
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL="INFO"
ENV TZ="UTC"

# 创建日志目录并设置权限
RUN mkdir -p /app/trading_logs /app/logs && \
    chown -R prometheus:prometheus /app

# 复制项目文件
COPY --chown=prometheus:prometheus . .

# 切换到非root用户
USER prometheus

# 健康检查脚本
COPY --chown=prometheus:prometheus <<'EOF' /app/healthcheck.sh
#!/bin/bash
# 检查进程是否在运行
if pgrep -f "run_virtual_trading.py" > /dev/null; then
    exit 0
else
    exit 1
fi
EOF

RUN chmod +x /app/healthcheck.sh

# 配置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD ["/app/healthcheck.sh"]

# 暴露端口（如果需要监控接口）
# EXPOSE 8080

# 启动命令（默认运行30天）
CMD ["python", "run_virtual_trading.py", "--duration", "2592000"]
