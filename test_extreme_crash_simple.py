"""
极端场景测试（简化版）：BTC市场崩盘（24小时内暴跌99%）

测试目标：
1. Daimon在极端危险场景下会给出什么决策？
2. 系统是否有足够的"恐惧"和风险控制？
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from prometheus.core.inner_council import Daimon
from prometheus.core.genome import GenomeVector
from prometheus.core.lineage import LineageVector
from prometheus.core.instinct import Instinct


def create_extreme_crash_context():
    """创建极端崩盘的市场环境"""
    
    # 模拟WorldSignature的极端危险信号
    class MockWorldSignature:
        def __init__(self):
            # 宏观特征：极度负drift，爆炸式volatility
            self.drift = -0.15  # -15%平均收益率（极度负值）
            self.volatility = 0.50  # 50%波动率（爆炸级别）
            self.trend_strength = -0.95  # 单向暴跌
            self.entropy = 0.2  # 低entropy（所有人都在卖）
            self.regime_label = "EXTREME_CRASH"
            
            # 微观特征
            self.order_imbalance = -0.95  # 卖方压倒性优势
            self.trade_intensity = 15.0  # 恐慌性抛售
            
            # 风险指标
            self.danger = 0.99  # 极度危险！
            self.stability = 0.02  # 极度不稳定
            self.opportunity = 0.01  # 几乎无机会
    
    return MockWorldSignature()


def test_daimon_in_extreme_crash():
    """测试Daimon在极端崩盘中的决策"""
    
    print("\n" + "🚨" * 30)
    print("极端场景压力测试：BTC市场崩盘（-99%）")
    print("🚨" * 30 + "\n")
    
    # 创建一个Mock Agent
    class MockEmotion:
        def __init__(self):
            self.fear = 0.5
            self.despair = 0.5
            self.confidence = 0.5
            self.greed = 0.3
            self.stress = 0.6
            
    class MockExperience:
        def get_similar_patterns(self, context):
            return []  # 无历史经验
    
    class MockAgent:
        def __init__(self):
            self.genome = GenomeVector.create_genesis()
            self.lineage = LineageVector.create_genesis(family_id=0)
            self.instinct = Instinct.create_genesis()
            self.meta_genome = None  # 使用默认权重
            self.emotion = MockEmotion()
            self.experience = MockExperience()
            self.position = {'amount': 0.0, 'side': 'none'}
            
    mock_agent = MockAgent()
    
    # 创建Daimon
    daimon = Daimon(agent=mock_agent)
    
    # 创建极端崩盘环境
    world_signature = create_extreme_crash_context()
    
    print("📊 市场状态：")
    print("=" * 60)
    print(f"   初始价格：$50,000")
    print(f"   当前价格：$500")
    print(f"   总跌幅：-99%")
    print(f"   时间跨度：24小时")
    print(f"   Drift：{world_signature.drift:.2%} 🔴 极度负值！")
    print(f"   Volatility：{world_signature.volatility:.2%} 🔴 爆炸式波动！")
    print(f"   Trend：{world_signature.trend_strength:.2f} 🔴 单向暴跌！")
    print(f"   Danger：{world_signature.danger:.2%} 🔴 极度危险！")
    print(f"   Stability：{world_signature.stability:.2%} 🔴 极度不稳定！")
    print("=" * 60 + "\n")
    
    # 场景1：持有BTC（最危险）
    print("【场景1】持有BTC，面临99%亏损...")
    print("-" * 60)
    context_holding = {
        'world_signature': world_signature,
        'position': {'amount': 1.0, 'side': 'long'},  # 满仓
        'unrealized_pnl': -0.99,  # 已亏损99%
        'account_health': 0.01,  # 账户几乎归零
        'market_data': {
            'close': 500,
            'volume': 50000,
            'returns': [-0.15, -0.20, -0.18, -0.22, -0.16]  # 近期持续暴跌
        }
    }
    
    decision_holding = daimon.guide(context_holding)
    print(f"\n   💡 决策：{decision_holding.action}")
    print(f"   📊 信心：{decision_holding.confidence:.2%}")
    print(f"   🗳️  投票明细：")
    for vote in decision_holding.all_votes:
        emoji = "✅" if vote.action in ['close', 'sell'] else "⚠️" if vote.action == 'hold' else "❌"
        weight = vote.weight if hasattr(vote, 'weight') else 0.0
        print(f"      {emoji} {vote.voter_category}: {vote.action} (信心 {vote.confidence:.2%}, 原因: {vote.reason[:30]}...)")
    
    # 场景2：空仓观望
    print("\n【场景2】空仓观望，是否抄底？")
    print("-" * 60)
    context_empty = {
        'world_signature': world_signature,
        'position': {'amount': 0.0, 'side': 'none'},  # 空仓
        'unrealized_pnl': 0.0,
        'account_health': 1.0,  # 账户健康
        'market_data': {
            'close': 500,
            'volume': 50000,
            'returns': [-0.15, -0.20, -0.18, -0.22, -0.16]
        }
    }
    
    decision_empty = daimon.guide(context_empty)
    print(f"\n   💡 决策：{decision_empty.action}")
    print(f"   📊 信心：{decision_empty.confidence:.2%}")
    print(f"   🗳️  投票明细：")
    for vote in decision_empty.all_votes:
        emoji = "✅" if vote.action in ['hold', 'sell'] else "⚠️" if vote.action == 'buy' else "❌"
        weight = vote.weight if hasattr(vote, 'weight') else 0.0
        print(f"      {emoji} {vote.voter_category}: {vote.action} (信心 {vote.confidence:.2%}, 原因: {vote.reason[:30]}...)")
    
    # 场景3：做空获利
    print("\n【场景3】做空持仓，已盈利300%，是否平仓？")
    print("-" * 60)
    context_short = {
        'world_signature': world_signature,
        'position': {'amount': 1.0, 'side': 'short'},  # 做空
        'unrealized_pnl': 3.0,  # 盈利300%
        'account_health': 4.0,  # 账户暴涨
        'market_data': {
            'close': 500,
            'volume': 50000,
            'returns': [-0.15, -0.20, -0.18, -0.22, -0.16]
        }
    }
    
    decision_short = daimon.guide(context_short)
    print(f"\n   💡 决策：{decision_short.action}")
    print(f"   📊 信心：{decision_short.confidence:.2%}")
    print(f"   🗳️  投票明细：")
    for vote in decision_short.all_votes:
        emoji = "✅" if vote.action in ['close', 'hold'] else "⚠️"
        weight = vote.weight if hasattr(vote, 'weight') else 0.0
        print(f"      {emoji} {vote.voter_category}: {vote.action} (信心 {vote.confidence:.2%}, 原因: {vote.reason[:30]}...)")
    
    # 分析系统响应
    print("\n" + "=" * 60)
    print("🎯 系统响应分析")
    print("=" * 60 + "\n")
    
    correct_count = 0
    total_count = 3
    
    # 场景1评估
    if decision_holding.action in ['close', 'sell']:
        print("✅ 场景1（持仓）：正确 - 立即止损")
        correct_count += 1
        if decision_holding.confidence > 0.7:
            print("   ↳ 高信心止损 - 「恐惧反应充足」🟢")
        else:
            print("   ↳ 低信心止损 - 「恐惧反应不足」🟡")
    else:
        print("❌ 场景1（持仓）：错误 - 应该立即止损！🔴")
        print("   ↳ 这是致命缺陷！")
    
    # 场景2评估
    if decision_empty.action in ['hold', 'sell']:
        print("✅ 场景2（空仓）：正确 - 不抄底")
        correct_count += 1
        print("   ↳ 理性控制贪婪 🟢")
    else:
        print("❌ 场景2（空仓）：错误 - 不应该抄底！🔴")
        print("   ↳ 「贪婪战胜恐惧」- 危险信号！")
    
    # 场景3评估
    if decision_short.action in ['close', 'hold']:
        print("✅ 场景3（做空）：合理 - 平仓或持有")
        correct_count += 1
    else:
        print("⚠️  场景3（做空）：可疑 - 为何要反向操作？")
    
    accuracy = correct_count / total_count
    print(f"\n📊 决策准确率：{accuracy:.1%} ({correct_count}/{total_count})")
    
    # 最终评估
    print("\n" + "=" * 60)
    print("💭 最终评估")
    print("=" * 60 + "\n")
    
    if decision_holding.action not in ['close', 'sell']:
        print("🚨 严重警告：系统在-99%崩盘中不止损！")
        print("\n这意味着：")
        print("   ❌ 1. 风险控制机制失效")
        print("   ❌ 2. Danger信号未被重视")
        print("   ❌ 3. 「求生本能」不足")
        print("\n⚠️  这是致命缺陷！必须修复！")
        print("\n修复建议：")
        print("   1. 提高instinct_voice对danger的敏感度")
        print("   2. 增加world_signature_voice的权重")
        print("   3. 添加硬性风控规则（-30%必须止损）")
        
    elif accuracy < 0.8:
        print("🟡 部分通过：系统能止损，但还有改进空间")
        print("\n优点：")
        print("   ✅ 持仓场景能正确止损")
        print("\n缺点：")
        if decision_empty.action == 'buy':
            print("   ⚠️  空仓时仍想抄底 - 贪婪控制不足")
        print("\n改进建议：")
        print("   1. 加强极端市场下的「恐惧」反应")
        print("   2. 降低「贪婪」在危险环境中的影响")
        
    else:
        print("🎉 优秀！系统通过极端压力测试！")
        print("\n系统表现：")
        print("   ✅ 持仓时能坚决止损")
        print("   ✅ 空仓时能抵制抄底诱惑")
        print("   ✅ 盈利时能理性决策")
        print("\n这表明：")
        print("   1. ✅ 风险控制机制有效")
        print("   2. ✅ Danger信号被正确识别")
        print("   3. ✅ 「求生本能」充足")
        print("   4. ✅ 情绪控制良好")
    
    print("\n" + "🚨" * 30)
    print("测试完成！")
    print("🚨" * 30 + "\n")
    
    return {
        'holding': decision_holding,
        'empty': decision_empty,
        'short': decision_short,
        'accuracy': accuracy
    }


if __name__ == '__main__':
    results = test_daimon_in_extreme_crash()

