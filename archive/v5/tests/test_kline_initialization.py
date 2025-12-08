#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本：验证创世阶段是否成功获取100条K线数据

这个脚本用于测试在系统初始化阶段是否能正确获取100条K线数据，并验证数据质量。
"""

import os
import sys
import logging
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_kline_init.log')
    ]
)

logger = logging.getLogger('test_kline_initialization')

# 测试环境配置
test_config = {
    'api_key': 'your_api_key',  # 实际测试时请替换为有效的API密钥
    'secret_key': 'your_secret_key',
    'passphrase': 'your_passphrase',
    'flag': '1',  # 模拟盘
    'max_retries': 3,
    'retry_base_delay': 1.0
}

def test_okx_adapter_kline_retrieval():
    """
    测试OKXTradingAdapter的get_candles方法是否能正确获取100条K线数据
    """
    logger.info("开始测试OKXTradingAdapter的K线数据获取...")
    
    try:
        from adapters.okx_adapter import OKXTradingAdapter
        
        # 初始化适配器
        adapter = OKXTradingAdapter(test_config)
        
        # 测试的交易对列表
        test_symbols = ['BTC-USDT', 'ETH-USDT']
        test_intervals = ['1H', '4H']
        
        for symbol in test_symbols:
            for interval in test_intervals:
                logger.info(f"测试获取 {symbol} {interval} K线数据，请求100条...")
                start_time = time.time()
                
                # 调用get_candles方法
                candles = adapter.get_candles(symbol, bar=interval, limit=100)
                
                # 检查结果
                elapsed_time = time.time() - start_time
                
                if not candles:
                    logger.error(f"错误: 未获取到{symbol} {interval}的K线数据")
                    continue
                
                logger.info(f"成功获取到{symbol} {interval}的K线数据，耗时{elapsed_time:.2f}秒")
                logger.info(f"获取到的K线数量: {len(candles)}")
                
                # 验证K线数量
                if len(candles) == 100:
                    logger.info(f"✓ 成功: {symbol} {interval} 获取到预期的100条K线数据")
                elif len(candles) > 0:
                    logger.warning(f"⚠️  警告: {symbol} {interval} 获取到{len(candles)}条K线数据，少于预期的100条")
                else:
                    logger.error(f"✗ 失败: {symbol} {interval} 未获取到任何K线数据")
                
                # 验证数据质量
                if candles:
                    logger.info(f"第一条K线数据时间戳: {candles[0][0]}")
                    logger.info(f"最后一条K线数据时间戳: {candles[-1][0]}")
                    logger.info(f"最新K线OHLC: {candles[-1][1:5]}")
                    
                # 延迟一段时间再请求下一个，避免触发API限流
                time.sleep(2)
                
    except Exception as e:
        logger.error(f"测试OKXTradingAdapter时发生异常: {e}", exc_info=True)
    
    logger.info("OKXTradingAdapter K线数据获取测试完成")

def test_market_data_manager_kline_retrieval():
    """
    直接测试MarketDataManager的get_candles方法
    """
    logger.info("开始测试MarketDataManager的K线数据获取...")
    
    try:
        from adapters.market_data import MarketDataManager
        
        # 初始化市场数据管理器
        market_data = MarketDataManager(test_config)
        
        # 测试的交易对列表
        test_symbols = ['BTC-USDT', 'ETH-USDT']
        
        for symbol in test_symbols:
            logger.info(f"直接测试获取 {symbol} 1H K线数据，请求100条...")
            start_time = time.time()
            
            # 直接调用get_candles方法
            candles = market_data.get_candles(symbol, bar='1H', limit=100)
            
            # 检查结果
            elapsed_time = time.time() - start_time
            
            if not candles:
                logger.error(f"错误: 未获取到{symbol}的K线数据")
                continue
            
            logger.info(f"成功获取到{symbol}的K线数据，耗时{elapsed_time:.2f}秒")
            logger.info(f"获取到的K线数量: {len(candles)}")
            
            # 验证K线数量
            if len(candles) == 100:
                logger.info(f"✓ 成功: {symbol} 获取到预期的100条K线数据")
            elif len(candles) > 0:
                logger.warning(f"⚠️  警告: {symbol} 获取到{len(candles)}条K线数据，少于预期的100条")
            else:
                logger.error(f"✗ 失败: {symbol} 未获取到任何K线数据")
                
            # 延迟一段时间再请求下一个，避免触发API限流
            time.sleep(2)
            
    except Exception as e:
        logger.error(f"测试MarketDataManager时发生异常: {e}", exc_info=True)
    
    logger.info("MarketDataManager K线数据获取测试完成")

def simulate_live_trading_system_initialization():
    """
    模拟LiveTradingSystem的初始化过程，验证创世阶段的K线数据获取
    """
    logger.info("开始模拟LiveTradingSystem的初始化过程...")
    
    try:
        from adapters.okx_adapter import OKXTradingAdapter
        
        # 初始化适配器
        adapter = OKXTradingAdapter(test_config)
        
        # 模拟LiveTradingSystem的_get_market_data方法调用
        logger.info("模拟_get_market_data方法调用...")
        
        # 模拟获取BTC-USDT的K线数据
        spot_symbol = 'BTC-USDT'
        logger.info(f"获取{spot_symbol} 1H K线数据 (limit=100)...")
        
        # 记录开始时间
        start_time = time.time()
        
        # 调用适配器的get_candles方法，与LiveTradingSystem中的调用方式一致
        candles = adapter.get_candles(spot_symbol, bar='1H', limit=100)
        
        # 记录结束时间
        elapsed_time = time.time() - start_time
        
        # 检查结果
        logger.info(f"模拟创世阶段获取K线数据完成，耗时{elapsed_time:.2f}秒")
        logger.info(f"获取到的K线数量: {len(candles)}")
        
        if len(candles) == 100:
            logger.info(f"✓ 成功: 创世阶段成功获取到预期的100条K线数据")
        else:
            logger.warning(f"⚠️  警告: 创世阶段获取到{len(candles)}条K线数据，少于预期的100条")
            
        # 验证数据质量
        if candles:
            first_ts = datetime.fromtimestamp(int(candles[0][0]) / 1000).strftime('%Y-%m-%d %H:%M:%S')
            last_ts = datetime.fromtimestamp(int(candles[-1][0]) / 1000).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"数据时间范围: {first_ts} 到 {last_ts}")
            logger.info(f"最新K线数据: {candles[-1]}")
            
    except Exception as e:
        logger.error(f"模拟LiveTradingSystem初始化时发生异常: {e}", exc_info=True)
    
    logger.info("LiveTradingSystem初始化模拟测试完成")

def main():
    """
    主测试函数
    """
    logger.info("======== 开始K线初始化测试 ========")
    
    # 运行各项测试
    test_market_data_manager_kline_retrieval()
    logger.info("\n")
    test_okx_adapter_kline_retrieval()
    logger.info("\n")
    simulate_live_trading_system_initialization()
    
    logger.info("======== K线初始化测试完成 ========")

if __name__ == "__main__":
    main()
