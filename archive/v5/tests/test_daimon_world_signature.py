"""
测试Daimon理解WorldSignature

验证朋友的批评是否解决：
让Daimon从"盲"变成"明"！
"""

import logging
from prometheus.core.inner_council import Daimon, CouncilDecision
from prometheus.core.lineage import LineageVector
from prometheus.core.genome import GenomeVector
from prometheus.core.instinct import Instinct
from prometheus.core.agent_v5 import AgentV5, EmotionalState

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def create_test_agent() -> AgentV5:
    """创建测试Agent"""
    lineage = LineageVector.create_genesis(family_id=0)
    genome = GenomeVector.create_genesis()
    instinct = Instinct.create_genesis()
    
    agent = AgentV5(
        agent_id="test_agent",
        initial_capital=10000,
        lineage=lineage,
        genome=genome,
        instinct=instinct
    )
    
    return agent


def test_bull_market_signature():
    """测试牛市WorldSignature"""
    logger.info("="*70)
    logger.info("🐂 测试场景1：牛市WorldSignature")
    logger.info("="*70)
    
    agent = create_test_agent()
    daimon = Daimon(agent)
    
    # 构造牛市WorldSignature
    world_signature = {
        'drift': 0.02,        # +2%漂移
        'volatility': 0.02,   # 2%波动
        'trend_strength': 0.8, # 80%趋势强度
        'entropy': 0.3,       # 30%熵
        'regime_label': 'steady_bull'
    }
    
    context = {
        'world_signature': world_signature,  # ✨ 关键！
        'capital_ratio': 1.0,
        'position': {'amount': 0, 'side': None},
        'recent_pnl': 0,
        'consecutive_losses': 0,
        'market_data': {},
        'bulletins': {}
    }
    
    # 让Daimon决策
    decision = daimon.guide(context)
    
    logger.info(f"\n决策结果:")
    logger.info(f"  行动: {decision.action}")
    logger.info(f"  信心: {decision.confidence:.1%}")
    logger.info(f"  推理: {decision.reasoning}")
    
    logger.info(f"\n投票详情:")
    for vote in decision.all_votes:
        logger.info(f"  [{vote.voter_category:15s}] {vote.action:5s} "
                   f"{vote.confidence:.1%} - {vote.reason}")
    
    return decision


def test_bear_market_signature():
    """测试熊市WorldSignature"""
    logger.info(f"\n{'='*70}")
    logger.info("🐻 测试场景2：熊市WorldSignature")
    logger.info("="*70)
    
    agent = create_test_agent()
    daimon = Daimon(agent)
    
    # 构造熊市WorldSignature（且有多头持仓）
    world_signature = {
        'drift': -0.03,       # -3%漂移
        'volatility': 0.05,   # 5%波动
        'trend_strength': 0.7, # 70%趋势强度
        'entropy': 0.5,       # 50%熵
        'regime_label': 'crash_bear'
    }
    
    context = {
        'world_signature': world_signature,  # ✨ 关键！
        'capital_ratio': 0.9,
        'position': {'amount': 1.0, 'side': 'long'},  # 有多头持仓
        'recent_pnl': -0.1,  # 亏10%
        'consecutive_losses': 1,
        'market_data': {},
        'bulletins': {}
    }
    
    # 让Daimon决策
    decision = daimon.guide(context)
    
    logger.info(f"\n决策结果:")
    logger.info(f"  行动: {decision.action}")
    logger.info(f"  信心: {decision.confidence:.1%}")
    logger.info(f"  推理: {decision.reasoning}")
    
    logger.info(f"\n投票详情:")
    for vote in decision.all_votes:
        logger.info(f"  [{vote.voter_category:15s}] {vote.action:5s} "
                   f"{vote.confidence:.1%} - {vote.reason}")
    
    return decision


def test_volatile_signature():
    """测试高波震荡WorldSignature"""
    logger.info(f"\n{'='*70}")
    logger.info("🌪️  测试场景3：高波震荡WorldSignature")
    logger.info("="*70)
    
    agent = create_test_agent()
    daimon = Daimon(agent)
    
    # 构造高波震荡WorldSignature
    world_signature = {
        'drift': 0.0,         # 无漂移
        'volatility': 0.08,   # 8%波动
        'trend_strength': 0.2, # 20%趋势强度
        'entropy': 0.8,       # 80%熵（混乱）
        'regime_label': 'high_volatility'
    }
    
    context = {
        'world_signature': world_signature,  # ✨ 关键！
        'capital_ratio': 1.0,
        'position': {'amount': 1.0, 'side': 'long'},  # 有持仓
        'recent_pnl': 0.05,
        'consecutive_losses': 0,
        'market_data': {},
        'bulletins': {}
    }
    
    # 让Daimon决策
    decision = daimon.guide(context)
    
    logger.info(f"\n决策结果:")
    logger.info(f"  行动: {decision.action}")
    logger.info(f"  信心: {decision.confidence:.1%}")
    logger.info(f"  推理: {decision.reasoning}")
    
    logger.info(f"\n投票详情:")
    for vote in decision.all_votes:
        logger.info(f"  [{vote.voter_category:15s}] {vote.action:5s} "
                   f"{vote.confidence:.1%} - {vote.reason}")
    
    return decision


def test_without_world_signature():
    """测试没有WorldSignature（旧版）"""
    logger.info(f"\n{'='*70}")
    logger.info("❌ 测试场景4：没有WorldSignature（盲的）")
    logger.info("="*70)
    
    agent = create_test_agent()
    daimon = Daimon(agent)
    
    context = {
        # ❌ 没有world_signature！
        'capital_ratio': 1.0,
        'position': {'amount': 0, 'side': None},
        'recent_pnl': 0,
        'consecutive_losses': 0,
        'market_data': {},
        'bulletins': {}
    }
    
    # 让Daimon决策
    decision = daimon.guide(context)
    
    logger.info(f"\n决策结果:")
    logger.info(f"  行动: {decision.action}")
    logger.info(f"  信心: {decision.confidence:.1%}")
    logger.info(f"  推理: {decision.reasoning}")
    
    logger.info(f"\n投票详情:")
    for vote in decision.all_votes:
        logger.info(f"  [{vote.voter_category:15s}] {vote.action:5s} "
                   f"{vote.confidence:.1%} - {vote.reason}")
    
    logger.info(f"\n💡 注意:")
    logger.info(f"  没有world_signature投票！")
    logger.info(f"  Daimon是'盲'的，只能靠本能和情绪")
    
    return decision


def demonstrate_comparison():
    """对比：有无WorldSignature的差异"""
    logger.info(f"\n{'='*70}")
    logger.info("🔍 对比：有无WorldSignature的决策差异")
    logger.info("="*70)
    
    agent = create_test_agent()
    daimon = Daimon(agent)
    
    # 相同的基础context
    base_context = {
        'capital_ratio': 1.0,
        'position': {'amount': 0, 'side': None},
        'recent_pnl': 0,
        'consecutive_losses': 0,
        'market_data': {},
        'bulletins': {}
    }
    
    # 情况1：没有WorldSignature
    context_blind = base_context.copy()
    decision_blind = daimon.guide(context_blind)
    
    # 情况2：有WorldSignature（牛市）
    context_aware = base_context.copy()
    context_aware['world_signature'] = {
        'drift': 0.02,
        'volatility': 0.02,
        'trend_strength': 0.8,
        'entropy': 0.3,
        'regime_label': 'steady_bull'
    }
    decision_aware = daimon.guide(context_aware)
    
    logger.info(f"\n❌ 没有WorldSignature（盲的）:")
    logger.info(f"  决策: {decision_blind.action}")
    logger.info(f"  信心: {decision_blind.confidence:.1%}")
    logger.info(f"  投票数: {len(decision_blind.all_votes)}")
    logger.info(f"  有world_signature投票: {'world_signature' in [v.voter_category for v in decision_blind.all_votes]}")
    
    logger.info(f"\n✅ 有WorldSignature（明的）:")
    logger.info(f"  决策: {decision_aware.action}")
    logger.info(f"  信心: {decision_aware.confidence:.1%}")
    logger.info(f"  投票数: {len(decision_aware.all_votes)}")
    logger.info(f"  有world_signature投票: {'world_signature' in [v.voter_category for v in decision_aware.all_votes]}")
    
    # 找出world_signature的投票
    ws_votes = [v for v in decision_aware.all_votes if v.voter_category == 'world_signature']
    if ws_votes:
        logger.info(f"\n  WorldSignature投票详情:")
        for vote in ws_votes:
            logger.info(f"    → {vote.action}({vote.confidence:.1%}): {vote.reason}")


def main():
    """主函数"""
    logger.info("="*70)
    logger.info("🧪 Daimon WorldSignature 集成测试")
    logger.info("="*70)
    logger.info("\n验证：Daimon是否能理解WorldSignature？")
    logger.info("目标：从'盲'变成'明'！\n")
    
    # 测试1：牛市
    test_bull_market_signature()
    
    # 测试2：熊市
    test_bear_market_signature()
    
    # 测试3：高波震荡
    test_volatile_signature()
    
    # 测试4：没有WorldSignature
    test_without_world_signature()
    
    # 对比测试
    demonstrate_comparison()
    
    # 总结
    logger.info(f"\n{'='*70}")
    logger.info("🎊 核心价值")
    logger.info("="*70)
    logger.info("""
朋友的批评：
❌ Agent是"盲"的，不知道世界是什么

现在的解决：
✅ Daimon新增"world_signature"声音
✅ 权重0.8（仅次于本能1.0）
✅ 基于5个特征做决策：
   - drift（漂移率）
   - volatility（波动率）
   - trend_strength（趋势强度）
   - entropy（熵）
   - regime_label（世界标签）
✅ Daimon现在"知道"它在什么世界中！

下一步：
- 集成到Mock训练学校
- 运行完整训练验证效果
- 对比有无WorldSignature的学习差异
    """)
    
    logger.info("="*70)


if __name__ == "__main__":
    main()

