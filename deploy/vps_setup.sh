#!/bin/bash
# VPS环境搭建脚本
# ==================

echo ""
echo "=========================================="
echo "🚀 Prometheus VPS环境搭建"
echo "=========================================="
echo ""

# 1. 更新系统
echo "📦 更新系统..."
sudo apt update && sudo apt upgrade -y

# 2. 安装Python 3.12
echo ""
echo "🐍 安装Python 3.12..."
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# 3. 安装必要工具
echo ""
echo "🔧 安装必要工具..."
sudo apt install -y git curl wget vim htop

# 4. 创建项目目录
echo ""
echo "📁 创建项目目录..."
mkdir -p ~/prometheus
cd ~/prometheus

# 5. 创建虚拟环境
echo ""
echo "🌐 创建Python虚拟环境..."
python3.12 -m venv venv
source venv/bin/activate

# 6. 升级pip
echo ""
echo "📦 升级pip..."
pip install --upgrade pip

# 7. 安装依赖
echo ""
echo "📦 安装Python依赖..."
pip install ccxt numpy pandas scipy matplotlib

# 8. 创建必要目录
echo ""
echo "📁 创建目录结构..."
mkdir -p logs data config

# 9. 显示信息
echo ""
echo "=========================================="
echo "✅ 环境搭建完成！"
echo "=========================================="
echo ""
echo "📋 下一步："
echo "   1. 上传Prometheus代码到 ~/prometheus"
echo "   2. 配置 config/vps_config.json"
echo "   3. 运行: source venv/bin/activate"
echo "   4. 启动: python vps_main.py"
echo ""
echo "=========================================="

