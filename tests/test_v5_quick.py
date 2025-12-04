"""快速测试 - 验证v5.0基础功能"""

import sys
sys.path.insert(0, '.')

print("开始测试...")

# 测试1: 导入模块
print("\n1. 测试模块导入...")
try:
    from prometheus.core.lineage import LineageVector
    from prometheus.core.genome import GenomeVector
    from prometheus.core.instinct import Instinct
    from prometheus.core.strategy import Strategy, StrategySignal, TrendFollowingStrategy
    from prometheus.core.personal_insights import PersonalInsights
    from prometheus.core.inner_council import Daimon, Vote, CouncilDecision
    from prometheus.core.agent_v5 import AgentV5
    print("✅ 所有模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

# 测试2: 创建Agent
print("\n2. 测试Agent创建...")
try:
    agent = AgentV5.create_genesis(
        agent_id="Test_001",
        initial_capital=10000.0,
        family_id=0,
        num_families=50
    )
    print(f"✅ Agent创建成功: {agent.agent_id}")
    print(f"   资金: ${agent.current_capital:.2f}")
    print(f"   策略池: {[s.name for s in agent.strategy_pool]}")
    print(f"   本能: {agent.instinct.describe_personality()}")
except Exception as e:
    print(f"❌ Agent创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3: 策略分析
print("\n3. 测试策略分析...")
try:
    market_data = {
        'price': 90000,
        'ohlcv': [[i, 90000, 90100, 89900, 90000, 1000] for i in range(20)],
        'volume': 2000,
        'trend': 'bullish',
        'volatility': 0.05,
    }
    
    signals = agent._analyze_with_strategies(market_data)
    print(f"✅ 策略分析成功: {len(signals)}个策略")
    for signal in signals:
        print(f"   {signal.strategy_name}: 看涨{signal.bullish_score:.1%}, 看跌{signal.bearish_score:.1%}")
except Exception as e:
    print(f"❌ 策略分析失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试4: Daimon决策
print("\n4. 测试Daimon决策...")
try:
    bulletins = {
        'minor_prophecy': {
            'trend': 'bullish',
            'confidence': 0.7,
            'environmental_pressure': 0.2,
        }
    }
    
    decision = agent.make_trading_decision(market_data, bulletins, cycle_count=5)
    
    if decision:
        print(f"✅ Daimon决策成功: {decision['action']}")
        print(f"   信心: {decision['confidence']:.1%}")
        print(f"   推理: {decision['reasoning']}")
    else:
        print(f"✅ Daimon决策成功: 观望")
except Exception as e:
    print(f"❌ Daimon决策失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ 所有测试通过！v5.0系统基础功能正常！")
print("=" * 70)

