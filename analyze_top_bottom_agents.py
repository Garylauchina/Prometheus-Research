#!/usr/bin/env python3
"""
深度分析：最好和最差的5个Agent
包括先天特质、后天特质、全生命周期行为
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class AgentLifecycleTracker:
    """Agent生命周期追踪器"""
    
    def __init__(self):
        self.agent_records = {}  # {agent_id: record}
        self.trading_history = {}  # {agent_id: [trades]}
    
    def register_agent(self, agent, birth_step):
        """注册新Agent"""
        agent_id = agent.agent_id
        
        # 提取先天特质
        instinct_traits = {
            'risk_tolerance': getattr(agent.instinct, 'risk_tolerance', 0.5),
            'time_preference': getattr(agent.instinct, 'time_preference', 0.5),
            'loss_aversion': getattr(agent.instinct, 'loss_aversion', 0.5),
            'curiosity': getattr(agent.instinct, 'curiosity', 0.5),
            'conservatism': getattr(agent.instinct, 'conservatism', 0.5),
        }
        
        # 提取家族信息
        try:
            family_info = agent.lineage.get_dominant_families(top_n=1)[0] if hasattr(agent, 'lineage') else None
        except:
            family_info = "Unknown"
        generation = agent.generation if hasattr(agent, 'generation') else 0
        
        self.agent_records[agent_id] = {
            'agent_id': agent_id,
            'birth_step': birth_step,
            'death_step': None,
            'initial_capital': agent.current_capital,
            'final_capital': agent.current_capital,
            'max_capital': agent.current_capital,
            'min_capital': agent.current_capital,
            'instinct_traits': instinct_traits,
            'family': family_info,
            'generation': generation,
            'personality': agent.instinct.describe_personality() if hasattr(agent.instinct, 'describe_personality') else '',
            'trade_count': 0,
            'long_trades': 0,
            'short_trades': 0,
            'total_leverage_used': 0.0,
            'evolution_survived': 0,
        }
        
        self.trading_history[agent_id] = []
    
    def record_trade(self, agent_id, step, position, leverage, capital_before, capital_after, price_change):
        """记录交易"""
        if agent_id not in self.agent_records:
            return
        
        record = self.agent_records[agent_id]
        record['trade_count'] += 1
        record['total_leverage_used'] += leverage
        
        if position > 0:
            record['long_trades'] += 1
        elif position < 0:
            record['short_trades'] += 1
        
        # 更新资金记录
        record['final_capital'] = capital_after
        record['max_capital'] = max(record['max_capital'], capital_after)
        record['min_capital'] = min(record['min_capital'], capital_after)
        
        # 记录交易详情
        self.trading_history[agent_id].append({
            'step': step,
            'position': position,
            'leverage': leverage,
            'capital_before': capital_before,
            'capital_after': capital_after,
            'pnl': capital_after - capital_before,
            'price_change': price_change
        })
    
    def record_evolution_survival(self, agent_id):
        """记录进化存活"""
        if agent_id in self.agent_records:
            self.agent_records[agent_id]['evolution_survived'] += 1
    
    def record_death(self, agent_id, step):
        """记录死亡"""
        if agent_id in self.agent_records:
            self.agent_records[agent_id]['death_step'] = step
    
    def get_top_agents(self, n=5):
        """获取最好的N个Agent"""
        agents = list(self.agent_records.values())
        agents.sort(key=lambda x: x['final_capital'], reverse=True)
        return agents[:n]
    
    def get_bottom_agents(self, n=5):
        """获取最差的N个Agent"""
        agents = list(self.agent_records.values())
        agents.sort(key=lambda x: x['final_capital'])
        return agents[:n]


def run_tracked_backtest():
    """运行带追踪的回测"""
    print()
    print("=" * 80)
    print("🔍 运行带生命周期追踪的回测")
    print("=" * 80)
    print()
    
    # 加载数据
    print("📥 加载OKX历史数据...")
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(f"✅ 数据加载完成: {len(df)}条")
    print()
    
    # 初始化系统
    print("🧬 初始化Prometheus系统...")
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 初始化追踪器
    tracker = AgentLifecycleTracker()
    
    # 创建初始Agent
    print("🌱 创建初始Agent...")
    agents = moirai._genesis_create_agents(
        agent_count=50,
        gene_pool=[],
        capital_per_agent=10000.0
    )
    
    for agent in agents:
        agent.fitness = 1.0
        tracker.register_agent(agent, birth_step=0)
    
    moirai.agents = agents
    print(f"✅ 创建完成: {len(agents)}个Agent")
    print()
    
    # 运行回测（简化版，只跑200步）
    print("🚀 开始回测（200步）...")
    evolution_interval = 30
    current_step = 0
    
    for idx, row in df.head(200).iterrows():
        current_step += 1
        current_price = row['close']
        
        if idx > 0:
            prev_price = df.iloc[idx - 1]['close']
            price_change = (current_price - prev_price) / prev_price
        else:
            price_change = 0.0
        
        # 每个Agent交易
        for agent in agents:
            if agent.current_capital <= 0:
                continue
            
            capital_before = agent.current_capital
            
            # Agent决策
            risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
            if abs(price_change) < 0.001:
                position = 0.0
            elif price_change > 0:
                position = risk_tolerance * 0.8
            else:
                position = -risk_tolerance * 0.8
            
            # 杠杆选择
            if risk_tolerance < 0.2:
                leverage = 1.0 + risk_tolerance * 10
            elif risk_tolerance < 0.6:
                leverage = 3.0 + (risk_tolerance - 0.2) * 10
            else:
                leverage = 5.0 + (risk_tolerance - 0.6) * 25
            
            leverage = min(leverage, 100.0)
            
            # 计算收益
            base_return = price_change * position
            leveraged_return = base_return * leverage
            
            # 简化成本
            if abs(position) > 0.01:
                cost = 0.0015  # 0.15%
                leveraged_return -= cost * leverage
            
            # 检查爆仓
            if leveraged_return <= -1.0:
                agent.current_capital = 0.0
                tracker.record_death(agent.agent_id, current_step)
            else:
                agent.current_capital *= (1 + leveraged_return)
            
            # 记录交易
            tracker.record_trade(
                agent.agent_id, current_step, position, leverage,
                capital_before, agent.current_capital, price_change
            )
        
        # 定期进化
        if current_step % evolution_interval == 0:
            # 淘汰爆仓Agent
            agents = [a for a in agents if a.current_capital > 0]
            moirai.agents = agents
            
            # 记录存活
            for agent in agents:
                tracker.record_evolution_survival(agent.agent_id)
            
            # 运行进化
            try:
                evolution_manager.run_evolution_cycle()
                agents = moirai.agents
                
                # 注册新Agent
                for agent in agents:
                    if agent.agent_id not in tracker.agent_records:
                        tracker.register_agent(agent, current_step)
            except Exception as e:
                pass
        
        if current_step % 50 == 0:
            print(f"   Step {current_step}/200 | Price: ${current_price:,.2f} | Agents: {len(agents)}")
    
    print()
    print("✅ 回测完成")
    print()
    
    return tracker


def analyze_agent(agent_data, tracker, rank, category):
    """分析单个Agent"""
    agent_id = agent_data['agent_id']
    
    print(f"{'='*80}")
    print(f"{'🏆' if category == 'top' else '💀'} #{rank} - {agent_id}")
    print(f"{'='*80}")
    print()
    
    # 基本信息
    print(f"📊 基本信息:")
    print(f"   Agent ID: {agent_id}")
    print(f"   出生: Step {agent_data['birth_step']}")
    death = agent_data['death_step']
    if death:
        print(f"   死亡: Step {death}")
        print(f"   寿命: {death - agent_data['birth_step']}步")
    else:
        print(f"   状态: 存活")
        print(f"   寿命: {200 - agent_data['birth_step']}步")
    print(f"   家族: {agent_data['family']}")
    print(f"   世代: 第{agent_data['generation']}代")
    print()
    
    # 资金表现
    print(f"💰 资金表现:")
    print(f"   初始资金: ${agent_data['initial_capital']:,.2f}")
    print(f"   最终资金: ${agent_data['final_capital']:,.2f}")
    print(f"   最高资金: ${agent_data['max_capital']:,.2f}")
    print(f"   最低资金: ${agent_data['min_capital']:,.2f}")
    profit = agent_data['final_capital'] - agent_data['initial_capital']
    roi = (agent_data['final_capital'] / agent_data['initial_capital'] - 1) * 100
    print(f"   盈亏: ${profit:,.2f}")
    print(f"   ROI: {roi:,.2f}%")
    print()
    
    # 交易统计
    print(f"📈 交易统计:")
    print(f"   总交易次数: {agent_data['trade_count']}")
    print(f"   做多次数: {agent_data['long_trades']}")
    print(f"   做空次数: {agent_data['short_trades']}")
    avg_leverage = agent_data['total_leverage_used'] / agent_data['trade_count'] if agent_data['trade_count'] > 0 else 0
    print(f"   平均杠杆: {avg_leverage:.2f}x")
    print(f"   进化存活: {agent_data['evolution_survived']}次")
    print()
    
    # 先天特质
    print(f"🧬 先天特质（基因+本能）:")
    traits = agent_data['instinct_traits']
    print(f"   风险承受度: {traits['risk_tolerance']:.3f} {'⚠️ 高风险' if traits['risk_tolerance'] > 0.7 else '✅ 适中' if traits['risk_tolerance'] > 0.3 else '🛡️ 保守'}")
    print(f"   时间偏好: {traits['time_preference']:.3f} {'📅 长期' if traits['time_preference'] > 0.6 else '⏱️ 短期' if traits['time_preference'] < 0.4 else '⚖️ 平衡'}")
    print(f"   损失厌恶: {traits['loss_aversion']:.3f} {'😰 极度厌恶' if traits['loss_aversion'] > 0.7 else '😐 一般' if traits['loss_aversion'] > 0.3 else '😎 麻木'}")
    print(f"   好奇心: {traits['curiosity']:.3f} {'🔍 极度好奇' if traits['curiosity'] > 0.7 else '👀 正常' if traits['curiosity'] > 0.3 else '😴 迟钝'}")
    print(f"   保守性: {traits['conservatism']:.3f} {'🛡️ 极度保守' if traits['conservatism'] > 0.7 else '⚖️ 适中' if traits['conservatism'] > 0.3 else '🚀 激进'}")
    print(f"   性格描述: {agent_data['personality']}")
    print()
    
    # 行为分析
    if agent_id in tracker.trading_history:
        trades = tracker.trading_history[agent_id]
        if len(trades) > 0:
            print(f"📊 行为分析:")
            
            # 盈利交易 vs 亏损交易
            profitable_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] < 0]
            print(f"   盈利交易: {len(profitable_trades)} ({len(profitable_trades)/len(trades)*100:.1f}%)")
            print(f"   亏损交易: {len(losing_trades)} ({len(losing_trades)/len(trades)*100:.1f}%)")
            
            # 最大单笔盈利/亏损
            if profitable_trades:
                max_profit = max(t['pnl'] for t in profitable_trades)
                print(f"   最大单笔盈利: ${max_profit:,.2f}")
            if losing_trades:
                max_loss = min(t['pnl'] for t in losing_trades)
                print(f"   最大单笔亏损: ${max_loss:,.2f}")
            
            # 平均仓位
            avg_position = np.mean([abs(t['position']) for t in trades])
            print(f"   平均仓位: {avg_position:.2f} {'(激进)' if avg_position > 0.6 else '(适中)' if avg_position > 0.3 else '(保守)'}")
            
            # 资金曲线波动
            capitals = [t['capital_after'] for t in trades]
            capital_std = np.std(capitals)
            capital_mean = np.mean(capitals)
            volatility = capital_std / capital_mean if capital_mean > 0 else 0
            print(f"   资金波动率: {volatility:.2%}")
            print()
            
            # 关键时刻（前5笔和后5笔交易）
            print(f"🎬 关键时刻:")
            print(f"   前5笔交易:")
            for i, trade in enumerate(trades[:5], 1):
                direction = "📈做多" if trade['position'] > 0 else "📉做空" if trade['position'] < 0 else "⏸️空仓"
                result = "✅盈利" if trade['pnl'] > 0 else "❌亏损"
                print(f"      {i}. Step {trade['step']}: {direction} {trade['leverage']:.1f}x | {result} ${trade['pnl']:,.2f} | 资金: ${trade['capital_after']:,.2f}")
            
            if len(trades) > 10:
                print(f"   ...")
                print(f"   后5笔交易:")
                for i, trade in enumerate(trades[-5:], len(trades)-4):
                    direction = "📈做多" if trade['position'] > 0 else "📉做空" if trade['position'] < 0 else "⏸️空仓"
                    result = "✅盈利" if trade['pnl'] > 0 else "❌亏损"
                    print(f"      {i}. Step {trade['step']}: {direction} {trade['leverage']:.1f}x | {result} ${trade['pnl']:,.2f} | 资金: ${trade['capital_after']:,.2f}")
            print()
    
    # 成功/失败原因分析
    print(f"💡 {'成功' if category == 'top' else '失败'}原因分析:")
    if category == 'top':
        print(f"   ✅ 关键成功因素:")
        if traits['risk_tolerance'] < 0.7:
            print(f"      1. 风险控制得当（风险承受度{traits['risk_tolerance']:.2f}）")
        if agent_data['evolution_survived'] > 3:
            print(f"      2. 多次进化存活（{agent_data['evolution_survived']}次）")
        if avg_leverage < 10:
            print(f"      3. 杠杆使用适度（平均{avg_leverage:.1f}x）")
        if agent_id in tracker.trading_history and len(tracker.trading_history[agent_id]) > 0:
            trades = tracker.trading_history[agent_id]
            profitable_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades)
            if profitable_rate > 0.5:
                print(f"      4. 盈利交易占比高（{profitable_rate*100:.1f}%）")
    else:
        print(f"   ❌ 关键失败因素:")
        if traits['risk_tolerance'] > 0.8:
            print(f"      1. 过度冒险（风险承受度{traits['risk_tolerance']:.2f}）")
        if agent_data['evolution_survived'] < 2:
            print(f"      2. 未能通过进化考验（仅存活{agent_data['evolution_survived']}次）")
        if avg_leverage > 15:
            print(f"      3. 杠杆过高（平均{avg_leverage:.1f}x）")
        if agent_data['death_step']:
            print(f"      4. 过早死亡（寿命仅{agent_data['death_step'] - agent_data['birth_step']}步）")
    
    print()


def main():
    print()
    print("=" * 80)
    print("🔍 深度分析：最好和最差的Agent")
    print("=" * 80)
    print()
    
    # 运行追踪回测
    tracker = run_tracked_backtest()
    
    # 分析最好的5个
    print()
    print("=" * 80)
    print("🏆 最好的5个Agent")
    print("=" * 80)
    print()
    
    top_agents = tracker.get_top_agents(5)
    for i, agent in enumerate(top_agents, 1):
        analyze_agent(agent, tracker, i, 'top')
    
    # 分析最差的5个
    print()
    print("=" * 80)
    print("💀 最差的5个Agent")
    print("=" * 80)
    print()
    
    bottom_agents = tracker.get_bottom_agents(5)
    for i, agent in enumerate(bottom_agents, 1):
        analyze_agent(agent, tracker, i, 'bottom')
    
    print()
    print("=" * 80)
    print("🎉 分析完成")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()

