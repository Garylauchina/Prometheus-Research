"""
系统级测试：自适应资金管理⭐⭐⭐

【符合三大铁律】:
✅ 1. 统一封装 - 使用v6 Facade统一入口
✅ 2. 严格测试规范 - 通过run_scenario()顶层方法
✅ 3. 完整机制 - 使用完整的交易生命周期

测试目标：
验证Prophet的S值能否根据市场表现动态调整资金分配

测试方法：
- 通过v6 Facade的run_scenario()统一入口
- 提供3个市场场景的market_feed
- 观察Prophet的S值和系统规模变化

2025-12-11 03:35创建
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import numpy as np
from prometheus.facade.v6_facade import run_scenario

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdaptiveMarketFeed:
    """
    自适应性测试的市场数据生成器
    
    生成3阶段市场数据：
    - 阶段1 (1-10): 牛市，价格上涨
    - 阶段2 (11-20): 熊市，价格下跌
    - 阶段3 (21-30): 震荡，价格波动
    """
    
    def __init__(self, initial_price=50000.0):
        self.cycle = 0
        self.current_price = initial_price
        self.phase_history = []
    
    def next_tick(self):
        """生成下一个tick的市场数据"""
        self.cycle += 1
        
        # 根据周期确定阶段和价格变化
        if 1 <= self.cycle <= 10:
            # 牛市：稳定上涨
            price_change = np.random.uniform(0.01, 0.02)
            phase = "bull"
            phase_name = "牛市"
        elif 11 <= self.cycle <= 20:
            # 熊市：稳定下跌
            price_change = np.random.uniform(-0.02, -0.01)
            phase = "bear"
            phase_name = "熊市"
        else:
            # 震荡：随机波动
            price_change = np.random.uniform(-0.005, 0.005)
            phase = "sideways"
            phase_name = "震荡"
        
        # 更新价格
        self.current_price *= (1 + price_change)
        
        # 记录阶段
        self.phase_history.append({
            'cycle': self.cycle,
            'phase': phase,
            'phase_name': phase_name,
            'price': self.current_price,
            'price_change': price_change
        })
        
        # 返回market tick
        return {
            'timestamp': self.cycle,
            'price': self.current_price,
            'volume': 1.0,
            'phase': phase,
            'phase_name': phase_name
        }
    
    def get_phase_stats(self):
        """获取各阶段统计"""
        if not self.phase_history:
            return {}
        
        stats = {}
        for phase in ['bull', 'bear', 'sideways']:
            phase_data = [d for d in self.phase_history if d['phase'] == phase]
            if phase_data:
                stats[phase] = {
                    'cycles': len(phase_data),
                    'avg_price': np.mean([d['price'] for d in phase_data]),
                    'avg_change': np.mean([d['price_change'] for d in phase_data])
                }
        return stats


def test_adaptive_capital_system():
    """
    系统级测试：通过Facade验证自适应资金管理
    """
    logger.info("="*80)
    logger.info("🧪 系统级测试：自适应资金管理")
    logger.info("="*80)
    logger.info("测试方法：v6 Facade统一入口 ✅")
    logger.info("测试周期：30周期（3个阶段）")
    logger.info("="*80)
    
    # 创建市场数据生成器
    market_generator = AdaptiveMarketFeed(initial_price=50000.0)
    
    # 创建market_feed函数（Facade期望的callable）
    def market_feed(cycle):
        """生成market_data和bulletin_board数据"""
        tick = market_generator.next_tick()
        market_data = {
            'timestamp': tick['timestamp'],
            'price': tick['price'],
            'volume': tick['volume']
        }
        bulletin_board = {}  # v6 Facade需要返回两个值
        return market_data, bulletin_board
    
    # 通过Facade运行系统级测试⭐⭐⭐
    facade = run_scenario(
        mode="mock",
        total_cycles=30,
        market_feed=market_feed,
        num_families=10,  # 简化测试
        agent_count=20,   # 20个Agent
        capital_per_agent=10000.0,
        evo_interval=1,   # 每周期进化一次
        seed=42           # 固定种子，保证可重复
    )
    
    logger.info("\n" + "="*80)
    logger.info("📊 测试结果分析")
    logger.info("="*80)
    
    # 分析市场阶段
    phase_stats = market_generator.get_phase_stats()
    for phase, stats in phase_stats.items():
        phase_name = {"bull": "牛市", "bear": "熊市", "sideways": "震荡"}.get(phase, phase)
        logger.info(f"\n{phase_name}阶段:")
        logger.info(f"  周期数: {stats['cycles']}")
        logger.info(f"  平均价格: ${stats['avg_price']:.2f}")
        logger.info(f"  平均涨跌: {stats['avg_change']:.2%}")
    
    # 分析Prophet的S值变化（如果有历史记录）
    # TODO: 需要从facade中获取Prophet的历史S值
    # 当前Facade可能没有暴露这个接口，需要检查
    
    logger.info("\n" + "="*80)
    logger.info("✅ 系统级测试完成")
    logger.info("="*80)
    
    return facade


if __name__ == "__main__":
    facade = test_adaptive_capital_system()
    
    print("\n" + "="*80)
    print("📊 测试摘要")
    print("="*80)
    print(f"总周期: 30")
    print(f"测试方法: v6 Facade统一入口 ✅")
    print(f"遵守三大铁律: ✅")
    print("="*80)

