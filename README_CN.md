## Prometheus-Research

<div align="center">

*面向 execution_world 的真值驱动、可审计研究记录仓库。*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[English](README.md)** · **[Docs Index](docs/README.md)** · **[V12 Index](docs/v12/V12_RESEARCH_INDEX.md)** · **[V11 Index](docs/v11/V11_RESEARCH_INDEX.md)** · **[V10 Index](docs/v10/V10_RESEARCH_INDEX.md)**

</div>

---

## 本仓库是什么（项目目标，而非技术细节）

这是 Prometheus 项目的**研究记录仓库**。
我们的目标是保存**可复核的证据链**，而不是叙事：当我们声称某个结论时，第三方应能沿证据路径追溯到具体产物。

V11 的核心定位是：在 **execution_world（交易所真值链）** 中，构建一个**可审计、可消融对比、可复现**的演化研究工作流，让每个结论都能回指证据。

---

## 基石（方法论 SSOT）

本仓库建立在一份统一的“复杂系统测量方法论”之上：

- **V10 — A Minimal Method for Measuring Complex Systems (Evolutionary Probing)**：[`docs/v10/V10_METHOD_MEASURING_COMPLEX_SYSTEMS.md`](docs/v10/V10_METHOD_MEASURING_COMPLEX_SYSTEMS.md)
- **白皮书版（叙事入口，中英双语）**：
  - English：[`docs/whitepaper/README.md`](docs/whitepaper/README.md)
  - 中文：[`docs/whitepaper/README_CN.md`](docs/whitepaper/README_CN.md)

该文档定义的是**我们如何测量**（可测性 Gate、NOT_MEASURABLE 纪律、measurement-bias 维度等），
并被视为 V11/V12 各类研究合同的上位基石引用。

---

## V11 目标（我们要交付什么）

- **可复核的真值链**：任何关于仓位 / 资金 / 成交 / 手续费的陈述必须能回查到交易所 JSON（或明确标注 unknown / NOT_MEASURABLE）。
- **证据优先、fail-closed**：关键证据缺失或链路断裂时，运行必须降级结论（NOT_MEASURABLE）或停止（fail-closed），禁止静默默认。
- **消融可比性**：每个新机制都必须能通过受控消融在可比条件下被评估，而不是靠预写叙事。
- **避免遗留语义污染**：V11 execution_world 必须在依赖闭包上隔离 legacy/v10 的执行语义。
- **可持续研究记录**：SSOT 文档 additive-only；破坏性变更需要 major bump 并重跑最小 PROBE 验收。

---

## V11 当前关注（我们测什么）

- **证据闭合与审计一致性**：run manifests、evidence_refs、paging closure、orphan detection 等，让结论始终可复核。
- **execution_world 下固定维度探针**：严格 mask 纪律；unknown 绝不伪造成 0。
- **消融模板**：例如 `C_off vs C_on`，强调可比性与事实输出（而非解释）。

---

## V12 方向（世界建模 + 生命系统上线）

V12 的定位：

- **V10 = 证据链诞生**
- **V11 = 证据链工业化**
- **V12 = 世界建模与生命系统上线**

### V12 主要交付（research-side，按顺序）

1) **建模工具：世界特征扫描器（World Feature Scanner）**
   - 在 `execution_world` 下扫描“世界事实”（从 **E/外显市场信息** 开始）
   - 输出机器可核验的证据包与建模报告

2) **基于扫描结果构建建模文档**
   - 将扫描事实转写为 SSOT：参数空间、枚举、限制、可用性、NOT_MEASURABLE 条件

3) **重构 Agent 基因维度**
   - 基因表达维度对齐交易所接口参数空间（禁止发明接口不存在的旋钮）

4) **事件驱动（初版）**
   - 市场数据：WebSocket（推送/事件驱动）
   - 交易执行：REST（请求/响应）

5) **个体新陈代谢（取代死亡审判）**
   - 基于真值反馈调整内部状态/约束，替代二值 kill switch

6) **资金翻倍→分裂繁殖（取代繁殖审判）**
   - 繁殖作为可审计资本增长的结果，而不是主观委员会裁决

### 两条必须提前冻结的硬要求

- **WS 证据纪律**：如果行情转为 WebSocket 驱动，必须持久化订阅与消息流作为证据，否则决策无法回放/审计。
- **代理交易员双资源门禁**：同时对 (a) Agent 个体资源 与 (b) 系统交易资源（交易所限速/接口可用性/降级模式）做 fail-closed gate，并落 reason codes。
- **建模验收口径**：Scanner 必须输出机器可读的“基因对齐表”（field→dimension mapping + mask/NOT_MEASURABLE 规则），否则基因重构会漂移成主观设计。

### V12 观测目标（现有资源条件下，我们要看到什么）

在算力有限时，我们不追求“覆盖演化空间”，而追求在可审计的世界合同下观察到**可复现结构**：

- **聚类（clustering）**：不同 run/不同窗口下，Agent 行为/状态能形成稳定可复现的簇（不是一次性画图）。
- **维度坍缩（dimension collapse）**：有效自由度随时间缩小（例如 effective rank / PCA 方差集中），并且有明确对照以排除“因为缺测(mask=0)/门槛/默认值导致的假坍缩”。

方法论说明（英文原句 + 中文释义）：

In a high-dimensional genotype space, even millions of agents over millions of generations cover only a negligible fragment of the evolutionary landscape.
Prometheus does not aim to exhaust this space, but to detect whether selection introduces statistically detectable bias in observed evolutionary trajectories.

中文释义：
在高维基因型空间里，即使让数百万 Agent 演化数百万代，覆盖的也只是演化景观中极小的一块碎片。
Prometheus 不追求穷举整个空间，而是希望在可观测的演化轨迹里检测到：自然选择是否引入了统计上可检出的偏置。

---

## Start here（从这里开始）

- **V11 入口（推荐）**：[`docs/v11/V11_RESEARCH_INDEX.md`](docs/v11/V11_RESEARCH_INDEX.md)
- **V10 入口（legacy mainline）**：[`docs/v10/V10_RESEARCH_INDEX.md`](docs/v10/V10_RESEARCH_INDEX.md)
- **Docs index**：[`docs/README.md`](docs/README.md)

> 注：V11 文档已物理隔离到 `docs/v11/`。  
> 任何位于 `docs/v10/` 下的 V11 文件仅作为 stub 指针，以避免历史链接断裂。

---

## Research vs Quant（职责边界）

- **Prometheus-Research**：项目目标、验收标准、决策记录、SSOT 文档、证据入口。
- **Prometheus-Quant**：实现与运行产物（代码、日志、run_dir 证据包、auditor 输出）。

---

## License

MIT License. See `LICENSE`.

---

## Legacy / 历史内容（已归档）

根目录旧版 `README_CN.md` 已原样归档到：

- `docs/legacy/README_CN_ROOT_OLD_20260101.md`
