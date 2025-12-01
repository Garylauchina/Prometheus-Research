"""OKX包接口适配器

这个模块提供了从python-okx库直接导入所需模块的功能。
"""

import logging
from okx import MarketData, Trade, Account

logger = logging.getLogger(__name__)

# 确保API类名称兼容性
# 为MarketData模块添加MarketAPI别名支持
if not hasattr(MarketData, 'MarketAPI'):
    MarketData.MarketAPI = MarketData.MarketDataAPI
    logger.info("为MarketData模块添加了MarketAPI类支持")

# 导出所需模块
__all__ = ['MarketData', 'Trade', 'Account']

logger.info("OKX接口适配器初始化完成")
