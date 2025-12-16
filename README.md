# Prometheus-Research

<div align="center">

*An evolutionary probe into market complexity*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[中文版](README_CN.md)** · **[Framework](docs/v8/V8.md)** · **[Methodology](docs/v8/METHODOLOGY_EN.md)** · **[Theory](docs/theory/CONJECTURE_EN.md)**

</div>

---

## 🎯 Research Question

**Can the unpredictability of markets be measured?**

---

## 💡 Hypothesis

Markets may be a **Gödelian system**: no complete, self-provable prediction framework can exist from within the system itself.

If this is true:
- We cannot find a "perfect" prediction model
- But can we measure the **strength** of unpredictability?
- Can we observe the **structure** of unpredictability?

---

## 🎯 Core Conjecture: Adaptive Exploration Theory

### What Question Are We Trying to Answer?

Imagine:

**Scenario A: Simple Environment**
- You're playing a highly structured game (like tic-tac-toe)
- Best strategy: think carefully, follow patterns
- No need for much "random exploration"

**Scenario B: Complex Environment**
- You're playing a game full of uncertainty (like poker)
- Best strategy: sometimes follow logic, sometimes randomize (bluff)
- Requires a certain degree of "unpredictability"

**Core Question:**
> Can an intelligent system, without knowing the environment's complexity, automatically find the optimal level of "randomness/exploration" through evolution?
> 
> If so, does this "optimal level" reflect the environment's complexity?

---

### 💡 The Core of Our Conjecture

**1. Convergence**:
- Give agents a heritable "exploration parameter" \( I \) (value between 0-1)
- Higher \( I \) = more random/contrarian behavior
- Lower \( I \) = more deterministic/conformist behavior
- After sufficient evolution time, \( I \) converges to a stable value \( I^* \)

**2. Environment Dependence**:
- Simple environment (high predictability) → Low \( I^* \) (~0.1)
- Complex environment (low predictability) → High \( I^* \) (~0.6+)
- **\( I^* \) quantifies the environment's "unpredictability"**

**3. Reverse Inference**:
- By observing how \( I^* \) converges (speed, path, stability)
- We can infer hidden environmental properties (memory length, periodicity, chaos level, etc.)
- Like: observing biological evolution traits → inferring environmental pressures

---

### 📊 Intuitive Analogies

#### Analogy 1: Darwin's Finches 🦎

```
Galápagos Islands:

Different islands → Different food environments
Finch beaks → Evolved different shapes
  - Hard-shelled seeds → Thick beaks
  - Insects → Thin beaks

Our Research:

Different markets → Different complexity levels
Agent's I* → Evolves to different values
  - Simple markets → Low I* (deterministic strategies)
  - Complex markets → High I* (exploratory strategies)

Through I* value, infer market complexity ✨
```

#### Analogy 2: Mutation Rate 🧬

```
Biology:

Stable environment → Low mutation rate (preserve effective genes)
Volatile environment → High mutation rate (rapid adaptation)

Our System:

Simple market → Low I* (low exploration/randomness)
Complex market → High I* (high exploration/randomness)

I* is like "cognitive mutation rate" ✨
```

---

### 🔬 How to Verify?

#### Experiment 1: Same Market, Multiple Runs

**If conjecture holds**:
- Systems with different random seeds
- Should converge to similar \( I^* \)
- Proves \( I^* \) is environment-determined, not random

#### Experiment 2: Different Markets, Same System

**If conjecture holds**:
- Gentle market → Low \( I^* \)
- Medium market → Medium \( I^* \)
- Brutal market → High \( I^* \)
- Proves \( I^* \) reflects environmental complexity

#### Experiment 3: Observe Convergence Process

**If conjecture holds**:
- Simple market: Fast, monotonic convergence
- Complex market: Slow, oscillatory convergence
- Chaotic market: Chaotic wandering, hard to converge
- Convergence "fingerprint" reveals microstructure

---

### 🌟 Possible Discoveries (Hypothetical)

**Discovery A: Market is "Markovian"**
```
Experimental results:
  I* = 0.05 (very low)
  Fast convergence (~3000 cycles)
  Monotonic path

Inference: Short memory, high predictability, suitable for modeling ✓
```

**Discovery B: Market is "Periodic"**
```
Experimental results:
  I* = 0.25 (medium)
  Slow convergence (~15000 cycles)
  Oscillatory path

Inference: Periodic structure, medium predictability ⚠️
```

**Discovery C: Market is "Chaotic"**
```
Experimental results:
  I* = 0.65 (very high)
  Very slow convergence (>50000 cycles)
  Chaotic path

Inference: Highly complex, low predictability ❌
```

**Discovery D: Market is "Non-stationary"**
```
Experimental results:
  I*(t) continuously drifts
  No convergence

Inference: Evolving microstructure, requires continuous adaptation 🔄
```

---

### 💎 Philosophical Significance

**"Evolution is the Only Solution to Incompleteness"**

```
Gödel tells us:
  Within formal systems, some truths cannot be proven

Markets might be like this:
  Within the system, complete prediction is impossible

But evolution tells us:
  No need to "prove"
  Only need "what works"
  
I* is evolution's "pragmatic solution":
  - Cannot be formally derived
  - But can be discovered through evolution
  - It quantifies the "unprovable boundary" ✨
```

---

**📐 For complete mathematical formulation and rigorous proofs, see: [Theory Document](docs/theory/CONJECTURE_EN.md)**

---

## 🔬 Research Framework

Assuming markets are a **Gödelian system** (no complete, self-provable prediction framework exists), we construct a multi-agent system with:

**Three Core Constraints:**
1. **No prior strategy** - Agents start with random weights, no human-designed logic
2. **No objective function** - No explicit "goal" to optimize
3. **No explicit optimization** - Only natural selection through survival pressure

Through **minimal, local, life-and-death trading rules**, we observe whether **stable, reproducible, comparable statistical structures** emerge spontaneously.

**Thus verifying: whether the unpredictability of markets is itself measurable.**

---

### Methodological Principles

To achieve this goal, we developed a methodology to design a measurement system.

**Principle 0: Measurability Criteria**
- 0.1 Disturbance is Measurable - Observation system's interference is quantifiable or comparable
- 0.2 Emergent Patterns - Results exhibit spontaneously emergent patterns

**Six Core Principles:**
1. Gene dimensions align with observable features
2. Allow redundant dimensions (evolution will reduce)
3. Features = measurable + measurement bias (evolution discovers truth)
4. Evolution follows natural selection (objective world as sole judge)
5. System evolves, observer recognizes patterns
6. Better solutions always exist (continuous exploration)

**→ [Complete Framework](docs/v8/V8.md)**

---

### Minimal Implementation

- **Features**: 31 aligned dimensions (market) + 1 intuition parameter (exploration)
- **Decision**: Linear weighting × contrarian coefficient → trading signal
- **Birth/Death**: Occur randomly, survival of the fittest

---

## 🧪 Current Status

**Experiment design in progress.**

System design has been refined through multiple iterations:
- Fixed critical bugs in capital management
- Simplified gene structure (removed mystery dimensions, kept intuition parameter)
- Implemented system-level survival pressure

**No results to report yet.** Waiting for reliable data before drawing conclusions.

---

## 📖 Documentation

### Theory & Framework
- **[Adaptive Exploration Conjecture](docs/theory/CONJECTURE_EN.md)** - Mathematical formulation (English)
- **[适应性探索猜想](docs/theory/CONJECTURE.md)** - 数学严格表述（中文）
- **[V8.0 Principles](docs/v8/V8.md)** - Principle 0 + 6 core principles (Chinese)

### Technical Implementation
- **[Methodology](docs/v8/METHODOLOGY_EN.md)** - Technical details (English)
- **[方法论](docs/v8/METHODOLOGY.md)** - 技术细节（中文）

### Reports
Experimental reports will be added as reliable data becomes available.

---

## 🤔 Why This Matters

### The Dilemma of Traditional Approaches

```
Question: "Are markets predictable?"

Traditional answer:
  - Design strategy → backtest → optimize → live trade
  - Success = "predictable"
  - Failure = "try another strategy"
  
Dilemma:
  ❌ Never know if it's "market unpredictable" or "strategy inadequate"
  ❌ Trapped in infinite loop
```

### Our Approach

```
New question: "How strong is market unpredictability?"

Our answer:
  - Design evolutionary system → observe I* convergence
  - Low I* → "High predictability, worth modeling"
  - High I* → "Strong unpredictability, proceed with caution"
  
Advantages:
  ✓ Directly quantifies unpredictability
  ✓ Independent of specific strategies
  ✓ Provides "can we predict?" signal
```

---

## 🔄 Replication

The mechanism is extremely simple.

Code is not open-sourced because:
1. The mechanism is very simple
2. The code is terrible (blame Cursor)

**If you replicate, please share your findings.**

---

## 💬 Note

This is an early-stage research project. Conclusions are not yet established.

I'm observing, recording, and waiting for data to speak.

---

## 🌌 Epilogue

> **The unknown is infinite, but it won't stop us from exploring.**

Are markets predictable? We don't know.  
Where is the boundary of predictability? We cannot measure.  
But unpredictability itself, perhaps, is measurable.

This is not a solution.  
This is an exploration.

**Not to "beat the market"**  
But to **"understand the boundary of market comprehensibility"**

**Not to "find the perfect strategy"**  
But to **"measure the possibility space of strategies"**

**Not to "conquer uncertainty"**  
But to **"quantify uncertainty itself"**

---

> *"I don't know. I'm just an agent, like you."*

---

## 📬 Contact

- GitHub Issues: [Report bugs or discuss ideas](https://github.com/Garylauchina/Prometheus-Research/issues)
- Email: garylauchina@gmail.com

---

## 📜 License

[MIT License](LICENSE)

---

<div align="center">

**Last updated: December 16, 2025**

</div>
