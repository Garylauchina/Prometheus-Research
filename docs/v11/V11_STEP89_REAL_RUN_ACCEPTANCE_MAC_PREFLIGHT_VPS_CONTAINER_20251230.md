# V11 Step 89 — Real Run Acceptance (Mac Preflight → VPS Container) — SSOT — 2025-12-30

目的：把 Step81–88 的“证据链机制 + P0–P5 订单确认闭环”落到一次 **真实运行** 的可复验验收上。先在 Mac 做 preflight（排除低级问题），再在 VPS 容器做最终验收（更接近 execution_world 真实网络/限流/时钟环境）。

本文件只允许追加（additive-only）。

前置：
- Step 88：P0–P5 order confirmation verifier + PASS/FAIL fixtures + CI gate
- Step 81–87：evidence refs/backfill/sha256/range/paging closure/auditor refs 体系

---

## 1) 运行分两阶段（冻结）

### Phase A: Mac Preflight（必须 PASS）

目标：验证代码可跑、门禁可跑、证据包可生成，避免把低级错误带到 VPS。

要求：
- 不需要真实下单（可跑 demo/fixture 或 dry-run），但必须：
  - runner preflight gates 全部通过
  - Step88 verifier 能在本地产物上运行并给出可解释结论（PASS 或 NOT_MEASURABLE）

产物：
- 本地 run_dir（可不上传），但必须保存日志片段作为 Step89 记录材料。

### Phase B: VPS Container Acceptance（最终验收）

目标：在更接近真实 execution_world 的环境中完成一次最小闭环验收。

要求（硬）：
- tick_count ≥ 10
- 至少 1 笔订单样本满足：
  - P0 intent recorded
  - P2 terminal status 可证（filled/canceled/rejected 均可）
- Step88 verifier 对该 run_dir：
  - PASS；或若真值受限则 NOT_MEASURABLE，但必须：
    - 给出 reason_codes
    - evidence_refs 可解引用且与审计报告一致
- `auditor_report.json` 的 verdict 与 verifier 结论一致（不得靠口头解释）

产物（必须归档为 evidence package）：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `evidence_ref_index.json`
- `research_bundle/entry.json`（若已启用）
- 与 Step88/87/86… 相关的关键 json/jsonl 文件（按 runner 的 evidence gate 输出）

---

## 2) Step89 最小验收清单（冻结）

必须满足：
- 订单确认闭环：P0–P5（按 Step88）
- paging closure proof：fills/bills/orders_history（按 Step88/87）
- evidence_refs/backfill view/sha256/range：按 Step81–87 的 bundle 规则
- fail-closed：任何必需证据缺失 → run-end gate / CI / verifier 必须失败（或 truthful NOT_MEASURABLE）

---

## 3) Step89 交付物（Quant）

Quant 必须新增一份不可变记录：
- `docs/v11/V11_STEP89_REAL_RUN_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`

记录内容最小集合：
- code commit SHA
- run_id / run_dir 路径（或其 archive 标识）
- tick_count
- P2 terminal 订单样本的 ordId/clOrdId（若敏感可脱敏，但必须可在证据中机器 join）
- Step88 verifier 命令与 exit code（含输出片段）
- auditor verdict（含 evidence_refs）
- evidence package 核心文件清单与 sha256_16 摘要


