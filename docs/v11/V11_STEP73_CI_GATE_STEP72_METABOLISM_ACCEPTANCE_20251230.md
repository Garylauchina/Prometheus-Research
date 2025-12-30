# V11 Step 73 — CI Gate: Step72 Agent Metabolism Acceptance (Quant) — SSOT — 2025-12-30

目的：将 Step72（agent metabolism 观测输出）升级为 **CI 必跑且不可回退** 的验收项，锁定：
- `research_bundle/agent_metabolism_summary.json` 生成与 schema
- 该产物被 `research_bundle/entry.json` 索引且可用 `evidence_ref_index.json` 复核 `sha256_16/byte_size`
- 不影响基线（不改 probe/DecisionEngine/Genome）

本文件只允许追加（additive-only）。

前置：
- Step67/68/69：research_bundle + entrypoint 生成与校验链路已冻结
- Step72 SSOT：`docs/v11/V11_STEP72_AGENT_METABOLISM_OBSERVABILITY_CONTRACT_20251230.md`
- Step72 Quant 已实现：`tools/generate_agent_metabolism_summary.py` + runner 集成

---

## 1) CI 必跑项（冻结）

Quant CI 必须新增一个 job 或 step（建议添加到 `.github/workflows/v11_evidence_gate.yml` 的 `verify_step54_integration` job 尾部）：

```text
python3 tools/test_step72_metabolism_acceptance.py
```

说明：
- 该测试脚本只读 `runs_step54_test/test_integration_run` 产物（由 Step54 integration test 生成），不需要联网。

预期：
- exit 0 → PASS
- exit 非 0 → FAIL（阻断合并）

---

## 2) 最小断言（硬）

测试至少验证：

### 2.1 文件存在
- `research_bundle/agent_metabolism_summary.json` 存在且可读
- `research_bundle/entry.json` 存在且可读
- `evidence_ref_index.json` 存在且可读

### 2.2 Step72 summary schema（最小）
- `contract_version == "V11_STEP72_AGENT_METABOLISM_SUMMARY_20251230.1"`
- `run_id`、`ts_utc`、`agent_count` 存在
- `m_intent` 存在，且至少包含一个 agent 记录（允许 hold-only）
- `m_resource_cpu_time.measurement_status` 存在
- `m_resource_api.measurement_status` 存在

### 2.3 entry.json 索引一致性
- `entry.json.artifacts[]` 中存在一条：
  - `kind == "agent_metabolism_summary_json"`
  - `rel_path == "research_bundle/agent_metabolism_summary.json"`
  - `sha256_16` 与 `byte_size` 非空

### 2.4 与 evidence_ref_index 复核一致
- `evidence_ref_index.json` 中存在 `rel_path == "research_bundle/agent_metabolism_summary.json"`
- 其 `sha256_16/byte_size` 与 entry.json 对应条目一致

### 2.5 不改变基线（写实）
- 不要求任何 probe 维度变化；不触发 Step52 对齐（该测试只验证产物与索引，不验证 feature_dim）

---

## 3) 失败语义（冻结）

- 任一断言失败 → CI FAIL（阻断合并）
- 不允许在 CI 中跳过（不得用条件判断把该测试静默跳过）

---

## 4) Research 侧交付物

- 本 SSOT 文档
- Quant 合入后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + workflow 修改位置 + CI 输出片段）


