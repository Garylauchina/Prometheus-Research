#!/usr/bin/env python3
"""
📥 OKX历史数据下载工具（使用CCXT库）

使用专业的CCXT库连接OKX，更稳定可靠
"""

import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class OKXDataDownloaderCCXT:
    """OKX数据下载器（使用CCXT）"""
    
    def __init__(self, output_dir: str = "data/okx"):
        """初始化"""
        self.exchange = ccxt.okx({'enableRateLimit': True})
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📥 OKX数据下载器初始化（CCXT版本）")
        logger.info(f"   输出目录: {self.output_dir}")
        logger.info(f"   交易所: {self.exchange.name}")
    
    def download_klines(self, symbol: str = "BTC/USDT", timeframe: str = "1d", days: int = 1000, max_requests: int = 50):
        """
        下载K线数据（循环下载，尽可能多）
        
        Args:
            symbol: 交易对（BTC/USDT）
            timeframe: 时间周期（1m, 5m, 15m, 1h, 4h, 1d）
            days: 目标天数
            max_requests: 最大请求次数（防止无限循环）
        """
        logger.info(f"\n📊 开始下载 {symbol} {timeframe} K线数据")
        logger.info(f"   目标天数: {days}天")
        logger.info(f"   最大请求次数: {max_requests}次")
        
        all_data = []
        
        # 从当前时间开始往前下载
        since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        limit = 100  # 每次请求100条（OKX稳定支持）
        request_count = 0
        
        while request_count < max_requests:
            try:
                request_count += 1
                
                # 获取数据
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    since=since,
                    limit=limit
                )
                
                if not ohlcv:
                    logger.info(f"   第{request_count}次请求: 无数据，停止")
                    break
                
                # 检查是否有重复数据
                new_count = 0
                for candle in ohlcv:
                    if candle not in all_data:
                        all_data.append(candle)
                        new_count += 1
                
                # 显示进度
                if request_count % 5 == 0 or new_count == 0:
                    logger.info(f"   请求{request_count}: +{new_count}条，总计{len(all_data)}条")
                
                # 如果没有新数据，说明到头了
                if new_count == 0:
                    logger.info(f"   ✅ 已到达最早数据（请求{request_count}次）")
                    break
                
                # 更新since为最后一条数据的时间戳+1
                since = ohlcv[-1][0] + 1
                
                # 如果返回的数据少于limit，可能接近最早数据
                if len(ohlcv) < limit:
                    logger.info(f"   ⚠️ 返回数据<{limit}条，可能接近最早数据")
                    # 但继续尝试
                
                # 避免请求过快（OKX限制：20次/2秒）
                time.sleep(0.15)
                
            except Exception as e:
                logger.error(f"❌ 第{request_count}次请求出错: {e}")
                break
        
        if not all_data:
            logger.error("❌ 未获取到数据")
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # 去重并排序
        df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"✅ 下载完成: {len(df)}条K线")
        logger.info(f"   时间范围: {df['timestamp'].min()} 至 {df['timestamp'].max()}")
        logger.info(f"   实际天数: {(df['timestamp'].max() - df['timestamp'].min()).days}天")
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """保存数据"""
        if df is None or df.empty:
            logger.error("❌ 无数据可保存")
            return None
        
        # 生成文件名
        symbol_clean = symbol.replace('/', '_')
        filename = f"{symbol_clean}_{timeframe}_{datetime.now().strftime('%Y%m%d')}.csv"
        filepath = self.output_dir / filename
        
        # 保存
        df.to_csv(filepath, index=False)
        
        file_size = filepath.stat().st_size / 1024
        logger.info(f"💾 已保存: {filepath}")
        logger.info(f"   文件大小: {file_size:.2f} KB")
        logger.info(f"   数据条数: {len(df)}条")
        
        return filepath


def main():
    """主函数"""
    logger.info("\n" + "="*80)
    logger.info("📥 OKX历史数据下载工具（CCXT版本）")
    logger.info("="*80)
    
    try:
        # 初始化
        downloader = OKXDataDownloaderCCXT(output_dir="data/okx")
        
        # 下载计划（尽可能多的历史数据）
        plans = [
            {"timeframe": "1d", "days": 2000, "max_requests": 100, "desc": "日线数据（尽可能多，最多10000条）"},
            {"timeframe": "4h", "days": 730, "max_requests": 100, "desc": "4小时线（尽可能多，最多10000条）"},
            {"timeframe": "1h", "days": 365, "max_requests": 100, "desc": "1小时线（尽可能多，最多10000条）"},
        ]
        
        logger.info("\n📋 下载计划:")
        for i, p in enumerate(plans, 1):
            logger.info(f"   {i}. {p['desc']}")
        
        results = []
        
        for i, plan in enumerate(plans, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"📥 任务 {i}/{len(plans)}: {plan['desc']}")
            logger.info(f"{'='*80}")
            
            try:
                df = downloader.download_klines(
                    symbol="BTC/USDT",
                    timeframe=plan['timeframe'],
                    days=plan['days'],
                    max_requests=plan.get('max_requests', 50)
                )
                
                if df is not None:
                    filepath = downloader.save_to_csv(df, "BTC/USDT", plan['timeframe'])
                    results.append({'timeframe': plan['timeframe'], 'success': True, 'filepath': filepath})
                else:
                    results.append({'timeframe': plan['timeframe'], 'success': False})
                
                if i < len(plans):
                    logger.info("\n⏸️  休息2秒...")
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ 任务失败: {e}")
                results.append({'timeframe': plan['timeframe'], 'success': False, 'error': str(e)})
        
        # 总结
        logger.info("\n" + "="*80)
        logger.info("📊 下载任务总结")
        logger.info("="*80)
        
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"\n✅ 成功: {success_count}/{len(results)}")
        
        for r in results:
            icon = "✅" if r['success'] else "❌"
            logger.info(f"\n{icon} {r['timeframe']}:")
            if r['success']:
                logger.info(f"   文件: {r['filepath']}")
            elif 'error' in r:
                logger.info(f"   错误: {r['error']}")
        
        logger.info("\n" + "="*80)
        logger.info("✅ 所有任务完成！")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

