"""
Virtual Trading Configuration for Prometheus v3.0
"""
import os

CONFIG_VIRTUAL_TRADING = {
    # 基础配置
    'initial_capital': 5000,  # $5,000 USDT
    'initial_agents': 5,      # 5个初始agent
    'max_agents': 10,         # 最多10个agent
    
    # 市场配置
    'markets': {
        'spot': {
            'enabled': True,
            'symbol': 'BTC-USDT',
            'fee_rate': 0.001,  # 0.10%
            'allocation': 0.5,   # 50%资金
            'min_order_size': 0.0001  # 最小0.0001 BTC
        },
        'futures': {
            'enabled': True,
            'symbol': 'BTC-USDT-SWAP',
            'fee_rate': 0.0005,  # 0.05%
            'allocation': 0.5,   # 50%资金
            'max_leverage': 3,   # 最高3倍杠杆
            'min_order_size': 1  # 最小1张合约
        }
    },
    
    # Agent配置
    'agent_manager': {
        'reproduction': {
            'enabled': True,
            'min_roi': 0.05,     # 5% ROI可繁殖
            'min_trades': 3,     # 至少3笔交易
            'cost_ratio': 0.1    # 繁殖成本10%
        },
        'death': {
            'roi_threshold': -0.20,      # 亏损20%死亡
            'max_inactive_days': 7,      # 7天不交易死亡
            'check_interval': 3600       # 每小时检查一次
        }
    },
    
    # 资金池
    'capital_manager': {
        'enabled': True,
        'pool_ratio': 0.3,  # 30%资金进入资金池
        'min_agent_capital': 100  # 每个agent最少$100
    },
    
    # 策略配置
    'strategy': {
        'long_threshold': 0.2,   # 做多阈值
        'short_threshold': -0.2, # 做空阈值
        'max_position': 1.0,     # 最大仓位
        'max_leverage': 1.0      # 最大杠杆（agent级别）
    },
    
    # 市场状态配置
    'market_regime': {
        'enabled': True,
        'lookback_days': 30,
        'regimes': {
            'strong_bull': {'long': 0.90, 'short': 0.10},
            'weak_bull': {'long': 0.70, 'short': 0.30},
            'sideways': {'long': 0.50, 'short': 0.50},
            'weak_bear': {'long': 0.30, 'short': 0.70},
            'strong_bear': {'long': 0.10, 'short': 0.90}
        }
    },
    
    # 风险控制
    'risk': {
        'max_daily_trades': 100,      # 每日最多100笔
        'max_daily_loss': 0.10,       # 每日最大亏损10%
        'max_leverage': 3,            # 最高3倍杠杆
        'max_position_pct': 0.30,     # 单个仓位最多30%
        'stop_loss_pct': 0.05,        # 止损5%
        'max_order_value': 500        # 单笔订单最大$500
    },
    
    # 交易循环
    'trading': {
        'update_interval': 60,  # 60秒更新一次
        'order_timeout': 300,   # 订单超时5分钟
        'retry_attempts': 3,    # 重试3次
        'retry_delay': 5        # 重试延迟5秒
    },
    
    # 日志配置
    'logging': {
        'level': 'INFO',
        'dir': 'logs',  # 使用相对路径，将在项目根目录下创建logs文件夹
        'file_prefix': 'prometheus',
        'max_size_mb': 100,
        'backup_count': 10
    },
    
    # OKX API配置
    'okx_api': {
        'api_key': '265a4c37-1dc1-40d8-80d0-11004026ca48',  # OKX API密钥
        'secret_key': '0AD30E01A7B66FBBBEB7E30D8E0E18B4',  # OKX Secret Key
        'passphrase': 'Garylauchina3.14',  # OKX密码
        'flag': '1'  # 1=模拟盘，0=实盘
    }
}
