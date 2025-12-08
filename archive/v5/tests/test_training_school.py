"""
测试Mock训练学校

验证多情境训练系统
"""

import numpy as np
import logging
from datetime import datetime

from prometheus.training import (
    MockTrainingSchool,
    BullMarketGenerator,
    BearMarketGenerator,
    VolatilityGenerator,
    SidewaysGenerator,
    create_standard_multi_regime
)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)


def test_regime_generators():
    """测试各种regime生成器"""
    print("="*70)
    print("🧪 测试Regime生成器")
    print("="*70)
    
    generators = [
        ("牛市", BullMarketGenerator()),
        ("熊市", BearMarketGenerator()),
        ("高波震荡", VolatilityGenerator()),
        ("低波盘整", SidewaysGenerator())
    ]
    
    for name, gen in generators:
        print(f"\n📊 {name}:")
        prices = gen.generate_series(days=100)
        stats = gen.get_statistics()
        
        print(f"  起始: ${stats['start_price']:,.0f}")
        print(f"  结束: ${stats['end_price']:,.0f}")
        print(f"  总收益: {stats['total_return']:+.1f}%")
        print(f"  平均日收益: {stats['avg_daily_return']:+.2f}%")
        print(f"  波动率: {stats['volatility']:.2f}%")
    
    print(f"\n{'='*70}")
    print("✅ Regime生成器测试完成")
    print(f"{'='*70}")


def test_multi_regime():
    """测试多regime生成器"""
    print(f"\n{'='*70}")
    print("🎭 测试多Regime生成器")
    print(f"{'='*70}")
    
    gen = create_standard_multi_regime()
    prices, regime_history = gen.generate_series(days=365, start_price=50000)
    stats = gen.get_statistics()
    
    print(f"\n生成结果:")
    print(f"  总天数: {stats['total_days']}")
    print(f"  总收益: {stats['total_return']:+.1f}%")
    print(f"  波动率: {stats['volatility']:.2f}%")
    print(f"  Regime切换: {stats['regime_switches']}次")
    
    print(f"\nRegime分布:")
    for regime, pct in stats['regime_distribution'].items():
        print(f"  {regime}: {pct:.1f}%")
    
    print(f"\n{'='*70}")
    print("✅ 多Regime生成器测试完成")
    print(f"{'='*70}")


def test_training_school():
    """测试训练学校"""
    print(f"\n{'='*70}")
    print("🏫 测试Mock训练学校")
    print(f"{'='*70}")
    
    school = MockTrainingSchool()
    
    # 测试单个课程
    session = school.curriculum.get_session(0)
    
    # 这里传None作为agent_system（因为我们还没有完整实现）
    # 实际应该传入真实的agent系统
    result = school.train_session(
        agent_system=None,
        session=session,
        verbose=True
    )
    
    print(f"\n课程结果:")
    print(f"  通过: {'✅' if result['passed'] else '❌'}")
    print(f"  ROI: {result['roi']:+.1f}%")
    print(f"  超额收益: {result['excess_return']:+.1f}%")
    
    print(f"\n{'='*70}")
    print("✅ 训练学校测试完成")
    print(f"{'='*70}")


def test_full_curriculum():
    """测试完整课程"""
    print(f"\n{'='*70}")
    print("🎓 测试完整课程体系")
    print(f"{'='*70}")
    
    school = MockTrainingSchool()
    
    # 运行完整课程（简化版）
    # 实际应该传入真实的agent系统
    summary = school.run_full_curriculum(
        agent_system=None,
        early_stop=False
    )
    
    print(f"\n最终总结:")
    print(f"  完成课程: {summary['total_sessions']}/{len(school.curriculum.sessions)}")
    print(f"  通过课程: {summary['passed_sessions']}/{summary['total_sessions']}")
    print(f"  通过率: {summary['pass_rate']:.0f}%")
    
    # 详细结果
    print(f"\n各课程表现:")
    for result in summary['results']:
        status = "✅" if result['passed'] else "❌"
        print(f"  {status} {result['session_name']}: "
              f"ROI {result['roi']:+.1f}% "
              f"(超额 {result['excess_return']:+.1f}%)")
    
    print(f"\n{'='*70}")


def demo_training_progression():
    """展示训练进程"""
    print(f"\n{'='*70}")
    print("🎬 训练进程演示")
    print(f"{'='*70}")
    
    school = MockTrainingSchool()
    
    print(f"\n课程列表:")
    for i, session in enumerate(school.curriculum.sessions, 1):
        print(f"\n{i}. {session.name}")
        print(f"   描述: {session.description}")
        print(f"   难度: {'⭐' * session.difficulty}")
        print(f"   天数: {session.duration_days}天")
        print(f"   通过标准:")
        print(f"     - 最低ROI: {session.pass_criteria['min_roi']}%")
        print(f"     - 跑赢率: {session.pass_criteria['beat_market_rate']*100:.0f}%")
    
    print(f"\n{'='*70}")
    print("💡 训练哲学")
    print(f"{'='*70}")
    print("""
渐进式训练：
1. 先学会单一环境（牛市、熊市、震荡、盘整）
2. 再学会环境切换（简单 → 复杂）
3. 最后掌握全环境适应

就像AlphaZero:
- 不是直接面对大师
- 而是通过自我对弈逐步提升
- Prometheus通过多情境训练逐步适应

这就是"进化学习"的本质！
    """)


def main():
    """主函数"""
    print("="*70)
    print("🧪 Mock训练学校 - 完整测试")
    print("="*70)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试Regime生成器
    test_regime_generators()
    
    # 2. 测试多Regime生成器
    test_multi_regime()
    
    # 3. 测试训练学校
    test_training_school()
    
    # 4. 测试完整课程
    test_full_curriculum()
    
    # 5. 展示训练进程
    demo_training_progression()
    
    print(f"\n{'='*70}")
    print("🎊 所有测试完成！")
    print(f"{'='*70}")
    
    print(f"\n✅ 成果:")
    print(f"  1. 4种基本Regime生成器")
    print(f"  2. 多Regime切换系统")
    print(f"  3. 6门渐进式训练课程")
    print(f"  4. 完整的训练评估体系")
    
    print(f"\n📋 下一步:")
    print(f"  1. 集成真实Agent系统")
    print(f"  2. 实现WorldSignature感知")
    print(f"  3. 配合Memory Layer记录经验")
    print(f"  4. 运行大规模训练验证")
    
    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()

