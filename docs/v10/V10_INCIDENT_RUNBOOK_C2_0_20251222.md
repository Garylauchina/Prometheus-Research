# V10 Incident Runbook (C2.0) / 事故处置手册（C2.0）— 2025-12-22

> Purpose / 目的：把“出事了怎么办”从临场发挥，变成**可执行、可审计、可复盘**的固定流程。  
> Non-goal / 非目的：本手册不定义策略、不改 core 行为，不替代研发判断；它只定义**证据保全 + 止血动作 + 复盘输入**。

---

## 0) Golden rule（黄金规则）

- **Evidence first / 先保全证据**：任何“立即修复/改代码/重启容器”的冲动都要后置。
- **Ops only / 只动外壳层**：事故处置阶段允许的动作只能发生在 `ops/` 或基础设施层（Docker/进程/限流/kill switch）。  
  **禁止**在事故处置期间改 `prometheus/v10/core/`（否则证据链与裁决口径失效）。
- **One action, one record / 一次动作一条记录**：每个动作都要写入事件记录（见 2.3）。

---

## 1) Trigger definitions（什么算“事故/异常”）

### 1.1 Hard failure（硬故障：必须处置）

- 运行中出现 **NaN/Inf/溢出**（任何一个字段出现都算）
- `run_manifest`/`summary` **缺失或不更新**（证据链断裂）
- 资金三元组不闭合或出现明显异常（例如 `current_total` 与分项不一致）
- STOP 语义异常（已 STOP 但仍持续交易/持续写盘）
- raw evidence 分片/索引损坏或 hash 不一致

### 1.2 Degradation（退化：允许继续跑，但必须记录）

- 频繁 API error / rate limit / partial fill 激增（执行摩擦异常）
- `positions_quality` 降级（demo positions 不可信、fallback 异常、或重建输入不足）
- 健康指标刷屏（同一告警每 tick 输出）但系统仍在跑

### 1.3 “Three-dimensional resonance”（三维共振：重大风险信号）

定义（检测维度来自 V10 的现有观测/证据链，**不是新增策略逻辑**）：

- **Macro trend obvious**：价格/收益出现明显单边趋势（E 侧可见）
- **Friction spikes**：延迟/部分成交/拒单/费率异常上升（M raw evidence 可见）
- **Mass death**：短时间内死亡/强平显著上升（death_log 可见）

出现三维共振不等于“必须停止”，但属于**必须打包证据并升级处置等级**（见 2.2/2.3）。

---

## 2) Response workflow（处置流程：固定四步）

### 2.1 Step A — Stabilize（先止血：不让灾情扩大）

允许动作（按从轻到重）：

- 开启/加严外壳限流（rate limit / order throttle）
- 启动 **STOP**（优先），让系统进入可审计的 `interrupted`
- 若怀疑“失控下单”，执行 kill switch（终止容器/进程）

禁止动作：

- 不允许修改 core 逻辑来“让它别下单”
- 不允许删除 runs 目录或 raw evidence（证据污染）

### 2.2 Step B — Preserve evidence（证据包：必须完整）

目标：形成一个“Incident Evidence Bundle（IEB）”，使得第三方只看包就能复盘。

**最小证据包（Mandatory）**：

- `run_manifest.json`（脱敏可）
- `multiple_experiments_summary.json`（或等价 summary）
- `execution_fingerprint.json`（若 mode 为 demo/live）
- positions 证据（若启用）：
  - `positions_snapshot.json`（或等价）
  - `positions_reconstruction_raw_index.json`（若启用分片索引）
- M raw evidence（若启用）：
  - `m_execution_raw_index.json`（若启用分片索引）
- `ccxt_alignment_report.json`/`okx_rest_alignment_report.json`（若本次 run 声明需要对齐）
- `V10_EXECUTION_INTERFACE_DIFF_LOG_OKX_CCXT.md` 的相关条目引用（如果本次属于接口差异类事故）

**运行上下文（Mandatory）**：

- Docker image tag + digest（manifest 中必须有）
- mode（offline / okx_demo_sim / okx_demo_api / okx_live）
- run_id + results_dir
- 是否启用 STP（self-trade prevention）/净额执行/聚合执行（如适用）

### 2.3 Step C — Record decision（裁决记录：一页就够）

每次事故必须新增一份事件记录（Markdown，放 Research 仓库），文件名建议：

- `docs/v10/incidents/INCIDENT-YYYYMMDD-<short_slug>.md`

最低字段（Mandatory）：

- What happened（现象，1–3 句）
- When / run_id / mode / commit / image digest
- Severity（Hard failure / Degradation / Resonance）
- Stop action taken（是否 STOP / kill switch，何时）
- Evidence bundle path（证据目录路径 + 关键文件列表）
- Initial hypothesis（最多 3 条）
- Next action owner（下一步由谁做、做什么、何时复核）

### 2.4 Step D — Postmortem（复盘：只允许最小改动）

复盘输出必须回答：

- 根因属于哪个层：**core / ops / exchange interface / infra / data**
- 是否触发了 Gate 0（例如 NaN/Inf、证据链断裂、对齐口径缺失）
- 修复是否会改变“世界规则”（core 变更）？若会：必须按 `V10_ACCEPTANCE_CRITERIA.md` 触发回归裁决

---

## 3) Mapping to acceptance criteria（与验收门槛的关系）

- 本手册属于 **C阶段工程能力**：它不提高收益，但提高“我们不会自欺”的概率。
- 一旦进入 `okx_demo_api / okx_live`，IEB 能力应视为 **强制 Gate**（否则出现执行世界异常时无法审计）。


