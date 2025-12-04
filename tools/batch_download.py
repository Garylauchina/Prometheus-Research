#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量下载OKX历史数据

一次性下载多个配置：
- BTC-USDT: 1h (3年), 4h (5年), 1d (10年)
- ETH-USDT: 1h (3年)
"""

import sys
sys.path.insert(0, '..')

from download_okx_data import OKXDataDownloader
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

print("="*80)
print("批量下载OKX历史数据")
print("="*80)

downloader = OKXDataDownloader(data_dir='../data/okx')

# 下载配置
download_configs = [
    # BTC-USDT
    {'symbol': 'BTC-USDT', 'period': '1h', 'years': 3, 'desc': 'BTC 1小时K线（3年）'},
    {'symbol': 'BTC-USDT', 'period': '4h', 'years': 5, 'desc': 'BTC 4小时K线（5年）'},
    {'symbol': 'BTC-USDT', 'period': '1d', 'years': 10, 'desc': 'BTC 日线（10年）'},
    
    # ETH-USDT
    {'symbol': 'ETH-USDT', 'period': '1h', 'years': 3, 'desc': 'ETH 1小时K线（3年）'},
    {'symbol': 'ETH-USDT', 'period': '1d', 'years': 5, 'desc': 'ETH 日线（5年）'},
]

print(f"\n计划下载 {len(download_configs)} 个数据集:")
for i, config in enumerate(download_configs, 1):
    print(f"  {i}. {config['desc']}")

print("\n开始下载...\n")

# 逐个下载
for i, config in enumerate(download_configs, 1):
    print(f"\n{'='*80}")
    print(f"[{i}/{len(download_configs)}] {config['desc']}")
    print("="*80)
    
    try:
        df = downloader.download_historical_data(
            symbol=config['symbol'],
            period=config['period'],
            years=config['years'],
            force_redownload=False  # 已存在则跳过
        )
        
        print(f"✅ 完成: {len(df):,}条数据")
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        continue

print("\n" + "="*80)
print("✅ 批量下载完成！")
print("="*80)
print(f"\n数据保存位置: {downloader.data_dir.absolute()}")
print("\n可用文件:")

# 列出所有下载的文件
for file in sorted(downloader.data_dir.glob("*.csv")):
    size_mb = file.stat().st_size / 1024 / 1024
    print(f"  📄 {file.name:50s} ({size_mb:.2f} MB)")

print("\n" + "="*80)

