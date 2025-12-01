#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OKX账户持仓检查脚本
用于查看当前账户的持仓、余额和未成交订单
"""

import sys
import os

# 添加项目路径
project_path = '/home/ubuntu/prometheus_v30'
if os.path.exists(project_path):
    sys.path.insert(0, project_path)
else:
    print(f"错误: 项目路径不存在: {project_path}")
    sys.exit(1)

try:
    from adapters.okx_adapter import OKXTradingAdapter
    from config_virtual import CONFIG_VIRTUAL_TRADING as CONFIG
except ImportError as e:
    print(f"错误: 无法导入模块: {e}")
    print(f"当前路径: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)

print("="*80)
print("OKX账户持仓检查")
print("="*80)

print("\n连接到OKX...")
try:
    adapter = OKXTradingAdapter(CONFIG)
except Exception as e:
    print(f"错误: 无法连接到OKX: {e}")
    sys.exit(1)

# 账户信息
print("\n" + "="*80)
print("账户信息")
print("="*80)
try:
    account_info = adapter.account_sync.get_account_summary()
    print(f"账户权益: ${account_info['equity']:.2f}")
    print(f"可用余额: ${account_info.get('available_balance', 0):.2f}")
    print(f"未实现盈亏: ${account_info['unrealized_pnl']:.2f}")
    print(f"已实现盈亏: ${account_info.get('realized_pnl', 0):.2f}")
except Exception as e:
    print(f"错误: 无法获取账户信息: {e}")

# 持仓列表
print("\n" + "="*80)
print("持仓列表")
print("="*80)
try:
    positions = adapter.get_positions(CONFIG['symbol'])
    if positions:
        print(f"找到 {len(positions)} 个持仓:\n")
        for i, pos in enumerate(positions, 1):
            print(f"持仓 {i}:")
            print(f"  交易对: {pos.get('instId', 'N/A')}")
            print(f"  方向: {pos.get('posSide', 'N/A')}")
            print(f"  数量: {pos.get('pos', 'N/A')}")
            print(f"  可平数量: {pos.get('availPos', 'N/A')}")
            print(f"  开仓均价: {pos.get('avgPx', 'N/A')}")
            print(f"  最新价格: {pos.get('last', 'N/A')}")
            print(f"  未实现盈亏: {pos.get('upl', 'N/A')}")
            print(f"  未实现盈亏率: {pos.get('uplRatio', 'N/A')}")
            print(f"  保证金: {pos.get('margin', 'N/A')}")
            print(f"  杠杆倍数: {pos.get('lever', 'N/A')}")
            print()
    else:
        print("✅ 没有持仓")
except Exception as e:
    print(f"错误: 无法获取持仓: {e}")

# 未成交订单
print("="*80)
print("未成交订单")
print("="*80)
try:
    orders = adapter.get_open_orders(CONFIG['symbol'])
    if orders:
        print(f"找到 {len(orders)} 个未成交订单:\n")
        for i, order in enumerate(orders, 1):
            print(f"订单 {i}:")
            print(f"  订单ID: {order.get('ordId', 'N/A')}")
            print(f"  交易对: {order.get('instId', 'N/A')}")
            print(f"  方向: {order.get('side', 'N/A')}")
            print(f"  持仓方向: {order.get('posSide', 'N/A')}")
            print(f"  订单类型: {order.get('ordType', 'N/A')}")
            print(f"  数量: {order.get('sz', 'N/A')}")
            print(f"  价格: {order.get('px', 'N/A')}")
            print(f"  状态: {order.get('state', 'N/A')}")
            print()
    else:
        print("✅ 没有未成交订单")
except Exception as e:
    print(f"错误: 无法获取订单: {e}")

print("="*80)
print("检查完成")
print("="*80)
