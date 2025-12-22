# V10 Fence Audit Checklist (Principle 4) / 围栏审计核对表（原则4：自然选择）— 2025-12-22

> Goal / 目标：把“任何人为参数不能偷偷变成策略本身”落成一张可执行的审计表。  
> Output / 输出：每次审计给出 **Pass/Fail + 证据位置**，不允许“感觉没问题”。

---

## 0) How to use（怎么用）

- **Scope**: include **ops/runner/analysis**, not only `core/`.
- **Rule**: Anything that changes **action space** is a candidate **strategy fence**.
- **Evidence**: every item must cite **file/function/snippet** and (if runtime) **telemetry counter id**.

Recommended output format (per audit run):

- `fence_inventory.md` update (append-only entries)
- `gating_telemetry.json` for at least one representative run
- A one-page summary: `PASS/FAIL + top 5 fences by block_rate`

---

## 1) Classification（分类判定：生态 vs 策略）

### 1.1 Ecological fence (allowed) / 生态围栏（允许）

Pass if **all true**:

- It is an exchange/physics/lifecycle constraint (margin/liquidation/fees/slippage/resource limits/death-repro rules/collapse-reboot).
- It does **not** encode “when to trade” as a preference.
- If it blocks actions, the blocking reason is **physical** (e.g., rate limit, max open orders, insufficient margin).

### 1.2 Strategy fence (forbidden in decision path) / 策略围栏（禁止潜伏在决策路径）

Fail if **any true**:

- It says “only trade when…” using thresholds derived from features/signals.
- It gates enter/exit/size based on handcrafted rules that look like strategy design.
- It silently replaces missing external data with “reasonable defaults” that create a stable “default world”.

---

## 2) Checklist items（核对项：逐条 Pass/Fail）

### C1 — Action space integrity（行为空间完整性）

- **C1.1**: No hard gate that blocks entry/exit/add/size based on signal magnitude or handcrafted thresholds.  
  - **Pass evidence**: no such gates in decision path (`Genome + Features -> Action`).  
  - **Fail example**: `if abs(signal) < 0.7: return HOLD`.

- **C1.2**: Any safety/risk limit that blocks order send lives in **ops/infra** and is classified as ecological, not strategy.  
  - **Pass evidence**: limiter exists, but it is purely notional/rate/margin based and emits telemetry.

### C2 — Missing data honesty（缺字段诚实，不造“默认世界”）

- **C2.1**: Missing/unreliable external fields must be `null + reason`, never “reasonable defaults”.  
  - **Pass evidence**: explicit `reason` fields; fallbacks are named.

- **C2.2**: Any fallback that affects behavior has a fence id and telemetry counter.  
  - **Pass evidence**: `FENCE_*` id exists; telemetry shows trigger/block counts.

### C3 — Visibility & measurability（可见性与可测量）

- **C3.1**: Fence Inventory is complete and includes **ops** gates (rate limiter, live auth guard, positions fallback, etc.).  
  - **Pass evidence**: inventory entries with location and what_it_gates.

- **C3.2**: Per-run `gating_telemetry.json` exists and is referenced by run artifacts (manifest/summary).  
  - **Pass evidence**: artifact exists; counters are non-empty.

### C4 — Falsifiability（可否证：必须可做对照）

- **C4.1**: Every `man_made` fence that touches trading behavior has a disable/ablation path (ops/runner only).  
  - **Pass evidence**: documented switch and command.

- **C4.2**: Counterfactual run exists (same commit/config/seed/window), and reports include block_rate delta and endpoints delta.  
  - **Pass evidence**: A/B report with `system_roi`, `extinction_rate`, and fence `block_rate`.

### C5 — Reporting discipline（报告纪律）

- **C5.1**: Any claim about “natural selection behavior” must state whether man-made block_rate is low.  
  - **Pass evidence**: summary includes ecological vs man-made pressure statement.

---

## 3) Minimum “Fail-fast” rules（最低一票否决）

Fail the audit if any of the following holds:

- A strategy fence exists inside the decision path.
- Missing external data is silently defaulted in a way that affects actions.
- `gating_telemetry.json` is missing for runs used in claims.
- A high-block man-made fence exists but has no counterfactual/ablation.

---

## 4) Where this checklist is anchored（本表的上位依据）

- Protocol: `docs/v10/V10_HIDDEN_FENCE_AUDIT_PROTOCOL_20251222.md`  
- Acceptance: `docs/v10/V10_ACCEPTANCE_CRITERIA.md` (Gate 0.6)  


