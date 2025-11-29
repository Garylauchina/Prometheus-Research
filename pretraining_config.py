"""
PreTraining Config - 预训练配置
"""

from .config import CONFIG_V3
import copy

# 预训练配置
PRETRAINING_CONFIG = {
    # 初始种群
    'initial_population': 1000,  # 初始随机基因数量（Round 4优化：从200增加到1000）
    'initial_capital_per_agent': 1000,
    
    # 训练场景
    'scenarios': [
        {
            'name': 'historical',
            'data': '/home/ubuntu/btc_daily_prices.json',
            'weight': 0.4,  # 权重
            'description': '历史数据 (8.3年)'
        },
        {
            'name': 'bull_market',
            'type': 'synthetic',
            'duration': 365,
            'trend': +0.9,  # +90%
            'volatility': 0.03,
            'weight': 0.2,
            'description': '极端牛市 (1年)'
        },
        {
            'name': 'bear_market',
            'type': 'synthetic',
            'duration': 365,
            'trend': -0.9,  # -90%
            'volatility': 0.03,
            'weight': 0.2,
            'description': '极端熊市 (1年)'
        },
        {
            'name': 'volatile',
            'type': 'synthetic',
            'duration': 365,
            'trend': 0.7,
            'volatility': 0.10,  # 高波动
            'weight': 0.2,
            'description': '极端震荡 (1年)'
        }
    ],
    
    # 筛选标准
    'selection': {
        'min_roi': 0.10,  # 最小ROI 10%
        'min_trades': 5,  # 最小交易次数
        'must_survive': True,  # 必须存活
        'top_n': 100,  # 选择Top 100（Round 4优化：从50增加到100）
        'diversity_threshold': 0.3,  # 多样性阈值
    },
    
    # 训练参数（宽松版，鼓励探索）
    'training_config': {
        # 系统配置
        'initial_capital': 0,  # 将被动态设置
        'initial_agents': 0,  # 手动初始化
        
        # 智能体管理器配置
        'agent_manager': copy.deepcopy(CONFIG_V3['agent_manager']),
        
        # 资金管理器配置
        'capital_manager': copy.deepcopy(CONFIG_V3['capital_manager']),
        
        # 市场分析器配置
        'market_analyzer': copy.deepcopy(CONFIG_V3['market_analyzer']),
    }
}

# 放宽训练配置
PRETRAINING_CONFIG['training_config']['agent_manager']['death_roi_threshold'] = -0.30  # 更宽松
PRETRAINING_CONFIG['training_config']['agent_manager']['max_inactive_days'] = 120  # 更宽松
PRETRAINING_CONFIG['training_config']['agent_manager']['reproduction']['min_roi'] = 0.10
PRETRAINING_CONFIG['training_config']['agent_manager']['reproduction']['min_trades'] = 3
