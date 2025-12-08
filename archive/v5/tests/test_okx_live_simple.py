#!/usr/bin/env python3
"""
OKX实时连续测试 - 使用test_ultimate_1000x.py的成熟架构
只修改：数据源从CSV改为OKX实时数据
"""

import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'config')
from okx_config import OKX_PAPER_TRADING

import pandas as pd
import numpy as np
import logging
import json
import time
from datetime import datetime
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.exchange.okx_api import OKXExchange

# 屏蔽冗余日志
logging.basicConfig(level=logging.WARNING)
logging.getLogger('prometheus.core.moirai').setLevel(logging.CRITICAL)

def main():
    print("=" * 80)
    print("🚀 OKX实时连续测试（使用成熟架构）")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # 初始化OKX
    print("📡 连接OKX...")
    exchange = OKXExchange(
        api_key=OKX_PAPER_TRADING['api_key'],
        api_secret=OKX_PAPER_TRADING['api_secret'],
        passphrase=OKX_PAPER_TRADING['passphrase'],
        paper_trading=False,
        testnet=True
    )
    
    # 清理持仓
    print("🧹 清理持仓...")
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
        for pos in active:
            request = {
                'instId': 'BTC-USDT-SWAP',
                'tdMode': 'cross',
                'side': 'sell' if pos['side'] == 'long' else 'buy',
                'posSide': pos['side'],
                'ordType': 'market',
                'sz': str(int(float(pos['contracts']))),
                'reduceOnly': True
            }
            ex.privatePostTradeOrder(request)
        print(f"   ✅ 已平{len(active)}个持仓")
    else:
        print("   ✅ 无持仓")
    
    # 初始化系统（完全复制test_ultimate_1000x.py的架构）
    print("🧬 初始化系统...")
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    
    # 创建初始Agent
    print("👥 创建50个Agent...")
    agents = moirai._genesis_create_agents(
        agent_count=50,
        gene_pool=[],
        capital_per_agent=10000.0
    )
    
    for agent in agents:
        agent.fitness = 1.0
    
    moirai.agents = agents
    print(f"✅ {len(agents)}个Agent已创建")
    print()
    
    # 运行参数
    current_step = 0
    evolution_count = 0
    total_trades = 0
    total_liquidations = 0
    evolution_interval = 30
    check_interval = 60  # 60秒检查一次
    
    symbol = 'BTC/USDT:USDT'
    last_price = None
    
    print("🚀 开始连续测试...")
    print("=" * 80)
    print()
    
    try:
        while True:
            current_step += 1
            
            # 获取OKX实时价格（替代CSV）
            ticker = exchange.get_ticker(symbol)
            if not ticker:
                print(f"⚠️  获取价格失败，跳过")
                time.sleep(check_interval)
                continue
            
            current_price = ticker['last']
            
            # 计算价格变化
            if last_price:
                price_change = (current_price - last_price) / last_price
            else:
                price_change = 0.0
            
            last_price = current_price
            
            # 显示进度
            print(f"🔄 步骤 {current_step} | {datetime.now().strftime('%H:%M:%S')}")
            print(f"   价格: ${current_price:,.2f} | 变化: {price_change:+.4%}")
            
            # 每个Agent交易（完全复制test_ultimate_1000x.py的逻辑）
            for agent in agents:
                if agent.current_capital <= 0:
                    continue
                
                # Agent决策
                risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
                time_preference = getattr(agent.instinct, 'time_preference', 0.5)
                
                # 简化决策逻辑
                if abs(price_change) < 0.001:
                    position = 0.0
                elif price_change > 0:
                    position = risk_tolerance * 0.8
                else:
                    position = -risk_tolerance * 0.8
                
                if position != 0:
                    total_trades += 1
                
                # 杠杆选择
                if risk_tolerance < 0.6:
                    leverage = 3.0 + (risk_tolerance - 0.2) * 10
                else:
                    leverage = 5.0 + (risk_tolerance - 0.6) * 25
                
                leverage = min(max(leverage, 1.0), 100.0)
                
                # 计算收益
                base_return = price_change * position
                leveraged_return = base_return * leverage
                
                # 交易成本
                if abs(position) > 0.01:
                    trading_fee = 0.001
                    slippage = 0.0001
                    funding_rate = 0.0003
                    total_cost = trading_fee + slippage + funding_rate
                    leveraged_return -= total_cost * leverage
                
                # 检查爆仓
                if leveraged_return <= -1.0:
                    agent.current_capital = 0.0
                    total_liquidations += 1
                else:
                    agent.current_capital *= (1 + leveraged_return)
            
            # 显示统计
            alive = [a for a in agents if a.current_capital > 0]
            if alive:
                capitals = [a.current_capital for a in alive]
                avg_cap = np.mean(capitals)
                max_cap = max(capitals)
                min_cap = min(capitals)
                profitable = sum(1 for c in capitals if c > 10000)
                print(f"   Agent: {len(alive)}存活 | 平均${avg_cap:,.0f} | 盈利{profitable}个")
            else:
                print(f"   ⚠️  所有Agent已爆仓")
            
            # 定期进化
            if current_step % evolution_interval == 0:
                evolution_count += 1
                agents = [a for a in agents if a.current_capital > 0]
                moirai.agents = agents
                
                print(f"   🧬 进化#{evolution_count}...")
                
                if len(agents) > 0:
                    try:
                        evolution_manager.run_evolution_cycle()
                        agents = moirai.agents
                        print(f"      ✅ 种群: {len(agents)}个")
                    except:
                        pass
                else:
                    print(f"      ⚠️  种群灭绝，重新创世")
                    agents = moirai._genesis_create_agents(50, [], 10000.0)
                    for agent in agents:
                        agent.fitness = 1.0
                    moirai.agents = agents
            
            print()
            
            # 等待
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        print("\n⚠️  手动停止")
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 保存结果
        print("\n" + "=" * 80)
        print("📊 测试结果")
        print("=" * 80)
        
        all_capitals = [a.current_capital for a in moirai.agents]
        alive = [c for c in all_capitals if c > 0]
        
        if alive:
            avg_all = np.mean(all_capitals)
            avg_alive = np.mean(alive)
            print(f"总步数: {current_step}")
            print(f"总交易: {total_trades}")
            print(f"总爆仓: {total_liquidations}")
            print(f"存活: {len(alive)}/50")
            print(f"平均资金(全部): ${avg_all:,.2f}")
            print(f"平均资金(存活): ${avg_alive:,.2f}")
            print(f"ROI(全部): {(avg_all/10000-1)*100:+.2f}%")
            print(f"ROI(存活): {(avg_alive/10000-1)*100:+.2f}%")
        else:
            print("所有Agent已灭绝")
        
        # 保存JSON
        result_file = f"test_okx_live_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_data = {
            "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "steps": current_step,
            "total_trades": total_trades,
            "total_liquidations": total_liquidations,
            "survivors": len(alive),
            "avg_all": float(np.mean(all_capitals)) if all_capitals else 0,
            "roi_all": float((np.mean(all_capitals)/10000-1)*100) if all_capitals else -100,
        }
        
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        print(f"\n💾 结果已保存: {result_file}")
        print("=" * 80)

if __name__ == "__main__":
    main()

