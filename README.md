## Prometheus-Research

<div align="center">

*An auditable evolutionary research program for probing market structure.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[中文说明](README_CN.md)** · **[Docs Index](docs/README.md)** · **[V10 Evidence Chain](docs/v10/V10_RESEARCH_INDEX.md)** · **[V10 Folder](docs/v10/README.md)**

</div>

---

## Why this repo exists (English) / 本仓库的定位（中文）

**English (primary)**: This repository is the **research record** of the Prometheus project.  
Its purpose is not to “sell an idea”, but to preserve a **reviewable evidence chain**:

- **Acceptance criteria** (what counts as a valid result)
- **Decision records** (what we concluded, and why)
- **Auditability constraints** (what we forbid to keep evidence clean)

**中文（辅助）**：这是 Prometheus 的“研究仓库”，核心目标是**让结论可被复核**。  
这里存的不是代码主仓，而是：验收标准、裁决记录、证据链入口与审计约束。

---

## Current status: V10 is the mainline / 当前主线：V10

- **Start here / 从这里开始**: `docs/v10/V10_RESEARCH_INDEX.md`
- **Acceptance criteria / 验收标准（项目宪法）**: `docs/v10/V10_ACCEPTANCE_CRITERIA.md`
- **Roadmap / 路线图（A→B→C）**: `docs/v10/V10_ROADMAP_A_ENGINEERING_B_RESEARCH_C_PRODUCT.md`

V10 is built to answer a very practical reviewer question:

- **English**: “Do you have evidence that the system exploits temporal structure, rather than artifacts or prior-coded strategy?”
- **中文**：“你如何证明系统利用的是时间结构，而不是漏洞、先验指标、或者人为预设策略？”

---

## Reproducibility & Evidence (English) / 可复核性与证据（中文）

**English (primary)**:
This repo intentionally keeps **documents and evidence pointers**.  
Raw simulation outputs and code live in the separate repository **Prometheus-Quant**.  
Most V10 decision documents include exact `results_...` directories to verify:

- summary JSON (run aggregates + invariants)
- agent-level behaviors (JSON)
- aligned genomes matrix (NPY)

**中文（辅助）**：Research 仓库存“文档+证据指针”，原始实验产物在 `Prometheus-Quant`。  
V10 文档会写清楚 `results_...` 路径，复核时只需要按路径读取即可（不靠口头解释）。

---

## What you can audit in V10 (English) / V10 可审计点（中文）

- **Null hypothesis**: A (real time) vs B2 (shuffle log-returns to destroy temporal structure)
- **Prior leakage defense**: mandatory ablations (M/C/E-subset/I and subsets)
- **Window migration**: non-overlapping windows (W1b/W2) for robustness
- **Mechanism attribution**: from run clusters → agent clusters → gene-level channels
- **Hardened audits**: winner definition (v2), IN/OUT sign consistency (v2), stratified stability (v3/v3.1)

入口都在：`docs/v10/V10_RESEARCH_INDEX.md`

---

## Repository map / 仓库地图

- **Primary (V10)**: `docs/v10/`
- **Research audits & memos**: `docs/research/`
- **Architecture notes**: `docs/architecture/`
- **Theory (optional)**: `docs/theory/`
- **Legacy**: `docs/v8/`, `docs/v7/`, `docs/v6/`

---

## Citation / 引用方式（可选）

If you refer to this work, cite the **repository** and the specific **V10 decision record(s)** by file path under `docs/v10/`.

---

## License

MIT License. See `LICENSE`.

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
