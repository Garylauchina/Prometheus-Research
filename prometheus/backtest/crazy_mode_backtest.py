"""
🔥 疯狂模式回测

放开Agent的所有束缚：
1. 双向持仓（同时做多做空）
2. 无仓位限制
3. 杠杆叠加
4. 极限测试

看看完全自由的Agent会做出什么选择！
"""

import numpy as np
import logging
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import pandas as pd
import json

from prometheus.backtest.historical_backtest import HistoricalBacktest

logger = logging.getLogger(__name__)


class CrazyModeBacktest(HistoricalBacktest):
    """
    疯狂模式回测：放开所有束缚
    
    新特性：
    1. 双向持仓：Agent可以同时持有多头和空头
    2. 杠杆叠加：多头和空头可以各自使用杠杆
    3. 无限制：移除仓位限制
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.warning("\n" + "="*60)
        logger.warning("🔥 疯狂模式已启动！")
        logger.warning("⚠️  所有安全限制已移除！")
        logger.warning("⚠️  Agent拥有完全自由！")
        logger.warning("="*60 + "\n")
    
    def _agent_make_dual_position_decision(self, agent, price_change: float) -> Dict[str, float]:
        """
        Agent做出双向持仓决策（疯狂模式）
        
        完全自由：
        - 可以同时做多做空
        - 可以各自选择杠杆
        - 可以任意仓位大小
        
        Returns:
            {
                'long_position': 0-1,    # 做多仓位
                'short_position': 0-1,   # 做空仓位
                'long_leverage': 1-100,  # 做多杠杆
                'short_leverage': 1-100  # 做空杠杆
            }
        """
        risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
        time_preference = getattr(agent.instinct, 'time_preference', 0.5)
        
        # 计算趋势
        if len(self.price_history) >= 5:
            recent_prices = [p['price'] for p in self.price_history[-5:]]
            short_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        else:
            short_trend = 0
        
        # 疯狂模式：Agent可以同时做多做空！
        long_position = 0.0
        short_position = 0.0
        long_leverage = self._agent_choose_leverage(agent)
        short_leverage = self._agent_choose_leverage(agent)
        
        # 策略1：高风险偏好者可能双向持仓（对冲或套利）
        if risk_tolerance > 0.7:
            # 激进策略：双向下注
            if abs(short_trend) > 0.02:
                # 趋势明显：主方向重仓，反方向轻仓对冲
                if short_trend > 0:
                    long_position = 0.7 * risk_tolerance
                    short_position = 0.2 * risk_tolerance  # 对冲
                    long_leverage = long_leverage * 1.2  # 主方向杠杆更高
                else:
                    short_position = 0.7 * risk_tolerance
                    long_position = 0.2 * risk_tolerance  # 对冲
                    short_leverage = short_leverage * 1.2
            else:
                # 震荡市：两边都下注
                long_position = 0.5 * risk_tolerance
                short_position = 0.5 * risk_tolerance
        
        elif risk_tolerance > 0.5:
            # 中等风险：根据趋势单边或小对冲
            if short_trend > 0.01:
                long_position = 0.6 * risk_tolerance
                short_position = 0.1 * risk_tolerance  # 小对冲
            elif short_trend < -0.01:
                short_position = 0.6 * risk_tolerance
                long_position = 0.1 * risk_tolerance  # 小对冲
            else:
                # 不确定：两边都试试
                long_position = 0.3 * risk_tolerance
                short_position = 0.3 * risk_tolerance
        
        else:
            # 保守者：还是单边为主
            if short_trend > 0.01:
                long_position = 0.4 * (1 - risk_tolerance)
                short_position = 0
            elif short_trend < -0.01:
                short_position = 0.4 * (1 - risk_tolerance)
                long_position = 0
            else:
                long_position = 0.2
                short_position = 0
        
        # 根据时间偏好调整
        factor = 0.5 + 0.5 * time_preference
        long_position *= factor
        short_position *= factor
        
        # 疯狂模式：允许超过100%（通过杠杆）！
        # 不限制仓位大小！
        
        return {
            'long_position': long_position,
            'short_position': short_position,
            'long_leverage': long_leverage,
            'short_leverage': short_leverage
        }
    
    def run_single_step(self, kline: Dict) -> Dict:
        """
        运行单个时间步（疯狂模式版本）
        """
        timestamp = kline['timestamp']
        current_price = kline['close']
        
        # 记录价格
        self.price_history.append({
            'timestamp': timestamp,
            'price': current_price
        })
        
        # Agent交易逻辑（疯狂模式：双向持仓）
        agents_to_remove = []
        
        for agent in self.evolution_manager.moirai.agents:
            if len(self.price_history) > 1:
                price_change = (current_price - self.price_history[-2]['price']) / self.price_history[-2]['price']
                
                # 疯狂模式：双向持仓决策
                positions = self._agent_make_dual_position_decision(agent, price_change)
                
                long_pos = positions['long_position']
                short_pos = positions['short_position']
                long_lev = positions['long_leverage']
                short_lev = positions['short_leverage']
                
                # 计算多头收益
                long_base_return = price_change * long_pos
                long_leveraged_return = long_base_return * long_lev
                
                # 计算空头收益
                short_base_return = price_change * (-short_pos)  # 做空收益相反
                short_leveraged_return = short_base_return * short_lev
                
                # 总收益 = 多头 + 空头
                total_return = long_leveraged_return + short_leveraged_return
                
                # 交易成本（双向都要付）
                trading_fee = 0.0005
                slippage = 0.0001
                funding_rate = 0.0003
                
                long_cost = 0
                short_cost = 0
                
                if long_pos > 0.01:
                    total_cost = trading_fee + slippage + funding_rate
                    long_cost = total_cost * long_lev
                
                if short_pos > 0.01:
                    total_cost = trading_fee + slippage + funding_rate
                    short_cost = total_cost * short_lev
                
                total_return -= (long_cost + short_cost)
                
                # 检查爆仓
                if total_return <= -1.0:
                    # 爆仓！
                    death_report = {
                        'agent_id': agent.agent_id,
                        'timestamp': timestamp,
                        'price': current_price,
                        'step': self.current_step,
                        'long_position': long_pos,
                        'short_position': short_pos,
                        'long_leverage': long_lev,
                        'short_leverage': short_lev,
                        'price_change': price_change,
                        'total_return': total_return,
                        'capital_before': agent.current_capital,
                        'risk_tolerance': getattr(agent.instinct, 'risk_tolerance', 'unknown'),
                        'trade_count': len(agent.trade_history) if hasattr(agent, 'trade_history') else 0,
                        'mode': 'CRAZY_MODE'
                    }
                    
                    if not hasattr(self, 'liquidation_records'):
                        self.liquidation_records = []
                    self.liquidation_records.append(death_report)
                    
                    logger.warning(f"💥 Agent {agent.agent_id} 爆仓（疯狂模式）！")
                    logger.warning(f"   ├─ 多头仓位: {long_pos:.2f} × {long_lev:.1f}x = {long_pos*long_lev:.2f}x总敞口")
                    logger.warning(f"   ├─ 空头仓位: {short_pos:.2f} × {short_lev:.1f}x = {short_pos*short_lev:.2f}x总敞口")
                    logger.warning(f"   ├─ 总敞口: {(long_pos*long_lev + short_pos*short_lev):.2f}x ⚠️")
                    logger.warning(f"   ├─ 价格变化: {price_change:+.2%}")
                    logger.warning(f"   └─ 总亏损: {total_return:.2%}")
                    
                    agents_to_remove.append(agent)
                    agent.current_capital = 0
                    continue
                
                # 更新资金
                agent.current_capital *= (1 + total_return)
                
                # 记录交易
                if not hasattr(agent, 'trade_history'):
                    agent.trade_history = []
                
                agent.trade_history.append({
                    'timestamp': timestamp,
                    'price': current_price,
                    'long_position': long_pos,
                    'short_position': short_pos,
                    'long_leverage': long_lev,
                    'short_leverage': short_lev,
                    'total_exposure': long_pos * long_lev + short_pos * short_lev,
                    'total_return': total_return,
                    'capital': agent.current_capital,
                    'mode': 'CRAZY'
                })
        
        # 移除爆仓Agent
        if agents_to_remove:
            for agent in agents_to_remove:
                if agent in self.evolution_manager.moirai.agents:
                    self.evolution_manager.moirai.agents.remove(agent)
            logger.warning(f"💀 本轮爆仓: {len(agents_to_remove)}个Agent（疯狂模式）")
        
        # 返回结果
        agents = self.evolution_manager.moirai.agents
        avg_capital = np.mean([a.current_capital for a in agents]) if agents else 0
        
        result = {
            'step': self.current_step,
            'timestamp': timestamp,
            'price': current_price,
            'population': len(agents),
            'avg_capital': avg_capital,
            'crazy_mode': True
        }
        
        self.current_step += 1
        
        return result
    
    def generate_results(self) -> Dict:
        """生成疯狂模式结果"""
        results = super().generate_results()
        
        # 添加疯狂模式特有统计
        agents = self.evolution_manager.moirai.agents
        
        if agents:
            total_long_exposure = 0
            total_short_exposure = 0
            max_total_exposure = 0
            dual_position_count = 0
            trade_count = 0
            
            for agent in agents:
                if hasattr(agent, 'trade_history'):
                    for trade in agent.trade_history:
                        if 'long_position' in trade and 'short_position' in trade:
                            trade_count += 1
                            long_exp = trade['long_position'] * trade['long_leverage']
                            short_exp = trade['short_position'] * trade['short_leverage']
                            total_exp = long_exp + short_exp
                            
                            total_long_exposure += long_exp
                            total_short_exposure += short_exp
                            max_total_exposure = max(max_total_exposure, total_exp)
                            
                            if trade['long_position'] > 0.01 and trade['short_position'] > 0.01:
                                dual_position_count += 1
            
            results['crazy_mode_stats'] = {
                'avg_long_exposure': float(total_long_exposure / trade_count) if trade_count > 0 else 0,
                'avg_short_exposure': float(total_short_exposure / trade_count) if trade_count > 0 else 0,
                'avg_total_exposure': float((total_long_exposure + total_short_exposure) / trade_count) if trade_count > 0 else 0,
                'max_total_exposure': float(max_total_exposure),
                'dual_position_count': dual_position_count,
                'dual_position_rate': float(dual_position_count / trade_count * 100) if trade_count > 0 else 0
            }
        
        return results


def test_crazy_mode():
    """测试疯狂模式"""
    from prometheus.core.moirai import Moirai
    from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
    from prometheus.market.okx_data_loader import OKXDataLoader
    
    print("\n" + "="*60)
    print("🔥 疯狂模式测试")
    print("="*60)
    print("⚠️  所有限制已解除！")
    print("⚠️  Agent拥有完全自由！")
    print("⚠️  这可能会很疯狂...让我们看看会发生什么！")
    print("="*60 + "\n")
    
    # 加载数据
    loader = OKXDataLoader()
    kline_data = loader.load_or_generate(days=30)
    
    # 初始化
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 创建疯狂模式回测
    backtest = CrazyModeBacktest(
        evolution_manager=evolution_manager,
        kline_data=kline_data,
        evolution_interval=10,
        initial_agents=50,
        initial_capital=10000.0
    )
    
    # 运行
    results = backtest.run()
    
    # 打印结果
    print("\n" + "="*60)
    print("🔥 疯狂模式结果")
    print("="*60)
    
    print(f"\n📊 基础结果:")
    print(f"   Agent收益: {results['returns']['avg_return']:+.2f}%")
    print(f"   市场收益: {results['market_performance']['market_return']:+.2f}%")
    print(f"   存活率: {results['population']['survival_rate']:.1f}%")
    print(f"   爆仓率: {results['risk_stats']['liquidation_rate']:.1f}%")
    
    if 'crazy_mode_stats' in results:
        crazy = results['crazy_mode_stats']
        print(f"\n🔥 疯狂模式特有统计:")
        print(f"   平均多头敞口: {crazy['avg_long_exposure']:.2f}x")
        print(f"   平均空头敞口: {crazy['avg_short_exposure']:.2f}x")
        print(f"   平均总敞口: {crazy['avg_total_exposure']:.2f}x ⚡")
        print(f"   最高总敞口: {crazy['max_total_exposure']:.2f}x 💀")
        print(f"   双向持仓次数: {crazy['dual_position_count']}次")
        print(f"   双向持仓比例: {crazy['dual_position_rate']:.1f}%")
    
    print("\n" + "="*60)
    
    return results


if __name__ == "__main__":
    test_crazy_mode()

