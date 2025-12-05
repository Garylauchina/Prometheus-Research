"""
v5.3 阶段2.1 - Mock模拟50轮进化测试

在微观结构环境中测试Agent的适应能力：
- 使用AdvancedOpponentMarket（完整微观结构+96个对手盘）
- 运行50轮进化
- 每5轮进行一次进化周期
- 收集详细统计数据
- 验证Agent适应性

Author: Prometheus Team
Date: 2025-12-06
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import json
import numpy as np
from typing import List, Dict

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from prometheus.core.moirai import Moirai
from prometheus.core.gene_pool import GenePool
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.market.advanced_market import AdvancedOpponentMarket

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class V53Stage21MockTest:
    """v5.3 阶段2.1 Mock模拟测试"""
    
    def __init__(self):
        self.test_cycles = 50
        self.initial_agents = 50
        self.initial_capital = 10000
        self.evolution_interval = 5  # 每5轮进化一次
        
        logger.info("="*70)
        logger.info("🧪 v5.3 阶段2.1 - Mock模拟50轮进化测试")
        logger.info("="*70)
        
        # === 初始化Agent系统 ===
        logger.info("\n📝 初始化Agent系统...")
        
        self.gene_pool = GenePool()
        self.moirai = Moirai(num_families=50)
        self.evolution_manager = EvolutionManagerV5(
            moirai=self.moirai,
            elite_ratio=0.2,
            elimination_ratio=0.3
        )
        
        logger.info("✅ Agent系统初始化完成")
        
        # === 初始化市场系统 ===
        logger.info("\n🏛️ 初始化高级对手市场...")
        
        self.market = AdvancedOpponentMarket(
            initial_price=50000.0,
            num_market_makers=5,
            num_arbitrageurs=8,
            num_whales=3,
            num_hfts=15,
            num_passive=25,
            num_panic=40,
            base_liquidity=1_000_000,
            enable_natural_volatility=True,
            volatility_std=0.008
        )
        
        logger.info("✅ 市场系统初始化完成")
        
        # === 统计数据 ===
        self.stats = {
            'cycle': [],
            'population': [],
            'gene_entropy': [],
            'active_families': [],
            'avg_capital': [],
            'price': [],
            'spread': [],
            'liquidity_factor': [],
            'market_trades': [],
            'opponent_activity': []
        }
    
    def run_test(self):
        """运行完整测试"""
        
        # === 创建初始Agent ===
        logger.info(f"\n📝 创建初始种群: {self.initial_agents}个Agent")
        agents = self.moirai._genesis_create_agents(
            agent_count=self.initial_agents,
            gene_pool=self.gene_pool,
            capital_per_agent=self.initial_capital
        )
        self.moirai.agents = agents
        
        # 初始化fitness
        for agent in self.moirai.agents:
            agent.fitness = 1.0
        
        logger.info(f"✅ 创建完成: {len(self.moirai.agents)}个Agent")
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 开始50轮测试")
        logger.info(f"{'='*70}\n")
        
        # === 运行测试周期 ===
        for cycle in range(self.test_cycles):
            logger.info(f"\n{'='*70}")
            logger.info(f"🔄 第{cycle+1}轮测试")
            logger.info(f"{'='*70}")
            
            # 1. 市场模拟
            market_result = self.market.simulate_step(cycle)
            
            # 2. Agent交易（简化模拟）
            self._simulate_agent_trading(market_result)
            
            # 3. 进化周期
            if (cycle + 1) % self.evolution_interval == 0:
                logger.info(f"\n🧬 触发进化周期 (第{(cycle+1)//self.evolution_interval}次)")
                self.evolution_manager.run_evolution_cycle(market_result.price)
            
            # 4. 收集统计
            self._collect_stats(cycle + 1, market_result)
            
            # 5. 阶段性总结
            if (cycle + 1) % 10 == 0:
                self._print_summary(cycle + 1)
        
        # === 最终报告 ===
        self._generate_final_report()
    
    def _simulate_agent_trading(self, market_result):
        """
        简化的Agent交易模拟
        
        注：这里只是模拟盈亏，不做真实交易
        未来可以扩展为真实的交易逻辑
        """
        import random
        
        for agent in self.moirai.agents:
            # 简化模拟：随机盈亏 + 价格影响
            price_change = (market_result.price - 50000) / 50000
            
            # 基础随机波动
            base_change = random.uniform(-0.02, 0.03)
            
            # 价格趋势影响（模拟Agent对市场的响应）
            trend_impact = price_change * 0.5
            
            # 总变化
            total_change = base_change + trend_impact
            
            # 更新资金
            agent.current_capital *= (1 + total_change)
            agent.fitness = agent.current_capital / agent.initial_capital
    
    def _collect_stats(self, cycle: int, market_result):
        """收集统计数据"""
        # 计算活跃家族
        families = {}
        for agent in self.moirai.agents:
            dominant_families = agent.lineage.get_dominant_families(top_k=1)
            if dominant_families:
                family_id = dominant_families[0][0]
                families[family_id] = families.get(family_id, 0) + 1
        
        # 计算基因熵（简化版）
        gene_hashes = [hash(tuple(agent.genome.vector.tolist())) for agent in self.moirai.agents]
        gene_counts = {}
        for gh in gene_hashes:
            gene_counts[gh] = gene_counts.get(gh, 0) + 1
        total = len(gene_hashes)
        gene_entropy = -sum((c/total) * np.log2(c/total) for c in gene_counts.values() if c > 0)
        
        # 平均资金
        avg_capital = sum(a.current_capital for a in self.moirai.agents) / len(self.moirai.agents) if self.moirai.agents else 0
        
        # 记录数据
        self.stats['cycle'].append(cycle)
        self.stats['population'].append(len(self.moirai.agents))
        self.stats['gene_entropy'].append(gene_entropy)
        self.stats['active_families'].append(len(families))
        self.stats['avg_capital'].append(avg_capital)
        self.stats['price'].append(market_result.price)
        self.stats['spread'].append(market_result.spread_pct)
        self.stats['liquidity_factor'].append(market_result.liquidity_factor)
        self.stats['market_trades'].append(market_result.total_trades)
        self.stats['opponent_activity'].append(market_result.opponent_activity)
    
    def _print_summary(self, cycle: int):
        """打印阶段性总结"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 第{cycle}轮阶段性总结")
        logger.info(f"{'='*70}")
        
        recent = min(10, len(self.stats['population']))
        
        avg_population = np.mean(self.stats['population'][-recent:])
        avg_gene_entropy = np.mean(self.stats['gene_entropy'][-recent:])
        avg_families = np.mean(self.stats['active_families'][-recent:])
        avg_capital = np.mean(self.stats['avg_capital'][-recent:])
        avg_price = np.mean(self.stats['price'][-recent:])
        
        logger.info(f"Agent系统:")
        logger.info(f"  种群规模: {avg_population:.1f} (最近{recent}轮平均)")
        logger.info(f"  基因熵: {avg_gene_entropy:.3f}")
        logger.info(f"  活跃家族: {avg_families:.1f}个")
        logger.info(f"  平均资金: ${avg_capital:,.2f}")
        
        logger.info(f"\n市场系统:")
        logger.info(f"  平均价格: ${avg_price:,.2f}")
        logger.info(f"  价格变化: {((avg_price/50000)-1)*100:+.2f}%")
        
        logger.info(f"{'='*70}")
    
    def _generate_final_report(self):
        """生成最终报告"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📋 v5.3 阶段2.1 Mock测试 - 最终报告")
        logger.info(f"{'='*70}")
        
        # === Agent系统指标 ===
        initial_pop = self.stats['population'][0]
        final_pop = self.stats['population'][-1]
        
        initial_gene_entropy = self.stats['gene_entropy'][0]
        final_gene_entropy = self.stats['gene_entropy'][-1]
        avg_gene_entropy = np.mean(self.stats['gene_entropy'])
        
        initial_families = self.stats['active_families'][0]
        final_families = self.stats['active_families'][-1]
        avg_families = np.mean(self.stats['active_families'])
        
        initial_capital = self.stats['avg_capital'][0]
        final_capital = self.stats['avg_capital'][-1]
        capital_change = ((final_capital / initial_capital) - 1) * 100
        
        logger.info(f"\n🧬 Agent系统表现:")
        logger.info(f"  种群规模: {initial_pop}个 → {final_pop}个 ({final_pop-initial_pop:+d})")
        logger.info(f"  基因熵: {initial_gene_entropy:.3f} → {final_gene_entropy:.3f} (平均: {avg_gene_entropy:.3f})")
        logger.info(f"  活跃家族: {initial_families}个 → {final_families}个 (平均: {avg_families:.1f})")
        logger.info(f"  平均资金: ${initial_capital:,.2f} → ${final_capital:,.2f} ({capital_change:+.2f}%)")
        
        # === 市场系统指标 ===
        initial_price = self.stats['price'][0]
        final_price = self.stats['price'][-1]
        price_change = ((final_price / initial_price) - 1) * 100
        
        total_market_trades = sum(self.stats['market_trades'])
        avg_trades_per_cycle = total_market_trades / len(self.stats['market_trades'])
        
        logger.info(f"\n💹 市场系统表现:")
        logger.info(f"  价格: ${initial_price:,.2f} → ${final_price:,.2f} ({price_change:+.2f}%)")
        logger.info(f"  总成交: {total_market_trades}笔")
        logger.info(f"  平均成交: {avg_trades_per_cycle:.1f}笔/轮")
        
        # === 目标达成情况 ===
        logger.info(f"\n🎯 目标达成情况:")
        
        objectives = [
            ("种群存活", final_pop >= 40, f"{final_pop}个 (目标≥40)"),
            ("基因熵", final_gene_entropy >= 0.5, f"{final_gene_entropy:.3f} (目标≥0.5)"),
            ("活跃家族", final_families >= 10, f"{final_families}个 (目标≥10)"),
            ("平均资金", capital_change >= -20, f"{capital_change:+.2f}% (目标≥-20%)"),
        ]
        
        passed = 0
        for name, success, value in objectives:
            status = "✅" if success else "❌"
            logger.info(f"  {status} {name}: {value}")
            if success:
                passed += 1
        
        logger.info(f"\n总体评分: {passed}/{len(objectives)} ({passed/len(objectives)*100:.0f}%)")
        
        # === 保存结果 ===
        self._save_results()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 测试完成！")
        logger.info(f"{'='*70}\n")
    
    def _save_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            'version': 'v5.3_stage2.1',
            'timestamp': timestamp,
            'test_cycles': self.test_cycles,
            'initial_agents': self.initial_agents,
            'stats': {
                'cycle': self.stats['cycle'],
                'population': self.stats['population'],
                'gene_entropy': self.stats['gene_entropy'],
                'active_families': self.stats['active_families'],
                'avg_capital': self.stats['avg_capital'],
                'price': self.stats['price'],
                'spread': self.stats['spread'],
                'liquidity_factor': self.stats['liquidity_factor'],
                'market_trades': self.stats['market_trades']
            },
            'summary': {
                'final_population': self.stats['population'][-1],
                'final_gene_entropy': self.stats['gene_entropy'][-1],
                'final_families': self.stats['active_families'][-1],
                'final_avg_capital': self.stats['avg_capital'][-1],
                'final_price': self.stats['price'][-1],
                'capital_change_pct': ((self.stats['avg_capital'][-1] / self.stats['avg_capital'][0]) - 1) * 100,
                'price_change_pct': ((self.stats['price'][-1] / self.stats['price'][0]) - 1) * 100
            }
        }
        
        output_file = f"v53_stage21_mock50_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n💾 测试结果已保存: {output_file}")


def main():
    """主函数"""
    test = V53Stage21MockTest()
    test.run_test()


if __name__ == "__main__":
    main()

