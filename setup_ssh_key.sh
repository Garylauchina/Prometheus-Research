#!/bin/bash
# 配置SSH密钥到VPS
# 运行方式：在终端直接执行以下命令

echo "======================================"
echo "🔑 配置SSH密钥到VPS"
echo "======================================"
echo ""

# 1. 显示公钥
echo "📋 你的SSH公钥内容："
echo "--------------------------------------"
cat ~/.ssh/id_rsa.pub
echo "--------------------------------------"
echo ""

# 2. 说明
echo "📝 手动配置步骤："
echo "1. 复制上面的公钥内容（整行）"
echo "2. 打开新终端，执行："
echo ""
echo "   ssh root@45.76.97.37"
echo "   （输入密码：9a%ZwL}gfx+c8eVz）"
echo ""
echo "3. 在VPS上执行："
echo ""
echo "   mkdir -p ~/.ssh"
echo "   chmod 700 ~/.ssh"
echo "   echo '你的公钥内容' >> ~/.ssh/authorized_keys"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo "   exit"
echo ""
echo "4. 测试无密码登录："
echo ""
echo "   ssh root@45.76.97.37"
echo "   （应该无需密码直接登录）"
echo ""
echo "======================================"
echo "✅ 配置完成后，bash脚本就能正常工作了！"
echo "======================================"

