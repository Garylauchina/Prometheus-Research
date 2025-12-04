#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OKX历史数据下载工具

功能：
1. 下载OKX历史K线数据（最多10年）
2. 支持多种时间周期（1m, 5m, 15m, 1h, 4h, 1d）
3. 断点续传
4. 进度显示
5. 保存为CSV和Parquet格式

使用方法：
    python download_okx_data.py --symbol BTC-USDT --period 1h --years 3
"""

import sys
sys.path.insert(0, '..')

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import logging
from typing import Optional, List
import json

logging.basicConfig(
    level=logging.INFO,  # 正常模式
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class OKXDataDownloader:
    """OKX数据下载器"""
    
    BASE_URL = "https://www.okx.com"
    API_ENDPOINT = "/api/v5/market/candles"
    
    # OKX API限制：每次最多300条
    MAX_CANDLES_PER_REQUEST = 300
    
    # 时间周期映射（秒）
    PERIOD_SECONDS = {
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '2h': 7200,
        '4h': 14400,
        '1d': 86400,
        '1w': 604800,
    }
    
    # OKX API时间周期格式映射（需要大写）
    PERIOD_TO_OKX = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1H',   # 需要大写
        '2h': '2H',   # 需要大写
        '4h': '4H',   # 需要大写
        '1d': '1D',   # 需要大写
        '1w': '1W',   # 需要大写
    }
    
    def __init__(self, data_dir: str = "data/okx"):
        """
        初始化下载器
        
        Args:
            data_dir: 数据保存目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"数据保存目录: {self.data_dir.absolute()}")
    
    def download_historical_data(
        self,
        symbol: str = "BTC-USDT",
        period: str = "1h",
        years: int = 3,
        force_redownload: bool = False
    ) -> pd.DataFrame:
        """
        下载历史数据
        
        Args:
            symbol: 交易对（如BTC-USDT）
            period: 时间周期（1m, 5m, 15m, 1h, 4h, 1d等）
            years: 下载年数（最多10年）
            force_redownload: 是否强制重新下载
        
        Returns:
            pd.DataFrame: 历史数据
        """
        logger.info("="*80)
        logger.info(f"开始下载 {symbol} {period} K线数据（最近{years}年）")
        logger.info("="*80)
        
        # 检查是否已存在
        csv_file = self.data_dir / f"{symbol.replace('-', '_')}_{period}_{years}y.csv"
        parquet_file = self.data_dir / f"{symbol.replace('-', '_')}_{period}_{years}y.parquet"
        
        if not force_redownload and csv_file.exists():
            logger.info(f"数据文件已存在: {csv_file}")
            logger.info("使用 --force 参数强制重新下载")
            df = pd.read_csv(csv_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            logger.info(f"读取完成: {len(df)}条数据")
            return df
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=365 * years)
        
        logger.info(f"时间范围: {start_time} 至 {end_time}")
        
        # 估算需要的请求次数
        period_seconds = self.PERIOD_SECONDS[period]
        total_seconds = (end_time - start_time).total_seconds()
        estimated_candles = int(total_seconds / period_seconds)
        estimated_requests = (estimated_candles // self.MAX_CANDLES_PER_REQUEST) + 1
        
        logger.info(f"预计K线数: {estimated_candles:,}")
        logger.info(f"预计请求数: {estimated_requests:,}")
        logger.info(f"预计耗时: {estimated_requests * 0.5:.1f}秒（0.5秒/请求）")
        
        # 分批下载
        all_data = []
        current_after = None  # 第一次不传after，获取最新数据
        request_count = 0
        max_retries = 3  # 最大重试次数
        max_requests = estimated_requests * 3  # 最大请求次数（防止无限循环）
        
        while True:
            # 重试机制
            for retry in range(max_retries):
                try:
                    # 调用API（使用after参数查询历史数据）
                    data = self._fetch_candles(symbol, period, after=current_after)
                    break  # 成功则跳出重试循环
                except Exception as e:
                    if retry < max_retries - 1:
                        logger.warning(f"请求失败，{3-retry}秒后重试... ({retry+1}/{max_retries})")
                        time.sleep(3)
                    else:
                        raise  # 最后一次重试失败，抛出异常
            
            try:
                
                if not data:
                    logger.info(f"没有更多数据 (请求#{request_count + 1}, after={current_after})")
                    break
                
                # 调试：检查数据顺序
                if request_count == 0:
                    first_ts = datetime.fromtimestamp(int(data[0][0]) / 1000)
                    last_ts = datetime.fromtimestamp(int(data[-1][0]) / 1000)
                    logger.info(f"📊 数据顺序检查: 第一条={first_ts} | 最后一条={last_ts}")
                    logger.info(f"   {'✅ 倒序(新→旧)' if first_ts > last_ts else '❌ 正序(旧→新)'}")
                
                logger.debug(f"获取到 {len(data)} 条数据 (请求#{request_count + 1})")
                
                all_data.extend(data)
                request_count += 1
                
                # 检查是否超过最大请求次数
                if request_count >= max_requests:
                    logger.warning(f"⚠️  达到最大请求次数限制({max_requests})，停止下载")
                    logger.warning(f"   这可能表明时间推进有问题，请检查日志")
                    break
                
                # 更新进度
                if request_count % 10 == 0:
                    latest_dt = datetime.fromtimestamp(int(data[0][0]) / 1000)
                    earliest_dt_temp = datetime.fromtimestamp(int(data[-1][0]) / 1000)
                    logger.info(f"已下载: {len(all_data):,}条数据 ({request_count}/{estimated_requests}请求) | 时间范围: {earliest_dt_temp} ~ {latest_dt}")
                
                # 获取最早的时间戳
                earliest_ts = int(data[-1][0])  # OKX返回的数据是倒序的
                earliest_dt = datetime.fromtimestamp(earliest_ts / 1000)
                
                # 获取最新的时间戳（用于调试）
                latest_ts = int(data[0][0])
                latest_dt = datetime.fromtimestamp(latest_ts / 1000)
                
                # 调试：显示时间推进
                if request_count <= 3:  # 前3次请求详细输出
                    logger.info(f"🔍 请求#{request_count} 返回数据:")
                    logger.info(f"   数量: {len(data)}")
                    logger.info(f"   时间范围: {earliest_dt} ~ {latest_dt}")
                    logger.info(f"   最旧时间戳: {earliest_ts}")
                    logger.info(f"   下次after: {earliest_ts}")
                
                # 检查是否已达到起始时间
                if earliest_dt <= start_time:
                    logger.info(f"已达到起始时间: {earliest_dt}")
                    break
                
                # 更新下一次请求的after参数（使用最旧时间戳获取更早的数据）
                current_after = earliest_ts
                
                # 避免请求过快（OKX限制：20次/2秒）
                time.sleep(0.1)  # 加快速度：0.1秒/请求
                
            except Exception as e:
                logger.error(f"下载出错: {e}")
                logger.info(f"已下载{len(all_data)}条数据，尝试保存...")
                break
        
        # 转换为DataFrame
        df = self._convert_to_dataframe(all_data)
        
        # 去重（按时间戳）
        df = df.drop_duplicates(subset=['timestamp'], keep='first')
        
        # 过滤时间范围
        df = df[df['timestamp'] >= start_time]
        
        # 排序（按时间升序）
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"\n✅ 下载完成: {len(df):,}条数据")
        logger.info(f"   时间范围: {df['timestamp'].min()} 至 {df['timestamp'].max()}")
        logger.info(f"   价格范围: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        
        # 保存数据
        self._save_data(df, csv_file, parquet_file)
        
        return df
    
    def _fetch_candles(
        self,
        symbol: str,
        period: str,
        after: Optional[int] = None
    ) -> List:
        """
        调用OKX API获取K线数据
        
        Args:
            symbol: 交易对
            period: 时间周期
            after: 结束时间戳（毫秒）- 查询此时间之后（更早）的数据
        
        Returns:
            List: K线数据
        """
        url = f"{self.BASE_URL}{self.API_ENDPOINT}"
        
        # 转换为OKX格式（大写）
        okx_period = self.PERIOD_TO_OKX.get(period, period)
        
        params = {
            'instId': symbol,
            'bar': okx_period,  # 使用OKX格式
            'limit': self.MAX_CANDLES_PER_REQUEST,
        }
        
        if after:
            params['after'] = after
        
        logger.debug(f"API请求: {url} | params={params}")
        
        response = requests.get(url, params=params, timeout=30)  # 增加超时时间
        response.raise_for_status()
        
        result = response.json()
        
        if result['code'] != '0':
            raise Exception(f"API错误: {result.get('msg', 'Unknown error')}")
        
        logger.debug(f"API返回: {len(result.get('data', []))} 条数据")
        
        return result['data']
    
    def _convert_to_dataframe(self, data: List) -> pd.DataFrame:
        """
        转换为DataFrame
        
        OKX返回格式：
        [timestamp, open, high, low, close, volume, volumeCcy, volumeCcyQuote, confirm]
        
        Args:
            data: 原始数据
        
        Returns:
            pd.DataFrame: 格式化的数据
        """
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close',
            'volume', 'volume_ccy', 'volume_quote', 'confirm'
        ])
        
        # 转换数据类型
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['volume_quote'] = df['volume_quote'].astype(float)
        
        # 删除不需要的列
        df = df.drop(['volume_ccy', 'confirm'], axis=1)
        
        return df
    
    def _save_data(
        self,
        df: pd.DataFrame,
        csv_file: Path,
        parquet_file: Path
    ):
        """
        保存数据
        
        Args:
            df: 数据
            csv_file: CSV文件路径
            parquet_file: Parquet文件路径
        """
        # 保存CSV（方便查看）
        df.to_csv(csv_file, index=False)
        logger.info(f"\n💾 CSV已保存: {csv_file}")
        logger.info(f"   文件大小: {csv_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        # 保存Parquet（节省空间，读取快）- 可选
        try:
            df.to_parquet(parquet_file, index=False)
            logger.info(f"\n💾 Parquet已保存: {parquet_file}")
            logger.info(f"   文件大小: {parquet_file.stat().st_size / 1024 / 1024:.2f} MB")
        except Exception as e:
            logger.warning(f"\n⚠️  Parquet保存失败: {e}")
            logger.warning(f"   提示: pip install pyarrow")
            logger.info(f"   CSV文件已保存，可正常使用")
        
        # 保存元数据
        metadata = {
            'symbol': csv_file.stem.rsplit('_', 2)[0],
            'period': csv_file.stem.rsplit('_', 2)[1],
            'start_time': df['timestamp'].min().isoformat(),
            'end_time': df['timestamp'].max().isoformat(),
            'num_candles': len(df),
            'price_range': {
                'min': float(df['low'].min()),
                'max': float(df['high'].max()),
            },
            'download_time': datetime.now().isoformat(),
        }
        
        metadata_file = csv_file.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"📋 元数据已保存: {metadata_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='OKX历史数据下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 下载BTC-USDT最近3年的1小时K线
  python download_okx_data.py --symbol BTC-USDT --period 1h --years 3
  
  # 下载ETH-USDT最近1年的15分钟K线
  python download_okx_data.py --symbol ETH-USDT --period 15m --years 1
  
  # 强制重新下载
  python download_okx_data.py --symbol BTC-USDT --period 1h --years 3 --force

支持的时间周期：
  1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w
        """
    )
    
    parser.add_argument(
        '--symbol',
        default='BTC-USDT',
        help='交易对（默认：BTC-USDT）'
    )
    
    parser.add_argument(
        '--period',
        default='1h',
        choices=['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w'],
        help='时间周期（默认：1h）'
    )
    
    parser.add_argument(
        '--years',
        type=int,
        default=3,
        help='下载年数（默认：3年，最多10年）'
    )
    
    parser.add_argument(
        '--data-dir',
        default='../data/okx',
        help='数据保存目录（默认：../data/okx）'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新下载（覆盖已存在的数据）'
    )
    
    args = parser.parse_args()
    
    # 创建下载器
    downloader = OKXDataDownloader(data_dir=args.data_dir)
    
    # 下载数据
    df = downloader.download_historical_data(
        symbol=args.symbol,
        period=args.period,
        years=min(args.years, 10),  # 最多10年
        force_redownload=args.force
    )
    
    # 显示统计信息
    print("\n" + "="*80)
    print("📊 数据统计")
    print("="*80)
    print(f"\n数据预览（前5条）:")
    print(df.head())
    print(f"\n基本统计:")
    print(df.describe())
    
    print("\n" + "="*80)
    print("✅ 完成！数据已保存到本地，可用于后续测试和回测")
    print("="*80)


if __name__ == "__main__":
    main()

