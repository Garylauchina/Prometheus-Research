"""
历史数据回测框架

基于真实历史K线数据进行回测：
1. 加载历史数据
2. 逐步回放市场
3. Agent在每个时间点做决策
4. 定期运行进化
5. 记录和分析结果
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class HistoricalBacktest:
    """历史数据回测引擎"""
    
    def __init__(self,
                 evolution_manager,
                 kline_data: pd.DataFrame,
                 evolution_interval: int = 24,
                 initial_agents: int = 50,
                 initial_capital: float = 10000.0):
        """
        初始化回测引擎
        
        Args:
            evolution_manager: 进化管理器实例
            kline_data: K线数据DataFrame
            evolution_interval: 进化间隔（多少根K线运行一次进化）
            initial_agents: 初始Agent数量
            initial_capital: 初始资金
        """
        self.evolution_manager = evolution_manager
        self.kline_data = kline_data
        self.evolution_interval = evolution_interval
        self.initial_agents = initial_agents
        self.initial_capital = initial_capital
        
        # 回测状态
        self.current_step = 0
        self.evolution_cycles = 0
        
        # 结果记录
        self.results_history = []
        self.price_history = []
        self.population_history = []
        
        logger.info("📊 历史回测引擎初始化")
        logger.info(f"   K线数量: {len(kline_data)}")
        logger.info(f"   进化间隔: 每{evolution_interval}根K线")
        logger.info(f"   初始Agent: {initial_agents}个")
        logger.info(f"   初始资金: ${initial_capital:.2f}")
    
    def initialize_agents(self):
        """初始化Agent种群"""
        logger.info(f"🌱 初始化{self.initial_agents}个Agent...")
        
        # 直接调用_genesis_create_agents创建初始种群（gene_pool传入空列表，会自动创建新基因）
        agents = self.evolution_manager.moirai._genesis_create_agents(
            agent_count=self.initial_agents,
            gene_pool=[],  # 空基因池，会自动创建新Agent
            capital_per_agent=self.initial_capital
        )
        
        # 初始化fitness
        for agent in agents:
            agent.fitness = 1.0
        
        # 设置到Moirai
        self.evolution_manager.moirai.agents = agents
        
        logger.info(f"✅ Agent初始化完成: {len(agents)}个")
        
        return agents
    
    def run_single_step(self, kline: Dict) -> Dict:
        """
        运行单个时间步
        
        Args:
            kline: 当前K线数据字典
            
        Returns:
            当前步骤的结果
        """
        timestamp = kline['timestamp']
        current_price = kline['close']
        
        # 记录价格
        self.price_history.append({
            'step': self.current_step,
            'timestamp': timestamp,
            'price': current_price
        })
        
        # Agent交易逻辑（支持多空 + 杠杆）
        # Agent会根据其基因和策略做出多空决策并选择杠杆
        agents_to_remove = []  # 爆仓的Agent
        
        for agent in self.evolution_manager.moirai.agents:
            # 简化的收益计算：基于价格变化
            if len(self.price_history) > 1:
                price_change = (current_price - self.price_history[-2]['price']) / self.price_history[-2]['price']
                
                # Agent选择杠杆倍数
                leverage = self._agent_choose_leverage(agent)
                
                # Agent根据策略决定持仓方向和大小
                # position ∈ [-1, +1]: 
                #   +1 = 100%做多，0 = 空仓，-1 = 100%做空
                position = self._agent_make_position_decision(agent, price_change)
                
                # 计算杠杆收益（支持做空 + 杠杆）
                base_return = price_change * position
                leveraged_return = base_return * leverage  # 杠杆放大收益
                
                # 检查是否爆仓（亏损超过100%）
                if leveraged_return <= -1.0:  # 亏损100%或更多
                    # 爆仓！💀
                    logger.warning(f"💥 Agent {agent.agent_id} 爆仓！| 杠杆:{leverage:.1f}x | 持仓:{position:+.2f} | 价格变化:{price_change:+.2%} | 亏损:{leveraged_return:.2%}")
                    agents_to_remove.append(agent)
                    agent.current_capital = 0  # 归零
                    continue
                
                # 更新资金（未爆仓）
                agent.current_capital *= (1 + leveraged_return)
                
                # 记录交易（包含多空 + 杠杆信息）
                if not hasattr(agent, 'trade_history'):
                    agent.trade_history = []
                
                agent.trade_history.append({
                    'timestamp': timestamp,
                    'price': current_price,
                    'position': position,
                    'leverage': leverage,  # 新增：杠杆倍数
                    'base_return': base_return,  # 基础收益
                    'leveraged_return': leveraged_return,  # 杠杆收益
                    'capital': agent.current_capital,
                    'position_type': 'long' if position > 0 else ('short' if position < 0 else 'neutral')
                })
        
        # 移除爆仓的Agent（模拟真实交易所强平）
        if agents_to_remove:
            for agent in agents_to_remove:
                if agent in self.evolution_manager.moirai.agents:
                    self.evolution_manager.moirai.agents.remove(agent)
            logger.warning(f"💀 本轮爆仓: {len(agents_to_remove)}个Agent被强制平仓")
        
        # 收集当前状态
        agents = self.evolution_manager.moirai.agents
        avg_capital = np.mean([a.current_capital for a in agents]) if agents else 0
        
        result = {
            'step': self.current_step,
            'timestamp': timestamp,
            'price': current_price,
            'population': len(agents),
            'avg_capital': avg_capital
        }
        
        self.current_step += 1
        
        return result
    
    def _agent_choose_leverage(self, agent) -> float:
        """
        Agent选择杠杆倍数
        
        基于风险偏好：
        - 高风险 → 高杠杆（10x-20x）
        - 中风险 → 中杠杆（3x-5x）
        - 低风险 → 低杠杆（1x-2x）
        
        Args:
            agent: Agent对象
            
        Returns:
            杠杆倍数（1-20）
        """
        risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
        
        # 根据风险偏好选择杠杆
        if risk_tolerance > 0.8:
            # 极度冒险：10x-20x杠杆
            leverage = 10 + (risk_tolerance - 0.8) * 50  # 10-20x
        elif risk_tolerance > 0.6:
            # 冒险：5x-10x杠杆
            leverage = 5 + (risk_tolerance - 0.6) * 25  # 5-10x
        elif risk_tolerance > 0.4:
            # 中等：3x-5x杠杆
            leverage = 3 + (risk_tolerance - 0.4) * 10  # 3-5x
        elif risk_tolerance > 0.2:
            # 保守：2x-3x杠杆
            leverage = 2 + (risk_tolerance - 0.2) * 5   # 2-3x
        else:
            # 极度保守：1x-2x杠杆
            leverage = 1 + risk_tolerance * 5           # 1-2x
        
        return min(20.0, max(1.0, leverage))  # 限制在1-20x
    
    def _agent_make_position_decision(self, agent, recent_price_change: float) -> float:
        """
        Agent做出持仓决策（支持多空）
        
        策略：基于Agent的基因特征和最近价格变化做判断
        
        Args:
            agent: Agent对象
            recent_price_change: 最近的价格变化率
            
        Returns:
            position ∈ [-1, +1]: 
                +1 = 100%做多
                 0 = 空仓
                -1 = 100%做空
        """
        # 获取Agent的风险偏好（从instinct属性）
        risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)  # 0-1
        
        # 获取Agent的时间偏好
        time_preference = getattr(agent.instinct, 'time_preference', 0.5)  # 0-1, 0=短期, 1=长期
        
        # 策略1: 基于价格动量的简单策略
        # 如果Agent是"冒险家"（高风险偏好），会逆向操作（低买高卖）
        # 如果Agent是"保守者"（低风险偏好），会顺势操作（追涨杀跌）
        
        # 计算趋势信号（基于最近几步的价格）
        if len(self.price_history) >= 5:
            # 短期趋势（最近5步）
            recent_prices = [p['price'] for p in self.price_history[-5:]]
            short_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        else:
            short_trend = recent_price_change
        
        # 决策逻辑
        if risk_tolerance > 0.6:
            # 高风险偏好：逆向交易（均值回归）
            if short_trend < -0.02:  # 价格下跌超过2%
                # 看跌趋势，做空！
                position = -0.5 * risk_tolerance  # 做空
            elif short_trend > 0.02:  # 价格上涨超过2%
                # 看涨趋势，但逆向思维：可能回调
                position = -0.3 * risk_tolerance  # 轻度做空
            else:
                position = 0.2 * risk_tolerance  # 小幅做多
        else:
            # 低风险偏好：顺势交易（趋势跟随）
            if short_trend > 0.01:  # 上涨趋势
                position = 0.5 * (1 - risk_tolerance)  # 做多
            elif short_trend < -0.01:  # 下跌趋势
                # 识别熊市，做空！
                position = -0.4 * (1 - risk_tolerance)  # 做空
            else:
                position = 0.1  # 小幅做多（默认）
        
        # 根据时间偏好调整仓位大小
        position *= (0.5 + 0.5 * time_preference)  # 长期主义者仓位更大
        
        # 限制在[-1, 1]范围内
        position = max(-1.0, min(1.0, position))
        
        return position
    
    def should_run_evolution(self) -> bool:
        """判断是否应该运行进化"""
        return self.current_step > 0 and self.current_step % self.evolution_interval == 0
    
    def run_evolution_cycle(self):
        """运行一次进化循环"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🧬 进化循环 #{self.evolution_cycles + 1}")
        logger.info(f"{'='*60}")
        
        # 运行进化（不传cycle_num参数）
        self.evolution_manager.run_evolution_cycle()
        
        self.evolution_cycles += 1
        
        # 记录种群状态
        agents = self.evolution_manager.moirai.agents
        self.population_history.append({
            'cycle': self.evolution_cycles,
            'step': self.current_step,
            'population': len(agents),
            'avg_capital': np.mean([a.current_capital for a in agents]) if agents else 0,
            'max_capital': max([a.current_capital for a in agents]) if agents else 0,
            'min_capital': min([a.current_capital for a in agents]) if agents else 0
        })
    
    def run(self) -> Dict:
        """
        运行完整回测
        
        Returns:
            回测结果字典
        """
        start_time = datetime.now()
        
        logger.info("\n" + "="*60)
        logger.info("🚀 开始历史回测")
        logger.info("="*60)
        
        # 初始化Agent
        self.initialize_agents()
        
        # 逐步回放历史数据
        logger.info(f"\n📈 开始回放{len(self.kline_data)}根K线数据...")
        
        for idx, row in self.kline_data.iterrows():
            kline = row.to_dict()
            
            # 运行单步
            result = self.run_single_step(kline)
            self.results_history.append(result)
            
            # 定期日志
            if self.current_step % 10 == 0:
                logger.info(
                    f"Step {self.current_step:4d} | "
                    f"Price: ${result['price']:,.2f} | "
                    f"Population: {result['population']:3d} | "
                    f"Avg Capital: ${result['avg_capital']:,.2f}"
                )
            
            # 判断是否进化
            if self.should_run_evolution():
                self.run_evolution_cycle()
        
        # 回测完成
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "="*60)
        logger.info("✅ 回测完成")
        logger.info("="*60)
        logger.info(f"⏱️  耗时: {duration:.2f}秒")
        logger.info(f"📊 K线数: {len(self.kline_data)}")
        logger.info(f"🧬 进化次数: {self.evolution_cycles}")
        logger.info(f"👥 最终种群: {len(self.evolution_manager.moirai.agents)}")
        
        # 生成结果
        results = self.generate_results()
        
        return results
    
    def generate_results(self) -> Dict:
        """生成回测结果"""
        agents = self.evolution_manager.moirai.agents
        
        if not agents:
            logger.warning("⚠️  没有存活的Agent！")
            return {}
        
        # 基础统计
        final_capitals = [a.current_capital for a in agents]
        initial_price = self.price_history[0]['price']
        final_price = self.price_history[-1]['price']
        
        # 统计多空交易 + 杠杆使用
        long_count = 0
        short_count = 0
        neutral_count = 0
        leverage_sum = 0
        leverage_count = 0
        max_leverage = 0
        
        for agent in agents:
            if hasattr(agent, 'trade_history'):
                for trade in agent.trade_history:
                    pos = trade.get('position', 0)
                    lev = trade.get('leverage', 1.0)
                    
                    if pos > 0.01:
                        long_count += 1
                    elif pos < -0.01:
                        short_count += 1
                    else:
                        neutral_count += 1
                    
                    leverage_sum += lev
                    leverage_count += 1
                    max_leverage = max(max_leverage, lev)
        
        total_trades = long_count + short_count + neutral_count
        avg_leverage = leverage_sum / leverage_count if leverage_count > 0 else 1.0
        
        # 计算爆仓数量
        liquidated_count = self.initial_agents - len(agents)
        
        results = {
            'backtest_summary': {
                'total_steps': self.current_step,
                'evolution_cycles': self.evolution_cycles,
                'duration_days': (self.kline_data['timestamp'].max() - self.kline_data['timestamp'].min()).days,
                'start_time': str(self.kline_data['timestamp'].min()),
                'end_time': str(self.kline_data['timestamp'].max())
            },
            'market_performance': {
                'initial_price': float(initial_price),
                'final_price': float(final_price),
                'market_return': float((final_price / initial_price - 1) * 100),
                'price_change': float(final_price - initial_price)
            },
            'population': {
                'initial': self.initial_agents,
                'final': len(agents),
                'survival_rate': float(len(agents) / self.initial_agents * 100)
            },
            'capital': {
                'initial_avg': self.initial_capital,
                'final_avg': float(np.mean(final_capitals)),
                'final_max': float(np.max(final_capitals)),
                'final_min': float(np.min(final_capitals)),
                'final_std': float(np.std(final_capitals))
            },
            'returns': {
                'avg_return': float((np.mean(final_capitals) / self.initial_capital - 1) * 100),
                'max_return': float((np.max(final_capitals) / self.initial_capital - 1) * 100),
                'min_return': float((np.min(final_capitals) / self.initial_capital - 1) * 100)
            },
            'trading_stats': {
                'total_trades': total_trades,
                'long_trades': long_count,
                'short_trades': short_count,
                'neutral_trades': neutral_count,
                'long_pct': float(long_count / total_trades * 100) if total_trades > 0 else 0,
                'short_pct': float(short_count / total_trades * 100) if total_trades > 0 else 0,
                'avg_leverage': float(avg_leverage),
                'max_leverage': float(max_leverage)
            },
            'risk_stats': {
                'initial_agents': self.initial_agents,
                'survived_agents': len(agents),
                'liquidated_agents': liquidated_count,
                'liquidation_rate': float(liquidated_count / self.initial_agents * 100)
            }
        }
        
        return results
    
    def save_results(self, output_dir: str = "results/historical_backtest"):
        """保存回测结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存结果JSON
        results = self.generate_results()
        results_file = output_path / f"results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 结果已保存: {results_file}")
        
        # 保存价格历史
        price_df = pd.DataFrame(self.price_history)
        price_file = output_path / f"price_history_{timestamp}.csv"
        price_df.to_csv(price_file, index=False)
        logger.info(f"💾 价格历史已保存: {price_file}")
        
        # 保存种群历史
        if self.population_history:
            pop_df = pd.DataFrame(self.population_history)
            pop_file = output_path / f"population_history_{timestamp}.csv"
            pop_df.to_csv(pop_file, index=False)
            logger.info(f"💾 种群历史已保存: {pop_file}")
        
        return results_file
    
    def print_summary(self):
        """打印回测摘要"""
        results = self.generate_results()
        
        print("\n" + "="*60)
        print("📊 回测结果摘要")
        print("="*60)
        
        print("\n📅 回测周期:")
        summary = results['backtest_summary']
        print(f"   开始时间: {summary['start_time']}")
        print(f"   结束时间: {summary['end_time']}")
        print(f"   回测天数: {summary['duration_days']}天")
        print(f"   K线数量: {summary['total_steps']}根")
        print(f"   进化次数: {summary['evolution_cycles']}次")
        
        print("\n📈 市场表现:")
        market = results['market_performance']
        print(f"   初始价格: ${market['initial_price']:,.2f}")
        print(f"   最终价格: ${market['final_price']:,.2f}")
        print(f"   市场收益: {market['market_return']:+.2f}%")
        
        print("\n👥 种群表现:")
        pop = results['population']
        print(f"   初始数量: {pop['initial']}个")
        print(f"   最终数量: {pop['final']}个")
        print(f"   存活率: {pop['survival_rate']:.1f}%")
        
        print("\n💰 资金表现:")
        capital = results['capital']
        print(f"   初始平均: ${capital['initial_avg']:,.2f}")
        print(f"   最终平均: ${capital['final_avg']:,.2f}")
        print(f"   最终最高: ${capital['final_max']:,.2f}")
        print(f"   最终最低: ${capital['final_min']:,.2f}")
        
        print("\n📊 收益率:")
        returns = results['returns']
        print(f"   平均收益: {returns['avg_return']:+.2f}%")
        print(f"   最高收益: {returns['max_return']:+.2f}%")
        print(f"   最低收益: {returns['min_return']:+.2f}%")
        
        print("\n📈 交易统计（多空 + 杠杆）:")
        trading = results['trading_stats']
        print(f"   总交易次数: {trading['total_trades']}次")
        print(f"   做多(Long): {trading['long_trades']}次 ({trading['long_pct']:.1f}%)")
        print(f"   做空(Short): {trading['short_trades']}次 ({trading['short_pct']:.1f}%)")
        print(f"   空仓(Neutral): {trading['neutral_trades']}次")
        print(f"   平均杠杆: {trading['avg_leverage']:.2f}x ⭐")
        print(f"   最高杠杆: {trading['max_leverage']:.2f}x")
        
        print("\n💥 风险统计（爆仓）:")
        risk = results['risk_stats']
        print(f"   初始Agent: {risk['initial_agents']}个")
        print(f"   幸存Agent: {risk['survived_agents']}个")
        print(f"   爆仓Agent: {risk['liquidated_agents']}个 💀")
        print(f"   爆仓率: {risk['liquidation_rate']:.1f}%")
        
        print("\n" + "="*60)
        
        # 对比市场
        if returns['avg_return'] > market['market_return']:
            outperform = returns['avg_return'] - market['market_return']
            print(f"✅ Agent平均跑赢市场 {outperform:.2f}个百分点")
        else:
            underperform = market['market_return'] - returns['avg_return']
            print(f"❌ Agent平均跑输市场 {underperform:.2f}个百分点")
        
        print("="*60)


def test_historical_backtest():
    """测试历史回测框架"""
    print("\n" + "="*60)
    print("🧪 测试历史回测框架")
    print("="*60)
    
    # 导入必要模块
    from prometheus.market.okx_data_loader import OKXDataLoader
    from prometheus.core.moirai import Moirai
    from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
    
    # 1. 加载历史数据
    print("\n📋 步骤1: 加载历史数据")
    loader = OKXDataLoader()
    kline_data = loader.generate_sample_data(
        symbol="BTC/USDT",
        days=30,
        interval="1d"
    )
    
    # 2. 初始化进化管理器
    print("\n📋 步骤2: 初始化进化管理器")
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 3. 创建回测引擎
    print("\n📋 步骤3: 创建回测引擎")
    backtest = HistoricalBacktest(
        evolution_manager=evolution_manager,
        kline_data=kline_data,
        evolution_interval=10,  # 每10根K线进化一次
        initial_agents=30,
        initial_capital=10000.0
    )
    
    # 4. 运行回测
    print("\n📋 步骤4: 运行回测")
    results = backtest.run()
    
    # 5. 打印结果
    backtest.print_summary()
    
    # 6. 保存结果
    print("\n📋 步骤6: 保存结果")
    backtest.save_results()
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    test_historical_backtest()

