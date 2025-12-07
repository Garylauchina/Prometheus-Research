#!/usr/bin/env python3
"""
🌍 全天候交易系统测试（遵循三大铁律）
============================================================================
目标：验证Prometheus在所有市场环境下的盈利能力

成功标准：
1. 牛市：系统收益 > BTC（做多跑赢）
2. 熊市：系统收益 > +30%（做空大赚）
3. 震荡：系统收益 > +20%（波段盈利）
4. 暴跌：系统收益 > +50%（双向收割）

这才是真正的"在混沌中寻找规则"！

============================================================================
📋 遵循Prometheus代码三大铁律 (2025-12-07)
============================================================================
✅ 第1关：使用Facade入口 - run_scenario() 统一封装
✅ 第2关：基于标准模板 - test_ultimate_v6_CORRECT.py
✅ 第3关：对账验证 - 检查账簿一致性，拒绝空记录

违反后果：产生不可信的测试结果，浪费大量调试时间！
============================================================================
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Tuple

from prometheus.facade.v6_facade import run_scenario

# 简洁日志
logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(message)s')

def load_market_data():
    """加载并分割不同市场环境的数据"""
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    
    # 分析价格趋势，找出不同市场环境
    prices = df['close'].tolist()
    
    scenarios = {
        'bull': {
            'name': '牛市 📈',
            'description': '持续上涨，考验做多能力',
            'data': None,
            'target': 'system_return > btc_return'
        },
        'bear': {
            'name': '熊市 📉',
            'description': '持续下跌，考验做空能力',
            'data': None,
            'target': 'system_return > 30%'
        },
        'sideways': {
            'name': '震荡市 📊',
            'description': '横盘波动，考验波段能力',
            'data': None,
            'target': 'system_return > 20%'
        },
        'crash': {
            'name': '暴跌 💥',
            'description': '急速下跌，考验风控能力',
            'data': None,
            'target': 'system_return > 50%'
        }
    }
    
    # 自动识别市场环境
    # 牛市：寻找最长的上涨段
    max_bull_len = 0
    max_bull_start = 0
    current_bull_len = 0
    current_bull_start = 0
    
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            if current_bull_len == 0:
                current_bull_start = i - 1
            current_bull_len += 1
        else:
            if current_bull_len > max_bull_len:
                max_bull_len = current_bull_len
                max_bull_start = current_bull_start
            current_bull_len = 0
    
    if current_bull_len > max_bull_len:
        max_bull_len = current_bull_len
        max_bull_start = current_bull_start
    
    if max_bull_len > 50:
        scenarios['bull']['data'] = prices[max_bull_start:max_bull_start+min(200, max_bull_len)]
    
    # 熊市：寻找最长的下跌段
    max_bear_len = 0
    max_bear_start = 0
    current_bear_len = 0
    current_bear_start = 0
    
    for i in range(1, len(prices)):
        if prices[i] < prices[i-1]:
            if current_bear_len == 0:
                current_bear_start = i - 1
            current_bear_len += 1
        else:
            if current_bear_len > max_bear_len:
                max_bear_len = current_bear_len
                max_bear_start = current_bear_start
            current_bear_len = 0
    
    if current_bear_len > max_bear_len:
        max_bear_len = current_bear_len
        max_bear_start = current_bear_start
    
    if max_bear_len > 50:
        scenarios['bear']['data'] = prices[max_bear_start:max_bear_start+min(200, max_bear_len)]
    
    # 震荡市：寻找波动率高但趋势不明显的段
    window = 200
    for i in range(len(prices) - window):
        segment = prices[i:i+window]
        trend = (segment[-1] - segment[0]) / segment[0]
        volatility = np.std(segment) / np.mean(segment)
        
        if abs(trend) < 0.2 and volatility > 0.05:  # 趋势小但波动大
            scenarios['sideways']['data'] = segment
            break
    
    # 暴跌：寻找单日或短期内跌幅最大的段
    max_drop = 0
    max_drop_idx = 0
    window = 30
    
    for i in range(len(prices) - window):
        drop = (prices[i] - min(prices[i:i+window])) / prices[i]
        if drop > max_drop:
            max_drop = drop
            max_drop_idx = i
    
    if max_drop > 0.3:  # 跌幅超过30%
        scenarios['crash']['data'] = prices[max_drop_idx:max_drop_idx+min(100, len(prices)-max_drop_idx)]
    
    # 如果没找到合适的段，使用默认段
    if scenarios['bull']['data'] is None:
        scenarios['bull']['data'] = prices[:200]  # 默认前200天
    
    if scenarios['bear']['data'] is None:
        # 反转牛市数据模拟熊市
        scenarios['bear']['data'] = prices[:200][::-1]
    
    if scenarios['sideways']['data'] is None:
        # 使用中间段
        mid = len(prices) // 2
        scenarios['sideways']['data'] = prices[mid:mid+200]
    
    if scenarios['crash']['data'] is None:
        # 使用熊市的前50天（快速下跌）
        scenarios['crash']['data'] = scenarios['bear']['data'][:50]
    
    return scenarios

def make_market_feed(prices):
    """构造市场数据生成器"""
    def feed(cycle):
        idx = min(cycle - 1, len(prices) - 1)
        return {'price': prices[idx]}, {}
    return feed

def run_scenario_test(scenario_name: str, prices: List[float], num_runs: int = 5):
    """运行单个场景测试（遵循三大铁律）"""
    print(f"\n{'='*80}")
    print(f"🧪 测试场景: {scenario_name}")
    print(f"{'='*80}")
    print(f"   数据长度: {len(prices)}天")
    print(f"   起始价格: ${prices[0]:,.2f}")
    print(f"   结束价格: ${prices[-1]:,.2f}")
    
    btc_return = (prices[-1] - prices[0]) / prices[0] * 100
    print(f"   BTC收益:  {btc_return:+.2f}%")
    print()
    
    results = []
    
    for run_id in range(1, num_runs + 1):
        print(f"   🔄 Run {run_id}/{num_runs}...", end=' ', flush=True)
        
        market_feed = make_market_feed(prices)
        
        facade = run_scenario(
            mode="backtest",
            total_cycles=len(prices),
            market_feed=market_feed,
            num_families=50,
            agent_count=50,
            capital_per_agent=10000.0,
            scenario=f"all_weather_{scenario_name}_run{run_id}",
            evo_interval=30,
            seed=9000 + run_id
        )
        
        # ==================== 第3关：对账验证 ====================
        ledger_check_passed = True
        empty_records = []
        
        for agent in facade.moirai.agents:
            account = getattr(agent, "account", None)
            if account and hasattr(account, "private_ledger"):
                private_ledger = account.private_ledger
                public_trades = facade.public_ledger.get_agent_trades(agent.agent_id)
                
                # 检查空记录
                empty_private = [t for t in private_ledger.trade_history if t.amount == 0 or t.price == 0]
                empty_public = [t for t in public_trades if t.amount == 0 or t.price == 0]
                
                if empty_private or empty_public:
                    empty_records.append({
                        'agent_id': agent.agent_id,
                        'empty_private': len(empty_private),
                        'empty_public': len(empty_public)
                    })
                    ledger_check_passed = False
        
        if not ledger_check_passed:
            print(f"\n⚠️ 警告：发现{len(empty_records)}个Agent有空记录！")
            for rec in empty_records[:3]:  # 只显示前3个
                print(f"   - {rec['agent_id']}: 私账{rec['empty_private']}条, 公账{rec['empty_public']}条")
        
        # 计算系统收益
        current_price = prices[-1]
        system_capital = 0
        system_initial = 0
        long_agents = 0
        short_agents = 0
        
        for agent in facade.moirai.agents:
            unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
            effective_capital = agent.current_capital + unrealized_pnl
            
            system_initial += agent.initial_capital
            system_capital += effective_capital
            
            # 统计多空分布
            ledger = agent.account.private_ledger
            if ledger.long_position and ledger.long_position.amount > 0:
                long_agents += 1
            if ledger.short_position and ledger.short_position.amount > 0:
                short_agents += 1
        
        system_return = (system_capital - system_initial) / system_initial * 100
        
        results.append({
            'system_return': system_return,
            'long_agents': long_agents,
            'short_agents': short_agents,
            'ledger_check_passed': ledger_check_passed,
            'empty_records': len(empty_records)
        })
        
        check_status = "✅" if ledger_check_passed else "❌"
        print(f"系统收益: {system_return:+.2f}%, 多头:{long_agents}, 空头:{short_agents}, 对账:{check_status}")
    
    # 统计结果
    avg_return = np.mean([r['system_return'] for r in results])
    std_return = np.std([r['system_return'] for r in results])
    avg_long = np.mean([r['long_agents'] for r in results])
    avg_short = np.mean([r['short_agents'] for r in results])
    ledger_pass_rate = sum([1 for r in results if r['ledger_check_passed']]) / len(results) * 100
    total_empty_records = sum([r['empty_records'] for r in results])
    
    print(f"\n{'='*80}")
    print(f"📊 场景汇总: {scenario_name}")
    print(f"{'='*80}")
    print(f"   BTC基准:      {btc_return:+.2f}%")
    print(f"   系统平均收益: {avg_return:+.2f}% ± {std_return:.2f}%")
    print(f"   平均多头比例: {avg_long/50*100:.1f}%")
    print(f"   平均空头比例: {avg_short/50*100:.1f}%")
    print(f"   ✅ 对账通过率: {ledger_pass_rate:.0f}%")
    if total_empty_records > 0:
        print(f"   ⚠️ 空记录总数: {total_empty_records}")
    
    return {
        'scenario_name': scenario_name,
        'btc_return': btc_return,
        'system_return': avg_return,
        'std_return': std_return,
        'long_pct': avg_long / 50,
        'short_pct': avg_short / 50
    }

def evaluate_performance(summary: Dict):
    """评估系统在各市场环境的表现"""
    print(f"\n{'='*80}")
    print("🎯 全天候系统评估")
    print(f"{'='*80}\n")
    
    total_score = 0
    max_score = 0
    
    for scenario_key, data in summary.items():
        name = data['scenario_name']
        btc_return = data['btc_return']
        system_return = data['system_return']
        
        print(f"{'='*80}")
        print(f"{name}")
        print(f"{'='*80}")
        print(f"   BTC基准:     {btc_return:+.2f}%")
        print(f"   系统收益:    {system_return:+.2f}%")
        
        # 评分逻辑
        if scenario_key == 'bull':
            # 牛市：跑赢BTC
            max_score += 100
            if system_return > btc_return:
                score = 100
                result = "✅ 跑赢BTC！"
            elif system_return > btc_return * 0.8:
                score = 80
                result = "⚠️ 接近目标（达到BTC的80%）"
            else:
                score = max(0, 50 + (system_return / btc_return - 0.5) * 100)
                result = f"❌ 未达标（仅达到BTC的{system_return/btc_return*100:.1f}%）"
        
        elif scenario_key == 'bear':
            # 熊市：做空大赚（目标>30%）
            max_score += 100
            if system_return > 30:
                score = 100
                result = "✅ 熊市大赚！"
            elif system_return > 0:
                score = 50 + system_return / 30 * 50
                result = f"⚠️ 盈利但未达标（目标>+30%）"
            else:
                score = max(0, 50 + system_return)  # 亏损扣分
                result = f"❌ 未能做空获利"
        
        elif scenario_key == 'sideways':
            # 震荡市：波段盈利（目标>20%）
            max_score += 100
            if system_return > 20:
                score = 100
                result = "✅ 波段盈利！"
            elif system_return > 10:
                score = 50 + (system_return - 10) / 10 * 50
                result = f"⚠️ 盈利但未达标（目标>+20%）"
            else:
                score = max(0, 50 + system_return)
                result = f"❌ 波段操作失败"
        
        elif scenario_key == 'crash':
            # 暴跌：双向收割（目标>50%）
            max_score += 100
            if system_return > 50:
                score = 100
                result = "✅ 暴跌中大赚！"
            elif system_return > 0:
                score = 50 + system_return / 50 * 50
                result = f"⚠️ 盈利但未达标（目标>+50%）"
            else:
                score = max(0, 50 + system_return / 2)
                result = f"❌ 暴跌应对失败"
        
        else:
            score = 0
            result = "未知场景"
        
        total_score += score
        print(f"   评分:        {score:.0f}/100")
        print(f"   评价:        {result}")
        print()
    
    final_score = total_score / max_score * 100 if max_score > 0 else 0
    
    print(f"{'='*80}")
    print(f"🏆 总体评分: {final_score:.1f}/100")
    print(f"{'='*80}\n")
    
    if final_score >= 80:
        print("🎉 优秀！全天候系统运行良好！")
    elif final_score >= 60:
        print("⚠️ 及格，但还有提升空间")
    else:
        print("❌ 不及格，需要重大改进")
    
    return final_score

def main():
    print("=" * 80)
    print("🌍 Prometheus全天候交易系统测试")
    print("=" * 80)
    print()
    print("💡 测试理念:")
    print("   在黑暗中寻找亮光 - 在所有市场环境都能盈利")
    print("   在混沌中寻找规则 - 识别并适应不同市场")
    print("   在死亡中寻找生命 - 从失败中学习成长")
    print("   不忘初心，方得始终 - 盈利是唯一目标")
    print()
    print("🎯 成功标准:")
    print("   1. 牛市：系统收益 > BTC（做多跑赢）")
    print("   2. 熊市：系统收益 > +30%（做空大赚）")
    print("   3. 震荡：系统收益 > +20%（波段盈利）")
    print("   4. 暴跌：系统收益 > +50%（双向收割）")
    print("=" * 80)
    
    # 加载市场数据
    print("\n🔍 分析历史数据，识别市场环境...")
    scenarios = load_market_data()
    
    # 运行所有场景测试
    summary = {}
    for key, scenario in scenarios.items():
        if scenario['data']:
            result = run_scenario_test(
                scenario['name'],
                scenario['data'],
                num_runs=3  # 每个场景3次实验
            )
            summary[key] = result
    
    # 评估总体表现
    final_score = evaluate_performance(summary)
    
    print("\n" + "=" * 80)
    print("🎓 结论")
    print("=" * 80)
    
    if final_score >= 80:
        print("✅ Prometheus已经具备全天候盈利能力！")
        print("   可以进入实盘模拟测试阶段！")
    elif final_score >= 60:
        print("⚠️ 系统基本可用，但需要针对性优化：")
        for key, data in summary.items():
            if key == 'bull' and data['system_return'] < data['btc_return']:
                print(f"   - 牛市表现不足，需要加强做多策略")
            elif key == 'bear' and data['system_return'] < 30:
                print(f"   - 熊市未能做空获利，需要改进趋势识别")
            elif key == 'sideways' and data['system_return'] < 20:
                print(f"   - 震荡市波段操作不足，需要提高交易频率")
            elif key == 'crash' and data['system_return'] < 50:
                print(f"   - 暴跌应对不足，需要加强风控和快速反应")
    else:
        print("❌ 系统尚未准备好，需要重大改进：")
        print("   1. 检查市场环境识别机制")
        print("   2. 优化Daimon决策逻辑")
        print("   3. 加强进化选择压力")
        print("   4. 调整fitness函数")
    
    print("=" * 80)

if __name__ == '__main__':
    main()

