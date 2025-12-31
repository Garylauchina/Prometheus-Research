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

## 4) Incident Handling（冻结）

触发条件（任一满足即为 incident）：
- `main` HEAD 的关键 gate 失败（证据链/对账/refs/sha256 相关）
- 运行记录锚点缺失导致 run 不可定位或不可复跑
- 证据文件缺失/不可解引用/sha256 对不上
- 发现疑似“观测污染”（例如僵尸进程、非本 run 的交易活动）

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


