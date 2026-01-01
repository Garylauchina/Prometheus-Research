## Prometheus-Research

<div align="center">

*Truth-driven, auditable research for evolving agents in an execution_world.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Chinese](README_CN.md)** · **[Docs Index](docs/README.md)** · **[V11 Index](docs/v11/V11_RESEARCH_INDEX.md)** · **[V10 Index](docs/v10/V10_RESEARCH_INDEX.md)**

</div>

---

## What this repository is (project goals, not technical details)

This is the **research record** of the Prometheus project.
The goal is to preserve **reviewable evidence chains** rather than narratives:
when we claim a result, a third party should be able to trace it to concrete artifacts.

V11’s core positioning is: in an **execution_world** (exchange truth chain),
build an **auditable, ablation-friendly, reproducible** evolutionary research workflow,
where every conclusion must point back to evidence.

---

## V11 goals (what we aim to deliver)

- **A reviewable truth chain**: any statement about positions / capital / fills / fees must be traceable to exchange-retrievable JSON (or explicitly marked as unknown / NOT_MEASURABLE).
- **Evidence-first, fail-closed**: if critical evidence is missing or the chain breaks, the run must downgrade the conclusion (NOT_MEASURABLE) or stop (fail-closed)—no silent defaults.
- **Ablation comparability**: every new mechanism (e.g. C-dimension social probes) must be evaluable via controlled ablations under comparable conditions, without pre-written narratives.
- **No legacy semantic contamination**: V11 execution_world must enforce “physical inaccessibility” of legacy/v10 execution semantics in the dependency closure.
- **Sustainable research record**: SSOT documents are additive-only; breaking changes require a major bump and re-running minimal PROBE acceptance.

---

## V11 current focus (what we measure)

- **Evidence closure & audit consistency**: run manifests, evidence_refs, paging closure, orphan detection—so claims remain verifiable.
- **Minimal, fixed-dimension probes in execution_world**: strict mask discipline; unknown is never fabricated as zero.
- **Ablation templates**: e.g. `C_off vs C_on`, emphasizing comparability and fact-only outputs (not interpretations).

---

## V12 direction (world modeling + life system)

V12’s positioning is:

- **V10 = evidence chain is born**
- **V11 = evidence chain is industrialized**
- **V12 = world modeling + life system comes online**

### V12 primary deliverables (research-side, ordered)

1) **Modeling tool: World Feature Scanner**
   - Scan “world facts” (starting from **E/exogenous market information**) under `execution_world`
   - Output machine-verifiable evidence bundles and a modeling report

2) **Modeling documents from scanner results**
   - Turn scanner facts into SSOT: parameter spaces, enums, limits, availability, NOT_MEASURABLE conditions

3) **Refactor Agent genome dimensions**
   - Align expressible dimensions to exchange interface parameter spaces (no invented knobs)

4) **Event-driven execution (initial)**
   - Market data: WebSocket (push/event-driven)
   - Trade execution: REST (request/response)

5) **Individual metabolism (replace “death judgment”)**
   - Agents adapt internal states/constraints based on truth-backed feedback, instead of binary kill switches

6) **Split reproduction by capital doubling (replace “reproduction judgment”)**
   - Reproduction becomes a consequence of auditable capital growth, rather than a subjective committee decision

### Two hard additions (must be frozen early)

- **WS evidence discipline**: if market data becomes WebSocket-driven, we must persist subscription + message streams as evidence (otherwise decisions cannot be replayed/audited).
- **Dual resource gates in Proxy Trader**: enforce both (a) per-agent resource limits and (b) system trading resources (exchange rate limits / endpoint availability / degraded modes) fail-closed, with reason codes.
- **Modeling acceptance**: the scanner must output a machine-readable “genome alignment table” (field→dimension mapping + mask/NOT_MEASURABLE rules), otherwise genome refactors will drift into subjective design.

---

## Start here

- **V11 entry (recommended)**: `docs/v11/V11_RESEARCH_INDEX.md`
- **V10 entry (legacy mainline)**: `docs/v10/V10_RESEARCH_INDEX.md`
- **Docs index**: `docs/README.md`

> Note: V11 documents have been physically separated into `docs/v11/`.
> Any V11 files under `docs/v10/` are kept as stub pointers to avoid breaking historical links.

---

## Research vs Quant (responsibility boundary)

- **Prometheus-Research**: project goals, acceptance criteria, decision records, SSOT docs, and evidence entrypoints.
- **Prometheus-Quant**: implementation and run artifacts (code, logs, run_dir evidence bundles, auditor outputs).

---

## License

MIT License. See `LICENSE`.
