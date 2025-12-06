"""
StreamingSignatureGenerator - 流式签名生成器

功能：
1. 维护滑动窗口数据
2. 实时计算特征
3. 生成完整签名
4. 计算评分指标
"""

from collections import deque
from typing import Dict, List, Optional
import numpy as np
import time
import logging

from .macro_code import MacroCode, compute_macro_features, discretize_macro, tags_to_compact_text as macro_compact, embed_macro
from .micro_code import MicroCode, compute_micro_features, discretize_micro, tags_to_compact_text as micro_compact, embed_micro
from .signature import WorldSignature_V2
from .metrics import calculate_all_metrics
from .regime import RegimeLibrary

logger = logging.getLogger(__name__)


class StreamingSignatureGenerator:
    """
    流式签名生成器
    
    支持：
    - Sliding window数据缓存
    - 增量特征计算
    - 实时签名生成
    - 评分指标计算
    """
    
    def __init__(
        self,
        instrument: str = "BTC-USDT",
        macro_window_hours: int = 4,
        micro_window_minutes: int = 5,
        history_size: int = 1000
    ):
        """
        初始化
        
        Args:
            instrument: 交易对
            macro_window_hours: 宏观窗口（小时）
            micro_window_hours: 微观窗口（分钟）
            history_size: 历史签名保存数量
        """
        self.instrument = instrument
        self.macro_window = macro_window_hours * 60  # 转换为分钟
        self.micro_window = micro_window_minutes
        
        # 滑动窗口数据
        self.ohlc_buffer = deque(maxlen=self.macro_window)  # OHLC数据
        self.volume_buffer = deque(maxlen=self.macro_window)  # 成交量
        self.price_buffer = deque(maxlen=self.macro_window)  # 价格
        self.micro_vec_buffer = deque(maxlen=100)  # 最近100个微观向量
        
        # 统计数据
        self.volume_30d_avg = None
        self.vol_30d_avg = 0.015  # 默认1.5%
        self.oi_24h_ago = None
        
        # 历史签名（用于novelty计算）
        self.historical_signatures = deque(maxlen=history_size)
        
        # Regime库（可选）
        self.regime_lib: Optional[RegimeLibrary] = None
        
        # 统计
        self.generation_count = 0
        
        logger.info(f"✅ StreamingSignatureGenerator初始化完成")
        logger.info(f"   Instrument: {instrument}")
        logger.info(f"   Macro窗口: {macro_window_hours}小时")
        logger.info(f"   Micro窗口: {micro_window_minutes}分钟")
    
    def update(
        self,
        market_data: Dict,
        funding_rate: float = 0.0,
        open_interest: float = 0.0
    ) -> WorldSignature_V2:
        """
        更新数据并生成新签名
        
        Args:
            market_data: {
                'price': float,
                'volume': float,
                'orderbook': {'bids': [...], 'asks': [...]},
                'trades': [{'price': float, 'size': float, 'side': str}, ...]
            }
            funding_rate: 资金费率
            open_interest: 持仓量
        
        Returns:
            新生成的签名
        """
        # 1. 更新buffer
        price = market_data.get('price', 50000.0)
        volume = market_data.get('volume', 1.0)
        
        self.price_buffer.append(price)
        self.volume_buffer.append(volume)
        
        # OHLC（简化：用当前价格）
        ohlc = [price, price, price, price]  # open, high, low, close
        self.ohlc_buffer.append(ohlc)
        
        # 2. 更新统计数据
        if self.volume_30d_avg is None:
            self.volume_30d_avg = volume * 1440  # 粗略估计
        
        if self.oi_24h_ago is None:
            self.oi_24h_ago = open_interest
        
        # 3. 计算宏观特征
        macro_features = self._compute_macro()
        macro_features['funding_rate'] = funding_rate
        macro_features['oi_change_pct'] = (
            (open_interest - self.oi_24h_ago) / self.oi_24h_ago
            if self.oi_24h_ago > 0 else 0.0
        )
        
        # 离散化
        macro_tags = discretize_macro(macro_features)
        macro_text = macro_compact(macro_tags, 'M')
        macro_vec = embed_macro(macro_features, macro_tags)
        
        macro_code = MacroCode(
            human_tags=macro_tags,
            compact_text=macro_text,
            macro_vec=macro_vec,
            raw_features=macro_features
        )
        
        # 4. 计算微观特征
        orderbook = market_data.get('orderbook', self._default_orderbook(price))
        trades = market_data.get('trades', [])
        
        micro_features = compute_micro_features(
            orderbook=orderbook,
            recent_trades=trades,
            price_history=np.array(list(self.price_buffer)),
            window_minutes=self.micro_window
        )
        
        # 离散化
        micro_tags = discretize_micro(micro_features)
        micro_text = micro_compact(micro_tags, 'm')
        micro_vec = embed_micro(micro_features, micro_tags)
        
        micro_code = MicroCode(
            human_tags=micro_tags,
            compact_text=micro_text,
            micro_vec=micro_vec,
            raw_features=micro_features
        )
        
        # 保存微观向量（用于稳定度计算）
        self.micro_vec_buffer.append(micro_vec)
        
        # 5. 创建签名
        signature = WorldSignature_V2(
            id=WorldSignature_V2.generate_id(),
            timestamp=time.time(),
            instrument=self.instrument,
            macro=macro_code,
            micro=micro_code
        )
        
        # 6. 计算评分指标
        metrics = calculate_all_metrics(
            signature=signature,
            regime_lib=self.regime_lib,
            recent_micro_vecs=list(self.micro_vec_buffer),
            historical_sigs=list(self.historical_signatures)
        )
        
        signature.regime_id = None
        signature.regime_confidence = metrics['regime_confidence']
        signature.stability_score = metrics['stability_score']
        signature.danger_index = metrics['danger_index']
        signature.opportunity_index = metrics['opportunity_index']
        signature.novelty_score = metrics['novelty_score']
        
        # 7. Regime匹配
        if self.regime_lib and len(self.regime_lib.regimes) > 0:
            regime_id, confidence = self.regime_lib.match_regime(signature)
            signature.regime_id = regime_id
            signature.regime_confidence = confidence
        
        # 8. 加入历史
        self.historical_signatures.append(signature)
        self.generation_count += 1
        
        # 9. 定期日志
        if self.generation_count % 100 == 0:
            logger.info(f"✅ 已生成{self.generation_count}个签名")
        
        return signature
    
    def _compute_macro(self) -> Dict[str, float]:
        """从buffer计算宏观特征"""
        if len(self.ohlc_buffer) < 2:
            return self._default_macro_features()
        
        ohlc_array = np.array(list(self.ohlc_buffer))
        volume_array = np.array(list(self.volume_buffer))
        
        features = compute_macro_features(
            ohlc_data=ohlc_array,
            volume_data=volume_array,
            funding_rate=0.0,  # 外部传入
            open_interest=0.0,  # 外部传入
            open_interest_24h_ago=self.oi_24h_ago or 0.0,
            volume_30d_avg=self.volume_30d_avg or 1.0,
            vol_30d_avg=self.vol_30d_avg,
            window_hours=len(self.ohlc_buffer) // 60
        )
        
        return features
    
    def _default_macro_features(self) -> Dict[str, float]:
        """默认宏观特征"""
        return {
            'trend_slope': 0.0,
            'realized_vol_1h': 0.015,
            'realized_vol_6h': 0.015,
            'realized_vol_24h': 0.015,
            'vol_spike_ratio': 1.0,
            'funding_rate': 0.0,
            'oi_change_pct': 0.0,
            'adv_ratio': 1.0,
            'momentum_24h': 0.0
        }
    
    def _default_orderbook(self, mid_price: float) -> Dict:
        """默认订单簿"""
        spread = mid_price * 0.001  # 0.1%价差
        
        return {
            'bids': [
                [mid_price - spread/2, 1.0],
                [mid_price - spread, 0.5],
                [mid_price - spread*2, 0.3],
            ],
            'asks': [
                [mid_price + spread/2, 1.0],
                [mid_price + spread, 0.5],
                [mid_price + spread*2, 0.3],
            ]
        }
    
    def set_regime_lib(self, regime_lib: RegimeLibrary):
        """设置Regime库"""
        self.regime_lib = regime_lib
        logger.info(f"✅ Regime库已设置: {len(regime_lib.regimes)}个Regime")
    
    def set_30d_stats(self, volume_avg: float, vol_avg: float):
        """设置30天统计数据"""
        self.volume_30d_avg = volume_avg
        self.vol_30d_avg = vol_avg
        logger.info(f"✅ 30天统计已更新: volume_avg={volume_avg:.0f}, vol_avg={vol_avg:.2%}")
    
    def get_latest_signature(self) -> Optional[WorldSignature_V2]:
        """获取最新签名"""
        if len(self.historical_signatures) > 0:
            return self.historical_signatures[-1]
        return None
    
    def get_historical_signatures(self) -> List[WorldSignature_V2]:
        """获取所有历史签名"""
        return list(self.historical_signatures)
    
    def statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'generation_count': self.generation_count,
            'buffer_size': {
                'ohlc': len(self.ohlc_buffer),
                'volume': len(self.volume_buffer),
                'price': len(self.price_buffer),
                'micro_vec': len(self.micro_vec_buffer)
            },
            'historical_signatures': len(self.historical_signatures),
            'regime_lib_size': len(self.regime_lib.regimes) if self.regime_lib else 0
        }

