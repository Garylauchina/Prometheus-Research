# V10 — A Minimal Method for Measuring Complex Systems (Evolutionary Probing)

> Version: 2025-12-24.1  
> Status: Canonical (V10)  
> Scope note: This document defines **how we measure**, not what the world “should” look like.

## Conjecture (working hypothesis)

In a complex system composed of many individuals, if all individuals share the same *class* of driving function and constraint structure (only parameters differ), then at any moment the system tends to fall into one of two regimes:

- it behaves like pure random noise (no repeatable structure), or
- its macroscopic dynamics can be described by a finite set of dominant effective dimensions; these dimensions may evolve slowly, but do not diverge without bound.

Clarification (what “common driving force” means here):
- We mean a *universal* driver shared by the population (not “the same strategy”), e.g., market participants are ultimately driven by profit/survival under risk and constraints; physical particles are driven by fundamental interactions under physical laws.
- In an ecosystem, individuals are driven by survival and reproduction under ecological constraints.

## 0) What this is (and what it is not)

- **This is measurement**: we design an operational procedure that produces auditable artifacts and allows rejection, not storytelling.
- **This is not validation**: if we only reproduce preset patterns, we validated presets, not measured the target.

## 1) Meta-judgment: measurability (Principle 0)

Before any claim, judge whether the target system is measurable under our setup.

- **P0.1 Disturbance is measurable**
  - The observation system’s disturbance on the target is quantifiable/comparable.
  - If an external complex system keeps intervening in a strongly-coupled way (changing rules, boundaries, or observation channels), the run becomes **Not Measurable**.
- **P0.2 Emergent patterns exist**
  - Observations exhibit non-preset, post-hoc explainable regularities.

V10 engineering binding:
- Gate 0 is the measurability gate. If Gate 0 fails, the run is **Invalid**.
- See `docs/v10/V10_ACCEPTANCE_CRITERIA.md` (G0.*).

## 2) Core principles (minimal)

- **P1 M = N (aligned dimensions)**  
  Gene dimensions align to the externally observable feature set (index-aligned).

- **P2 Redundancy allowed**  
  We prefer redundancy over omission. Evolution can down-weight useless dimensions.

- **P3 Features include bias dimensions**  
  World features = measurable dimensions + measurement-bias dimensions. We admit imperfection and make it auditable.

- **P4 Natural selection, no designer strategy**  
  The world is the evaluator. We do not inject strategy fences into the decision path.
  - Allowed: ecological fences for system safety (capital conservation, STOP, rate limiting), and post-hoc audit labels.
  - Forbidden: “must trade / must act” fences to force outcomes.

- **P5 The system demonstrates; the observer decides**  
  The system produces evidence; the observer performs acceptance/rejection based on contracts.

- **P6 There is always a better solution**  
  Conclusions are provisional; continuous probing is expected.

## 3) Evidence-first operational contract (V10)

Every run must be judged on artifacts, not console outputs.

Minimum requirements:
- **Reproducibility**: same world version + config + seed + window → same key summaries within tolerance.
- **Auditability**: run_dir contains `FILELIST` + `SHA256SUMS`, and key JSONL/JSON artifacts.
- **No fake trades** in OKX demo/live execution world.
- **Interface freeze** after acceptance: schema changes require version bump + minimal regression rerun.

Reference contracts:
- `docs/v10/V10_ACCEPTANCE_CRITERIA.md`
- `docs/v10/V10_EXECUTION_ENGINE_CONTRACT_OKX_DEMO_LIVE.md`
- `docs/v10/V10_RECONCILIATION_MODULE_CONTRACT_OKX_EXECUTION_WORLD.md`

## 4) Minimal falsification loop (what we must be able to reject)

We must be able to say “no” with evidence:

- **Not measurable**: strong-coupling intervention occurred (rules/boundaries/observation channels drifted).
- **Invalid**: missing artifacts, NaN/Inf, broken accounting, fake trades, or uncontrolled schema drift.
- **Inconclusive**: evidence exists but did not exercise a required claim (e.g., NO_TRADE → cannot conclude fill/fee closure).

## 5) Practical reading map

- If you want the rules: `docs/v10/V10_ACCEPTANCE_CRITERIA.md`
- If you want the “execution world” semantics: execution + reconciliation contracts (above)
- If you want the Mac OKX demo stage plan: `docs/v10/V10_GATE4_OKX_DEMO_EVOLUTION_MAC.md`

---

# V10 — 用进化探测测量复杂系统（极简版）

> 版本：2025-12-24.1  
> 状态：V10 正文（当前口径）

## 猜想（工作假设）

在由大量个体组成的复杂系统中，若所有个体共享同一类驱动力函数与约束结构（仅参数不同），那么系统在任意时刻往往只有两种状态：

- 要么整体表现为纯随机噪声（没有可复述结构）；
- 要么其宏观动力学可由有限个主导有效维度来描述，这些维度可以缓慢演化，但不会无限发散。

说明：这里的“共同驱动力”指更底层的、普适的驱动（不是“同一套策略”）。例如市场中的个体最终受“盈利/生存（在风险与约束下）”驱动；物理世界中的个体受基本相互作用与物理定律约束驱动。
生态系统中的个体则受“生存/繁殖（在生态约束下）”驱动。

## 0）这是什么/不是什么

- **这是测量**：用操作流程产出可审计证据，允许被拒绝，而不是讲故事。
- **这不是验证**：如果只是复现预设模式，我们验证的是预设，不是测量目标系统。

## 1）元判断：可测量性（原则0）

任何结论之前，先判断“能不能测”。

- **0.1 干扰可测量**：观测系统对目标系统的干扰必须可量化/可比较。  
  若外部复杂系统以强耦合方式频繁介入（改变规则/边界/观测通道），则本次 run **不可测量**（Not Measurable）。
- **0.2 涌现规律**：观测结果存在非预设、事后可解释的规律。

工程对齐：Gate 0 是“可测量性门”。Gate 0 失败 → run **Invalid**。

## 2）核心原则（只保留最小集合）

- **原则1：M=N（维度对齐）**：基因维度与外显特征集按索引对齐。
- **原则2：允许冗余**：宁可冗余不可遗漏，演化会自动降权/降维。
- **原则3：承认测量偏差**：特征集包含“可测量维度 + 偏差维度”，并要求可审计。
- **原则4：自然选择，不做设计师策略**：世界是唯一评估者。  
  允许生态围栏（STOP/限流/资金守恒/审计标签）；禁止把“必须交易/必须动作”等人为围栏塞进决策路径。
- **原则5：系统演示，观察者裁决**：系统只负责产证据；是否通过由观察者按合同裁决。
- **原则6：永远存在更优解**：结论是暂时的，持续探测是默认行为。

## 3）证据优先（V10 最小操作契约）

每次 run 必须能给出：可复现 + 可审计 + 可证伪的证据包（FILELIST + SHA256 + 关键 JSON/JSONL）。
OKX demo/live 必须“无伪造交易”，接口/证据 schema 通过后冻结。

参考：
- `docs/v10/V10_ACCEPTANCE_CRITERIA.md`
- `docs/v10/V10_EXECUTION_ENGINE_CONTRACT_OKX_DEMO_LIVE.md`
- `docs/v10/V10_RECONCILIATION_MODULE_CONTRACT_OKX_EXECUTION_WORLD.md`

