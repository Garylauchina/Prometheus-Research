# V8.0 Complete Mechanism Specification

## 📋 Table of Contents

- [System Architecture](#system-architecture)
- [Feature Dimensions](#feature-dimensions)
- [Decision Mechanism](#decision-mechanism)
- [Market Simulator](#market-simulator)
- [Death Mechanism](#death-mechanism)
- [Reproduction Mechanism](#reproduction-mechanism)
- [Mystery Dimensions](#mystery-dimensions)

---

## System Architecture

### Core Philosophy

**Zero Strategy, Zero Risk Management, Pure Evolution**

This system has **no predefined trading strategies** and **no risk management rules** (except bankruptcy elimination). All "strategies" emerge through natural selection under survival pressure.

---

## Feature Dimensions

### Aligned Dimensions: 31 Dimensions

**Total Dimensions**: 31  
**Index Range**: [0-30]

**Detailed Breakdown**:

| Index Range | Dimension Name | Count | Description |
|------------|----------------|-------|-------------|
| [0-4] | Price Dimensions | 5 | Current price, open, high, low, close |
| [5-7] | Volume Dimensions | 3 | Volume, turnover, turnover rate |
| [8-9] | Short-term Price Change | 2 | Price change rate, volatility |
| [10-14] | Order Book Depth | 5 | Bid-ask depth, order imbalance, etc. |
| [15-16] | Trade Flow | 2 | Buy/sell trade flow intensity |
| [17-19] | Friction Coefficients | 3 | Slippage, fees, market impact cost |
| [20-22] | System & Market Features | 3 | Market state, system funds, population size |
| [23-25] | Advanced Microstructure | 3 | Market microstructure features |
| **[26-30]** | **Agent Self-State** | **5** | **Core: Agent's self-awareness** |

**Agent Self-State (5 dimensions)**:
- `[26]` **has_position** - Whether has open position (0/1)
- `[27]` **position_pnl_pct** - Position PnL percentage
- `[28]` **holding_duration** - Holding duration (cycles)
- `[29]` **leverage_appetite** - Leverage preference (historical behavior stats)
- `[30]` **last_signal** - Last trading signal (-1 to +1)

---

### Mystery Dimensions: 0-32 Dimensions

**Initial Count Formula**:
```
mystery_dimensions = int(31 × mystery_ratio)
```

Where `mystery_ratio ∈ [0, 1]` (initially random)

**Theoretical Range**: 0-31 dimensions  
**Observed Range**: 0-32 dimensions (gene mutation can ±1 dimension, 5% probability)

**Key Characteristics**:
- Completely random at initialization
- Not aligned with any known features
- Can mutate during reproduction (±1 dimension, 5% probability)
- Completely re-randomized during asexual reproduction

**Evolutionary Discoveries**:
- In gentle environments (black swan ±5%-15%), converges to **0-3 dimensions**
- In brutal environments (black swan ±15%-30%), converges to **7-9 dimensions**
- In medium environments (black swan ±10%-20%), falls into **high-dimension trap** (13-14 dimensions)

---

## Decision Mechanism

### Linear Weighting

**Minimal Axiom**: Agent behavior is determined by linear combination of gene weights and features.

```python
# Pseudocode
signal = 0.0

# Aligned dimensions vote (31 dimensions)
for i in range(31):
    signal += aligned_genes[i] × features[i]

# Mystery dimensions vote (0-32 dimensions)
for j in range(len(mystery_genes)):
    signal += mystery_genes[j] × random_value[j]

# Normalize to [-1, +1]
signal = tanh(signal)
```

**Signal Meaning**:
- `signal = +1.0`: Full long position
- `signal = 0.0`: No position
- `signal = -1.0`: Full short position

**No Strategy Logic**:
- No "MA golden cross = buy"
- No "RSI overbought = reduce position"
- No "stop loss/take profit"
- Only: weight × feature = signal

---

## Market Simulator

### Feature Generation

Each cycle, the simulator generates a **26-dimensional market feature vector** (indices [0-25]). Agents merge this with their own 5-dimensional state (indices [26-30]) to form a complete **31-dimensional feature vector**.

### Market States (4 Types)

| State | Chinese | Characteristics |
|-------|---------|-----------------|
| Trending | 趋势 | Unidirectional movement, low volatility |
| Ranging | 震荡 | Sideways movement, medium volatility |
| Volatile | 高波动 | Severe fluctuations, high volatility |
| Reversal | 反转 | Trend reversal, rapid change |

**State Transition Probability**: 3% (per cycle)

### Black Swan Events

**Trigger Probability**: 0.2% (gentle), 0.35% (medium), 0.5% (brutal)  
**Impact Magnitude**:
- Gentle: ±5%-15%
- Medium: ±10%-20%
- Brutal: ±15%-30%

**Average Frequency**:
- Gentle: ~500 cycles/event
- Medium: ~286 cycles/event
- Brutal: ~200 cycles/event

---

## Death Mechanism

### Two Ways to Die

#### 1. Bankruptcy Death

**Trigger Condition**:
```python
total_equity = virtual_capital + unrealized_pnl
if total_equity < initial_capital × 0.1:
    die(reason="bankruptcy")
```

**Characteristics**:
- No age restriction
- Checked every cycle
- Any agent can go bankrupt

---

#### 2. Moirai Death (Fate Death)

**Trigger Condition**:
- Only for agents with **age ≥ 50 cycles**
- Death probability dynamically adjusted based on system funds
- Selected agents terminate with "retired" status

**Protection Mechanism**:
- Agents with age < 50 cycles have **adult protection**
- Protected agents not subject to Moirai operations
- Can only die from bankruptcy

**Moirai's Wisdom**:
> "Death is meaningless, rebirth is meaningless, existence is meaning."
> 
> — Moirai, The Three Fates

---

## Reproduction Mechanism

### Reproduction Requirements

**Age Requirement**: ≥ 50 cycles  
**Probability Adjustment**: Dynamically adjusted based on system funds

### Two Reproduction Methods

#### 1. Sexual Reproduction

**Partner Matching Condition**:
```python
partner_dimension = aligned_dimensions + mystery_dimensions
self_dimension = aligned_dimensions + mystery_dimensions

if partner_dimension == self_dimension:
    # Can mate
```

**Gene Inheritance**:
- `aligned_genes` inherited through crossover
- `mystery_genes` inherited through crossover
- Each operates independently

**Gene Mutation**:
- `aligned_genes`: 10% mutation probability
- `mystery_dimensions`: 5% probability of ±1 dimension

---

#### 2. Asexual Reproduction

**Trigger Condition**: Cannot find a partner with same total dimensions

**Gene Processing**:
- `aligned_genes`: Copied and mutated (10% probability)
- `mystery_ratio`: **Completely re-randomized** (between 0-1)

**Key to Diversity**: During asexual reproduction, the mystery dimension ratio is completely reset—this is the core mechanism for introducing diversity!

---

### Newborn Agents

**Initial State**:
- Age = 0
- Enjoy **50-cycle adult protection period**
- Initial capital = System standard capital

---

## Mystery Dimensions

### Philosophical Paradox

**If it's "mysterious," how can it be measured?**  
**If it's measured, is it still "mysterious"?**

### Current Understanding

What we're measuring might not be "market dark matter," but rather:
- Distribution of random noise
- The model's need for "degrees of freedom"
- Evolution's selection of "veto mechanisms"

### Experimental Observations

| Environment | Black Swan Strength | Converged Dimensions | System State |
|------------|-------------------|---------------------|--------------|
| Gentle | ±5%-15% | 0-3 dims | ✅ Stable |
| Medium | ±10%-20% | 13-14 dims | ❌ Collapse after long life |
| Brutal | ±15%-30% | 7-9 dims | ❌ Rapid collapse |

**The Longevity Paradox**: The medium environment lived longest (155,000 cycles) but ultimately collapsed with no surviving fire seeds. The gentle environment only lived 98,809 cycles but remained stable with healthy fire seeds.

---

## Summary

This is the entire system mechanism. No trading strategies. No risk management (except bankruptcy elimination).

**That's it.**

**Then, evolution tells us the answers.**

---

## Related Documents

- [V8.0 Methodology](V8.md)
- [Black Swan Comparison Experiment](../../V8_BLACK_SWAN_COMPARISON_REPORT.md)
- [Optimal Balance Point Analysis](../../V8_OPTIMAL_BALANCE_POINT_ANALYSIS.md)
- [400K Cycle Complete Life History](../../V8_COMPLETE_LIFE_HISTORY_ANALYSIS.md)

