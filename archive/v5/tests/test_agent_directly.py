#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接测试LiveAgent类的update方法，验证final_signal_strength日志记录功能
"""

import sys
import os
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入LiveAgent类
from live_agent import LiveAgent

# 配置日志
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('direct_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def main():
    print(f"{'='*80}")
    print(f"开始直接测试LiveAgent.update方法")
    print(f"当前时间: {datetime.now()}")
    print(f"{'='*80}")
    
    try:
        # 创建一个LiveAgent实例
        config = {}
        agent = LiveAgent(
            agent_id="test_agent_direct",
            initial_capital=1000.0,
            config=config
        )
        
        print(f"成功创建代理: {agent.agent_id}")
        print(f"代理基因: {agent.gene}")
        
        # 准备模拟的market_data和regime
        market_data = {
            'spot': {'price': 50000.0},
            'futures': {'price': 50100.0},
            'candles': [[1630000000, 49800, 50200, 49700, 50100, 1000]]
        }
        regime = "sideways"
        
        print(f"\n准备调用update方法...")
        print(f"市场状态: {regime}")
        print(f"Market Data Keys: {list(market_data.keys())}")
        
        # 直接调用update方法
        agent.update(market_data, regime)
        
        print(f"\n{'='*80}")
        print(f"update方法调用完成")
        print(f"pending_signals: {agent.pending_signals}")
        
        # 检查日志文件是否创建
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'final_signal_strength.log')
        if os.path.exists(log_path):
            print(f"\nfinal_signal_strength.log已创建，大小: {os.path.getsize(log_path)} bytes")
            with open(log_path, 'r', encoding='utf-8') as f:
                print("\n最新日志内容:")
                lines = f.readlines()[-10:]  # 显示最后10行
                for i, line in enumerate(lines):
                    print(f"[{len(lines)-10+i+1}] {line.strip()}")
        else:
            print(f"\n错误: {log_path} 文件未创建")
            
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"测试结束")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
