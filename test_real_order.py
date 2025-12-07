#!/usr/bin/env python3
"""
测试真实下单功能
================

这个脚本会尝试在OKX模拟盘上真实下单
确保能在OKX页面上看到订单
"""

import sys
sys.path.insert(0, '.')

from prometheus.exchange.okx_api import OKXExchange
import time
import json
import os

print("="*70)
print("🧪 测试OKX模拟盘真实下单")
print("="*70)

# 1. 读取配置文件
print("\n📋 读取配置...")

# 尝试读取VPS配置（JSON格式）
vps_config_path = 'config/vps_config.json'
if os.path.exists(vps_config_path):
    with open(vps_config_path, 'r') as f:
        config = json.load(f)
    okx_config = config['okx']
    api_key = okx_config['api_key']
    api_secret = okx_config['api_secret']
    passphrase = okx_config['passphrase']
    paper_trading = okx_config['paper_trading']
    print(f"✅ 使用VPS配置: {vps_config_path}")
else:
    # 读取本地配置（Python格式）
    sys.path.insert(0, 'config')
    try:
        from okx_config import OKX_PAPER_TRADING
        api_key = OKX_PAPER_TRADING['api_key']
        api_secret = OKX_PAPER_TRADING['api_secret']
        passphrase = OKX_PAPER_TRADING['passphrase']
        paper_trading = True  # 本地默认使用模拟盘
        print(f"✅ 使用本地配置: config/okx_config.py")
    except Exception as e:
        print(f"❌ 无法读取配置: {e}")
        sys.exit(1)

print(f"   模拟盘模式: {paper_trading}")

# 2. 初始化OKX
print("\n📡 初始化OKX...")
print(f"   使用API: {api_key[:10]}...")

# 修复：使用sandbox模式连接OKX模拟盘（而不是本地模拟）
exchange = OKXExchange(
    api_key=api_key,
    api_secret=api_secret,
    passphrase=passphrase,
    paper_trading=False,  # 不使用本地模拟
    testnet=True  # 使用OKX sandbox（模拟盘）
)

# 2. 测试连接
print("\n🔗 测试连接...")
if not exchange.test_connection():
    print("❌ 连接失败")
    sys.exit(1)
print("✅ 连接成功")

# 3. 获取当前价格
print("\n📊 获取当前价格...")
ticker = exchange.get_ticker('BTC/USDT')
if ticker:
    current_price = ticker['last']
    print(f"✅ 当前BTC价格: ${current_price:,.2f}")
else:
    print("❌ 无法获取价格")
    sys.exit(1)

# 4. 获取账户余额
print("\n💰 获取账户余额...")
balance = exchange.get_account_value()
print(f"✅ 账户余额: ${balance:,.2f}")

# 5. 尝试下单（极小数量）
print("\n"+"="*70)
print("⚠️  准备下单测试")
print("="*70)
print("配置:")
print("  - 交易对: BTC/USDT")
print("  - 方向: BUY (开多)")
print("  - 数量: 0.0001 BTC (最小数量)")
print("  - 类型: 市价单")
print("  - 杠杆: 1x")
print()

confirm = input("是否继续下单测试？(输入 YES 继续): ")
if confirm != "YES":
    print("❌ 已取消")
    sys.exit(0)

print("\n📝 下单中...")
try:
    order = exchange.place_order(
        symbol='BTC/USDT',
        side='buy',
        size=0.0001,  # 最小数量
        order_type='market',
        leverage=1.0
    )
    
    if order:
        print("✅ 下单成功！")
        print(f"订单信息: {order}")
        print("\n" + "="*70)
        print("🎉 成功！请到OKX模拟盘页面查看订单")
        print("="*70)
        print("OKX模拟盘地址: https://www.okx.com/cn/trade-demo")
        print()
        
        # 等待3秒后平仓
        print("⏳ 等待3秒后自动平仓...")
        time.sleep(3)
        
        print("\n📝 平仓中...")
        close_order = exchange.place_order(
            symbol='BTC/USDT',
            side='sell',
            size=0.0001,
            order_type='market'
        )
        
        if close_order:
            print("✅ 平仓成功！")
            print(f"订单信息: {close_order}")
        else:
            print("⚠️  平仓失败，请手动在OKX页面平仓")
    else:
        print("❌ 下单失败：未返回订单信息")
        
except Exception as e:
    print(f"❌ 下单异常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n"+"="*70)
print("✅ 测试完成")
print("="*70)

