"""
Config - 配置模块

职责: 定义系统配置
"""

# Prometheus v3.0 默认配置
CONFIG_V3 = {
    # 系统级配置
    'initial_capital': 10000,  # Round 9: 与v2.5公平对比
    'initial_agents': 3,  # 修改为3个初始Agent
    'trading_fee': 0.001,  # Round 10: OKX taker fee 0.1% (correct rate)
    
    # OKX API配置占位符
    'okx_api': {
        'api_key': '',  # 请在此处填入您的OKX API密钥
        'secret_key': '',  # 请在此处填入您的OKX API密钥
        'passphrase': '',  # 请在此处填入您的OKX API密钥
        'flag': 0  # 交易模式：0-实盘，1-模拟盘
    },
    
    # 智能体管理器配置
    'agent_manager': {
        'max_agents': 50,
        
        # 策略配置
        'strategy': {
            'long_threshold': 0.2,  # 做多阈值（优化：从0.3降低到0.2）
            'short_threshold': -0.2,  # 做空阈值（优化：从-0.3提高到-0.2）
            'max_position': 1.0,  # 最大单边仓位
            'max_leverage': 1.0,  # 最大总杠杆
        },
        
        # 死亡配置
        'death': {
            'death_roi_threshold': -0.20,  # ROI < -20% 死亡（优化：从-15%放宽）
            'max_inactive_days': 90,  # 90天不交易死亡（优化：从60天放宽）
        },
        
        # 繁殖配置
        'reproduction': {
            'min_roi': 0.03,  # 最小ROI（优化：从15%降低到3%）
            'min_trades': 1,  # 最小交易次数（优化：从5降低到1）
            'min_child_capital': 500,  # 子代最小资金
            'child_capital_ratio': 0.3,  # 从父代继承的比例
            'mutation_rate': 0.1,  # 变异率
            
            # 资金池配置
            'pool_capital_enabled': True,  # 是否从资金池获取额外资金
            'pool_capital_ratio': 1.0,  # 从资金池获取的比例（优化：从0.5增加到1.0）
        },
    },
    
    # 资金管理器配置
    'capital_manager': {
        'enabled': False,  # 默认禁用
        'reallocation_period': 90,  # 重新分配周期（天）
        'roi_weight': 0.7,  # ROI权重
        'frequency_weight': 0.3,  # 交易频率权重
        'min_capital_ratio': 0.01,  # 最小资金比例
    },
    
    # 市场分析器配置
    'market_analyzer': {
        'ma_short': 7,  # 短期均线
        'ma_long': 30,  # 长期均线
        'rsi_period': 14,  # RSI周期
        'volatility_window': 20,  # 波动率窗口
    }
}


# 激进配置 - 更高风险，更高收益
CONFIG_V3_AGGRESSIVE = {
    **CONFIG_V3,
    'agent_manager': {
        **CONFIG_V3['agent_manager'],
        'death': {
            'death_roi_threshold': -0.10,  # 更宽松的死亡阈值
            'max_inactive_days': 30,  # 更严格的活跃度要求
        },
        'reproduction': {
            **CONFIG_V3['agent_manager']['reproduction'],
            'min_roi': 0.10,  # 更低的繁殖阈值
            'pool_capital_ratio': 1.0,  # 从资金池获取更多资金
        },
    },
    'capital_manager': {
        **CONFIG_V3['capital_manager'],
        'enabled': True,  # 启用动态分配
        'reallocation_period': 60,  # 更频繁的重新分配
    }
}


# 保守配置 - 更低风险，更稳定
CONFIG_V3_CONSERVATIVE = {
    **CONFIG_V3,
    'agent_manager': {
        **CONFIG_V3['agent_manager'],
        'strategy': {
            'long_threshold': 0.4,  # 更高的交易阈值
            'short_threshold': -0.4,
            'max_position': 0.8,  # 更小的仓位
            'max_leverage': 0.8,
        },
        'death': {
            'death_roi_threshold': -0.20,  # 更宽松的死亡阈值
            'max_inactive_days': 90,  # 更宽松的活跃度要求
        },
        'reproduction': {
            **CONFIG_V3['agent_manager']['reproduction'],
            'min_roi': 0.20,  # 更高的繁殖阈值
            'min_trades': 10,  # 更多的交易次数要求
            'pool_capital_ratio': 0.3,  # 从资金池获取较少资金
        },
    },
}
