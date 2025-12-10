"""
MarketDataInterface - v8.0市场数据接口⭐⭐⭐

职责：
  • 为Prophet提供统一的市场数据获取接口
  • 支持实盘、回测、模拟三种模式
  • 屏蔽底层数据源差异

设计理念：
  • v7.0 Prophet只依赖这个接口
  • v8.0可以轻松切换数据源
  • 不侵入v7.0代码

Created: 2025-12-11
Author: Prometheus Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketSnapshot:
    """
    市场快照数据结构⭐
    
    标准化的市场数据，供Prophet使用
    """
    # 基础数据
    timestamp: datetime
    symbol: str
    price: float
    
    # 价格变化
    price_change: float          # 单周期变化
    price_change_24h: float      # 24小时变化
    
    # 波动率
    volatility: float            # 当前波动率
    volatility_24h: float        # 24小时波动率
    volatility_change: float     # 波动率变化
    
    # 成交量
    volume: float                # 当前成交量
    volume_24h: float            # 24小时成交量
    volume_ratio: float          # 成交量比率
    volume_change: float         # 成交量变化
    
    # 市场深度（可选）
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    bid_volume: Optional[float] = None
    ask_volume: Optional[float] = None
    
    # 扩展数据（可选）
    extras: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（兼容v7.0的world_signature格式）"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'price': self.price,
            'price_change': self.price_change,
            'price_change_24h': self.price_change_24h,
            'volatility': self.volatility,
            'volatility_24h': self.volatility_24h,
            'volatility_change': self.volatility_change,
            'volume': self.volume,
            'volume_24h': self.volume_24h,
            'volume_ratio': self.volume_ratio,
            'volume_change': self.volume_change,
        }


class MarketDataInterface(ABC):
    """
    市场数据接口（抽象基类）⭐⭐⭐
    
    v7.0 Prophet通过这个接口获取市场数据
    v8.0提供多种实现：实盘、回测、模拟
    """
    
    @abstractmethod
    def get_current_snapshot(self) -> MarketSnapshot:
        """
        获取当前市场快照⭐
        
        Returns:
            MarketSnapshot: 标准化的市场数据
        """
        pass
    
    @abstractmethod
    def get_historical_snapshots(
        self, 
        start_time: datetime, 
        end_time: datetime,
        interval: str = '5m'
    ) -> List[MarketSnapshot]:
        """
        获取历史市场快照（用于回测）
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            interval: 时间间隔（'1m', '5m', '15m', '1h'等）
        
        Returns:
            List[MarketSnapshot]: 历史快照列表
        """
        pass
    
    @abstractmethod
    def is_market_open(self) -> bool:
        """
        市场是否开放⭐
        
        Returns:
            bool: True=开放，False=关闭
        """
        pass
    
    @abstractmethod
    def get_market_status(self) -> Dict[str, Any]:
        """
        获取市场状态
        
        Returns:
            Dict: 市场状态信息（包括开盘时间、休市通知等）
        """
        pass


class LiveMarketData(MarketDataInterface):
    """
    实盘市场数据⭐
    
    从交易所API获取实时数据
    """
    
    def __init__(self, exchange: str, symbol: str, api_key: str = None):
        """
        Args:
            exchange: 交易所名称（'okx', 'binance'等）
            symbol: 交易对（'BTC-USDT'等）
            api_key: API密钥（可选）
        """
        self.exchange = exchange
        self.symbol = symbol
        self.api_key = api_key
        
        # TODO: 初始化交易所连接
        logger.info(f"📡 LiveMarketData已初始化: {exchange}/{symbol}")
    
    def get_current_snapshot(self) -> MarketSnapshot:
        """获取实时市场数据"""
        # TODO: 实现从交易所API获取数据
        raise NotImplementedError("LiveMarketData.get_current_snapshot() 待实现")
    
    def get_historical_snapshots(
        self, 
        start_time: datetime, 
        end_time: datetime,
        interval: str = '5m'
    ) -> List[MarketSnapshot]:
        """获取历史数据（从交易所）"""
        # TODO: 实现从交易所API获取历史数据
        raise NotImplementedError("LiveMarketData.get_historical_snapshots() 待实现")
    
    def is_market_open(self) -> bool:
        """实盘市场总是开放（加密货币24/7）"""
        return True
    
    def get_market_status(self) -> Dict[str, Any]:
        """获取市场状态"""
        return {
            'exchange': self.exchange,
            'symbol': self.symbol,
            'status': 'open',
            'type': 'live'
        }


class BacktestMarketData(MarketDataInterface):
    """
    回测市场数据⭐
    
    从历史数据文件读取
    """
    
    def __init__(self, data_file: str, symbol: str):
        """
        Args:
            data_file: 历史数据文件路径
            symbol: 交易对
        """
        self.data_file = data_file
        self.symbol = symbol
        self.current_index = 0
        self.snapshots: List[MarketSnapshot] = []
        
        # TODO: 加载历史数据
        logger.info(f"📊 BacktestMarketData已初始化: {data_file}")
    
    def get_current_snapshot(self) -> MarketSnapshot:
        """获取当前回测快照"""
        if self.current_index >= len(self.snapshots):
            raise IndexError("回测数据已耗尽")
        
        snapshot = self.snapshots[self.current_index]
        self.current_index += 1
        return snapshot
    
    def get_historical_snapshots(
        self, 
        start_time: datetime, 
        end_time: datetime,
        interval: str = '5m'
    ) -> List[MarketSnapshot]:
        """获取历史快照（从加载的数据中筛选）"""
        # TODO: 实现时间范围筛选
        raise NotImplementedError("BacktestMarketData.get_historical_snapshots() 待实现")
    
    def is_market_open(self) -> bool:
        """回测中市场总是开放"""
        return self.current_index < len(self.snapshots)
    
    def get_market_status(self) -> Dict[str, Any]:
        """获取回测状态"""
        return {
            'data_file': self.data_file,
            'symbol': self.symbol,
            'status': 'backtest',
            'progress': f"{self.current_index}/{len(self.snapshots)}",
            'type': 'backtest'
        }


class SimulatedMarketData(MarketDataInterface):
    """
    模拟市场数据⭐⭐⭐
    
    生成模拟的市场数据，用于训练和测试
    支持各种市场情景（牛市、熊市、黑天鹅等）
    """
    
    def __init__(
        self, 
        symbol: str,
        initial_price: float = 50000.0,
        scenario: str = 'random'
    ):
        """
        Args:
            symbol: 交易对
            initial_price: 初始价格
            scenario: 市场情景（'random', 'bull', 'bear', 'crash', 'sideways'）
        """
        self.symbol = symbol
        self.current_price = initial_price
        self.scenario = scenario
        self.cycle = 0
        
        # 历史数据（用于计算变化）
        self.history = {
            'prev_volatility': 0.01,
            'prev_volume': 1.0
        }
        
        logger.info(f"🎮 SimulatedMarketData已初始化: {symbol}, 场景={scenario}")
    
    def get_current_snapshot(self) -> MarketSnapshot:
        """生成模拟市场快照"""
        import random
        
        self.cycle += 1
        
        # 根据场景生成价格变化
        if self.scenario == 'bull':
            price_change = random.uniform(0.01, 0.03)
        elif self.scenario == 'bear':
            price_change = random.uniform(-0.03, -0.01)
        elif self.scenario == 'crash':
            if self.cycle % 20 == 0:
                price_change = -0.15  # 定期暴跌
            else:
                price_change = random.uniform(-0.01, 0.01)
        elif self.scenario == 'sideways':
            price_change = random.uniform(-0.005, 0.005)
        else:  # random
            price_change = random.uniform(-0.02, 0.02)
        
        # 更新价格
        self.current_price *= (1 + price_change)
        
        # 生成其他指标
        current_volatility = abs(price_change) * 2
        current_volume = 1.0 + random.uniform(-0.2, 0.2)
        
        volatility_change = current_volatility - self.history['prev_volatility']
        volume_change = current_volume - self.history['prev_volume']
        
        # 更新历史
        self.history['prev_volatility'] = current_volatility
        self.history['prev_volume'] = current_volume
        
        # 创建快照
        snapshot = MarketSnapshot(
            timestamp=datetime.now(),
            symbol=self.symbol,
            price=self.current_price,
            price_change=price_change,
            price_change_24h=price_change * 12,
            volatility=current_volatility,
            volatility_24h=current_volatility,
            volatility_change=volatility_change,
            volume=current_volume,
            volume_24h=current_volume * 24,
            volume_ratio=current_volume,
            volume_change=volume_change
        )
        
        return snapshot
    
    def get_historical_snapshots(
        self, 
        start_time: datetime, 
        end_time: datetime,
        interval: str = '5m'
    ) -> List[MarketSnapshot]:
        """生成模拟历史数据"""
        # TODO: 根据时间范围生成历史快照
        raise NotImplementedError("SimulatedMarketData.get_historical_snapshots() 待实现")
    
    def is_market_open(self) -> bool:
        """模拟市场总是开放"""
        return True
    
    def get_market_status(self) -> Dict[str, Any]:
        """获取模拟市场状态"""
        return {
            'symbol': self.symbol,
            'scenario': self.scenario,
            'cycle': self.cycle,
            'price': self.current_price,
            'status': 'simulated',
            'type': 'simulation'
        }


# ========== 工厂函数 ==========

def create_market_data(
    mode: str,
    **kwargs
) -> MarketDataInterface:
    """
    工厂函数：创建市场数据接口⭐⭐⭐
    
    Args:
        mode: 模式（'live', 'backtest', 'simulation'）
        **kwargs: 各模式特定参数
    
    Returns:
        MarketDataInterface: 市场数据接口实例
    
    Examples:
        # 实盘
        market_data = create_market_data('live', exchange='okx', symbol='BTC-USDT')
        
        # 回测
        market_data = create_market_data('backtest', data_file='btc_2024.csv', symbol='BTC-USDT')
        
        # 模拟
        market_data = create_market_data('simulation', symbol='BTC-USDT', scenario='bull')
    """
    if mode == 'live':
        return LiveMarketData(**kwargs)
    elif mode == 'backtest':
        return BacktestMarketData(**kwargs)
    elif mode == 'simulation':
        return SimulatedMarketData(**kwargs)
    else:
        raise ValueError(f"不支持的模式: {mode}")


if __name__ == "__main__":
    # 测试代码
    print("测试SimulatedMarketData...")
    market = SimulatedMarketData(symbol='BTC-USDT', scenario='bull')
    
    for i in range(5):
        snapshot = market.get_current_snapshot()
        print(f"周期{i+1}: 价格={snapshot.price:.2f}, 变化={snapshot.price_change:+.2%}")
    
    print("\n✅ MarketDataInterface设计完成！")

