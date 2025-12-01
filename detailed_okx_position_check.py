#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
详细检查OKX BTC-USDT-SWAP持仓脚本
用于深入分析持仓显示不一致问题
"""

import os
import json
import time
from datetime import datetime
import pandas as pd
from adapters.okx_adapter import OKXTradingAdapter
import config

class DetailedPositionChecker:
    def __init__(self):
        # 首先让用户选择环境
        print("请选择查询环境:")
        print("1. 实盘 (flag=0)")
        print("2. 模拟盘 (flag=1)")
        choice = input("请输入选择 (1 或 2): ").strip()
        
        if choice == "1":
            flag_value = "0"
            self.env_name = "实盘"
        else:
            flag_value = "1"
            self.env_name = "模拟盘"
        
        print(f"\n正在使用 {self.env_name} 环境 (flag={flag_value})...\n")
        
        # 直接使用与check_positions.py相同的API凭证
        adapter_config = {
            'api_key': "265a4c37-1dc1-40d8-80d0-11004026ca48",
            'secret_key': "0AD30E01A7B66FBBBEB7E30D8E0E18B4",
            'passphrase': "Garylauchina3.14",
            'flag': flag_value
        }
        
        # 初始化适配器
        self.adapter = OKXTradingAdapter(adapter_config)
        self.symbol = "BTC-USDT-SWAP"
    
    def print_separator(self, title):
        print("=" * 80)
        print(f"{title} - {self.env_name}")
        print("=" * 80)
    
    def get_raw_positions(self):
        """获取原始持仓数据"""
        self.print_separator("原始持仓数据 (get_positions())")
        try:
            positions = self.adapter.get_positions()
            if positions:
                print(f"找到 {len(positions)} 个持仓")
                for pos in positions:
                    print(json.dumps(pos, ensure_ascii=False, indent=2))
            else:
                print("未找到持仓")
            return positions
        except Exception as e:
            print(f"获取持仓数据时出错: {e}")
            return []
    
    def get_account_summary(self):
        """获取账户摘要"""
        self.print_separator("账户摘要 (get_account_summary())")
        try:
            summary = self.adapter.get_account_summary()
            print(f"账户摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")
            
            # 特别关注持仓信息
            if 'positions' in summary and summary['positions']:
                print("\n账户摘要中的持仓信息:")
                for pos in summary['positions']:
                    print(json.dumps(pos, ensure_ascii=False, indent=2))
            
            return summary
        except Exception as e:
            print(f"获取账户摘要时出错: {e}")
            return None
    
    def get_position_details(self):
        """获取指定交易对的详细持仓信息"""
        self.print_separator(f"{self.symbol} 详细持仓信息")
        try:
            # 直接访问_account_sync获取最原始的持仓数据
            if hasattr(self.adapter, '_account_sync'):
                account_sync = self.adapter._account_sync
                
                # 强制刷新数据
                print("强制刷新账户数据...")
                account_sync.refresh_account_data()
                
                # 获取所有持仓
                all_positions = account_sync.get_positions()
                
                # 过滤指定交易对
                target_positions = [p for p in all_positions if p['instId'] == self.symbol]
                
                if target_positions:
                    print(f"找到 {len(target_positions)} 个 {self.symbol} 持仓")
                    for pos in target_positions:
                        print(json.dumps(pos, ensure_ascii=False, indent=2))
                        print("-" * 50)
                else:
                    print(f"未找到 {self.symbol} 持仓")
                
                return target_positions
            else:
                print("无法访问 _account_sync 属性")
                return []
        except Exception as e:
            print(f"获取详细持仓信息时出错: {e}")
            return []
    
    def get_order_history(self):
        """获取订单历史"""
        self.print_separator(f"{self.symbol} 订单历史")
        try:
            # 获取最近的订单历史
            orders = []
            limit = 50  # 获取最近50个订单
            
            # 注意：这里需要根据实际的adapter接口调整
            # 如果adapter有get_orders或类似方法，使用它
            # 否则使用_account_sync
            if hasattr(self.adapter, '_account_sync'):
                # 尝试直接调用API获取订单历史
                # 这里使用OKX API的标准参数
                params = {
                    'instType': 'SWAP',
                    'instId': self.symbol,
                    'ordType': '',
                    'state': '',  # 空字符串表示查询所有状态
                    'after': '',
                    'before': '',
                    'limit': str(limit)
                }
                
                # 直接调用底层API
                response = self.adapter._account_sync._api.get_orders(**params)
                if 'data' in response and response['data']:
                    orders = response['data']
                    print(f"找到 {len(orders)} 个订单")
                    
                    # 按时间倒序排序
                    orders.sort(key=lambda x: x.get('cTime', ''), reverse=True)
                    
                    # 显示最近10个订单
                    for i, order in enumerate(orders[:10]):
                        print(f"\n订单 {i+1}:")
                        print(f"时间: {order.get('cTime', 'N/A')}")
                        print(f"订单ID: {order.get('ordId', 'N/A')}")
                        print(f"价格: {order.get('px', 'N/A')}")
                        print(f"数量: {order.get('sz', 'N/A')}")
                        print(f"方向: {order.get('side', 'N/A')}")
                        print(f"状态: {order.get('state', 'N/A')}")
                        print(f"成交数量: {order.get('accFillSz', 'N/A')}")
                else:
                    print("未找到订单历史")
            else:
                print("无法访问订单历史")
                
            return orders
        except Exception as e:
            print(f"获取订单历史时出错: {e}")
            return []
    
    def get_orders_algo(self):
        """获取策略订单（如止损止盈）"""
        self.print_separator(f"{self.symbol} 策略订单")
        try:
            if hasattr(self.adapter, '_account_sync'):
                params = {
                    'instType': 'SWAP',
                    'instId': self.symbol,
                    'ordType': '',
                    'algoType': '',  # 空字符串表示查询所有类型
                    'state': '',
                    'after': '',
                    'before': '',
                    'limit': '20'
                }
                
                response = self.adapter._account_sync._api.get_orders_algo(**params)
                if 'data' in response and response['data']:
                    algo_orders = response['data']
                    print(f"找到 {len(algo_orders)} 个策略订单")
                    for order in algo_orders[:10]:  # 显示最近10个
                        print(f"\n策略订单:")
                        print(f"类型: {order.get('algoType', 'N/A')}")
                        print(f"时间: {order.get('cTime', 'N/A')}")
                        print(f"订单ID: {order.get('algoId', 'N/A')}")
                        print(f"价格: {order.get('px', 'N/A')}")
                        print(f"数量: {order.get('sz', 'N/A')}")
                        print(f"方向: {order.get('side', 'N/A')}")
                        print(f"状态: {order.get('state', 'N/A')}")
                else:
                    print("未找到策略订单")
            else:
                print("无法访问策略订单")
        except Exception as e:
            print(f"获取策略订单时出错: {e}")
    
    def check_api_cache(self):
        """检查API缓存状态"""
        self.print_separator("API缓存状态检查")
        try:
            if hasattr(self.adapter, '_account_sync'):
                account_sync = self.adapter._account_sync
                
                # 检查缓存相关属性
                print("账户同步对象属性:")
                for attr in dir(account_sync):
                    if not attr.startswith('__'):
                        print(f"  - {attr}")
                
                # 检查是否有缓存更新时间
                if hasattr(account_sync, '_last_update_time'):
                    print(f"\n上次更新时间: {account_sync._last_update_time}")
                
                # 检查是否有缓存失效机制
                print("\n尝试刷新缓存...")
                start_time = time.time()
                account_sync.refresh_account_data()
                end_time = time.time()
                print(f"刷新耗时: {(end_time - start_time) * 1000:.2f} ms")
        except Exception as e:
            print(f"检查缓存状态时出错: {e}")
    
    def run_complete_check(self):
        """运行完整检查"""
        print(f"开始详细检查 {self.symbol} 持仓...\n")
        
        # 1. 获取原始持仓数据
        raw_positions = self.get_raw_positions()
        print()
        
        # 2. 获取账户摘要
        account_summary = self.get_account_summary()
        print()
        
        # 3. 获取详细持仓信息
        position_details = self.get_position_details()
        print()
        
        # 4. 检查API缓存
        self.check_api_cache()
        print()
        
        # 5. 获取订单历史
        order_history = self.get_order_history()
        print()
        
        # 6. 获取策略订单
        self.get_orders_algo()
        print()
        
        # 汇总分析
        self.print_separator("汇总分析")
        
        # 检查是否存在BTC-USDT-SWAP持仓
        has_btc_position = False
        position_data = None
        
        # 首先检查账户摘要中的持仓
        if account_summary and 'positions' in account_summary:
            positions = account_summary['positions']
            if self.symbol in positions:
                has_btc_position = True
                position_data = positions[self.symbol]
        
        if has_btc_position and position_data:
            print(f"系统检测到 {self.symbol} 持仓存在:")
            print(f"  - 持仓数量: {position_data.get('pos', 'N/A')}")
            print(f"  - 可用数量: {position_data.get('availPos', 'N/A')}")
            print(f"  - 开仓均价: {position_data.get('avgPx', 'N/A')}")
            print(f"  - 方向: {position_data.get('posSide', 'N/A')}")
            print(f"  - 未实现盈亏: {position_data.get('upl', 'N/A')}")
            
            # 分析可能的原因
            print("\n可能的原因分析:")
            print("1. 您可能查看的是实盘，而系统连接的是模拟盘")
            print("2. 持仓可能是历史持仓，未完全平仓")
            print("3. API返回的数据可能存在延迟或缓存")
            print("4. 检查是否有未触发的策略订单")
        else:
            print(f"未检测到 {self.symbol} 持仓")
        
        print("\n检查完成!")

if __name__ == "__main__":
    checker = DetailedPositionChecker()
    checker.run_complete_check()
