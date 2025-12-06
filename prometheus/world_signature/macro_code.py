"""
MacroCode - 宏观市场编码

长时间窗口（1h-24h）特征：
- 价格趋势
- 波动率
- 流动性
- 资金费率
- 持仓量
- 成交量
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class MacroCode:
    """
    宏观编码
    
    包含：
    - human_tags: 人类可读标签
    - compact_text: 紧凑文本编码
    - macro_vec: 向量嵌入
    - raw_features: 原始特征值
    """
    
    human_tags: List[str]
    compact_text: str
    macro_vec: np.ndarray
    raw_features: Dict[str, float]
    
    def __post_init__(self):
        """验证数据格式"""
        assert len(self.human_tags) > 0, "human_tags不能为空"
        assert len(self.compact_text) > 0, "compact_text不能为空"
        assert len(self.macro_vec.shape) == 1, "macro_vec必须是1维向量"
        assert len(self.raw_features) > 0, "raw_features不能为空"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'human_tags': self.human_tags,
            'compact_text': self.compact_text,
            'macro_vec': self.macro_vec.tolist(),
            'raw_features': self.raw_features
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MacroCode':
        """从字典创建"""
        return cls(
            human_tags=data['human_tags'],
            compact_text=data['compact_text'],
            macro_vec=np.array(data['macro_vec']),
            raw_features=data['raw_features']
        )


def compute_macro_features(
    ohlc_data: np.ndarray,
    volume_data: np.ndarray,
    funding_rate: float,
    open_interest: float,
    open_interest_24h_ago: float,
    volume_30d_avg: float,
    vol_30d_avg: float,
    window_hours: int = 4
) -> Dict[str, float]:
    """
    计算宏观特征
    
    Args:
        ohlc_data: OHLC价格数组 (N, 4) - open, high, low, close
        volume_data: 成交量数组 (N,)
        funding_rate: 当前资金费率
        open_interest: 当前持仓量
        open_interest_24h_ago: 24小时前持仓量
        volume_30d_avg: 30天平均成交量
        vol_30d_avg: 30天平均波动率
        window_hours: 计算窗口（小时）
    
    Returns:
        特征字典
    """
    features = {}
    
    # 提取close价格
    if len(ohlc_data.shape) == 2:
        close_prices = ohlc_data[:, 3]  # close列
    else:
        close_prices = ohlc_data
    
    # 确保有足够数据
    window_minutes = window_hours * 60
    if len(close_prices) < window_minutes:
        logger.warning(f"数据不足: 需要{window_minutes}分钟，实际{len(close_prices)}分钟")
        window_minutes = len(close_prices)
    
    prices = close_prices[-window_minutes:]
    
    # 1. 价格趋势（线性斜率）
    if len(prices) >= 2:
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        features['trend_slope'] = slope / np.mean(prices)  # 归一化
    else:
        features['trend_slope'] = 0.0
    
    # 2. 已实现波动率（多时间尺度）
    if len(close_prices) >= 60:
        features['realized_vol_1h'] = _calculate_realized_vol(close_prices[-60:])
    else:
        features['realized_vol_1h'] = 0.01
    
    if len(close_prices) >= 360:
        features['realized_vol_6h'] = _calculate_realized_vol(close_prices[-360:])
    else:
        features['realized_vol_6h'] = features['realized_vol_1h']
    
    if len(close_prices) >= 1440:
        features['realized_vol_24h'] = _calculate_realized_vol(close_prices[-1440:])
    else:
        features['realized_vol_24h'] = features['realized_vol_1h']
    
    # 3. 波动率突增比率
    current_vol = features['realized_vol_1h']
    features['vol_spike_ratio'] = current_vol / (vol_30d_avg + 1e-6)
    
    # 4. 资金费率
    features['funding_rate'] = funding_rate
    
    # 5. 持仓量变化
    if open_interest_24h_ago > 0:
        features['oi_change_pct'] = (open_interest - open_interest_24h_ago) / open_interest_24h_ago
    else:
        features['oi_change_pct'] = 0.0
    
    # 6. 成交量比率
    volume_24h = np.sum(volume_data[-1440:]) if len(volume_data) >= 1440 else np.sum(volume_data)
    features['adv_ratio'] = volume_24h / (volume_30d_avg + 1e-6)
    
    # 7. 价格动量（简化）
    if len(close_prices) >= 24:
        momentum_24h = (close_prices[-1] - close_prices[-24]) / close_prices[-24]
        features['momentum_24h'] = momentum_24h
    else:
        features['momentum_24h'] = 0.0
    
    return features


def _calculate_realized_vol(prices: np.ndarray) -> float:
    """
    计算已实现波动率
    
    使用对数收益率的标准差
    """
    if len(prices) < 2:
        return 0.01
    
    log_returns = np.diff(np.log(prices + 1e-10))
    vol = np.std(log_returns)
    
    return vol


def discretize_macro(features: Dict[str, float]) -> List[str]:
    """
    将宏观特征离散化为tags
    
    使用阈值规则
    """
    tags = []
    
    # 1. 趋势
    slope = features.get('trend_slope', 0.0)
    if slope > 0.05:
        tags.append("trend:STRONG_UP")
    elif slope > 0.01:
        tags.append("trend:UP")
    elif slope < -0.05:
        tags.append("trend:STRONG_DOWN")
    elif slope < -0.01:
        tags.append("trend:DOWN")
    else:
        tags.append("trend:SIDEWAYS")
    
    # 2. 波动率
    vol_1h = features.get('realized_vol_1h', 0.015)
    vol_spike = features.get('vol_spike_ratio', 1.0)
    
    if vol_spike > 1.5:
        tags.append("vol:HIGH")
    elif vol_spike < 0.7:
        tags.append("vol:LOW")
    else:
        tags.append("vol:NORMAL")
    
    # 3. 流动性（基于成交量比率）
    adv_ratio = features.get('adv_ratio', 1.0)
    if adv_ratio > 1.5:
        tags.append("liquidity:HIGH")
    elif adv_ratio < 0.7:
        tags.append("liquidity:LOW")
    else:
        tags.append("liquidity:NORMAL")
    
    # 4. 资金费率
    funding = features.get('funding_rate', 0.0)
    if abs(funding) > 0.0005:
        tags.append(f"funding:{funding:+.4f}")
    else:
        tags.append("funding:NEUTRAL")
    
    # 5. 持仓量
    oi_change = features.get('oi_change_pct', 0.0)
    if oi_change > 0.1:
        tags.append("OI:RISING")
    elif oi_change < -0.1:
        tags.append("OI:FALLING")
    else:
        tags.append("OI:STABLE")
    
    # 6. 动量
    momentum = features.get('momentum_24h', 0.0)
    if momentum > 0.05:
        tags.append("momentum:STRONG_POS")
    elif momentum > 0.02:
        tags.append("momentum:POS")
    elif momentum < -0.05:
        tags.append("momentum:STRONG_NEG")
    elif momentum < -0.02:
        tags.append("momentum:NEG")
    else:
        tags.append("momentum:NEUTRAL")
    
    return tags


def tags_to_compact_text(tags: List[str], prefix: str = 'M') -> str:
    """
    将tags转换为紧凑文本
    
    示例: "M:TRD↑|V:HIGH|L:LOW|F:+0.03"
    """
    compact_parts = [f"{prefix}"]
    
    for tag in tags:
        key, value = tag.split(':')
        
        # 缩写映射
        abbrev_map = {
            'trend': 'TRD',
            'vol': 'V',
            'liquidity': 'L',
            'funding': 'F',
            'OI': 'OI',
            'momentum': 'MOM'
        }
        
        key_short = abbrev_map.get(key, key[:3].upper())
        
        # 值缩写
        value_abbrev = {
            'STRONG_UP': '↑↑',
            'UP': '↑',
            'STRONG_DOWN': '↓↓',
            'DOWN': '↓',
            'SIDEWAYS': '→',
            'HIGH': 'H',
            'LOW': 'L',
            'NORMAL': 'N',
            'RISING': '↑',
            'FALLING': '↓',
            'STABLE': '=',
            'NEUTRAL': '~',
            'STRONG_POS': '++',
            'POS': '+',
            'STRONG_NEG': '--',
            'NEG': '-'
        }
        
        value_short = value_abbrev.get(value, value)
        compact_parts.append(f"{key_short}:{value_short}")
    
    return '|'.join(compact_parts)


def embed_macro(features: Dict[str, float], tags: List[str], dim: int = 128) -> np.ndarray:
    """
    将宏观特征嵌入为向量
    
    v5.5版本：简单方法，直接用特征值+归一化
    v6.0版本：使用MLP或Transformer
    
    Args:
        features: 特征字典
        tags: 标签列表
        dim: 向量维度
    
    Returns:
        嵌入向量
    """
    # 简单版本：特征值归一化后填充
    feature_vec = np.array([
        features.get('trend_slope', 0.0),
        features.get('realized_vol_1h', 0.015),
        features.get('realized_vol_6h', 0.015),
        features.get('realized_vol_24h', 0.015),
        features.get('vol_spike_ratio', 1.0),
        features.get('funding_rate', 0.0),
        features.get('oi_change_pct', 0.0),
        features.get('adv_ratio', 1.0),
        features.get('momentum_24h', 0.0),
    ])
    
    # 归一化到[-1, 1]
    feature_vec = np.tanh(feature_vec * 10)
    
    # 填充到指定维度
    if len(feature_vec) < dim:
        # 用特征值的组合填充剩余维度
        padding_size = dim - len(feature_vec)
        padding = np.random.randn(padding_size) * 0.1  # 小噪声
        embedding = np.concatenate([feature_vec, padding])
    else:
        embedding = feature_vec[:dim]
    
    # L2归一化
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding

