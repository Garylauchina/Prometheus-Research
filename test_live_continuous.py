#!/usr/bin/env python3
"""
连续不间断测试 - 使用OKX虚拟盘实时数据
==========================================

特性：
- 使用OKX虚拟盘实时价格
- 50个Agent持续交易
- 每30个周期进化一次
- 真实下单到OKX
- 不间断运行直到手动停止
"""

import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'config')
from okx_config import OKX_PAPER_TRADING

import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.exchange.okx_api import OKXExchange
from prometheus.core.ledger_system import PublicLedger, AgentAccountSystem, Role

# 只显示关键信息
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

# 屏蔽冗余日志
logging.getLogger('prometheus.core.diversity_monitor').setLevel(logging.CRITICAL)
logging.getLogger('prometheus.core.diversity_protection').setLevel(logging.CRITICAL)
logging.getLogger('prometheus.core.moirai').setLevel(logging.WARNING)  # 不显示Agent诞生详情

logger = logging.getLogger(__name__)

def main():
    print("="*80)
    print("🚀 Prometheus - 连续不间断测试 (OKX虚拟盘)")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    # 初始化OKX
    logger.info("📡 连接OKX虚拟盘...")
    exchange = OKXExchange(
        api_key=OKX_PAPER_TRADING['api_key'],
        api_secret=OKX_PAPER_TRADING['api_secret'],
        passphrase=OKX_PAPER_TRADING['passphrase'],
        paper_trading=False,
        testnet=True
    )
    
    symbol = 'BTC/USDT:USDT'
    
    # 获取初始余额
    initial_balance = exchange.get_account_value()
    logger.info(f"💰 初始余额: ${initial_balance:,.2f}")
    
    # 清理所有持仓
    logger.info("🧹 清理现有持仓...")
    try:
        import ccxt
        ex = ccxt.okx({
            'apiKey': OKX_PAPER_TRADING['api_key'],
            'secret': OKX_PAPER_TRADING['api_secret'],
            'password': OKX_PAPER_TRADING['passphrase'],
            'sandbox': True,
            'options': {'defaultType': 'swap'}
        })
        
        positions = ex.fetch_positions()
        active = [p for p in positions if float(p.get('contracts', 0)) > 0]
        
        if active:
            logger.info(f"   发现 {len(active)} 个持仓，开始平仓...")
            for pos in active:
                side = pos['side']
                contracts = float(pos['contracts'])
                request = {
                    'instId': 'BTC-USDT-SWAP',
                    'tdMode': 'cross',
                    'side': 'sell' if side == 'long' else 'buy',
                    'posSide': side,
                    'ordType': 'market',
                    'sz': str(int(contracts)),
                    'reduceOnly': True
                }
                ex.privatePostTradeOrder(request)
                logger.info(f"   ✅ 平{side.upper()}仓: {contracts}张")
            logger.info("   ✅ 平仓完成")
        else:
            logger.info("   ✅ 无持仓，跳过")
    except Exception as e:
        logger.warning(f"   ⚠️  平仓失败: {e}")
    
    # 初始化系统
    logger.info("🧬 初始化进化系统...")
    
    # 创建公共账簿
    public_ledger = PublicLedger()
    
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 创建50个初始Agent
    logger.info("👥 创建50个Agent...")
    agents = moirai._genesis_create_agents(
        agent_count=50,
        gene_pool=[],
        capital_per_agent=10000.0
    )
    
    # 为每个Agent创建账户系统（标准流程）
    agent_accounts = {}
    for agent in agents:
        agent.fitness = 1.0
        account_system = AgentAccountSystem(
            agent_id=agent.agent_id,
            initial_capital=10000.0,
            public_ledger=public_ledger
        )
        agent_accounts[agent.agent_id] = account_system
        agent.account = account_system  # 关键！挂载到Agent对象
    
    moirai.agents = agents
    logger.info(f"✅ 创建了{len(agents)}个Agent，每个都有独立账户系统")
    
    logger.info(f"✅ 初始化完成！开始连续交易...")
    print()
    
    # 运行参数
    cycle = 0
    evolution_interval = 30  # 每30个周期进化一次
    check_interval = 60  # 每60秒检查一次
    last_price = None
    total_trades = 0
    total_liquidations = 0
    
    try:
        while True:
            cycle += 1
            
            print(f"\n{'='*80}")
            print(f"🔄 周期 {cycle} | {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*80}")
            
            # 获取当前价格
            ticker = exchange.get_ticker(symbol)
            if not ticker:
                logger.error("无法获取行情，跳过本周期")
                time.sleep(check_interval)
                continue
            current_price = ticker['last']
            
            # 计算价格变化
            if last_price:
                price_change = (current_price - last_price) / last_price
            else:
                price_change = 0.0
            
            print(f"📊 当前价格: ${current_price:,.2f}")
            if last_price:
                print(f"   价格变化: {price_change:+.4%}")
            
            last_price = current_price
            
            # 每个Agent交易
            active_agents = [a for a in moirai.agents if a.current_capital > 0]
            print(f"👥 活跃Agent: {len(active_agents)}/{len(moirai.agents)}")
            
            cycle_trades = 0
            
            for agent in active_agents:
                # Agent决策
                risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
                time_preference = getattr(agent.instinct, 'time_preference', 0.5)
                
                # 简化决策逻辑
                if abs(price_change) < 0.0001:  # 降低阈值到0.01%
                    position = 0.0
                elif price_change > 0:
                    position = risk_tolerance * 0.8
                else:
                    position = -risk_tolerance * 0.8
                
                if abs(position) > 0.05:  # 降低交易阈值
                    cycle_trades += 1
                    
                    # 获取Agent账户（标准方式）
                    account = getattr(agent, 'account', None)
                    if not account:
                        logger.error(f"Agent {agent.agent_id} 没有账户系统！")
                        continue
                    
                    # 决定交易方向和类型
                    side = 'buy' if position > 0 else 'sell'
                    
                    # 杠杆选择
                    if risk_tolerance < 0.6:
                        leverage = 3.0 + (risk_tolerance - 0.2) * 10
                    else:
                        leverage = 5.0 + (risk_tolerance - 0.6) * 25
                    
                    leverage = min(max(leverage, 1.0), 10.0)  # 限制最大10倍
                    
                    # 计算交易数量（根据Agent账户的真实资金）
                    agent_capital = account.private_ledger.virtual_capital
                    capital_ratio = abs(position)
                    btc_value = (agent_capital * capital_ratio) / current_price
                    btc_amount = max(0.01, min(btc_value, 0.1))  # 限制在0.01-0.1 BTC之间
                    
                    # 确定正确的trade_type（关键！）
                    # 查询当前持仓状态
                    has_long = account.private_ledger.long_position is not None
                    has_short = account.private_ledger.short_position is not None
                    
                    # 根据持仓和决策方向确定trade_type
                    if position > 0:  # 做多信号
                        if has_short:
                            trade_type = 'cover'  # 先平空
                            actual_side = 'buy'
                        else:
                            trade_type = 'buy'  # 开多或加多
                            actual_side = 'buy'
                    else:  # 做空信号
                        if has_long:
                            trade_type = 'sell'  # 先平多
                            actual_side = 'sell'
                        else:
                            trade_type = 'short'  # 开空或加空
                            actual_side = 'sell'
                    
                    # 下单到OKX
                    try:
                        order = exchange.place_order(symbol, actual_side, btc_amount, leverage=leverage)
                        if order:
                            total_trades += 1
                            # 记录交易到账簿系统
                            account.record_trade(
                                trade_type=trade_type,
                                amount=btc_amount,
                                price=current_price,
                                confidence=abs(position),
                                is_real=True,
                                caller_role=Role.SUPERVISOR,
                                okx_order_id=order.get('order_id')
                            )
                            # 更新Agent的current_capital（从账簿系统同步）
                            agent.current_capital = account.private_ledger.virtual_capital
                    except Exception as e:
                        pass  # 忽略单笔交易错误
            
            print(f"📊 本周期交易: {cycle_trades}笔")
            print(f"📊 累计交易: {total_trades}笔")
            print(f"📊 累计爆仓: {total_liquidations}个")
            
            # 定期进化
            if cycle % evolution_interval == 0:
                logger.info(f"🧬 执行进化 (第{cycle//evolution_interval}次)...")
                
                # 检查是否有Agent因资金过低需要淘汰（低于初始资金的20%）
                moirai.agents = [a for a in moirai.agents if a.current_capital > 2000.0]
                
                if len(moirai.agents) > 0:
                    try:
                        evolution_manager.run_evolution_cycle()
                        logger.info(f"   ✅ 进化完成，当前种群: {len(moirai.agents)}个")
                    except Exception as e:
                        logger.error(f"   ❌ 进化失败: {e}")
                else:
                    logger.warning(f"   ⚠️  所有Agent已爆仓，重新创世...")
                    agents = moirai._genesis_create_agents(50, [], 10000.0)
                    for agent in agents:
                        agent.fitness = 1.0
                    moirai.agents = agents
            
            # 显示Agent统计（基于账簿系统的真实数据）
            try:
                current_balance = exchange.get_account_value()
                print(f"💼 OKX余额: ${current_balance:,.2f}")
                
                # 从账簿系统获取Agent真实资金（标准方式）
                if len(moirai.agents) > 0:
                    capitals = []
                    for agent in moirai.agents:
                        account = getattr(agent, 'account', None)
                        if account:
                            # 同步账簿系统的资金到Agent
                            agent.current_capital = account.private_ledger.virtual_capital
                            capitals.append(agent.current_capital)
                    
                    if capitals:
                        avg_capital = np.mean(capitals)
                        max_capital = max(capitals)
                        min_capital = min(capitals)
                        print(f"💰 Agent资金: 平均${avg_capital:,.2f} | 最高${max_capital:,.2f} | 最低${min_capital:,.2f}")
                        
                        # 显示资金分布
                        profitable = sum(1 for c in capitals if c > 10000)
                        print(f"   盈利Agent: {profitable}/{len(capitals)} ({profitable/len(capitals)*100:.0f}%)")
            except Exception as e:
                logger.error(f"更新统计失败: {e}")
            
            # 等待
            print(f"\n⏳ 等待{check_interval}秒...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("⚠️  手动停止")
        print("="*80)
    except Exception as e:
        print(f"\n\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 获取最终余额
        try:
            final_balance = exchange.get_account_value()
        except:
            final_balance = 0
        
        # 计算Agent统计（从账簿系统获取真实数据，标准方式）
        capitals = []
        for agent in moirai.agents:
            account = getattr(agent, 'account', None)
            if account:
                capital = account.private_ledger.virtual_capital
                capitals.append(capital)
                agent.current_capital = capital  # 同步
        
        alive_agents = [a for a in moirai.agents if a.current_capital > 0]
        if capitals:
            avg_capital = np.mean(capitals)
            max_capital = max(capitals)
            min_capital = min(capitals)
        else:
            avg_capital = max_capital = min_capital = 0
        
        # 打印统计
        print("\n" + "="*80)
        print("📊 测试统计")
        print("="*80)
        print(f"测试时长: {cycle}个周期 ({cycle * check_interval / 60:.1f}分钟)")
        print(f"总交易: {total_trades}笔")
        print(f"总爆仓: {total_liquidations}个")
        print(f"存活Agent: {len(alive_agents)}/50")
        print(f"平均资金: ${avg_capital:,.2f}")
        print(f"最高资金: ${max_capital:,.2f}")
        print(f"最低资金: ${min_capital:,.2f}")
        print(f"初始余额: ${initial_balance:,.2f}")
        print(f"最终余额: ${final_balance:,.2f}")
        print(f"余额变化: ${final_balance - initial_balance:+,.2f} ({(final_balance/initial_balance - 1)*100:+.2f}%)")
        print("="*80)
        
        # 保存结果到文件
        result_file = f"test_live_continuous_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_data = {
            "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "duration_cycles": cycle,
            "duration_minutes": cycle * check_interval / 60,
            "total_trades": total_trades,
            "total_liquidations": total_liquidations,
            "alive_agents": len(alive_agents),
            "avg_capital": float(avg_capital),
            "max_capital": float(max_capital),
            "min_capital": float(min_capital),
            "initial_balance": float(initial_balance),
            "final_balance": float(final_balance),
            "balance_change": float(final_balance - initial_balance),
            "balance_change_pct": float((final_balance/initial_balance - 1)*100),
            "agent_count": 50,
            "check_interval": check_interval,
        }
        
        import json
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        print(f"\n💾 结果已保存到: {result_file}")
        print("="*80)

if __name__ == "__main__":
    main()

