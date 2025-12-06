"""
极端场景测试（低恐惧Agent）：验证硬性止损对"不怕死"的Agent是否有效

测试目标：
即使Agent的fear_of_death很低（敢死队），硬性止损规则仍然有效
"""

import pandas as pd
import numpy as np
from prometheus.core.inner_council import Daimon
from prometheus.core.genome import GenomeVector
from prometheus.core.lineage import LineageVector
from prometheus.core.instinct import Instinct


def create_extreme_crash_context():
    """创建极端崩盘的市场环境"""
    class MockWorldSignature:
        def __init__(self):
            self.drift = -0.15
            self.volatility = 0.50
            self.trend_strength = -0.95
            self.entropy = 0.2
            self.regime_label = "EXTREME_CRASH"
            self.order_imbalance = -0.95
            self.trade_intensity = 15.0
            self.danger = 0.99  # 极度危险！
            self.stability = 0.02
            self.opportunity = 0.01
    
    return MockWorldSignature()


def test_low_fear_agent():
    """测试低恐惧Agent在极端崩盘中的表现"""
    
    print("\n" + "🚨" * 30)
    print("极端场景测试：低恐惧Agent（敢死队）")
    print("🚨" * 30 + "\n")
    
    # 创建一个"不怕死"的Agent
    class MockEmotion:
        def __init__(self):
            self.fear = 0.2  # 低恐惧
            self.despair = 0.2
            self.confidence = 0.8  # 高自信
            self.greed = 0.7  # 高贪婪
            self.stress = 0.3  # 低压力
    
    class MockExperience:
        def get_similar_patterns(self, context):
            return []
    
    class MockAgent:
        def __init__(self, fear_level: float):
            self.genome = GenomeVector.create_genesis()
            self.lineage = LineageVector.create_genesis(family_id=0)
            
            # 创建一个低恐惧的Instinct
            self.instinct = Instinct(
                fear_of_death=fear_level,      # 可变
                loss_aversion=0.2,             # 低损失厌恶
                risk_appetite=0.9,             # 高风险偏好
                reproductive_drive=0.5,
                curiosity=0.5,
                time_preference=0.5,
                generation=0,
                parent_instincts=None
            )
            
            self.meta_genome = None
            self.emotion = MockEmotion()
            self.experience = MockExperience()
            self.position = {'amount': 0.0, 'side': 'none'}
    
    # 测试不同恐惧等级的Agent
    fear_levels = [0.1, 0.5, 1.0, 1.5, 2.0]
    
    print("📊 测试场景：持有BTC，面临99%亏损\n")
    print("=" * 80)
    
    for fear_level in fear_levels:
        mock_agent = MockAgent(fear_level=fear_level)
        daimon = Daimon(agent=mock_agent)
        
        world_signature = create_extreme_crash_context()
        
        context = {
            'world_signature': world_signature,
            'position': {'amount': 1.0, 'side': 'long'},
            'unrealized_pnl': -0.99,
            'account_health': 0.01,
            'capital_ratio': 0.01,
            'recent_pnl': -0.99,
            'consecutive_losses': 10,
            'market_data': {
                'close': 500,
                'volume': 50000,
                'returns': [-0.15, -0.20, -0.18, -0.22, -0.16]
            }
        }
        
        decision = daimon.guide(context)
        
        # 评估
        is_correct = decision.action in ['close', 'sell']
        emoji = "✅" if is_correct else "❌"
        
        print(f"\n【Fear of Death = {fear_level:.1f}】")
        print(f"   特征：", end="")
        if fear_level < 0.5:
            print("敢死队（极度激进）")
        elif fear_level < 1.0:
            print("冒险者（激进）")
        elif fear_level < 1.5:
            print("平衡派（中立）")
        else:
            print("保守派（谨慎）")
        
        print(f"   决策：{decision.action} {emoji}")
        print(f"   信心：{decision.confidence:.2%}")
        
        # 找出instinct的投票
        instinct_votes = [v for v in decision.all_votes if v.voter_category == 'instinct']
        ws_votes = [v for v in decision.all_votes if v.voter_category == 'world_signature']
        
        print(f"   Instinct投票：", end="")
        if instinct_votes:
            for v in instinct_votes:
                print(f"{v.action} ({v.confidence:.0%})", end=" | ")
        else:
            print("无投票")
        
        print(f"\n   WorldSig投票：", end="")
        if ws_votes:
            for v in ws_votes:
                print(f"{v.action} ({v.confidence:.0%})", end=" | ")
        else:
            print("无投票")
        
        print()
    
    print("\n" + "=" * 80)
    
    # 分析
    print("\n💡 分析：硬性止损规则的作用")
    print("=" * 80)
    print("""
硬性止损规则（在instinct_voice中）：
1. 亏损>30% → 100%信心强制止损（直接返回）
2. 账户健康度<20% → 99%信心强制平仓（直接返回）

这两条规则的特点：
✅ 不依赖于fear_of_death的值
✅ 直接返回，不考虑其他因素
✅ 100%或99%信心，无法被其他投票压倒

因此：
即使Agent的fear_of_death=0.1（完全不怕死）
也会触发硬性止损！

这就是"铁律"的意义：
- 柔性本能可以进化
- 硬性规则保证底线
- 自然选择 + 人工安全网 = 完美结合
""")
    
    print("\n🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨")
    print("测试完成！")
    print("🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨\n")


if __name__ == '__main__':
    test_low_fear_agent()

