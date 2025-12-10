"""
Prometheus v7.0 - 核心集成测试

测试Prophet + Moirai的完整信息流⭐⭐⭐
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prometheus.core.prophet_v7 import ProphetV7
from prometheus.core.moirai_v7 import MoiraiV7
import logging

logger = logging.getLogger(__name__)


class SimpleBulletinBoard:
    """简单的公告板（用于测试）"""
    
    def __init__(self):
        self.data = {}
    
    def publish(self, key: str, value: dict):
        """发布数据"""
        self.data[key] = value
    
    def get(self, key: str):
        """获取数据"""
        return self.data.get(key)


def test_prophet_moirai_integration():
    """
    测试Prophet + Moirai集成⭐⭐⭐
    
    场景：
      1. 模拟初始状态（系统规模50%）
      2. 模拟牛市场景（价格上涨，Agent表现好）
      3. Prophet计算S+E
      4. Moirai自主决策
      5. 验证系统扩张
    """
    
    logger.info("="*60)
    logger.info("🧪 测试：Prophet + Moirai集成")
    logger.info("="*60)
    
    # ===== 初始化 =====
    
    bb = SimpleBulletinBoard()
    prophet = ProphetV7(bb)
    
    # 暂时不创建真实的EvolutionManager，只测试决策逻辑
    moirai = MoiraiV7.__new__(MoiraiV7)
    moirai.bulletin_board = bb
    moirai.current_scale = 0.5  # 当前规模50%
    
    logger.info("\n📊 初始状态:")
    logger.info(f"   系统规模: {moirai.current_scale:.0%}")
    
    # ===== 场景1：牛市，Agent表现好⭐ =====
    
    logger.info("\n" + "="*60)
    logger.info("📈 场景1：牛市，Agent表现好")
    logger.info("="*60)
    
    # 模拟Moirai报告（Agent表现很好）
    bb.publish('moirai_report', {
        'survival_rate': 0.85,    # 存活率高
        'avg_roi': 0.30,          # ROI高
        'diversity': 0.70,        # 多样性好
    })
    
    # 模拟WorldSignature（牛市）
    bb.publish('world_signature', {
        'price_change_24h': 0.10,    # 价格上涨10%
        'volume_ratio': 1.8,         # 成交量增加
        'volatility_24h': 0.04,
        'volatility_change': 0.02,
    })
    
    # Prophet发布公告
    prophet.run_decision_cycle()
    
    # Moirai自主决策
    announcement = bb.get('prophet_announcement')
    S = announcement['reproduction_target']
    E = announcement['E']
    
    new_scale = moirai.decide(S, E)
    
    logger.info(f"\n✅ 场景1结果:")
    logger.info(f"   Prophet计算: S={S:.2f}, E={E:+.2f}")
    logger.info(f"   Moirai决策: {moirai.current_scale:.0%}")
    logger.info(f"   预期: 系统应该扩张（S高，E正）")
    
    assert new_scale > 0.5, "❌ 牛市应该扩张系统"
    logger.info(f"   ✅ 测试通过：系统扩张到{new_scale:.0%}")
    
    # ===== 场景2：熊市，Agent表现差⭐ =====
    
    logger.info("\n" + "="*60)
    logger.info("📉 场景2：熊市，Agent表现差")
    logger.info("="*60)
    
    # 模拟Moirai报告（Agent表现很差）
    bb.publish('moirai_report', {
        'survival_rate': 0.40,    # 存活率低
        'avg_roi': -0.15,         # ROI负
        'diversity': 0.50,        # 多样性一般
    })
    
    # 模拟WorldSignature（熊市）
    bb.publish('world_signature', {
        'price_change_24h': -0.12,   # 价格下跌12%
        'volume_ratio': 0.6,         # 成交量减少
        'volatility_24h': 0.08,
        'volatility_change': 0.04,   # 波动率增加
    })
    
    # Prophet发布公告
    prophet.run_decision_cycle()
    
    # Moirai自主决策
    announcement = bb.get('prophet_announcement')
    S = announcement['reproduction_target']
    E = announcement['E']
    
    old_scale = moirai.current_scale
    new_scale = moirai.decide(S, E)
    
    logger.info(f"\n✅ 场景2结果:")
    logger.info(f"   Prophet计算: S={S:.2f}, E={E:+.2f}")
    logger.info(f"   Moirai决策: {old_scale:.0%} → {new_scale:.0%}")
    logger.info(f"   预期: 系统应该收缩（S低，E负）")
    
    assert new_scale < old_scale, "❌ 熊市应该收缩系统"
    logger.info(f"   ✅ 测试通过：系统收缩到{new_scale:.0%}")
    
    # ===== 场景3：震荡市，Agent表现中等⭐ =====
    
    logger.info("\n" + "="*60)
    logger.info("😐 场景3：震荡市，Agent表现中等")
    logger.info("="*60)
    
    # 模拟Moirai报告（Agent表现中等）
    bb.publish('moirai_report', {
        'survival_rate': 0.60,    # 存活率中等
        'avg_roi': 0.05,          # ROI小幅盈利
        'diversity': 0.65,        # 多样性还行
    })
    
    # 模拟WorldSignature（震荡市）
    bb.publish('world_signature', {
        'price_change_24h': 0.02,    # 价格小幅上涨
        'volume_ratio': 1.1,         # 成交量略增
        'volatility_24h': 0.03,
        'volatility_change': 0.0,
    })
    
    # Prophet发布公告
    prophet.run_decision_cycle()
    
    # Moirai自主决策
    announcement = bb.get('prophet_announcement')
    S = announcement['reproduction_target']
    E = announcement['E']
    
    old_scale = moirai.current_scale
    new_scale = moirai.decide(S, E)
    
    logger.info(f"\n✅ 场景3结果:")
    logger.info(f"   Prophet计算: S={S:.2f}, E={E:+.2f}")
    logger.info(f"   Moirai决策: {old_scale:.0%} → {new_scale:.0%}")
    logger.info(f"   预期: 系统应该缓慢调整（E小）")
    
    # 震荡市，变化应该很小
    assert abs(new_scale - old_scale) < 0.1, "❌ 震荡市应该缓慢调整"
    logger.info(f"   ✅ 测试通过：系统缓慢调整到{new_scale:.0%}")
    
    # ===== 测试完成⭐⭐⭐ =====
    
    logger.info("\n" + "="*60)
    logger.info("🏆 测试结果汇总")
    logger.info("="*60)
    logger.info("✅ 场景1（牛市）：系统正确扩张")
    logger.info("✅ 场景2（熊市）：系统正确收缩")
    logger.info("✅ 场景3（震荡）：系统缓慢调整")
    logger.info("")
    logger.info("🎉 所有测试通过！Prophet + Moirai集成成功！⭐⭐⭐")
    logger.info("="*60)


def test_extreme_scenarios():
    """
    测试极端场景⭐
    
    验证系统在极端情况下的鲁棒性
    """
    
    logger.info("\n" + "="*60)
    logger.info("🧪 测试：极端场景")
    logger.info("="*60)
    
    bb = SimpleBulletinBoard()
    
    # 初始化Moirai
    moirai = MoiraiV7.__new__(MoiraiV7)
    moirai.bulletin_board = bb
    moirai.current_scale = 0.5
    
    # ===== 极端场景1：S=1.0, E=1.0（完美牛市）⭐ =====
    
    logger.info("\n📊 极端场景1：完美牛市（S=1.0, E=1.0）")
    new_scale = moirai.decide(S=1.0, E=1.0)
    logger.info(f"   结果: {new_scale:.2f}")
    assert new_scale <= 1.0, "❌ 规模应该限制在1.0"
    assert new_scale > 0.5, "❌ 完美牛市应该扩张"
    logger.info(f"   ✅ 测试通过")
    
    # ===== 极端场景2：S=0.0, E=-1.0（灾难熊市）⭐ =====
    
    moirai.current_scale = 0.5  # 重置
    logger.info("\n📊 极端场景2：灾难熊市（S=0.0, E=-1.0）")
    new_scale = moirai.decide(S=0.0, E=-1.0)
    logger.info(f"   结果: {new_scale:.2f}")
    assert new_scale >= 0.0, "❌ 规模应该限制在0.0以上"
    assert new_scale < 0.5, "❌ 灾难熊市应该收缩"
    logger.info(f"   ✅ 测试通过")
    
    # ===== 极端场景3：S=0.5, E=0.0（完全中性）⭐ =====
    
    moirai.current_scale = 0.5  # 重置
    logger.info("\n📊 极端场景3：完全中性（S=0.5, E=0.0）")
    new_scale = moirai.decide(S=0.5, E=0.0)
    logger.info(f"   结果: {new_scale:.2f}")
    assert abs(new_scale - 0.5) < 0.01, "❌ 完全中性应该不变"
    logger.info(f"   ✅ 测试通过")
    
    # ===== 极端场景4：快速震荡⭐ =====
    
    moirai.current_scale = 0.5  # 重置
    logger.info("\n📊 极端场景4：快速震荡（连续10次随机调整）")
    
    import random
    scales = [0.5]
    
    for i in range(10):
        S = random.uniform(0.3, 0.7)
        E = random.uniform(-0.3, 0.3)
        new_scale = moirai.decide(S, E)
        scales.append(new_scale)
        logger.debug(f"   第{i+1}次: S={S:.2f}, E={E:+.2f} → {new_scale:.2f}")
    
    # 验证规模始终在合理范围内
    assert all(0 <= s <= 1 for s in scales), "❌ 规模超出合理范围"
    logger.info(f"   最终规模: {scales[-1]:.2f}")
    logger.info(f"   ✅ 测试通过：系统稳定")
    
    logger.info("\n" + "="*60)
    logger.info("🎉 极端场景测试通过！系统鲁棒性良好！⭐")
    logger.info("="*60)


if __name__ == "__main__":
    """
    运行测试
    """
    
    # 配置logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "🚀 " + "="*58)
    print("🚀 Prometheus v7.0 - 核心集成测试")
    print("🚀 " + "="*58 + "\n")
    
    # 测试1：基本集成
    test_prophet_moirai_integration()
    
    # 测试2：极端场景
    test_extreme_scenarios()
    
    print("\n" + "🏆 " + "="*58)
    print("🏆 所有测试完成！v7.0核心功能正常！⭐⭐⭐")
    print("🏆 " + "="*58 + "\n")

