"""
测试WorldSignature训练数据生成

验证朋友第一优先级建议的实现
"""

import logging
from prometheus.training.signature_training import (
    SignatureAwareTrainingGenerator,
    SignatureEnrichedData
)
from prometheus.training.regime_generators import BullMarketGenerator, BearMarketGenerator

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_bull_market():
    """测试牛市训练数据"""
    logger.info("="*70)
    logger.info("🐂 测试牛市WorldSignature训练数据")
    logger.info("="*70)
    
    # 创建牛市生成器
    bull_gen = BullMarketGenerator()
    
    # 创建signature-aware生成器
    sig_gen = SignatureAwareTrainingGenerator(
        regime_generator=bull_gen
    )
    
    # 生成训练数据
    data = sig_gen.generate_training_data(days=100)
    
    # 显示前5天
    logger.info(f"\n前5天数据:")
    for d in data[:5]:
        logger.info(f"\n  Day {d.day}:")
        logger.info(f"    价格: ${d.price:,.2f}")
        logger.info(f"    drift: {d.drift:+.4f}")
        logger.info(f"    volatility: {d.volatility:.4f}")
        logger.info(f"    trend_strength: {d.trend_strength:.4f}")
        logger.info(f"    entropy: {d.entropy:.4f}")
        logger.info(f"    regime: {d.regime_label}")
    
    # 统计
    stats = sig_gen.get_statistics(data)
    logger.info(f"\n统计信息:")
    logger.info(f"  总天数: {stats['total_days']}")
    logger.info(f"  总收益: {stats['total_return']:+.1f}%")
    logger.info(f"  平均drift: {stats['avg_drift']:+.4f}")
    logger.info(f"  平均volatility: {stats['avg_volatility']:.4f}")
    logger.info(f"\n  Regime分布:")
    for regime, pct in stats['regime_distribution'].items():
        logger.info(f"    {regime}: {pct:.1f}%")
    
    return data


def test_bear_market():
    """测试熊市训练数据"""
    logger.info(f"\n{'='*70}")
    logger.info("🐻 测试熊市WorldSignature训练数据")
    logger.info("="*70)
    
    # 创建熊市生成器
    bear_gen = BearMarketGenerator()
    
    # 创建signature-aware生成器
    sig_gen = SignatureAwareTrainingGenerator(
        regime_generator=bear_gen
    )
    
    # 生成训练数据
    data = sig_gen.generate_training_data(days=100)
    
    # 统计
    stats = sig_gen.get_statistics(data)
    logger.info(f"\n统计信息:")
    logger.info(f"  总天数: {stats['total_days']}")
    logger.info(f"  总收益: {stats['total_return']:+.1f}%")
    logger.info(f"  平均drift: {stats['avg_drift']:+.4f}")
    logger.info(f"  平均volatility: {stats['avg_volatility']:.4f}")
    logger.info(f"\n  Regime分布:")
    for regime, pct in stats['regime_distribution'].items():
        logger.info(f"    {regime}: {pct:.1f}%")
    
    return data


def demonstrate_agent_receives_signature():
    """演示Agent接收WorldSignature"""
    logger.info(f"\n{'='*70}")
    logger.info("🤖 演示：Agent现在接收什么数据")
    logger.info("="*70)
    
    bull_gen = BullMarketGenerator()
    sig_gen = SignatureAwareTrainingGenerator(regime_generator=bull_gen)
    data = sig_gen.generate_training_data(days=10)
    
    logger.info("\n❌ 之前Agent接收:")
    logger.info("   {")
    logger.info("     'price': 50000.0")
    logger.info("   }")
    
    logger.info("\n✅ 现在Agent接收:")
    sample = data[5]
    logger.info("   {")
    logger.info(f"     'price': {sample.price:.2f},")
    logger.info(f"     'drift': {sample.drift:+.4f},")
    logger.info(f"     'volatility': {sample.volatility:.4f},")
    logger.info(f"     'trend_strength': {sample.trend_strength:.4f},")
    logger.info(f"     'entropy': {sample.entropy:.4f},")
    logger.info(f"     'regime_label': '{sample.regime_label}'")
    logger.info("   }")
    
    logger.info("\n💡 关键差异:")
    logger.info("   之前：Agent是'盲'的，不知道世界")
    logger.info("   现在：Agent'知道'它在什么世界中！")


def main():
    """主函数"""
    logger.info("="*70)
    logger.info("🎯 WorldSignature训练数据 - 完整测试")
    logger.info("="*70)
    logger.info("\n实现朋友的第一优先级建议：")
    logger.info("✅ 每条训练数据都带WorldSignature标签")
    
    # 测试牛市
    bull_data = test_bull_market()
    
    # 测试熊市
    bear_data = test_bear_market()
    
    # 演示Agent接收数据
    demonstrate_agent_receives_signature()
    
    # 总结
    logger.info(f"\n{'='*70}")
    logger.info("🎊 核心价值")
    logger.info("="*70)
    logger.info("""
朋友指出的核心问题：
❌ Agent不知道"世界是什么"

现在的解决方案：
✅ 每一天都带上WorldSignature标签
✅ 包含：drift, vol, trend_strength, entropy, label
✅ Agent现在"知道"它在什么世界中

下一步：
1. 让Agent学会使用这些信息
2. Memory Layer记录"在X世界，Y策略有效"
3. 实现真正的contextual meta-learning
    """)
    
    logger.info("="*70)


if __name__ == "__main__":
    main()

