# V11 Step 47 — Gene/Feature/Ledger SSOT Implemented in Quant — 2025-12-30

目的：记录 Step 47（execution_world 下退役 `has_position`，以持仓真值三元组替代）的 **Quant 落地实现锚点**（含 SHA）与最小实现事实。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_20251230.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit（短）：`1bc43a2`
- Quant commit（完整）：`1bc43a26d8c609d56fbe2bb493e450b6ad172751`
- message：`v11: Step47 retire has_position in execution_world (exposure_ratio+pos_side_sign+truth_quality)`

---

## 2) 落地摘要（用户验收事实）

变更文件：
- `prometheus/v11/ops/ledger/ledger_module.py`

Contract/Schema：
- Ledger contract version：`V11_LEDGER_MODULE_20251230`
- Ledger schema version：`2025-12-30.1`

新增（Position Truth Triad）：
- `position_exposure_ratio: Optional[float]`
- `pos_side_sign: Optional[int]`（-1/0/+1）
- `positions_truth_quality: ok/unreliable/unknown`（既有字段，作为 triad 的质量门）

新增（derived，可读性字段，NOT for core decision vector）：
- `has_position_derived: Optional[bool]`（由 `position_exposure_ratio > ε` 派生；quality!=ok → None）
- `capital_health_ratio: Optional[float]`（equity 缺失 → None）

强制规则（实现侧）：
- `positions_truth_quality != "ok"` → `position_exposure_ratio` 与 `pos_side_sign` 必须为 `None`（禁止伪造 flat/0）
- `positions_truth_quality == "ok"` → `position_exposure_ratio` 与 `pos_side_sign` 必须非空且合法

向后兼容：
- 保留 `positions: Optional[Dict[str, Any]]` 标记为 legacy（兼容旧路径）
- `record_tick_snapshot()` 新增参数均为可选默认 None，使 stub/unknown 调用点无需修改


