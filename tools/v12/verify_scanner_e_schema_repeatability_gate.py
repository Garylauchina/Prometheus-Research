#!/usr/bin/env python3
"""
Batch gate: Scanner E schema verification repeatability (Research repo, stdlib only).

Given a Quant artifacts root (default: runs_v12_modeling_tool) and a list of run_ids
(or a seed_sweep_summary_*.json from Quant), verify that E-schema verifier has:
  FAIL count == 0

This tool is read-only with respect to run_dir artifacts.

Exit codes:
  0: PASS (FAIL=0)
  2: FAIL (FAIL>0 or cannot load inputs)
  1: ERROR (tool crash)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).parent.parent.parent
E_VERIFIER = REPO_ROOT / "tools" / "v12" / "verify_scanner_e_schema_v0.py"


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs_root", default="", help="Quant runs root (e.g. /.../Prometheus-Quant/runs_v12_modeling_tool)")
    ap.add_argument("--summary_json", default="", help="Optional seed_sweep_summary_*.json to read run_ids from")
    ap.add_argument("--run_ids", default="", help="Optional comma-separated run_ids (overrides summary_json)")
    ap.add_argument("--output", default="", help="Optional output json path")
    args = ap.parse_args()

    runs_root = Path(args.runs_root).expanduser().resolve() if args.runs_root else None
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if args.run_ids:
        run_ids = [x.strip() for x in args.run_ids.split(",") if x.strip()]
    elif args.summary_json:
        sj = Path(args.summary_json).expanduser().resolve()
        if not sj.exists():
            print(f"ERROR: summary_json not found: {sj}", file=sys.stderr)
            return 2
        data = _read_json(sj)
        run_ids = list(data.get("run_ids", []))
    else:
        print("ERROR: must provide --run_ids or --summary_json", file=sys.stderr)
        return 2

    if not run_ids:
        print("ERROR: empty run_ids", file=sys.stderr)
        return 2

    if runs_root is None:
        print("ERROR: must provide --runs_root", file=sys.stderr)
        return 2
    if not runs_root.exists():
        print(f"ERROR: runs_root not found: {runs_root}", file=sys.stderr)
        return 2

    if not E_VERIFIER.exists():
        print(f"ERROR: E verifier not found: {E_VERIFIER}", file=sys.stderr)
        return 2

    import subprocess

    results: List[Dict[str, Any]] = []
    fail = 0

    for rid in run_ids:
        run_dir = runs_root / rid
        cmd = [sys.executable, str(E_VERIFIER), "--run_dir", str(run_dir)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        verdict = "ERROR"
        errs = []
        try:
            if p.stdout.strip():
                rep = json.loads(p.stdout.strip())
                verdict = rep.get("verdict", "ERROR")
                errs = rep.get("errors", [])[:10]
        except Exception:
            verdict = "ERROR"

        if p.returncode != 0 or verdict == "FAIL":
            fail += 1

        results.append(
            {
                "run_id": rid,
                "run_dir": str(run_dir),
                "exit_code": p.returncode,
                "verdict": verdict,
                "errors_head": errs,
            }
        )

    report = {
        "tool": "verify_scanner_e_schema_repeatability_gate",
        "generated_at_utc": _ts_utc(),
        "runs_root": str(runs_root),
        "run_count": len(run_ids),
        "fail_count": fail,
        "pass_count": len(run_ids) - fail,
        "results": results,
        "gate_passed": (fail == 0),
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())


