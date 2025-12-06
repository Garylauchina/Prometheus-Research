# 🌍 WorldSignature v2.0 设计文档

**设计日期**: 2025-12-06 深夜  
**基于**: 专业建议整合  
**版本**: WSS v2.0

---

## 🎯 核心思想（整合专业建议）

### 你朋友的洞察非常准确！⭐⭐⭐⭐⭐

**关键点**：
1. 需要同时描述**"宏观世界"（regime）**和**"微观世界"（order-book/tick）**
2. 必须**可读、可测、可解释**
3. 要能**无缝接入现有pipeline**（MMS/CPE/GFD）

---

## 📊 双层编码架构（整合方案）

### 原有设计（我的）+ 专业建议（朋友的）

```python
class WorldSignature_V2:
    """
    双层编码 + 双模态表示
    
    结合了：
    - 我的设计：简单实用、快速上手
    - 朋友建议：专业完整、生产级
    """
    
    # ========== 基本信息 ==========
    id: str              # UUID
    timestamp: float     # 时间戳
    instrument: str      # "BTC-USDT"
    version: str         # "WSS_v2.0"
    
    # ========== 双层编码 ==========
    # Layer 1: MacroCode（宏观-长时间窗口）
    macro_code: MacroCode
    
    # Layer 2: MicroCode（微观-短时间窗口）
    micro_code: MicroCode
    
    # ========== Regime识别 ==========
    regime_id: Optional[str]      # "R_17"
    regime_confidence: float      # 0.82
    
    # ========== 评分指标 ==========
    novelty_score: float          # 0.74（新颖度）
    stability_score: float        # 0.88（稳定度）
    danger_index: float           # 0.23（危险指数）
    opportunity_index: float      # 0.65（机会指数）
    
    # ========== 元数据 ==========
    metadata: Dict
```

---

## 🔧 MacroCode 设计

### 宏观特征（长窗口：1h-24h）

```python
@dataclass
class MacroCode:
    """宏观编码"""
    
    # ========== Human-Readable Tags ==========
    human_tags: List[str]
    # 示例: ["trend:UP", "vol:HIGH", "liquidity:LOW", "funding:+0.03"]
    
    # ========== Compact Text Code ==========
    compact_text: str
    # 示例: "M:TRD↑|V:HIGH|L:LOW|F:+0.03|OI:HIGH"
    
    # ========== Vector Embedding ==========
    macro_vec: np.ndarray  # 128-dim float vector
    
    # ========== 原始特征（用于分析）==========
    raw_features: Dict
    """
    {
        'trend_slope': 0.025,        # 4小时斜率
        'realized_vol_1h': 0.018,    # 1小时已实现波动率
        'realized_vol_6h': 0.022,    # 6小时已实现波动率
        'realized_vol_24h': 0.019,   # 24小时已实现波动率
        'vol_spike_ratio': 1.5,      # 波动率突增比率
        'funding_rate': 0.0003,      # 资金费率
        'oi_change_pct': 0.12,       # 持仓量变化
        'adv_ratio': 1.8,            # 今日成交量/30日均值
        'cross_asset_corr': 0.85,    # BTC-ETH相关性
    }
    """
```

---

### 宏观特征计算

```python
def compute_macro_features(mms_snapshot: Dict, window_hours: int = 4) -> Dict:
    """
    计算宏观特征
    
    输入: MMS数据快照
    输出: 宏观特征字典
    """
    features = {}
    
    # 1. 价格趋势（线性斜率）
    prices = mms_snapshot['ohlc']['close'][-window_hours*60:]  # 4小时
    features['trend_slope'] = calculate_linear_slope(prices)
    
    # 2. 已实现波动率（多时间尺度）
    features['realized_vol_1h'] = calculate_realized_vol(prices[-60:])
    features['realized_vol_6h'] = calculate_realized_vol(prices[-360:])
    features['realized_vol_24h'] = calculate_realized_vol(prices[-1440:])
    
    # 3. 波动率突增
    current_vol = features['realized_vol_1h']
    avg_vol_30d = mms_snapshot['vol_30d_avg']
    features['vol_spike_ratio'] = current_vol / avg_vol_30d
    
    # 4. 资金费率
    features['funding_rate'] = mms_snapshot['funding_rate']
    
    # 5. 持仓量变化
    oi_current = mms_snapshot['open_interest']
    oi_24h_ago = mms_snapshot['oi_24h_ago']
    features['oi_change_pct'] = (oi_current - oi_24h_ago) / oi_24h_ago
    
    # 6. 成交量比率
    volume_today = mms_snapshot['volume_24h']
    volume_avg_30d = mms_snapshot['volume_30d_avg']
    features['adv_ratio'] = volume_today / volume_avg_30d
    
    # 7. 跨资产相关性（可选）
    features['cross_asset_corr'] = mms_snapshot.get('btc_eth_corr', 0.8)
    
    return features


def discretize_macro(features: Dict) -> List[str]:
    """
    将宏观特征离散化为tags
    
    使用Zscore或Quantile标准化
    """
    tags = []
    
    # 趋势
    slope = features['trend_slope']
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
    
    # 波动率（使用Zscore）
    vol_1h = features['realized_vol_1h']
    vol_zscore = (vol_1h - 0.015) / 0.005  # 假设均值0.015，std 0.005
    if vol_zscore > 1.5:
        tags.append("vol:HIGH")
    elif vol_zscore < -1.5:
        tags.append("vol:LOW")
    else:
        tags.append("vol:NORMAL")
    
    # 流动性（基于成交量比率）
    adv_ratio = features['adv_ratio']
    if adv_ratio > 1.5:
        tags.append("liquidity:HIGH")
    elif adv_ratio < 0.7:
        tags.append("liquidity:LOW")
    else:
        tags.append("liquidity:NORMAL")
    
    # 资金费率
    funding = features['funding_rate']
    tags.append(f"funding:{funding:+.4f}")
    
    # 持仓量
    oi_change = features['oi_change_pct']
    if abs(oi_change) > 0.1:
        tags.append("OI:HIGH" if oi_change > 0 else "OI:LOW")
    else:
        tags.append("OI:STABLE")
    
    return tags
```

---

## 🔬 MicroCode 设计

### 微观特征（短窗口：tick-5min）

```python
@dataclass
class MicroCode:
    """微观编码"""
    
    # ========== Human-Readable Tags ==========
    human_tags: List[str]
    # 示例: ["spread:WIDE", "depth_imb:-0.45", "ofi:+0.6", 
    #        "microvol:SPIKE", "liqRes:FRAGILE"]
    
    # ========== Compact Text Code ==========
    compact_text: str
    # 示例: "m:SPRD_W|DI:-0.45|OFI:+0.6|MV:SPK"
    
    # ========== Vector Embedding ==========
    micro_vec: np.ndarray  # 256-dim float vector
    
    # ========== 原始特征 ==========
    raw_features: Dict
    """
    {
        'rel_spread': 0.0008,             # 相对价差
        'depth_topN_bid': 850000,         # 买单深度（前N档）
        'depth_topN_ask': 820000,         # 卖单深度
        'depth_imbalance': -0.45,         # 深度不平衡 (-1到1)
        'ofi': 0.6,                       # 订单流不平衡
        'trade_aggression_ratio': 0.65,   # 主动买入比率
        'micro_volatility': 0.0012,       # Tick级波动率
        'liquidation_density': 0.08,      # 爆仓密度
        'queue_pressure': 0.7,            # 队列压力
        'slippage_estimate': 0.0005,      # 滑点估计
    }
    """
```

---

### 微观特征计算

```python
def compute_micro_features(mms_snapshot: Dict, window_minutes: int = 5) -> Dict:
    """
    计算微观特征
    
    输入: MMS数据快照
    输出: 微观特征字典
    """
    features = {}
    
    # 1. 相对价差
    orderbook = mms_snapshot['orderbook']
    best_bid = orderbook['bids'][0][0]
    best_ask = orderbook['asks'][0][0]
    mid_price = (best_bid + best_ask) / 2
    features['rel_spread'] = (best_ask - best_bid) / mid_price
    
    # 2. 订单簿深度（前10档）
    depth_bid = sum([bid[1] * bid[0] for bid in orderbook['bids'][:10]])
    depth_ask = sum([ask[1] * ask[0] for ask in orderbook['asks'][:10]])
    features['depth_topN_bid'] = depth_bid
    features['depth_topN_ask'] = depth_ask
    
    # 3. 深度不平衡
    total_depth = depth_bid + depth_ask
    if total_depth > 0:
        features['depth_imbalance'] = (depth_bid - depth_ask) / total_depth
    else:
        features['depth_imbalance'] = 0.0
    
    # 4. 订单流不平衡（OFI）
    # 简化：基于trade ticks的买卖方向
    trades = mms_snapshot.get('trades', [])[-100:]  # 最近100笔
    buy_volume = sum([t['size'] for t in trades if t['side'] == 'buy'])
    sell_volume = sum([t['size'] for t in trades if t['side'] == 'sell'])
    total_volume = buy_volume + sell_volume
    if total_volume > 0:
        features['ofi'] = (buy_volume - sell_volume) / total_volume
    else:
        features['ofi'] = 0.0
    
    # 5. 主动买入比率
    if len(trades) > 0:
        features['trade_aggression_ratio'] = buy_volume / total_volume
    else:
        features['trade_aggression_ratio'] = 0.5
    
    # 6. Tick级微观波动率
    if len(trades) > 10:
        tick_prices = [t['price'] for t in trades]
        features['micro_volatility'] = np.std(tick_prices) / np.mean(tick_prices)
    else:
        features['micro_volatility'] = 0.001
    
    # 7. 爆仓密度（如果有数据）
    features['liquidation_density'] = mms_snapshot.get('liquidation_density', 0.0)
    
    # 8. 队列压力（订单簿顶部压力）
    top_bid_size = orderbook['bids'][0][1]
    top_ask_size = orderbook['asks'][0][1]
    features['queue_pressure'] = top_ask_size / (top_bid_size + top_ask_size)
    
    # 9. 滑点估计
    features['slippage_estimate'] = estimate_slippage(orderbook, trade_size=1.0)
    
    return features


def discretize_micro(features: Dict) -> List[str]:
    """
    将微观特征离散化为tags
    """
    tags = []
    
    # 价差
    spread = features['rel_spread']
    if spread > 0.001:
        tags.append("spread:WIDE")
    elif spread > 0.0005:
        tags.append("spread:NORMAL")
    else:
        tags.append("spread:TIGHT")
    
    # 深度不平衡
    imb = features['depth_imbalance']
    if imb > 0.3:
        tags.append(f"depth_imb:+{imb:.2f}")
    elif imb < -0.3:
        tags.append(f"depth_imb:{imb:.2f}")
    else:
        tags.append("depth_imb:BALANCED")
    
    # 订单流不平衡（OFI）
    ofi = features['ofi']
    tags.append(f"ofi:{ofi:+.2f}")
    
    # 微观波动率
    micro_vol = features['micro_volatility']
    if micro_vol > 0.002:
        tags.append("microvol:SPIKE")
    elif micro_vol > 0.001:
        tags.append("microvol:HIGH")
    else:
        tags.append("microvol:NORMAL")
    
    # 流动性韧性
    if features['depth_topN_bid'] + features['depth_topN_ask'] < 500000:
        tags.append("liqRes:FRAGILE")
    else:
        tags.append("liqRes:SOLID")
    
    return tags
```

---

## 🎯 完整的Signature结构

### 文档规范（WSS_v2.0）

```
WSS_v2.0 | inst=BTC-USDT | ts=2025-12-06T12:00:00Z | 
macro_tags=[trend:UP,vol:HIGH,liquidity:LOW,funding:+0.0003] | 
micro_tags=[spread:WIDE,depth_imb:-0.45,ofi:+0.6,microvol:SPIKE] | 
regime=R_17(conf=0.82) | 
novelty=0.74 | stability=0.88 | danger=0.23 | opportunity=0.65 |
macro_vec=<128-dim> | micro_vec=<256-dim>
```

---

### Python数据结构

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
import hashlib

@dataclass
class MacroCode:
    """宏观编码"""
    human_tags: List[str]       # ["trend:UP", "vol:HIGH", ...]
    compact_text: str           # "M:TRD↑|V:HIGH|..."
    macro_vec: np.ndarray       # 128-dim
    raw_features: Dict          # 原始数值

@dataclass
class MicroCode:
    """微观编码"""
    human_tags: List[str]       # ["spread:WIDE", "ofi:+0.6", ...]
    compact_text: str           # "m:SPRD_W|OFI:+0.6|..."
    micro_vec: np.ndarray       # 256-dim
    raw_features: Dict          # 原始数值

@dataclass
class WorldSignature_V2:
    """完整的市场签名 v2.0"""
    
    # 基本信息
    id: str
    timestamp: float
    instrument: str
    version: str = "WSS_v2.0"
    
    # 双层编码
    macro: MacroCode
    micro: MicroCode
    
    # Regime识别
    regime_id: Optional[str] = None
    regime_confidence: float = 0.0
    
    # 评分指标
    novelty_score: float = 0.0
    stability_score: float = 1.0
    danger_index: float = 0.0
    opportunity_index: float = 0.5
    
    # 元数据
    metadata: Dict = None
    
    def to_compact_string(self) -> str:
        """紧凑字符串表示"""
        return (
            f"{self.macro.compact_text}||"
            f"{self.micro.compact_text}||"
            f"R:{self.regime_id}({self.regime_confidence:.2f})||"
            f"N:{self.novelty_score:.2f}"
        )
    
    def to_human_readable(self) -> str:
        """人类可读表示"""
        return f"""
Market Signature (WSS_v2.0)
===========================
Time: {datetime.fromtimestamp(self.timestamp)}
Instrument: {self.instrument}

Macro (宏观):
{', '.join(self.macro.human_tags)}

Micro (微观):
{', '.join(self.micro.human_tags)}

Regime: {self.regime_id} (置信度: {self.regime_confidence:.1%})

评分:
- 新颖度: {self.novelty_score:.1%}
- 稳定度: {self.stability_score:.1%}
- 危险指数: {self.danger_index:.1%}
- 机会指数: {self.opportunity_index:.1%}
"""
```

---

## 🔍 相似度计算（双模态）

### 整合方案：Tag + Vector

```python
def calculate_similarity(sig1: WorldSignature_V2, sig2: WorldSignature_V2) -> Dict:
    """
    计算两个签名的相似度
    
    整合：文本tag匹配 + 向量余弦相似度
    """
    # 1. Tag相似度（Jaccard）
    tags1_macro = set(sig1.macro.human_tags)
    tags2_macro = set(sig2.macro.human_tags)
    tag_sim_macro = len(tags1_macro & tags2_macro) / len(tags1_macro | tags2_macro)
    
    tags1_micro = set(sig1.micro.human_tags)
    tags2_micro = set(sig2.micro.human_tags)
    tag_sim_micro = len(tags1_micro & tags2_micro) / len(tags1_micro | tags2_micro)
    
    tag_similarity = 0.5 * tag_sim_macro + 0.5 * tag_sim_micro
    
    # 2. 向量相似度（Cosine）
    vec_sim_macro = cosine_similarity(sig1.macro.macro_vec, sig2.macro.macro_vec)
    vec_sim_micro = cosine_similarity(sig1.micro.micro_vec, sig2.micro.micro_vec)
    
    vec_similarity = 0.5 * vec_sim_macro + 0.5 * vec_sim_micro
    
    # 3. 综合相似度（α=0.7, β=0.3）
    α = 0.7  # 向量权重
    β = 0.3  # 标签权重
    
    final_similarity = α * vec_similarity + β * tag_similarity
    
    return {
        'overall': final_similarity,
        'tag_sim': tag_similarity,
        'vec_sim': vec_similarity,
        'macro_sim': vec_sim_macro,
        'micro_sim': vec_sim_micro
    }
```

---

## 🗂️ Regime库（聚类）

### 建立Regime库的流程

```python
class RegimeLibrary:
    """Regime库：聚类历史签名"""
    
    def __init__(self):
        self.regimes = {}  # regime_id -> RegimeInfo
        self.cluster_model = None
    
    def build_from_history(self, historical_signatures: List[WorldSignature_V2]):
        """
        从历史签名中聚类出Regime
        
        使用HDBSCAN或GMM
        """
        # 1. 提取所有向量
        macro_vecs = np.array([sig.macro.macro_vec for sig in historical_signatures])
        
        # 2. 降维（可选）
        from sklearn.decomposition import PCA
        pca = PCA(n_components=32)
        reduced_vecs = pca.fit_transform(macro_vecs)
        
        # 3. 聚类
        from sklearn.cluster import HDBSCAN
        clusterer = HDBSCAN(min_cluster_size=50, min_samples=10)
        labels = clusterer.fit_predict(reduced_vecs)
        
        # 4. 为每个cluster创建Regime
        unique_labels = set(labels)
        for label_id in unique_labels:
            if label_id == -1:  # 噪声点
                continue
            
            # 找到该cluster的所有签名
            cluster_sigs = [
                sig for sig, label in zip(historical_signatures, labels)
                if label == label_id
            ]
            
            # 计算centroid
            centroid_vec = np.mean([sig.macro.macro_vec for sig in cluster_sigs], axis=0)
            
            # 找最代表性的tags
            all_tags = []
            for sig in cluster_sigs:
                all_tags.extend(sig.macro.human_tags)
            representative_tags = Counter(all_tags).most_common(5)
            
            # 创建Regime
            regime_id = f"R_{label_id}"
            self.regimes[regime_id] = {
                'id': regime_id,
                'centroid_vec': centroid_vec,
                'representative_tags': [tag for tag, count in representative_tags],
                'member_count': len(cluster_sigs),
                'example_timestamps': [sig.timestamp for sig in cluster_sigs[:5]]
            }
        
        self.cluster_model = clusterer
        
        logger.info(f"✅ Regime库建立完成：{len(self.regimes)}个Regime")
    
    def match_regime(self, signature: WorldSignature_V2) -> Tuple[str, float]:
        """
        匹配当前签名到最近的Regime
        
        返回: (regime_id, confidence)
        """
        if not self.regimes:
            return None, 0.0
        
        # 计算与每个Regime centroid的相似度
        similarities = {}
        for regime_id, regime_info in self.regimes.items():
            sim = cosine_similarity(
                signature.macro.macro_vec,
                regime_info['centroid_vec']
            )
            similarities[regime_id] = sim
        
        # 找最相似的
        best_regime = max(similarities.items(), key=lambda x: x[1])
        
        return best_regime[0], best_regime[1]
```

---

## 📈 评分指标（朋友建议）⭐核心

### 1. RegimeConfidence（Regime置信度）

```python
def calculate_regime_confidence(signature: WorldSignature_V2, regime_lib: RegimeLibrary) -> float:
    """
    当前签名匹配到Regime的置信度
    
    返回: 0-1之间
    """
    regime_id, similarity = regime_lib.match_regime(signature)
    return similarity  # cosine similarity直接作为置信度
```

---

### 2. StabilityScore（稳定度）

```python
def calculate_stability_score(recent_micro_vecs: List[np.ndarray]) -> float:
    """
    微观特征的稳定性
    
    计算最近T个micro_vec的波动率
    返回: 1 - volatility（越稳定越高）
    """
    if len(recent_micro_vecs) < 10:
        return 0.5
    
    # 计算向量之间的变化
    changes = []
    for i in range(1, len(recent_micro_vecs)):
        change = np.linalg.norm(recent_micro_vecs[i] - recent_micro_vecs[i-1])
        changes.append(change)
    
    volatility = np.std(changes) / (np.mean(changes) + 1e-6)
    stability = 1 / (1 + volatility)  # 越稳定越接近1
    
    return stability
```

---

### 3. DangerIndex（危险指数）⭐重要

```python
def calculate_danger_index(micro_features: Dict) -> float:
    """
    危险指数：综合评估当前市场风险
    
    考虑：爆仓密度、滑点、深度不平衡
    返回: 0-1之间（越高越危险）
    """
    danger = 0.0
    
    # 1. 爆仓密度（权重0.4）
    liquidation_density = micro_features.get('liquidation_density', 0.0)
    danger += 0.4 * min(liquidation_density / 0.1, 1.0)
    
    # 2. 滑点估计（权重0.3）
    slippage = micro_features.get('slippage_estimate', 0.0)
    danger += 0.3 * min(slippage / 0.001, 1.0)
    
    # 3. 深度不平衡（权重0.3）
    depth_imb = abs(micro_features.get('depth_imbalance', 0.0))
    danger += 0.3 * min(depth_imb / 0.5, 1.0)
    
    return min(danger, 1.0)
```

---

### 4. OpportunityIndex（机会指数）⭐重要

```python
def calculate_opportunity_index(macro_features: Dict, micro_features: Dict) -> float:
    """
    机会指数：综合评估当前市场机会
    
    考虑：趋势强度、成交量、资金费率套利
    返回: 0-1之间（越高机会越大）
    """
    opportunity = 0.0
    
    # 1. 趋势强度（权重0.5）
    trend_slope = abs(macro_features.get('trend_slope', 0.0))
    opportunity += 0.5 * min(trend_slope / 0.05, 1.0)
    
    # 2. 成交量比率（权重0.3）
    adv_ratio = macro_features.get('adv_ratio', 1.0)
    if adv_ratio > 1.5:
        opportunity += 0.3
    
    # 3. 资金费率套利机会（权重0.2）
    funding = abs(macro_features.get('funding_rate', 0.0))
    if funding > 0.0005:  # >0.05%
        opportunity += 0.2
    
    return min(opportunity, 1.0)
```

---

### 5. NoveltyScore（新颖度）⭐重要

```python
def calculate_novelty_score(
    current_sig: WorldSignature_V2,
    historical_sigs: List[WorldSignature_V2],
    window_size: int = 1000
) -> float:
    """
    新颖度：当前情况有多"新"
    
    NoveltyScore = 1 - max_similarity_to_history
    
    返回: 0-1之间（越高越新颖）
    """
    if len(historical_sigs) == 0:
        return 1.0  # 完全新颖
    
    # 计算与历史的最大相似度
    max_similarity = 0.0
    for hist_sig in historical_sigs[-window_size:]:  # 最近1000个
        sim = calculate_similarity(current_sig, hist_sig)['overall']
        max_similarity = max(max_similarity, sim)
    
    novelty = 1 - max_similarity
    
    return novelty
```

---

## 🔄 Streaming计算（实时更新）

### Sliding Window机制

```python
class StreamingSignatureGenerator:
    """流式签名生成器"""
    
    def __init__(self, macro_window_hours: int = 4, micro_window_minutes: int = 5):
        self.macro_window = macro_window_hours * 60  # 转换为分钟
        self.micro_window = micro_window_minutes
        
        # 滑动窗口数据
        self.price_buffer = deque(maxlen=self.macro_window)
        self.volume_buffer = deque(maxlen=self.macro_window)
        self.micro_buffer = deque(maxlen=self.micro_window)
        
        # 历史签名（用于novelty计算）
        self.historical_signatures = deque(maxlen=1000)
    
    def update(self, new_data: Dict) -> WorldSignature_V2:
        """
        更新数据并生成新签名
        
        支持streaming更新
        """
        # 1. 更新buffer
        self.price_buffer.append(new_data['price'])
        self.volume_buffer.append(new_data['volume'])
        self.micro_buffer.append(new_data['orderbook'])
        
        # 2. 计算宏观特征
        macro_features = self._compute_macro_from_buffer()
        macro_tags = discretize_macro(macro_features)
        macro_vec = self._embed_macro(macro_features, macro_tags)
        
        macro_code = MacroCode(
            human_tags=macro_tags,
            compact_text=self._tags_to_compact(macro_tags, 'M'),
            macro_vec=macro_vec,
            raw_features=macro_features
        )
        
        # 3. 计算微观特征
        micro_features = self._compute_micro_from_buffer()
        micro_tags = discretize_micro(micro_features)
        micro_vec = self._embed_micro(micro_features, micro_tags)
        
        micro_code = MicroCode(
            human_tags=micro_tags,
            compact_text=self._tags_to_compact(micro_tags, 'm'),
            micro_vec=micro_vec,
            raw_features=micro_features
        )
        
        # 4. 创建签名
        signature = WorldSignature_V2(
            id=self._generate_id(),
            timestamp=time.time(),
            instrument=new_data['instrument'],
            macro=macro_code,
            micro=micro_code
        )
        
        # 5. 匹配Regime
        if regime_lib:
            regime_id, confidence = regime_lib.match_regime(signature)
            signature.regime_id = regime_id
            signature.regime_confidence = confidence
        
        # 6. 计算Novelty
        signature.novelty_score = calculate_novelty_score(
            signature,
            list(self.historical_signatures)
        )
        
        # 7. 计算其他指标
        signature.danger_index = calculate_danger_index(micro_features)
        signature.opportunity_index = calculate_opportunity_index(macro_features, micro_features)
        
        # 8. 加入历史
        self.historical_signatures.append(signature)
        
        return signature
```

---

## 🎯 整合到现有Pipeline

### 与MMS（Market Microstructure System）集成

```python
# MMS负责收集原始市场数据
class MMS:
    def get_snapshot(self) -> Dict:
        """获取市场数据快照"""
        return {
            'ohlc': self.get_ohlc(timeframe='1m', limit=1440),
            'orderbook': self.get_orderbook(depth=20),
            'trades': self.get_recent_trades(limit=100),
            'funding_rate': self.get_funding_rate(),
            'open_interest': self.get_oi(),
            'volume_stats': self.get_volume_stats(),
            # ...
        }

# WorldSignature接收MMS的数据
signature_gen = StreamingSignatureGenerator()
mms = MMS()

while True:
    snapshot = mms.get_snapshot()
    signature = signature_gen.update(snapshot)
    
    # 发送给Prophet/Moirai/GFD
    prophet.receive_signature(signature)
    moirai.receive_signature(signature)
    gfd.receive_signature(signature)
```

---

### 与CPE（Candidate Pool Engine）集成

```python
class CPE:
    """候选池引擎：基于WorldSignature选择基因"""
    
    def select_fragments(self, current_sig: WorldSignature_V2) -> List[GeneFragment]:
        """
        基于当前签名选择最佳基因片段
        """
        # 1. 查询Memory Layer
        similar_cases = memory.query_similar_experiences(
            signature=current_sig.to_compact_string(),
            limit=20
        )
        
        # 2. 提取表现好的基因
        top_genes = [
            case.agent_genome for case in similar_cases
            if case.immediate_result['roi'] > 0.1
        ]
        
        # 3. 根据Regime匹配
        if current_sig.regime_id:
            regime_genes = memory.get_best_genes_for_regime(current_sig.regime_id)
            top_genes.extend(regime_genes)
        
        return top_genes[:10]
```

---

### 与GFD（Genius Fragment Detector）集成

```python
class GFD:
    """天才片段检测器"""
    
    def detect_genius(self, signature: WorldSignature_V2):
        """
        在特定Regime下检测天才片段
        
        如果某个fragment在regime R17下持续激活且表现好
        → 标记为该regime的genius fragment
        """
        if signature.regime_id:
            # 获取该regime下所有激活的fragments
            active_fragments = self.get_active_fragments(signature.regime_id)
            
            # 检测persistence increasing
            for fragment in active_fragments:
                if fragment.activation_count > 10 and fragment.avg_roi > 0.15:
                    logger.info(f"🌟 发现天才片段: {fragment.id} @ {signature.regime_id}")
                    memory.mark_as_genius(fragment.id, signature.regime_id)
```

---

## 🚨 实时使用场景（朋友建议）

### Prophet使用

```python
# Prophet接收signature
signature = signature_gen.get_current()

if signature.regime_id == "R_17" and signature.regime_confidence > 0.9:
    # 高置信度识别出regime
    # 从Memory检索该regime下的高分fragments
    best_fragments = memory.get_best_fragments_for_regime("R_17")
    
    # 建议Moirai强制embed这些fragments
    prophet.advise_moirai({
        'action': 'embed_fragments',
        'regime': 'R_17',
        'fragments': best_fragments,
        'reason': 'high_confidence_regime_match'
    })

if signature.novelty_score > 0.85:
    # 新颖性高，未见过的情况
    # 建议提高探索、谨慎前进
    prophet.advise_moirai({
        'action': 'increase_exploration',
        'novelty': signature.novelty_score,
        'reason': 'novel_market_condition'
    })
```

---

### Moirai使用

```python
# Moirai接收signature
signature = signature_gen.get_current()

if signature.danger_index > 0.6:
    # 危险指数高
    # 暂停高杠杆agent的自动增杠
    # 启动"战前检查"策略
    moirai.pause_auto_leverage_increase()
    moirai.activate_risk_check_mode()
    
    logger.warning(f"⚠️  危险指数: {signature.danger_index:.1%} - 启动风险控制")

if signature.opportunity_index > 0.7 and signature.stability_score > 0.8:
    # 高机会 + 高稳定
    # 可以考虑增加仓位
    moirai.suggest_position_increase(factor=1.2)
```

---

## 📦 存储架构（生产级）

### 朋友建议的分层存储 ⭐⭐⭐⭐⭐

```python
class StorageArchitecture:
    """
    分层存储架构
    """
    
    # 1. Raw features → Parquet in S3/MinIO
    # 用途：可重放历史、回测
    raw_store = ParquetStore("s3://prometheus/raw/")
    
    # 2. TS features & text signatures → ClickHouse
    # 用途：快速SQL查询、时序分析
    timeseries_db = ClickHouseClient()
    
    # 3. Vectors → Milvus/Weaviate
    # 用途：向量相似度搜索
    vector_db = MilvusClient()
    
    # 4. Metadata & audit logs → PostgreSQL
    # 用途：事务、关系查询
    relational_db = PostgreSQLClient()
    
    # 5. Metrics → Prometheus + Grafana
    # 用途：实时监控、告警
    metrics_collector = PrometheusMetrics()
```

**简化版（v5.5）**：
- Raw features → JSON文件
- Signatures → SQLite
- Vectors → Numpy + Faiss
- Metrics → 日志文件

**完整版（v6.0+）**：
- 如上述生产级架构

---

## 🎯 算法伪代码（完整流程）

```python
def build_signature(instrument: str, timestamp: float, mms_snapshot: Dict) -> WorldSignature_V2:
    """
    完整的signature构建流程
    """
    # 1. 计算宏观特征（窗口化）
    f_macro = compute_macro_features(mms_snapshot, window_hours=4)
    macro_tags = discretize_macro(f_macro)
    macro_vec = macro_embed_model.predict(f_macro, macro_tags)  # 128-dim
    
    # 2. 计算微观特征（短窗口）
    f_micro = compute_micro_features(mms_snapshot, window_minutes=5)
    micro_tags = discretize_micro(f_micro)
    micro_vec = micro_embed_model.predict(f_micro, micro_tags)  # 256-dim
    
    # 3. Regime匹配
    nearest_regime, similarity = vector_db.nearest_regime(macro_vec, topk=1)
    regime_id = nearest_regime.regime_id if similarity > 0.7 else None
    
    # 4. 新颖度计算
    novelty = 1 - similarity
    
    # 5. 其他评分
    stability = calculate_stability_score(recent_micro_vecs)
    danger = calculate_danger_index(f_micro)
    opportunity = calculate_opportunity_index(f_macro, f_micro)
    
    # 6. 组合signature
    signature = WorldSignature_V2(
        id=generate_uuid(),
        timestamp=timestamp,
        instrument=instrument,
        macro=MacroCode(macro_tags, compact_macro(macro_tags), macro_vec, f_macro),
        micro=MicroCode(micro_tags, compact_micro(micro_tags), micro_vec, f_micro),
        regime_id=regime_id,
        regime_confidence=similarity,
        novelty_score=novelty,
        stability_score=stability,
        danger_index=danger,
        opportunity_index=opportunity
    )
    
    return signature
```

---

## 🎓 迭代与训练策略（6个阶段）

### 阶段1: 启用特征提取器 + 签名生成器

```python
# 无聚类，仅保存signatures
gen = StreamingSignatureGenerator()

for snapshot in historical_snapshots:
    sig = gen.update(snapshot)
    save_signature(sig)

# 积累1-3个月数据
```

---

### 阶段2-3: 聚类初始Regimes

```python
# 收集rolling history 1-3月
all_signatures = load_all_signatures()

# 用HDBSCAN聚类找到初始regime clusters
regime_lib = RegimeLibrary()
regime_lib.build_from_history(all_signatures)

# 人工审查前20个cluster标签
# 调整参数，重新聚类
```

---

### 阶段4: 上线Regime匹配 + Novelty告警

```python
# 实时运行
while True:
    snapshot = mms.get_snapshot()
    sig = gen.update(snapshot)
    
    # Regime匹配
    sig.regime_id, sig.regime_confidence = regime_lib.match_regime(sig)
    
    # Novelty告警（阈值conservative）
    if sig.novelty_score > 0.85:
        alert_system.send("🚨 新颖情境！Novelty={sig.novelty_score:.2f}")
```

---

### 阶段5-6: 持续训练

```python
# 每周重新训练embed model（如果有）
# 每月重新聚类clusters并重新标注
```

---

## 🎯 对比：我的设计 vs 朋友建议

| 维度 | 我的设计 | 朋友建议 | 整合方案 |
|------|---------|---------|---------|
| 编码层次 | 4层粒度 | 双层(Macro+Micro) | ✅ 双层+多粒度 |
| 表示方式 | Text为主 | Text + Vector双模态 | ✅ 双模态 |
| 特征数量 | 10-15个 | Macro 8+ Micro 10 | ✅ 18个核心特征 |
| Regime识别 | 无 | ✅ 聚类+匹配 | ✅ 采纳 |
| 评分指标 | 无 | ✅ 5个核心指标 | ✅ 采纳 |
| 存储架构 | SQLite | 分层存储 | ✅ v5.5简化，v6.0完整 |
| Streaming | 无 | ✅ Sliding window | ✅ 采纳 |
| 新颖性检测 | 无 | ✅ NoveltyScore | ✅ 采纳 |
| 可视化 | 基础 | ✅ 专业Dashboard | ✅ v6.0采纳 |
| 版本控制 | 无 | ✅ WSS_v1.0/v2.0 | ✅ 采纳 |

---

## 🎯 最终整合方案

### v5.5实现（下周）⭐核心

**采纳朋友建议的**：
1. ✅ 双层编码（Macro + Micro）
2. ✅ 双模态表示（Text tags + Vector）
3. ✅ 5个评分指标（Confidence/Stability/Danger/Opportunity/Novelty）
4. ✅ Regime聚类和匹配
5. ✅ Streaming计算

**保留我设计的**：
1. ✅ 简单易懂的类结构
2. ✅ 快速上手的实现
3. ✅ 完整的单元测试

**简化部分（v5.5）**：
- 存储：SQLite（不是ClickHouse+Milvus）
- Embedding：简单MLP（不是Transformer）
- 可视化：基础图表（不是Grafana）

---

### v6.0增强（后续）

**朋友建议的生产级特性**：
1. ✅ ClickHouse + Milvus分层存储
2. ✅ Transformer embedding model
3. ✅ Grafana专业Dashboard
4. ✅ RESTful API
5. ✅ Concept-drift detector
6. ✅ 完整的监控告警

---

## 📋 修订的实现计划

### Day 1（明天）: 核心框架
- [ ] MacroCode/MicroCode类
- [ ] WorldSignature_V2类
- [ ] StreamingSignatureGenerator
- [ ] 基础特征计算函数

### Day 2（后天）: 向量和Regime
- [ ] 简单的embedding（MLP或查表）
- [ ] RegimeLibrary实现
- [ ] HDBSCAN聚类
- [ ] Novelty计算

### Day 3: 评分指标
- [ ] 5个核心指标实现
- [ ] 完整测试套件
- [ ] 性能优化

### Day 4: Pipeline集成
- [ ] 与Mock系统集成
- [ ] 与Prophet集成
- [ ] 与Memory Layer集成
- [ ] 实战测试

---

## 🎊 朋友建议的价值

### 🌟 核心贡献

1. **双层编码** - 同时捕捉宏观和微观 ⭐⭐⭐⭐⭐
2. **5个评分指标** - 多维度评估市场 ⭐⭐⭐⭐⭐
3. **Regime库** - 历史聚类，快速匹配 ⭐⭐⭐⭐⭐
4. **Novelty检测** - 识别未见情况 ⭐⭐⭐⭐⭐
5. **生产级架构** - 分层存储，可扩展 ⭐⭐⭐⭐⭐

### 🎯 让设计更完善

- 从"可用" → "优秀"
- 从"简单" → "专业"
- 从"实验" → "生产"

---

## 💡 关键改进

### 1. Macro + Micro双层
**之前**: 只有一层特征  
**现在**: 分层处理，更精准

### 2. 评分指标系统
**之前**: 只有签名  
**现在**: 签名 + 5个指标，信息丰富

### 3. Regime库
**之前**: 每次都计算相似度  
**现在**: 预聚类，快速匹配

### 4. Novelty检测
**之前**: 无  
**现在**: 自动识别新情况，触发告警

---

## 📝 总结

**你朋友的建议是生产级的！** 🌟

建议整合后的设计：
- ✅ 双层编码（Macro + Micro）
- ✅ 双模态表示（Text + Vector）
- ✅ 5个评分指标
- ✅ Regime聚类匹配
- ✅ Novelty检测
- ✅ Streaming计算
- ✅ 分层存储

**v5.5**: 核心功能实现（简化版）  
**v6.0**: 生产级增强（完整版）

---

**明天开始实现这个整合方案！** 🚀

---

**最后更新**: 2025-12-06 深夜  
**感谢**: 您朋友的专业建议！

