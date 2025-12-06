"""
WorldSignature集成训练

让Agent"知道"它在什么世界中
这是朋友指出的最关键问题！
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

from .regime_generators import RegimeGenerator
from prometheus.world_signature import StreamingSignatureGenerator

logger = logging.getLogger(__name__)


@dataclass
class SignatureEnrichedData:
    """带WorldSignature的训练数据"""
    
    day: int
    price: float
    
    # WorldSignature特征
    drift: float        # 漂移率
    volatility: float   # 波动率
    trend_strength: float  # 趋势强度
    entropy: float      # 熵
    regime_label: str   # Regime标签
    
    # 原始signature
    signature: 'WorldSignature_V2' = None


class SignatureAwareTrainingGenerator:
    """
    带WorldSignature感知的训练生成器
    
    这解决了朋友指出的核心问题：
    让Agent"知道"它在什么世界中！
    """
    
    def __init__(
        self,
        regime_generator: RegimeGenerator,
        instrument: str = "BTC-USDT"
    ):
        """
        初始化
        
        Args:
            regime_generator: Regime生成器
            instrument: 交易对
        """
        self.regime_generator = regime_generator
        self.signature_generator = StreamingSignatureGenerator(
            instrument=instrument,
            macro_window_hours=24,  # 24小时窗口
            micro_window_minutes=60  # 1小时窗口
        )
    
    def generate_training_data(
        self,
        days: int
    ) -> List[SignatureEnrichedData]:
        """
        生成带WorldSignature的训练数据
        
        这是关键：每一天都带上WS标签！
        
        Args:
            days: 天数
            
        Returns:
            带签名的训练数据列表
        """
        logger.info(f"🏷️  生成带WorldSignature的训练数据（{days}天）")
        
        # 生成价格序列
        prices = self.regime_generator.generate_series(days)
        
        # 为每一天生成WorldSignature
        enriched_data = []
        
        for day, price in enumerate(prices):
            # 生成signature
            market_data = self._create_market_data(price, day)
            signature = self.signature_generator.update(
                market_data=market_data,
                funding_rate=0.0003,
                open_interest=1000000
            )
            
            # 提取关键特征
            macro_features = signature.macro.human_tags
            
            # 计算特征值
            drift = self._extract_drift(macro_features)
            volatility = self._extract_volatility(macro_features)
            trend_strength = self._extract_trend_strength(signature)
            entropy = signature.novelty_score
            regime_label = self._infer_regime_label(macro_features)
            
            # 创建enriched data
            data = SignatureEnrichedData(
                day=day,
                price=price,
                drift=drift,
                volatility=volatility,
                trend_strength=trend_strength,
                entropy=entropy,
                regime_label=regime_label,
                signature=signature
            )
            
            enriched_data.append(data)
            
            if (day + 1) % 100 == 0:
                logger.info(f"  生成进度: {day+1}/{days}")
        
        logger.info(f"✅ 生成完成：{len(enriched_data)}天，全部带WorldSignature")
        
        return enriched_data
    
    def _create_market_data(self, price: float, day: int) -> Dict:
        """创建market data"""
        spread = price * 0.001
        
        return {
            'price': price,
            'volume': 10.0 + np.random.rand() * 5,
            'orderbook': {
                'bids': [[price - spread/2 * (1 + i*0.1), 1.0 + i*0.1] for i in range(10)],
                'asks': [[price + spread/2 * (1 + i*0.1), 1.0 + i*0.1] for i in range(10)]
            },
            'trades': []
        }
    
    def _extract_drift(self, tags: List[str]) -> float:
        """从tags提取漂移率"""
        tags_str = ' '.join(tags)
        
        if 'STRONG_UP' in tags_str:
            return 0.02
        elif 'trend:UP' in tags_str:
            return 0.01
        elif 'STRONG_DOWN' in tags_str:
            return -0.02
        elif 'trend:DOWN' in tags_str:
            return -0.01
        else:
            return 0.0
    
    def _extract_volatility(self, tags: List[str]) -> float:
        """从tags提取波动率"""
        tags_str = ' '.join(tags)
        
        if 'vol:HIGH' in tags_str:
            return 0.05
        elif 'vol:MED' in tags_str:
            return 0.03
        else:
            return 0.01
    
    def _extract_trend_strength(self, signature: 'WorldSignature_V2') -> float:
        """提取趋势强度"""
        # 基于regime confidence和stability
        return signature.regime_confidence * signature.stability_score
    
    def _infer_regime_label(self, tags: List[str]) -> str:
        """推断regime标签"""
        tags_str = ' '.join(tags)
        
        if 'STRONG_UP' in tags_str or 'trend:UP' in tags_str:
            if 'vol:HIGH' in tags_str:
                return "volatile_bull"
            else:
                return "steady_bull"
        elif 'STRONG_DOWN' in tags_str or 'trend:DOWN' in tags_str:
            if 'vol:HIGH' in tags_str:
                return "crash_bear"
            else:
                return "steady_bear"
        elif 'vol:HIGH' in tags_str:
            return "high_volatility"
        elif 'vol:LOW' in tags_str:
            return "low_volatility"
        else:
            return "sideways"
    
    def get_statistics(self, data: List[SignatureEnrichedData]) -> Dict:
        """获取统计信息"""
        if not data:
            return {}
        
        # Regime分布
        regime_counts = {}
        for d in data:
            regime_counts[d.regime_label] = regime_counts.get(d.regime_label, 0) + 1
        
        regime_distribution = {
            name: count / len(data) * 100
            for name, count in regime_counts.items()
        }
        
        # 特征统计
        drifts = [d.drift for d in data]
        vols = [d.volatility for d in data]
        trends = [d.trend_strength for d in data]
        entropies = [d.entropy for d in data]
        
        return {
            'total_days': len(data),
            'regime_distribution': regime_distribution,
            'avg_drift': np.mean(drifts),
            'avg_volatility': np.mean(vols),
            'avg_trend_strength': np.mean(trends),
            'avg_entropy': np.mean(entropies),
            'price_start': data[0].price,
            'price_end': data[-1].price,
            'total_return': (data[-1].price / data[0].price - 1) * 100
        }


def demonstrate_signature_training():
    """演示WorldSignature训练数据生成"""
    from .regime_generators import BullMarketGenerator
    
    logger.info("="*70)
    logger.info("🎯 WorldSignature训练数据演示")
    logger.info("="*70)
    
    # 创建牛市生成器
    bull_gen = BullMarketGenerator()
    
    # 创建signature-aware生成器
    sig_gen = SignatureAwareTrainingGenerator(
        regime_generator=bull_gen
    )
    
    # 生成训练数据
    data = sig_gen.generate_training_data(days=100)
    
    # 显示前5天数据
    logger.info(f"\n{'='*70}")
    logger.info("📋 前5天数据示例")
    logger.info(f"{'='*70}")
    
    for d in data[:5]:
        logger.info(f"\nDay {d.day}:")
        logger.info(f"  价格: ${d.price:,.2f}")
        logger.info(f"  WorldSignature特征:")
        logger.info(f"    - drift: {d.drift:+.4f}")
        logger.info(f"    - volatility: {d.volatility:.4f}")
        logger.info(f"    - trend_strength: {d.trend_strength:.4f}")
        logger.info(f"    - entropy: {d.entropy:.4f}")
        logger.info(f"    - regime: {d.regime_label}")
    
    # 统计信息
    stats = sig_gen.get_statistics(data)
    
    logger.info(f"\n{'='*70}")
    logger.info("📊 统计信息")
    logger.info(f"{'='*70}")
    logger.info(f"总天数: {stats['total_days']}")
    logger.info(f"总收益: {stats['total_return']:+.1f}%")
    logger.info(f"\n平均特征:")
    logger.info(f"  drift: {stats['avg_drift']:+.4f}")
    logger.info(f"  volatility: {stats['avg_volatility']:.4f}")
    logger.info(f"  trend_strength: {stats['avg_trend_strength']:.4f}")
    logger.info(f"  entropy: {stats['avg_entropy']:.4f}")
    logger.info(f"\nRegime分布:")
    for regime, pct in stats['regime_distribution'].items():
        logger.info(f"  {regime}: {pct:.1f}%")
    
    logger.info(f"\n{'='*70}")
    logger.info("🎊 关键价值")
    logger.info(f"{'='*70}")
    logger.info("""
现在Agent接收的不仅仅是：
❌ 价格
    
而是：
✅ 价格
✅ drift（漂移率）
✅ volatility（波动率）
✅ trend_strength（趋势强度）
✅ entropy（熵）
✅ regime_label（世界标签）

Agent终于可以"知道"它在什么世界中了！

这正是朋友指出的关键问题的解决方案！
    """)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    demonstrate_signature_training()

