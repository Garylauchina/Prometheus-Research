"""
Market Data Manager for OKX API
"""

import logging
import time
import ssl
import socket
from functools import wraps
# 使用兼容性模块来解决导入问题
from .okx_compat import MarketData
from .errors import APIError

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries=3, backoff_factor=0.5, retry_exceptions=(socket.timeout, ssl.SSLError, APIError)):
    """
    重试装饰器，用于处理网络错误和API错误，增强版：特别优化了对SSL握手超时的处理
    
    Args:
        max_retries: 最大重试次数
        backoff_factor: 退避因子，用于计算重试间隔
        retry_exceptions: 需要重试的异常类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            retries = 0
            last_exception = None
            ssl_handshake_errors = 0
            max_wait_time = 10  # 最大等待时间限制，避免过长的等待
            
            while retries <= max_retries:
                try:
                    # 如果是SSL错误后的重试，可以记录此次尝试
                    if ssl_handshake_errors > 0:
                        logger.info(f"SSL错误后的重试尝试 ({retries}/{max_retries})")
                    
                    return func(self, *args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    error_str = str(e)
                    
                    # 判断错误类型并统计SSL握手超时
                    is_ssl_handshake_timeout = isinstance(e, ssl.SSLError) and "handshake operation timed out" in error_str
                    is_connection_timeout = isinstance(e, socket.timeout)
                    is_ssl_error = isinstance(e, ssl.SSLError)
                    
                    if is_ssl_handshake_timeout:
                        error_type = "SSL握手超时"
                        ssl_handshake_errors += 1
                        # 记录SSL握手错误详情
                        logger.error(f"{error_type} - 方法: {func.__name__}, 参数: {args[:1]}, 错误码: {getattr(e, 'errno', 'N/A')}")
                    elif is_connection_timeout:
                        error_type = "连接超时"
                        logger.error(f"{error_type} - 方法: {func.__name__}, 参数: {args[:1]}")
                    else:
                        error_type = "API错误"
                        logger.error(f"{error_type} - {e}")
                    
                    # 更新健康状态
                    if hasattr(self, 'update_health_status'):
                        self.update_health_status(False, error_str)
                    elif hasattr(self, 'health_status'):
                        self.health_status['is_healthy'] = False
                        self.health_status['last_error'] = error_str
                        self.health_status['consecutive_failures'] = self.health_status.get('consecutive_failures', 0) + 1
                    
                    if retries < max_retries:
                        # 根据错误类型采用不同的退避策略
                        if is_ssl_handshake_timeout:
                            # SSL握手超时使用更激进的退避策略
                            # 第一次SSL握手错误就使用较长的等待时间
                            wait_time = backoff_factor * (2 ** (retries + 1))
                            logger.warning(f"{error_type}，采用增强退避策略，正在重试 ({retries + 1}/{max_retries})，等待 {wait_time:.2f}秒...")
                            
                            # 立即尝试重置连接（如果有此方法）
                            if hasattr(self, 'reset_connection'):
                                try:
                                    logger.info("SSL握手超时，尝试立即重置连接...")
                                    self.reset_connection()
                                    logger.info("连接重置完成")
                                except Exception as reset_error:
                                    logger.error(f"重置连接失败: {reset_error}")
                        else:
                            # 普通错误使用标准退避策略
                            wait_time = backoff_factor * (2 ** retries)
                            logger.warning(f"{error_type}，正在重试 ({retries + 1}/{max_retries})，等待 {wait_time:.2f}秒...")
                        
                        # 限制最大等待时间
                        wait_time = min(wait_time, max_wait_time)
                        
                        # 更新重试计数
                        retries += 1
                        
                        # 执行等待
                        time.sleep(wait_time)
                    else:
                        logger.error(f"达到最大重试次数 {max_retries}，操作失败: {e}")
                        
                        # 最终失败前再次尝试重置连接（如果是SSL错误）
                        if is_ssl_error and hasattr(self, 'reset_connection'):
                            try:
                                logger.info("最后重试失败，尝试最终连接重置...")
                                self.reset_connection()
                            except Exception as reset_error:
                                logger.error(f"最终重置连接失败: {reset_error}")
                        
                        break
            
            # 重试失败后，尝试使用缓存数据（扩展到更多方法）
            if hasattr(self, 'cache') and args:
                symbol = args[0]
                cached = self.cache.get(symbol, {})
                
                # 扩展缓存使用到多个方法
                if func.__name__ == 'get_ticker' and 'price' in cached:
                    cache_age = time.time() - cached.get('timestamp', 0)
                    logger.warning(f"使用缓存价格 (缓存时间: {cache_age:.1f}秒): {symbol} = {cached['price']}")
                    # 更新缓存时间戳，表示我们刚刚使用了这个缓存
                    cached['last_used'] = time.time()
                    return cached['price']
                elif func.__name__ == 'get_candles' and 'candles' in cached:
                    cache_age = time.time() - cached.get('timestamp', 0)
                    logger.warning(f"使用缓存K线数据 (缓存时间: {cache_age:.1f}秒): {symbol}")
                    cached['last_used'] = time.time()
                    return cached['candles']
            
            # 如果没有可用缓存或不支持缓存，重新抛出最后一个异常
            raise last_exception
        return wrapper
    return decorator


class MarketDataManager:
    """市场数据管理器"""
    
    def __init__(self, config):
        """
        初始化
        
        Args:
            config: 配置字典
                - flag: '0'实盘, '1'模拟盘
                - timeout: 请求超时时间（秒）
                - max_retries: 最大重试次数
                - backoff_factor: 退避因子
        """
        self.config = config
        self.flag = config.get('flag', '1')
        self.timeout = config.get('timeout', 10)  # 默认超时时间10秒
        self.max_retries = config.get('max_retries', 3)
        self.backoff_factor = config.get('backoff_factor', 0.5)
        
        # In okx v0.4.0, MarketData is a module that contains MarketAPI class
        self.rest_api = MarketData.MarketAPI(flag=self.flag)
        
        # 增强的缓存系统
        self.cache = {}
        self.cache_max_age = config.get('cache_max_age', 300)  # 缓存最大有效期5分钟
        
        # 连接状态监控
        self.health_status = {
            'last_success': time.time(),
            'consecutive_failures': 0,
            'last_error': None
        }
        
        logger.info(f"市场数据管理器初始化完成 (flag={self.flag}, timeout={self.timeout}s, max_retries={self.max_retries})")
    
    @retry_with_backoff(max_retries=3, backoff_factor=0.5)
    def get_ticker(self, symbol):
        """
        获取Ticker
        
        Args:
            symbol: 交易对，如'BTC-USDT'
        
        Returns:
            float: 最新价格
        """
        # 先检查缓存是否在有效期内
        cached = self.cache.get(symbol, {})
        current_time = time.time()
        cache_age = current_time - cached.get('timestamp', 0)
        
        # 如果缓存较新（3秒内），直接返回缓存
        if 'price' in cached and cache_age < 3:
            return cached['price']
        
        try:
            # 设置请求超时
            # 注意：这里假设MarketData.MarketAPI支持timeout参数
            # 如果不支持，可能需要修改okx_compat模块
            result = self.rest_api.get_ticker(instId=symbol)
            
            if result['code'] == '0' and len(result['data']) > 0:
                price = float(result['data'][0]['last'])
                
                # 更新缓存
                self.cache[symbol] = {
                    'price': price,
                    'timestamp': current_time,
                    'last_used': current_time
                }
                
                # 更新健康状态
                self.health_status['last_success'] = current_time
                self.health_status['consecutive_failures'] = 0
                self.health_status['last_error'] = None
                
                return price
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Failed to get ticker for {symbol}: {error_msg}")
                # 更新失败次数
                self._update_health_status(False, error_msg)
                raise APIError(f"Failed to get ticker: {error_msg}")
        
        except Exception as e:
            logger.error(f"Exception in get_ticker for {symbol}: {e}")
            # 更新失败状态
            self._update_health_status(False, str(e))
            
            # 尝试返回缓存价格（即使过期）
            if 'price' in cached:
                logger.warning(f"使用缓存价格 (缓存时间: {cache_age:.1f}秒): {symbol} = {cached['price']}")
                # 更新最后使用时间
                cached['last_used'] = current_time
                return cached['price']
            raise
    
    @retry_with_backoff(max_retries=3, backoff_factor=0.5)
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
            # 为K线数据也添加缓存
            cache_key = f"{symbol}_{bar}_{limit}"
            cached = self.cache.get(cache_key, {})
            current_time = time.time()
            cache_age = current_time - cached.get('timestamp', 0)
            
            # K线数据缓存时间较短（10秒）
            if 'data' in cached and cache_age < 10:
                return cached['data']
            
            result = self.rest_api.get_candlesticks(
                instId=symbol,
                bar=bar,
                limit=str(limit)
            )
            
            if result['code'] == '0':
                # 更新缓存
                self.cache[cache_key] = {
                    'data': result['data'],
                    'timestamp': current_time
                }
                
                # 更新健康状态
                self.health_status['last_success'] = current_time
                self.health_status['consecutive_failures'] = 0
                self.health_status['last_error'] = None
                
                return result['data']
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Failed to get candles for {symbol}: {error_msg}")
                # 更新失败次数
                self._update_health_status(False, error_msg)
                raise APIError(f"Failed to get candles: {error_msg}")
        
        except Exception as e:
            logger.error(f"Exception in get_candles for {symbol}: {e}")
            # 更新失败状态
            self._update_health_status(False, str(e))
            
            # 尝试返回缓存的K线数据（即使过期）
            cache_key = f"{symbol}_{bar}_{limit}"
            cached = self.cache.get(cache_key, {})
            if 'data' in cached:
                logger.warning(f"使用缓存的K线数据: {symbol}_{bar}")
                return cached['data']
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
                - from_cache: 数据是否来自缓存
        """
        try:
            from_cache = False
            
            # 分别获取价格和K线，它们各自有自己的重试和缓存逻辑
            price = self.get_ticker(symbol)
            candles = self.get_candles(symbol, bar='1m', limit=100)
            
            # 检查是否使用了过期缓存
            cached_price = self.cache.get(symbol, {})
            cached_candles = self.cache.get(f"{symbol}_1m_100", {})
            cache_age_price = time.time() - cached_price.get('timestamp', 0) if 'timestamp' in cached_price else float('inf')
            cache_age_candles = time.time() - cached_candles.get('timestamp', 0) if 'timestamp' in cached_candles else float('inf')
            
            # 如果任一数据来自过期缓存，则标记为来自缓存
            if cache_age_price > 3 or cache_age_candles > 10:
                from_cache = True
                logger.info(f"市场数据部分使用缓存: {symbol}")
            
            return {
                'price': price,
                'candles': candles,
                'timestamp': time.time(),
                'from_cache': from_cache
            }
        
        except Exception as e:
            logger.error(f"Exception in get_market_data for {symbol}: {e}")
            # 尝试返回可用的部分数据
            partial_data = {'timestamp': time.time(), 'from_cache': True}
            
            # 尝试获取缓存的价格
            cached_price = self.cache.get(symbol, {})
            if 'price' in cached_price:
                partial_data['price'] = cached_price['price']
            
            # 尝试获取缓存的K线
            cached_candles = self.cache.get(f"{symbol}_1m_100", {})
            if 'data' in cached_candles:
                partial_data['candles'] = cached_candles['data']
            
            # 如果有部分数据，返回它
            if partial_data.get('price') or partial_data.get('candles'):
                logger.warning(f"返回部分缓存数据: {symbol}")
                return partial_data
            
            # 如果没有任何缓存数据，抛出异常
            raise
    
    def get_multiple_tickers(self, symbols):
        """
        批量获取Ticker
        
        Args:
            symbols: 交易对列表
        
        Returns:
            dict: {symbol: price}
            dict: {symbol: error_msg} - 失败的请求
        """
        result = {}
        failed = {}
        
        # 先检查所有缓存
        for symbol in symbols:
            cached = self.cache.get(symbol, {})
            current_time = time.time()
            cache_age = current_time - cached.get('timestamp', 0)
            
            # 对于批量请求，可以使用稍旧的缓存（10秒内）直接返回
            if 'price' in cached and cache_age < 10:
                result[symbol] = cached['price']
                cached['last_used'] = current_time
        
        # 只对没有缓存或缓存过期的symbol发起请求
        symbols_to_fetch = [s for s in symbols if s not in result]
        
        # 为避免频繁请求，添加适当的延迟
        if symbols_to_fetch:
            logger.info(f"批量获取 {len(symbols_to_fetch)} 个交易对的价格")
        
        for i, symbol in enumerate(symbols_to_fetch):
            # 在请求之间添加小延迟，避免触发API限流
            if i > 0:
                time.sleep(0.1)  # 100ms延迟
                
            try:
                price = self.get_ticker(symbol)
                result[symbol] = price
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to get ticker for {symbol}: {error_msg}")
                failed[symbol] = error_msg
                
                # 尝试使用过期缓存
                cached = self.cache.get(symbol, {})
                if 'price' in cached:
                    logger.warning(f"使用过期缓存价格: {symbol} = {cached['price']}")
                    result[symbol] = cached['price']
                    cached['last_used'] = time.time()
        
        # 如果有失败的请求，记录日志
        if failed:
            logger.warning(f"批量获取价格完成，但有 {len(failed)} 个失败")
        
        return result, failed
    
    def _update_health_status(self, success, error_msg=None):
        """
        更新健康状态
        
        Args:
            success: 请求是否成功
            error_msg: 错误信息（如果失败）
        """
        current_time = time.time()
        if success:
            self.health_status['last_success'] = current_time
            self.health_status['consecutive_failures'] = 0
            self.health_status['last_error'] = None
        else:
            self.health_status['consecutive_failures'] += 1
            self.health_status['last_error'] = error_msg
    
    def get_health_status(self):
        """
        获取健康状态
        
        Returns:
            dict: 健康状态信息
        """
        current_time = time.time()
        last_success_age = current_time - self.health_status['last_success']
        
        # 判断是否健康（最近30秒内有成功请求且连续失败次数小于3）
        is_healthy = last_success_age < 30 and self.health_status['consecutive_failures'] < 3
        
        return {
            'is_healthy': is_healthy,
            'last_success': self.health_status['last_success'],
            'last_success_age': last_success_age,
            'consecutive_failures': self.health_status['consecutive_failures'],
            'last_error': self.health_status['last_error']
        }
    
    def cleanup_cache(self):
        """
        清理过期缓存，避免内存泄漏
        """
        current_time = time.time()
        expired_keys = []
        
        for key, value in self.cache.items():
            cache_age = current_time - value.get('timestamp', 0)
            # 清理过期的缓存项
            if cache_age > self.cache_max_age:
                expired_keys.append(key)
        
        if expired_keys:
            for key in expired_keys:
                del self.cache[key]
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    def set_timeout(self, timeout):
        """
        动态设置超时时间
        
        Args:
            timeout: 新的超时时间（秒）
        """
        self.timeout = timeout
        logger.info(f"更新请求超时时间: {timeout}秒")
    
    def reset_connection(self):
        """
        重置API连接，可能有助于解决持续的连接问题
        """
        logger.warning("正在重置API连接...")
        try:
            # 创建新的API实例
            self.rest_api = MarketData.MarketAPI(flag=self.flag)
            logger.info("API连接重置成功")
            # 重置健康状态
            self.health_status = {
                'last_success': time.time(),
                'consecutive_failures': 0,
                'last_error': None
            }
        except Exception as e:
            logger.error(f"API连接重置失败: {e}")
            raise
