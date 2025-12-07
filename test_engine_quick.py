#!/usr/bin/env python3
"""快速测试live_engine_full"""
import sys
sys.path.insert(0, '.')

print("🧪 快速测试live_engine_full...")

try:
    from prometheus.exchange.okx_api import OKXExchange
    from prometheus.core.moirai import Moirai
    from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
    from prometheus.trading.live_engine_full import LiveTradingEngine
    print("✅ 导入成功")
    
    # 测试初始化
    exchange = OKXExchange(paper_trading=True)
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 创建1个测试Agent
    agents = moirai._genesis_create_agents(1, [], 10000.0)
    moirai.agents = agents
    
    # 创建引擎
    engine = LiveTradingEngine(
        exchange=exchange,
        moirai=moirai,
        evolution_manager=evolution_manager,
        enable_real_trading=False
    )
    print("✅ 引擎初始化成功")
    
    # 测试决策逻辑（不实际运行）
    agent = agents[0]
    decision = engine.agent_make_decision(agent, 0.0002, 89500)
    print(f"✅ 决策测试: {decision}")
    
    print("\n🎉 所有测试通过！可以部署")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

