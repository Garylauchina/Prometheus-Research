# V11 Step 27 — Step 26 Evidence Package: Minimal Review Checklist — 2025-12-29

目的：把 **V11 Step 26（DecisionEngine 输入接入 MFStats/Comfort）** 的“可复核状态”冻结成一份 **最小审计清单**（human checklist + machine-verifiable）。  
原则：**fail-closed**（缺证据=不可证明=FAIL），且 **additive-only**（后续只允许追加检查项，不允许改旧语义）。

适用范围：
- execution_world 的单次 run 目录（run_dir），包含 `run_manifest.json` 与 append-only 证据文件。
- 仅验证：**输入合同/固定维度/证据链闭合/mask 纪律**。不验证策略效果与盈利。

---

## 1) 必备文件（缺一即 FAIL）

- `run_manifest.json`
- `decision_trace.jsonl`
- `e_probes.jsonl`（E probes 证据）
- `mf_stats_ticks.jsonl`（MFStats 事实统计）
- `comfort_ticks.jsonl`（Comfort 投影）
- `FILELIST.ls.txt`（证据包索引）
- `SHA256SUMS.txt`（证据包 hash）

说明：
- 若某 run 设计上不产生某文件（例如未启用某模块），必须在 `run_manifest.json` 里以**写实字段**声明，并给出 `reason_code`；否则视为证据缺口。

---

## 2) run_manifest.json（最小必查字段）

### 2.1 feature_contract（Step 26 关键字段）

必须存在：
- `feature_contract.contract_version`（示例：`V11_FEATURE_PROBE_CONTRACT_20251228.1`）
- `feature_contract.dimension`（示例：10）
- `feature_contract.probe_order`（固定顺序，per-run frozen）
- `feature_contract.probe_categories`（至少包含：`E_probes`、`MF_stats`、`comfort`）

硬规则：
- `dimension == len(probe_order)` 必须成立，否则 FAIL。
- 同一 run 内不得出现两个互相矛盾的 `probe_order` 版本（例如 manifest 与 trace 不一致）→ FAIL。

### 2.2 决策合同版本（可追溯）

必须存在（字段名允许实现差异，但语义必须等价）：
- DecisionEngine 的 `decision_contract_version`（示例：`V11_DECISION_ENGINE_PURE_20251228.1`）

---

## 3) decision_trace.jsonl（最小必查字段与纪律）

对每个 tick 的 tick_summary（或等价记录）至少要求：
- `tick`、`run_id`
- `feature_contract_version`
- `total_features_count`
- `effective_features_count`（mask=1 的数量）
- `evidence_refs`：至少能回指到：
  - `e_probes.jsonl` 的行号
  - `mf_stats_ticks.jsonl` 的行号
  - `comfort_ticks.jsonl` 的行号

硬规则（mask discipline）：
- `0 <= effective_features_count <= total_features_count`
- 当 `mf_stats` 不可测（或被 mask=0）时：
  - DecisionEngine 必须仍能输出决策（不崩溃）
  - 且不得把不可测维度当作真值（必须体现在 `effective_features_count` 与 mask 摘要里）

边界声明（观测不执法）：
- 文档审计中不得出现 “comfort 阈值触发强制 HOLD/STOP” 的决策口径；硬门只来自 ProbeGating/证据链失败。

### 3.1 写路径参数对齐（Decision 输出契约，First Flight 起冻结）

当 `decision_trace.jsonl` 中出现 agent-level 的“写路径 intent”（例如 intent_action 为 open/close，或显式标记 will_trade=true），必须能从同一条 agent_detail（或可 join 的同 tick 记录）中读到“交易员可执行”的最小订单参数集合（字段名允许实现差异，但语义必须等价）：
- `inst_id`
- `td_mode`（cross/isolated）
- `pos_side`（long/short/net）
- `order_type`（market/limit）
- `requested_sz`（合约张数）
- `limit_px`（仅当 order_type=limit 时必填；market 时必须为 null）
- `leverage_target`（必填；不得沉默）

硬规则：
- 缺任一必填字段 → 该 tick 的写路径 intent 证据应判为 NOT_MEASURABLE（或 FAIL，取决于 gate 级别），并给出 `reason_code`；不得用默认值伪造（例如 leverage 缺失导致交易所用默认杠杆）。
- 若该 tick 无写路径 intent（hold），允许上述字段为 null/unknown，但不得伪造为 0。

---

## 4) evidence_refs 行号可回查（闭合性）

要求：
- `decision_trace.jsonl` 内的 `evidence_refs.{file,line}` 必须能在对应 jsonl 文件里定位到同一个 tick/run_id（或等价锚点）。
- 若采用范围引用（start/end），必须保证范围内记录连续且可解释。

FAIL 条件：
- 行号越界、文件缺失、tick 不一致、run_id 不一致、或引用的记录缺少必要字段。

---

## 5) FILELIST + SHA256SUMS（证据包可验）

要求：
- `FILELIST.ls.txt` 必须包含本清单 §1 的所有文件。
- `SHA256SUMS.txt` 必须包含本清单 §1 的所有文件 hash。

FAIL 条件：
- FILELIST 或 SHA256SUMS 缺失/不包含关键文件。
- 任一关键文件存在但未被 hash 索引覆盖（形成证据盲区）。

---

## 6) 一键校验脚本（推荐）

建议使用同仓库的校验脚本（只读 run_dir，fail-closed）：
- `tools/verify_step26_evidence.py --run-dir <RUN_DIR>`

退出码（冻结）：
- `0`：PASS（满足最小可复核清单）
- `1`：FAIL（证据缺口/字段不一致/引用不可回查）
- `2`：ERROR（脚本自身异常/输入不可读）


