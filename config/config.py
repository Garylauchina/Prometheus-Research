"""
Prometheus v4.0 配置管理
使用环境变量加载配置，提高安全性
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 交易模式配置
TRADING_MODE = os.getenv('TRADING_MODE', 'mock').lower()  # 默认使用模拟数据

# OKX API配置（从环境变量读取）
OKX_PAPER_TRADING = {
    'api_key': os.getenv('OKX_API_KEY'),
    'api_secret': os.getenv('OKX_API_SECRET'),
    'passphrase': os.getenv('OKX_PASSPHRASE'),
}

# 验证配置
def validate_config():
    """验证必要的环境变量是否已设置"""
    if TRADING_MODE not in ['mock', 'okx']:
        raise ValueError(
            f"TRADING_MODE 必须是 'mock' 或 'okx'，当前值: {TRADING_MODE}"
        )
    
    # 仅在OKX模式下验证API配置
    if TRADING_MODE == 'okx':
        required_keys = ['OKX_API_KEY', 'OKX_API_SECRET', 'OKX_PASSPHRASE']
        missing = [key for key in required_keys if not os.getenv(key)]
        
        if missing:
            raise ValueError(
                f"OKX模式需要以下环境变量: {', '.join(missing)}\n"
                f"请在 .env 文件中配置，或切换为 TRADING_MODE=mock"
            )
    
    return True

# 其他配置
OKX_SANDBOX = os.getenv('OKX_SANDBOX', 'True').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# 测试参数
TEST_CONFIG = {
    'symbol': 'BTC/USDT:USDT',
    'duration_minutes': 360,         # 6小时
    'check_interval': 20,            # 20秒
    'agent_count': 20,               # 20个Agent
    'position_size': 0.01,           # 最小0.01 BTC
    'consensus_threshold': 0.4,
    'support_ratio': 0.3,
}

