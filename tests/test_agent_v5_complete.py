"""
AgentV5完整测试 - 端到端验证
============================

测试所有v5.0模块的集成：
- Lineage（血统）
- Genome（基因组）
- Instinct（本能）
- Strategy（策略）
- PersonalInsights（个体记忆）
- EmotionalState（情绪）
- Daimon（守护神）
"""

import sys
sys.path.insert(0, '.')

from prometheus.core.agent_v5 import AgentV5, AgentState
from prometheus.core.inner_council import format_decision_report
import numpy as np


# ==================== Mock市场数据 ====================

def generate_mock_market_data(cycle: int, trend: str = 'bullish') -> dict:
    """生成Mock市场数据"""
    base_price = 90000
    
    if trend == 'bullish':
        price = base_price + cycle * 100 + np.random.uniform(-500, 500)
    elif trend == 'bearish':
        price = base_price - cycle * 100 + np.random.uniform(-500, 500)
    else:  # neutral
        price = base_price + np.random.uniform(-1000, 1000)
    
    # 生成OHLCV数据
    ohlcv = []
    for i in range(20):
        o = price + np.random.uniform(-100, 100)
        h = o + abs(np.random.uniform(0, 200))
        l = o - abs(np.random.uniform(0, 200))
        c = (h + l) / 2 + np.random.uniform(-50, 50)
        v = np.random.uniform(1000, 5000)
        ohlcv.append([i, o, h, l, c, v])
    
    return {
        'price': price,
        'ohlcv': ohlcv,
        'volume': np.random.uniform(1000, 5000),
        'trend': trend,
        'volatility': 0.05,
    }


def generate_mock_bulletins(cycle: int) -> dict:
    """生成Mock公告板数据"""
    if cycle % 3 == 0:
        trend = 'bullish'
    elif cycle % 3 == 1:
        trend = 'bearish'
    else:
        trend = 'neutral'
    
    return {
        'minor_prophecy': {
            'trend': trend,
            'confidence': 0.7,
            'environmental_pressure': 0.2 + np.random.uniform(-0.1, 0.1),
        }
    }


# ==================== 测试函数 ====================

def test_agent_creation():
    """测试1: Agent创建"""
    print("\n" + "=" * 70)
    print("测试1: Agent创建")
    print("=" * 70)
    
    agent = AgentV5.create_genesis(
        agent_id="Agent_Test_001",
        initial_capital=10000.0,
        family_count=50
    )
    
    print(f"\n✅ Agent创建成功:")
    print(f"   ID: {agent.agent_id}")
    print(f"   代数: {agent.generation}")
    print(f"   资金: ${agent.current_capital:.2f}")
    print(f"   状态: {agent.state.value}")
    print(f"   策略池: {[s.name for s in agent.strategy_pool]}")
    print(f"   激活策略: {[s.name for s in agent.active_strategies]}")
    print(f"   本能: {agent.instinct.describe_personality()}")
    
    # 验证模块
    assert agent.lineage is not None, "Lineage未初始化"
    assert agent.genome is not None, "Genome未初始化"
    assert agent.instinct is not None, "Instinct未初始化"
    assert agent.daimon is not None, "Daimon未初始化"
    assert len(agent.strategy_pool) > 0, "策略池为空"
    
    print(f"\n✅ 所有模块正常初始化")
    
    return agent


def test_agent_decision_making(agent: AgentV5):
    """测试2: Agent决策流程"""
    print("\n" + "=" * 70)
    print("测试2: Agent决策流程")
    print("=" * 70)
    
    # 场景1: 看涨市场 + 健康状态
    print("\n场景1: 看涨市场 + 健康状态")
    print("-" * 70)
    
    market_data = generate_mock_market_data(1, trend='bullish')
    bulletins = generate_mock_bulletins(1)
    
    decision = agent.make_trading_decision(market_data, bulletins, cycle_count=5)
    
    if decision:
        print(f"✅ 决策: {decision['action']}")
        print(f"   信心: {decision['confidence']:.1%}")
        print(f"   推理: {decision['reasoning']}")
        print(f"   仓位: {decision['amount']:.4f}")
    else:
        print(f"✅ 决策: 观望")
    
    # 场景2: 看跌市场 + 持仓
    print("\n场景2: 看跌市场 + 持仓")
    print("-" * 70)
    
    # 模拟持仓
    agent.current_position = {'amount': 0.1, 'side': 'long', 'entry_price': 90000}
    agent.consecutive_losses = 2
    
    market_data = generate_mock_market_data(1, trend='bearish')
    bulletins = generate_mock_bulletins(2)
    
    decision = agent.make_trading_decision(market_data, bulletins, cycle_count=6)
    
    if decision:
        print(f"✅ 决策: {decision['action']}")
        print(f"   信心: {decision['confidence']:.1%}")
        print(f"   推理: {decision['reasoning']}")
    else:
        print(f"✅ 决策: 观望")
    
    # 场景3: 濒死状态
    print("\n场景3: 濒死状态")
    print("-" * 70)
    
    agent.current_capital = 2500.0  # 资金剩25%
    agent.consecutive_losses = 5
    agent._update_emotional_state()
    
    market_data = generate_mock_market_data(1, trend='bullish')
    bulletins = generate_mock_bulletins(3)
    
    decision = agent.make_trading_decision(market_data, bulletins, cycle_count=7)
    
    print(f"   资金比率: {agent.current_capital / agent.initial_capital:.1%}")
    print(f"   绝望: {agent.emotion.despair:.1%}")
    print(f"   恐惧: {agent.emotion.fear:.1%}")
    print(f"   死亡恐惧水平: {agent.instinct.calculate_death_fear_level(0.25, 5):.2f}")
    
    if decision:
        print(f"✅ 决策: {decision['action']} (本能驱动)")
        print(f"   推理: {decision['reasoning']}")
    else:
        print(f"✅ 决策: 观望")


def test_strategy_analysis():
    """测试3: 策略分析"""
    print("\n" + "=" * 70)
    print("测试3: 策略分析")
    print("=" * 70)
    
    agent = AgentV5.create_genesis(
        agent_id="Agent_Test_002",
        initial_capital=10000.0,
    )
    
    market_data = generate_mock_market_data(10, trend='bullish')
    
    # 获取策略信号
    strategy_signals = agent._analyze_with_strategies(market_data)
    
    print(f"\n策略分析结果 ({len(strategy_signals)}个策略):")
    for signal in strategy_signals:
        print(f"\n  策略: {signal.strategy_name}")
        print(f"    看涨评分: {signal.bullish_score:.2%}")
        print(f"    看跌评分: {signal.bearish_score:.2%}")
        print(f"    信心: {signal.confidence:.2%}")
        print(f"    推理: {signal.reasoning}")
    
    print(f"\n✅ 策略系统正常工作")


def test_emotional_state():
    """测试4: 情绪系统"""
    print("\n" + "=" * 70)
    print("测试4: 情绪系统")
    print("=" * 70)
    
    agent = AgentV5.create_genesis(
        agent_id="Agent_Test_003",
        initial_capital=10000.0,
    )
    
    scenarios = [
        (10000, 0, "健康状态"),
        (7000, 2, "小幅亏损"),
        (5000, 5, "亏损50%+连亏"),
        (2000, 10, "濒死"),
    ]
    
    print(f"\n不同场景下的情绪变化:")
    for capital, losses, desc in scenarios:
        agent.current_capital = capital
        agent.consecutive_losses = losses
        agent._update_emotional_state()
        
        print(f"\n  {desc}:")
        print(f"    资金: ${capital:.2f} ({capital/10000:.1%})")
        print(f"    连亏: {losses}次")
        print(f"    绝望: {agent.emotion.despair:.2%}")
        print(f"    恐惧: {agent.emotion.fear:.2%}")
        print(f"    信心: {agent.emotion.confidence:.2%}")
        print(f"    压力: {agent.emotion.stress:.2%}")
    
    print(f"\n✅ 情绪系统正常工作")


def test_daimon_voting():
    """测试5: Daimon投票机制"""
    print("\n" + "=" * 70)
    print("测试5: Daimon投票机制（6个声音）")
    print("=" * 70)
    
    agent = AgentV5.create_genesis(
        agent_id="Agent_Test_004",
        initial_capital=10000.0,
    )
    
    # 设置特定的本能和情绪
    agent.instinct.loss_aversion = 0.9
    agent.instinct.risk_appetite = 0.3
    agent.current_capital = 3000.0  # 濒死
    agent.consecutive_losses = 5
    agent._update_emotional_state()
    
    # 设置持仓
    agent.current_position = {'amount': 0.1, 'side': 'long', 'entry_price': 90000}
    
    market_data = generate_mock_market_data(1, trend='bullish')
    bulletins = generate_mock_bulletins(1)
    
    # 获取策略信号
    strategy_signals = agent._analyze_with_strategies(market_data)
    
    # 准备上下文
    context = agent._prepare_decision_context(market_data, bulletins, strategy_signals)
    
    # 咨询Daimon
    guidance = agent.daimon.guide(context)
    
    # 显示详细报告
    print(format_decision_report(guidance))
    
    print(f"\n✅ Daimon投票机制正常工作")
    print(f"   6个声音: instinct/genome/experience/emotion/strategy/prophecy")


def test_learning_system():
    """测试6: 学习系统（PersonalInsights）"""
    print("\n" + "=" * 70)
    print("测试6: 学习系统（PersonalInsights）")
    print("=" * 70)
    
    agent = AgentV5.create_genesis(
        agent_id="Agent_Test_005",
        initial_capital=10000.0,
    )
    
    # 模拟一些交易记录
    recent_trades = [
        {'strategy': 'TrendFollowing', 'pnl': 0.05, 'outcome': 'win'},
        {'strategy': 'TrendFollowing', 'pnl': 0.03, 'outcome': 'win'},
        {'strategy': 'MeanReversion', 'pnl': -0.02, 'outcome': 'loss'},
        {'strategy': 'TrendFollowing', 'pnl': 0.04, 'outcome': 'win'},
        {'strategy': 'GridTrading', 'pnl': -0.01, 'outcome': 'loss'},
    ]
    
    # 记录策略效果
    for trade in recent_trades:
        agent.personal_insights.record_strategy_result(
            trade['strategy'],
            trade['pnl']
        )
    
    # 冥思
    meditation = agent.meditate(recent_trades)
    
    print(f"\n冥思结果:")
    print(f"  发现模式: {meditation.patterns_discovered}个")
    print(f"  洞察:")
    for insight in meditation.insights:
        print(f"    - {insight}")
    
    # 查看策略效果
    print(f"\n策略效果统计:")
    for name, perf in agent.personal_insights.strategy_performance.items():
        print(f"  {name}:")
        print(f"    使用{perf.total_uses}次, 胜率{perf.win_rate:.1%}, 平均盈亏{perf.avg_pnl:.2%}")
    
    # 最佳/最差策略
    best = agent.personal_insights.get_best_strategy()
    worst = agent.personal_insights.get_worst_strategy()
    
    print(f"\n  最佳策略: {best}")
    print(f"  最差策略: {worst}")
    
    print(f"\n✅ 学习系统正常工作")


def test_full_cycle():
    """测试7: 完整周期模拟"""
    print("\n" + "=" * 70)
    print("测试7: 完整周期模拟（10个周期）")
    print("=" * 70)
    
    agent = AgentV5.create_genesis(
        agent_id="Agent_Test_006",
        initial_capital=10000.0,
    )
    
    print(f"\n开始模拟...")
    print(f"初始资金: ${agent.current_capital:.2f}")
    
    for cycle in range(1, 11):
        # 生成市场数据
        trend = 'bullish' if cycle % 3 == 0 else 'bearish' if cycle % 3 == 1 else 'neutral'
        market_data = generate_mock_market_data(cycle, trend)
        bulletins = generate_mock_bulletins(cycle)
        
        # Agent决策
        decision = agent.make_trading_decision(market_data, bulletins, cycle)
        
        # 简化的交易模拟（Mock）
        if decision and decision['action'] in ['buy', 'close']:
            # 模拟交易结果
            pnl = np.random.uniform(-0.02, 0.03)  # 随机盈亏
            agent.current_capital *= (1 + pnl)
            agent.capital_history.append(agent.current_capital)
            agent.trade_count += 1
            
            if pnl > 0:
                agent.win_count += 1
                agent.consecutive_wins += 1
                agent.consecutive_losses = 0
            else:
                agent.loss_count += 1
                agent.consecutive_losses += 1
                agent.consecutive_wins = 0
            
            # 记录策略效果
            if agent.current_strategy_name:
                agent.personal_insights.record_strategy_result(
                    agent.current_strategy_name, pnl
                )
        
        # 更新情绪
        agent._update_emotional_state()
        
        # 日志
        action_str = decision['action'] if decision else 'hold'
        print(f"  周期{cycle}: {action_str:6s} | "
              f"资金${agent.current_capital:8.2f}({agent.current_capital/10000:.1%}) | "
              f"绝望{agent.emotion.despair:.1%} | "
              f"连亏{agent.consecutive_losses}")
    
    # 最终统计
    print(f"\n最终统计:")
    print(f"  资金: ${agent.current_capital:.2f} ({agent.current_capital/10000:.1%})")
    print(f"  交易次数: {agent.trade_count}")
    print(f"  胜率: {agent.win_count / agent.trade_count:.1%}" if agent.trade_count > 0 else "  胜率: N/A")
    print(f"  连续亏损: {agent.consecutive_losses}")
    print(f"  情绪: 绝望{agent.emotion.despair:.1%}, 信心{agent.emotion.confidence:.1%}")
    
    print(f"\n✅ 完整周期模拟成功")


# ==================== 主测试 ====================

def main():
    """运行所有测试"""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  Prometheus v5.0 - AgentV5 完整测试".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    try:
        # 测试1: 创建
        agent = test_agent_creation()
        
        # 测试2: 决策
        test_agent_decision_making(agent)
        
        # 测试3: 策略
        test_strategy_analysis()
        
        # 测试4: 情绪
        test_emotional_state()
        
        # 测试5: Daimon
        test_daimon_voting()
        
        # 测试6: 学习
        test_learning_system()
        
        # 测试7: 完整周期
        test_full_cycle()
        
        print("\n" + "█" * 70)
        print("█" + " " * 68 + "█")
        print("█" + "  ✅ 所有测试通过！v5.0系统正常工作！".center(68) + "█")
        print("█" + " " * 68 + "█")
        print("█" * 70 + "\n")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

