#!/usr/bin/env python3
"""
VPS主程序
=========

用于在VPS上运行Prometheus实盘/虚拟盘交易

用法：
    python vps_main.py --config config/vps_config.json
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from prometheus.exchange.okx_api import OKXExchange
from prometheus.trading.live_engine import LiveTradingEngine
from prometheus.monitoring.system_monitor import SystemMonitor
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('prometheus_vps.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def initialize_system(config: dict):
    """初始化系统"""
    logger.info("🚀 初始化Prometheus系统...")
    
    # 1. 初始化交易所
    okx_config = config['okx']
    
    # 虚拟盘模式不需要API密钥（只获取公开市场数据）
    if okx_config['paper_trading']:
        exchange = OKXExchange(
            api_key="",
            api_secret="",
            passphrase="",
            paper_trading=True,
            testnet=False
        )
    else:
        # 实盘模式需要真实API密钥
        exchange = OKXExchange(
            api_key=okx_config['api_key'],
            api_secret=okx_config['api_secret'],
            passphrase=okx_config['passphrase'],
            paper_trading=False,
            testnet=okx_config.get('testnet', False)
        )
    
    # 测试连接
    if not exchange.test_connection():
        logger.error("❌ 交易所连接失败")
        sys.exit(1)
    
    # 2. 初始化监控
    monitor_config = config['monitoring']
    monitor = SystemMonitor(log_dir=monitor_config['log_dir'])
    
    # 3. 初始化Moirai和进化管理器
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    evolution_manager.immigration_enabled = False
    
    # 4. 创建初始Agent
    agent_config = config['agents']
    agents = moirai._genesis_create_agents(
        agent_count=agent_config['initial_count'],
        gene_pool=[],
        capital_per_agent=agent_config['initial_capital']
    )
    
    for agent in agents:
        agent.fitness = 1.0
    
    moirai.agents = agents
    
    logger.info(f"✅ 初始Agent创建完成: {len(agents)}个")
    
    # 5. 创建交易引擎
    trading_config = config['trading']
    engine = LiveTradingEngine(
        exchange=exchange,
        moirai=moirai,
        evolution_manager=evolution_manager,
        symbol=trading_config['symbol'],
        interval=trading_config['interval'],
        evolution_interval=trading_config['evolution_interval'],
        max_position_size=trading_config['max_position_size'],
        max_leverage=trading_config['max_leverage']
    )
    
    return exchange, monitor, engine


def main():
    """主程序"""
    parser = argparse.ArgumentParser(description='Prometheus VPS交易系统')
    parser.add_argument('--config', type=str, default='config/vps_config.json',
                       help='配置文件路径')
    args = parser.parse_args()
    
    print()
    print("=" * 80)
    print("🚀 Prometheus VPS交易系统")
    print("=" * 80)
    print()
    
    # 加载配置
    logger.info(f"📋 加载配置: {args.config}")
    config = load_config(args.config)
    
    # 显示关键配置
    print("📋 配置信息:")
    print(f"   交易模式: {'虚拟盘' if config['okx']['paper_trading'] else '实盘'}")
    print(f"   交易对: {config['trading']['symbol']}")
    print(f"   交易周期: {config['trading']['interval']}秒")
    print(f"   进化周期: {config['trading']['evolution_interval']}秒 ({config['trading']['evolution_interval']/3600:.1f}小时)")
    print(f"   初始Agent: {config['agents']['initial_count']}个")
    print(f"   初始资金: ${config['agents']['initial_capital'] * config['agents']['initial_count']:,.0f}")
    print()
    
    # 初始化系统
    exchange, monitor, engine = initialize_system(config)
    
    # 启动交易
    logger.info("🚀 启动交易引擎...")
    print("🚀 交易引擎启动中...")
    print()
    print("⚠️  按Ctrl+C停止")
    print()
    print("=" * 80)
    print()
    
    try:
        engine.start()
    except KeyboardInterrupt:
        logger.info("⏹️  收到停止信号")
        print("\n⏹️  正在停止...")
    finally:
        # 生成最终报告
        logger.info("📄 生成最终报告...")
        report = monitor.generate_daily_report()
        print(f"\n📄 报告已生成")
        print()


if __name__ == "__main__":
    main()

