"""
Market Data Manager for OKX API
"""

import logging
import time
from okx import MarketData
from .errors import APIError

logger = logging.getLogger(__name__)


class MarketDataManager:
    """市场数据管理器"""
    
    def __init__(self, config):
        """
        初始化
        
        Args:
            config: 配置字典
                - flag: '0'实盘, '1'模拟盘
        """
        self.config = config
        self.flag = config.get('flag', '1')
        self.rest_api = MarketData.MarketAPI(flag=self.flag)
        self.cache = {}
        
        logger.info(f"市场数据管理器初始化完成 (flag={self.flag})")
    
    def get_ticker(self, symbol):
        """
        获取Ticker
        
        Args:
            symbol: 交易对，如'BTC-USDT'
        
        Returns:
            float: 最新价格
        """
        try:
            result = self.rest_api.get_ticker(instId=symbol)
            
            if result['code'] == '0' and len(result['data']) > 0:
                price = float(result['data'][0]['last'])
                
                # 更新缓存
                self.cache[symbol] = {
                    'price': price,
                    'timestamp': time.time()
                }
                
                return price
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Failed to get ticker for {symbol}: {error_msg}")
                raise APIError(f"Failed to get ticker: {error_msg}")
        
        except Exception as e:
            logger.error(f"Exception in get_ticker for {symbol}: {e}")
            # 返回缓存价格
            cached = self.cache.get(symbol, {})
            if 'price' in cached:
                logger.warning(f"Using cached price for {symbol}: {cached['price']}")
                return cached['price']
            raise
    
    def get_candles(self, symbol, bar='1m', limit=100):
        """
        获取K线
        
        Args:
            symbol: 交易对
            bar: K线周期，如'1m', '5m', '1H', '1D'
            limit: 数量限制
        
        Returns:
            list: K线数据列表
        """
        try:
            result = self.rest_api.get_candlesticks(
                instId=symbol,
                bar=bar,
                limit=str(limit)
            )
            
            if result['code'] == '0':
                return result['data']
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Failed to get candles for {symbol}: {error_msg}")
                raise APIError(f"Failed to get candles: {error_msg}")
        
        except Exception as e:
            logger.error(f"Exception in get_candles for {symbol}: {e}")
            raise
    
    def get_market_data(self, symbol):
        """
        获取完整市场数据
        
        Args:
            symbol: 交易对
        
        Returns:
            dict: 市场数据
                - price: 当前价格
                - candles: K线数据
                - timestamp: 时间戳
        """
        try:
            price = self.get_ticker(symbol)
            candles = self.get_candles(symbol, bar='1m', limit=100)
            
            return {
                'price': price,
                'candles': candles,
                'timestamp': time.time()
            }
        
        except Exception as e:
            logger.error(f"Exception in get_market_data for {symbol}: {e}")
            raise
    
    def get_multiple_tickers(self, symbols):
        """
        批量获取Ticker
        
        Args:
            symbols: 交易对列表
        
        Returns:
            dict: {symbol: price}
        """
        result = {}
        for symbol in symbols:
            try:
                price = self.get_ticker(symbol)
                result[symbol] = price
            except Exception as e:
                logger.error(f"Failed to get ticker for {symbol}: {e}")
                # 继续处理其他symbol
                continue
        
        return result
