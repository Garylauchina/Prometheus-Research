"""
OKX API配置文件示例

使用方法：
1. 复制此文件为 okx_config.py
2. 填入您的OKX模拟盘API信息
3. 不要将 okx_config.py 提交到Git（已在.gitignore中）
"""

# OKX模拟盘API配置
OKX_PAPER_TRADING = {
    'api_key': 'a0caae06-0fab-4790-9ed3-bdddd2e0c09f',
    'api_secret': 'AC1A19FF1D64E9FDF15CA2B0A46E2656',
    'passphrase': 'Garylauchina3.14',
}

# 测试参数
TEST_CONFIG = {
    'symbol': 'BTC/USDT:USDT',      # 交易对（永续合约）
    'duration_minutes': 360,         # 测试时长（分钟）= 6小时 🌙
    'check_interval': 120,           # 检查间隔（秒）= 2分钟
    'agent_count': 10,               # Agent数量（10个创世Agent）
    'position_size': 0.01,           # 每次交易数量（BTC）OKX最小精度
    'consensus_threshold': 0.4,      # 共识阈值（已降低，更容易交易）
    'support_ratio': 0.3,            # 支持比例（已降低，更容易达成共识）
}

# OKX模拟盘说明
"""
1. 登录 OKX 官网: https://www.okx.com
2. 进入"交易"->"模拟交易"
3. 创建API密钥（需要启用交易权限）
4. 获取模拟盘充值（通常默认有10万USDT）
5. 将API信息填入上方配置

注意事项：
- 模拟盘API与实盘API完全隔离
- 模拟盘数据与实盘相同，但交易不会真实执行
- API密钥务必保密，不要泄露
"""

