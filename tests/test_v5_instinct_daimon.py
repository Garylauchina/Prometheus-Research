"""
v5.0基础模块测试 - Instinct + Daimon
===================================

使用Mock数据测试Instinct和Daimon的功能
"""

import sys
sys.path.insert(0, '.')

from prometheus.core.instinct import Instinct, calculate_instinct_diversity, get_dominant_instinct
from prometheus.core.inner_council import Daimon, Vote, CouncilDecision, format_decision_report
from dataclasses import dataclass


# ==================== Mock Agent ====================

@dataclass
class MockEmotionalState:
    """Mock情绪状态"""
    despair: float = 0.0
    fear: float = 0.0
    confidence: float = 0.5
    stress: float = 0.0


@dataclass
class MockGenome:
    """Mock基因组"""
    active_params: dict


@dataclass
class MockAgent:
    """Mock Agent（简化版，用于测试）"""
    agent_id: str
    instinct: Instinct
    genome: MockGenome
    emotion: MockEmotionalState


# ==================== 测试函数 ====================

def test_instinct_creation():
    """测试1: 本能创建"""
    print("\n" + "=" * 60)
    print("测试1: 本能创建")
    print("=" * 60)
    
    # 创世本能
    instinct = Instinct.create_genesis()
    print(f"\n创世本能:")
    print(f"  死亡恐惧: {instinct.fear_of_death:.2f} (固定)")
    print(f"  繁殖欲望: {instinct.reproductive_drive:.2f}")
    print(f"  损失厌恶: {instinct.loss_aversion:.2f}")
    print(f"  风险偏好: {instinct.risk_appetite:.2f}")
    print(f"  好奇心: {instinct.curiosity:.2f}")
    print(f"  时间偏好: {instinct.time_preference:.2f}")
    print(f"\n性格描述: {instinct.describe_personality()}")
    
    return instinct


def test_instinct_inheritance():
    """测试2: 本能遗传"""
    print("\n" + "=" * 60)
    print("测试2: 本能遗传")
    print("=" * 60)
    
    # 创建两个父母
    parent1 = Instinct.create_genesis()
    parent2 = Instinct.create_genesis()
    
    print(f"\n父母1: {parent1.describe_personality()}")
    print(f"  繁殖欲望: {parent1.reproductive_drive:.2f}")
    print(f"  风险偏好: {parent1.risk_appetite:.2f}")
    
    print(f"\n父母2: {parent2.describe_personality()}")
    print(f"  繁殖欲望: {parent2.reproductive_drive:.2f}")
    print(f"  风险偏好: {parent2.risk_appetite:.2f}")
    
    # 遗传
    child = Instinct.inherit_from_parents(parent1, parent2, generation=1)
    
    print(f"\n子代: {child.describe_personality()}")
    print(f"  繁殖欲望: {child.reproductive_drive:.2f} (父母平均: {(parent1.reproductive_drive + parent2.reproductive_drive)/2:.2f})")
    print(f"  风险偏好: {child.risk_appetite:.2f} (父母平均: {(parent1.risk_appetite + parent2.risk_appetite)/2:.2f})")
    print(f"  代数: {child.generation}")
    
    return child


def test_instinct_fear_calculation():
    """测试3: 死亡恐惧计算"""
    print("\n" + "=" * 60)
    print("测试3: 死亡恐惧计算")
    print("=" * 60)
    
    instinct = Instinct.create_genesis()
    
    scenarios = [
        (1.0, 0, "健康状态"),
        (0.7, 0, "小幅亏损"),
        (0.5, 0, "亏损50%"),
        (0.3, 0, "濒死"),
        (0.2, 3, "濒死+连续亏损"),
    ]
    
    print(f"\n不同场景下的死亡恐惧水平:")
    for capital_ratio, consecutive_losses, desc in scenarios:
        fear = instinct.calculate_death_fear_level(capital_ratio, consecutive_losses)
        should_survive = instinct.should_prioritize_survival(capital_ratio)
        print(f"  {desc:20s} (资金{capital_ratio:.1%}, 连亏{consecutive_losses}次): "
              f"恐惧={fear:.2f}, 优先生存={should_survive}")


def test_instinct_diversity():
    """测试4: 本能多样性"""
    print("\n" + "=" * 60)
    print("测试4: 本能多样性")
    print("=" * 60)
    
    # 创建10个创世本能
    instincts = [Instinct.create_genesis() for _ in range(10)]
    
    # 计算多样性
    diversity = calculate_instinct_diversity(instincts)
    
    print(f"\n10个创世本能的多样性: {diversity:.2f}")
    print(f"\n各本能的主导特征:")
    for i, inst in enumerate(instincts[:5], 1):  # 只显示前5个
        dominant_name, dominant_value = get_dominant_instinct(inst)
        from prometheus.core.instinct import get_instinct_chinese_name
        print(f"  本能{i}: {inst.describe_personality():30s} "
              f"(主导: {get_instinct_chinese_name(dominant_name)} {dominant_value:.2f})")


def test_daimon_decision():
    """测试5: Daimon决策"""
    print("\n" + "=" * 60)
    print("测试5: Daimon决策")
    print("=" * 60)
    
    # 创建Mock Agent
    instinct = Instinct.create_genesis()
    instinct.loss_aversion = 0.8  # 高损失厌恶
    instinct.risk_appetite = 0.3  # 低风险偏好
    
    genome = MockGenome(active_params={
        'trend_pref': 0.7,
        'mean_reversion': 0.3,
        'patience': 0.6,
    })
    
    emotion = MockEmotionalState(
        despair=0.2,
        fear=0.3,
        confidence=0.5,
        stress=0.4,
    )
    
    agent = MockAgent(
        agent_id="Agent_Test",
        instinct=instinct,
        genome=genome,
        emotion=emotion,
    )
    
    # 创建Daimon
    daimon = Daimon(agent)
    
    # 场景1: 濒死+持仓
    print("\n场景1: 濒死+持仓")
    context1 = {
        'capital_ratio': 0.25,  # 濒死
        'recent_pnl': -0.15,
        'consecutive_losses': 5,
        'position': {'amount': 0.1, 'side': 'long'},
        'bulletins': {},
        'market_data': {'trend': 'bearish'},
    }
    
    decision1 = daimon.guide(context1)
    print(format_decision_report(decision1))
    
    # 场景2: 健康+无仓+看涨
    print("\n场景2: 健康+无仓+看涨预言")
    context2 = {
        'capital_ratio': 1.2,  # 盈利
        'recent_pnl': 0.1,
        'consecutive_losses': 0,
        'consecutive_wins': 3,
        'position': {'amount': 0, 'side': None},
        'bulletins': {
            'minor_prophecy': {
                'trend': 'bullish',
                'confidence': 0.75,
                'environmental_pressure': 0.2,
            }
        },
        'market_data': {'trend': 'bullish'},
    }
    
    decision2 = daimon.guide(context2)
    print(format_decision_report(decision2))
    
    # 场景3: 震荡市+高压力
    print("\n场景3: 震荡市+环境高压力")
    context3 = {
        'capital_ratio': 0.9,
        'recent_pnl': -0.02,
        'consecutive_losses': 1,
        'position': {'amount': 0.05, 'side': 'long'},
        'bulletins': {
            'minor_prophecy': {
                'trend': 'neutral',
                'confidence': 0.5,
                'environmental_pressure': 0.85,  # 高压力
            }
        },
        'market_data': {'trend': 'neutral'},
    }
    
    decision3 = daimon.guide(context3)
    print(format_decision_report(decision3))


def test_instinct_pressure():
    """测试6: 本能压力对决策的影响"""
    print("\n" + "=" * 60)
    print("测试6: 本能压力对决策的影响")
    print("=" * 60)
    
    # 创建高损失厌恶的本能
    instinct = Instinct.create_genesis()
    instinct.loss_aversion = 0.9
    instinct.risk_appetite = 0.2
    
    # 基础决策分数（假设其他模块给出的）
    base_scores = {
        'buy': 0.4,
        'sell': 0.3,
        'hold': 0.2,
        'close': 0.1,
    }
    
    # 场景：亏损中
    context = {
        'capital_ratio': 0.6,
        'recent_pnl': -0.08,
        'consecutive_losses': 2,
    }
    
    print(f"\n基础决策分数: {base_scores}")
    print(f"场景: 资金剩60%, 亏损8%, 连亏2次")
    print(f"本能: 高损失厌恶({instinct.loss_aversion:.1%}), 低风险偏好({instinct.risk_appetite:.1%})")
    
    adjusted_scores = instinct.apply_instinct_pressure(base_scores, context)
    
    print(f"\n施加本能压力后的分数:")
    for action, score in sorted(adjusted_scores.items(), key=lambda x: -x[1]):
        change = score - base_scores[action]
        symbol = "+" if change > 0 else ""
        print(f"  {action:5s}: {score:.2%} ({symbol}{change:.2%})")


# ==================== 主测试 ====================

def main():
    """运行所有测试"""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  Prometheus v5.0 - Instinct + Daimon 测试".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)
    
    try:
        test_instinct_creation()
        test_instinct_inheritance()
        test_instinct_fear_calculation()
        test_instinct_diversity()
        test_daimon_decision()
        test_instinct_pressure()
        
        print("\n" + "█" * 60)
        print("█" + " " * 58 + "█")
        print("█" + "  ✅ 所有测试通过！".center(58) + "█")
        print("█" + " " * 58 + "█")
        print("█" * 60 + "\n")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

