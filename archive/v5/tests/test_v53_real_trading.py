"""
v5.3 阶段2.1 - 真实交易逻辑测试

使用真实的交易成本和理性决策，验证Agent表现

对比：
- 简化版（随机盈亏）vs 真实版（考虑成本）
- 验证收益的真实性

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
from prometheus.market.network_simulator import NetworkSimulator
from prometheus.agent.simple_trading import SimpleAgentTrader, agent_make_trading_decision, OrderSide

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class V53RealTradingTest:
    """v5.3 真实交易逻辑测试"""
    
    def __init__(self, test_cycles: int = 30):
        self.test_cycles = test_cycles
        self.initial_agents = 50
        self.initial_capital = 10000
        self.evolution_interval = 5
        
        logger.info("="*70)
        logger.info("🧪 v5.3 真实交易逻辑测试")
        logger.info("="*70)
        logger.info(f"测试周期: {test_cycles}轮")
        logger.info(f"初始Agent: {self.initial_agents}个")
        logger.info(f"="*70)
        
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
        
        # === 初始化交易系统 ===
        logger.info("\n🔧 初始化交易系统...")
        
        self.network = NetworkSimulator(
            enabled=True,
            base_latency_ms=30,
            jitter_ms=10
        )
        
        self.trader = SimpleAgentTrader(
            market=self.market,
            network_simulator=self.network
        )
        
        logger.info("✅ 交易系统初始化完成")
        
        # === 统计数据 ===
        self.stats = {
            'cycle': [],
            'population': [],
            'avg_capital': [],
            'price': [],
            'total_trades': [],
            'successful_trades': [],
            'avg_trade_cost_pct': []
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
        logger.info(f"🚀 开始{self.test_cycles}轮测试（真实交易逻辑）")
        logger.info(f"{'='*70}\n")
        
        # === 运行测试周期 ===
        for cycle in range(self.test_cycles):
            logger.info(f"\n{'='*70}")
            logger.info(f"🔄 第{cycle+1}轮测试")
            logger.info(f"{'='*70}")
            
            # 1. 市场模拟
            market_result = self.market.simulate_step(cycle)
            current_price = market_result.price
            
            logger.info(f"💹 市场价格: ${current_price:,.2f}")
            
            # 2. Agent真实交易
            trade_stats = self._execute_agent_trading(current_price)
            
            logger.info(f"📊 交易统计: {trade_stats['successful']}/{trade_stats['attempted']}笔成功")
            if trade_stats['successful'] > 0:
                logger.info(f"   平均成本: {trade_stats['avg_cost_pct']*100:.3f}%")
            
            # 3. 进化周期
            if (cycle + 1) % self.evolution_interval == 0:
                logger.info(f"\n🧬 触发进化周期")
                self.evolution_manager.run_evolution_cycle(current_price)
            
            # 4. 收集统计
            self._collect_stats(cycle + 1, market_result, trade_stats)
            
            # 5. 阶段性总结
            if (cycle + 1) % 10 == 0:
                self._print_summary(cycle + 1)
        
        # === 最终报告 ===
        self._generate_final_report()
    
    def _execute_agent_trading(self, current_price: float) -> Dict:
        """
        执行Agent真实交易
        
        每个Agent：
        1. 做出交易决策
        2. 评估成本
        3. 如果预期收益 > 成本，则交易
        4. 更新资金和fitness
        """
        attempted = 0
        successful = 0
        total_cost_pct = 0.0
        
        for agent in self.moirai.agents:
            # 1. Agent决策
            should_trade, side, quantity, expected_profit_pct = agent_make_trading_decision(
                agent, current_price
            )
            
            if not should_trade:
                continue
            
            attempted += 1
            
            # 2. 执行交易
            result = self.trader.execute_trade(
                agent_id=agent.agent_id,
                side=side,
                quantity=quantity,
                agent_capital=agent.current_capital,
                expected_profit_pct=expected_profit_pct
            )
            
            # 3. 更新Agent状态
            if result.success:
                successful += 1
                total_cost_pct += result.cost.total_cost_pct
                
                # 更新资金（考虑真实成本）
                if side == OrderSide.BUY:
                    # 买入：扣除成本
                    agent.current_capital += result.pnl
                else:
                    # 卖出：获得收益（扣除成本）
                    agent.current_capital += result.pnl
                
                # 更新fitness
                agent.fitness = agent.current_capital / agent.initial_capital
        
        avg_cost_pct = total_cost_pct / successful if successful > 0 else 0
        
        return {
            'attempted': attempted,
            'successful': successful,
            'avg_cost_pct': avg_cost_pct
        }
    
    def _collect_stats(self, cycle: int, market_result, trade_stats: Dict):
        """收集统计数据"""
        avg_capital = sum(a.current_capital for a in self.moirai.agents) / len(self.moirai.agents) if self.moirai.agents else 0
        
        self.stats['cycle'].append(cycle)
        self.stats['population'].append(len(self.moirai.agents))
        self.stats['avg_capital'].append(avg_capital)
        self.stats['price'].append(market_result.price)
        self.stats['total_trades'].append(trade_stats['attempted'])
        self.stats['successful_trades'].append(trade_stats['successful'])
        self.stats['avg_trade_cost_pct'].append(trade_stats['avg_cost_pct'])
    
    def _print_summary(self, cycle: int):
        """打印阶段性总结"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 第{cycle}轮阶段性总结")
        logger.info(f"{'='*70}")
        
        recent = min(10, len(self.stats['population']))
        
        avg_population = np.mean(self.stats['population'][-recent:])
        avg_capital = np.mean(self.stats['avg_capital'][-recent:])
        avg_price = np.mean(self.stats['price'][-recent:])
        total_trades = sum(self.stats['successful_trades'][-recent:])
        
        logger.info(f"Agent系统:")
        logger.info(f"  种群规模: {avg_population:.1f}")
        logger.info(f"  平均资金: ${avg_capital:,.2f}")
        
        logger.info(f"\n市场系统:")
        logger.info(f"  平均价格: ${avg_price:,.2f}")
        
        logger.info(f"\n交易系统:")
        logger.info(f"  成功交易: {total_trades}笔")
        
        logger.info(f"{'='*70}")
    
    def _generate_final_report(self):
        """生成最终报告"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📋 v5.3 真实交易测试 - 最终报告")
        logger.info(f"{'='*70}")
        
        # Agent指标
        initial_pop = self.stats['population'][0]
        final_pop = self.stats['population'][-1]
        
        initial_capital = self.stats['avg_capital'][0]
        final_capital = self.stats['avg_capital'][-1]
        capital_change = ((final_capital / initial_capital) - 1) * 100
        
        # 市场指标
        initial_price = self.stats['price'][0]
        final_price = self.stats['price'][-1]
        price_change = ((final_price / initial_price) - 1) * 100
        
        # 交易指标
        total_trades = sum(self.stats['successful_trades'])
        avg_cost = np.mean([c for c in self.stats['avg_trade_cost_pct'] if c > 0])
        
        logger.info(f"\n🧬 Agent系统表现:")
        logger.info(f"  种群规模: {initial_pop}个 → {final_pop}个 ({final_pop-initial_pop:+d})")
        logger.info(f"  平均资金: ${initial_capital:,.2f} → ${final_capital:,.2f} ({capital_change:+.2f}%)")
        
        logger.info(f"\n💹 市场系统表现:")
        logger.info(f"  价格: ${initial_price:,.2f} → ${final_price:,.2f} ({price_change:+.2f}%)")
        
        logger.info(f"\n💰 交易系统表现:")
        logger.info(f"  成功交易: {total_trades}笔")
        logger.info(f"  平均成本: {avg_cost*100:.3f}%")
        
        # 网络统计
        net_stats = self.network.get_stats()
        logger.info(f"\n🌐 网络系统表现:")
        logger.info(f"  总延迟次数: {net_stats['total_delays']}")
        logger.info(f"  平均延迟: {net_stats['avg_delay_ms']:.2f}ms")
        
        # 评估
        logger.info(f"\n🎯 目标达成情况:")
        
        objectives = [
            ("种群存活", final_pop >= 40, f"{final_pop}个 (目标≥40)"),
            ("平均资金", capital_change >= -20, f"{capital_change:+.2f}% (目标≥-20%)"),
            ("交易执行", total_trades > 0, f"{total_trades}笔 (目标>0)"),
        ]
        
        passed = 0
        for name, success, value in objectives:
            status = "✅" if success else "❌"
            logger.info(f"  {status} {name}: {value}")
            if success:
                passed += 1
        
        logger.info(f"\n总体评分: {passed}/{len(objectives)} ({passed/len(objectives)*100:.0f}%)")
        
        # 保存结果
        self._save_results()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 测试完成！")
        logger.info(f"{'='*70}\n")
    
    def _save_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            'version': 'v5.3_real_trading',
            'timestamp': timestamp,
            'test_cycles': self.test_cycles,
            'stats': {
                'cycle': self.stats['cycle'],
                'population': self.stats['population'],
                'avg_capital': self.stats['avg_capital'],
                'price': self.stats['price'],
                'successful_trades': self.stats['successful_trades']
            },
            'summary': {
                'final_population': self.stats['population'][-1],
                'final_avg_capital': self.stats['avg_capital'][-1],
                'final_price': self.stats['price'][-1],
                'capital_change_pct': ((self.stats['avg_capital'][-1] / self.stats['avg_capital'][0]) - 1) * 100,
                'total_trades': sum(self.stats['successful_trades'])
            }
        }
        
        output_file = f"v53_real_trading_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n💾 测试结果已保存: {output_file}")


def main():
    """主函数"""
    test = V53RealTradingTest(test_cycles=30)
    test.run_test()


if __name__ == "__main__":
    main()

