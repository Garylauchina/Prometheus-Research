"""
MicroCode - 微观市场编码

短时间窗口（tick-5min）特征：
- 买卖价差
- 订单簿深度
- 订单流不平衡
- 交易侵略性
- 微观波动率
- 流动性韧性
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class MicroCode:
    """
    微观编码
    
    包含：
    - human_tags: 人类可读标签
    - compact_text: 紧凑文本编码
    - micro_vec: 向量嵌入
    - raw_features: 原始特征值
    """
    
    human_tags: List[str]
    compact_text: str
    micro_vec: np.ndarray
    raw_features: Dict[str, float]
    
    def __post_init__(self):
        """验证数据格式"""
        assert len(self.human_tags) > 0, "human_tags不能为空"
        assert len(self.compact_text) > 0, "compact_text不能为空"
        assert len(self.micro_vec.shape) == 1, "micro_vec必须是1维向量"
        assert len(self.raw_features) > 0, "raw_features不能为空"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'human_tags': self.human_tags,
            'compact_text': self.compact_text,
            'micro_vec': self.micro_vec.tolist(),
            'raw_features': self.raw_features
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MicroCode':
        """从字典创建"""
        return cls(
            human_tags=data['human_tags'],
            compact_text=data['compact_text'],
            micro_vec=np.array(data['micro_vec']),
            raw_features=data['raw_features']
        )


def compute_micro_features(
    orderbook: Dict,
    recent_trades: List[Dict],
    price_history: np.ndarray,
    window_minutes: int = 5
) -> Dict[str, float]:
    """
    计算微观特征
    
    Args:
        orderbook: 订单簿快照 {'bids': [[price, size], ...], 'asks': [[price, size], ...]}
        recent_trades: 最近交易列表 [{'price': float, 'size': float, 'side': str}, ...]
        price_history: 价格历史数组
        window_minutes: 计算窗口（分钟）
    
    Returns:
        特征字典
    """
    features = {}
    
    # 提取订单簿数据
    bids = orderbook.get('bids', [])
    asks = orderbook.get('asks', [])
    
    if len(bids) == 0 or len(asks) == 0:
        logger.warning("订单簿为空")
        return _default_micro_features()
    
    best_bid = bids[0][0]
    best_ask = asks[0][0]
    mid_price = (best_bid + best_ask) / 2
    
    # 1. 相对价差
    features['rel_spread'] = (best_ask - best_bid) / mid_price
    
    # 2. 订单簿深度（前10档）
    top_n = min(10, len(bids), len(asks))
    
    depth_bid = sum([bid[1] * bid[0] for bid in bids[:top_n]])
    depth_ask = sum([ask[1] * ask[0] for ask in asks[:top_n]])
    
    features['depth_topN_bid'] = depth_bid
    features['depth_topN_ask'] = depth_ask
    
    # 3. 深度不平衡
    total_depth = depth_bid + depth_ask
    if total_depth > 0:
        features['depth_imbalance'] = (depth_bid - depth_ask) / total_depth
    else:
        features['depth_imbalance'] = 0.0
    
    # 4. 订单流不平衡（OFI）
    if len(recent_trades) > 0:
        buy_volume = sum([t['size'] for t in recent_trades if t.get('side') == 'buy'])
        sell_volume = sum([t['size'] for t in recent_trades if t.get('side') == 'sell'])
        total_volume = buy_volume + sell_volume
        
        if total_volume > 0:
            features['ofi'] = (buy_volume - sell_volume) / total_volume
        else:
            features['ofi'] = 0.0
        
        # 5. 主动买入比率
        features['trade_aggression_ratio'] = buy_volume / total_volume if total_volume > 0 else 0.5
    else:
        features['ofi'] = 0.0
        features['trade_aggression_ratio'] = 0.5
    
    # 6. Tick级微观波动率
    if len(price_history) >= 10:
        recent_prices = price_history[-min(len(price_history), window_minutes * 60):]
        if len(recent_prices) > 1:
            features['micro_volatility'] = np.std(recent_prices) / np.mean(recent_prices)
        else:
            features['micro_volatility'] = 0.001
    else:
        features['micro_volatility'] = 0.001
    
    # 7. 队列压力
    top_bid_size = bids[0][1]
    top_ask_size = asks[0][1]
    features['queue_pressure'] = top_ask_size / (top_bid_size + top_ask_size + 1e-6)
    
    # 8. 滑点估计（简化版）
    features['slippage_estimate'] = _estimate_slippage(orderbook, trade_size=1.0)
    
    # 9. 流动性深度总和
    features['total_liquidity'] = total_depth
    
    # 10. 订单簿斜率（简化）
    if len(bids) >= 5 and len(asks) >= 5:
        bid_slope = (bids[0][0] - bids[4][0]) / 5
        ask_slope = (asks[4][0] - asks[0][0]) / 5
        features['orderbook_slope'] = (bid_slope + ask_slope) / mid_price
    else:
        features['orderbook_slope'] = 0.0
    
    return features


def _default_micro_features() -> Dict[str, float]:
    """返回默认微观特征"""
    return {
        'rel_spread': 0.001,
        'depth_topN_bid': 100000,
        'depth_topN_ask': 100000,
        'depth_imbalance': 0.0,
        'ofi': 0.0,
        'trade_aggression_ratio': 0.5,
        'micro_volatility': 0.001,
        'queue_pressure': 0.5,
        'slippage_estimate': 0.0005,
        'total_liquidity': 200000,
        'orderbook_slope': 0.0
    }


def _estimate_slippage(orderbook: Dict, trade_size: float) -> float:
    """
    估计给定交易规模的滑点
    
    Args:
        orderbook: 订单簿
        trade_size: 交易数量（BTC）
    
    Returns:
        预估滑点（相对比例）
    """
    asks = orderbook.get('asks', [])
    if len(asks) == 0:
        return 0.001
    
    best_ask = asks[0][0]
    remaining_size = trade_size
    total_cost = 0.0
    
    for price, size in asks:
        if remaining_size <= 0:
            break
        
        fill_size = min(remaining_size, size)
        total_cost += fill_size * price
        remaining_size -= fill_size
    
    if remaining_size > 0:
        # 订单簿深度不足
        return 0.01  # 1%滑点
    
    avg_price = total_cost / trade_size
    slippage = (avg_price - best_ask) / best_ask
    
    return max(slippage, 0.0)


def discretize_micro(features: Dict[str, float]) -> List[str]:
    """
    将微观特征离散化为tags
    """
    tags = []
    
    # 1. 价差
    spread = features.get('rel_spread', 0.001)
    if spread > 0.002:
        tags.append("spread:WIDE")
    elif spread > 0.0008:
        tags.append("spread:NORMAL")
    else:
        tags.append("spread:TIGHT")
    
    # 2. 深度不平衡
    imb = features.get('depth_imbalance', 0.0)
    if imb > 0.3:
        tags.append(f"depth_imb:+{imb:.2f}")
    elif imb < -0.3:
        tags.append(f"depth_imb:{imb:.2f}")
    else:
        tags.append("depth_imb:BALANCED")
    
    # 3. 订单流不平衡（OFI）
    ofi = features.get('ofi', 0.0)
    if abs(ofi) > 0.3:
        tags.append(f"ofi:{ofi:+.2f}")
    else:
        tags.append("ofi:NEUTRAL")
    
    # 4. 微观波动率
    micro_vol = features.get('micro_volatility', 0.001)
    if micro_vol > 0.003:
        tags.append("microvol:SPIKE")
    elif micro_vol > 0.0015:
        tags.append("microvol:HIGH")
    else:
        tags.append("microvol:NORMAL")
    
    # 5. 流动性韧性
    total_liq = features.get('total_liquidity', 200000)
    if total_liq < 300000:
        tags.append("liqRes:FRAGILE")
    elif total_liq > 800000:
        tags.append("liqRes:STRONG")
    else:
        tags.append("liqRes:NORMAL")
    
    # 6. 滑点
    slippage = features.get('slippage_estimate', 0.0005)
    if slippage > 0.002:
        tags.append("slippage:HIGH")
    elif slippage > 0.001:
        tags.append("slippage:MEDIUM")
    else:
        tags.append("slippage:LOW")
    
    # 7. 交易侵略性
    aggression = features.get('trade_aggression_ratio', 0.5)
    if aggression > 0.65:
        tags.append("aggression:BUY_HEAVY")
    elif aggression < 0.35:
        tags.append("aggression:SELL_HEAVY")
    else:
        tags.append("aggression:BALANCED")
    
    return tags


def tags_to_compact_text(tags: List[str], prefix: str = 'm') -> str:
    """
    将tags转换为紧凑文本
    
    示例: "m:SPRD_W|DI:-0.45|OFI:+0.6"
    """
    compact_parts = [f"{prefix}"]
    
    for tag in tags:
        if ':' not in tag:
            continue
        
        key, value = tag.split(':', 1)
        
        # 缩写映射
        abbrev_map = {
            'spread': 'SPRD',
            'depth_imb': 'DI',
            'ofi': 'OFI',
            'microvol': 'MV',
            'liqRes': 'LR',
            'slippage': 'SLP',
            'aggression': 'AGG'
        }
        
        key_short = abbrev_map.get(key, key[:3].upper())
        
        # 值缩写
        value_abbrev = {
            'WIDE': 'W',
            'NORMAL': 'N',
            'TIGHT': 'T',
            'BALANCED': 'BAL',
            'NEUTRAL': '~',
            'SPIKE': 'SPK',
            'HIGH': 'H',
            'FRAGILE': 'FRG',
            'STRONG': 'STR',
            'LOW': 'L',
            'MEDIUM': 'M',
            'BUY_HEAVY': 'BUY+',
            'SELL_HEAVY': 'SEL+'
        }
        
        value_short = value_abbrev.get(value, value)
        compact_parts.append(f"{key_short}:{value_short}")
    
    return '|'.join(compact_parts)


def embed_micro(features: Dict[str, float], tags: List[str], dim: int = 256) -> np.ndarray:
    """
    将微观特征嵌入为向量
    
    v5.5版本：简单方法
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
        features.get('rel_spread', 0.001) * 1000,  # 放大到合理范围
        features.get('depth_topN_bid', 100000) / 1000000,  # 归一化
        features.get('depth_topN_ask', 100000) / 1000000,
        features.get('depth_imbalance', 0.0),
        features.get('ofi', 0.0),
        features.get('trade_aggression_ratio', 0.5),
        features.get('micro_volatility', 0.001) * 1000,
        features.get('queue_pressure', 0.5),
        features.get('slippage_estimate', 0.0005) * 1000,
        features.get('total_liquidity', 200000) / 1000000,
        features.get('orderbook_slope', 0.0) * 100,
    ])
    
    # 归一化到[-1, 1]
    feature_vec = np.tanh(feature_vec)
    
    # 填充到指定维度
    if len(feature_vec) < dim:
        padding_size = dim - len(feature_vec)
        # 用特征的非线性组合填充
        padding = np.random.randn(padding_size) * 0.1
        embedding = np.concatenate([feature_vec, padding])
    else:
        embedding = feature_vec[:dim]
    
    # L2归一化
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding

