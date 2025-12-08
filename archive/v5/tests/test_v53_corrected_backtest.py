#!/usr/bin/env python3
"""
Prometheus v5.3 - 修正版回测（消除幸存者偏差）
==================================================

修正内容：
1. ✅ 修正幸存者偏差：计算所有Agent的平均（包括死亡的）
2. ✅ 添加动态滑点：资金越大，滑点越高
3. ✅ 添加市场冲击成本
4. ✅ 更真实的成本模型
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class CorrectedHistoricalBacktest:
    """修正版历史回测引擎"""
    
    def __init__(self,
                 evolution_manager,
                 kline_data: pd.DataFrame,
                 evolution_interval: int = 30,
                 initial_agents: int = 50,
                 initial_capital: float = 10000.0):
        self.evolution_manager = evolution_manager
        self.kline_data = kline_data
        self.evolution_interval = evolution_interval
        self.initial_agents = initial_agents
        self.initial_capital = initial_capital
        
        self.current_step = 0
        self.evolution_cycles = 0
        
        # 📊 修正1: 跟踪所有Agent（消除幸存者偏差）
        self.all_agents_ever_existed = []  # 所有曾经存在的Agent
        self.all_agents_final_capital = {}  # {agent_id: final_capital}
        
        # 📊 修正2: 详细统计
        self.total_agents_created = 0
        self.total_agents_died = 0
        self.liquidation_records = []
        
        logger.info("✅ 修正版回测引擎初始化")
        logger.info(f"   修正1: 消除幸存者偏差")
        logger.info(f"   修正2: 动态滑点模型")
        logger.info(f"   修正3: 市场冲击成本")
    
    def calculate_dynamic_slippage(self, capital: float, leverage: float) -> float:
        """
        动态滑点模型：资金越大，滑点越高
        
        Args:
            capital: 当前资金
            leverage: 杠杆倍数
            
        Returns:
            滑点百分比
        """
        trade_size = capital * leverage
        
        # 基础滑点
        base_slippage = 0.0001  # 0.01%
        
        # 根据交易规模动态调整
        if trade_size < 10000:  # <$10K
            return base_slippage
        elif trade_size < 100000:  # $10K-$100K
            return base_slippage * 1.5
        elif trade_size < 1000000:  # $100K-$1M
            return base_slippage * 3
        elif trade_size < 10000000:  # $1M-$10M
            return base_slippage * 10
        elif trade_size < 100000000:  # $10M-$100M
            return base_slippage * 30
        else:  # >$100M
            return base_slippage * 100  # 1% 滑点！
    
    def calculate_market_impact(self, capital: float, leverage: float) -> float:
        """
        市场冲击成本：大单会影响市场价格
        
        Args:
            capital: 当前资金
            leverage: 杠杆倍数
            
        Returns:
            市场冲击成本百分比
        """
        trade_size = capital * leverage
        
        # 假设BTC日均交易量$50B
        daily_volume = 50_000_000_000
        
        # 市场冲击 = (交易规模 / 日交易量) ^ 0.5
        impact_ratio = (trade_size / daily_volume) ** 0.5
        
        # 转换为百分比成本
        market_impact = impact_ratio * 0.001  # 基础冲击系数
        
        return min(market_impact, 0.05)  # 最高5%
    
    def calculate_total_cost(self, capital: float, leverage: float, position: float) -> float:
        """
        计算总交易成本（含动态滑点和市场冲击）
        
        Args:
            capital: 当前资金
            leverage: 杠杆倍数
            position: 仓位
            
        Returns:
            总成本百分比
        """
        if abs(position) < 0.01:
            return 0.0  # 无仓位，无成本
        
        # 1. 固定成本
        trading_fee = 0.001  # 0.10% OKX Taker
        funding_rate = 0.0003  # 0.03%/天
        
        # 2. 动态滑点
        dynamic_slippage = self.calculate_dynamic_slippage(capital, leverage)
        
        # 3. 市场冲击
        market_impact = self.calculate_market_impact(capital, leverage)
        
        # 总成本
        total_cost = trading_fee + funding_rate + dynamic_slippage + market_impact
        
        return total_cost
    
    def _agent_make_position_decision(self, agent, price_change: float) -> float:
        """
        Agent决策：基于本能和基因（使用原始回测的逻辑）
        
        Args:
            agent: Agent实例
            price_change: 价格变化
            
        Returns:
            仓位 (-1到1，负数为做空)
        """
        # 使用与原始回测相同的逻辑
        risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
        time_preference = getattr(agent.instinct, 'time_preference', 0.5)
        
        # 基于价格变化判断
        if abs(price_change) < 0.001:  # 价格基本不变
            return 0.0  # 空仓
        
        # 简化策略：顺势交易 + 风险调整
        if price_change > 0:  # 上涨
            # 做多，力度由风险承受度决定
            position = risk_tolerance * 0.8
        else:  # 下跌
            # 做空，力度由风险承受度决定
            position = -risk_tolerance * 0.8
        
        # 限制在-1到1之间
        return np.clip(position, -1, 1)
    
    def _agent_choose_leverage(self, agent) -> float:
        """
        Agent选择杠杆倍数（使用原始回测的逻辑）
        
        Args:
            agent: Agent实例
            
        Returns:
            杠杆倍数 (1-100)
        """
        risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
        
        # 使用与原始回测相同的杠杆选择逻辑
        if risk_tolerance < 0.2:
            return 1.0 + risk_tolerance * 10  # 1-3x
        elif risk_tolerance < 0.4:
            return 3.0 + (risk_tolerance - 0.2) * 10  # 3-5x
        elif risk_tolerance < 0.6:
            return 5.0 + (risk_tolerance - 0.4) * 25  # 5-10x
        elif risk_tolerance < 0.8:
            return 10.0 + (risk_tolerance - 0.6) * 50  # 10-20x
        elif risk_tolerance < 0.9:
            return 20.0 + (risk_tolerance - 0.8) * 300  # 20-50x
        else:
            return 50.0 + (risk_tolerance - 0.9) * 500  # 50-100x
    
    def initialize_agents(self):
        """初始化Agent种群"""
        logger.info(f"🌱 初始化{self.initial_agents}个Agent...")
        
        agents = self.evolution_manager.moirai._genesis_create_agents(
            agent_count=self.initial_agents,
            gene_pool=[],
            capital_per_agent=self.initial_capital
        )
        
        for agent in agents:
            agent.fitness = 1.0
            # 记录所有Agent
            self.all_agents_ever_existed.append(agent.agent_id)
            self.all_agents_final_capital[agent.agent_id] = self.initial_capital
        
        self.total_agents_created = len(agents)
        
        self.evolution_manager.moirai.agents = agents
        
        logger.info(f"✅ 初始化完成: {len(agents)}个Agent")
        return agents
    
    def run(self):
        """运行回测"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("🚀 开始修正版回测")
        logger.info("=" * 80)
        logger.info("")
        
        # 初始化Agent
        agents = self.initialize_agents()
        
        # 记录初始价格
        initial_price = self.kline_data.iloc[0]['close']
        
        # 逐步回放历史
        for idx, row in self.kline_data.iterrows():
            self.current_step += 1
            current_price = row['close']
            timestamp = row['timestamp']
            
            # 计算价格变化
            if idx > 0:
                prev_price = self.kline_data.iloc[idx - 1]['close']
                price_change = (current_price - prev_price) / prev_price
            else:
                price_change = 0.0
            
            # 每个Agent做决策并更新资金
            for agent in agents:
                # 使用Agent的真实决策逻辑
                position = self._agent_make_position_decision(agent, price_change)
                leverage = self._agent_choose_leverage(agent)
                
                # 计算基础收益
                base_return = price_change * position
                leveraged_return = base_return * leverage
                
                # 📊 修正: 使用动态成本模型
                total_cost = self.calculate_total_cost(
                    agent.current_capital,
                    leverage,
                    position
                )
                
                # 扣除成本
                leveraged_return -= total_cost * leverage
                
                # 检查爆仓
                if leveraged_return <= -1.0:
                    # 爆仓
                    self.liquidation_records.append({
                        'agent_id': agent.agent_id,
                        'step': self.current_step,
                        'capital': agent.current_capital,
                        'leverage': leverage
                    })
                    agent.current_capital = 0.0
                    self.total_agents_died += 1
                else:
                    # 更新资金
                    agent.current_capital *= (1 + leveraged_return)
                
                # 更新记录
                self.all_agents_final_capital[agent.agent_id] = agent.current_capital
            
            # 定期进化
            if self.current_step % self.evolution_interval == 0:
                self.evolution_cycles += 1
                
                # 淘汰爆仓Agent
                agents = [a for a in agents if a.current_capital > 0]
                self.evolution_manager.moirai.agents = agents
                
                # 运行进化
                try:
                    self.evolution_manager.run_evolution_cycle()
                    agents = self.evolution_manager.moirai.agents
                    
                    # 记录新Agent
                    for agent in agents:
                        if agent.agent_id not in self.all_agents_ever_existed:
                            self.all_agents_ever_existed.append(agent.agent_id)
                            self.all_agents_final_capital[agent.agent_id] = agent.current_capital
                            self.total_agents_created += 1
                except Exception as e:
                    logger.warning(f"进化失败: {e}")
            
            # 定期输出
            if self.current_step % 10 == 0:
                logger.info(f"Step {self.current_step} | Price: ${current_price:,.2f} | Population: {len(agents):3d} | Avg Capital: ${np.mean([a.current_capital for a in agents]):,.2f}")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ 回测完成")
        logger.info("=" * 80)
        logger.info("")
        
        return self.generate_results(agents, initial_price, current_price)
    
    def generate_results(self, agents, initial_price, final_price):
        """生成结果（修正版）"""
        
        # 📊 修正: 计算所有Agent的平均（包括死亡的）
        all_capitals = [self.all_agents_final_capital[aid] for aid in self.all_agents_ever_existed]
        
        # 幸存者
        survivor_capitals = [a.current_capital for a in agents]
        
        results = {
            'backtest_summary': {
                'total_steps': self.current_step,
                'evolution_cycles': self.evolution_cycles,
            },
            'market_performance': {
                'initial_price': float(initial_price),
                'final_price': float(final_price),
                'market_return': float((final_price / initial_price - 1) * 100),
            },
            'population': {
                'initial': self.initial_agents,
                'final_survivors': len(agents),
                'total_ever_created': self.total_agents_created,
                'total_died': self.total_agents_died,
                'survival_rate_initial': float(len(agents) / self.initial_agents * 100),
            },
            'capital_corrected': {
                'note': '修正版：包含所有Agent（包括死亡的）',
                'initial_avg': self.initial_capital,
                'final_avg_all_agents': float(np.mean(all_capitals)),  # 所有Agent平均
                'final_avg_survivors': float(np.mean(survivor_capitals)),  # 仅幸存者平均
                'final_median_all': float(np.median(all_capitals)),
                'final_median_survivors': float(np.median(survivor_capitals)),
                'final_max': float(np.max(all_capitals)),
                'final_min': float(np.min(all_capitals)),
            },
            'returns_corrected': {
                'note': '修正版：基于所有Agent的平均',
                'avg_return_all': float((np.mean(all_capitals) / self.initial_capital - 1) * 100),
                'avg_return_survivors': float((np.mean(survivor_capitals) / self.initial_capital - 1) * 100),
                'profit_multiple_all': float(np.mean(all_capitals) / self.initial_capital),
                'profit_multiple_survivors': float(np.mean(survivor_capitals) / self.initial_capital),
            },
            'liquidation': {
                'count': len(self.liquidation_records),
                'rate': float(len(self.liquidation_records) / self.total_agents_created * 100),
            }
        }
        
        return results
    
    def print_summary(self, results):
        """打印摘要"""
        print()
        print("=" * 80)
        print("📊 修正版回测结果")
        print("=" * 80)
        print()
        
        print(f"📅 回测周期:")
        print(f"   总步数: {results['backtest_summary']['total_steps']}")
        print(f"   进化次数: {results['backtest_summary']['evolution_cycles']}")
        print()
        
        print(f"📈 市场表现:")
        print(f"   初始价格: ${results['market_performance']['initial_price']:,.2f}")
        print(f"   最终价格: ${results['market_performance']['final_price']:,.2f}")
        print(f"   市场收益: {results['market_performance']['market_return']:+.2f}%")
        print()
        
        print(f"👥 种群表现:")
        print(f"   初始数量: {results['population']['initial']}个")
        print(f"   最终幸存: {results['population']['final_survivors']}个")
        print(f"   累计创建: {results['population']['total_ever_created']}个")
        print(f"   累计死亡: {results['population']['total_died']}个")
        print()
        
        print(f"💰 资金表现（修正版）:")
        cap = results['capital_corrected']
        print(f"   初始平均: ${cap['initial_avg']:,.2f}")
        print(f"   🔴 所有Agent平均: ${cap['final_avg_all_agents']:,.2f} ⭐ (包括死亡)")
        print(f"   🟢 仅幸存者平均: ${cap['final_avg_survivors']:,.2f} (原始偏差)")
        print(f"   中位数（所有）: ${cap['final_median_all']:,.2f}")
        print(f"   中位数（幸存）: ${cap['final_median_survivors']:,.2f}")
        print()
        
        print(f"📊 收益率（修正版）:")
        ret = results['returns_corrected']
        print(f"   🔴 所有Agent平均: {ret['avg_return_all']:+,.2f}%")
        print(f"   🔴 盈利倍数（所有）: {ret['profit_multiple_all']:,.2f}倍 ⭐")
        print()
        print(f"   🟢 仅幸存者平均: {ret['avg_return_survivors']:+,.2f}%")
        print(f"   🟢 盈利倍数（幸存）: {ret['profit_multiple_survivors']:,.2f}倍 (原始偏差)")
        print()
        
        # 计算年化
        years = 5.48
        if ret['profit_multiple_all'] > 1:
            annualized_all = (ret['profit_multiple_all'] ** (1/years) - 1) * 100
            print(f"   🔴 年化收益率（所有）: {annualized_all:.2f}% ⭐")
        if ret['profit_multiple_survivors'] > 1:
            annualized_survivors = (ret['profit_multiple_survivors'] ** (1/years) - 1) * 100
            print(f"   🟢 年化收益率（幸存）: {annualized_survivors:.2f}% (原始偏差)")
        print()
        
        print(f"💥 爆仓统计:")
        liq = results['liquidation']
        print(f"   爆仓次数: {liq['count']}次")
        print(f"   爆仓率: {liq['rate']:.2f}%")
        print()
        
        print("=" * 80)
        print("✅ 🔴 标记为修正版结果（消除幸存者偏差）")
        print("✅ 🟢 标记为原始结果（存在幸存者偏差）")
        print("=" * 80)


def main():
    logger.info("")
    logger.info("=" * 80)
    logger.info("🔧 Prometheus v5.3 - 修正版回测（消除偏差）")
    logger.info("=" * 80)
    logger.info("")
    
    # 加载数据
    logger.info("📥 加载OKX历史数据...")
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    logger.info(f"✅ 数据加载完成: {len(df)}条")
    logger.info("")
    
    # 初始化系统
    logger.info("🧬 初始化Prometheus系统...")
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    logger.info("✅ 系统初始化完成")
    logger.info("")
    
    # 创建回测引擎
    logger.info("⚙️  创建修正版回测引擎...")
    backtest = CorrectedHistoricalBacktest(
        evolution_manager=evolution_manager,
        kline_data=df,
        evolution_interval=30,
        initial_agents=50,
        initial_capital=10000.0
    )
    logger.info("✅ 回测引擎创建完成")
    logger.info("")
    
    # 运行回测
    start_time = datetime.now()
    results = backtest.run()
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    logger.info(f"⏱️  用时: {duration:.2f}秒")
    logger.info("")
    
    # 打印摘要
    backtest.print_summary(results)
    
    # 保存结果
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"backtest_results_corrected_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 结果已保存: {results_file}")
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("🎉 修正版回测完成！")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

