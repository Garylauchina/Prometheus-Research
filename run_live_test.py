#!/usr/bin/env python3
"""
Prometheus - 本地连续实盘测试
"""

import sys
sys.path.insert(0, 'config')
from okx_config import OKX_PAPER_TRADING

import logging
from datetime import datetime
from prometheus.exchange.okx_api import OKXExchange
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.trading.live_engine_full import LiveTradingEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

def main():
    print("=" * 70)
    print("🚀 Prometheus - 本地连续实盘测试")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("按 Ctrl+C 停止测试")
    print("=" * 70)
    print()
    
    # 1. 初始化交易所
    logger.info("📡 初始化OKX交易所...")
    exchange = OKXExchange(
        api_key=OKX_PAPER_TRADING['api_key'],
        api_secret=OKX_PAPER_TRADING['api_secret'],
        passphrase=OKX_PAPER_TRADING['passphrase'],
        paper_trading=False,  # 不使用本地模拟
        testnet=True  # 使用OKX Sandbox
    )
    
    # 2. 初始化Moirai（种群管理）
    logger.info("⚖️  初始化Moirai种群管理...")
    moirai = Moirai(
        bulletin_board=None,
        num_families=50
    )
    
    # 3. 初始化进化管理器
    logger.info("🧬 初始化进化管理器...")
    evolution_manager = EvolutionManagerV5(
        moirai=moirai,
        elite_ratio=0.3,
        elimination_ratio=0.3,
        num_families=50
    )
    
    # 创建初始Agent种群
    logger.info("👥 创建初始Agent种群（10个）...")
    from prometheus.core.agent_v5 import AgentV5
    moirai.agents = []
    for i in range(10):
        agent = AgentV5.create_genesis(
            agent_id=f"LiveAgent_{i+1:02d}",
            family_id=f"family_{(i % 50) + 1}",
            initial_capital=10000.0
        )
        moirai.agents.append(agent)
    logger.info(f"✅ 创建了{len(moirai.agents)}个Agent")
    
    # 4. 初始化交易引擎
    logger.info("🎯 初始化交易引擎...")
    engine = LiveTradingEngine(
        exchange=exchange,
        moirai=moirai,
        evolution_manager=evolution_manager,
        symbol='BTC/USDT:USDT',
        interval=300,  # 5分钟
        evolution_interval=86400,  # 24小时进化一次
        max_position_size=0.02,
        max_leverage=3.0,
        enable_real_trading=True
    )
    
    print()
    print("=" * 70)
    print("✅ 所有组件初始化完成，开始交易...")
    print("=" * 70)
    print()
    
    # 5. 启动引擎
    try:
        engine.start()
    except KeyboardInterrupt:
        print("\n\n⚠️  手动停止")
    except Exception as e:
        print(f"\n\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "=" * 70)
        print("📊 测试结束统计")
        print("=" * 70)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总周期数: {engine.cycle_count}")
        print(f"总订单数: {engine.total_orders}")
        print(f"成功订单: {engine.successful_orders}")
        print(f"失败订单: {engine.failed_orders}")
        print("=" * 70)

if __name__ == "__main__":
    main()

