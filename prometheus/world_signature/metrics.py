"""
评分指标计算

5个核心指标：
1. RegimeConfidence - Regime匹配置信度
2. StabilityScore - 市场微结构稳定性
3. DangerIndex - 综合风险评估
4. OpportunityIndex - 交易机会评估
5. NoveltyScore - 未见情况检测
"""

from typing import List, Dict
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_regime_confidence(
    current_signature: 'WorldSignature_V2',
    regime_lib: 'RegimeLibrary'
) -> float:
    """
    计算Regime匹配置信度
    
    Args:
        current_signature: 当前签名
        regime_lib: Regime库
    
    Returns:
        置信度 [0, 1]
    """
    if regime_lib is None or len(regime_lib.regimes) == 0:
        return 0.0
    
    regime_id, similarity = regime_lib.match_regime(current_signature)
    
    return similarity


def calculate_stability_score(recent_micro_vecs: List[np.ndarray]) -> float:
    """
    计算市场微结构稳定性
    
    稳定性 = 1 - 波动率（归一化）
    
    Args:
        recent_micro_vecs: 最近的微观向量列表
    
    Returns:
        稳定度 [0, 1]，越高越稳定
    """
    if len(recent_micro_vecs) < 2:
        return 0.5  # 默认中等稳定
    
    # 计算向量之间的变化
    changes = []
    for i in range(1, len(recent_micro_vecs)):
        change = np.linalg.norm(recent_micro_vecs[i] - recent_micro_vecs[i-1])
        changes.append(change)
    
    if len(changes) == 0:
        return 0.5
    
    # 计算波动率（标准差/均值）
    mean_change = np.mean(changes)
    std_change = np.std(changes)
    
    if mean_change < 1e-6:
        return 1.0  # 完全稳定
    
    volatility = std_change / mean_change
    
    # 转换为稳定度
    # volatility低 → stability高
    stability = 1 / (1 + volatility)
    
    return stability


def calculate_danger_index(micro_features: Dict[str, float]) -> float:
    """
    计算危险指数
    
    综合评估：
    - 滑点（30%权重）
    - 深度不平衡（30%权重）
    - 流动性（20%权重）
    - 波动率（20%权重）
    
    Args:
        micro_features: 微观特征
    
    Returns:
        危险指数 [0, 1]，越高越危险
    """
    danger = 0.0
    
    # 1. 滑点（权重0.3）
    slippage = micro_features.get('slippage_estimate', 0.0005)
    # 0.1% → 0分，1% → 满分
    slippage_score = min(slippage / 0.01, 1.0)
    danger += 0.3 * slippage_score
    
    # 2. 深度不平衡（权重0.3）
    depth_imb = abs(micro_features.get('depth_imbalance', 0.0))
    # 0 → 0分，0.5 → 满分
    imbalance_score = min(depth_imb / 0.5, 1.0)
    danger += 0.3 * imbalance_score
    
    # 3. 流动性（权重0.2）
    total_liq = micro_features.get('total_liquidity', 200000)
    # 流动性低 → 危险高
    # 1000000 → 0分，100000 → 满分
    if total_liq < 100000:
        liquidity_score = 1.0
    elif total_liq > 1000000:
        liquidity_score = 0.0
    else:
        liquidity_score = 1 - (total_liq - 100000) / 900000
    danger += 0.2 * liquidity_score
    
    # 4. 微观波动率（权重0.2）
    micro_vol = micro_features.get('micro_volatility', 0.001)
    # 0.1% → 0分，0.5% → 满分
    vol_score = min(micro_vol / 0.005, 1.0)
    danger += 0.2 * vol_score
    
    return min(danger, 1.0)


def calculate_opportunity_index(
    macro_features: Dict[str, float],
    micro_features: Dict[str, float]
) -> float:
    """
    计算机会指数
    
    综合评估：
    - 趋势强度（40%权重）
    - 成交量（30%权重）
    - 资金费率套利（20%权重）
    - 流动性（10%权重）
    
    Args:
        macro_features: 宏观特征
        micro_features: 微观特征
    
    Returns:
        机会指数 [0, 1]，越高机会越大
    """
    opportunity = 0.0
    
    # 1. 趋势强度（权重0.4）
    trend_slope = abs(macro_features.get('trend_slope', 0.0))
    # 0 → 0分，5% → 满分
    trend_score = min(trend_slope / 0.05, 1.0)
    opportunity += 0.4 * trend_score
    
    # 2. 成交量比率（权重0.3）
    adv_ratio = macro_features.get('adv_ratio', 1.0)
    # 1.0 → 0分，2.0以上 → 满分
    if adv_ratio > 2.0:
        volume_score = 1.0
    elif adv_ratio > 1.0:
        volume_score = (adv_ratio - 1.0) / 1.0
    else:
        volume_score = 0.0
    opportunity += 0.3 * volume_score
    
    # 3. 资金费率套利机会（权重0.2）
    funding = abs(macro_features.get('funding_rate', 0.0))
    # 0.05% → 0分，0.1%以上 → 满分
    if funding > 0.001:
        funding_score = 1.0
    elif funding > 0.0005:
        funding_score = (funding - 0.0005) / 0.0005
    else:
        funding_score = 0.0
    opportunity += 0.2 * funding_score
    
    # 4. 流动性（权重0.1）
    total_liq = micro_features.get('total_liquidity', 200000)
    # 流动性高 → 机会大（容易进出）
    # 200000 → 0分，1000000以上 → 满分
    if total_liq > 1000000:
        liquidity_score = 1.0
    elif total_liq > 200000:
        liquidity_score = (total_liq - 200000) / 800000
    else:
        liquidity_score = 0.0
    opportunity += 0.1 * liquidity_score
    
    return min(opportunity, 1.0)


def calculate_novelty_score(
    current_sig: 'WorldSignature_V2',
    historical_sigs: List['WorldSignature_V2'],
    window_size: int = 1000
) -> float:
    """
    计算新颖度
    
    NoveltyScore = 1 - max_similarity_to_history
    
    Args:
        current_sig: 当前签名
        historical_sigs: 历史签名列表
        window_size: 查找窗口大小
    
    Returns:
        新颖度 [0, 1]，越高越新颖
    """
    if len(historical_sigs) == 0:
        return 1.0  # 完全新颖（没有历史）
    
    # 导入相似度计算函数
    from .signature import calculate_similarity
    
    # 计算与历史的最大相似度
    max_similarity = 0.0
    
    # 只看最近window_size个
    recent_sigs = historical_sigs[-window_size:] if len(historical_sigs) > window_size else historical_sigs
    
    for hist_sig in recent_sigs:
        try:
            sim_result = calculate_similarity(current_sig, hist_sig)
            similarity = sim_result['overall']
            max_similarity = max(max_similarity, similarity)
        except Exception as e:
            logger.warning(f"相似度计算失败: {e}")
            continue
    
    # 新颖度 = 1 - 最大相似度
    novelty = 1 - max_similarity
    
    return novelty


def calculate_all_metrics(
    signature: 'WorldSignature_V2',
    regime_lib: 'RegimeLibrary' = None,
    recent_micro_vecs: List[np.ndarray] = None,
    historical_sigs: List['WorldSignature_V2'] = None
) -> Dict[str, float]:
    """
    一次性计算所有指标
    
    Args:
        signature: 当前签名
        regime_lib: Regime库
        recent_micro_vecs: 最近的微观向量
        historical_sigs: 历史签名
    
    Returns:
        所有指标字典
    """
    metrics = {}
    
    # 1. Regime置信度
    if regime_lib:
        metrics['regime_confidence'] = calculate_regime_confidence(signature, regime_lib)
    else:
        metrics['regime_confidence'] = 0.0
    
    # 2. 稳定度
    if recent_micro_vecs and len(recent_micro_vecs) > 1:
        metrics['stability_score'] = calculate_stability_score(recent_micro_vecs)
    else:
        metrics['stability_score'] = 0.5
    
    # 3. 危险指数
    metrics['danger_index'] = calculate_danger_index(signature.micro.raw_features)
    
    # 4. 机会指数
    metrics['opportunity_index'] = calculate_opportunity_index(
        signature.macro.raw_features,
        signature.micro.raw_features
    )
    
    # 5. 新颖度
    if historical_sigs:
        metrics['novelty_score'] = calculate_novelty_score(signature, historical_sigs)
    else:
        metrics['novelty_score'] = 1.0
    
    return metrics


def interpret_metrics(metrics: Dict[str, float]) -> str:
    """
    解释指标含义
    
    Args:
        metrics: 指标字典
    
    Returns:
        人类可读的解释
    """
    interpretation = []
    
    # Regime置信度
    conf = metrics.get('regime_confidence', 0.0)
    if conf > 0.8:
        interpretation.append(f"✅ 高置信度匹配到已知regime ({conf:.1%})")
    elif conf > 0.5:
        interpretation.append(f"⚠️  中等置信度匹配 ({conf:.1%})")
    else:
        interpretation.append(f"❓ 低置信度，可能是新regime ({conf:.1%})")
    
    # 稳定度
    stability = metrics.get('stability_score', 0.5)
    if stability > 0.8:
        interpretation.append(f"📊 市场非常稳定 ({stability:.1%})")
    elif stability > 0.5:
        interpretation.append(f"📊 市场中等稳定 ({stability:.1%})")
    else:
        interpretation.append(f"⚡ 市场波动剧烈 ({stability:.1%})")
    
    # 危险指数
    danger = metrics.get('danger_index', 0.0)
    if danger > 0.7:
        interpretation.append(f"🚨 高危险！建议谨慎 ({danger:.1%})")
    elif danger > 0.4:
        interpretation.append(f"⚠️  中等风险 ({danger:.1%})")
    else:
        interpretation.append(f"✅ 低风险环境 ({danger:.1%})")
    
    # 机会指数
    opportunity = metrics.get('opportunity_index', 0.5)
    if opportunity > 0.7:
        interpretation.append(f"🎯 高机会！可考虑增仓 ({opportunity:.1%})")
    elif opportunity > 0.4:
        interpretation.append(f"💡 中等机会 ({opportunity:.1%})")
    else:
        interpretation.append(f"😴 低机会，可观望 ({opportunity:.1%})")
    
    # 新颖度
    novelty = metrics.get('novelty_score', 0.0)
    if novelty > 0.85:
        interpretation.append(f"🆕 极度新颖！未见过的情况 ({novelty:.1%})")
    elif novelty > 0.6:
        interpretation.append(f"🆕 较新情况 ({novelty:.1%})")
    else:
        interpretation.append(f"📚 常见情况 ({novelty:.1%})")
    
    return "\n".join(interpretation)

