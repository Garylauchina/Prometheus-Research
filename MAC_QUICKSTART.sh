#!/bin/bash
# Prometheus v5.2 MAC快速启动脚本
# 使用方法: bash MAC_QUICKSTART.sh

echo "========================================================================"
echo "🍎 Prometheus v5.2 MAC环境快速设置"
echo "========================================================================"
echo ""

# 检查是否在正确的目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 步骤1：检查Python版本
echo "📋 步骤1/5：检查Python版本..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "   发现: $PYTHON_VERSION"

if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "   ✅ Python版本符合要求 (需要3.10+)"
else
    echo "   ❌ Python版本过低，请安装Python 3.10+"
    echo "   安装命令: brew install python@3.10"
    exit 1
fi
echo ""

# 步骤2：创建虚拟环境
echo "📋 步骤2/5：创建虚拟环境..."
if [ -d "venv" ]; then
    echo "   ⚠️  虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "   ✅ 虚拟环境创建成功"
fi
echo ""

# 步骤3：激活虚拟环境并安装依赖
echo "📋 步骤3/5：安装依赖..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "   ✅ 依赖安装完成"
echo ""

# 步骤4：验证分支
echo "📋 步骤4/5：验证分支..."
CURRENT_BRANCH=$(git branch --show-current)
echo "   当前分支: $CURRENT_BRANCH"
if [ "$CURRENT_BRANCH" != "develop/v5.0" ]; then
    echo "   ⚠️  警告：你在 $CURRENT_BRANCH 分支"
    echo "   建议切换到 develop/v5.0: git checkout develop/v5.0"
else
    echo "   ✅ 分支正确 (develop/v5.0)"
fi
echo ""

# 步骤5：运行测试
echo "📋 步骤5/5：运行验证测试..."
echo "   正在运行 test_fitness_v2.py..."
if python test_fitness_v2.py > /dev/null 2>&1; then
    echo "   ✅ Fitness测试通过"
else
    echo "   ❌ Fitness测试失败，请检查日志"
    exit 1
fi
echo ""

# 完成
echo "========================================================================"
echo "🎉 环境设置完成！"
echo "========================================================================"
echo ""
echo "📚 下一步："
echo "   1. 激活虚拟环境: source venv/bin/activate"
echo "   2. 阅读交接文档: MAC_HANDOVER.md"
echo "   3. 在Cursor中打开项目: open -a Cursor ."
echo ""
echo "🚀 准备开始Day 3开发：Lineage熵监控优化"
echo ""

