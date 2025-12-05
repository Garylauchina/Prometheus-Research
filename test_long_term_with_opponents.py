"""
长期进化测试（带简单对手）

测试内容：
1. 50轮完整进化循环
2. 包含机构和散户对手
3. 完整的多样性监控
4. 生成详细报告和可视化

目标：
- 验证Day 3的多样性监控系统
- 测试在有对手环境下的表现
- 为未来的对抗性系统打基础
"""

import sys
import os
import logging
from datetime import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.diversity_monitor import DiversityMonitor
from prometheus.core.diversity_visualizer import DiversityVisualizer
from prometheus.market.simple_opponents import SimpleOpponentMarket

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LongTermTestWithOpponents:
    """
    长期测试（带对手）
    
    运行流程：
    1. 初始化种群和对手
    2. 50轮进化循环
    3. 每轮收集数据
    4. 生成完整报告
    """
    
    def __init__(self,
                 num_cycles: int = 50,
                 initial_agents: int = 50,
                 num_institutions: int = 10,
                 num_retailers: int = 100):
        """
        初始化测试
        
        Args:
            num_cycles: 进化轮数
            initial_agents: 初始Agent数量
            num_institutions: 机构数量
            num_retailers: 散户数量
        """
        self.num_cycles = num_cycles
        self.initial_agents = initial_agents
        
        # 创建Moirai（生命管理器）
        self.moirai = Moirai(num_families=50)
        
        # 创建进化管理器
        self.evolution_manager = EvolutionManagerV5(
            moirai=self.moirai,
            elite_ratio=0.2,
            elimination_ratio=0.3,
            num_families=50
        )
        
        # 创建市场（带对手）
        self.market = SimpleOpponentMarket(
            num_institutions=num_institutions,
            num_retailers=num_retailers,
            base_liquidity=1_000_000,
            enable_natural_volatility=True,  # 🆕 启用自然波动
            volatility_std=0.008  # 0.8%波动率（中等）
        )
        
        # 创建可视化器
        self.visualizer = DiversityVisualizer()
        
        # 数据收集
        self.history = {
            'cycle': [],
            'population': [],
            'avg_capital': [],
            'diversity_score': [],
            'gene_entropy': [],
            'strategy_entropy': [],
            'lineage_entropy': [],
            'active_families': [],
            'market_price': [],
            'market_trades': [],
            'inst_trades': [],
            'retail_trades': []
        }
        
        logger.info("="*70)
        logger.info("🚀 长期进化测试（带简单对手） - 初始化完成")
        logger.info("="*70)
        logger.info(f"📋 测试配置:")
        logger.info(f"   进化轮数: {num_cycles}")
        logger.info(f"   初始Agent: {initial_agents}")
        logger.info(f"   机构数量: {num_institutions}")
        logger.info(f"   散户数量: {num_retailers}")
        logger.info("="*70)
    
    def initialize_population(self):
        """初始化种群"""
        logger.info("\n🌱 初始化种群...")
        
        # 创建初始Agent
        # _genesis_create_agents需要: agent_count, gene_pool, capital_per_agent
        gene_pool = []  # 空基因池，Moirai会随机生成
        capital_per_agent = 10000.0  # 每个Agent初始资金
        
        agents = self.moirai._genesis_create_agents(
            agent_count=self.initial_agents,
            gene_pool=gene_pool,
            capital_per_agent=capital_per_agent
        )
        
        # 🔧 修复：手动将Agent添加到moirai.agents中
        # 因为_genesis_create_agents只是返回列表，不会自动添加
        self.moirai.agents.extend(agents)
        
        logger.info(f"✅ 创建完成: {len(agents)} 个Agent")
        
        # 🔧 修复：给每个Agent设置初始Fitness数据
        # 这样它们就能参与进化评估了
        logger.info("\n🔧 初始化Agent的Fitness数据...")
        
        for agent in self.moirai.agents:
            # 设置基础交易历史（模拟一些历史交易）
            import random
            from datetime import datetime, timedelta
            
            # 模拟一些历史交易记录
            num_past_trades = random.randint(5, 20)
            for i in range(num_past_trades):
                # 模拟交易结果（有盈有亏）
                pnl = random.gauss(0, 50)  # 平均0，标准差50
                agent.current_capital += pnl
                agent.total_pnl += pnl
                
                # 记录到历史
                agent.pnl_history.append(pnl)
                agent.capital_history.append(agent.current_capital)
            
            # 确保capital_ratio合理
            agent.current_capital = max(agent.current_capital, capital_per_agent * 0.5)  # 至少保留50%
            agent.current_capital = min(agent.current_capital, capital_per_agent * 1.5)  # 最多150%
            
            # 🔧 设置初始fitness（多样性保护器需要）
            # fitness是一个简单的数值，基于capital ratio
            capital_ratio = agent.current_capital / agent.initial_capital
            agent.fitness = capital_ratio  # 简单的fitness：资金比率
        
        logger.info(f"   ✅ 已为{len(self.moirai.agents)}个Agent设置初始交易历史")
        
        # 计算平均资金
        avg_capital = sum(a.current_capital for a in self.moirai.agents) / len(self.moirai.agents) if self.moirai.agents else 0
        logger.info(f"   种群: {len(self.moirai.agents)} | 平均资金: ${avg_capital:.2f}")
    
    def run_cycle(self, cycle_num: int, current_price: float = 50000.0):
        """
        运行一轮进化循环
        
        Args:
            cycle_num: 当前轮数
            current_price: 当前价格
        """
        logger.info("\n" + "="*70)
        logger.info(f"🔄 第 {cycle_num}/{self.num_cycles} 轮进化")
        logger.info("="*70)
        
        # 1. 模拟市场步骤（对手交易）
        current_time = datetime.now()
        new_price, opponent_trades = self.market.simulate_step(
            current_price=current_price,
            current_time=current_time
        )
        
        # 记录市场数据
        market_stats = self.market.get_market_stats()
        inst_trades = market_stats['institutions']['total_trades']
        retail_trades = market_stats['retailers']['total_trades']
        
        price_change_pct = (new_price/current_price-1)*100 if current_price > 0 else 0
        
        logger.info(f"📊 市场状态:")
        logger.info(f"   价格: ${current_price:.2f} → ${new_price:.2f} ({price_change_pct:+.3f}%)")
        
        if len(opponent_trades) > 0:
            logger.info(f"   💰 对手活跃: {len(opponent_trades)}笔交易 (机构: {inst_trades}, 散户: {retail_trades})")
        else:
            logger.debug(f"   😴 对手休眠: 0笔交易")
        
        logger.info(f"   流动性: ${market_stats['market']['current_liquidity']:,.0f}")
        
        # 2. 🔧 模拟Agent交易（让它们积累数据）
        if len(self.moirai.agents) > 0:
            import random
            
            num_agents_trading = min(5, len(self.moirai.agents))  # 每轮5个Agent交易
            trading_agents = random.sample(list(self.moirai.agents), num_agents_trading)
            
            for agent in trading_agents:
                # 模拟一次交易的盈亏
                volatility = abs(new_price - current_price) / current_price if current_price > 0 else 0
                pnl = random.gauss(0, 20) * (1 + volatility * 10)  # 波动越大，盈亏越大
                
                agent.current_capital += pnl
                agent.current_capital = max(agent.current_capital, 1000)  # 确保不破产
                agent.total_pnl += pnl
                
                # 记录到历史
                agent.pnl_history.append(pnl)
                agent.capital_history.append(agent.current_capital)
                agent.trade_count += 1
            
            logger.debug(f"   📊 模拟交易: {num_agents_trading}个Agent完成交易")
        
        # 3. 运行进化循环（使用新价格）
        self.evolution_manager.run_evolution_cycle(current_price=new_price)
        
        # 4. 收集数据
        diversity_metrics = self.evolution_manager.diversity_monitor.get_latest_metrics()
        
        self.history['cycle'].append(cycle_num)
        self.history['population'].append(len(self.moirai.agents))
        
        # 计算平均资金
        avg_capital = sum(a.current_capital for a in self.moirai.agents) / len(self.moirai.agents) if self.moirai.agents else 0
        self.history['avg_capital'].append(avg_capital)
        self.history['diversity_score'].append(diversity_metrics.diversity_score if diversity_metrics else 0)
        self.history['gene_entropy'].append(diversity_metrics.gene_entropy if diversity_metrics else 0)
        self.history['strategy_entropy'].append(diversity_metrics.strategy_entropy if diversity_metrics else 0)
        self.history['lineage_entropy'].append(diversity_metrics.lineage_entropy if diversity_metrics else 0)
        self.history['active_families'].append(diversity_metrics.active_families if diversity_metrics else 0)
        self.history['market_price'].append(new_price)
        self.history['market_trades'].append(len(opponent_trades))
        self.history['inst_trades'].append(inst_trades)
        self.history['retail_trades'].append(retail_trades)
        
        # 5. 周期性报告
        if cycle_num % 10 == 0:
            logger.info("\n" + "="*70)
            logger.info(f"📈 阶段性总结 (第 {cycle_num} 轮)")
            logger.info("="*70)
            logger.info(f"种群规模: {len(self.moirai.agents)}")
            
            # 计算平均资金
            avg_capital = sum(a.current_capital for a in self.moirai.agents) / len(self.moirai.agents) if self.moirai.agents else 0
            logger.info(f"平均资金: ${avg_capital:.2f}")
            logger.info(f"多样性得分: {diversity_metrics.diversity_score:.3f}" if diversity_metrics else "N/A")
            # health_status属性已经在diversity_metrics中显示了，不需要单独打印
            # logger.info(f"健康状态: {diversity_metrics.health_status}" if diversity_metrics else "N/A")
            logger.info(f"市场价格: ${new_price:.2f}")
            logger.info(f"累计对手交易: {market_stats['market']['total_trades']}")
            logger.info("="*70)
        
        return new_price
    
    def run(self):
        """运行完整测试"""
        start_time = datetime.now()
        
        # 1. 初始化种群
        self.initialize_population()
        
        # 2. 运行进化循环
        current_price = 50000.0  # 初始价格
        
        for cycle in range(1, self.num_cycles + 1):
            try:
                current_price = self.run_cycle(cycle, current_price)
            except Exception as e:
                logger.error(f"❌ 第 {cycle} 轮出错: {e}")
                import traceback
                traceback.print_exc()
                break
        
        # 3. 生成报告
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "="*70)
        logger.info("✅ 测试完成！")
        logger.info("="*70)
        logger.info(f"⏱️  总耗时: {duration:.2f}秒")
        logger.info(f"📊 完成轮数: {len(self.history['cycle'])}/{self.num_cycles}")
        logger.info("="*70)
        
        self.generate_report()
    
    def generate_report(self):
        """生成完整报告"""
        logger.info("\n📊 生成测试报告...")
        
        # 1. 保存数据到JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = "results/long_term_test"
        os.makedirs(report_dir, exist_ok=True)
        
        # 保存历史数据
        data_file = f"{report_dir}/test_data_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ 数据已保存: {data_file}")
        
        # 2. 生成可视化
        self._generate_visualizations(report_dir, timestamp)
        
        # 3. 生成文本报告
        self._generate_text_report(report_dir, timestamp)
        
        logger.info(f"✅ 完整报告已生成在: {report_dir}/")
    
    def _generate_visualizations(self, report_dir: str, timestamp: str):
        """生成可视化图表"""
        logger.info("📈 生成可视化图表...")
        
        # 创建大图（4行2列）
        fig, axes = plt.subplots(4, 2, figsize=(16, 20))
        fig.suptitle(f'长期进化测试报告（带对手）\n测试时间: {timestamp}', 
                     fontsize=16, fontweight='bold')
        
        cycles = self.history['cycle']
        
        # 1. 种群规模
        ax = axes[0, 0]
        ax.plot(cycles, self.history['population'], 'b-', linewidth=2)
        ax.set_title('种群规模变化', fontsize=12, fontweight='bold')
        ax.set_xlabel('进化轮数')
        ax.set_ylabel('Agent数量')
        ax.grid(True, alpha=0.3)
        
        # 2. 平均资金
        ax = axes[0, 1]
        ax.plot(cycles, self.history['avg_capital'], 'g-', linewidth=2)
        ax.set_title('平均资金变化', fontsize=12, fontweight='bold')
        ax.set_xlabel('进化轮数')
        ax.set_ylabel('平均资金 (USDT)')
        ax.grid(True, alpha=0.3)
        
        # 3. 多样性得分
        ax = axes[1, 0]
        ax.plot(cycles, self.history['diversity_score'], 'r-', linewidth=2, label='多样性得分')
        ax.axhline(y=0.5, color='orange', linestyle='--', label='健康阈值')
        ax.set_title('多样性得分', fontsize=12, fontweight='bold')
        ax.set_xlabel('进化轮数')
        ax.set_ylabel('得分')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 4. 三种熵值
        ax = axes[1, 1]
        ax.plot(cycles, self.history['gene_entropy'], 'b-', label='基因熵', linewidth=2)
        ax.plot(cycles, self.history['strategy_entropy'], 'g-', label='策略熵', linewidth=2)
        ax.plot(cycles, self.history['lineage_entropy'], 'r-', label='血统熵', linewidth=2)
        ax.set_title('三种熵值变化', fontsize=12, fontweight='bold')
        ax.set_xlabel('进化轮数')
        ax.set_ylabel('熵值')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 5. 活跃家族数
        ax = axes[2, 0]
        ax.plot(cycles, self.history['active_families'], 'purple', linewidth=2)
        ax.set_title('活跃家族数量', fontsize=12, fontweight='bold')
        ax.set_xlabel('进化轮数')
        ax.set_ylabel('家族数')
        ax.grid(True, alpha=0.3)
        
        # 6. 市场价格变化
        ax = axes[2, 1]
        ax.plot(cycles, self.history['market_price'], 'orange', linewidth=2)
        ax.set_title('市场价格变化（受对手影响）', fontsize=12, fontweight='bold')
        ax.set_xlabel('进化轮数')
        ax.set_ylabel('价格 (USDT)')
        ax.grid(True, alpha=0.3)
        
        # 7. 对手交易活动
        ax = axes[3, 0]
        ax.plot(cycles, self.history['inst_trades'], 'b-', label='机构交易', linewidth=2)
        ax.plot(cycles, self.history['retail_trades'], 'g-', label='散户交易', linewidth=2)
        ax.set_title('对手交易活动', fontsize=12, fontweight='bold')
        ax.set_xlabel('进化轮数')
        ax.set_ylabel('累计交易数')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 8. 每轮交易数
        ax = axes[3, 1]
        ax.bar(cycles, self.history['market_trades'], color='coral', alpha=0.7)
        ax.set_title('每轮对手交易数', fontsize=12, fontweight='bold')
        ax.set_xlabel('进化轮数')
        ax.set_ylabel('交易数')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # 保存图表
        chart_file = f"{report_dir}/comprehensive_report_{timestamp}.png"
        plt.savefig(chart_file, dpi=150, bbox_inches='tight')
        logger.info(f"✅ 图表已保存: {chart_file}")
        plt.close()
        
        # 使用DiversityVisualizer生成多样性仪表板
        if self.evolution_manager.diversity_monitor.metrics_history:
            dashboard_file = f"{report_dir}/diversity_dashboard_{timestamp}.png"
            self.visualizer.generate_dashboard(
                self.evolution_manager.diversity_monitor.metrics_history,
                self.evolution_manager.diversity_monitor.alerts_history,
                save_path=dashboard_file
            )
            logger.info(f"✅ 多样性仪表板已保存: {dashboard_file}")
    
    def _generate_text_report(self, report_dir: str, timestamp: str):
        """生成文本报告"""
        logger.info("📝 生成文本报告...")
        
        report_file = f"{report_dir}/test_report_{timestamp}.txt"
        
        # 计算统计数据
        final_population = self.history['population'][-1] if self.history['population'] else 0
        final_capital = self.history['avg_capital'][-1] if self.history['avg_capital'] else 0
        final_diversity = self.history['diversity_score'][-1] if self.history['diversity_score'] else 0
        
        avg_diversity = np.mean(self.history['diversity_score']) if self.history['diversity_score'] else 0
        min_diversity = np.min(self.history['diversity_score']) if self.history['diversity_score'] else 0
        max_diversity = np.max(self.history['diversity_score']) if self.history['diversity_score'] else 0
        
        final_price = self.history['market_price'][-1] if self.history['market_price'] else 50000
        initial_price = self.history['market_price'][0] if self.history['market_price'] else 50000
        price_change = (final_price / initial_price - 1) * 100 if initial_price > 0 else 0
        
        total_inst_trades = self.history['inst_trades'][-1] if self.history['inst_trades'] else 0
        total_retail_trades = self.history['retail_trades'][-1] if self.history['retail_trades'] else 0
        
        # 获取市场统计
        market_stats = self.market.get_market_stats()
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("长期进化测试报告（带简单对手）\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"测试时间: {timestamp}\n")
            f.write(f"完成轮数: {len(self.history['cycle'])}/{self.num_cycles}\n\n")
            
            f.write("="*70 + "\n")
            f.write("📊 最终状态\n")
            f.write("="*70 + "\n")
            f.write(f"种群规模: {final_population}\n")
            f.write(f"平均资金: ${final_capital:.2f}\n")
            f.write(f"多样性得分: {final_diversity:.3f}\n")
            f.write(f"市场价格: ${final_price:.2f} (变化: {price_change:+.2f}%)\n\n")
            
            f.write("="*70 + "\n")
            f.write("📈 多样性统计\n")
            f.write("="*70 + "\n")
            f.write(f"平均多样性: {avg_diversity:.3f}\n")
            f.write(f"最低多样性: {min_diversity:.3f}\n")
            f.write(f"最高多样性: {max_diversity:.3f}\n\n")
            
            f.write("="*70 + "\n")
            f.write("🏦 对手统计\n")
            f.write("="*70 + "\n")
            f.write(f"机构玩家: {market_stats['institutions']['count']}个\n")
            f.write(f"  总资金: ${market_stats['institutions']['total_capital']:,.0f}\n")
            f.write(f"  总交易: {total_inst_trades}笔\n")
            f.write(f"  平均交易/机构: {market_stats['institutions']['avg_trades_per_inst']:.1f}笔\n\n")
            
            f.write(f"散户玩家: {market_stats['retailers']['count']}个\n")
            f.write(f"  总资金: ${market_stats['retailers']['total_capital']:,.0f}\n")
            f.write(f"  总交易: {total_retail_trades}笔\n")
            f.write(f"  平均交易/散户: {market_stats['retailers']['avg_trades_per_retail']:.1f}笔\n\n")
            
            f.write(f"市场总交易: {market_stats['market']['total_trades']}笔\n")
            f.write(f"当前流动性: ${market_stats['market']['current_liquidity']:,.0f}\n\n")
            
            f.write("="*70 + "\n")
            f.write("🎯 关键发现\n")
            f.write("="*70 + "\n")
            
            # 分析多样性健康
            if avg_diversity > 0.5:
                f.write("✅ 多样性保持健康（平均>0.5）\n")
            else:
                f.write("⚠️  多样性偏低（平均<0.5），需要关注\n")
            
            # 分析种群稳定性
            if final_population >= self.initial_agents * 0.8:
                f.write("✅ 种群规模稳定\n")
            else:
                f.write("⚠️  种群规模下降较大\n")
            
            # 分析对手影响
            if abs(price_change) > 10:
                f.write(f"⚠️  对手对价格影响显著（{price_change:+.2f}%）\n")
            else:
                f.write(f"✅ 对手对价格影响温和（{price_change:+.2f}%）\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("测试完成！\n")
            f.write("="*70 + "\n")
        
        logger.info(f"✅ 文本报告已保存: {report_file}")


def main():
    """主函数"""
    print("="*70)
    print("🚀 Prometheus v5.2 长期进化测试（带简单对手）")
    print("="*70)
    print()
    print("测试配置：")
    print("  - 50轮进化循环")
    print("  - 50个初始Agent")
    print("  - 10个机构玩家")
    print("  - 100个散户玩家")
    print("  - 完整多样性监控")
    print("  - 🆕 启用价格波动（±0.8%）")
    print()
    print("预计时间：3-5分钟")
    print()
    print("🌟 本次测试新增：自然价格波动，激活对手交易！")
    print("="*70)
    print()
    
    # 创建并运行测试
    test = LongTermTestWithOpponents(
        num_cycles=50,
        initial_agents=50,
        num_institutions=10,
        num_retailers=100
    )
    
    test.run()
    
    print()
    print("="*70)
    print("✅ 测试完成！报告已生成在 results/long_term_test/ 目录")
    print("="*70)


if __name__ == "__main__":
    main()

