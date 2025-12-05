"""
简单对手Agent系统

为长期测试提供基础的市场对手，让环境更真实：
- SimpleInstitution: 机构玩家（趋势跟随）
- SimpleRetailer: 散户玩家（追涨杀跌）
- SimpleOpponentMarket: 带对手的市场环境

注意：这是简化版本，不包含复杂的对抗性AI和GAN训练
"""

import random
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class OpponentTrade:
    """对手交易记录"""
    opponent_type: str  # 'institution' or 'retailer'
    side: str  # 'buy' or 'sell'
    amount: float
    price: float
    timestamp: datetime
    impact_on_price: float  # 对价格的影响（%）


class SimpleInstitution:
    """
    简单机构玩家
    
    特征：
    - 大资金（100K-1M USDT）
    - 趋势跟随策略
    - 慢速交易（低频）
    - 对价格有显著影响（3-5%市场冲击）
    - 持仓周期长（数小时到数天）
    """
    
    def __init__(self, 
                 capital: float = 500_000,
                 impact_factor: float = 0.03,
                 patience: float = 0.9,
                 trend_threshold: float = 0.02):
        """
        初始化机构玩家
        
        Args:
            capital: 资金量
            impact_factor: 市场冲击系数（对价格的影响）
            patience: 耐心系数（0-1，越高越不频繁交易）
            trend_threshold: 趋势判断阈值（价格变化超过此值才行动）
        """
        self.capital = capital
        self.impact_factor = impact_factor
        self.patience = patience
        self.trend_threshold = trend_threshold
        
        self.position = 0.0  # 当前持仓
        self.entry_price = 0.0
        self.last_trade_time = None
        self.trades_history = []
        
    def make_decision(self, 
                     current_price: float,
                     price_history: List[float],
                     current_time: datetime) -> Optional[OpponentTrade]:
        """
        做出交易决策
        
        策略：简单的趋势跟随
        - 价格上涨超过threshold → 买入
        - 价格下跌超过threshold → 卖出
        - 考虑patience：不是每次都交易
        
        Args:
            current_price: 当前价格
            price_history: 历史价格（最近N个）
            current_time: 当前时间
            
        Returns:
            OpponentTrade or None
        """
        # 1. 耐心检查（不频繁交易）
        if random.random() > (1 - self.patience):
            # 太耐心了，这次不交易
            return None
        
        # 2. 计算趋势
        if len(price_history) < 10:
            return None
        
        # 简单的趋势：最近10个价格的平均变化
        recent_prices = price_history[-10:]
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # 3. 决策
        trade = None
        
        if price_change > self.trend_threshold:
            # 上涨趋势 → 买入（如果还没持仓）
            if self.position <= 0:
                trade_amount = self.capital * 0.3 / current_price  # 投入30%资金
                
                trade = OpponentTrade(
                    opponent_type='institution',
                    side='buy',
                    amount=trade_amount,
                    price=current_price,
                    timestamp=current_time,
                    impact_on_price=self.impact_factor
                )
                
                self.position = trade_amount
                self.entry_price = current_price
                self.last_trade_time = current_time
                self.trades_history.append(trade)
                
                logger.debug(f"🏦 机构买入: {trade_amount:.4f} @ ${current_price:.2f}")
        
        elif price_change < -self.trend_threshold:
            # 下跌趋势 → 卖出（如果有持仓）
            if self.position > 0:
                trade_amount = self.position
                
                trade = OpponentTrade(
                    opponent_type='institution',
                    side='sell',
                    amount=trade_amount,
                    price=current_price,
                    timestamp=current_time,
                    impact_on_price=-self.impact_factor  # 卖出压低价格
                )
                
                # 计算盈亏
                pnl = (current_price - self.entry_price) * self.position
                self.capital += pnl
                
                self.position = 0
                self.last_trade_time = current_time
                self.trades_history.append(trade)
                
                logger.debug(f"🏦 机构卖出: {trade_amount:.4f} @ ${current_price:.2f}, PNL: ${pnl:.2f}")
        
        return trade
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'type': 'institution',
            'capital': self.capital,
            'position': self.position,
            'total_trades': len(self.trades_history)
        }


class SimpleRetailer:
    """
    简单散户玩家
    
    特征：
    - 小资金（1K-10K USDT）
    - 追涨杀跌策略（情绪化）
    - 高频交易
    - 对价格几乎无影响（0.01%市场冲击）
    - 持仓周期短（数分钟到数小时）
    - 羊群效应（跟随大趋势）
    """
    
    def __init__(self,
                 capital: float = 5_000,
                 impact_factor: float = 0.0001,
                 emotion_factor: float = 0.8,
                 herd_tendency: float = 0.7):
        """
        初始化散户玩家
        
        Args:
            capital: 资金量
            impact_factor: 市场冲击系数（很小）
            emotion_factor: 情绪化系数（0-1，越高越容易冲动交易）
            herd_tendency: 羊群倾向（0-1，越高越跟风）
        """
        self.capital = capital
        self.impact_factor = impact_factor
        self.emotion_factor = emotion_factor
        self.herd_tendency = herd_tendency
        
        self.position = 0.0
        self.entry_price = 0.0
        self.last_trade_time = None
        self.trades_history = []
        
    def make_decision(self,
                     current_price: float,
                     price_history: List[float],
                     current_time: datetime,
                     market_sentiment: float = 0.0) -> Optional[OpponentTrade]:
        """
        做出交易决策
        
        策略：追涨杀跌 + 羊群效应
        - 价格刚涨 → 立即买入（怕错过）
        - 价格刚跌 → 立即卖出（怕亏损）
        - 受市场情绪影响（其他人在买，我也买）
        
        Args:
            current_price: 当前价格
            price_history: 历史价格
            current_time: 当前时间
            market_sentiment: 市场情绪（-1到1，正值表示看涨）
            
        Returns:
            OpponentTrade or None
        """
        # 1. 情绪化检查（高概率交易）
        if random.random() > self.emotion_factor:
            # 这次冷静了，不交易
            return None
        
        # 2. 计算短期价格变化（追涨杀跌）
        if len(price_history) < 3:
            return None
        
        # 最近3个价格的变化
        short_term_change = (price_history[-1] - price_history[-3]) / price_history[-3]
        
        # 3. 羊群效应：跟随市场情绪
        herd_factor = market_sentiment * self.herd_tendency
        
        # 4. 综合决策
        decision_score = short_term_change + herd_factor
        
        trade = None
        
        if decision_score > 0.005:  # 0.5%的变化就行动
            # 追涨：刚涨就买！
            if self.position <= 0:
                trade_amount = self.capital * 0.5 / current_price  # 投入50%（激进）
                
                trade = OpponentTrade(
                    opponent_type='retailer',
                    side='buy',
                    amount=trade_amount,
                    price=current_price,
                    timestamp=current_time,
                    impact_on_price=self.impact_factor  # 几乎无影响
                )
                
                self.position = trade_amount
                self.entry_price = current_price
                self.last_trade_time = current_time
                self.trades_history.append(trade)
                
                logger.debug(f"👨‍💼 散户买入: {trade_amount:.4f} @ ${current_price:.2f}")
        
        elif decision_score < -0.005:
            # 杀跌：刚跌就卖！
            if self.position > 0:
                trade_amount = self.position
                
                trade = OpponentTrade(
                    opponent_type='retailer',
                    side='sell',
                    amount=trade_amount,
                    price=current_price,
                    timestamp=current_time,
                    impact_on_price=-self.impact_factor
                )
                
                # 计算盈亏
                pnl = (current_price - self.entry_price) * self.position
                self.capital += pnl
                
                self.position = 0
                self.last_trade_time = current_time
                self.trades_history.append(trade)
                
                logger.debug(f"👨‍💼 散户卖出: {trade_amount:.4f} @ ${current_price:.2f}, PNL: ${pnl:.2f}")
        
        return trade
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'type': 'retailer',
            'capital': self.capital,
            'position': self.position,
            'total_trades': len(self.trades_history)
        }


class SimpleOpponentMarket:
    """
    带对手的简单市场环境
    
    模拟真实市场中的多方博弈：
    - 我们的Prometheus Agents
    - 机构玩家（10个）
    - 散户玩家（100个）
    
    市场特性：
    - 价格受所有参与者影响
    - 有限的流动性
    - 基础的市场摩擦
    - 🆕 自然价格波动（打破僵局）
    """
    
    def __init__(self,
                 num_institutions: int = 10,
                 num_retailers: int = 100,
                 base_liquidity: float = 1_000_000,
                 enable_natural_volatility: bool = True,
                 volatility_std: float = 0.005):
        """
        初始化市场环境
        
        Args:
            num_institutions: 机构数量
            num_retailers: 散户数量
            base_liquidity: 基础流动性（USDT）
            enable_natural_volatility: 是否启用自然波动（打破价格僵局）
            volatility_std: 波动率标准差（默认0.5%）
        """
        self.num_institutions = num_institutions
        self.num_retailers = num_retailers
        self.base_liquidity = base_liquidity
        self.enable_natural_volatility = enable_natural_volatility
        self.volatility_std = volatility_std
        
        # 创建对手
        self.institutions = [
            SimpleInstitution(
                capital=random.uniform(100_000, 1_000_000),
                impact_factor=random.uniform(0.02, 0.05),
                patience=random.uniform(0.8, 0.95),
                trend_threshold=random.uniform(0.015, 0.03)
            )
            for _ in range(num_institutions)
        ]
        
        self.retailers = [
            SimpleRetailer(
                capital=random.uniform(1_000, 10_000),
                impact_factor=0.0001,
                emotion_factor=random.uniform(0.7, 0.95),
                herd_tendency=random.uniform(0.5, 0.9)
            )
            for _ in range(num_retailers)
        ]
        
        # 市场状态
        self.price_history = []
        self.all_trades = []
        self.current_liquidity = base_liquidity
        
        logger.info(f"🏛️ 市场初始化:")
        logger.info(f"   机构: {num_institutions}个")
        logger.info(f"   散户: {num_retailers}个")
        logger.info(f"   流动性: ${base_liquidity:,.0f}")
    
    def simulate_step(self,
                     current_price: float,
                     current_time: datetime) -> Tuple[float, List[OpponentTrade]]:
        """
        模拟一个市场步骤
        
        流程：
        1. 所有对手做出决策
        2. 收集所有交易
        3. 计算价格影响
        4. 更新价格
        5. 更新流动性
        
        Args:
            current_price: 当前价格
            current_time: 当前时间
            
        Returns:
            (new_price, trades): 新价格和交易列表
        """
        # 1. 记录价格历史
        self.price_history.append(current_price)
        
        # 保持最近1000个价格
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
        
        # 2. 收集所有对手的交易
        step_trades = []
        
        # 机构交易
        for inst in self.institutions:
            trade = inst.make_decision(
                current_price=current_price,
                price_history=self.price_history,
                current_time=current_time
            )
            if trade:
                step_trades.append(trade)
        
        # 散户交易
        # 计算市场情绪（机构的净买入/卖出）
        inst_sentiment = 0.0
        for trade in step_trades:
            if trade.opponent_type == 'institution':
                inst_sentiment += 1 if trade.side == 'buy' else -1
        
        market_sentiment = np.tanh(inst_sentiment / len(self.institutions))  # 归一化到[-1,1]
        
        for retailer in self.retailers:
            trade = retailer.make_decision(
                current_price=current_price,
                price_history=self.price_history,
                current_time=current_time,
                market_sentiment=market_sentiment
            )
            if trade:
                step_trades.append(trade)
        
        # 3. 计算总价格影响
        total_price_impact = sum(trade.impact_on_price for trade in step_trades)
        
        # 3.5 🆕 添加自然市场波动（打破僵局）
        natural_volatility = 0.0
        if self.enable_natural_volatility:
            # 模拟市场自然波动（外部因素、新闻、情绪等）
            natural_volatility = np.random.normal(0, self.volatility_std)
            
            # 偶尔会有较大波动（模拟重要新闻）
            if random.random() < 0.05:  # 5%概率
                natural_volatility *= 3  # 3倍波动
            
            logger.debug(f"   🌊 自然波动: {natural_volatility*100:+.2f}%")
        
        # 4. 更新价格（对手影响 + 自然波动）
        total_impact = total_price_impact + natural_volatility
        new_price = current_price * (1 + total_impact)
        
        # 确保价格合理（不会暴涨暴跌）
        price_change_limit = 0.05  # 单轮最大变化5%
        price_change = (new_price - current_price) / current_price
        if abs(price_change) > price_change_limit:
            new_price = current_price * (1 + np.sign(price_change) * price_change_limit)
            logger.warning(f"   ⚠️  价格变化过大，限制在±5%")
        
        # 5. 更新流动性（交易越多，流动性暂时降低）
        trade_volume = sum(trade.amount * trade.price for trade in step_trades)
        liquidity_drain = trade_volume / self.base_liquidity
        self.current_liquidity = self.base_liquidity * (1 - liquidity_drain * 0.5)
        
        # 6. 记录交易
        self.all_trades.extend(step_trades)
        
        # 日志
        if step_trades:
            logger.debug(f"📊 市场步骤: {len(step_trades)}笔交易, 价格影响: {total_price_impact*100:.3f}%")
        
        return new_price, step_trades
    
    def get_market_stats(self) -> Dict:
        """获取市场统计信息"""
        # 机构统计
        inst_stats = [inst.get_stats() for inst in self.institutions]
        total_inst_capital = sum(s['capital'] for s in inst_stats)
        total_inst_trades = sum(s['total_trades'] for s in inst_stats)
        
        # 散户统计
        retail_stats = [r.get_stats() for r in self.retailers]
        total_retail_capital = sum(s['capital'] for s in retail_stats)
        total_retail_trades = sum(s['total_trades'] for s in retail_stats)
        
        return {
            'institutions': {
                'count': self.num_institutions,
                'total_capital': total_inst_capital,
                'total_trades': total_inst_trades,
                'avg_trades_per_inst': total_inst_trades / self.num_institutions if self.num_institutions > 0 else 0
            },
            'retailers': {
                'count': self.num_retailers,
                'total_capital': total_retail_capital,
                'total_trades': total_retail_trades,
                'avg_trades_per_retail': total_retail_trades / self.num_retailers if self.num_retailers > 0 else 0
            },
            'market': {
                'total_trades': len(self.all_trades),
                'current_liquidity': self.current_liquidity,
                'base_liquidity': self.base_liquidity
            }
        }
    
    def reset(self):
        """重置市场状态"""
        for inst in self.institutions:
            inst.position = 0
            inst.entry_price = 0
            inst.trades_history = []
        
        for retailer in self.retailers:
            retailer.position = 0
            retailer.entry_price = 0
            retailer.trades_history = []
        
        self.price_history = []
        self.all_trades = []
        self.current_liquidity = self.base_liquidity
        
        logger.info("🔄 市场已重置")

