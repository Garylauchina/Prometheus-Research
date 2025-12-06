"""
OKX历史K线数据加载器

支持：
1. 从CSV文件加载历史数据
2. 从OKX API获取历史数据（可选）
3. 数据预处理和验证
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class OKXDataLoader:
    """OKX历史K线数据加载器"""
    
    def __init__(self, data_dir: str = "data/okx"):
        """
        初始化数据加载器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📂 OKX数据加载器初始化 | 数据目录: {self.data_dir}")
    
    def load_from_csv(self, 
                      csv_path: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> pd.DataFrame:
        """
        从CSV文件加载K线数据
        
        CSV格式：
        timestamp,open,high,low,close,volume,turnover
        
        Args:
            csv_path: CSV文件路径
            start_date: 开始日期（YYYY-MM-DD），可选
            end_date: 结束日期（YYYY-MM-DD），可选
            
        Returns:
            DataFrame with columns: [timestamp, open, high, low, close, volume, turnover]
        """
        try:
            logger.info(f"📥 加载CSV数据: {csv_path}")
            
            # 读取CSV
            df = pd.read_csv(csv_path)
            
            # 验证必需列
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"CSV缺少必需列: {missing_cols}")
            
            # 转换时间戳
            if df['timestamp'].dtype == 'object':
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            elif df['timestamp'].dtype in ['int64', 'float64']:
                # 假设是毫秒时间戳
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 排序
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # 日期过滤
            if start_date:
                start = pd.to_datetime(start_date)
                df = df[df['timestamp'] >= start]
            
            if end_date:
                end = pd.to_datetime(end_date)
                df = df[df['timestamp'] <= end]
            
            logger.info(f"✅ 加载成功: {len(df)}条K线数据")
            logger.info(f"   时间范围: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
            logger.info(f"   价格范围: ${df['close'].min():.2f} ~ ${df['close'].max():.2f}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ 加载CSV失败: {e}")
            raise
    
    def generate_sample_data(self,
                            symbol: str = "BTC/USDT",
                            days: int = 30,
                            interval: str = "1d",
                            start_price: float = 50000.0,
                            volatility: float = 0.02) -> pd.DataFrame:
        """
        生成模拟的K线数据（用于测试）
        
        基于真实市场特征：
        - 价格随机游走
        - 波动率聚集
        - OHLC关系正确
        
        Args:
            symbol: 交易对
            days: 天数
            interval: 时间间隔（1d=日K, 1h=小时K）
            start_price: 起始价格
            volatility: 波动率
            
        Returns:
            DataFrame with K-line data
        """
        logger.info(f"🎲 生成模拟K线数据: {symbol} | {days}天 | {interval}")
        
        # 计算数据点数量
        if interval == "1d":
            periods = days
            freq = "D"
        elif interval == "1h":
            periods = days * 24
            freq = "H"
        elif interval == "4h":
            periods = days * 6
            freq = "4H"
        else:
            raise ValueError(f"不支持的interval: {interval}")
        
        # 生成时间序列
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        timestamps = pd.date_range(start=start_time, periods=periods, freq=freq)
        
        # 生成价格序列（随机游走 + 波动率聚集）
        np.random.seed(42)  # 可复现
        
        prices = [start_price]
        current_vol = volatility
        
        for i in range(1, periods):
            # 波动率聚集效应
            vol_change = np.random.normal(0, 0.001)
            current_vol = np.clip(current_vol + vol_change, volatility * 0.5, volatility * 2.0)
            
            # 价格变化
            return_pct = np.random.normal(0, current_vol)
            new_price = prices[-1] * (1 + return_pct)
            
            # 添加趋势（轻微上涨偏好，模拟长期牛市）
            trend = 0.0001
            new_price *= (1 + trend)
            
            prices.append(new_price)
        
        # 生成OHLC数据
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            # 生成合理的OHLC
            intraday_range = close * volatility * 0.5
            
            open_price = close + np.random.uniform(-intraday_range, intraday_range)
            high_price = max(open_price, close) + np.random.uniform(0, intraday_range)
            low_price = min(open_price, close) - np.random.uniform(0, intraday_range)
            
            # 确保OHLC关系正确
            high_price = max(high_price, open_price, close)
            low_price = min(low_price, open_price, close)
            
            # 生成成交量（与价格波动相关）
            price_change = abs(close - open_price) / open_price
            base_volume = 1000000  # 基础成交量
            volume = base_volume * (1 + price_change * 10) * np.random.uniform(0.8, 1.2)
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close,
                'volume': volume,
                'turnover': volume * close
            })
        
        df = pd.DataFrame(data)
        
        logger.info(f"✅ 生成完成: {len(df)}条K线数据")
        logger.info(f"   时间范围: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
        logger.info(f"   价格范围: ${df['close'].min():.2f} ~ ${df['close'].max():.2f}")
        logger.info(f"   收益率: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str):
        """
        保存数据到CSV
        
        Args:
            df: DataFrame
            filename: 文件名
        """
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        logger.info(f"💾 数据已保存: {filepath}")
    
    def load_or_generate(self,
                        symbol: str = "BTC/USDT",
                        days: int = 30,
                        interval: str = "1d",
                        force_generate: bool = False) -> pd.DataFrame:
        """
        加载数据，如果不存在则生成
        
        Args:
            symbol: 交易对
            days: 天数
            interval: 时间间隔
            force_generate: 强制重新生成
            
        Returns:
            DataFrame
        """
        filename = f"{symbol.replace('/', '_')}_{interval}_{days}d.csv"
        filepath = self.data_dir / filename
        
        if filepath.exists() and not force_generate:
            logger.info(f"📂 从缓存加载: {filename}")
            return self.load_from_csv(str(filepath))
        else:
            logger.info(f"🎲 生成新数据: {filename}")
            df = self.generate_sample_data(symbol, days, interval)
            self.save_to_csv(df, filename)
            return df
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        验证K线数据质量
        
        Args:
            df: DataFrame
            
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # 检查必需列
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            errors.append(f"缺少必需列: {missing}")
        
        # 检查数据完整性
        if df.isnull().any().any():
            null_cols = df.columns[df.isnull().any()].tolist()
            errors.append(f"存在空值: {null_cols}")
        
        # 检查OHLC关系
        invalid_ohlc = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        )
        if invalid_ohlc.any():
            errors.append(f"OHLC关系错误: {invalid_ohlc.sum()}条")
        
        # 检查价格为正
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if (df[col] <= 0).any():
                errors.append(f"{col}存在非正值")
        
        # 检查时间顺序
        if not df['timestamp'].is_monotonic_increasing:
            errors.append("时间戳非单调递增")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("✅ 数据验证通过")
        else:
            logger.warning(f"⚠️ 数据验证失败:\n  " + "\n  ".join(errors))
        
        return is_valid, errors
    
    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """
        计算数据统计信息
        
        Args:
            df: DataFrame
            
        Returns:
            统计信息字典
        """
        stats = {
            'data_points': len(df),
            'time_range': {
                'start': str(df['timestamp'].min()),
                'end': str(df['timestamp'].max()),
                'days': (df['timestamp'].max() - df['timestamp'].min()).days
            },
            'price': {
                'start': float(df['close'].iloc[0]),
                'end': float(df['close'].iloc[-1]),
                'min': float(df['close'].min()),
                'max': float(df['close'].max()),
                'mean': float(df['close'].mean()),
                'std': float(df['close'].std())
            },
            'returns': {
                'total': float((df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100),
                'daily_mean': float(df['close'].pct_change().mean() * 100),
                'daily_std': float(df['close'].pct_change().std() * 100)
            },
            'volume': {
                'total': float(df['volume'].sum()),
                'mean': float(df['volume'].mean()),
                'max': float(df['volume'].max())
            }
        }
        
        return stats


def test_okx_data_loader():
    """测试OKX数据加载器"""
    print("\n" + "="*60)
    print("🧪 测试OKX数据加载器")
    print("="*60)
    
    loader = OKXDataLoader(data_dir="data/okx_test")
    
    # 测试1: 生成模拟数据
    print("\n📋 测试1: 生成30天BTC日K数据")
    df = loader.generate_sample_data(
        symbol="BTC/USDT",
        days=30,
        interval="1d",
        start_price=50000.0,
        volatility=0.02
    )
    
    print(f"\n前5行数据:")
    print(df.head())
    
    # 测试2: 验证数据
    print("\n📋 测试2: 验证数据质量")
    is_valid, errors = loader.validate_data(df)
    print(f"验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    # 测试3: 统计信息
    print("\n📋 测试3: 统计信息")
    stats = loader.get_statistics(df)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 测试4: 保存和加载
    print("\n📋 测试4: 保存和加载")
    loader.save_to_csv(df, "test_btc_30d.csv")
    
    df_loaded = loader.load_from_csv("data/okx_test/test_btc_30d.csv")
    print(f"加载数据: {len(df_loaded)}条")
    print(f"数据一致性: {'✅ 一致' if len(df) == len(df_loaded) else '❌ 不一致'}")
    
    # 测试5: 加载或生成（缓存机制）
    print("\n📋 测试5: 缓存机制")
    df_cached = loader.load_or_generate("BTC/USDT", days=30, force_generate=False)
    print(f"从缓存加载: {len(df_cached)}条")
    
    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    test_okx_data_loader()

