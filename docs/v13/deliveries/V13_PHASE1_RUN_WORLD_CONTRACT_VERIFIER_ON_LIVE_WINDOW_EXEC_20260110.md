# Delivery — Quant Instructions — V13 Phase 1: run World Contract v0.2 verifier on live window — 2026-01-10

Repo (Research): `/Users/liugang/Cursor_Store/Prometheus-Research`

This instruction file (absolute path):
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/deliveries/V13_PHASE1_RUN_WORLD_CONTRACT_VERIFIER_ON_LIVE_WINDOW_EXEC_20260110.md`

Goal (Phase 1, minimal):
- Produce one **Contract Layer** verdict for the current live capture window, without adding any adjudication logic.
- Return only facts + file pointers.

Hard bans:
- Do NOT compute `L` / gates / adjudication.
- Do NOT fabricate any world evidence.

---

## A) Identify current window_dir on VPS

From your report, VPS and window root are:
- VPS: `45.76.97.37`
- window_dir: `/data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h`

If the active window changed, use the actual current window_dir (facts only).

---

## B) Confirm the 3 required window files exist (V13 minimal contract)

On VPS, run:

```bash
ssh root@45.76.97.37 "ls -la /data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h | sed -n '1,120p'"
ssh root@45.76.97.37 "cat /data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h/window.meta.yaml | sed -n '1,120p'"
ssh root@45.76.97.37 "cat /data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h/phenomena.log.md | sed -n '1,120p'"
ssh root@45.76.97.37 "cat /data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h/verdict.md"
```

---

## C) Ensure `evidence.json` exists in window_dir

If recorder already generates it on shutdown, it may not exist yet. In that case, run the standalone generator (Quant side) to create it **without stopping the recorder**.

On VPS (Quant repo assumed at `~/Prometheus-Quant`):

```bash
ssh root@45.76.97.37 "cd ~/Prometheus-Quant && git rev-parse HEAD"

# Generate evidence.json into the window_dir (idempotent overwrite OK)
ssh root@45.76.97.37 \"cd ~/Prometheus-Quant && python3 tools/v13/generate_evidence_v0_2.py \\
  --window_dir /data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h \\
  --output_json /data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h/evidence.json\"

ssh root@45.76.97.37 \"python3 -c 'import json; p=\"/data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h/evidence.json\"; print(\"OK\", p, \"records=\", len(json.load(open(p))))'\"
```

---

## D) Run Research verifier against the window_dir (read-only)

On the same machine where `/Users/liugang/Cursor_Store/Prometheus-Research` exists (local), run:

```bash
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v13/verify_world_contract_v0_2.py \
  --run_dir "<LOCAL_MOUNTED_RUN_DIR_OR_COPY_DIR>" \
  --output_json /tmp/v13_world_contract_v0_2_verdict_live_window.json
```

If `evidence.json` exists only on VPS, you can copy it locally first:

```bash
scp root@45.76.97.37:/data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h/evidence.json /tmp/v13_live_window_evidence.json
mkdir -p /tmp/v13_live_window_dir
cp /tmp/v13_live_window_evidence.json /tmp/v13_live_window_dir/evidence.json
python3 /Users/liugang/Cursor_Store/Prometheus-Research/tools/v13/verify_world_contract_v0_2.py \
  --run_dir /tmp/v13_live_window_dir \
  --output_json /tmp/v13_world_contract_v0_2_verdict_live_window.json
```

---

## E) Return to Research (facts only)

Send back:
- Quant commit hash (from VPS)
- window_dir absolute path (VPS)
- absolute paths (VPS) to:
  - `window.meta.yaml`
  - `phenomena.log.md`
  - `verdict.md`
  - `evidence.json`
- `/tmp/v13_world_contract_v0_2_verdict_live_window.json` (content or file)

