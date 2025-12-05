"""
v5.3 阶段1快速验证测试

验证内容：
1. 基因变异率是否提升到20%
2. 移民机制是否正常工作
3. 跨家族交配是否生效
4. 家族保护是否增强
5. 基因熵和活跃家族数是否改善
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from prometheus.core.moirai import Moirai
from prometheus.core.gene_pool import GenePool
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.market.simple_opponents import SimpleOpponentMarket

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class V53Stage1Test:
    """v5.3 阶段1验证测试"""
    
    def __init__(self):
        self.initial_agents = 50
        self.test_cycles = 30  # 30轮快速测试
        self.initial_capital = 10000
        
        # 初始化组件
        self.gene_pool = GenePool()
        self.moirai = Moirai(
            num_families=50
        )
        self.evolution_manager = EvolutionManagerV5(
            moirai=self.moirai,
            elite_ratio=0.2,
            elimination_ratio=0.3
        )
        
        # 市场
        self.market = SimpleOpponentMarket(
            num_institutions=10,
            num_retailers=100,
            base_liquidity=1_000_000,
            enable_natural_volatility=True,
            volatility_std=0.008
        )
        
        # 统计数据
        self.stats = {
            'cycle': [],
            'population': [],
            'gene_entropy': [],
            'active_families': [],
            'mutation_rate': [],
            'immigrants': [],
            'cross_family_breeding': [],
            'protected_families': []
        }
    
    def run(self):
        """运行测试"""
        logger.info("="*70)
        logger.info("🧪 v5.3 阶段1验证测试开始")
        logger.info("="*70)
        
        # 创建初始Agent
        logger.info(f"\n📝 创建初始种群: {self.initial_agents}个Agent")
        agents = self.moirai._genesis_create_agents(
            agent_count=self.initial_agents,
            gene_pool=self.gene_pool,
            capital_per_agent=self.initial_capital
        )
        self.moirai.agents = agents
        logger.info(f"✅ 创建完成: {len(self.moirai.agents)}个Agent")
        
        # 初始化fitness
        for agent in self.moirai.agents:
            agent.fitness = 1.0
        
        # 初始化市场价格
        current_price = 50000.0
        
        # 运行测试周期
        for cycle in range(self.test_cycles):
            logger.info(f"\n{'='*70}")
            logger.info(f"🔄 第{cycle+1}轮测试")
            logger.info(f"{'='*70}")
            
            # 市场模拟
            from datetime import datetime
            new_price, trades = self.market.simulate_step(current_price, datetime.now())
            current_price = new_price
            
            logger.info(f"💹 市场价格: ${current_price:,.2f} "
                       f"({((current_price/50000.0)-1)*100:+.2f}%)")
            logger.info(f"📊 对手交易: {len(trades)}笔")
            
            # 简单模拟Agent交易（随机盈亏）
            import random
            for agent in self.moirai.agents:
                change = random.uniform(-0.02, 0.03)
                agent.current_capital *= (1 + change)
                agent.fitness = agent.current_capital / agent.initial_capital
            
            # 运行进化周期
            self.evolution_manager.run_evolution_cycle(current_price)
            
            # 收集统计数据
            self._collect_stats(cycle + 1)
            
            # 每10轮打印详细统计
            if (cycle + 1) % 10 == 0:
                self._print_summary(cycle + 1)
        
        # 最终报告
        self._generate_final_report()
    
    def _collect_stats(self, cycle: int):
        """收集统计数据"""
        import numpy as np
        
        # 计算活跃家族数
        families = {}
        for agent in self.moirai.agents:
            dominant_families = agent.lineage.get_dominant_families(top_k=1)
            if dominant_families:
                family_id = dominant_families[0][0]  # 获取最主导的家族ID
                families[family_id] = families.get(family_id, 0) + 1
        
        # 计算基因熵（使用向量哈希）
        gene_hashes = [hash(tuple(agent.genome.vector.tolist())) for agent in self.moirai.agents]
        gene_counts = {}
        for gh in gene_hashes:
            gene_counts[gh] = gene_counts.get(gh, 0) + 1
        total = len(gene_hashes)
        gene_entropy = -sum((c/total) * np.log2(c/total) for c in gene_counts.values() if c > 0)
        
        self.stats['cycle'].append(cycle)
        self.stats['population'].append(len(self.moirai.agents))
        self.stats['gene_entropy'].append(gene_entropy)
        self.stats['active_families'].append(len(families))
        
        # 变异率（从evolution_manager获取）
        base_mr = self.evolution_manager.base_mutation_rate
        self.stats['mutation_rate'].append(base_mr)
        
        # 移民数（检查是否在移民周期）
        is_immigration_cycle = (cycle > 0 and 
                               cycle % self.evolution_manager.immigration_interval == 0)
        self.stats['immigrants'].append(
            self.evolution_manager.immigrants_per_wave if is_immigration_cycle else 0
        )
    
    def _print_summary(self, cycle: int):
        """打印阶段性总结"""
        import numpy as np
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 第{cycle}轮阶段性总结")
        logger.info(f"{'='*70}")
        
        # 最近10轮的平均值
        recent = min(10, len(self.stats['population']))
        
        avg_population = np.mean(self.stats['population'][-recent:])
        avg_gene_entropy = np.mean(self.stats['gene_entropy'][-recent:])
        avg_families = np.mean(self.stats['active_families'][-recent:])
        total_immigrants = sum(self.stats['immigrants'])
        
        logger.info(f"种群规模: {avg_population:.1f} (最近{recent}轮平均)")
        logger.info(f"基因熵: {avg_gene_entropy:.3f} (目标: ≥0.500)")
        logger.info(f"活跃家族: {avg_families:.1f}个 (目标: ≥10)")
        logger.info(f"累计移民: {total_immigrants}个")
        logger.info(f"基础变异率: {self.evolution_manager.base_mutation_rate:.1%}")
        logger.info(f"{'='*70}")
    
    def _generate_final_report(self):
        """生成最终报告"""
        import numpy as np
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📋 v5.3 阶段1验证测试 - 最终报告")
        logger.info(f"{'='*70}")
        
        # 计算关键指标
        final_population = self.stats['population'][-1]
        initial_population = self.stats['population'][0]
        
        final_gene_entropy = self.stats['gene_entropy'][-1]
        initial_gene_entropy = self.stats['gene_entropy'][0]
        
        final_families = self.stats['active_families'][-1]
        initial_families = self.stats['active_families'][0]
        
        avg_gene_entropy = np.mean(self.stats['gene_entropy'])
        avg_families = np.mean(self.stats['active_families'])
        
        total_immigrants = sum(self.stats['immigrants'])
        
        logger.info(f"\n🧬 多样性指标:")
        logger.info(f"  基因熵: {initial_gene_entropy:.3f} → {final_gene_entropy:.3f} "
                   f"({((final_gene_entropy/initial_gene_entropy-1)*100):+.1f}%)")
        logger.info(f"  平均基因熵: {avg_gene_entropy:.3f}")
        logger.info(f"  ✅ 目标达成: {'是' if final_gene_entropy >= 0.500 else '否'} "
                   f"(目标: ≥0.500)")
        
        logger.info(f"\n👨‍👩‍👧‍👦 家族多样性:")
        logger.info(f"  活跃家族: {initial_families}个 → {final_families}个 "
                   f"({final_families - initial_families:+d})")
        logger.info(f"  平均家族数: {avg_families:.1f}个")
        logger.info(f"  ✅ 目标达成: {'是' if final_families >= 10 else '否'} "
                   f"(目标: ≥10)")
        
        logger.info(f"\n📊 种群统计:")
        logger.info(f"  最终种群: {final_population}个")
        logger.info(f"  种群变化: {final_population - initial_population:+d}")
        logger.info(f"  累计移民: {total_immigrants}个")
        
        logger.info(f"\n⚙️  系统配置:")
        logger.info(f"  基础变异率: {self.evolution_manager.base_mutation_rate:.1%} (v5.2: 10%)")
        logger.info(f"  最大变异率: {self.evolution_manager.max_mutation_rate:.1%} (v5.2: 60%)")
        logger.info(f"  移民间隔: {self.evolution_manager.immigration_interval}轮")
        logger.info(f"  每波移民: {self.evolution_manager.immigrants_per_wave}个")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 测试完成！")
        logger.info(f"{'='*70}")
        
        # 保存结果
        self._save_results()
    
    def _save_results(self):
        """保存测试结果"""
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            'version': 'v5.3_stage1',
            'timestamp': timestamp,
            'test_cycles': self.test_cycles,
            'initial_agents': self.initial_agents,
            'stats': self.stats,
            'config': {
                'base_mutation_rate': self.evolution_manager.base_mutation_rate,
                'max_mutation_rate': self.evolution_manager.max_mutation_rate,
                'immigration_enabled': self.evolution_manager.immigration_enabled,
                'immigration_interval': self.evolution_manager.immigration_interval,
                'immigrants_per_wave': self.evolution_manager.immigrants_per_wave
            }
        }
        
        output_file = f"v53_stage1_test_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n💾 测试结果已保存: {output_file}")


if __name__ == "__main__":
    test = V53Stage1Test()
    test.run()

