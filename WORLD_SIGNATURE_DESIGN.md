# 🌍 WorldSignature 设计文档

**设计日期**: 2025-12-06  
**目标版本**: v5.5  
**设计者**: Prometheus开发团队

---

## 📋 目录

1. [核心概念](#核心概念)
2. [设计目标](#设计目标)
3. [特征维度](#特征维度)
4. [编码算法](#编码算法)
5. [相似度计算](#相似度计算)
6. [数据结构](#数据结构)
7. [API设计](#api设计)
8. [使用场景](#使用场景)
9. [测试方案](#测试方案)
10. [未来扩展](#未来扩展)

---

## 🎯 核心概念

### 什么是WorldSignature？

**定义**: 市场世界的"指纹"或"DNA"，是对当前市场状态的唯一编码。

**类比**：
- **围棋**: 棋盘状态 → 局面编码 → AlphaZero识别相似局面
- **Prometheus**: 市场状态 → WorldSignature → 识别相似市场环境

**作用**：
```
当前市场状态
    ↓ 编码
WorldSignature: "BULL_HIGH_VOL_LIQUID_MOMENTUM_STRONG"
    ↓ 检索
历史最佳策略: [Gene1, Gene2, Gene3]
    ↓ 应用
Agent快速适配
```

---

## 🎯 设计目标

### 功能目标
1. ✅ **唯一性**: 相同市场 → 相同签名
2. ✅ **稳定性**: 微小波动 → 签名不变
3. ✅ **可比性**: 相似市场 → 相似签名
4. ✅ **可解释**: 签名 → 可理解的市场描述
5. ✅ **高效性**: 毫秒级编码速度

### 性能目标
- 编码速度: < 1ms
- 相似度计算: < 0.1ms
- 签名长度: < 100字符
- 特征维度: 10-20个

---

## 📊 特征维度

### 第1类：价格特征（Price Features）

#### 1.1 价格趋势（Price Trend）
```python
def calculate_price_trend(prices: List[float], window: int = 20) -> str:
    """
    计算价格趋势
    
    返回值:
        'STRONG_BULL'  : 涨幅 > 5%
        'BULL'         : 涨幅 1-5%
        'WEAK_BULL'    : 涨幅 0.1-1%
        'SIDEWAYS'     : 涨跌 < 0.1%
        'WEAK_BEAR'    : 跌幅 0.1-1%
        'BEAR'         : 跌幅 1-5%
        'STRONG_BEAR'  : 跌幅 > 5%
    """
    pass
```

**重要性**: ⭐⭐⭐⭐⭐（最重要）

---

#### 1.2 波动率（Volatility）
```python
def calculate_volatility(prices: List[float], window: int = 20) -> str:
    """
    计算波动率（标准差）
    
    返回值:
        'EXTREME_VOL'  : std > 3%
        'HIGH_VOL'     : std 1.5-3%
        'MEDIUM_VOL'   : std 0.5-1.5%
        'LOW_VOL'      : std < 0.5%
    """
    pass
```

**重要性**: ⭐⭐⭐⭐⭐

---

#### 1.3 价格位置（Price Position）
```python
def calculate_price_position(current: float, high: float, low: float) -> str:
    """
    当前价格在区间中的位置
    
    返回值:
        'TOP'     : > 80%
        'UPPER'   : 60-80%
        'MIDDLE'  : 40-60%
        'LOWER'   : 20-40%
        'BOTTOM'  : < 20%
    """
    position = (current - low) / (high - low)
    # ...
```

**重要性**: ⭐⭐⭐⭐

---

### 第2类：动量特征（Momentum Features）

#### 2.1 动量强度（Momentum Strength）
```python
def calculate_momentum(prices: List[float], window: int = 10) -> str:
    """
    计算动量（ROC: Rate of Change）
    
    返回值:
        'STRONG_UP'    : ROC > 2%
        'MEDIUM_UP'    : ROC 0.5-2%
        'WEAK_UP'      : ROC 0-0.5%
        'NEUTRAL'      : ROC ≈ 0
        'WEAK_DOWN'    : ROC -0.5-0
        'MEDIUM_DOWN'  : ROC -2--0.5%
        'STRONG_DOWN'  : ROC < -2%
    """
    pass
```

**重要性**: ⭐⭐⭐⭐⭐

---

#### 2.2 加速度（Acceleration）
```python
def calculate_acceleration(momentum: List[float]) -> str:
    """
    动量的变化率
    
    返回值:
        'ACCELERATING'  : 动量增强
        'STABLE'        : 动量稳定
        'DECELERATING'  : 动量减弱
    """
    pass
```

**重要性**: ⭐⭐⭐

---

### 第3类：成交量特征（Volume Features）

#### 3.1 成交量水平（Volume Level）
```python
def calculate_volume_level(volume: float, avg_volume: float) -> str:
    """
    相对平均成交量的水平
    
    返回值:
        'HUGE'     : > 2x平均
        'HIGH'     : 1.5-2x平均
        'NORMAL'   : 0.7-1.5x平均
        'LOW'      : < 0.7x平均
    """
    pass
```

**重要性**: ⭐⭐⭐⭐

---

#### 3.2 成交量趋势（Volume Trend）
```python
def calculate_volume_trend(volumes: List[float]) -> str:
    """
    成交量变化趋势
    
    返回值:
        'INCREASING'  : 成交量增加
        'STABLE'      : 成交量平稳
        'DECREASING'  : 成交量减少
    """
    pass
```

**重要性**: ⭐⭐⭐

---

### 第4类：市场微结构（Market Microstructure）

#### 4.1 买卖压力（Order Flow）
```python
def calculate_order_flow(bids: List, asks: List) -> str:
    """
    订单簿买卖压力
    
    返回值:
        'STRONG_BUY'   : 买单 >> 卖单
        'BUY_PRESSURE' : 买单 > 卖单
        'BALANCED'     : 买卖平衡
        'SELL_PRESSURE': 卖单 > 买单
        'STRONG_SELL'  : 卖单 >> 买单
    """
    pass
```

**重要性**: ⭐⭐⭐⭐

---

#### 4.2 流动性（Liquidity）
```python
def calculate_liquidity(orderbook_depth: float, spread: float) -> str:
    """
    市场流动性水平
    
    返回值:
        'DEEP'      : 深度大、价差小
        'NORMAL'    : 正常
        'THIN'      : 深度小、价差大
        'DRY'       : 流动性枯竭
    """
    pass
```

**重要性**: ⭐⭐⭐⭐⭐

---

#### 4.3 价差（Spread）
```python
def calculate_spread(bid: float, ask: float) -> str:
    """
    买卖价差
    
    返回值:
        'TIGHT'   : < 0.01%
        'NORMAL'  : 0.01-0.05%
        'WIDE'    : 0.05-0.1%
        'HUGE'    : > 0.1%
    """
    pass
```

**重要性**: ⭐⭐⭐

---

### 第5类：时间特征（Time Features）

#### 5.1 时间尺度（Timeframe）
```python
def get_timeframe() -> str:
    """
    当前分析的时间尺度
    
    返回值:
        'INTRADAY_1M'  : 1分钟
        'INTRADAY_5M'  : 5分钟
        'INTRADAY_1H'  : 1小时
        'DAILY'        : 日线
        'WEEKLY'       : 周线
    """
    pass
```

**重要性**: ⭐⭐⭐

---

#### 5.2 市场阶段（Market Phase）
```python
def calculate_market_phase(price_history: List[float]) -> str:
    """
    当前市场所处阶段
    
    返回值:
        'ACCUMULATION'  : 底部吸筹
        'MARKUP'        : 上升趋势
        'DISTRIBUTION'  : 顶部派发
        'MARKDOWN'      : 下降趋势
    """
    pass
```

**重要性**: ⭐⭐⭐⭐

---

### 第6类：高级特征（Advanced Features）

#### 6.1 市场情绪（Market Sentiment）
```python
def calculate_sentiment(fear_greed_index: float) -> str:
    """
    市场情绪指标
    
    返回值:
        'EXTREME_FEAR'   : < 20
        'FEAR'           : 20-40
        'NEUTRAL'        : 40-60
        'GREED'          : 60-80
        'EXTREME_GREED'  : > 80
    """
    pass
```

**重要性**: ⭐⭐⭐（可选）

---

#### 6.2 趋势强度（Trend Strength）
```python
def calculate_trend_strength(prices: List[float]) -> str:
    """
    趋势的强度（ADX等指标）
    
    返回值:
        'VERY_STRONG'  : ADX > 50
        'STRONG'       : ADX 25-50
        'WEAK'         : ADX < 25
        'NO_TREND'     : 无明显趋势
    """
    pass
```

**重要性**: ⭐⭐⭐⭐

---

## 🔧 编码算法

### 方案1: 分层编码（推荐）⭐⭐⭐⭐⭐

```python
class WorldSignature:
    """市场世界签名"""
    
    @staticmethod
    def encode(market_data: Dict) -> str:
        """
        编码市场状态
        
        格式: LAYER1_LAYER2_LAYER3_...
        
        示例: "BULL_HIGH_VOL_STRONG_UP_DEEP_LIQUID_MARKUP"
        """
        # Layer 1: 趋势（最重要）
        trend = calculate_price_trend(market_data['prices'])
        
        # Layer 2: 波动率
        volatility = calculate_volatility(market_data['prices'])
        
        # Layer 3: 动量
        momentum = calculate_momentum(market_data['prices'])
        
        # Layer 4: 流动性
        liquidity = calculate_liquidity(
            market_data['orderbook_depth'],
            market_data['spread']
        )
        
        # Layer 5: 市场阶段
        phase = calculate_market_phase(market_data['price_history'])
        
        # 组合成签名
        signature = f"{trend}_{volatility}_{momentum}_{liquidity}_{phase}"
        
        return signature
```

**优点**：
- ✅ 可读性强
- ✅ 易于扩展
- ✅ 层次清晰
- ✅ 可以灵活调整权重

---

### 方案2: 哈希编码（备选）

```python
@staticmethod
def encode_hash(market_data: Dict) -> str:
    """
    使用哈希编码（更紧凑）
    
    格式: 固定长度的哈希字符串
    示例: "A7F3E9D2B1C8"
    """
    features = extract_all_features(market_data)
    feature_vector = [quantize_feature(f) for f in features]
    hash_value = hashlib.md5(str(feature_vector).encode()).hexdigest()[:12]
    return hash_value
```

**优点**：
- ✅ 紧凑
- ✅ 固定长度

**缺点**：
- ❌ 不可读
- ❌ 难以调试

---

### 方案3: 向量编码（高级）

```python
@staticmethod
def encode_vector(market_data: Dict) -> np.ndarray:
    """
    编码为向量（用于机器学习）
    
    返回: [0.8, 0.3, 0.9, 0.1, ...]  # 归一化特征向量
    """
    features = {
        'trend': normalize(calculate_price_trend(...)),
        'volatility': normalize(calculate_volatility(...)),
        'momentum': normalize(calculate_momentum(...)),
        # ...
    }
    return np.array(list(features.values()))
```

**优点**：
- ✅ 可以用余弦相似度
- ✅ 支持机器学习

**缺点**：
- ❌ 计算开销大
- ❌ 存储开销大

---

## 📏 相似度计算

### 方案1: 编辑距离（Levenshtein Distance）

```python
@staticmethod
def similarity_levenshtein(sig1: str, sig2: str) -> float:
    """
    基于编辑距离的相似度
    
    返回: 0.0-1.0之间的相似度
    
    示例:
        sig1 = "BULL_HIGH_VOL_STRONG_UP"
        sig2 = "BULL_HIGH_VOL_MEDIUM_UP"
        相似度 ≈ 0.85
    """
    distance = levenshtein_distance(sig1, sig2)
    max_len = max(len(sig1), len(sig2))
    similarity = 1 - (distance / max_len)
    return similarity
```

**优点**：
- ✅ 简单直观
- ✅ 计算快速

---

### 方案2: 层级匹配（推荐）⭐⭐⭐⭐⭐

```python
@staticmethod
def similarity_hierarchical(sig1: str, sig2: str) -> float:
    """
    层级匹配相似度（考虑不同层的权重）
    
    示例:
        sig1 = "BULL_HIGH_VOL_STRONG_UP_DEEP"
        sig2 = "BULL_HIGH_VOL_MEDIUM_UP_NORMAL"
        
        匹配:
        Layer 1 (趋势): BULL == BULL ✓ (权重: 0.4)
        Layer 2 (波动): HIGH_VOL == HIGH_VOL ✓ (权重: 0.2)
        Layer 3 (动量): STRONG_UP != MEDIUM_UP ✗ (权重: 0.2)
        Layer 4 (流动性): DEEP != NORMAL ✗ (权重: 0.1)
        
        相似度 = 0.4 + 0.2 = 0.6
    """
    layers1 = sig1.split('_')
    layers2 = sig2.split('_')
    
    # 层级权重（趋势最重要）
    weights = [0.4, 0.2, 0.2, 0.1, 0.1]
    
    similarity = 0.0
    for i, (l1, l2) in enumerate(zip(layers1, layers2)):
        if l1 == l2:
            similarity += weights[i] if i < len(weights) else 0.05
    
    return similarity
```

**优点**：
- ✅ 考虑层级权重
- ✅ 趋势匹配更重要
- ✅ 灵活可调

---

### 方案3: 余弦相似度（用于向量）

```python
@staticmethod
def similarity_cosine(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    余弦相似度（用于向量编码）
    
    返回: 0.0-1.0之间的相似度
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)
```

---

## 🗄️ 数据结构

### 核心类

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

@dataclass
class MarketFeatures:
    """市场特征"""
    # 价格特征
    price_trend: str          # 价格趋势
    volatility: str           # 波动率
    price_position: str       # 价格位置
    
    # 动量特征
    momentum: str             # 动量强度
    acceleration: str         # 加速度
    
    # 成交量特征
    volume_level: str         # 成交量水平
    volume_trend: str         # 成交量趋势
    
    # 微结构特征
    order_flow: str           # 买卖压力
    liquidity: str            # 流动性
    spread: str               # 价差
    
    # 时间特征
    timeframe: str            # 时间尺度
    market_phase: str         # 市场阶段
    
    # 高级特征（可选）
    sentiment: Optional[str] = None    # 市场情绪
    trend_strength: Optional[str] = None  # 趋势强度


@dataclass
class WorldSignature:
    """世界签名"""
    signature: str            # 签名字符串
    features: MarketFeatures  # 原始特征
    timestamp: float          # 时间戳
    metadata: Dict            # 元数据
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'signature': self.signature,
            'features': self.features.__dict__,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """从字典创建"""
        features = MarketFeatures(**data['features'])
        return cls(
            signature=data['signature'],
            features=features,
            timestamp=data['timestamp'],
            metadata=data['metadata']
        )


class SignatureEncoder:
    """签名编码器"""
    
    def __init__(self, encoding_method: str = 'hierarchical'):
        """
        初始化编码器
        
        Args:
            encoding_method: 'hierarchical', 'hash', 'vector'
        """
        self.encoding_method = encoding_method
    
    def encode(self, market_data: Dict) -> WorldSignature:
        """
        编码市场数据
        
        Args:
            market_data: {
                'prices': [float],
                'volumes': [float],
                'orderbook': {...},
                ...
            }
        
        Returns:
            WorldSignature对象
        """
        # 1. 提取特征
        features = self._extract_features(market_data)
        
        # 2. 生成签名
        if self.encoding_method == 'hierarchical':
            signature = self._encode_hierarchical(features)
        elif self.encoding_method == 'hash':
            signature = self._encode_hash(features)
        elif self.encoding_method == 'vector':
            signature = self._encode_vector(features)
        else:
            raise ValueError(f"Unknown encoding method: {self.encoding_method}")
        
        # 3. 创建WorldSignature对象
        return WorldSignature(
            signature=signature,
            features=features,
            timestamp=time.time(),
            metadata={'method': self.encoding_method}
        )
    
    def similarity(self, sig1: WorldSignature, sig2: WorldSignature) -> float:
        """
        计算两个签名的相似度
        
        Returns:
            0.0-1.0之间的相似度分数
        """
        if self.encoding_method == 'hierarchical':
            return self._similarity_hierarchical(sig1.signature, sig2.signature)
        elif self.encoding_method == 'hash':
            return self._similarity_levenshtein(sig1.signature, sig2.signature)
        elif self.encoding_method == 'vector':
            vec1 = self._signature_to_vector(sig1)
            vec2 = self._signature_to_vector(sig2)
            return self._similarity_cosine(vec1, vec2)
    
    def _extract_features(self, market_data: Dict) -> MarketFeatures:
        """提取所有特征"""
        # TODO: 实现特征提取
        pass
    
    def _encode_hierarchical(self, features: MarketFeatures) -> str:
        """层级编码"""
        # TODO: 实现
        pass
    
    # ... 其他方法
```

---

## 📚 API设计

### 使用示例

```python
# 1. 创建编码器
encoder = SignatureEncoder(encoding_method='hierarchical')

# 2. 编码当前市场状态
market_data = {
    'prices': [89000, 89100, 89200, ...],
    'volumes': [1000, 1100, 950, ...],
    'orderbook': {
        'bids': [[89650, 10], [89649, 5], ...],
        'asks': [[89651, 8], [89652, 12], ...]
    }
}

current_signature = encoder.encode(market_data)
print(current_signature.signature)
# 输出: "BULL_HIGH_VOL_STRONG_UP_DEEP_MARKUP"

# 3. 查找相似的历史签名
historical_signatures = load_historical_signatures()

similar_sigs = []
for hist_sig in historical_signatures:
    similarity = encoder.similarity(current_signature, hist_sig)
    if similarity > 0.7:  # 相似度阈值
        similar_sigs.append((hist_sig, similarity))

# 4. 检索最佳策略
best_genes = []
for sig, score in sorted(similar_sigs, key=lambda x: x[1], reverse=True)[:5]:
    genes = knowledge_base.get_best_genes(sig.signature)
    best_genes.extend(genes)

# 5. 应用策略到Agent
agent.apply_historical_genes(best_genes)
```

---

## 🎯 使用场景

### 场景1: Mock训练学校

```python
# 训练器根据签名生成训练场景
training_signature = "SIDEWAYS_HIGH_VOL_WEAK_UP_THIN"
mock_market.generate_scenario_from_signature(training_signature)

# Agent在该场景下训练
for step in range(1000):
    agent.trade(mock_market)
    performance = evaluate(agent)
    
    # 记录该签名下的表现
    knowledge_base.record_performance(
        signature=training_signature,
        agent=agent,
        performance=performance
    )
```

---

### 场景2: 实时策略检索

```python
# 每个交易周期
current_signature = encoder.encode(get_current_market_data())

# 检索历史最佳策略
best_genes = knowledge_base.get_best_genes(current_signature.signature)

# 动态调整Agent策略
for agent in agents:
    if len(best_genes) > 0:
        agent.blend_genes(best_genes)  # 混合历史最优基因
```

---

### 场景3: 市场分类统计

```python
# 分析历史数据，统计各种签名的出现频率
signature_stats = {}

for historical_data in load_all_historical_data():
    sig = encoder.encode(historical_data)
    if sig.signature not in signature_stats:
        signature_stats[sig.signature] = {
            'count': 0,
            'avg_return': 0,
            'best_strategy': None
        }
    signature_stats[sig.signature]['count'] += 1
    # ...

# 输出报告
print("市场签名统计:")
for sig, stats in sorted(signature_stats.items(), key=lambda x: x[1]['count'], reverse=True):
    print(f"{sig}: 出现{stats['count']}次, 平均回报{stats['avg_return']:.2%}")
```

---

## 🧪 测试方案

### 测试1: 唯一性测试

```python
def test_uniqueness():
    """相同市场应该生成相同签名"""
    market_data = generate_test_market_data()
    
    sig1 = encoder.encode(market_data)
    sig2 = encoder.encode(market_data)
    
    assert sig1.signature == sig2.signature
    print("✅ 唯一性测试通过")
```

---

### 测试2: 稳定性测试

```python
def test_stability():
    """微小变化不应该改变签名"""
    market_data = generate_test_market_data()
    sig1 = encoder.encode(market_data)
    
    # 添加1%的噪声
    market_data_noisy = add_noise(market_data, noise_level=0.01)
    sig2 = encoder.encode(market_data_noisy)
    
    # 签名应该相同或高度相似
    similarity = encoder.similarity(sig1, sig2)
    assert similarity > 0.95
    print("✅ 稳定性测试通过")
```

---

### 测试3: 可比性测试

```python
def test_comparability():
    """相似市场应该有相似签名"""
    # 生成两个相似的市场（都是牛市、高波动）
    market1 = generate_bull_market(volatility='high')
    market2 = generate_bull_market(volatility='high')
    
    sig1 = encoder.encode(market1)
    sig2 = encoder.encode(market2)
    
    similarity = encoder.similarity(sig1, sig2)
    assert similarity > 0.7
    print(f"✅ 可比性测试通过 (相似度: {similarity:.2f})")
```

---

### 测试4: 区分性测试

```python
def test_discrimination():
    """不同市场应该有不同签名"""
    bull_market = generate_bull_market()
    bear_market = generate_bear_market()
    
    sig_bull = encoder.encode(bull_market)
    sig_bear = encoder.encode(bear_market)
    
    similarity = encoder.similarity(sig_bull, sig_bear)
    assert similarity < 0.5
    print(f"✅ 区分性测试通过 (相似度: {similarity:.2f})")
```

---

### 测试5: 性能测试

```python
def test_performance():
    """编码速度测试"""
    market_data = generate_test_market_data()
    
    import time
    start = time.time()
    for _ in range(1000):
        sig = encoder.encode(market_data)
    end = time.time()
    
    avg_time = (end - start) / 1000
    assert avg_time < 0.001  # 应该 < 1ms
    print(f"✅ 性能测试通过 (平均编码时间: {avg_time*1000:.2f}ms)")
```

---

## 🚀 未来扩展

### v5.5: 基础实现
- ✅ 基本特征提取（10-15个特征）
- ✅ 层级编码
- ✅ 层级相似度计算
- ✅ 基础测试

### v6.0: Memory Layer集成
- 🎯 数据库存储（SQLite）
- 🎯 签名索引（快速检索）
- 🎯 情境化基因库
- 🎯 自动学习（元学习）

### v7.0: 机器学习增强
- 🎯 向量编码
- 🎯 深度学习特征提取
- 🎯 自适应特征权重
- 🎯 端到端学习

---

## 📊 实现计划

### Day 1: 核心框架（明天上午）
- [ ] 创建基础类结构
- [ ] 实现MarketFeatures数据类
- [ ] 实现WorldSignature数据类
- [ ] 实现SignatureEncoder框架

### Day 1: 特征提取（明天下午）
- [ ] 实现price_trend计算
- [ ] 实现volatility计算
- [ ] 实现momentum计算
- [ ] 实现liquidity计算
- [ ] 实现market_phase计算

### Day 2: 编码和相似度（后天上午）
- [ ] 实现hierarchical编码
- [ ] 实现hierarchical相似度计算
- [ ] 单元测试

### Day 2: 集成测试（后天下午）
- [ ] 完整测试套件
- [ ] 性能优化
- [ ] 文档完善

### Day 3: Mock集成
- [ ] 集成到Mock训练系统
- [ ] 实战测试
- [ ] 调优

---

## 📝 总结

### 核心设计决策

1. **编码方法**: 层级编码（可读性 + 灵活性）⭐
2. **特征维度**: 10-15个核心特征
3. **相似度算法**: 层级匹配（考虑权重）⭐
4. **数据结构**: 明确的dataclass（类型安全）

### 关键优势

- ✅ 可读性强: "BULL_HIGH_VOL_STRONG_UP"一目了然
- ✅ 可扩展: 轻松添加新特征
- ✅ 高效: 毫秒级编码
- ✅ 灵活: 支持多种编码方法

### 预期效果

1. **v5.5**: Mock训练学校的基石
2. **v6.0**: Memory Layer的核心
3. **长期**: 实现"越用越聪明"的系统

---

**设计完成！明天开始实现！** 🚀

---

**最后更新**: 2025-12-06 23:30  
**下一步**: 实现核心框架（明天）

