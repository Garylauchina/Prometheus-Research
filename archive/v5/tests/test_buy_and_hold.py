#!/usr/bin/env python3
"""
🧪 最小可行性验证：买入持有策略
=========================================

目标：验证系统基础功能是否正常

测试策略：
1. 第1天：买入全部资金（$10,000）的BTC
2. 第2-2000天：持有，不做任何操作
3. 第2000天：计算最终收益

预期结果：
- 如果接近+837%：✅ 系统基础功能正常
- 如果远低于此：❌ 底层存在严重bug
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
from prometheus.core.ledger_system import PublicLedger, AgentAccountSystem, Role

def test_buy_and_hold():
    print('='*80)
    print('🧪 买入持有策略验证测试')
    print('='*80)
    print()
    
    # 1. 加载数据
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    prices = df['close'].tolist()[:2000]
    
    start_price = prices[0]
    end_price = prices[-1]
    btc_return = (end_price - start_price) / start_price * 100
    
    print(f'📊 BTC基准数据：')
    print(f'   起始价格: ${start_price:,.2f}')
    print(f'   结束价格: ${end_price:,.2f}')
    print(f'   理论收益: {btc_return:+.2f}%')
    print()
    
    # 2. 创建账簿系统
    public_ledger = PublicLedger()
    initial_capital = 10000.0
    account = AgentAccountSystem(
        agent_id='test_agent',
        initial_capital=initial_capital,
        public_ledger=public_ledger
    )
    
    print('📝 初始化完成：')
    print(f'   初始资金: ${initial_capital:,.2f}')
    print()
    
    # 3. 第1天：买入
    buy_price = prices[0]
    buy_amount = initial_capital / buy_price * 0.998  # 考虑0.2%手续费
    
    print(f'📈 第1天 买入：')
    print(f'   价格: ${buy_price:,.2f}')
    print(f'   数量: {buy_amount:.6f} BTC')
    print(f'   成本: ${initial_capital:,.2f}')
    
    # 记录买入交易
    account.record_trade(
        trade_type='buy',
        amount=buy_amount,
        price=buy_price,
        confidence=1.0,
        is_real=False,  # 回测模式
        caller_role=Role.SUPERVISOR,
        okx_order_id='BUY_DAY1'
    )
    
    print('   ✅ 买入交易已记录')
    print()
    
    # 4. 第2-2000天：持有（什么都不做）
    print('⏳ 第2-2000天：持有...')
    print()
    
    # 5. 第2000天：计算最终收益
    final_price = prices[-1]
    
    # 计算未实现盈亏
    position = account.private_ledger.long_position
    if position:
        unrealized_pnl = (final_price - position.entry_price) * position.amount
        final_value = initial_capital + unrealized_pnl
        actual_return = (final_value - initial_capital) / initial_capital * 100
        
        print('='*80)
        print('📊 最终结果')
        print('='*80)
        print(f'持仓数量: {position.amount:.6f} BTC')
        print(f'买入价格: ${position.entry_price:,.2f}')
        print(f'当前价格: ${final_price:,.2f}')
        print(f'未实现盈亏: ${unrealized_pnl:,.2f}')
        print(f'最终价值: ${final_value:,.2f}')
        print()
        print(f'理论收益率: {btc_return:+.2f}%')
        print(f'实际收益率: {actual_return:+.2f}%')
        print(f'差异: {abs(btc_return - actual_return):.2f}%')
        print()
        
        if abs(btc_return - actual_return) < 5:
            print('✅ 测试通过！系统基础功能正常！')
            print('   问题确实在决策层和进化层。')
        else:
            print('❌ 测试失败！底层存在严重bug！')
            print('   需要检查账簿系统和盈亏计算。')
        print('='*80)
    else:
        print('❌ 错误：持仓记录丢失！')

if __name__ == '__main__':
    test_buy_and_hold()

