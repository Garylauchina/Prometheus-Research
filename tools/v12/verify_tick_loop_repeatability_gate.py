#!/usr/bin/env python3
"""
V12.3 repeatability gate: tick loop + E schema (Research repo, stdlib only).

Given a Quant runs_root and a list of tick-loop run_ids (or a file containing them),
this tool verifies:
  - each run_dir passes E schema verifier (exit 0)
  - each run_dir passes tick loop verifier (exit 0)
  - FAIL count == 0

NOT_MEASURABLE is allowed as long as verifiers exit 0 (evidence valid but degraded).

Exit codes:
  0: PASS (FAIL=0)
  2: FAIL (FAIL>0 or invalid inputs)
  1: ERROR (tool crash)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).parent.parent.parent
E_VERIFIER = REPO_ROOT / "tools" / "v12" / "verify_scanner_e_schema_v0.py"
TICK_VERIFIER = REPO_ROOT / "tools" / "v12" / "verify_tick_loop_v0.py"


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_run_ids(args: argparse.Namespace) -> List[str]:
    if args.run_ids:
        return [x.strip() for x in args.run_ids.split(",") if x.strip()]
    if args.run_ids_file:
        p = Path(args.run_ids_file).expanduser().resolve()
        lines = [x.strip() for x in p.read_text(encoding="utf-8").splitlines()]
        return [x for x in lines if x and not x.startswith("#")]
    raise ValueError("must provide --run_ids or --run_ids_file")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs_root", required=True, help="Quant runs root (absolute path)")
    ap.add_argument("--run_ids", default="", help="Comma-separated tick loop run_ids")
    ap.add_argument("--run_ids_file", default="", help="File containing run_ids, one per line")
    ap.add_argument("--min_ticks", type=int, default=120, help="Minimum tick count required")
    ap.add_argument("--max_backward_ms", type=int, default=0, help="Allowed backward drift (ms)")
    ap.add_argument("--output", default="", help="Optional output json path")
    args = ap.parse_args()

    runs_root = Path(args.runs_root).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not runs_root.exists():
        print(f"ERROR: runs_root not found: {runs_root}", file=sys.stderr)
        return 2
    if not E_VERIFIER.exists():
        print(f"ERROR: E verifier not found: {E_VERIFIER}", file=sys.stderr)
        return 2
    if not TICK_VERIFIER.exists():
        print(f"ERROR: tick verifier not found: {TICK_VERIFIER}", file=sys.stderr)
        return 2

    try:
        run_ids = _load_run_ids(args)
    except Exception as e:
        print(f"ERROR: invalid run_ids input: {e}", file=sys.stderr)
        return 2

    if not run_ids:
        print("ERROR: empty run_ids", file=sys.stderr)
        return 2

    import subprocess

    results: List[Dict[str, Any]] = []
    fail = 0

    for rid in run_ids:
        run_dir = runs_root / rid
        r: Dict[str, Any] = {"run_id": rid, "run_dir": str(run_dir)}

        # E schema
        e_cmd = [sys.executable, str(E_VERIFIER), "--run_dir", str(run_dir)]
        e_p = subprocess.run(e_cmd, capture_output=True, text=True)
        r["e_exit"] = e_p.returncode
        r["e_verdict"] = "ERROR"
        try:
            if e_p.stdout.strip():
                e_rep = json.loads(e_p.stdout.strip())
                r["e_verdict"] = e_rep.get("verdict", "ERROR")
                r["e_errors_head"] = e_rep.get("errors", [])[:5]
        except Exception:
            r["e_errors_head"] = ["e_verifier_output_unparseable"]

        # Tick loop
        t_cmd = [
            sys.executable,
            str(TICK_VERIFIER),
            "--run_dir",
            str(run_dir),
            "--min_ticks",
            str(args.min_ticks),
            "--max_backward_ms",
            str(args.max_backward_ms),
        ]
        t_p = subprocess.run(t_cmd, capture_output=True, text=True)
        r["tick_exit"] = t_p.returncode
        r["tick_verdict"] = "ERROR"
        try:
            if t_p.stdout.strip():
                t_rep = json.loads(t_p.stdout.strip())
                r["tick_verdict"] = t_rep.get("verdict", "ERROR")
                r["tick_errors_head"] = t_rep.get("errors", [])[:5]
                r["tick_warnings_head"] = t_rep.get("warnings", [])[:5]
                r["tick_stats"] = t_rep.get("stats", {})
        except Exception:
            r["tick_errors_head"] = ["tick_verifier_output_unparseable"]

        ok = (e_p.returncode == 0) and (t_p.returncode == 0)
        r["ok"] = ok
        if not ok:
            fail += 1
        results.append(r)

    report = {
        "tool": "verify_tick_loop_repeatability_gate",
        "generated_at_utc": _ts_utc(),
        "runs_root": str(runs_root),
        "run_count": len(run_ids),
        "fail_count": fail,
        "pass_count": len(run_ids) - fail,
        "gate_passed": (fail == 0),
        "min_ticks": args.min_ticks,
        "max_backward_ms": args.max_backward_ms,
        "results": results,
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())


