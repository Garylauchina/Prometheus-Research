#!/usr/bin/env python3
"""
快速验证：交易频率测试
目标：确认"鼓励探索"的修复是否生效
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
from prometheus.facade.v6_facade import run_scenario

def load_prices(limit):
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    return df['close'].tolist()[:limit]

def make_feed(prices):
    def feed(cycle):
        idx = min(cycle - 1, len(prices) - 1)
        return {'price': prices[idx]}, {}
    return feed

print('='*80)
print('🧪 交易频率验证测试（100周期）')
print('='*80)
print()
print('目标：验证Agent是否开始积极交易')
print()

prices = load_prices(100)
btc_return = (prices[-1] - prices[0]) / prices[0] * 100

print(f'📊 BTC基准（100天）: {btc_return:+.2f}%')
print()
print('开始测试...')
print('-'*80)

facade = run_scenario(
    mode='backtest',
    total_cycles=100,
    market_feed=make_feed(prices),
    num_families=10,
    agent_count=10,
    capital_per_agent=10000.0,
    scenario='trading_freq_test',
    evo_interval=50,  # 延长进化周期
    seed=3000
)

status = facade.report_status()
agent_return = (status['avg_capital'] - 10000) / 10000 * 100

# 获取交易统计 - ✅ 使用private_ledger的trade_count
total_trades = 0
for agent in facade.moirai.agents:
    actual_count = agent.account.private_ledger.trade_count if hasattr(agent, 'account') else 0
    total_trades += actual_count

avg_trades_per_agent = total_trades / len(facade.moirai.agents)
trade_frequency = avg_trades_per_agent / 100  # 每周期交易次数

print()
print('='*80)
print('📊 交易频率分析')
print('='*80)
print(f'总交易数: {total_trades}')
print(f'Agent数量: {len(facade.moirai.agents)}')
print(f'平均每Agent交易: {avg_trades_per_agent:.1f}次')
print(f'交易频率: {trade_frequency*100:.1f}% (每周期有交易的比例)')
print()
print('='*80)
print('📊 收益对比')
print('='*80)
print(f'BTC收益率:    {btc_return:+.2f}%')
print(f'Agent收益率:  {agent_return:+.2f}%')
print(f'相对表现:     {agent_return / btc_return * 100:.1f}% of BTC')
print()
print('='*80)
print('📊 诊断结论')
print('='*80)

if trade_frequency > 0.3:
    print('✅ 交易频率良好（>30%）')
    print('   "鼓励探索"修复生效！')
    print('   ✅ 下一步：立即实施Memory Layer')
elif trade_frequency > 0.1:
    print('⚠️ 交易频率一般（10-30%）')
    print('   修复部分生效，但仍需加强')
    print('   建议：进一步降低门槛或增加奖励')
else:
    print('❌ 交易频率仍然过低（<10%）')
    print('   修复未生效！')
    print('   必须：重新诊断决策逻辑')

if agent_return > btc_return * 0.5:
    print('✅ 收益表现尚可（>50% of BTC）')
else:
    print('❌ 收益表现差（<50% of BTC）')

print('='*80)

