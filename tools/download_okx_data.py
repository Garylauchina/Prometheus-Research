#!/usr/bin/env python3
"""
📥 OKX历史数据下载工具

功能：
1. 下载BTC/USDT历史K线数据
2. 支持多种时间周期（1h, 4h, 1d）
3. 自动分批下载，避免API限制
4. 保存为CSV格式，便于分析

使用OKX公开API，无需API key
"""

import requests
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


class OKXDataDownloader:
    """OKX数据下载器"""
    
    def __init__(self, output_dir: str = "data/okx"):
        """
        初始化下载器
        
        Args:
            output_dir: 数据输出目录
        """
        self.base_url = "https://www.okx.com/api/v5/market/history-candles"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📥 OKX数据下载器初始化")
        logger.info(f"   输出目录: {self.output_dir}")
    
    def download_klines(self, 
                       symbol: str = "BTC-USDT",
                       interval: str = "1D",
                       days: int = 1000,
                       limit: int = 100):
        """
        下载K线数据
        
        Args:
            symbol: 交易对（如BTC-USDT）
            interval: 时间周期（1m, 5m, 15m, 1H, 4H, 1D）
            days: 下载多少天的历史数据
            limit: 每次请求的K线数量（最大100）
            
        Returns:
            DataFrame包含K线数据
        """
        logger.info(f"\n📊 开始下载 {symbol} {interval} K线数据")
        logger.info(f"   目标天数: {days}天")
        
        all_data = []
        end_time = int(datetime.now().timestamp() * 1000)  # 当前时间（毫秒）
        
        # 计算需要请求多少次
        if interval == "1D":
            total_requests = (days + limit - 1) // limit
        elif interval == "4H":
            total_requests = (days * 6 + limit - 1) // limit
        elif interval == "1H":
            total_requests = (days * 24 + limit - 1) // limit
        else:
            total_requests = 10  # 默认
        
        logger.info(f"   预计请求次数: {total_requests}")
        
        for i in range(total_requests):
            try:
                # 构建请求参数
                params = {
                    'instId': symbol,
                    'bar': interval,
                    'before': end_time,
                    'limit': limit
                }
                
                # 发送请求
                response = requests.get(self.base_url, params=params, timeout=10)
                
                if response.status_code != 200:
                    logger.error(f"❌ 请求失败: {response.status_code}")
                    logger.error(f"   响应: {response.text[:200]}")
                    break
                
                data = response.json()
                
                if data['code'] != '0':
                    logger.error(f"❌ API错误: {data.get('msg', 'Unknown error')}")
                    logger.error(f"   完整响应: {data}")
                    break
                
                klines = data.get('data', [])
                
                # 第一次请求，显示调试信息
                if i == 0:
                    logger.info(f"   首次请求返回{len(klines) if klines else 0}条数据")
                    if not klines:
                        logger.error(f"   响应详情: {data}")
                
                if not klines:
                    if i == 0:
                        logger.error("❌ 首次请求无数据")
                    else:
                        logger.info("✅ 已到达最早数据")
                    break
                
                all_data.extend(klines)
                
                # 更新end_time为当前批次最早的时间
                end_time = int(klines[-1][0])
                
                # 进度显示
                if (i + 1) % 10 == 0:
                    logger.info(f"   已下载: {len(all_data)}条 ({i+1}/{total_requests})")
                
                # 避免请求过快
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"❌ 下载出错: {e}")
                break
        
        if not all_data:
            logger.error("❌ 未获取到数据")
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'volume_currency', 'volume_quote', 'confirm'
        ])
        
        # 数据类型转换
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # 按时间排序（从旧到新）
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"✅ 下载完成: {len(df)}条K线")
        logger.info(f"   时间范围: {df['timestamp'].min()} 至 {df['timestamp'].max()}")
        logger.info(f"   实际天数: {(df['timestamp'].max() - df['timestamp'].min()).days}天")
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, symbol: str, interval: str):
        """
        保存数据到CSV
        
        Args:
            df: K线数据DataFrame
            symbol: 交易对
            interval: 时间周期
        """
        if df is None or df.empty:
            logger.error("❌ 无数据可保存")
            return
        
        # 生成文件名
        filename = f"{symbol.replace('-', '_')}_{interval}_{datetime.now().strftime('%Y%m%d')}.csv"
        filepath = self.output_dir / filename
        
        # 保存
        df.to_csv(filepath, index=False)
        
        file_size = filepath.stat().st_size / 1024  # KB
        logger.info(f"💾 已保存: {filepath}")
        logger.info(f"   文件大小: {file_size:.2f} KB")
        logger.info(f"   数据条数: {len(df)}条")
        
        return filepath
    
    def download_and_save(self, symbol: str = "BTC-USDT", interval: str = "1D", days: int = 1000):
        """
        下载并保存数据（一体化）
        
        Args:
            symbol: 交易对
            interval: 时间周期
            days: 天数
        """
        df = self.download_klines(symbol=symbol, interval=interval, days=days)
        if df is not None:
            return self.save_to_csv(df, symbol, interval)
        return None


def main():
    """主函数"""
    logger.info("\n" + "="*80)
    logger.info("📥 OKX历史数据下载工具")
    logger.info("="*80)
    logger.info("🎯 目标：下载BTC/USDT历史K线数据")
    logger.info("📊 数据源：OKX公开API（无需API key）")
    logger.info("="*80 + "\n")
    
    # 初始化下载器
    downloader = OKXDataDownloader(output_dir="data/okx")
    
    # 下载计划
    download_plan = [
        {"interval": "1D", "days": 1000, "desc": "日线数据（约3年）"},
        {"interval": "4H", "days": 365, "desc": "4小时线（1年）"},
        {"interval": "1H", "days": 180, "desc": "1小时线（半年）"},
    ]
    
    logger.info("📋 下载计划:")
    for i, plan in enumerate(download_plan, 1):
        logger.info(f"   {i}. {plan['desc']} - {plan['interval']}")
    
    logger.info("\n🚀 开始下载...\n")
    
    results = []
    
    for i, plan in enumerate(download_plan, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"📥 任务 {i}/{len(download_plan)}")
        logger.info(f"{'='*80}")
        
        try:
            filepath = downloader.download_and_save(
                symbol="BTC-USDT",
                interval=plan['interval'],
                days=plan['days']
            )
            
            if filepath:
                results.append({
                    'interval': plan['interval'],
                    'filepath': filepath,
                    'status': 'success'
                })
            else:
                results.append({
                    'interval': plan['interval'],
                    'filepath': None,
                    'status': 'failed'
                })
            
            # 任务间休息
            if i < len(download_plan):
                logger.info("\n⏸️  休息3秒...")
                time.sleep(3)
                
        except Exception as e:
            logger.error(f"❌ 任务失败: {e}")
            results.append({
                'interval': plan['interval'],
                'filepath': None,
                'status': 'error',
                'error': str(e)
            })
    
    # 总结
    logger.info("\n" + "="*80)
    logger.info("📊 下载任务总结")
    logger.info("="*80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    
    logger.info(f"\n✅ 成功: {success_count}/{len(results)}")
    
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        logger.info(f"\n{status_icon} {result['interval']}:")
        if result['status'] == 'success':
            logger.info(f"   文件: {result['filepath']}")
        else:
            logger.info(f"   状态: {result['status']}")
            if 'error' in result:
                logger.info(f"   错误: {result['error']}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ 所有下载任务完成！")
    logger.info("="*80)
    
    # 使用建议
    logger.info("\n💡 使用建议:")
    logger.info("   1. 日线数据（1D）: 适合长期回测（365天+）")
    logger.info("   2. 4小时线（4H）: 适合中期策略验证")
    logger.info("   3. 1小时线（1H）: 适合短期高频测试")
    logger.info("\n   加载数据:")
    logger.info("   ```python")
    logger.info("   import pandas as pd")
    logger.info("   df = pd.read_csv('data/okx/BTC_USDT_1D_20251206.csv')")
    logger.info("   ```")
    
    logger.info("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
