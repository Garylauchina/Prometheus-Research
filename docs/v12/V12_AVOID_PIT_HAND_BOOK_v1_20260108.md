# V12 避坑手册（v1.0 — 2026-01-08）

Additive-only. 本文档只追加不修改：未来任何新坑以 **§N+1** 追加在末尾，禁止回改旧条目。

目标：把我们已经踩过的坑（V0.x）以及前人经典失败模式，压缩成**可审计、可拷问、可执行的上线门禁**。

---

## §0 原则（冻结）

- 只记录**真实踩过的坑**：
  - **我们的坑**：必须能在本 repo 里指向明确证据（SSOT / summary / artifacts）。
  - **前人坑**：必须是“经典、反复出现”的失败模式，并提供最小可复述出处（书/论文/平台名即可），且必须转化为可拷问项。
- 每条坑必须包含（缺一不可）：
  - 描述
  - 原因
  - 数据/证据（可复核引用）
  - 缓解/拷问方式（上线门禁）
  - 关联原理（对应我们 D1 的可证伪命题/红线）
- 任何新机制/参数上线前，必须先对照本文档完成 **§1.1 六拷问流程**，通过后方可进入实验（否则 NOT_READY）。

---

## §1 上线前门禁：六拷问流程（v1.0）

以下 6 条拷问必须在 pre-reg 或 SSOT 的“frozen knobs”里给出可机器检查的答案（能落到证据字段/统计阈值/ablation 对照）。

1) **Ablation 拷问（必杀）**  
   - 去掉新机制/参数（OFF 或回退到基线）后，关键现象是否**立即消失**？  
   - 如果消失不了：说明现象不是由该机制产生 → **拒绝上线**。

2) **负控拷问（时间/结构破坏）**  
   - 是否存在明确的 `shuffle` / `time_reversal` / block-permute 等负控？  
   - 负控下指标是否按预期塌缩？若不塌缩：说明“结构”可能是伪的 → **拒绝上线**。  
   - 参见 D0 的负控与“禁止误读”条款：`docs/v12/D0_SUMMARY_APPEND_ONLY_V1_20260107.md`。

3) **W0 可测性拷问（不许在无结构世界制造结构）**  
   - 任何声称“world→cost/pressure→survival”的实验必须先通过 W0 gate。  
   - 若 W0=NOT_MEASURABLE，则该实验必须停止并自标 NOT_MEASURABLE（fail-closed）。  
   - 参见：`docs/v12/V12_SSOT_UGLY_BASELINE_DEATH_ONLY_V0_20260106.md`（W0 gate 语义）与 `docs/v12/V12_SSOT_D0_FALSIFICATION_DEATH_VERDICT_V0_20260107.md`（D0 先决条件）。

4) **敏感性拷问（参数扰动）**  
   - 对关键阈值/指数/放大系数做 ±10% 扰动：关键结论是否稳定（例如变化 <5% 或不改变 PASS/FAIL）？  
   - 若高度敏感：大概率是“人为阈值注入 artifact” → **拒绝上线**。

5) **跨世界拷问（反圈养/反单一吸引子）**  
   - 至少做一次跨世界（跨市场/跨时间窗）的 pseudo-independence check；如果只在单一世界成立，必须在结论里明确“环境特定”。  
   - 参见 D0 Trial-9 的结论边界与 RR 病理区说明：`docs/v12/D0_SUMMARY_APPEND_ONLY_V1_20260107.md`。

6) **审计拷问（证据链完整）**  
   - 是否严格 JSON/JSONL？是否能 join/recompute？缺任何必需证据文件是否 fail-closed？  
   - 若不能独立复算：一律 **拒绝上线**（不是“先跑起来再说”）。

---

## §2 已知坑清单（v1.0）

### §2.1 坑1：线性死亡裁决导致“定时灭绝”（我们已踩）

- **描述**：存活/灭绝轨迹高度聚集，长尾分化缺失（例如 extinction_tick 的 std 明显小于 mean）。
- **原因**：能量扣减路径近似线性（固定 attempt_cost/impedance_cost 族），且死亡阈值刚性（`energy_after<=0`）。
- **数据/证据（可复核）**：
  - `docs/v12/V12_SSOT_UGLY_BASELINE_DEATH_ONLY_V0_20260106.md`：
    - v0.1 decision-cost：extinction_tick `mean=67, std=0.0, range=[67,67]`
    - v0.3 reject-stress：extinction_tick `mean=13.95, std=1.42, range=[12,18]`
    - v0.4 tail_reject_stress：extinction_tick `mean=183, std=15.04, range=134`
    - v0.5 dirty_tail：extinction_tick `mean=168, std=11.99, range=67` 且 `alive@5000 = 0%`
- **缓解/拷问方式（上线门禁）**：
  - 允许引入非线性（例如 hazard / prob-of-death 的非线性或路径依赖），但必须通过：
    - **Ablation 拷问**：关掉非线性后是否退化回线性聚集？否则拒绝。
    - **敏感性拷问**：非线性指数/阈值 ±10% 扰动后是否仍稳定？否则拒绝。
  - 任何缓解不得违反“death is NOT reward”红线（reward 不得直接进入 survival energy）。
- **关联原理**：
  - D1 候选：`Axiom-5 (nonlinear life/death feedback necessity)`（参见 `docs/v12/D1_KILLABLE_AXIOMS_V0_20260107.md`）。

---

### §2.2 坑2：coupling 机制失效（世界特征对死亡/投影无关）（我们已踩）

- **描述**：world→pressure 的映射过弱，导致效应不可测（NOT_MEASURABLE），或测到的差异与时间结构无关。
- **原因**：proxy 设计太弱（尺度不匹配、只看 1-tick、缺少 run-length/聚类），或“结构”其实由阈值/放大器注入。
- **数据/证据（可复核）**：
  - “读 world ≠ world 影响 survival”的负例基线：`docs/v12/V12_SSOT_UGLY_BASELINE_DEATH_ONLY_V0_20260106.md`（v0.1 decision-cost 的注释段）。
  - “时间结构的必要条件/负控”与“不可伪造条款”：`docs/v12/D0_SUMMARY_APPEND_ONLY_V1_20260107.md`（Trial-6/7/8/9 事实与 §3 Do-not-misread）。
- **缓解/拷问方式（上线门禁）**：
  - 必须先过 **W0 可测性拷问**，否则禁止做大规模 sweep。
  - 必须提供 **负控拷问**（shuffle/time reversal）并预注册 PASS/FAIL 判据。
  - 如引入放大/归一化：必须通过 **敏感性拷问** + **Ablation 拷问**，避免“人为制造结构”。
- **关联原理**：
  - D0/D1 共识：时间序列耦合是必要条件（参见 `docs/v12/D1_KILLABLE_AXIOMS_V0_20260107.md` 的 Axiom-2）。

---

### §2.3 坑3：投影摆设（决策对存活无真实影响）（我们已踩）

- **描述**：决策/投影的变化并不改变成本暴露或死亡轨迹；表现为某些行为统计（如 reject_rate）极其稳定、对“投影变化”不敏感。
- **原因**：投影只影响“记录/标签”，没有进入 survival ledger 的可审计路径（action_cost / impedance_cost）或进入路径但强度不足。
- **数据/证据（可复核）**：
  - v0.1 decision-cost 的关键注释：`docs/v12/V12_SSOT_UGLY_BASELINE_DEATH_ONLY_V0_20260106.md`（说明读取 world 输入不代表影响 survival）。
  - v0.4/v0.5 的 reject_rate 统计（稳定到极小 std）同样在上述 SSOT 中有事实记录。
- **缓解/拷问方式（上线门禁）**：
  - 新机制必须显式回答：投影如何改变 `interaction_intensity`，以及它如何改变 `action_cost/impedance_cost`（可审计、可 ablate）。
  - 通过 **Ablation 拷问**：去掉“投影→成本暴露”的链路，差异必须消失。
- **关联原理**：
  - D1 SSOT 的闭环先决条件：`F2 interoception expressed in behavior` 与 `F3 interaction coupled to cost exposure`（参见 `docs/v12/D1_SSOT_ACTIVE_INTEROCEPTION_AND_BIDIRECTIONAL_COUPLING_V0_20260107.md`）。

---

### §2.4 坑4：人为阈值制造伪结构（经典前人坑 + 我们高风险）

- **描述**：看起来有结构（分布分化/聚集），但换阈值/微小扰动/换种子就消失；结构来自公式病理区间或阈值注入，而非系统机制。
- **原因**：阈值/指数/概率函数在某些区间会产生“结构性放大”（例如分母病理、clip gate），并被误读为系统性。
- **数据/证据（可复核）**：
  - RR 病理区间与“禁止误读”已在 D0 summary 明确冻结：`docs/v12/D0_SUMMARY_APPEND_ONLY_V1_20260107.md`（§3 Do-not-misread, Trial-9 的 denom=1 说明）。
  - signal_window 的二值门控（W<k 完全 clip）也在同一文档中以硬事实记录（Trial-6/7）。
- **缓解/拷问方式（上线门禁）**：
  - 必须做 **敏感性拷问**（±10% 扰动）与 **强制消融**（ON vs OFF）。
  - 对任何存在“门控/clip/饱和”的环节，必须显式记录 `clip_ratio`/触发比例，并预注册“门控导致的 FAIL 语义”。
- **关联原理**：
  - “反叙事偏置”：我们只允许以负控/消融来声明结构，不允许事后解释。

---

### §2.5 坑5：观察者效应/规模陷阱（经典 ABM 坑；D1 必须正视）

- **描述**：
  - 代理数过少：欠采样，结果被噪声支配。
  - 代理数过多：测量本身改变世界，出现集体 artifact（伪流动性/伪稳定）。
- **原因**：测量过程参与了系统动力学（interaction changes world）；规模改变等价于改变实验条件。
- **数据/证据（可复核）**：
  - v0.x 的“高度聚集灭绝”说明：单一规模下很容易被误读为机制失败或机制成功（参见 `docs/v12/V12_SSOT_UGLY_BASELINE_DEATH_ONLY_V0_20260106.md` 的多版本统计）。
- **缓解/拷问方式（上线门禁）**：
  - 必须做 **跨规模拷问**：agent_count 做 1×/10×/100×（或至少 2 档），观察关键结论是否保持同号/同阶。
  - 若规模变化导致结论反转：必须在结论里显式标注“规模依赖”，不得对外宣称“机制普适”。
- **关联原理**：
  - D1 的“跨世界/跨条件稳定性”是反圈养的核心（与 §1 的跨世界拷问同源）。

---

### §2.6 坑6：复现崩坏（跨种子/跨窗口/跨数据集不稳）（经典前人坑；我们已见到边界）

- **描述**：换 seed/时间窗/数据集，结构消失或反转。
- **原因**：尺度依赖 artifact + 种子敏感 + “单世界吸引子”误读。
- **数据/证据（可复核）**：
  - D0 Trial-9：ETH 强而稳定，BTC 明显更弱且 RR 存在病理区间风险（参见 `docs/v12/D0_SUMMARY_APPEND_ONLY_V1_20260107.md` 的 Trial-9 硬事实与 RR 误读条款）。
- **缓解/拷问方式（上线门禁）**：
  - 必须做 **跨种子** 与 **跨世界**（至少 2 个 world-input）复核；并预注册“变化上限/稳定性阈值”。
  - 明确区分：
    - 机制可复算（必须）
    - 结果完全一致（不作为成功标准；若跨世界塌缩成单一吸引子 → domestication risk）
- **关联原理**：
  - D1 的“measurement tool, not goal pursuit / domestication risk”硬约束（参见 `docs/v12/D1_SSOT_ACTIVE_INTEROCEPTION_AND_BIDIRECTIONAL_COUPLING_V0_20260107.md` §0）。

---

## §3 新坑条目模板（追加用）

复制以下模板，作为新条目追加到文末（禁止回改旧条目）：

```
### §X 坑名（来源：我们/前人）

- 描述：
- 原因：
- 数据/证据（必须可复核引用到 repo 内 SSOT/summary/artifact；或前人最小出处）：
- 缓解/拷问方式（必须能落地到 §1 六拷问流程的至少两条）：
- 关联原理（链接到 D1 axiom / SSOT / red-line）：
```

