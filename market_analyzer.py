"""
MarketAnalyzer - 市场分析器模块

职责: 计算市场特征
"""

from typing import Dict, List
import math


class MarketAnalyzer:
    """市场分析器 - 计算市场特征"""
    
    def __init__(self, config: Dict):
        """
        Args:
            config: 分析器配置
        """
        self.config = config
    
    def _get_price(self, price_history: List, index: int) -> float:
        """
        获取价格（支持两种格式）
        
        Args:
            price_history: 价格历史
            index: 索引
        
        Returns:
            价格
        """
        if isinstance(price_history[index], dict):
            return price_history[index]['price']
        return price_history[index]
    
    def analyze(self, price_history: List[float], current_day: int) -> Dict[str, float]:
        """
        分析市场特征
        
        Args:
            price_history: 价格历史
            current_day: 当前天数
        
        Returns:
            市场特征字典 {feature_name: value}
            value范围 [-1, 1]
        """
        if current_day < 1 or current_day >= len(price_history):
            return {}
        
        features = {}
        
        # 1. 趋势方向
        features.update(self._analyze_trend_direction(price_history, current_day))
        
        # 2. 波动性
        features.update(self._analyze_volatility(price_history, current_day))
        
        # 3. 情绪
        features.update(self._analyze_sentiment(price_history, current_day))
        
        # 4. 成交量（简化版，使用价格波动代替）
        features.update(self._analyze_volume(price_history, current_day))
        
        # 5. 价格模式
        features.update(self._analyze_price_pattern(price_history, current_day))
        
        # 6. 趋势强度
        features.update(self._analyze_trend_strength(price_history, current_day))
        
        # 7. 支撑阻力
        features.update(self._analyze_support_resistance(price_history, current_day))
        
        return features
    
    def _analyze_trend_direction(self, prices: List[float], day: int) -> Dict[str, float]:
        """分析趋势方向"""
        ma_short = self.config.get('ma_short', 7)
        ma_long = self.config.get('ma_long', 30)
        
        if day < ma_long:
            return {}
        
        # 计算短期和长期均线
        short_ma = sum([self._get_price(prices, i) for i in range(day-ma_short, day)]) / ma_short
        long_ma = sum([self._get_price(prices, i) for i in range(day-ma_long, day)]) / ma_long
        current_price = self._get_price(prices, day)
        
        # 计算相对位置
        short_diff = (current_price - short_ma) / short_ma
        long_diff = (short_ma - long_ma) / long_ma
        
        features = {}
        
        # 强牛市: 价格远高于短期均线，短期均线远高于长期均线
        if short_diff > 0.05 and long_diff > 0.03:
            features['strong_bull'] = 1.0
        # 牛市
        elif short_diff > 0.02 and long_diff > 0.01:
            features['bull'] = 0.8
        # 弱牛市
        elif short_diff > 0 and long_diff > 0:
            features['weak_bull'] = 0.5
        # 横盘
        elif abs(short_diff) < 0.01 and abs(long_diff) < 0.01:
            features['sideways'] = 0.6
        # 弱熊市
        elif short_diff < 0 and long_diff < 0:
            features['weak_bear'] = 0.5
        # 熊市
        elif short_diff < -0.02 and long_diff < -0.01:
            features['bear'] = 0.8
        # 强熊市
        elif short_diff < -0.05 and long_diff < -0.03:
            features['strong_bear'] = 1.0
        
        return features
    
    def _analyze_volatility(self, prices: List[float], day: int) -> Dict[str, float]:
        """分析波动性"""
        window = self.config.get('volatility_window', 20)
        
        if day < window:
            return {}
        
        # 计算日收益率
        returns = []
        for i in range(day-window+1, day+1):
            if i > 0:
                ret = (self._get_price(prices, i) - self._get_price(prices, i-1)) / self._get_price(prices, i-1)
                returns.append(ret)
        
        if not returns:
            return {}
        
        # 计算标准差（波动率）
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance)
        
        features = {}
        
        # 根据波动率分类
        if volatility > 0.08:
            features['extreme_high_vol'] = 1.0
        elif volatility > 0.05:
            features['high_vol'] = 0.9
        elif volatility > 0.02:
            features['normal_vol'] = 0.6
        elif volatility > 0.01:
            features['low_vol'] = 0.7
        else:
            features['ultra_low_vol'] = 0.8
        
        return features
    
    def _analyze_sentiment(self, prices: List[float], day: int) -> Dict[str, float]:
        """分析市场情绪（基于RSI）"""
        rsi_period = self.config.get('rsi_period', 14)
        
        if day < rsi_period + 1:
            return {}
        
        # 计算RSI
        gains = []
        losses = []
        
        for i in range(day-rsi_period, day):
            change = self._get_price(prices, i+1) - self._get_price(prices, i)
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / rsi_period
        avg_loss = sum(losses) / rsi_period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        features = {}
        
        # 根据RSI分类情绪
        if rsi > 80:
            features['extreme_greed'] = 1.0
        elif rsi > 70:
            features['greed'] = 0.8
        elif rsi > 45 and rsi < 55:
            features['neutral'] = 0.6
        elif rsi < 30:
            features['fear'] = 0.8
        elif rsi < 20:
            features['extreme_fear'] = 1.0
        
        return features
    
    def _analyze_volume(self, prices: List[float], day: int) -> Dict[str, float]:
        """分析成交量（简化版，使用价格波动幅度代替）"""
        window = 10
        
        if day < window:
            return {}
        
        # 计算最近的价格波动幅度
        recent_ranges = []
        for i in range(day-window, day):
            if i > 0:
                price_range = abs(self._get_price(prices, i) - self._get_price(prices, i-1)) / self._get_price(prices, i-1)
                recent_ranges.append(price_range)
        
        if not recent_ranges:
            return {}
        
        avg_range = sum(recent_ranges) / len(recent_ranges)
        current_range = abs(self._get_price(prices, day) - self._get_price(prices, day-1)) / self._get_price(prices, day-1)
        
        features = {}
        
        # 根据相对波动幅度分类
        if current_range > avg_range * 2:
            features['volume_surge'] = 1.0
        elif current_range > avg_range * 1.2:
            features['normal_volume'] = 0.6
        elif current_range < avg_range * 0.5:
            features['volume_drying_up'] = 0.8
        else:
            features['low_volume'] = 0.7
        
        return features
    
    def _analyze_price_pattern(self, prices: List[float], day: int) -> Dict[str, float]:
        """分析价格模式"""
        if day < 5:
            return {}
        
        current = self._get_price(prices, day)
        prev = self._get_price(prices, day-1)
        prev2 = self._get_price(prices, day-2)
        
        change = (current - prev) / prev
        prev_change = (prev - prev2) / prev2
        
        features = {}
        
        # 突破
        if change > 0.03:
            features['breakout'] = 1.0
        # 跌破
        elif change < -0.03:
            features['breakdown'] = 1.0
        # 回调
        elif change < 0 and prev_change > 0.02:
            features['pullback'] = 0.8
        # 向上跳空
        elif change > 0.05:
            features['gap_up'] = 0.9
        # 向下跳空
        elif change < -0.05:
            features['gap_down'] = 0.9
        # 横盘
        elif abs(change) < 0.01:
            if abs(prev_change) < 0.01:
                features['ranging'] = 0.7
            else:
                features['consolidation'] = 0.6
        
        return features
    
    def _analyze_trend_strength(self, prices: List[float], day: int) -> Dict[str, float]:
        """分析趋势强度"""
        window = 20
        
        if day < window:
            return {}
        
        # 计算价格变化的一致性
        changes = []
        for i in range(day-window+1, day+1):
            if i > 0:
                change = (self._get_price(prices, i) - self._get_price(prices, i-1)) / self._get_price(prices, i-1)
                changes.append(change)
        
        if not changes:
            return {}
        
        # 计算同向变化的比例
        positive = sum(1 for c in changes if c > 0)
        negative = sum(1 for c in changes if c < 0)
        total = len(changes)
        
        consistency = max(positive, negative) / total
        
        features = {}
        
        # 根据一致性分类趋势强度
        if consistency > 0.8:
            features['very_strong_trend'] = 1.0
        elif consistency > 0.7:
            features['strong_trend'] = 0.8
        elif consistency > 0.6:
            features['weak_trend'] = 0.6
        elif consistency < 0.55:
            features['choppy'] = 0.7
        else:
            features['no_trend'] = 0.6
        
        return features
    
    def _analyze_support_resistance(self, prices: List[float], day: int) -> Dict[str, float]:
        """分析支撑和阻力"""
        window = 50
        
        if day < window:
            return {}
        
        recent_prices = [self._get_price(prices, i) for i in range(day-window, day+1)]
        current = self._get_price(prices, day)
        
        # 找到最高和最低价
        highest = max(recent_prices)
        lowest = min(recent_prices)
        price_range = highest - lowest
        
        if price_range == 0:
            return {}
        
        # 计算当前价格的相对位置
        position = (current - lowest) / price_range
        
        features = {}
        
        # 根据位置分类
        if position > 0.9:
            features['near_resistance'] = 1.0
        elif position > 0.95:
            features['breaking_resistance'] = 0.9
        elif position < 0.1:
            features['near_support'] = 1.0
        elif position < 0.05:
            features['breaking_support'] = 0.9
        else:
            features['middle_range'] = 0.5
        
        return features
    
    def __repr__(self) -> str:
        return f"MarketAnalyzer(config={self.config})"
