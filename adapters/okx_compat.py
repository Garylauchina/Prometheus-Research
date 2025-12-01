"""OKX包接口适配器

这个模块提供了直接从python-okx库导入所需模块的功能，
确保系统能够正确使用python-okx库的API。
"""

import logging
from okx import MarketData, Trade, Account

logger = logging.getLogger(__name__)

# 为python-okx 0.4.0版本添加MarketAPI类支持
# 确保MarketData模块包含MarketAPI类
if not hasattr(MarketData, 'MarketAPI'):
    MarketData.MarketAPI = MarketData.MarketDataAPI
    logger.info("为MarketData模块添加了MarketAPI类支持")

# 确保API类名称兼容性
if not hasattr(Trade, 'TradeAPI'):
    Trade.TradeAPI = Trade.TradeAPI
    logger.info("确保Trade模块包含TradeAPI类")

if not hasattr(Account, 'AccountAPI'):
    Account.AccountAPI = Account.AccountAPI
    logger.info("确保Account模块包含AccountAPI类")

# 导出所需模块
__all__ = ['MarketData', 'Trade', 'Account']

logger.info("OKX接口适配器初始化完成")
