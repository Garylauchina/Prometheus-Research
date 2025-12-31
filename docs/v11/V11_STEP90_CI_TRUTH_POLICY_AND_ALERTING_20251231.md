# V11 Step 90 — CI Truth Policy & Alerting (Main HEAD) — SSOT — 2025-12-31

目的：把“CI 红绿信号”变成 **可机读、可审计、不会误判** 的真值来源；同时通过 Gmail/GitHub 通知策略做到“降噪但不失明”。

本文件只允许追加（additive-only）。

---

## 1) 定义（冻结）

### 1.1 Truth of CI（真值）

对 V11 而言，“CI 真值”定义为：
- **同一工作流（workflow）在 `main` 分支 HEAD 上的最新成功（success）运行**；
- 或在没有 success 的情况下，**`main` 分支 HEAD 上的最新运行**（必须读取其失败原因，不得用历史红替代）。

### 1.2 Non-truth Signals（非真值信号）

以下均不得用来判断“当前系统状态”：
- 历史 commit（非 `main` HEAD）的失败 runs
- 对旧 SHA 的 rerun（rerun 不会包含之后的修复）
- 非 `main` 分支的红（除非该分支即将合并回 main，并且被 main 的 required checks 阻断）

---

## 2) 规则（冻结）

### 2.1 只看 main HEAD（硬规则）

当我们说“CI 红/绿”，默认指：
- `main` 分支 **当前 HEAD** 的最新 run 状态。

禁止行为：
- 以旧 SHA 的 rerun 结果推断“当前 main 仍失败/仍成功”

### 2.2 Fix Ordering（修复顺序）

当 main HEAD 失败时，必须按以下顺序推进（直到 main HEAD 绿）：
- 只追第一个失败 gate（first failure），后续“Check exit code”类步骤通常是包装提示，不是根因。
- 修复后用 **新的 commit** 触发新的 run；不要反复 rerun 旧 SHA 试图“刷绿”。

---

## 3) Alerting（降噪但不失明）

### 3.1 邮件提醒目标（冻结）

邮件收件箱只保留：
- `main` 分支上关键 workflow 的失败（至少包含：`V11 Evidence Gate (Step26)`；可选包含：`Build and Push GHCR`）

其它全部归档到标签（不删除），随时可追溯。

### 3.2 Gmail 实施建议（可操作）

建议使用两个标签：
- `github-actions/keep-main-fail`
- `github-actions/noise`

并设置两个过滤器：
- Filter A（保留 main 关键失败到收件箱）：匹配 `main + failure + (V11 Evidence Gate 或 GHCR)`，打 `keep-main-fail`，不跳过收件箱。
- Filter B（其余 Actions 邮件归档）：匹配所有 Actions/workflow run 邮件，打 `noise`，跳过收件箱。

说明：
- Filter 默认不回溯旧邮件；如需对历史邮件生效，需勾选 “同时将过滤器应用于匹配的对话”。

---

## 4) 交付物（冻结）

当本 Step 90 实施完成时，必须满足：
- Research SSOT 中有明确入口（本文件）
- Research index（`docs/v11/V11_RESEARCH_INDEX.md`）包含本 Step 90 链接
- 团队对 “CI 真值=main HEAD 最新成功 run” 的共识可被机器复核（有 headSha + run URL）

---

## 5) 变更记录（追加区）

- 2025-12-31: 创建本 SSOT（定义 CI 真值口径 + Gmail 通知策略），并与 Step89 的“运行记录锚点”形成闭环。


