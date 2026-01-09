# V12 SSOT — Epoch Constitution (Evolution “Constitution”) — 2026-01-02

目标：将 “Epoch” 冻结为 V12 演化实验的**宪法级约束**，用于保证长期实验的可比性、可回放性与可审计性。

本文件 additive-only。

---

## 1) Definition（冻结）

**Epoch**：在一个演化实验中，满足以下三类语义均保持不变的**最大连续区间**：

1) **Evolutionary operators**（演化算子语义不变）  
2) **World contract**（世界合同/证据合同语义不变）  
3) **Observation semantics**（观测语义/采样与聚合口径不变）

关键点（冻结）：
- Epoch **不是时间切片**：不会因为跨日/重启/跑了很久而自动切换。
- Epoch 仅在发生 **semantic break（语义断裂）** 时切换。
- “最大连续区间”表示：在语义不变的前提下，epoch 不能再向前或向后扩展。

---

## 2) Why it matters（冻结）

演化对环境与观测条件高度敏感。若跨越语义断裂仍把样本当作同一条件下的连续数据，会产生不可控偏差：
- A/B 对照失效（不同 epoch 的样本不可直接对比）
- 聚类/坍缩观察被“仪器变化”污染
- 长期实验无法复核（无法回答“当时规则是什么？”）

Epoch 的作用（冻结）：
- **同一 epoch 内**：允许严格对照/消融/统计聚合（可比性成立）
- **跨 epoch**：必须显式标注“不可直接对比”（除非额外做对齐/迁移证明）

---

## 3) Semantic break triggers（epoch 切换触发器，冻结）

### 3.1 Evolutionary operators break（冻结）

以下任一变化均视为切 epoch：
- 选择/变异/交叉/繁殖/新陈代谢等算子**语义**变更
- 关键超参改变且会改变算子语义（例如从“资金翻倍分裂”改为“阈值委员会裁决”）

### 3.2 World contract break（冻结）

以下任一变化均视为切 epoch：
- canonical schema 字段**语义**变化（字段含义/单位/类型/枚举意义改变）
- join keys 语义变化（例如从 snapshot_id 改为 event_ref 且不可兼容）
- NOT_MEASURABLE 纪律发生语义级变化（不仅是新增 reason_code；例如把缺测从 null 改为 0 伪装）

备注：SSOT additive-only 允许“追加字段/追加 reason_code vocabulary”，但若追加导致旧 run 无法按原语义回放或解释，即属于 semantic break。

### 3.3 Observation semantics break（冻结）

以下任一变化均视为切 epoch：
- 从 **tick snapshot** 切到 **event-driven events**（或相反）
- 采样窗口语义改变（例如从 t-1 标量改为 rolling window）
- 观测聚合口径改变且影响统计解释（例如从 mean 改为 median/trimmed mean，且不再并存）

---

## 4) epoch_id & epoch manifest（冻结入口）

### 4.1 epoch_id（冻结）

`epoch_id` 必须仅由“语义合同三件套版本”决定，而不是由时间决定：

- `evolution_operators_contract_id`
- `world_contract_id`
- `observation_semantics_id`

推荐（冻结入口）：
- 用一个稳定的、可机读的 `epoch_contract` JSON 进行 canonical serialization，再做 hash 得到 `epoch_id`。
- 重要：serialization 规则必须稳定（字段顺序、字符串化规则），否则 epoch_id 会漂移。

### 4.2 epoch_manifest.json（必须落盘，冻结）

每个 run_dir 必须包含 `epoch_manifest.json`（即使 epoch 不切换，也必须写入）。

最小字段（冻结）：
- `epoch_id`（string）
- `epoch_contract`（object）：
  - `evolution_operators_contract_id`（string）
  - `world_contract_id`（string）
  - `observation_semantics_id`（string）
- `epoch_semantic_break`（object）：
  - `is_break`（bool）
  - `break_reason_codes`（array[string]）
  - `break_notes`（string, optional）
- `references`（object, optional）：
  - `ssot_anchors`（array[string]，引用 SSOT 文件路径或版本号）
  - `quant_commit`（string, optional）

Fail-closed（冻结）：
- 若 run 缺失 `epoch_manifest.json`：该 run 必须判为 NOT_MEASURABLE（evidence_incomplete:epoch_manifest_missing）
- 若 `epoch_id` 与 `epoch_contract` 不一致（可机验 hash 不匹配）：verifier 必须 FAIL（不是 NOT_MEASURABLE）

---

## 5) Cross-links（只读）

- V12 index: `docs/v12/V12_RESEARCH_INDEX.md`
- Uplink/Downlink evidence: `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`
- Modeling pipeline: `docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`



---

## Appendix A — Audit Coordinate System: Consensus Epoch Candidates from world_u changepoints (BTC, annotation-only)

This appendix is **annotation-only**.

- It does **not** redefine Epoch (semantic-break based) in §1.
- It does **not** change any downstream mechanism, parameters, or evaluation semantics.
- It provides a frozen coordinate system to re-index / summarize evidence by *candidate* epoch segments.

Source (frozen):
- Trial-9 consensus boundaries (PASS):
  - `docs/v12/artifacts/world_pressure_epoch_annotation/trial9_btc_epoch_annotation_v0_20260109/epoch_candidates.json`

Consensus boundaries (tick indices, N=10000; BTC 2021–2022, full runs used in Trial-8/9):
- `[644, 3837, 5812, 6339, 6676]`

Segments:
- E0: [0, 644)
- E1: [644, 3837)
- E2: [3837, 5812)
- E3: [5812, 6339)
- E4: [6339, 6676)
- E5: [6676, 10000)

Audit boundary note (frozen pointer):
- Trial-10 (descriptive audit of evidence-chain stats by these epochs) verdict = **FAIL** under frozen thresholds:
  - `docs/v12/artifacts/world_pressure_evidence_reindex/trial10_btc_reindex_by_epoch_v0_20260109/trial10_btc_evidence_reindex_report.md`

Interpretation constraint:
- These epoch candidates may be used to **organize** evidence summaries.
- They must not be used to claim semantic breaks or to justify mechanism changes.

Hard prohibition (appendix-level, aligned with SSOT):
- The consensus epoch candidates above are **annotation-only** and are **prohibited** as downstream control variables / conditioning windows / mechanism design drivers.
- Enforced by: `docs/v12/V12_SSOT_WORLD_PRESSURE_BOUNDARY_SIGNAL_V0_20260109.md` (§6) and Trial-10 FAIL: `docs/v12/artifacts/world_pressure_evidence_reindex/trial10_btc_reindex_by_epoch_v0_20260109/trial10_btc_evidence_reindex_report.md`.
