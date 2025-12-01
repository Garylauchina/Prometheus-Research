#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OKX账户持仓检查脚本
用于查看当前账户的持仓、余额和未成交订单
"""

import sys
import os

# 添加项目路径
project_path = 'E:\\Trae_store\\prometheus-v30\\'
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
    # 确保正确传递API配置
    okx_config = {
        'api_key': CONFIG['okx_api']['api_key'],
        'secret_key': CONFIG['okx_api']['secret_key'],
        'passphrase': CONFIG['okx_api']['passphrase'],
        'flag': CONFIG['okx_api']['flag']
    }
    adapter = OKXTradingAdapter(okx_config)
except Exception as e:
    print(f"错误: 无法连接到OKX: {e}")
    print(f"配置信息: {CONFIG.get('okx_api', '未找到okx_api配置')}")
    sys.exit(1)

# 账户信息
print("\n" + "="*80)
print("账户信息")
print("="*80)
try:
    account_info = adapter.get_account_summary()
    print(f"账户权益: ${account_info.get('total_equity', 0):.2f}")
    print(f"可用余额: ${account_info.get('available_balance', 0):.2f}")
    print(f"未实现盈亏: ${account_info.get('total_unrealized_pnl', 0):.2f}")
    print(f"已实现盈亏: ${account_info.get('realized_pnl', 0):.2f}")
    # 显示更多可用的账户信息
    for key, value in account_info.items():
        if key not in ['total_equity', 'available_balance', 'total_unrealized_pnl', 'realized_pnl']:
            print(f"  {key}: {value}")
except Exception as e:
    print(f"错误: 无法获取账户信息: {e}")
    print(f"账户信息详情: {account_info}")

# 持仓列表
print("\n" + "="*80)
print("持仓列表")
print("="*80)
try:
    # 直接获取所有持仓，不指定inst_type参数
    positions = adapter.get_positions()
    
    # 从账户摘要中获取持仓信息（备用方案）
    account_info = adapter.get_account_summary()
    summary_positions = account_info.get('positions', {})
    
    # 合并两种方式获取的持仓信息
    all_positions = summary_positions.copy()
    
    # 处理返回类型差异
    if isinstance(positions, dict) and positions:
        # 如果是字典格式，合并到all_positions
        for key, value in positions.items():
            if key not in all_positions:
                all_positions[key] = value
    elif isinstance(positions, list):
        # 如果是列表格式，转换为字典
        for pos in positions:
            if isinstance(pos, dict) and 'instId' in pos:
                all_positions[pos['instId']] = pos
    
    if all_positions:
        print(f"找到 {len(all_positions)} 个持仓:\n")
        for i, (inst_id, pos) in enumerate(all_positions.items(), 1):
            print(f"持仓 {i}:")
            print(f"  交易对: {inst_id}")
            print(f"  方向: {pos.get('side', pos.get('posSide', 'N/A'))}")
            print(f"  数量: {pos.get('size', pos.get('pos', 'N/A'))}")
            print(f"  开仓均价: {pos.get('avg_price', pos.get('avgPx', 'N/A'))}")
            print(f"  未实现盈亏: {pos.get('unrealized_pnl', pos.get('upl', 'N/A'))}")
            print(f"  杠杆倍数: {pos.get('leverage', pos.get('lever', 'N/A'))}")
            print()
    else:
        print("✅ 没有持仓")
except Exception as e:
    print(f"错误: 无法获取持仓: {e}")
    # 即使出错也显示账户信息中的持仓
    if 'account_info' in locals() and 'positions' in account_info:
        summary_positions = account_info['positions']
        if summary_positions:
            print("\n从账户摘要获取的持仓信息:")
            for inst_id, pos in summary_positions.items():
                print(f"  {inst_id}: {pos}")

# USDT余额检查
print("\n" + "="*80)
print("USDT余额")
print("="*80)
try:
    usdt_balance = adapter.get_usdt_balance()
    print(f"USDT可用余额: ${usdt_balance:.2f}")
except Exception as e:
    print(f"错误: 无法获取USDT余额: {e}")

# API调用统计
print("\n" + "="*80)
print("API调用统计")
print("="*80)
try:
    api_stats = adapter.get_api_stats()
    print(f"成功调用: {api_stats.get('success', 0)}")
    print(f"失败调用: {api_stats.get('failure', 0)}")
    print(f"重试次数: {api_stats.get('retry', 0)}")
except Exception as e:
    print(f"错误: 无法获取API统计: {e}")

print("="*80)
print("检查完成")
print("="*80)
