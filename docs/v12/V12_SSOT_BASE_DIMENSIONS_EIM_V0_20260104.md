# V12 SSOT — Base Dimensions from Scanner (E / I / M) — v0 — 2026-01-04

目标：把 Scanner 已经能“真实落盘 + 可回放 + 可验收”的维度集合，冻结为 **基础维度（base dimensions）** 的输入合同，供后续建模/对齐/演化使用。

本文件 additive-only。

---

## 0) 基本维度原则（冻结）

- **E/I/M 三类维度均属于基础维度（base dimensions）**：可被演化筛选，但不得人为删减字段集合。
- 不可测必须走 **NOT_MEASURABLE**：用 `null + reason_codes`（或等价 mask/quality 结构）表达；禁止用 `0` 伪造“可测”。
- schema 变更只能 additive：新增字段/新增 reason_codes/新增验证规则；不得删除旧字段或改变旧语义。

---

## 1) E — Exogenous market info（market_snapshot）

**Canonical evidence**：`market_snapshot.jsonl`

- **SSOT（权威口径）**：`docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
- **最小 join anchors（冻结入口）**：
  - `snapshot_id`（字符串，run 内唯一）
  - `ts_utc`（ISO8601）
  - `inst_id`（v0 固定 `BTC-USDT-SWAP`）
  - `source_call_ids` / `source_message_ids`（回放锚点，来源不同但语义一致）
- **NOT_MEASURABLE 纪律（冻结入口）**：
  - 任一字段不可得 → `null + reason_codes`
  - overall verdict 语义以对应 SSOT/verifier 为准（fail-closed）

说明：本文件不重复列举 E 字段全集；以 E schema SSOT 为准，避免多处漂移。

---

## 2) I — Identity / account-local state truth（positions snapshot）

**Canonical evidence**：`position_snapshots.jsonl`

用途（冻结）：
- 为非 order 参数空间（例如 `mgnMode/posSide/leverage`）提供 **读真值**，用于对齐与审计（避免“写了但没生效/读错对象”）。

最小 record schema（v0 frozen entry；只增不改）：
- `snapshot_id`：string（run 内唯一）
- `ts_utc`：string（ISO8601）
- `account_id_hash`：string（account-local truth anchor）
- `inst_id`：string（例如 `BTC-USDT-SWAP`）
- `mgn_mode`：string（`cross|isolated`；若不可得 → null + reason）
- `pos_side`：string|null（`long|short|net`；与 `posMode` 相关；不可得 → null + reason）
- `lever`：string|number|null（实际杠杆倍数；不可得 → null + reason）
- `pos`：string|number|null（持仓量；不可得 → null + reason）
- `avg_px`：string|number|null（均价；不可得 → null + reason）
- `upl`：string|number|null（未实现盈亏；不可得 → null + reason）
- `evidence_refs`：object（必须存在；允许为空）
  - `exchange_api_call_ids`：array[string]（可回指到 `okx_api_calls.jsonl` / `exchange_api_calls.jsonl`）

NOT_MEASURABLE reason_codes（入口词表；可追加）：
- `not_measurable:positions_truth_unavailable`
- `not_measurable:positions_response_missing_fields`
- `not_measurable:account_id_hash_unknown`

---

## 3) M — Market interaction / execution friction（interaction impedance）

**Canonical evidence**：`interaction_impedance.jsonl`

用途（冻结）：
- 这是 **account-local 交互摩擦真值**（与网络/限速/权限/账户模式强相关），可作为后续裁决输入/建模维度，但不能当作“全球市场真值”共享。

最小 record schema（v0 frozen entry；只增不改）：
- `ts_utc`：string（ISO8601；窗口结束时刻或统计写入时刻）
- `window_ms`：number（统计窗口长度；或使用 begin/end 两字段，二选一入口）
- `account_id_hash`：string
- `attempts`：number
- `okx_reject_count`：number（业务拒绝：OKX `code!=0` 或 `sCode!=0`）
- `rate_limited_count`：number（限速拒绝/429/50011/50061 等归类）
- `http_error_count`：number（HTTP/连接错误，不包含业务拒绝）
- `avg_latency_ms`：number|null
- `verdict`：string（`PASS|NOT_MEASURABLE|FAIL`）
- `reason_codes`：array[string]（可为空）
- `evidence_refs`：object（必须存在；允许为空）
  - `exchange_api_call_ids`：array[string]

NOT_MEASURABLE 纪律（冻结入口）：
- “业务拒绝但证据完整”优先判 `NOT_MEASURABLE`（而不是 FAIL）。
- “缺证据/缺 required files/无法回放”才允许 FAIL（fail-closed）。

---

## 4) Cross-links（只读）

- E schema SSOT：`docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
- Non-order parameter space SSOT：`docs/v12/V12_SSOT_OKX_ACCOUNT_POSITION_AND_PRETRADE_PARAMETER_SPACE_V1_20260103.md`
- Pipeline + alignment SSOT：`docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`

---

## 5) Verifier tool（冻结入口）

工具（stdlib-only）：
- `tools/v12/verify_base_dimensions_eim_v0.py`

Required files（缺一即 FAIL；即使为空文件也必须存在）：
- `run_manifest.json`
- `market_snapshot.jsonl`（E）
- `position_snapshots.jsonl`（I）
- `interaction_impedance.jsonl`（M）
- `errors.jsonl`

强制规则（fail-closed）：
- 严格 JSONL：每行必须是合法 JSON object（禁止注释/尾逗号/多行 JSON）。
- I/M 最小 schema 必须满足（见本文件 §2/§3）。

Exit codes（冻结）：
- PASS / NOT_MEASURABLE → exit 0（NOT_MEASURABLE 必须打印 WARNING）
- FAIL → exit 2

Usage:
- `python3 tools/v12/verify_base_dimensions_eim_v0.py --run_dir <RUN_DIR> --output <REPORT.json>`


