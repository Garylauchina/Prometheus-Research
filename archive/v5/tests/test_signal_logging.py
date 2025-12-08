#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本：直接测试final_signal_strength的日志记录功能
"""

import os
import sys
import logging
from datetime import datetime

# 确保日志级别设置正确
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_debug.log'),
        logging.StreamHandler()
    ]
)

def test_direct_signal_logging():
    """直接测试信号强度日志记录功能"""
    print("=== 开始测试信号强度日志记录 ===")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    agent_id = "test_agent_1"
    test_signal_strength = 0.85
    
    # 测试所有可能的日志记录渠道
    try:
        # 1. 标准输出
        separator = '#' * 80
        print(f"\n{separator}")
        print(f"🔔🔔🔔 [{timestamp}] [{agent_id}] FINAL SIGNAL STRENGTH = {test_signal_strength} 🔔🔔🔔")
        print(f"{separator}\n")
        sys.stdout.flush()
        
        # 2. 标准错误
        print(f"\n{separator}")
        print(f"🔔🔔🔔 [{timestamp}] [{agent_id}] FINAL SIGNAL STRENGTH = {test_signal_strength} 🔔🔔🔔", file=sys.stderr)
        print(f"{separator}\n", file=sys.stderr)
        sys.stderr.flush()
        
        # 3. 日志记录
        logging.critical(f"[{agent_id}] CRITICAL: 🚨 FINAL SIGNAL STRENGTH = {test_signal_strength} 🚨")
        logging.error(f"[{agent_id}] ERROR: 🚨 FINAL SIGNAL STRENGTH = {test_signal_strength} 🚨")
        logging.warning(f"[{agent_id}] WARNING: 🚨 FINAL SIGNAL STRENGTH = {test_signal_strength} 🚨")
        logging.info(f"[{agent_id}] INFO: 🚨 FINAL SIGNAL STRENGTH = {test_signal_strength} 🚨")
        
        # 4. 写入专用文件
        log_files = ['final_signal_strength.log', 'signal_monitor_log.txt', 'debug_log.txt']
        
        for log_file in log_files:
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] 🔔🔔🔔 [{agent_id}] FINAL_SIGNAL_STRENGTH = {test_signal_strength} 🔔🔔🔔\n")
                    f.write(f"[{timestamp}] [{agent_id}] 直接测试记录\n\n")
                print(f"✅ 成功写入 {log_file}")
            except Exception as e:
                print(f"❌ 写入{log_file}失败: {e}", file=sys.stderr)
        
        # 验证文件是否创建
        for log_file in log_files:
            if os.path.exists(log_file):
                file_size = os.path.getsize(log_file)
                print(f"✅ {log_file} 已创建，大小: {file_size} 字节")
                # 读取文件内容进行验证
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "FINAL_SIGNAL_STRENGTH" in content:
                            print(f"✅ {log_file} 包含预期的信号强度记录")
                        else:
                            print(f"❌ {log_file} 不包含预期的信号强度记录")
                except Exception as e:
                    print(f"❌ 读取{log_file}失败: {e}", file=sys.stderr)
            else:
                print(f"❌ {log_file} 未创建")
                
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}", file=sys.stderr)
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_direct_signal_logging()
