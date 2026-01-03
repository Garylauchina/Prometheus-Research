# V11 程序员AI操作规则（超简洁版）— 2025-12-27

**实现指令的默认附带链接**：`docs/v11/V11_PROGRAMMER_AI_OPERATING_RULES_20251227.md`

**实现前必读（只看这 3 个）**
- `docs/v11/V11_BASELINE_CHANGELOG_20251226.md`
- `docs/v11/V11_DESIGN_EXECUTION_WORLD_20251227.md`
- `docs/v11/V11_EXECUTION_WORLD_CLOSURE_ALLOWLIST_20251227.md`

---

## 0) 工作方式（必须遵守）

- **先对齐再动手**：开始实现前，用 3 行以内确认：目标/触及文件/是否影响 contract 或 evidence schema。
- **最小改动集**：只改本次目标所必需的最少文件；禁止“顺手重构/顺手清理”。
- **不确定就停**：遇到契约冲突、字段语义不明、需要新增 schema/版本号时，先停下发问，不要擅自定口径。

---

## 1) 禁止做（Do NOT）

- **不要**在 `execution_world` 内部模拟成交/仓位/资金/费用为真值（严禁“自认为成交”）。
- **不要**绕过 BrokerTrader 直接调用 connector/exchange client 的写接口（下单/撤单/改单/强平）。
- **不要**把 CCXT 引入 execution_world 的写路径/运行闭包（baseline hard rule：CCXT 仅允许审计/对齐的 read-only, probe-only 工具使用）。
- **不要**在真值缺失时用 `0`/默认值冒充（除非同时输出 `mask/quality/reason_code` 明确“占位”）。
- **不要**把成交/收益/ROI 之类“结果信号”喂进 C 维度（除非另立契约并通过消融验收）。
- **不要**让 `execution_world` 入口依赖 `v10/legacy` 路径（闭包里出现即 FAIL）。
- **不要**改冻结契约的旧语义（只允许新增字段；语义变更=版本提升+重跑 PROBE）。
- **不要**在未明确指令下做：删除文件/大范围重命名/批量格式化/“清理无用代码”。

---

## 2) 必须做（Must）

- `execution_world`：core 只产出 `intent_action ∈ {open, close, hold}`（intent-only）。
- 所有交易写动作必须走 **BrokerTrader**；ack 后必须按协议完成 **P2 终态可回查**（否则 freeze/STOP）。
- 所有关键 evidence **append-only**，且 run_dir 必须可校验（filelist+sha256）。
- `run_manifest.json` 必须记录：`truth_profile` + 本次实现相关的 `contract_version`（或等价版本字段）。
- **运行记录锚点（必须，防证据“跑过但找不到/对不齐”）**：
  - 每次真实运行必须在输出 banner + `run_manifest.json` 写入可校验的构建指纹（至少：`build_git_sha`；不得为 `unknown`）。
  - 必须明确产物位置：`runs_root`（host 路径或 docker volume 名）+ `run_id`（run_dir 目录名），以便第三方定位并复核 `okx_api_calls.jsonl/order_attempts.jsonl/...`。
  - 若使用容器运行：必须记录 `image_digest`（或等价不可变标识），避免“Mac 与 VPS 跑的不是同一镜像”而无法机器判定。
- ExchangeAuditor：`NOT_MEASURABLE` 必须打印 WARNING 且 `exit_code=0`；`FAIL` 必须 `exit_code=2`；报告内必须写入 `exit_code` 与拆分后的 `contract_versions`（审计器/证据生产者/协议版本）。
- **保持英文现状**：代码/注释/日志中的英文口径不做“翻译式重写”，除非为契约一致性所必需。

- **First Flight / Real Flight 入口纪律（truth-first）**：
  - **First Flight**：从 first_flight 开始的模块测试必须真实对接交易所（OKX demo），并在 run_dir 内落盘交易所真值（至少 `orders_history.jsonl`；若 filled 则 `fills.jsonl`/`bills.jsonl` 必须存在且可 join）。**没有真值落盘 → 一概不采信**。
  - **Real Flight**：独立的干净运行入口（只做真实运行与落盘，不加载 tools 编排），用于后续稳定期运行。
  - **停止使用 `run_v11_service.py` 作为 flight 验收入口**：允许保留兼容/历史复跑，但后续验收命令不得依赖它（标记 deprecated，不强删以免断链）。
  - 验收必须提供：固定 `runs_root` + `run_id` + 复跑命令 + Step88/相关 verifier 的 PASS/FAIL 输出（不可口头描述代替）。

- **Leverage truth binding（First Flight 起强制）**：
  - 若 V11 的 Genome/Decision 声称存在“杠杆偏好/杠杆上限”，则：
    - Decision evidence（`decision_trace.jsonl`）必须写入 `leverage_target`（以及 source/reason_code）
    - Trader input（`order_attempts.jsonl` / api_calls）必须包含 `leverage_target`，并能被交易所真值核验已生效或明确 NOT_MEASURABLE
  - 禁止“基因里有 leverage 但执行链完全沉默”的情况（这是不可审计缺口）。

---

## 2.1) 操作规范（C 路线：仅靠规程约束，不依赖 MCP）

目的：让程序员AI的“操作”也符合证据链与 fail-closed，避免临时调试绕过 run_dir/manifest，造成不可复现与不可归因。

硬规则（必须遵守）：

- **禁止裸跑（No bare runs）**：
  - 任何涉及交易所读写/审计/结算/验证的运行，都必须产生 `run_dir`，并在 `run_manifest.json` 内写清 `runs_root/run_id` 与关键版本指纹（至少 `build_git_sha`）。
  - 禁止只给终端输出而不落盘证据；禁止“跑过了但找不到 run_dir”。

- **禁止绕过证据链（No direct probes outside evidence）**：
  - 禁止用临时 `curl`、临时脚本直接打 OKX（尤其是写接口）；必须走系统入口（flight runners / tools verifiers）。
  - 若确需临时探测：也必须落盘到某个 `run_dir`，并记录 `okx_api_calls.jsonl` 与 `errors.jsonl`（否则视为无效样本）。

- **严格 JSONL（Strict JSONL, no exceptions）**：
  - 所有 `*.jsonl` 证据文件必须“一行一个合法 JSON object”，不得包含注释、不得包含 `_note` 这类说明性字段。
  - 任意不合法 JSONL 必须被 verifier 判为 FAIL（或至少 structure_check FAIL），禁止口头放行。

- **共享状态冻结（Shared-state freeze, as policy）**：
  - 在“多 Agent 共享账户/共享执行通道”的阶段，账户级共享状态默认冻结为 `system_fact`（例如 `posMode/mgnMode`），不得让 Agent 直接碰撞这些旋钮。
  - 若未来开放：只能走“Agent 提议（proposable）→ Broker gate-control 执行 → write+read truth 闭环证据”的路径；否则一律 NOT_MEASURABLE。

说明（入口链接，不影响当前版本节奏）：
- V12 对“系统级/工程级公理”的更完整汇总：`docs/v12/V12_SSOT_AXIOMS_SYSTEM_AND_ENGINEERING_20260103.md`

---

## 2.2) Future: MCP（占位，不作为当前验收项）

如果未来启用 Cursor MCP 来规范程序员AI操作，则应遵循：
- **写侧能力默认禁用**：只有在具备 run_dir 落盘与 verifier 可机验闭环时才允许开放。
- **所有工具必须输出可 join 的证据锚点**：`event_id/evidence_ref/run_id`，避免绕过证据链。
- **MCP 只是“受控入口”，不是新的旁路**：启用后反而应减少裸命令与临时脚本。

---

## 3) 交付物（每次改动至少给出）

- **改动说明**：改了什么、为什么、对应哪条 SSOT/Design 条目（引用文件路径即可）。
- **证据文件清单**（如本改动涉及执行/真值/冻结）：需要新增/更新哪些 evidence 文件（文件名即可）。
- **FAIL 条件**：本改动下，哪些条件触发 freeze/STOP（列 3 条以内）。


