#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基因随机性增强测试脚本

此脚本用于验证LiveAgent类中基因参数生成的随机性增强效果，
包括不同概率分布（对数正态分布、正态分布、三角分布等）的应用效果，
以及生成基因的多样性指标分析。
"""

import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns
from collections import defaultdict

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入LiveAgent类，如无法导入则模拟其功能
try:
    from live_agent import LiveAgent
    LIVE_AGENT_AVAILABLE = True
except ImportError:
    print("警告: 无法导入LiveAgent类，使用模拟版本进行测试")
    LIVE_AGENT_AVAILABLE = False


class MockLiveAgent:
    """LiveAgent类的模拟版本，用于在无法导入真实类时进行测试"""
    
    def __init__(self, agent_id=None, initial_capital=10000.0, config=None, gene=None):
        self.agent_id = agent_id or f"mock_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.initial_capital = initial_capital
        self.config = config or {}
        self.gene = gene or self._generate_random_gene()
    
    def _generate_random_gene(self):
        """模拟LiveAgent中的_generate_random_gene方法，使用改进的分布"""
        import numpy as np
        
        # 使用对数正态分布生成的参数（更符合金融参数特性）
        long_threshold = np.random.lognormal(mean=-2.0, sigma=0.5)  # 范围约0.05-0.5
        short_threshold = np.random.lognormal(mean=-2.0, sigma=0.5)
        stop_loss = np.random.lognormal(mean=-3.0, sigma=0.6)  # 范围约0.01-0.3
        take_profit = np.random.lognormal(mean=-2.5, sigma=0.5)  # 范围约0.02-0.4
        holding_period = int(np.random.lognormal(mean=3.0, sigma=1.0)) + 1  # 范围约3-100
        
        # 使用三角分布生成的参数（有明确的最小值、最可能值和最大值）
        max_position = np.random.triangular(left=0.1, mode=0.3, right=0.8)  # 0.1-0.8，最可能0.3
        
        # 使用正态分布生成的参数（围绕均值分布，有正有负）
        risk_aversion = max(0.01, min(2.0, np.random.normal(loc=1.0, scale=0.5)))  # 0.01-2.0，均值1.0
        
        # 新增：波动率调整因子（正态分布）
        volatility_adjustment = max(0.5, min(2.0, np.random.normal(loc=1.0, scale=0.3)))  # 0.5-2.0，均值1.0
        
        # 新增：市场状态敏感度（对数正态分布）
        market_state_sensitivity = np.random.lognormal(mean=0.0, sigma=0.4)  # 范围约0.5-2.0
        
        # 新增：技术指标权重（均匀分布后归一化）
        weights = {
            'momentum': np.random.uniform(0.1, 1.0),
            'rsi': np.random.uniform(0.1, 1.0),
            'macd': np.random.uniform(0.1, 1.0),
            'bollinger': np.random.uniform(0.1, 1.0)
        }
        # 归一化权重使其总和为1
        total_weight = sum(weights.values())
        indicator_weights = {k: v / total_weight for k, v in weights.items()}
        
        return {
            'long_threshold': long_threshold,
            'short_threshold': short_threshold,
            'max_position': max_position,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'holding_period': holding_period,
            'risk_aversion': risk_aversion,
            'volatility_adjustment': volatility_adjustment,
            'market_state_sensitivity': market_state_sensitivity,
            'indicator_weights': indicator_weights
        }


def calculate_gene_distance(gene1, gene2):
    """
    计算两个基因之间的欧氏距离
    
    Args:
        gene1: 第一个基因字典
        gene2: 第二个基因字典
        
    Returns:
        float: 归一化的欧氏距离
    """
    # 提取主要参数作为特征向量
    features1 = []
    features2 = []
    
    # 主要参数
    main_params = ['long_threshold', 'short_threshold', 'max_position', 
                   'stop_loss', 'take_profit', 'holding_period', 'risk_aversion',
                   'volatility_adjustment', 'market_state_sensitivity']
    
    for param in main_params:
        if param in gene1 and param in gene2:
            val1 = gene1[param]
            val2 = gene2[param]
            
            # 对于不同参数进行适当的归一化
            if param == 'holding_period':
                # 对时间参数进行对数归一化
                val1 = np.log(val1 + 1)
                val2 = np.log(val2 + 1)
            elif param in ['long_threshold', 'short_threshold', 'stop_loss', 'take_profit']:
                # 对阈值参数进行缩放
                val1 *= 10
                val2 *= 10
            
            features1.append(val1)
            features2.append(val2)
    
    # 处理指标权重
    if 'indicator_weights' in gene1 and 'indicator_weights' in gene2:
        weights1 = gene1['indicator_weights']
        weights2 = gene2['indicator_weights']
        
        # 确保使用相同的顺序
        weight_keys = sorted(set(weights1.keys()).intersection(weights2.keys()))
        for key in weight_keys:
            features1.append(weights1[key])
            features2.append(weights2[key])
    
    if not features1 or not features2:
        return 0.0
    
    # 转换为numpy数组
    vec1 = np.array(features1)
    vec2 = np.array(features2)
    
    # 计算欧氏距离
    distance = np.linalg.norm(vec1 - vec2)
    
    # 归一化距离
    max_possible_distance = np.linalg.norm(np.ones_like(vec1) * 10)
    normalized_distance = min(1.0, distance / (max_possible_distance + 1e-10))
    
    return normalized_distance


def analyze_gene_distribution(genes, output_dir=None):
    """
    分析基因参数的分布特性
    
    Args:
        genes: 基因列表
        output_dir: 输出目录（用于保存图表）
    
    Returns:
        dict: 分布统计信息
    """
    # 创建输出目录
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 提取参数数据
    param_data = defaultdict(list)
    for gene in genes:
        # 处理主要参数
        for param in ['long_threshold', 'short_threshold', 'max_position', 
                      'stop_loss', 'take_profit', 'holding_period', 'risk_aversion',
                      'volatility_adjustment', 'market_state_sensitivity']:
            if param in gene:
                param_data[param].append(gene[param])
        
        # 处理指标权重
        if 'indicator_weights' in gene:
            for weight_name, weight_value in gene['indicator_weights'].items():
                param_data[f'weight_{weight_name}'].append(weight_value)
    
    # 计算统计信息
    from scipy import stats
    distribution_stats = {}
    for param, values in param_data.items():
        values_array = np.array(values)
        distribution_stats[param] = {
            'mean': np.mean(values_array),
            'std': np.std(values_array),
            'min': np.min(values_array),
            'max': np.max(values_array),
            'median': np.median(values_array),
            'skewness': stats.skew(values_array) if len(values_array) > 2 else 0,
            'kurtosis': stats.kurtosis(values_array) if len(values_array) > 3 else 0
        }
    
    # 绘制分布图
    if output_dir:
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # 主要参数分布图
        main_params = ['long_threshold', 'short_threshold', 'max_position', 
                      'stop_loss', 'take_profit', 'holding_period', 'risk_aversion',
                      'volatility_adjustment', 'market_state_sensitivity']
        
        # 创建主参数分布图
        n_cols = 3
        n_rows = (len(main_params) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
        axes = axes.flatten() if n_rows > 1 else [axes]
        
        for i, param in enumerate(main_params):
            if i < len(axes) and param in param_data:
                ax = axes[i]
                values = param_data[param]
                
                # 绘制直方图和KDE
                sns.histplot(values, kde=True, ax=ax, bins=30)
                ax.set_title(f'{param} 分布')
                ax.set_xlabel('值')
                ax.set_ylabel('频率')
                
                # 添加统计信息文本
                stats_text = (f'均值: {np.mean(values):.4f}\n'  
                             f'标准差: {np.std(values):.4f}\n'  
                             f'最小值: {np.min(values):.4f}\n'  
                             f'最大值: {np.max(values):.4f}')
                ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, 
                        verticalalignment='top', horizontalalignment='right',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 隐藏多余的子图
        for i in range(len(main_params), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'gene_params_distribution.png'), dpi=300)
        plt.close()
        
        # 指标权重分布图
        weight_params = [f'weight_{name}' for name in ['momentum', 'rsi', 'macd', 'bollinger']]
        
        if any(w in param_data for w in weight_params):
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()
            
            for i, param in enumerate(weight_params):
                if i < len(axes) and param in param_data:
                    ax = axes[i]
                    values = param_data[param]
                    
                    # 绘制直方图和KDE
                    sns.histplot(values, kde=True, ax=ax, bins=30)
                    ax.set_title(f'{param.replace("weight_", "")} 权重分布')
                    ax.set_xlabel('权重值')
                    ax.set_ylabel('频率')
                    
                    # 添加统计信息文本
                    stats_text = (f'均值: {np.mean(values):.4f}\n'  
                                 f'标准差: {np.std(values):.4f}')
                    ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, 
                            verticalalignment='top', horizontalalignment='right',
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'indicator_weights_distribution.png'), dpi=300)
            plt.close()
    
    return distribution_stats


def analyze_gene_diversity(genes, output_dir=None):
    """
    分析基因多样性
    
    Args:
        genes: 基因列表
        output_dir: 输出目录（用于保存图表）
    
    Returns:
        dict: 多样性统计信息
    """
    if len(genes) < 2:
        return {
            'error': '代理数量不足，无法计算多样性'
        }
    
    # 计算所有基因对之间的距离
    distances = []
    similarities = []
    
    for i in range(len(genes)):
        for j in range(i + 1, len(genes)):
            distance = calculate_gene_distance(genes[i], genes[j])
            distances.append(distance)
            similarities.append(1.0 - distance)  # 相似度 = 1 - 距离
    
    # 计算多样性统计信息
    diversity_stats = {
        'average_distance': np.mean(distances),
        'minimum_distance': np.min(distances),
        'maximum_distance': np.max(distances),
        'average_similarity': np.mean(similarities),
        'maximum_similarity': np.max(similarities),
        'distance_variance': np.var(distances),
        'total_pairs': len(distances),
        'agent_count': len(genes)
    }
    
    # 绘制距离分布图
    if output_dir:
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # 距离分布图
        plt.figure(figsize=(10, 6))
        sns.histplot(distances, kde=True, bins=50)
        plt.axvline(diversity_stats['average_distance'], color='red', linestyle='--', 
                   label=f'平均距离: {diversity_stats["average_distance"]:.4f}')
        plt.title('基因间距离分布')
        plt.xlabel('归一化欧氏距离')
        plt.ylabel('频率')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'gene_distance_distribution.png'), dpi=300)
        plt.close()
        
        # 相似度分布图
        plt.figure(figsize=(10, 6))
        sns.histplot(similarities, kde=True, bins=50)
        plt.axvline(diversity_stats['average_similarity'], color='red', linestyle='--', 
                   label=f'平均相似度: {diversity_stats["average_similarity"]:.4f}')
        plt.title('基因间相似度分布')
        plt.xlabel('相似度 (1-距离)')
        plt.ylabel('频率')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'gene_similarity_distribution.png'), dpi=300)
        plt.close()
    
    return diversity_stats


def run_simulation(agent_count=100, output_dir=None):
    """
    运行基因生成模拟并分析结果
    
    Args:
        agent_count: 生成的代理数量
        output_dir: 输出目录
    
    Returns:
        dict: 模拟结果
    """
    print(f"开始模拟，生成 {agent_count} 个代理...")
    
    # 生成基因
    genes = []
    for i in range(agent_count):
        if LIVE_AGENT_AVAILABLE:
            # 使用真实的LiveAgent类
            config = {}
            agent = LiveAgent(agent_id=f"test_agent_{i}", initial_capital=10000.0, config=config)
            genes.append(agent.gene)
        else:
            # 使用模拟的LiveAgent类
            agent = MockLiveAgent(agent_id=f"mock_agent_{i}")
            genes.append(agent.gene)
        
        if (i + 1) % 100 == 0:
            print(f"已生成 {i + 1}/{agent_count} 个代理...")
    
    # 分析参数分布
    print("\n分析基因参数分布...")
    distribution_stats = analyze_gene_distribution(genes, output_dir)
    
    # 分析基因多样性
    print("\n分析基因多样性...")
    diversity_stats = analyze_gene_diversity(genes, output_dir)
    
    # 输出结果摘要
    print("\n===== 结果摘要 =====")
    print(f"代理数量: {len(genes)}")
    print(f"基因多样性 - 平均距离: {diversity_stats['average_distance']:.4f}")
    print(f"基因多样性 - 最小距离: {diversity_stats['minimum_distance']:.4f}")
    print(f"基因多样性 - 最大相似度: {diversity_stats['maximum_similarity']:.4f}")
    
    # 将NumPy类型转换为Python原生类型
    def convert_numpy_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    # 保存结果到JSON文件
    if output_dir:
        results = {
            'timestamp': datetime.now().isoformat(),
            'agent_count': agent_count,
            'distribution_stats': distribution_stats,
            'diversity_stats': diversity_stats
        }
        
        # 转换结果中的NumPy类型
        serializable_results = convert_numpy_types(results)
        
        with open(os.path.join(output_dir, 'simulation_results.json'), 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到: {os.path.join(output_dir, 'simulation_results.json')}")
    
    return {
        'distribution_stats': distribution_stats,
        'diversity_stats': diversity_stats
    }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='基因随机性增强测试脚本')
    parser.add_argument('--agents', type=int, default=100, help='生成的代理数量')
    parser.add_argument('--output', type=str, default=None, help='输出目录')
    
    args = parser.parse_args()
    
    # 如果未指定输出目录，创建基于当前时间的目录
    if not args.output:
        args.output = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  f"gene_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    # 确保numpy和scipy已安装
    try:
        import numpy as np
        from scipy import stats
    except ImportError:
        print("错误: 需要安装numpy和scipy库")
        print("请运行: pip install numpy scipy matplotlib seaborn")
        return 1
    
    # 运行模拟
    run_simulation(agent_count=args.agents, output_dir=args.output)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
