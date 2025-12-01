#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试OKX持仓情况的脚本
绕过缓存机制，直接调用API查看原始持仓数据
"""

import sys
from adapters.okx_compat import Account

def test_direct_positions():
    # 使用与check_positions.py相同的API凭证
    okx_config = {
        'api_key': "265a4c37-1dc1-40d8-80d0-11004026ca48",
        'secret_key': "0AD30E01A7B66FBBBEB7E30D8E0E18B4",
        'passphrase': "Garylauchina3.14",
        'flag': "1"  # 使用模拟盘模式
    }
    
    print("直接调用OKX API获取持仓信息（不使用缓存）...")
    print(f"使用的配置: flag={okx_config['flag']}")
    
    # 直接初始化AccountAPI
    account_api = Account.AccountAPI(
        okx_config['api_key'],
        okx_config['secret_key'],
        okx_config['passphrase'],
        flag=okx_config['flag']
    )
    
    # 1. 获取持仓信息
    print("\n1. 获取原始持仓数据:")
    try:
        # 获取所有类型的持仓
        result = account_api.get_positions()
        print(f"API响应状态码: {result['code']}")
        print(f"API响应消息: {result['msg']}")
        print(f"持仓数据项数: {len(result['data'])}")
        
        if result['data']:
            print("\n原始持仓数据详情:")
            for i, pos in enumerate(result['data']):
                print(f"\n持仓 {i+1}:")
                for key, value in pos.items():
                    print(f"  {key}: {value}")
        else:
            print("\n没有持仓数据")
    except Exception as e:
        print(f"获取持仓失败: {e}")
    
    # 2. 获取账户余额信息
    print("\n2. 获取账户余额信息:")
    try:
        balance_result = account_api.get_account_balance()
        print(f"API响应状态码: {balance_result['code']}")
        print(f"API响应消息: {balance_result['msg']}")
        
        if balance_result['code'] == '0' and len(balance_result['data']) > 0:
            print("\n账户余额详情:")
            for item in balance_result['data'][0]['details']:
                print(f"\n币种: {item.get('ccy')}")
                print(f"  可用余额: {item.get('availBal')}")
                print(f"  冻结余额: {item.get('frozenBal')}")
                print(f"  权益: {item.get('eq')}")
    except Exception as e:
        print(f"获取余额失败: {e}")
    
    # 3. 特别检查永续合约持仓
    print("\n3. 专门检查永续合约(SWAP)持仓:")
    try:
        swap_result = account_api.get_positions(instType="SWAP")
        print(f"API响应状态码: {swap_result['code']}")
        print(f"API响应消息: {swap_result['msg']}")
        print(f"永续合约持仓数据项数: {len(swap_result['data'])}")
        
        if swap_result['data']:
            print("\n永续合约持仓详情:")
            for i, pos in enumerate(swap_result['data']):
                print(f"\n持仓 {i+1}:")
                for key, value in pos.items():
                    print(f"  {key}: {value}")
        else:
            print("\n没有永续合约持仓")
    except Exception as e:
        print(f"获取永续合约持仓失败: {e}")

if __name__ == "__main__":
    test_direct_positions()
