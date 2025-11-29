"""
Trading error classes
"""

class TradingError(Exception):
    """交易错误基类"""
    pass

class APIError(TradingError):
    """API错误"""
    pass

class RiskControlError(TradingError):
    """风控错误"""
    pass

class OrderError(TradingError):
    """订单错误"""
    pass

class NetworkError(TradingError):
    """网络错误"""
    pass
