#!/usr/bin/env python3
"""
本地测试实盘交易引擎
==================

用于在本地快速测试完整版实盘引擎
"""

import sys
sys.path.insert(0, '.')

import logging
from prometheus.exchange.okx_api import OKXExchange
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.trading.live_engine_full import LiveTradingEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print()
    print("="*70)
    print("🧪 本地测试 - 完整版实盘交易引擎")
    print("="*70)
    print()
    
    # 1. 初始化交易所（虚拟盘模式）
    print("📡 初始化OKX虚拟盘...")
    exchange = OKXExchange(
        api_key="",
        api_secret="",
        passphrase="",
        paper_trading=True,  # 虚拟盘
        testnet=False
    )
    
    if not exchange.test_connection():
        print("❌ OKX连接失败")
        return
    
    print("✅ OKX连接成功")
    
    # 2. 初始化Moirai和进化管理器
    print("\n🧬 初始化Moirai...")
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    evolution_manager.immigration_enabled = False
    
    # 3. 创建初始Agent（少量用于测试）
    print("\n👥 创建测试Agent...")
    agents = moirai._genesis_create_agents(
        agent_count=5,  # 只创建5个Agent测试
        gene_pool=[],
        capital_per_agent=10000.0
    )
    
    for agent in agents:
        agent.fitness = 1.0
    
    moirai.agents = agents
    print(f"✅ 创建了 {len(agents)} 个测试Agent")
    
    # 4. 创建交易引擎
    print("\n🚀 创建交易引擎...")
    engine = LiveTradingEngine(
        exchange=exchange,
        moirai=moirai,
        evolution_manager=evolution_manager,
        symbol='BTC/USDT',
        interval=30,  # 30秒一个周期（测试用）
        evolution_interval=300,  # 5分钟进化一次（测试用）
        max_position_size=0.001,  # 减小持仓（测试用）
        max_leverage=5.0,  # 降低杠杆（测试用）
        enable_real_trading=False  # 先用False测试，确认无误后改为True
    )
    
    print("✅ 交易引擎创建完成")
    
    # 5. 显示配置
    print("\n" + "="*70)
    print("⚙️  配置信息:")
    print("   - 模式: 虚拟盘 + 模拟交易（enable_real_trading=False）")
    print("   - Agent数量: 5个")
    print("   - 交易周期: 30秒")
    print("   - 最大持仓: 0.001 BTC")
    print("   - 测试时长: 自动运行（按Ctrl+C停止）")
    print("="*70)
    
    # 6. 自动启动测试
    print("\n🚀 启动测试...")
    print("⚠️  按Ctrl+C停止")
    print()
    
    try:
        engine.start()
    except KeyboardInterrupt:
        print("\n\n⏹️  测试已停止")
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == '__main__':
    main()

