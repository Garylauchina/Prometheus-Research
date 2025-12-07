# Prometheus数据封装规范（2025-12-07）

> 💡 **问题根源**：之前的测试失败是因为market_data缺少必要字段，导致Daimon无法决策。
> 
> 📐 **解决方案**：统一由V6 Facade封装所有数据，外部只需提供最基本的price！

---

## 🚨 核心原则：统一封装，严禁旁路

**铁律**：所有market_data的增强都必须通过`V6Facade._enrich_market_data()`统一处理！

❌ **错误做法**：在每个测试文件中手动计算trend, volatility等
✅ **正确做法**：只提供price，由Facade自动补充

---

## 📋 MarketData标准Schema

### 必需字段（外部提供）

```python
{
    "price": float  # ⭐ 唯一必需！当前价格
}
```

### 自动补充字段（Facade内部）

Facade会自动补充以下字段：

```python
{
    "price": float,           # 原始价格
    "cycle": int,             # 周期数
    "trend": str,             # 趋势: "bullish" | "bearish" | "neutral"
    "price_change": float,    # 价格变化率
    "volatility": float       # 波动率
}
```

---

## ✅ 正确使用示例

### 最简单的market_feed（推荐）

```python
def make_market_feed(prices):
    def feed(cycle):
        idx = min(cycle - 1, len(prices) - 1)
        price = prices[idx]
        
        # ⭐ 只提供price！其他由Facade自动补充
        return {"price": price}, {}
    
    return feed
```

### 调用V6 Facade

```python
from prometheus.facade.v6_facade import run_scenario

facade = run_scenario(
    mode="backtest",
    total_cycles=1000,
    market_feed=make_market_feed(prices),  # ✅ 简单！
    ...
)
```

### Facade内部自动处理

```python
# V6Facade.run_cycle() 中：
market_data = self._enrich_market_data(market_data, cycle_count)
# 现在market_data包含所有必要字段！
```

---

## ❌ 错误示例（勿学）

### 错误1：手动计算trend（重复劳动）

```python
# ❌ 不要这样做！
def feed(cycle):
    price = prices[cycle]
    
    # ❌ 手动计算trend - 重复实现！
    if cycle > 0:
        prev_price = prices[cycle - 1]
        price_change = (price - prev_price) / prev_price
        trend = 'bullish' if price_change > 0.01 else 'bearish'
    else:
        trend = 'neutral'
    
    return {"price": price, "trend": trend}, {}
```

**问题**：
1. 每个测试都要重复实现trend计算
2. 不同测试的计算逻辑可能不一致
3. 如果Daimon需要新字段，所有测试都要改

### 错误2：缺少字段（导致决策失败）

```python
# ❌ 不要这样做！
def feed(cycle):
    return {"price": prices[cycle]}, {}  # ❌ 缺少trend等字段
```

**结果**：Daimon的genome_voice无法工作 → 所有Agent返回hold → 没有交易！

---

## 🔧 Facade内部实现原理

### _enrich_market_data方法

```python
def _enrich_market_data(self, market_data: Dict, cycle_count: int) -> Dict:
    """统一数据增强 - 解决数据封装问题的核心方法"""
    enriched = market_data.copy()
    
    # 1. 验证price
    if "price" not in enriched:
        raise ValueError("market_data必须包含price字段！")
    
    # 2. 自动补充cycle
    enriched["cycle"] = enriched.get("cycle", cycle_count)
    
    # 3. 计算trend和price_change（基于历史价格）
    if not hasattr(self, '_price_history'):
        self._price_history = []
    
    if len(self._price_history) > 0:
        prev_price = self._price_history[-1]
        price_change = (enriched["price"] - prev_price) / prev_price
        enriched["price_change"] = price_change
        
        # 趋势判断（阈值1%）
        if price_change > 0.01:
            enriched["trend"] = 'bullish'
        elif price_change < -0.01:
            enriched["trend"] = 'bearish'
        else:
            enriched["trend"] = 'neutral'
    else:
        enriched["price_change"] = 0.0
        enriched["trend"] = 'neutral'
    
    # 4. 计算volatility（基于20期标准差）
    if len(self._price_history) > 10:
        returns = np.diff(self._price_history[-20:]) / self._price_history[-21:-1]
        enriched["volatility"] = float(np.std(returns))
    else:
        enriched["volatility"] = 0.02  # 默认2%
    
    # 5. 更新历史
    self._price_history.append(enriched["price"])
    if len(self._price_history) > 100:
        self._price_history.pop(0)
    
    return enriched
```

---

## 📊 为什么要这样做？

### 问题1：Daimon决策依赖复杂数据

Daimon有7个"声音"：
1. **instinct_voice**: 需要capital_ratio, position等
2. **genome_voice**: 需要**trend**（关键！）
3. **emotion_voice**: 需要recent_pnl等
4. **strategy_voice**: 需要技术指标
5. **prophecy_voice**: 需要公告板信息
6. **world_signature_voice**: 需要WorldSignature
7. **experience_voice**: 需要历史记录

如果缺少**trend**，genome_voice就不会投票 → 所有声音都不投票 → 返回hold！

### 问题2：数据来源多样

- 回测：从CSV文件读取
- Mock：模拟生成
- 实盘：从交易所API获取

**统一封装**确保无论数据来源如何，Daimon都能正常工作！

---

## 🎯 总结

| 角色 | 职责 | 不应该做 |
|------|------|----------|
| **外部调用者** | 提供price | ❌ 不要计算trend, volatility等 |
| **V6 Facade** | 补充所有必要字段 | ✅ 统一封装数据 |
| **Daimon** | 基于完整数据决策 | ✅ 假设数据完整 |

**核心思想**：**数据封装责任单一化！**

---

## 📚 相关文档

- V6 Facade实现：`prometheus/facade/v6_facade.py`
- Daimon决策逻辑：`prometheus/core/inner_council.py`
- 标准测试模板：`templates/STANDARD_TEST_TEMPLATE.py`
- 正确测试示例：`test_ultimate_v6_CORRECT.py`

---

## ⚠️ 重要提醒

如果以后发现Daimon需要新的字段（如momentum, support_resistance等），
**不要在每个测试中添加！**

✅ **正确做法**：
1. 在`V6Facade._enrich_market_data()`中添加计算逻辑
2. 所有测试自动获得新字段！

这就是**统一封装**的威力！ 🎉

