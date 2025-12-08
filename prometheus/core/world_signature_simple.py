"""
WorldSignatureSimple - 简化版市场签名

14维向量，足够区分不同市场状态：
  - 趋势类（3维）
  - 波动类（3维）
  - 动量类（4维）
  - 成交量类（2维）
  - 市场状态（2维）

用途：
  - Mock训练学校的经验记录
  - 智能创世的市场匹配
  - 未来可升级为完整版WorldSignature
"""

import numpy as np
import pandas as pd
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class WorldSignatureSimple:
    """
    简化版WorldSignature
    
    14维向量，基于技术指标
    """
    
    DIMENSION = 14
    
    # ✨ v6.0: 维度权重（用于加权相似度计算）
    # 突出关键维度（trend, rsi, market_phase）的重要性
    DIMENSION_WEIGHTS = np.array([
        2.0,  # 0: trend_7d
        3.0,  # 1: trend_30d ⭐ 最重要！
        2.5,  # 2: trend_strength ⭐
        1.5,  # 3: volatility_7d
        1.5,  # 4: volatility_30d
        1.0,  # 5: atr
        2.5,  # 6: rsi ⭐ 很重要！
        1.5,  # 7: macd
        1.5,  # 8: momentum_7d
        2.0,  # 9: momentum_30d
        1.0,  # 10: volume_ratio
        1.0,  # 11: volume_trend
        2.5,  # 12: market_phase ⭐
        3.0   # 13: crash_signal ⭐ 最重要！
    ])
    
    def __init__(self):
        self.vector = np.zeros(self.DIMENSION)
    
    @classmethod
    def from_market_data(cls, df: pd.DataFrame, window_size: int = 100):
        """
        从市场数据计算WorldSignature
        
        参数：
          - df: 市场K线数据（需要包含：open, high, low, close, volume）
          - window_size: 窗口大小（默认100根K线）
        
        返回：
          - WorldSignatureSimple对象
        """
        ws = cls()
        
        # 确保有足够的数据
        if len(df) < window_size:
            logger.warning(f"数据不足{window_size}根K线，使用全部数据")
            recent = df
        else:
            recent = df.tail(window_size)
        
        # 计算各项指标
        try:
            # 1. 趋势类（3维）
            ws.vector[0] = ws._calculate_trend(recent, period=7)
            ws.vector[1] = ws._calculate_trend(recent, period=30)
            ws.vector[2] = abs(ws.vector[1])  # 趋势强度
            
            # 2. 波动类（3维）
            ws.vector[3] = ws._calculate_volatility(recent, period=7)
            ws.vector[4] = ws._calculate_volatility(recent, period=30)
            ws.vector[5] = ws._calculate_atr(recent, period=14)
            
            # 3. 动量类（4维）
            ws.vector[6] = ws._calculate_rsi(recent, period=14)
            ws.vector[7] = ws._calculate_macd(recent)
            ws.vector[8] = ws._calculate_momentum(recent, period=7)
            ws.vector[9] = ws._calculate_momentum(recent, period=30)
            
            # 4. 成交量类（2维）
            ws.vector[10] = ws._calculate_volume_ratio(recent)
            ws.vector[11] = ws._calculate_volume_trend(recent)
            
            # 5. 市场状态（2维）
            ws.vector[12] = ws._classify_market_phase(ws.vector[1], ws.vector[4])
            ws.vector[13] = ws._detect_crash_signal(ws.vector[1], ws.vector[4])
            
        except Exception as e:
            logger.error(f"计算WorldSignature失败: {e}")
            # 返回零向量
        
        return ws
    
    # ===== 技术指标计算 =====
    
    @staticmethod
    def _calculate_trend(df: pd.DataFrame, period: int) -> float:
        """计算趋势（涨跌幅）"""
        if len(df) < period:
            return 0.0
        return (df['close'].iloc[-1] / df['close'].iloc[-period] - 1)
    
    @staticmethod
    def _calculate_volatility(df: pd.DataFrame, period: int) -> float:
        """计算波动率（标准差）"""
        if len(df) < period:
            return 0.0
        returns = df['close'].pct_change().tail(period)
        return returns.std()
    
    @staticmethod
    def _calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
        """计算平均真实波幅（归一化）"""
        if len(df) < period + 1:
            return 0.0
        
        high = df['high']
        low = df['low']
        close_prev = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close_prev).abs()
        tr3 = (low - close_prev).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.tail(period).mean()
        
        # 归一化（相对于价格）
        return atr / df['close'].iloc[-1] if df['close'].iloc[-1] > 0 else 0.0
    
    @staticmethod
    def _calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
        """计算RSI（0-1范围）"""
        if len(df) < period + 1:
            return 0.5
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).tail(period).mean()
        loss = (-delta.where(delta < 0, 0)).tail(period).mean()
        
        if loss == 0:
            return 1.0
        
        rs = gain / loss
        rsi = 1 - (1 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_macd(df: pd.DataFrame) -> float:
        """计算MACD（归一化）"""
        if len(df) < 26:
            return 0.0
        
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        macd = ema12 - ema26
        
        # 归一化
        return macd.iloc[-1] / df['close'].iloc[-1] if df['close'].iloc[-1] > 0 else 0.0
    
    @staticmethod
    def _calculate_momentum(df: pd.DataFrame, period: int) -> float:
        """计算动量"""
        if len(df) < period:
            return 0.0
        return (df['close'].iloc[-1] - df['close'].iloc[-period]) / df['close'].iloc[-period]
    
    @staticmethod
    def _calculate_volume_ratio(df: pd.DataFrame) -> float:
        """计算成交量比率"""
        if len(df) < 2:
            return 1.0
        avg_volume = df['volume'].mean()
        if avg_volume == 0:
            return 1.0
        return df['volume'].iloc[-1] / avg_volume
    
    @staticmethod
    def _calculate_volume_trend(df: pd.DataFrame) -> float:
        """计算成交量趋势"""
        if len(df) < 30:
            return 0.0
        vol_7 = df['volume'].tail(7).mean()
        vol_30 = df['volume'].tail(30).mean()
        if vol_30 == 0:
            return 0.0
        return (vol_7 / vol_30 - 1)
    
    @staticmethod
    def _classify_market_phase(trend_30d: float, volatility_30d: float) -> float:
        """分类市场阶段（0=熊市，1=震荡市，2=牛市）"""
        if trend_30d > 0.1:
            return 2.0  # 牛市
        elif trend_30d < -0.1:
            return 0.0  # 熊市
        else:
            return 1.0  # 震荡市
    
    @staticmethod
    def _detect_crash_signal(trend_30d: float, volatility_30d: float) -> float:
        """检测崩盘信号（0=正常，1=崩盘）"""
        if volatility_30d > 0.05 and trend_30d < -0.1:
            return 1.0  # 崩盘
        else:
            return 0.0  # 正常
    
    # ===== 相似度计算 =====
    
    def similarity(self, other: 'WorldSignatureSimple', use_weights: bool = True) -> float:
        """
        计算与另一个WorldSignature的相似度（加权欧氏距离）
        
        v6.0优化：
        - 改用加权欧氏距离（关注绝对差异）
        - 突出关键维度（trend, rsi, market_phase）的差异
        - 提高不同市场类型的区分度
        
        参数：
          - other: 另一个WorldSignature
          - use_weights: 是否使用权重（默认True）
        
        返回：0-1之间的值，1表示完全相同
        """
        if use_weights:
            # ✨ 加权欧氏距离
            # 关键维度的差异会被放大
            diff = self.vector - other.vector
            weighted_diff = diff * self.DIMENSION_WEIGHTS
            distance = np.linalg.norm(weighted_diff)
            
            # 转换为相似度（距离越小，相似度越高）
            # 使用exponential decay: similarity = exp(-distance / scale)
            # scale参数控制衰减速度，这里设为2.0
            similarity = np.exp(-distance / 2.0)
        else:
            # 原始余弦相似度（向后兼容）
            dot_product = np.dot(self.vector, other.vector)
            norm_self = np.linalg.norm(self.vector)
            norm_other = np.linalg.norm(other.vector)
            
            if norm_self == 0 or norm_other == 0:
                return 0.0
            
            similarity = dot_product / (norm_self * norm_other)
        
        return max(0.0, min(1.0, similarity))  # 限制在[0, 1]
    
    # ===== 序列化 =====
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            'trend_7d': float(self.vector[0]),
            'trend_30d': float(self.vector[1]),
            'trend_strength': float(self.vector[2]),
            'volatility_7d': float(self.vector[3]),
            'volatility_30d': float(self.vector[4]),
            'atr': float(self.vector[5]),
            'rsi': float(self.vector[6]),
            'macd': float(self.vector[7]),
            'momentum_7d': float(self.vector[8]),
            'momentum_30d': float(self.vector[9]),
            'volume_ratio': float(self.vector[10]),
            'volume_trend': float(self.vector[11]),
            'market_phase': float(self.vector[12]),
            'crash_signal': float(self.vector[13])
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorldSignatureSimple':
        """从字典反序列化"""
        ws = cls()
        ws.vector[0] = data['trend_7d']
        ws.vector[1] = data['trend_30d']
        ws.vector[2] = data['trend_strength']
        ws.vector[3] = data['volatility_7d']
        ws.vector[4] = data['volatility_30d']
        ws.vector[5] = data['atr']
        ws.vector[6] = data['rsi']
        ws.vector[7] = data['macd']
        ws.vector[8] = data['momentum_7d']
        ws.vector[9] = data['momentum_30d']
        ws.vector[10] = data['volume_ratio']
        ws.vector[11] = data['volume_trend']
        ws.vector[12] = data['market_phase']
        ws.vector[13] = data['crash_signal']
        return ws
    
    def to_human_readable(self) -> str:
        """转换为人类可读的字符串"""
        d = self.to_dict()
        
        # 市场阶段
        phase_map = {0.0: '熊市', 1.0: '震荡市', 2.0: '牛市'}
        phase = phase_map.get(d['market_phase'], '未知')
        
        # 崩盘信号
        crash = '⚠️ 崩盘' if d['crash_signal'] > 0.5 else '正常'
        
        return (
            f"市场状态: {phase} ({crash})\n"
            f"  趋势: 7日={d['trend_7d']*100:.1f}%, 30日={d['trend_30d']*100:.1f}%\n"
            f"  波动: 7日={d['volatility_7d']*100:.2f}%, 30日={d['volatility_30d']*100:.2f}%\n"
            f"  动量: RSI={d['rsi']*100:.0f}, MACD={d['macd']*1000:.2f}\n"
            f"  成交量: 比率={d['volume_ratio']:.2f}, 趋势={d['volume_trend']*100:.1f}%"
        )
    
    def __repr__(self) -> str:
        return f"WorldSignatureSimple(phase={self.vector[12]:.0f}, trend_30d={self.vector[1]:.3f})"

