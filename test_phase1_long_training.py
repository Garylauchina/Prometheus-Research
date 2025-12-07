#!/usr/bin/env python3
"""
Phase 1: 长期训练测试
====================================

目标: 验证AlphaZero式系统在长期训练下能否自然涌现盈利策略

配置:
- Seed: 8004 (Phase 0最佳)
- 周期: 500
- 观测点: 每100周期
- Agent: 50
- 全参数解锁: True

判断标准:
✅ 收益曲线上升 → AlphaZero有效
⚠️ 收益平坦但交易增加 → 需要更多训练
❌ 收益下降且交易不变 → 需要调参
"""

import logging
from pathlib import Path
from datetime import datetime
import json
import pandas as pd

from prometheus.facade.v6_facade import run_scenario

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_phase1():
    """
    Phase 1: 长期训练单个最佳种子
    """
    logger.info("=" * 80)
    logger.info("🚀 Phase 1: 长期训练测试开始")
    logger.info("=" * 80)
    logger.info("配置:")
    logger.info("  - Seed: 8004 (Phase 0最佳)")
    logger.info("  - 周期: 500")
    logger.info("  - 观测点: 每100周期")
    logger.info("  - 预计时间: 10-30分钟")
    logger.info("")
    
    # 加载历史数据
    logger.info("📊 加载历史数据...")
    try:
        df_btc = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
        if df_btc.empty:
            logger.error("❌ 数据文件为空")
            return None
        logger.info(f"✅ 数据加载成功: {len(df_btc)} 条记录")
    except FileNotFoundError:
        logger.error("❌ 数据文件不存在: data/okx/BTC_USDT_1d_20251206.csv")
        logger.error("💡 请先下载数据: python3 tools/download_okx_data.py")
        return None
    except Exception as e:
        logger.error(f"❌ 数据加载失败: {e}")
        return None
    
    logger.info("")
    
    # Phase 1配置
    seed = 8004
    total_cycles = 500
    agent_count = 50
    num_families = 50
    
    # 构造market_feed函数（与Phase 0保持一致）
    prices = df_btc['close'].tolist()
    def make_market_feed():
        def feed(cycle):
            idx = min(cycle - 1, len(prices) - 1)
            return {'price': prices[idx]}, {}
        return feed
    
    logger.info(f"🧪 开始训练 (Seed: {seed})")
    logger.info("=" * 80)
    
    # 运行场景
    try:
        result = run_scenario(
            mode="backtest",
            total_cycles=total_cycles,
            market_feed=make_market_feed(),
            
            # 种群配置
            num_families=num_families,
            agent_count=agent_count,
            capital_per_agent=10000.0,
            
            # 进化配置
            evo_interval=10,  # 每10个周期进化一次
            
            # 随机种子
            seed=seed,
            evolution_seed=None,  # 演化随机
            
            # AlphaZero式配置
            full_genome_unlock=True  # 全参数解锁
        )
        
        # 获取最终状态
        facade = result
        moirai = facade.moirai
        
        # 统计（使用state判断存活）
        from prometheus.core.agent_v5 import AgentState
        alive_agents = len([a for a in moirai.agents if a.state != AgentState.DEAD])
        total_trades = sum(len(a.account.private_ledger.trade_history) 
                         for a in moirai.agents if hasattr(a, 'account') and a.account)
        
        # 计算系统收益
        agent_count_final = len(moirai.agents)
        system_initial = agent_count_final * 10000.0
        current_price = prices[min(total_cycles - 1, len(prices) - 1)]
        system_current = sum(
            a.account.private_ledger.virtual_capital + a.calculate_unrealized_pnl(current_price)
            for a in moirai.agents if hasattr(a, 'account') and a.account
        )
        system_return = (system_current - system_initial) / system_initial * 100
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"✅ 训练完成 (Seed: {seed})")
        logger.info("=" * 80)
        logger.info(f"   存活Agent: {alive_agents}/{agent_count_final}")
        logger.info(f"   总交易数: {total_trades}")
        logger.info(f"   系统收益: {system_return:+.2f}%")
        logger.info(f"   人均交易: {total_trades/agent_count_final:.1f}笔" if agent_count_final > 0 else "   人均交易: 0.0笔")
        logger.info("")
        
        # 保存结果
        result_data = {
            "config": {
                "seed": seed,
                "cycles": total_cycles,
                "agent_count": agent_count,
                "full_genome_unlock": True
            },
            "result": {
                "alive_agents": alive_agents,
                "total_agents": agent_count_final,
                "total_trades": total_trades,
                "system_return": system_return,
                "avg_trades_per_agent": total_trades / agent_count_final if agent_count_final > 0 else 0,
                "status": "success"
            }
        }
        
        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = Path(f"results/phase1_training_{timestamp}.json")
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        logger.info(f"💾 结果已保存: {result_file}")
        logger.info("")
        
        # 判断结果
        logger.info("=" * 80)
        logger.info("🎯 结果判定")
        logger.info("=" * 80)
        
        if system_return > 0:
            logger.info(f"🎉 AlphaZero成功！系统盈利 {system_return:+.2f}%")
            logger.info("✅ 可以进入Phase 2（多种子大规模训练）")
        elif system_return > -1 and total_trades > 50:
            logger.info(f"⚠️ 系统轻微亏损 {system_return:+.2f}%，但交易活跃")
            logger.info("💡 建议: 继续训练更多周期 (1000+)")
        else:
            logger.info(f"❌ 系统亏损 {system_return:+.2f}%")
            logger.info("🛠️ 建议: 需要调整参数或Fitness函数")
        
        logger.info("")
        
        return result_data
        
    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    run_phase1()

