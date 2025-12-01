"""
多市场交易系统配置
"""

import copy

# 多市场配置
CONFIG_MULTI_MARKET = {
    # 系统配置
    'initial_capital': 10000,  # 总初始资金
    'initial_agents': 3,
    
    # 市场配置
    'markets': {
        'spot': {
            'name': 'Spot',
            'fee_rate': 0.001,      # 0.10% (OKX现货Taker)
            'leverage': 1.0,        # 现货无杠杆
            'min_position': 0.0,    # 现货不能做空
            'max_position': 1.0
        },
        'futures': {
            'name': 'Futures',
            'fee_rate': 0.0005,     # 0.05% (OKX合约Taker)
            'leverage': 5.0,        # 阶段1：最高5倍杠杆
            'min_position': -1.0,   # 期货可以做空
            'max_position': 1.0
        }
    },
    
    # 资金分配策略
    'capital_allocation': {
        'mode': 'gene_controlled',  # 'fixed' or 'gene_controlled'
        'default_spot_ratio': 0.5,  # 默认50%现货
        'default_futures_ratio': 0.5  # 默认50%期货
    },
    
    # Agent管理配置
    'agent_manager': {
        'max_agents': 50,
        
        # 繁殖配置
        'reproduction': {
            'enabled': True,
            'min_roi': 0.03,        # 3% ROI才能繁殖
            'min_trades': 1,
            'mutation_rate': 0.1
        },
        
        # 死亡配置
        'death': {
            'enabled': True,
            'roi_threshold': -0.20,  # ROI < -20%死亡
            'max_inactive_days': 90  # 90天无交易死亡
        }
    },
    
    # 资金池配置
    'capital_manager': {
        'enabled': True,
        'pool_capital_ratio': 1.0  # 100%资金池
    },
    
    # 生命周期配置
    'lifecycle': {
        'hibernation': {
            'enabled': True,
            'fitness_threshold': 0.25,
            'wake_fitness_threshold': 0.60,
            'maintenance_cost_rate': 0.0002
        },
        'phoenix': {
            'enabled': True,
            'trigger_active_agents': 10,
            'trigger_system_roi': -0.70,
            'max_rebirths_per_trigger': 3
        }
    },
    
    # 市场状态配置（继承自v3.0）
    'market_regime': {
        'strong_bull': {'long': 0.90, 'short': 0.10},
        'weak_bull': {'long': 0.70, 'short': 0.30},
        'sideways': {'long': 0.50, 'short': 0.50},
        'weak_bear': {'long': 0.30, 'short': 0.70},
        'strong_bear': {'long': 0.10, 'short': 0.90}
    },
    
    # 策略配置
    'strategy': {
        'long_threshold': 0.2,
        'short_threshold': -0.2,
        'max_position': 1.0
    },
    
    # 风险管理
    'risk_management': {
        'futures_liquidation_threshold': -0.90,  # 期货爆仓阈值
        'margin_call_threshold': -0.70,          # 保证金预警阈值
        'max_leverage': 5.0                      # 阶段1最大杠杆
    }
}


def generate_multi_market_gene():
    """生成多市场基因"""
    import random
    
    gene = {
        # 策略权重（4个特征）
        'weights': [random.uniform(-1, 1) for _ in range(4)],
        
        # 资金分配基因
        'market_allocation': {
            'spot_ratio': random.uniform(0.3, 0.7),  # 30-70%现货
            'futures_ratio': None  # 自动计算为1-spot_ratio
        },
        
        # 杠杆基因（期货）
        'futures_leverage': random.uniform(1.0, 5.0),  # 1-5倍杠杆
        
        # 市场偏好基因
        'market_preference': {
            'spot_threshold_multiplier': random.uniform(0.8, 1.2),
            'futures_threshold_multiplier': random.uniform(0.8, 1.2)
        }
    }
    
    # 计算期货比例
    gene['market_allocation']['futures_ratio'] = 1.0 - gene['market_allocation']['spot_ratio']
    
    return gene


def mutate_multi_market_gene(gene: dict, mutation_rate: float = 0.1) -> dict:
    """变异多市场基因"""
    import random
    
    new_gene = copy.deepcopy(gene)
    
    # 变异策略权重
    for i in range(len(new_gene['weights'])):
        if random.random() < mutation_rate:
            new_gene['weights'][i] += random.uniform(-0.2, 0.2)
            new_gene['weights'][i] = max(-1, min(1, new_gene['weights'][i]))
    
    # 变异资金分配
    if random.random() < mutation_rate:
        new_gene['market_allocation']['spot_ratio'] += random.uniform(-0.1, 0.1)
        new_gene['market_allocation']['spot_ratio'] = max(0.3, min(0.7, 
            new_gene['market_allocation']['spot_ratio']))
        new_gene['market_allocation']['futures_ratio'] = 1.0 - new_gene['market_allocation']['spot_ratio']
    
    # 变异杠杆
    if random.random() < mutation_rate:
        new_gene['futures_leverage'] += random.uniform(-0.5, 0.5)
        new_gene['futures_leverage'] = max(1.0, min(5.0, new_gene['futures_leverage']))
    
    # 变异市场偏好
    for key in new_gene['market_preference']:
        if random.random() < mutation_rate:
            new_gene['market_preference'][key] += random.uniform(-0.1, 0.1)
            new_gene['market_preference'][key] = max(0.5, min(1.5, 
                new_gene['market_preference'][key]))
    
    return new_gene
