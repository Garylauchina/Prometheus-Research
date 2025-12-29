## Prometheus-Research

<div align="center">

*Truth-driven, auditable research for evolving agents in an execution_world.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[中文说明](README_CN.md)** · **[Docs Index](docs/README.md)** · **[V11 Index](docs/v11/V11_RESEARCH_INDEX.md)** · **[V10 Index](docs/v10/V10_RESEARCH_INDEX.md)**

</div>

---

## 本仓库是什么（项目目标，而非技术说明）

这是 Prometheus 项目的 **研究仓库（Research Record）**。我们在这里沉淀“可以被第三方复核”的研究结论，而不是堆叠想法或口头解释。

V11 的核心定位是：在 **execution_world**（真实交易所真值链）里，建立一套**可审计、可消融、可复现**的演化实验体系，让系统的每个“结论”都能指回证据链。

---

## V11 的目标（我们要交付什么）

- **可复核的真值链**：任何关于仓位/资金/成交/费用的结论，都必须能回指到“交易所可回查 JSON”（或明确标注 unknown / NOT_MEASURABLE）。
- **证据优先、失败即停**：当关键证据缺失或链路断裂时，结论必须降级（NOT_MEASURABLE）或直接终止（fail-closed），而不是用默认值继续跑。
- **消融可比性**：每个新机制（例如 C 维度 social probe）必须能通过对照/消融在相同条件下产出可观测差异；差异的好坏不提前叙事。
- **防旧语义污染**：V11 的 execution_world 需要“物理不可达”的闭包边界，避免任何 legacy/v10 执行语义被误接回主链路。
- **研究记录可持续**：所有关键口径以文档 SSOT 冻结，保持 additive-only；破坏性变更必须升 major 并重跑最小 PROBE。

---

## V11 当前关注点（what we measure）

- **证据闭环与审计一致性**：run_manifest / evidence_refs / paging closure / orphan detection 等，确保“可查、可证、可对齐”。
- **execution_world 下的最小可用探针体系**：固定维度输入 + mask 纪律，unknown 不伪造为 0。
- **消融实验模板**：例如 `C_off vs C_on`，强调可比性与事实统计产物（而不是解释）。

---

## 入口（你应该从哪里开始）

- **V11 统一入口（推荐）**：`docs/v11/V11_RESEARCH_INDEX.md`
- **V10 研究主线入口（历史主线）**：`docs/v10/V10_RESEARCH_INDEX.md`
- **Docs 总入口**：`docs/README.md`

> 备注：V11 文档已从 `docs/v10/` 物理分区到 `docs/v11/`；`docs/v10/` 中保留的 V11 文件为 stub 指针，用于兼容旧链接。

---

## Research vs Quant（职责边界）

- **Prometheus-Research**：保存“项目目标、验收口径、裁决记录、SSOT 文档、证据链入口”。
- **Prometheus-Quant**：实现与运行产物（代码、日志、run_dir 证据包、审计工具输出）。

---

## License

MIT License. See `LICENSE`.
