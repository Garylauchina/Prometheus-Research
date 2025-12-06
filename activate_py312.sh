#!/bin/bash
# 激活Python 3.12虚拟环境

echo "🐍 激活Python 3.12虚拟环境..."
source venv312/bin/activate
echo "✅ Python 3.12环境已激活！"
python --version
echo ""
echo "💡 使用提示:"
echo "   - 运行测试: python test_xxx.py"
echo "   - 退出环境: deactivate"
echo ""

