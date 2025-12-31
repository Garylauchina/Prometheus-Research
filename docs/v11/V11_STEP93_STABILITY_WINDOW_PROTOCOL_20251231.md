# V11 Step 93 — Stability Window Protocol (1–2 months) — SSOT — 2025-12-31

目的：定义 V11 在稳定期（1–2 个月）内的**运行纪律、真值口径、变更边界与例行检查**，确保系统在真实环境中稳定运行且证据链可持续复核。

本文件只允许追加（additive-only）。

---

## 1) Truth Policy（冻结）

CI 真值口径：
- 只认 `main` HEAD 的最新成功 run（见 Step90：`docs/v11/V11_STEP90_CI_TRUTH_POLICY_AND_ALERTING_20251231.md`）。
- 历史红与旧 SHA rerun 均为非真值信号。

运行真值口径：
- 只认带有运行记录锚点的 run（`run_id` / `runs_root` / `build_git_sha` / `image_digest`），并能复跑定位（见 Step89）。

---

## 2) Change Policy（冻结）

稳定期内允许的变更类型（仅此三类）：
- 证据缺口补齐（additive-only：加字段/加文件/加 verifier，不改旧语义）
- 确定性 bug 修复（修复导致 FAIL/NOT_MEASURABLE 的确定性问题）
- 运维级降噪与可复跑性增强（不触碰交易语义与证据合同）

稳定期内禁止的变更类型：
- 架构级升级（例如 ROI 繁殖驱动 / tickless 事件驱动主循环替换）
- 改写/删除既有证据 schema 字段语义
- 放宽 fail-closed（不得为了“让它继续跑”而隐瞒缺证据）

---

## 3) Weekly Checklist（冻结）

每周至少一次（建议固定 UTC 时间）：
- Quant `main`：`V11 Evidence Gate (Step26)` 最新 run 必须 success（Step90 真值口径）
- Step89：真实运行验收链路仍可复核（Research closure + Quant record anchors 可直达）
- Step91/92：CI fixture gate 仍可 PASS（schema/verifier 未回归）
- Metabolism（Step72/73）：观测证据仍可生成，且 entry/index 一致性未破坏

产出：
- 若全部正常：无需额外文档（避免噪音）
- 若异常：必须创建 incident 文档（见 §4）

---

## 3.2) Rollout Cadence (First Flight → Real Flight, frozen)

为避免“入口混用/环境差异导致的反复排查”，稳定窗口内新增冻结的四阶段推进顺序（truth-first）：

- Stage 1 — **Mac First Flight**：在 Mac 本地把 First Flight 的各模块 truth-backed 测试跑通（每个 case 必须有交易所真值落盘）。
- Stage 2 — **VPS First Flight**：在 VPS 复现同一套 First Flight（同一 Quant main HEAD + anchors 对齐），确认真实环境仍可闭环。
- Stage 3 — **Mac Real Flight**：回到 Mac 实现/验证 `real_flight` 干净入口（不编排 tools；只做真实运行与落盘）。
- Stage 4 — **VPS Real Flight**：部署 `real_flight` 到 VPS 作为正式运行入口，并纳入本文件的周检/日检。

硬规则：
- 任一 Stage 的验收 run 必须具备运行记录锚点（`run_id/runs_root/build_git_sha/image_digest`），且能复跑定位。
- First Flight 阶段对“无交易所真值落盘”的 run 一概不采信（至少 `orders_history.jsonl`；filled 则 `fills/bills` 必须可 join）。

## 3.1) Daily Observability Minimum (Agent-first, stability window)（冻结）

稳定窗口的核心观测对象是 **Agent**。因此每日 run（尤其是 VPS demo 96 ticks）必须能在证据层回答：
- 哪些 Agent 行动（by `agent_id_hash`）
- 它们对应的基因参数锚点是什么（可用于聚类/谱系/回溯）

### 必须产物（run_dir，append-only / additive-only）

- `agent_roster.json`（新增，必须落盘）
  - 目的：提供 `agent_id_hash` → `gene_id`/`genome_schema_version`/`feature_contract_version`/`weights_sha256` 的可机读锚点，使“行为归因”可回扣到“基因特征”。
  - 最小字段（顶层）：
    - `run_id`
    - `build_git_sha`
    - `image_digest`
    - `feature_contract_version`
    - `feature_dimension`
    - `genome_schema_version`
    - `agents`（list）
  - `agents[]` 最小字段：
    - `agent_id`（可脱敏）
    - `agent_id_hash`（必需，join key）
    - `gene_id`（GenomeV11.gene_id，16 hex）
    - `weights_sha256`（对 genome 参数 JSON 的 sha256_16 或 full sha256；必须明确口径）
    - `weights_count`（应 == feature_dimension）
    - `metadata`（可选：seed/generation/parent_id 等；允许为空）

### 最小一致性校验（Verifier，冻结）

新增一个 read-only verifier（CI/runner gate 均可用）：
- 输入：run_dir
- 规则：
  - `agent_roster.json` 必须存在，且 JSON 可解析
  - 对 `order_attempts.jsonl` 中每一条 **agent-level** 记录（`agent_id_hash` 非 null）：
    - `agent_id_hash` 必须能在 `agent_roster.json.agents[].agent_id_hash` 找到
  - 对 `agent_roster.json.agents[]`：
    - `weights_count == feature_dimension`（fail-closed）
    - `gene_id` 必须为 16 hex
- Verdict：
  - 缺文件/缺字段/无法 join：FAIL（这是“演化观测缺口”，稳定窗口内视为 incident）

---

## 4) Incident Handling（冻结）

触发条件（任一满足即为 incident）：
- `main` HEAD 的关键 gate 失败（证据链/对账/refs/sha256 相关）
- 运行记录锚点缺失导致 run 不可定位或不可复跑
- 证据文件缺失/不可解引用/sha256 对不上
- 发现疑似“观测污染”（例如僵尸进程、非本 run 的交易活动）
- Agent-first 观测缺口：run_dir 无法把 agent-level 行为（`agent_id_hash`）回扣到基因锚点（`agent_roster.json` 缺失/不可用/无法 join）

处理流程（最小闭环）：
- 1) 创建 incident 文档（additive-only，记录时间、环境、run_id、headSha、复现命令、最小日志）
- 2) 修复（只做最小必要改动）
- 3) 用 `main` HEAD 最新成功 run 作为真值锚点收口（run link + headSha）

---

## 5) Deferred Ideas（非规范）

稳定期结束后可讨论的升级方向（先不实施）：
- Judgement v2 shadow：metabolism/ROI 作为观测与候选判定（不立即替换驱动）
- Event-driven contract：tickless 事件合同冻结与幂等/因果链证据化

---

## 6) Change Log（追加区）

- 2025-12-31: 创建 Step93 稳定期运行协议（冻结真值口径/变更边界/周检/incident 流程）。
- 2025-12-31: 追加 Agent-first daily minimum：run_dir 必须落盘 `agent_roster.json`（agent→genome anchors），并新增 startup `system_flatten` 作为稳定窗口的 fail-closed preflight（Quant main commit: `10bdcfb`）。


