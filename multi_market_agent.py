"""
MultiMarketAgent类 - 支持多市场交易的智能体
"""

from .account import Account
from .strategy_v2 import StrategyV2
from .market_regime import MarketRegimeDetector
import copy

class MultiMarketAgent:
    """多市场交易智能体"""
    
    def __init__(self, agent_id: int, gene: dict, spot_market, futures_market,
                 spot_capital: float, futures_capital: float):
        """
        初始化多市场智能体
        
        Args:
            agent_id: 智能体ID
            gene: 基因字典
            spot_market: 现货市场对象
            futures_market: 期货市场对象
            spot_capital: 现货初始资金
            futures_capital: 期货初始资金
        """
        # 基本信息
        self.agent_id = agent_id
        self.gene = gene
        total_capital = spot_capital + futures_capital
        self.initial_capital = total_capital
        self.capital = total_capital
        
        # 生命周期
        self.is_alive = True
        self.death_reason = None
        
        # 交易统计
        self.trade_count = 0
        self.last_trade_day = 0
        
        # 性能指标
        self.roi = 0.0
        self.capital_history = []
        self.roi_history = []
        
        # 创建两个账户
        self.spot_account = Account(spot_market, spot_capital)
        self.futures_account = Account(futures_market, futures_capital)
        
        # 保存初始资金
        self.initial_spot = spot_capital
        self.initial_futures = futures_capital
        
        # 创建策略（使用StrategyV2支持动态多空比例）
        self.strategy = StrategyV2(gene)
        
        # 市场状态检测器
        self.market_detector = MarketRegimeDetector()
        
        # 杠杆倍数（从基因中读取，默认3.0）
        self.futures_leverage = gene.get('futures_leverage', 3.0)
        # 确保不超过市场上限
        self.futures_leverage = min(self.futures_leverage, futures_market.leverage)
        
    def update(self, day: int, price: float, market_data: dict):
        """
        更新智能体状态（多市场版本）
        
        Args:
            day: 当前天数
            price: 当前价格
            market_data: 市场数据
        """
        # 检测市场状态
        market_regime = self.market_detector.detect(market_data['prices'])
        
        # 计算现货信号
        spot_signal = self._calculate_spot_signal(market_data, market_regime)
        
        # 计算期货信号
        futures_signal = self._calculate_futures_signal(market_data, market_regime)
        
        # 执行交易
        spot_pnl = self.spot_account.trade(price, spot_signal)
        futures_pnl = self.futures_account.trade(price, futures_signal)
        
        # 检查期货爆仓
        if self.futures_account.check_liquidation(price, threshold=-0.90):
            # 强制平仓
            liquidation_pnl = self.futures_account.force_close(price)
            futures_pnl += liquidation_pnl
            self.death_reason = 'liquidation'
            self.is_alive = False
        
        # 更新总资本
        self.capital = self.spot_account.capital + self.futures_account.capital
        
        # 更新ROI
        self.roi = (self.capital - self.initial_capital) / self.initial_capital
        
        # 更新交易计数
        self.trade_count = self.spot_account.trades + self.futures_account.trades
        
        # 更新最后交易日
        if spot_pnl != 0 or futures_pnl != 0:
            self.last_trade_day = day
        
        # 更新历史
        self.capital_history.append(self.capital)
        self.roi_history.append(self.roi)
        
        return spot_pnl + futures_pnl
    
    def _calculate_spot_signal(self, market_data: dict, market_regime: str) -> float:
        """
        计算现货交易信号
        
        Args:
            market_data: 市场数据
            market_regime: 市场状态
            
        Returns:
            交易信号 (0.0 to 1.0, 现货只能做多)
        """
        # 使用StrategyV2计算基础信号
        long_ratio, short_ratio = self.strategy.calculate_dynamic_ratio(market_regime)
        base_signal = self.strategy.calculate(market_data)
        
        # 现货信号 = 做多信号 * 做多比例
        # 现货只能做多，所以只取正值
        spot_signal = max(0, base_signal) * long_ratio
        
        # 应用市场偏好（如果基因中有）
        spot_multiplier = self.gene.get('market_preference', {}).get(
            'spot_threshold_multiplier', 1.0
        )
        
        return spot_signal * spot_multiplier
    
    def _calculate_futures_signal(self, market_data: dict, market_regime: str) -> float:
        """
        计算期货交易信号
        
        Args:
            market_data: 市场数据
            market_regime: 市场状态
            
        Returns:
            交易信号 (-1.0 to 1.0, 期货可做多做空)
        """
        # 使用StrategyV2计算基础信号
        long_ratio, short_ratio = self.strategy.calculate_dynamic_ratio(market_regime)
        base_signal = self.strategy.calculate(market_data)
        
        # 期货信号 = 基础信号 * 对应比例
        if base_signal > 0:
            futures_signal = base_signal * long_ratio
        else:
            futures_signal = base_signal * short_ratio
        
        # 应用市场偏好（如果基因中有）
        futures_multiplier = self.gene.get('market_preference', {}).get(
            'futures_threshold_multiplier', 1.0
        )
        
        # 应用杠杆调整（高杠杆时降低仓位）
        leverage_adjustment = 1.0 / (1.0 + (self.futures_leverage - 1.0) * 0.1)
        
        return futures_signal * futures_multiplier * leverage_adjustment
    
    def get_total_trades(self) -> int:
        """获取总交易次数"""
        return self.spot_account.trades + self.futures_account.trades
    
    def get_total_fees(self) -> float:
        """获取总手续费"""
        return self.spot_account.total_fees + self.futures_account.total_fees
    
    def get_account_summary(self) -> dict:
        """获取账户摘要"""
        return {
            'total_capital': self.capital,
            'total_roi': self.roi,
            'spot': {
                'capital': self.spot_account.capital,
                'roi': self.spot_account.get_roi(),
                'position': self.spot_account.position,
                'trades': self.spot_account.trades,
                'fees': self.spot_account.total_fees
            },
            'futures': {
                'capital': self.futures_account.capital,
                'roi': self.futures_account.get_roi(),
                'position': self.futures_account.position,
                'trades': self.futures_account.trades,
                'fees': self.futures_account.total_fees,
                'leverage': self.futures_leverage
            }
        }
    
    def __repr__(self):
        return (f"MultiMarketAgent(id={self.agent_id}, capital=${self.capital:.2f}, "
                f"ROI={self.roi:.2%}, spot_pos={self.spot_account.position:.2f}, "
                f"futures_pos={self.futures_account.position:.2f})")
