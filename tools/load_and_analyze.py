#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
加载和分析本地历史数据

展示如何使用下载的数据进行分析和测试
"""

import sys
sys.path.insert(0, '..')

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)


def load_data(symbol: str = "BTC-USDT", period: str = "1h", years: int = 3) -> pd.DataFrame:
    """
    加载本地数据
    
    Args:
        symbol: 交易对
        period: 时间周期
        years: 年数
    
    Returns:
        pd.DataFrame: 历史数据
    """
    data_dir = Path('../data/okx')
    filename = f"{symbol.replace('-', '_')}_{period}_{years}y.parquet"
    file_path = data_dir / filename
    
    if not file_path.exists():
        # 尝试CSV
        csv_file = file_path.with_suffix('.csv')
        if csv_file.exists():
            print(f"📂 加载数据: {csv_file.name}")
            df = pd.read_csv(csv_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            raise FileNotFoundError(
                f"数据文件不存在: {filename}\n"
                f"请先运行: python download_okx_data.py --symbol {symbol} --period {period} --years {years}"
            )
    
    print(f"📂 加载数据: {filename}")
    df = pd.read_parquet(file_path)
    return df


def analyze_market_conditions(df: pd.DataFrame):
    """
    分析市场条件（用于配置滑点和资金费率模型）
    
    Args:
        df: 历史数据
    """
    print("\n" + "="*80)
    print("📊 市场条件分析")
    print("="*80)
    
    # 1. 波动率分析
    df['returns'] = df['close'].pct_change()
    daily_vol = df['returns'].std()
    
    print(f"\n1. 波动率分析:")
    print(f"   日均波动率: {daily_vol:.4%}")
    print(f"   年化波动率: {daily_vol * (365**0.5):.2%}")
    
    # 波动率分位数
    vol_quantiles = df['returns'].abs().quantile([0.5, 0.75, 0.9, 0.95, 0.99])
    print(f"\n   波动率分位数:")
    for q, val in vol_quantiles.items():
        print(f"   {q*100:5.1f}%: {val:.4%}")
    
    # 2. 价格范围分析
    print(f"\n2. 价格范围:")
    print(f"   最低价: ${df['low'].min():,.2f}")
    print(f"   最高价: ${df['high'].max():,.2f}")
    print(f"   当前价: ${df['close'].iloc[-1]:,.2f}")
    print(f"   价格振幅: {(df['high'].max() / df['low'].min() - 1) * 100:.1f}%")
    
    # 3. 成交量分析
    print(f"\n3. 成交量分析:")
    print(f"   平均成交量: ${df['volume_quote'].mean():,.0f}")
    print(f"   中位成交量: ${df['volume_quote'].median():,.0f}")
    print(f"   最大成交量: ${df['volume_quote'].max():,.0f}")
    
    # 4. 价差估算（基于波动率）
    avg_spread_estimate = daily_vol * 0.1  # 假设价差约为波动率的10%
    print(f"\n4. 价差估算:")
    print(f"   估计价差: {avg_spread_estimate:.4%}")
    print(f"   （基于波动率 × 10%）")
    
    # 5. 推荐模型参数
    print(f"\n5. 推荐模型参数:")
    print(f"\n   SlippageModel:")
    print(f"   - base_slippage: {daily_vol * 0.02:.6f}  # 波动率 × 2%")
    print(f"   - liquidity_factor: 0.01")
    print(f"   - volatility_factor: {0.5 if daily_vol < 0.03 else 0.8}")
    
    print(f"\n   MarketCondition:")
    print(f"   - volatility: {daily_vol:.6f}")
    print(f"   - bid_ask_spread: {avg_spread_estimate:.6f}")
    print(f"   - liquidity_depth: {df['volume_quote'].median():.0f}  # 使用中位成交量")


def find_extreme_periods(df: pd.DataFrame, top_n: int = 10):
    """
    找出极端波动时期（用于压力测试）
    
    Args:
        df: 历史数据
        top_n: 返回前N个极端时期
    """
    print("\n" + "="*80)
    print(f"🌪️  极端波动时期（Top {top_n}）")
    print("="*80)
    
    df['returns'] = df['close'].pct_change()
    df['abs_returns'] = df['returns'].abs()
    
    # 找出最大波动时期
    extreme_periods = df.nlargest(top_n, 'abs_returns')[
        ['timestamp', 'close', 'returns', 'volume_quote']
    ]
    
    print("\n（可用于极端市场压力测试）\n")
    for i, row in enumerate(extreme_periods.itertuples(), 1):
        print(f"{i:2d}. {row.timestamp} | "
              f"价格: ${row.close:,.0f} | "
              f"波动: {row.returns:+.2%} | "
              f"成交量: ${row.volume_quote:,.0f}")


if __name__ == "__main__":
    # 加载数据
    try:
        df = load_data(symbol="BTC-USDT", period="1h", years=3)
        
        print(f"\n✅ 数据加载成功: {len(df):,}条")
        print(f"   时间范围: {df['timestamp'].min()} 至 {df['timestamp'].max()}")
        
        # 分析市场条件
        analyze_market_conditions(df)
        
        # 找出极端时期
        find_extreme_periods(df)
        
        print("\n" + "="*80)
        print("💡 使用建议:")
        print("="*80)
        print("\n1. 回测系统:")
        print("   df = load_data('BTC-USDT', '1h', 3)")
        print("   # 使用df进行回测\n")
        print("2. 测试极端市场:")
        print("   # 使用上面的极端时期数据测试系统")
        print("   extreme_data = df.loc[df['timestamp'] == '2024-XX-XX']\n")
        print("3. 配置真实参数:")
        print("   # 根据上面的推荐参数配置SlippageModel和MarketCondition")
        
    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        print("\n请先运行下载脚本:")
        print("  cd tools")
        print("  python download_okx_data.py --symbol BTC-USDT --period 1h --years 3")

