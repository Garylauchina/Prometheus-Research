#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX委托查询工具
用于查询OKX模拟盘中的当前委托和历史委托记录
特别关注BTC-USDT-SWAP的做空交易
"""

import sys
import time
from datetime import datetime

# 直接使用python-okx库
from okx import Trade

class OKXOrderChecker:
    def __init__(self, flag="1"):
        """
        初始化OKX订单检查器
        flag: 1表示模拟盘，0表示实盘
        """
        self.flag = flag
        self.symbol = "BTC-USDT-SWAP"
        self.expected_side = "short"
        self.expected_size = 320.0
        self.expected_avg_price = 91259.9645375
        self.price_tolerance = 0.1  # 价格容差
        
        # 初始化OKX Trade API
        self._init_trade_api()
    
    def _init_trade_api(self):
        """
        初始化OKX Trade API
        使用之前确认的正确API凭证
        """
        try:
            # 使用硬编码的API凭证，与check_positions.py一致
            api_key = '475458e9-6d8a-468d-95f0-fcfdc1a18643'
            secret_key = '74996019-6d60-4f70-89f5-f5196a11d22d'
            passphrase = 'Garylauchina3.14'
            
            print(f"正在初始化OKX Trade API (环境: {'模拟盘' if self.flag == '1' else '实盘'})...")
            self.trade_api = Trade.TradeAPI(
                api_key,
                secret_key,
                passphrase,
                flag=self.flag
            )
            print("Trade API初始化成功!")
        except Exception as e:
            print(f"初始化Trade API失败: {str(e)}")
            raise
    
    def get_open_orders(self):
        """
        获取当前未成交委托
        """
        try:
            print("\n正在获取当前未成交委托...")
            # 使用Trade API的get_open_orders方法
            result = self.trade_api.get_open_orders(
                instType="SWAP",
                instId=self.symbol,
                ordType="",
                state="live"
            )
            
            # 处理返回结果
            if result.get('code') == '0' and 'data' in result:
                open_orders = result['data']
                print(f"成功获取当前未成交委托，共 {len(open_orders)} 条记录")
                return open_orders
            else:
                error_msg = result.get('msg', 'Unknown error')
                print(f"获取当前未成交委托失败: {error_msg}")
                return []
        except Exception as e:
            print(f"获取当前未成交委托时出现异常: {str(e)}")
            return []
    
    def get_order_history(self, limit=100):
        """
        获取历史委托记录
        limit: 返回记录数量上限
        """
        try:
            print("\n正在获取历史委托记录...")
            # 获取近7天的历史委托
            end_ts = int(time.time() * 1000)
            start_ts = end_ts - 7 * 24 * 60 * 60 * 1000  # 7天前
            
            # 使用Trade API的get_orders_history方法
            result = self.trade_api.get_orders_history(
                instType="SWAP",
                instId=self.symbol,
                ordType="",
                state="",
                after=str(start_ts),
                before=str(end_ts),
                limit=str(limit)
            )
            
            # 处理返回结果
            if result.get('code') == '0' and 'data' in result:
                order_history = result['data']
                print(f"成功获取历史委托记录，共 {len(order_history)} 条记录")
                return order_history
            else:
                error_msg = result.get('msg', 'Unknown error')
                print(f"获取历史委托记录失败: {error_msg}")
                return []
        except Exception as e:
            print(f"获取历史委托记录时出现异常: {str(e)}")
            return []
    
    def find_matching_orders(self, orders):
        """
        查找匹配指定条件的委托记录
        orders: 委托记录列表
        返回匹配的委托记录列表
        """
        matching_orders = []
        
        for order in orders:
            try:
                # 检查订单是否匹配条件
                # 由于数据结构可能不同，采用更宽松的检查
                is_matching = False
                
                # 检查基本信息
                if isinstance(order, dict):
                    # 检查合约类型
                    if order.get('instId') != self.symbol:
                        continue
                    
                    # 检查方向
                    order_side = order.get('side', '').lower()
                    if order_side != self.expected_side:
                        continue
                    
                    # 检查数量（考虑可能存在的不同字段名）
                    size = None
                    for size_key in ['sz', 'size', 'quantity']:
                        if size_key in order:
                            try:
                                size = float(order[size_key])
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    # 检查价格（考虑可能存在的不同字段名）
                    price = None
                    for price_key in ['px', 'price', 'avgPx', 'avgPrice']:
                        if price_key in order:
                            try:
                                price = float(order[price_key])
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    # 判断是否匹配
                    if size and price:
                        size_match = abs(size - self.expected_size) < 0.01
                        price_match = abs(price - self.expected_avg_price) <= self.price_tolerance
                        
                        if size_match and price_match:
                            is_matching = True
                
                if is_matching:
                    matching_orders.append(order)
                    print(f"找到匹配的委托记录: {order}")
            except Exception as e:
                print(f"处理订单记录时出错: {str(e)}")
                continue
        
        return matching_orders
    
    def print_order_details(self, order):
        """
        打印委托记录详细信息
        """
        if not isinstance(order, dict):
            print(f"  无效的订单数据类型: {type(order)}")
            return
        
        print("  订单详情:")
        print(f"    合约代码: {order.get('instId', 'N/A')}")
        print(f"    订单ID: {order.get('ordId', order.get('orderId', 'N/A'))}")
        print(f"    方向: {order.get('side', 'N/A')}")
        print(f"    类型: {order.get('ordType', 'N/A')}")
        print(f"    数量: {order.get('sz', order.get('size', 'N/A'))}")
        print(f"    价格: {order.get('px', order.get('price', 'N/A'))}")
        print(f"    平均成交价: {order.get('avgPx', order.get('avgPrice', 'N/A'))}")
        print(f"    状态: {order.get('state', order.get('status', 'N/A'))}")
        print(f"    杠杆: {order.get('lever', 'N/A')}")
        
        # 格式化时间
        for time_key in ['cTime', 'createTime', 'tTime', 'updateTime']:
            if time_key in order:
                try:
                    timestamp = int(order[time_key])
                    # 处理毫秒级时间戳
                    if timestamp > 10000000000:
                        timestamp = timestamp // 1000
                    time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"    {time_key}: {time_str}")
                except Exception as e:
                    print(f"    {time_key}: {order[time_key]} (格式化失败: {str(e)})")
    
    def check_all_orders(self):
        """
        检查所有委托记录
        """
        try:
            print("=" * 80)
            print(f"开始查询OKX委托记录 (环境: {'模拟盘' if self.flag == '1' else '实盘'})")
            print(f"查询条件: 合约={self.symbol}, 方向={self.expected_side}, 数量={self.expected_size}, 价格={self.expected_avg_price}")
            print("=" * 80)
            
            # 获取并检查当前委托
            open_orders = self.get_open_orders()
            matching_open_orders = self.find_matching_orders(open_orders)
            
            print(f"\n匹配的当前未成交委托数量: {len(matching_open_orders)}")
            for i, order in enumerate(matching_open_orders, 1):
                print(f"\n  未成交委托 #{i}:")
                self.print_order_details(order)
            
            # 获取并检查历史委托
            history_orders = self.get_order_history()
            matching_history_orders = self.find_matching_orders(history_orders)
            
            print(f"\n匹配的历史委托数量: {len(matching_history_orders)}")
            for i, order in enumerate(matching_history_orders, 1):
                print(f"\n  历史委托 #{i}:")
                self.print_order_details(order)
            
            # 总结
            total_matches = len(matching_open_orders) + len(matching_history_orders)
            print("\n" + "=" * 80)
            if total_matches > 0:
                print(f"成功找到 {total_matches} 条匹配的委托记录!")
            else:
                print("未找到匹配的委托记录")
            print("=" * 80)
            
            return matching_open_orders, matching_history_orders
            
        except Exception as e:
            print(f"查询过程中发生错误: {str(e)}")
            raise


def main():
    """
    主函数
    """
    try:
        # 默认使用模拟盘
        flag = "1"
        
        # 允许通过命令行参数指定环境
        if len(sys.argv) > 1:
            flag_input = sys.argv[1].lower()
            if flag_input in ["0", "实盘", "live"]:
                flag = "0"
            elif flag_input in ["1", "模拟盘", "demo"]:
                flag = "1"
        
        # 初始化并执行查询
        checker = OKXOrderChecker(flag=flag)
        checker.check_all_orders()
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
