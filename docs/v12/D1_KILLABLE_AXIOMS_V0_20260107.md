# D1 — Killable Axioms (minimal falsifiable proposition set) v0 — 2026-01-07

Additive-only. This document is **implementation-agnostic** and **falsifiable**: each axiom defines a failure world.

This is not encouragement or narrative. It is a constraint set for future work (D1+).

---

## Axiom-0 — Measurability prerequisite (not a belief)

> There exists a class of worlds in which agent survival differences are, in principle, externally observable and comparable.

- **Falsification condition**: no world input can pass measurability gates; all subsequent axioms become `NOT_MEANINGFUL`.
- **D0 evidence status**: enforced via `W0` gate (measurability precondition).

---

## Axiom-1 — Non-goal adjudication existence

> Without explicit reward / utility objectives, there exists an adjudication mechanism that produces statistically separable long-horizon survival distributions.

- **Falsification condition**: for any adjudication mechanism, removing explicit objectives makes survival distributions converge (no separation).
- **D0 evidence status**: not universally decided. D0 explored a limited mechanism family; does not cover “all adjudication mechanisms”.

---

## Axiom-2 — Time-coupling necessity (sequence, not marginals)

> Survival differences must depend on time-series coupling between agent and world, not only on marginal statistics.

- **Falsification condition**: after `time_reversal` or `shuffle`, survival differences do **not** collapse (i.e., remain materially similar to baseline).
- **D0 evidence status**: **SUPPORTED** by negative control (Trial-8): time reversal makes ON ≈ SHUFFLE under the frozen protocol.
  - Important wording: this is **not** “axiom falsified”; it is “falsification attempt failed”, therefore the axiom is supported in the tested regime.

---

## Axiom-3 — Weak-structure amplification (∃, not ∀)

> In weak-structure worlds (low structure, low tail, low regime shift), small time differences may still be amplifiable into observable survival differences.

- **Falsification condition**: across a defined class of weak-structure worlds, for all seeds/steps/population, survival differences converge to 0.
- **D0 evidence status**: not universally decided (depends on the formal definition of “weak structure” beyond W0=PASS).

---

## Axiom-4 — Cross-world non-parasitism boundary

> If a survival difference exists only in a single market / microstructure, it is not an “evolutionary structure” but an environment-specific phenomenon.

- **Falsification condition**: in structurally similar but source-distinct worlds (e.g., ETH vs BTC SWAP under identical knobs), the effect fails to remain stable and same-order.
- **D0 evidence status**: **SUPPORTED** by Trial-9 under frozen knobs: ETH strong/stable, BTC substantially weaker/less stable.
  - Note: do not read “BTC RR mean/std larger ⇒ stronger effect”. RR enters a pathological amplification regime when `denom = max(1, |gap_on|) = 1`.

---

## Axiom-5 — Nonlinear life/death feedback necessity (candidate)

> If survival adjudication responds only linearly (or quasi-linearly) to agent-world coupling, then in unstructured worlds long-horizon differentiation is not sustainable.

- **Falsification condition**: there exists a purely linear adjudication that yields stable long-horizon differentiation in an unstructured world class.
- **D0 evidence status**: not decided. Treat as a D1 candidate hypothesis, not as a claim.

---

## Do-not-misread constraints (hard)

- Do not use these axioms to retroactively “explain” results. They are **pre-registered targets** for future falsification.
- Do not treat “SUPPORTED in D0” as “proved”. It only means: the specific falsification attempt did not kill it.
- Do not conflate RR explosion with stronger effects when `gap_on≈0` (structural denominator amplification).
- Reward must not usurp death adjudication:
  - Forbidden (direct): reward MUST NOT increase survival energy or alter death thresholds/caps/cost tables.
  - Allowed (indirect): reward MAY bias action choices, indirectly changing future cost exposure.


