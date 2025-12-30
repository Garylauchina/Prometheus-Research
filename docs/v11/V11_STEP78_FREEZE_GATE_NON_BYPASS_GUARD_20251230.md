# V11 Step 78 — Freeze Gate Non-Bypass Structural Guard (Quant) — SSOT — 2025-12-30

目的：将“冻结后 connector 写入口物理不可达”的安全性从 demo/E2E 扩展为 **生产写路径的结构性保证**：任何生产代码路径不得绕过 freeze pre-check 直接触达 connector 写方法。

本文件只允许追加（additive-only）。

前置：
- Step74/75：freeze 机制与 CI gate
- Step76/77：E2E 断言“冻结后 connector 不可达”

---

## 1) 威胁模型（冻结）

隐患：未来某次重构/新增模块可能出现“旁路”：
- 直接调用 connector 的 place/cancel/replace
- 新增一个未接入 freeze gate 的写入口

目标：在 CI 中 **结构性检测** 并阻断合并，而不是靠人工 review。

---

## 2) 结构性门禁（冻结）

Quant 必须提供一个静态门禁工具（建议 Python AST 扫描）：
- `tools/freeze_gate_guard.py`

扫描范围（冻结）：
- `prometheus/v11/` 下所有生产代码（不含 tests/fixtures）

违规定义（冻结，最小集合）：
- 任何文件中出现对 connector 写方法的直接调用（示例关键词）：
  - `.place_order(` / `.cancel_order(` / `.replace_order(`
  - 或等价的写 API 名称（以 Quant 实际 connector 接口为准）
- 除了允许清单（allowlist）之外，任何位置调用上述方法均为 violation。

允许清单（冻结，最小集合）：
- 仅允许在 **BrokerTrader 的唯一写入口实现文件**中出现 connector 写调用（例如 `prometheus/v11/core/broker_trader.py` 或等价路径）。
- allowlist 必须以“文件路径 + 允许的方法名集合”的形式冻结在 guard 工具中（或外部 json 配置，但必须版本化并可审计）。

输出（冻结）：
- 打印 violations：file + line + snippet
- exit code：
  - 0 = PASS（0 violations）
  - 1 = FAIL（violations > 0）
  - 2 = ERROR（扫描失败/异常）

---

## 3) CI 集成（冻结）

将该 guard 纳入 `.github/workflows/v11_evidence_gate.yml`（建议在 verify_step54_integration job 末尾或单独 job）：

```text
python3 tools/freeze_gate_guard.py
```

失败语义（冻结）：
- exit != 0 → CI FAIL（阻断合并）
- 不允许条件跳过

---

## 4) 最小验收（硬）

必须证明：
- PASS：正常分支下 0 violations
- FAIL：在一个测试 PR/临时分支中，故意新增一处旁路调用，guard 能检测并失败（可通过单元测试或自检脚本证明）

---

## 5) Research 侧交付物

- 本 SSOT 文档
- Quant 落地后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + CI 输出片段 + allowlist 内容）


