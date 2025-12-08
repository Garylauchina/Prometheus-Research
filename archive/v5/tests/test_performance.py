"""
性能测试脚本 - 用于测试Prometheus v3.0的性能优化功能
"""

import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# 添加当前目录到路径
sys.path.insert(0, os.path.abspath('.'))

from live_trading_system import LiveTradingSystem
from config_virtual import CONFIG_VIRTUAL_TRADING

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PerformanceTest")


def setup_performance_test_config():
    """
    设置性能测试的配置
    """
    config = CONFIG_VIRTUAL_TRADING.copy()
    
    # 配置性能测试专用参数
    config['performance_test'] = True
    config['performance_metrics_enabled'] = True
    config['max_agents'] = 20  # 增加代理数量以测试并发性能
    config['api_call_limit_per_minute'] = 300  # 设置较高的API调用限制
    config['cache_ttl_seconds'] = 5  # 较短的缓存TTL以测试缓存刷新
    config['concurrent_agents_threshold'] = 10  # 较低的并发阈值以更容易触发并发模式
    
    # 减少每个循环的休眠时间以加速测试
    config['trading_interval_seconds'] = 2
    
    return config


def run_performance_test(duration_seconds=300):
    """
    运行性能测试
    """
    logger.info("="*80)
    logger.info(f"开始性能测试 - 持续时间: {duration_seconds}秒")
    logger.info("="*80)
    
    # 设置测试配置
    config = setup_performance_test_config()
    okx_config = config['okx_api'].copy()
    okx_config['risk_config'] = config['risk']
    
    # 验证API凭证
    if not all([okx_config['api_key'], okx_config['secret_key'], okx_config['passphrase']]):
        logger.error("在config_virtual.py中未找到OKX API凭证")
        return False
    
    try:
        # 创建交易系统
        system = LiveTradingSystem(config, okx_config)
        
        # 记录开始时间
        start_time = time.time()
        
        # 运行交易系统
        system.run(duration_seconds=duration_seconds)
        
        # 记录结束时间
        end_time = time.time()
        actual_duration = end_time - start_time
        
        logger.info("="*80)
        logger.info(f"性能测试完成")
        logger.info(f"实际运行时间: {actual_duration:.2f}秒")
        
        # 收集性能统计数据
        performance_stats = {
            'total_api_calls': system._total_api_calls,
            'throttled_api_calls': system._throttled_api_calls,
            'cache_hits': system._cache_hits,
            'cache_misses': system._cache_misses,
            'avg_agent_update_time': system._avg_agent_update_time,
            'avg_order_execution_time': system._avg_order_execution_time,
            'concurrent_updates': system._concurrent_updates_count,
            'serial_updates': system._serial_updates_count,
            'batch_trades_executed': system._batch_trades_executed,
            'total_trades': system._total_trades_executed
        }
        
        # 打印性能统计
        logger.info("\n性能统计:")
        for key, value in performance_stats.items():
            logger.info(f"  {key}: {value}")
        
        # 保存性能数据
        with open(f"performance_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(performance_stats, f, indent=2)
        
        # 生成性能报告
        generate_performance_report(performance_stats, actual_duration)
        
        # 验证性能优化功能是否正常工作
        validate_performance_optimizations(performance_stats)
        
        return True
        
    except Exception as e:
        logger.error(f"性能测试失败: {e}", exc_info=True)
        return False


def generate_performance_report(performance_stats, duration):
    """
    生成性能报告
    """
    try:
        # 计算每秒的API调用次数
        api_calls_per_second = performance_stats['total_api_calls'] / duration
        
        # 计算缓存命中率
        cache_hit_rate = (performance_stats['cache_hits'] / 
                         (performance_stats['cache_hits'] + performance_stats['cache_misses']) * 100) if \
                         (performance_stats['cache_hits'] + performance_stats['cache_misses']) > 0 else 0
        
        # 计算并发率
        total_updates = performance_stats['concurrent_updates'] + performance_stats['serial_updates']
        concurrent_rate = (performance_stats['concurrent_updates'] / total_updates * 100) if total_updates > 0 else 0
        
        logger.info("\n性能分析报告:")
        logger.info(f"  API调用频率: {api_calls_per_second:.2f} 次/秒")
        logger.info(f"  缓存命中率: {cache_hit_rate:.2f}%")
        logger.info(f"  并发更新比例: {concurrent_rate:.2f}%")
        logger.info(f"  平均代理更新时间: {performance_stats['avg_agent_update_time']:.4f} 秒")
        logger.info(f"  平均订单执行时间: {performance_stats['avg_order_execution_time']:.4f} 秒")
        
        # 尝试生成图表
        try:
            # 创建数据框架
            df = pd.DataFrame([performance_stats])
            
            # 创建图表目录
            os.makedirs('performance_charts', exist_ok=True)
            
            # 绘制API调用统计
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            # API调用统计
            api_data = [
                performance_stats['total_api_calls'],
                performance_stats['throttled_api_calls']
            ]
            axes[0, 0].bar(['总API调用', '限流API调用'], api_data)
            axes[0, 0].set_title('API调用统计')
            axes[0, 0].set_ylabel('次数')
            
            # 缓存统计
            cache_data = [
                performance_stats['cache_hits'],
                performance_stats['cache_misses']
            ]
            axes[0, 1].pie(cache_data, labels=['缓存命中', '缓存未命中'], autopct='%1.1f%%')
            axes[0, 1].set_title('缓存命中率')
            
            # 更新模式统计
            update_data = [
                performance_stats['concurrent_updates'],
                performance_stats['serial_updates']
            ]
            axes[1, 0].pie(update_data, labels=['并发更新', '串行更新'], autopct='%1.1f%%')
            axes[1, 0].set_title('代理更新模式分布')
            
            # 交易统计
            trade_data = [
                performance_stats['batch_trades_executed'],
                performance_stats['total_trades']
            ]
            axes[1, 1].bar(['批量交易批次', '总交易次数'], trade_data)
            axes[1, 1].set_title('交易执行统计')
            axes[1, 1].set_ylabel('次数')
            
            plt.tight_layout()
            chart_file = f"performance_charts/performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_file)
            logger.info(f"性能图表已保存到: {chart_file}")
            
        except Exception as e:
            logger.warning(f"无法生成性能图表: {e}")
            
    except Exception as e:
        logger.error(f"生成性能报告时出错: {e}")


def validate_performance_optimizations(performance_stats):
    """
    验证性能优化功能是否正常工作
    """
    logger.info("\n性能优化功能验证:")
    
    # 检查API调用节流
    if performance_stats['throttled_api_calls'] > 0:
        logger.info("✅ API调用节流功能正常工作")
    else:
        logger.warning("⚠️  未检测到API调用节流，可能需要更严格的限制或更长的测试时间")
    
    # 检查缓存机制
    if performance_stats['cache_hits'] > 0:
        logger.info("✅ 市场数据缓存功能正常工作")
    else:
        logger.warning("⚠️  未检测到缓存命中，可能需要调整缓存配置或增加重复请求")
    
    # 检查并发更新
    if performance_stats['concurrent_updates'] > 0:
        logger.info("✅ 并发代理更新功能正常工作")
    else:
        logger.warning("⚠️  未检测到并发代理更新，可能需要增加代理数量或调整并发阈值")
    
    # 检查批量交易
    if performance_stats['batch_trades_executed'] > 0:
        logger.info("✅ 批量交易执行功能正常工作")
    else:
        logger.warning("⚠️  未检测到批量交易执行，可能需要更多同时交易信号")
    
    # 总体评估
    features_working = sum([
        1 if performance_stats['throttled_api_calls'] > 0 else 0,
        1 if performance_stats['cache_hits'] > 0 else 0,
        1 if performance_stats['concurrent_updates'] > 0 else 0,
        1 if performance_stats['batch_trades_executed'] > 0 else 0
    ])
    
    logger.info(f"\n性能优化功能工作状态: {features_working}/4")
    
    if features_working == 4:
        logger.info("🎉 所有性能优化功能验证通过!")
    else:
        logger.info("📊 部分性能优化功能已验证，建议进一步调整配置以测试所有功能")


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='Prometheus v3.0 性能测试')
    parser.add_argument('--duration', type=int, default=300, help='测试持续时间(秒)')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    args = parser.parse_args()
    
    # 设置日志级别
    logger.setLevel(getattr(logging, args.log_level))
    
    # 运行性能测试
    success = run_performance_test(args.duration)
    
    if success:
        logger.info("\n性能测试成功完成！")
        sys.exit(0)
    else:
        logger.error("\n性能测试失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()
