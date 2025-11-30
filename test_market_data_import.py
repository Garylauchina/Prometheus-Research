import logging
from okx import MarketData

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_market_data():
    try:
        # 初始化MarketData API (使用模拟盘)
        logger.info("初始化MarketData API...")
        rest_api = MarketData.MarketAPI(flag='1')  # 1表示模拟盘
        
        # 尝试获取一个简单的行情数据
        logger.info("获取BTC-USDT行情...")
        result = rest_api.get_ticker(instId='BTC-USDT')
        
        logger.info(f"获取成功，返回码: {result.get('code')}")
        if result.get('code') == '0' and result.get('data'):
            logger.info(f"BTC-USDT最新价格: {result['data'][0]['last']}")
        else:
            logger.info(f"响应数据: {result}")
            
        logger.info("MarketData API测试成功!")
        return True
    except Exception as e:
        logger.error(f"MarketData API测试失败: {e}")
        return False

if __name__ == "__main__":
    test_market_data()
