# V11 execution_world Closure Allowlist (Run-time dependency whitelist) — 2025-12-27

目的：把 “V11 execution_world 的运行闭包（closure）” 明确冻结成 **白名单**，用于防止 legacy/v10 路径被误接回执行链路（骑士事故类型风险）。  
本文件是 **验收门槛**：只要违反白名单，即视为 execution_world world-mixing 风险 → 必须 STOP/拒绝发布/拒绝长跑。

适用范围：
- Prometheus-Quant（实现仓库）的 execution_world runner / entrypoints
- 任何会触达交易所 IO / 下单能力的运行产物（build artifact）

---

## 0) 基本原则（hard）

- **execution_world 运行产物必须不包含 v10/legacy 的可达路径**（不是“运行时不调用”，而是“依赖闭包里不存在”）。
- **写能力（place/cancel/amend/close）只能存在于 BrokerTrader**；core/runner 无权直接接触写接口。
- **Fail closed**：无法证明闭包合规时，宁可 STOP/拒绝发布，也不允许“先跑起来再说”。

---

## 1) 允许的能力边界（capability boundary）

### 1.1 允许（Allowed）

- **Core（intent-only）**：只产出 `intent_action`，不触达交易所 IO
- **BrokerTrader（唯一写入口）**：唯一允许执行交易所写端点的模块
- **Ledger / ProbeGating（只读 + 聚合）**：只读拉取真值并输出 probe/quality，不发明真值
- **ExchangeAuditor（只读）**：独立只读校验，不干预执行
- **RunArtifacts（证据/哈希/IEB）**：生成 run_dir 与证据包

### 1.2 禁止（Forbidden）

- runner/core **直接**调用 connector/exchange client 的写 API（绕过 BrokerTrader）
- 在 execution_world 下使用 offline_sim 的“内部成交/内部仓位/内部资金变化”逻辑作为真值
- 引入“结果导向”特征（成交/收益/ROI）作为 C 维度输入（除非单独立约并通过消融验收）

---

## 2) 运行闭包白名单（dependency allowlist）

> 说明：白名单按“概念模块”描述，具体实现文件路径在实现仓库中应映射到 `prometheus/v11/...`（或等价命名空间）。  
> 验收关注的是：**execution_world entrypoint 的依赖图必须只落在白名单之内**。

- **Core / intent-only**
  - Genome / DecisionEngine / Agent / SystemManager（无 IO）
  - decision trace（append-only evidence writer，仅写本地文件）

- **Truth & probes**
  - Ledger（truth snapshots, append-only）
  - ProbeGating（truth_profile + mask/reason_code + STOP policy）
  - 最小历史投影 probes（capital_health_ratio、position_exposure_ratio）
  - C(t-1 intent) social probe（作为消融开关；非真值）

- **Execution & registry**
  - BrokerTrader（唯一写入口）
  - Order Confirmation Protocol（P0–P5）
  - execution freeze（对证据链缺口 fail closed）

- **Audit**
  - ExchangeAuditor（只读交叉核验，evidence-only）

- **RunArtifacts**
  - run_manifest / FILELIST / SHA256SUMS / errors.jsonl / IEB packaging

---

## 3) 明确禁止的依赖（denylist）

以下任意一条出现在 execution_world 运行闭包中，均视为 **FAIL**：

- `prometheus/v10/**`（或任何 legacy 命名空间）被 execution_world 入口直接或间接 import
- 任何 `offline_sim` 的成交模拟、仓位模拟、资金模拟模块被 execution_world 入口依赖
- 任何绕过 BrokerTrader 的下单/撤单/改单调用路径
- **任何 CCXT 写链路依赖**：execution_world 闭包内出现 `ccxt`（或其封装 writer）即 FAIL  
  - 解释：CCXT 仅允许用于 **审计/对齐工具（read-only, probe-only）**，不得进入执行世界写路径（baseline hard rule）

> 注：研究/对照用 legacy 代码允许存在于仓库，但必须在 execution_world 闭包中 **物理不可达**。

---

## 4) 验收方式（how to enforce）

V11 baseline 推荐采用“三道门”叠加（越靠前越便宜）：

1) **静态依赖扫描（build-time gate）**
   - 对 execution_world entrypoint 做 import graph 扫描
   - 发现 `v10/legacy` 命名空间 → 直接失败

2) **运行时自证（run_manifest）**
   - `run_manifest.json` 写入 `closure_allowlist_version`
   - 写入 `entrypoint` 与 `module_namespace`（v11）

3) **证据包校验（post-run / CI）**
   - IEB 内包含依赖清单与哈希（用于事后复核）

本文件冻结点：
- `closure_allowlist_version = 2025-12-27.1`
- 只允许新增（additive-only）；若要移除/改变规则语义，必须提升 major 并重跑 Gate/PROBE。


