# V11 Incident — Agent Genome Anchor Not Landed (Clustering Blocked) — 2025-12-31

目的：记录一个稳定窗口（Step93）下的**观测缺口 incident**：虽然交易链证据（P0–P5 / Step88）可核验闭环，但 **agent-level 行为无法在证据层回扣到 genome/weights 锚点**，导致聚类/谱系分析不可复核。

本文件只允许追加（additive-only）。

---

## 1) Summary

- **Impact**：无法对 Agent 做基因特征核查与可复核聚类（观测目标偏离：只剩“交易审计”，缺“演化观测”）。
- **Severity**：High（稳定窗口核心目标受阻）。
- **Type**：Observability gap (Agent-first) / Evidence landing gap（非交易证据链事故）。

---

## 2) Trigger / Evidence

在 VPS demo daily run 中，我们可证明某笔订单由某个 `agent_id_hash` 触发，并完成 Step88 PASS，但 run_dir 内缺少能把 `agent_id_hash` 映射到 genome 参数锚点的可机读证据文件。

示例（已观测到的事实锚点）：

- run_id: `run_daily_vps_okx_demo_api_20251231T084358Z`
- run_dir: `/var/lib/prometheus-quant/runs/run_daily_vps_okx_demo_api_20251231T084358Z`
- order_attempts.jsonl 记录包含：
  - `agent_id_hash="58e79269a0479524"`
  - `intent_kind="agent_intent_open"`
  - `client_order_id="v11bb2a6176000001"`
- orders_history / fills / bills / Step88 verifier: PASS

缺口：
- run_dir 未提供 `agent_id_hash → gene_id / weights_sha256 / genome_schema_version / feature_contract_version` 的稳定锚点文件（例如 `agent_roster.json`）。

---

## 3) Expected vs Actual

### Expected (Agent-first observability)

对于任一 agent-level 行为（`order_attempts.jsonl` 中 `agent_id_hash` 非 null）：
- 必须能从 run_dir 的证据中追溯到该 agent 的 genome 参数锚点（至少 gene_id + weights_sha256），用于聚类/谱系/回溯。

### Actual

- 目前证据链可以回答 “哪一个 agent 下了单（agent_id_hash）”。
- 但无法在证据层回答 “该 agent 的基因特征（genome 参数锚点）是什么”。

---

## 4) Root Cause (SSOT gap)

经查 Research SSOT：
- Step93 原始版本未硬要求 run_dir 落盘 `agent_roster.json`（agent→genome 锚点），因此实现侧不会被 gate 约束。

结论：
- 这是 **SSOT/contract 未覆盖的观测缺口**，需要在 Step93 追加冻结规范，并在 Quant 实现最小落盘与 verifier。

---

## 5) Proposed Fix (additive-only)

### 5.1 Step93 SSOT addendum

- 增加 run_dir 必须产物：`agent_roster.json`
- 增加最小 verifier：对 `order_attempts.jsonl` 的 agent-level 记录，必须能 join 到 roster；并校验 weights_count 与 feature_dimension 一致。

### 5.2 Quant implementation (minimal)

- 在 runner 生成 run_dir 后写入 `agent_roster.json`
- roster 至少包含：`agent_id_hash`、`gene_id`、`weights_sha256`、`weights_count`、`feature_contract_version`、`genome_schema_version`
- 新增 `tools/verify_step93_agent_roster.py`（或等价命名）用于 CI/runner gate

---

## 6) Closure Criteria

当满足以下条件时可关闭 incident：
- `agent_roster.json` 在 VPS daily run 中稳定落地
- verifier 对当日 run_dir 给出 PASS
- 任一 agent-level order_attempt 都可在 roster 中找到一致的 genome 锚点

---

## 7) Fix Implemented (Quant)

Quant `main` 已实现（additive-only）：
- Commit: `10bdcfb` — `chore(step93): land agent_roster + enforce startup system_flatten (fail-closed)`
- Changes:
  - 新增 `prometheus/v11/ops/step93_helpers.py`：生成 `agent_roster.json` + 执行 startup `system_flatten` preflight
  - 修改 `prometheus/v11/ops/run_v11_service.py`：引入上述 helper（落盘 roster + 启动清仓）
  - 新增 `tools/verify_step93_agent_roster.py`：fail-closed 验证 roster schema + join

Pending closure evidence（需要 VPS 跑一次新 main 并产出 run_dir）：
- run_dir 内存在 `agent_roster.json`
- `run_manifest.json` 内存在 `startup_flatten` 且 completed=true
- `python3 tools/verify_step93_agent_roster.py <run_dir>` = PASS

---

## 8) Closure Evidence (VPS)

已满足 closure criteria（VPS evidence）：

- Quant main build_git_sha: `10bdcfb7379e0ba9a72fed4f3732810e1ebd8a97`
- run_id: `run_daily_vps_okx_demo_api_20251231T094159Z`
- run_dir: `/var/lib/prometheus-quant/runs/run_daily_vps_okx_demo_api_20251231T094159Z`
- startup_flatten:
  - enabled=true
  - positions_detected=0
  - orders_submitted=0
  - completed=true
  - reason_code=`no_positions_detected`
- `agent_roster.json` exists (662 bytes)
- `python3 tools/verify_step93_agent_roster.py <run_dir>`: PASS

Status:
- ✅ incident closed (evidence landed + verifier PASS)


