# Prometheus v3.0 - Docker镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 设置环境变量（通过docker-compose或docker run传入）
ENV OKX_API_KEY=""
ENV OKX_SECRET_KEY=""
ENV OKX_PASSPHRASE=""

# 暴露端口（如果需要监控接口）
# EXPOSE 8080

# 启动命令（默认运行30天）
CMD ["python", "run_virtual_trading.py", "--duration", "2592000"]
