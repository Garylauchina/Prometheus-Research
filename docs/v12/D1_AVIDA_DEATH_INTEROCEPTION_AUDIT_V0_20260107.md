# D1 — Avida “death / energy interoception” audit v0 — 2026-01-07

Additive-only. This is a **mechanism audit**. It does not adopt Avida’s reward semantics.

Goal: extract **auditably transferable primitives** for “death terminal affects decision” without letting reward hijack death adjudication (our red line).

---

## §0 Scope + constraints (frozen)

- Target repo (local): `/Users/liugang/Cursor_Store/avida`
- Focus component: `avida-core`
- What we are auditing:
  - whether internal survival state is exposed to the organism’s control flow (“interoception”)
  - how death is triggered (terminal conditions)
  - how action costs consume internal resources (energy)
- What we explicitly do **not** adopt:
  - Avida’s `merit/fitness` as reward for survival in our system (D1 red line: reward must not hijack death).

---

## §1 Evidence: Avida has energy-state interoception

### §1.1 Internal energy is a first-class phenotype state

- File: `avida-core/source/main/cPhenotype.h`
  - `energy_store` is stored energy.
  - `GetStoredEnergy()` returns current energy.
  - `GetDiscreteEnergyLevel()` classifies energy into LOW/MEDIUM/HIGH.

### §1.2 Discrete energy level is computed from configured thresholds

- File: `avida-core/source/main/cPhenotype.cc`
  - `cPhenotype::GetDiscreteEnergyLevel()` maps `energy_store` into `{LOW, MEDIUM, HIGH}` using `ENERGY_THRESH_LOW/HIGH` and `ENERGY_CAP`.

### §1.3 Organism code can branch on its own energy level (and neighbors’)

- File: `avida-core/source/cpu/cHardwareCPU.cc`
  - Instruction handlers exist such as:
    - `Inst_IfEnergyLow`, `Inst_IfEnergyHigh`, `Inst_IfEnergyMed`
    - `Inst_IfFacedEnergyLow`, `Inst_IfFacedEnergyLess`, etc.
  - These modify the instruction pointer based on `GetDiscreteEnergyLevel()` / `GetStoredEnergy()`.

**Audit conclusion**: Avida implements “interoception” as **energy-dependent control-flow branching**. This is the concrete mechanism form of “death terminal affects decision”, without requiring a reward signal.

---

## §2 Evidence: Avida has explicit death triggers (terminal conditions)

### §2.1 Lethal reactions set a death flag

- File: `avida-core/source/main/cPhenotype.cc`
  - In reaction result processing, lethal results set `to_die = true`.

### §2.2 CPU execution loop enforces death flag (hard terminal)

- File: `avida-core/source/cpu/cHardwareTransSMT.cc`
  - After executing a slice, organisms are killed if `phenotype.GetToDie()` is true (or if a max-executed limit is exceeded).

**Audit conclusion**: Avida has a clear “terminal enforcement” stage that is independent from the organism’s immediate instruction flow (the organism can influence it only through avoiding lethal events).

---

## §3 Evidence: Avida supports per-instruction energy costs (action → energy consumption)

- File: `avida-core/source/cpu/cInstSet.h` / `cInstSet.cc`
  - instruction library supports `energy_cost`.
- File: `avida-core/source/cpu/cHardwareBase.cc`
  - energy cost handling exists (energy required to execute, applied per instruction).

**Audit conclusion**: Avida models “activity consumes survival budget” via **per-action energy cost**, not only via end-of-life accounting.

---

## §4 Non-transferable semantics (must not copy into D1)

These are core to Avida’s evolutionary success but violate our current D1 red lines if copied directly:

- **`merit` / `fitness` used to grant more CPU / more reproduction opportunity** (reward hijacks survival path).
  - Example surface locations:
    - `cMerit` and scheduling priority adjustment in population code.
- Any direct mapping “success ⇒ more compute ⇒ more survival” is **not** allowed under our D1 constraint A (reward must not hijack death adjudication).

---

## §5 Transferable primitives (candidate building blocks for D1 death-terminal-in-decision)

### P1) Survival interoception variable

Minimum:
- `energy_level_discrete ∈ {low, med, high}` derived from `energy / energy_cap` using frozen thresholds.

Optional:
- `energy_ratio = clamp(energy / energy_cap, 0, 1)`

### P2) Decision-time conditioning

Decision contract MUST include:
- `decision_input.energy_level_discrete` (or equivalent)
- and/or `decision_input.energy_ratio`

### P3) Action-cost traceability (per action, not only per tick)

Model action cost as:
- `action_cost = sum(cost(action_i))` with costs determined by a frozen table (analogous to `energy_cost`).
This supports “active agents die faster” with auditable accounting.

### P4) Explicit terminal enforcement stage

Have an explicit stage where:
- terminal flags are checked (`energy<=0`, lethal event, safety gate)
- death is applied consistently and logged.

---

## §6 Do-not-misread constraints

- This audit does **not** claim Avida “proves” any philosophy.
- This audit does **not** import Avida’s reward semantics (merit/fitness).
- This audit is only used to justify that “death/energy interoception” is an existing, mature mechanism pattern that we can re-express under our red lines.


