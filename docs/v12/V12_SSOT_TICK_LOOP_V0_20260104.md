# V12 SSOT — Tick Loop v0 (Polling World Input, Evidence-First) — 2026-01-04

目标：冻结 V12 主线的世界输入驱动方式：**tick 周期轮询**（polling），并将其输出变成可回放、可机验的证据序列。

本文件 additive-only。

---

## 0) 定位（冻结）

- Tick loop 是 V12 主线的“世界输入主循环驱动器”（暂不依赖 DSM/WS event-driven）。
- Tick loop **不做策略**：只负责按固定节奏采样世界外显事实（E），并落盘证据。
- Tick loop 必须遵守：
  - **strict JSONL**
  - **fail-closed / NOT_MEASURABLE**
  - **evidence replayability**

---

## 1) Inputs（冻结）

- `inst_id`：`BTC-USDT-SWAP`（v0 固定）
- `mode`：`okx_demo_api|okx_live_api`
- `tick_interval_ms`：每次采样间隔（例如 1000ms）
- `tick_count_target`：目标 tick 数（例如 120）

---

## 2) Outputs (run_dir)（冻结）

### 2.1 Required files（缺一即 FAIL）

- `run_manifest.json`
- `okx_api_calls.jsonl`
- `errors.jsonl`
- `market_snapshot.jsonl`（必须非空，且应包含多行 tick 序列）

### 2.2 Canonical schema（引用）

- `market_snapshot.jsonl` 必须符合 E schema SSOT：
  - `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
  - required fields：`ts_utc, inst_id, snapshot_id, source_endpoints, quality{overall,reason_codes}`

---

## 3) Manifest contract（冻结入口）

`run_manifest.json` 最小必含（字段名可实现差异，但语义必须等价）：

- `run_id`（string）
- `run_kind`：必须为 `production`（tick loop 属主线生产驱动；建模工具不得冒充 tick loop）
- `mode`（string）
- `inst_id`（string）
- `tick_loop`（object）：
  - `tick_interval_ms`（int）
  - `tick_count_target`（int）
  - `tick_count_actual`（int）
  - `start_ts_utc`（string）
  - `end_ts_utc`（string）
- `verdict`（`PASS|NOT_MEASURABLE|FAIL`）
- `reason_codes`（array[string]）

---

## 4) Tick semantics（冻结）

- Tick 的输出是 `market_snapshot.jsonl` 的一行（或一组行，但 v0 建议 1 tick = 1 snapshot）。
- 时间锚点：
  - `ts_utc` 必须单调不减（允许极小抖动但不得回退；回退视为 FAIL）。
- 可回放性：
  - `source_endpoints` 必须能在同 run_dir 的 `okx_api_calls.jsonl` 中找到对应证据（best-effort 匹配）。
- fail-closed：
  - 若连续 K 个 tick 都不可测（例如 endpoint 全挂/网络阻断），必须把 run 判为 `NOT_MEASURABLE` 并写 reason_codes（K 可在实现中配置，v0 推荐 K>=10）。

---

## 5) Acceptance (V12.3)（冻结入口）

PASS（必须全部满足）：
- Required files 全部存在
- `market_snapshot.jsonl` 非空，且 `tick_count_actual >= tick_count_target`
- `market_snapshot.jsonl` 通过 E schema verifier（见下）
- `ts_utc` 单调不减，`snapshot_id` 在 run 内唯一
- `run_manifest.json.run_kind == "production"`

NOT_MEASURABLE（允许）：
- 证据完整且 strict JSONL 合规，但由于网络/接口可用性导致**大比例不可测**（必须有可统计 reason_codes）

FAIL（任一触发即 FAIL）：
- 缺 required files
- JSONL 非 strict
- `ts_utc` 回退 / `snapshot_id` 大量重复
- `market_snapshot` 不符合 canonical required fields

---

## 6) Verifiers（冻结入口）

单 run 校验：
- E schema verifier：
  - `python3 tools/v12/verify_scanner_e_schema_v0.py --run_dir <RUN_DIR>`
- Tick loop verifier：
  - `python3 tools/v12/verify_tick_loop_v0.py --run_dir <RUN_DIR> --min_ticks <N> --max_backward_ms 0`


