# V12 SSOT — Survival Difficulty via Local Reachability (M-frozen) v0 — Minimal Contract — 2026-01-09

Additive-only. This document defines a **measurement-only** contract to quantify:

> Under a frozen world contract **M**, how fast the world structurally compresses the agent’s **next-step actionability neighborhood**.

This document is a contract for execution and verification (**no narrative, no “how to survive”**).

---

## §0 Positioning / design intent (frozen)

- Target of measurement is **not** an agent trajectory, policy, or “better behavior”.
- Target is:
  - **state → local action feasibility set** (a local neighborhood of “what actions are possible now”).
- The purpose is to measure **structural compression speed** of local actionability induced by the world (under M).

If at any time we discuss:
- “which behavior is better”
- “how to live longer”
- “how to avoid death”

then we have drifted and must stop.

Hard boundary (inherits V12 Life red-line):
- Reward / profit / ROI MUST NOT enter survival energy or death adjudication.
- This SSOT does **not** introduce any reward proxy.

---

## §1 Frozen object of study (must not drift)

We study:

- **Local object**: \(F(s)\) = local feasibility set at state \(s\)
- **Not allowed**: trajectories, long-horizon rollouts, global optimization, “best path”, planning/search

### §1.1 What is a “state” \(s\) (frozen minimal definition)

The exact state representation is implementation-specific, but the SSOT requires:

- \(s\) MUST be a function of:
  - current tick alignment key (`snapshot_id` or equivalent)
  - account-local truth needed to validate a proposal (minimal I-truth, if any)
  - the frozen world contract M evidence available at that tick (not future)
- \(s\) MUST be hashable to a stable `state_id` (deterministic for identical evidence inputs).

Prohibited:
- using future evidence
- embedding post-hoc labels into the state

### §1.2 What is a “local action neighborhood” \(A(s)\) (frozen)

At each state \(s\), we define a **finite** set of candidate action proposals:

- \(A(s) = \{a_1, ..., a_N\}\) with \(N \ge 1\)
- \(A(s)\) MUST be generated without:
  - rollout
  - search over long paths
  - optimizing for any objective

Allowed:
- a fixed, pre-registered local perturbation template (e.g., “micro-variations” around the agent’s current proposal)
- a fixed, pre-registered discrete catalog of action prototypes

Forbidden:
- adaptive expansion until “good actions” are found
- using the feasibility result to guide the generation of more candidates in the same tick

### §1.3 What is “feasible / reachable” (frozen minimal)

Each candidate action \(a \in A(s)\) is assigned a feasibility label:

- `feasible(a,s) ∈ {0,1}`

Rules:

- Feasibility MUST be judged by **current** world/interface constraints under frozen M.
- Feasibility MUST NOT use:
  - future outcomes
  - any “success score”
  - any reward or PnL signal

Interpretation:
- `feasible=1` means “the action is allowed/executable under the current contract”
- It does **not** imply profitability or “goodness”

---

## §2 Frozen graph primitives (optional but must be explicit)

If we build a local graph, it is a graph over actions **within a tick**:

- Nodes: candidate actions \(a \in A(s)\)
- Edge: a “legal micro-change” relation \(a \to a'\)

Frozen constraints:
- Edges MUST be defined by a small, pre-registered local operator set (no path search).
- Only **one-step** or **short-step** (bounded) connectivity statistics are allowed.

Forbidden:
- global path planning on the action graph
- “find a route to feasibility”

---

## §3 First-order difficulty measures (frozen; descriptive only)

We do **not** do threshold-based decisions here.
We produce **descriptive statistics only**.

Required per-state measures (minimal):

- `candidate_count = |A(s)|`
- `feasible_count = |{a ∈ A(s): feasible(a,s)=1}|`
- `feasible_ratio = feasible_count / max(1, candidate_count)`

Optional (if graph is defined; still descriptive only):

- `feasible_component_count` (connected components on feasible subgraph)
- `largest_feasible_component_ratio`
- `edge_cut_rate` (fraction of edges removed by infeasibility)

Primary “compression speed” readouts (post-hoc aggregation; no threshold):

- time series of `feasible_ratio`
- first differences: `Δ feasible_ratio` and its distribution
- “fracture frequency” (times when feasible connectivity sharply breaks) — as a descriptive time series, not a decision rule

---

## §4 Death role (frozen)

Death is **ex-post label only**:

- Death/extinction is used only after the fact to test whether local reachability compression has any stable association with termination events.

Hard bans:
- Death MUST NOT be an input to feasibility computation.
- Death MUST NOT be used as feedback or optimization target.

---

## §5 Evidence contract (v0; frozen)

### §5.1 Canonical evidence file

- `local_reachability.jsonl` (strict JSONL, append-only; one record per (tick, agent))

### §5.2 Required fields (v0)

```json
{
  "ts_utc": "ISO8601",
  "snapshot_id": "string",
  "account_id_hash": "string",
  "tick_index": "int",

  "state_id": "string",
  "world_contract": {
    "M_frozen": true,
    "world_epoch_id": "string"
  },

  "neighborhood": {
    "candidate_count": "int",
    "feasible_count": "int",
    "feasible_ratio": "number"
  },

  "graph_optional": {
    "enabled": "bool",
    "feasible_component_count": "int|null",
    "largest_feasible_component_ratio": "number|null",
    "edge_cut_rate": "number|null"
  },

  "death_label_ex_post": {
    "enabled": "bool",
    "dead_at_or_before_tick": "bool|null"
  },

  "reason_codes": ["string"]
}
```

Fail-closed:
- Missing required fields ⇒ verifier FAIL.
- `candidate_count < 1` ⇒ FAIL (neighborhood undefined).

---

## §6 Falsification criteria (must be pre-registered; failure-first)

This tool is **rejected** if any of the following triggers (examples; must be frozen in pre-reg for each run bundle):

- **Epoch sensitivity failure**: the compression signature is extremely sensitive to epoch granularity while world contract is unchanged.
- **Seed reordering / instability**: across seeds, compression patterns are fully reordered with no stable structure.
- **No association with termination label**: `feasible_ratio` / compression speed shows no stable relationship with ex-post termination events (when a termination label exists).

Stop rule (hard):
- If falsification triggers ⇒ **stop the tool** (no patching/repair within the same claim).

---

## §7 Explicit boundaries (must be enforced)

This tool MUST NOT be used to:

- guide agent behavior at runtime
- compare agents as “better/worse”
- derive an optimal strategy
- replace or justify any reward/cost function

Frozen closing sentence (non-narrative):

> We do not search for ways to make the agent live; we measure how the world makes actionability collapse.

