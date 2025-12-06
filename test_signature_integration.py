"""
WorldSignature集成测试

对比：
- 无WorldSignature的系统（原版）
- 有WorldSignature的系统（新版）

验证WorldSignature是否解决"单一生态适应"问题
"""

import numpy as np
import json
from datetime import datetime
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def simulate_price_series(env_params, days=365, start_price=50000):
    """模拟价格序列"""
    prices = [start_price]
    
    for _ in range(days - 1):
        drift = env_params['drift']
        vol = env_params['volatility']
        
        random_return = np.random.normal(drift, vol)
        new_price = prices[-1] * (1 + random_return)
        
        # 限制价格范围
        new_price = max(new_price, start_price * 0.1)
        new_price = min(new_price, start_price * 10)
        
        prices.append(new_price)
    
    return np.array(prices)


def run_baseline_backtest(prices, num_agents=50, initial_capital=500000):
    """
    基线回测（无WorldSignature）
    
    原始简单策略
    """
    agents_capital = np.ones(num_agents) * (initial_capital / num_agents)
    agents_position = np.zeros(num_agents)
    agents_alive = np.ones(num_agents, dtype=bool)
    
    for day, price in enumerate(prices[1:], 1):
        prev_price = prices[day - 1]
        
        for i in range(num_agents):
            if not agents_alive[i]:
                continue
            
            # 简单策略：基于短期趋势
            if day > 10:
                recent_trend = (prices[day] - prices[day-10]) / prices[day-10]
                
                if recent_trend > 0.05:
                    decision = np.random.choice(['hold', 'long'], p=[0.6, 0.4])
                elif recent_trend < -0.05:
                    decision = np.random.choice(['hold', 'short'], p=[0.6, 0.4])
                else:
                    decision = np.random.choice(['hold', 'long', 'short'], p=[0.7, 0.15, 0.15])
            else:
                decision = 'hold'
            
            # 执行决策
            if decision == 'long' and agents_position[i] == 0:
                agents_position[i] = agents_capital[i] * 0.1 / price
            elif decision == 'short' and agents_position[i] == 0:
                agents_position[i] = -agents_capital[i] * 0.1 / price
            elif decision == 'hold' and agents_position[i] != 0:
                pnl = agents_position[i] * (price - prev_price)
                agents_capital[i] += pnl
                agents_position[i] = 0
            
            if agents_position[i] != 0:
                unrealized_pnl = agents_position[i] * (price - prev_price)
                agents_capital[i] += unrealized_pnl
                
                if agents_capital[i] < initial_capital / num_agents * 0.1:
                    agents_alive[i] = False
                    agents_capital[i] = 0
                    agents_position[i] = 0
    
    survivors = np.sum(agents_alive)
    total_capital = np.sum(agents_capital)
    roi = (total_capital / initial_capital - 1) * 100
    
    return {
        'survivors': int(survivors),
        'total_capital': float(total_capital),
        'roi': float(roi)
    }


def run_signature_backtest(prices, num_agents=50, initial_capital=500000):
    """
    WorldSignature回测（新版）
    
    使用WorldSignature指导策略
    """
    from prometheus.adapters import create_regime_aware_backtest
    
    result = create_regime_aware_backtest(
        prices=prices,
        num_agents=num_agents,
        initial_capital=initial_capital
    )
    
    return result


def compare_systems(env_name: str, env_params: Dict, num_runs: int = 10):
    """
    对比两个系统在特定环境下的表现
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"🔬 测试环境: {env_name}")
    logger.info(f"   {env_params['description']}")
    logger.info(f"{'='*70}")
    
    baseline_results = []
    signature_results = []
    
    for run in range(num_runs):
        # 生成价格序列
        prices = simulate_price_series(env_params, days=365)
        market_roi = (prices[-1] / prices[0] - 1) * 100
        
        # 运行基线回测
        baseline = run_baseline_backtest(prices)
        baseline['market_roi'] = market_roi
        baseline_results.append(baseline)
        
        # 运行WorldSignature回测
        signature = run_signature_backtest(prices)
        signature['market_roi'] = market_roi
        signature_results.append(signature)
        
        if (run + 1) % 5 == 0:
            logger.info(f"  进度: {run+1}/{num_runs}")
    
    # 统计对比
    baseline_avg = np.mean([r['roi'] for r in baseline_results])
    signature_avg = np.mean([r['roi'] for r in signature_results])
    market_avg = np.mean([r['market_roi'] for r in baseline_results])
    
    improvement = signature_avg - baseline_avg
    
    logger.info(f"\n📊 结果对比:")
    logger.info(f"  市场ROI:      {market_avg:>8.1f}%")
    logger.info(f"  基线系统:     {baseline_avg:>8.1f}% (超额: {baseline_avg - market_avg:>+7.1f}%)")
    logger.info(f"  Signature系统: {signature_avg:>8.1f}% (超额: {signature_avg - market_avg:>+7.1f}%)")
    logger.info(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"  改进幅度:     {improvement:>+8.1f}%")
    
    if improvement > 5:
        logger.info(f"  ✅ WorldSignature显著改进表现！")
    elif improvement > 0:
        logger.info(f"  ✅ WorldSignature轻微改进表现")
    else:
        logger.info(f"  ⚠️  WorldSignature未改进表现")
    
    return {
        'env_name': env_name,
        'baseline_avg': baseline_avg,
        'signature_avg': signature_avg,
        'market_avg': market_avg,
        'improvement': improvement,
        'baseline_results': baseline_results,
        'signature_results': signature_results
    }


def main():
    """主函数"""
    logger.info("="*70)
    logger.info("🎯 WorldSignature集成效果验证")
    logger.info("="*70)
    logger.info("\n对比: 无Signature vs 有Signature")
    logger.info("目标: 验证WorldSignature是否解决'单一生态适应'问题")
    
    # 定义测试环境
    market_environments = {
        '强势牛市': {
            'drift': 0.002,
            'volatility': 0.02,
            'description': '持续上涨，低波动'
        },
        '暴跌熊市': {
            'drift': -0.003,
            'volatility': 0.05,
            'description': '持续下跌，高波动'
        },
        '高波震荡': {
            'drift': 0.0,
            'volatility': 0.06,
            'description': '无方向，剧烈波动'
        },
        '低波盘整': {
            'drift': 0.0001,
            'volatility': 0.01,
            'description': '无趋势，低波动'
        }
    }
    
    # 运行对比测试
    all_comparisons = {}
    
    for env_name, env_params in market_environments.items():
        comparison = compare_systems(env_name, env_params, num_runs=10)
        all_comparisons[env_name] = comparison
    
    # 综合分析
    logger.info(f"\n{'='*70}")
    logger.info("📊 综合对比 - WorldSignature的效果")
    logger.info(f"{'='*70}")
    
    logger.info(f"\n{'环境':<12} {'基线':<10} {'Signature':<10} {'市场':<10} {'改进':<10}")
    logger.info("-"*70)
    
    for env_name, comp in all_comparisons.items():
        logger.info(f"{env_name:<12} "
                   f"{comp['baseline_avg']:>8.1f}% "
                   f"{comp['signature_avg']:>8.1f}% "
                   f"{comp['market_avg']:>8.1f}% "
                   f"{comp['improvement']:>+8.1f}%")
    
    # 计算总体改进
    all_improvements = [c['improvement'] for c in all_comparisons.values()]
    avg_improvement = np.mean(all_improvements)
    min_improvement = np.min(all_improvements)
    max_improvement = np.max(all_improvements)
    
    logger.info(f"\n{'='*70}")
    logger.info("🎯 核心结论")
    logger.info(f"{'='*70}")
    logger.info(f"\nWorldSignature效果:")
    logger.info(f"  平均改进: {avg_improvement:+.1f}%")
    logger.info(f"  最小改进: {min_improvement:+.1f}%")
    logger.info(f"  最大改进: {max_improvement:+.1f}%")
    
    # 判断效果
    if avg_improvement > 10:
        logger.info(f"\n✅ WorldSignature显著提升系统表现！")
        logger.info(f"   朋友的建议：完全正确")
        logger.info(f"   '单一生态适应'问题：得到改善")
    elif avg_improvement > 0:
        logger.info(f"\n✅ WorldSignature有所改善")
        logger.info(f"   但还需要进一步优化")
    else:
        logger.info(f"\n⚠️  当前实现效果有限")
        logger.info(f"   需要改进策略调整逻辑")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 简化保存（避免numpy序列化问题）
    save_data = {}
    for env_name, comp in all_comparisons.items():
        save_data[env_name] = {
            'baseline_avg': comp['baseline_avg'],
            'signature_avg': comp['signature_avg'],
            'market_avg': comp['market_avg'],
            'improvement': comp['improvement']
        }
    
    with open(f'signature_integration_test_{timestamp}.json', 'w') as f:
        json.dump(save_data, f, indent=2)
    
    logger.info(f"\n✅ 结果已保存: signature_integration_test_{timestamp}.json")
    
    logger.info(f"\n{'='*70}")


if __name__ == "__main__":
    main()

