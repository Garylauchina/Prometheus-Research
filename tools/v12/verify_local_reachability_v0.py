#!/usr/bin/env python3
"""
V12 Local Reachability verifier v0 (Research repo, stdlib only).

Purpose (fail-closed):
  - Verify `<RUN_DIR>/local_reachability.jsonl` exists and follows strict JSONL + SSOT schema.
  - Verify minimal internal consistency:
      * candidate_count >= 1
      * 0 <= feasible_count <= candidate_count
      * feasible_ratio == feasible_count / candidate_count (within tolerance)
      * M_frozen == true

Exit codes (frozen):
  - 0: PASS or NOT_MEASURABLE (prints WARNING when NOT_MEASURABLE)
  - 2: FAIL (evidence missing / strict-jsonl broken / schema violation)
  - 1: ERROR (tool crash / invalid usage)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _iter_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            s = raw.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at {path} line {line_no}: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL record must be an object at {path} line {line_no}")
            yield line_no, obj


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _is_str(x: Any) -> bool:
    return isinstance(x, str)


def _is_list_of_str(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


@dataclass
class CheckResult:
    verdict: str  # PASS|NOT_MEASURABLE|FAIL
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]


def _get(d: Dict[str, Any], key: str) -> Any:
    return d.get(key)


def _approx_equal(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def _verify_local_reachability_schema(path: Path) -> CheckResult:
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {"records": 0}

    # For basic sanity stats
    min_fr = None
    max_fr = None

    for line_no, rec in _iter_jsonl(path):
        stats["records"] += 1

        # required top-level fields
        for k in ("ts_utc", "snapshot_id", "account_id_hash", "tick_index", "state_id", "world_contract", "neighborhood", "graph_optional", "death_label_ex_post", "reason_codes"):
            if k not in rec:
                errors.append(f"missing_required_field:{k} (line={line_no})")

        ts = _get(rec, "ts_utc")
        sid = _get(rec, "snapshot_id")
        aid = _get(rec, "account_id_hash")
        ti = _get(rec, "tick_index")
        stid = _get(rec, "state_id")
        wc = _get(rec, "world_contract")
        nb = _get(rec, "neighborhood")
        go = _get(rec, "graph_optional")
        dl = _get(rec, "death_label_ex_post")
        rc = _get(rec, "reason_codes")

        if ts is not None and not _is_str(ts):
            errors.append(f"invalid_type:ts_utc (line={line_no})")
        if not (_is_str(sid) and sid):
            errors.append(f"invalid_value:snapshot_id (line={line_no})")
        if not (_is_str(aid) and aid):
            errors.append(f"invalid_value:account_id_hash (line={line_no})")
        if not _is_int(ti):
            errors.append(f"invalid_type:tick_index (line={line_no})")
        if not (_is_str(stid) and stid):
            errors.append(f"invalid_value:state_id (line={line_no})")

        # world_contract
        if not isinstance(wc, dict):
            errors.append(f"invalid_type:world_contract (line={line_no})")
        else:
            mf = wc.get("M_frozen")
            if mf is not True:
                errors.append(f"world_contract_not_frozen (line={line_no})")
            we = wc.get("world_epoch_id")
            if we is not None and not _is_str(we):
                errors.append(f"invalid_type:world_epoch_id (line={line_no})")

        # neighborhood
        if not isinstance(nb, dict):
            errors.append(f"invalid_type:neighborhood (line={line_no})")
        else:
            cc = nb.get("candidate_count")
            fc = nb.get("feasible_count")
            fr = nb.get("feasible_ratio")
            if not (_is_int(cc) and cc >= 1):
                errors.append(f"invalid_value:neighborhood.candidate_count (line={line_no})")
            if not (_is_int(fc) and fc >= 0):
                errors.append(f"invalid_value:neighborhood.feasible_count (line={line_no})")
            if _is_int(cc) and _is_int(fc) and (fc > cc):
                errors.append(f"inconsistent:feasible_count_gt_candidate_count (line={line_no})")
            if not _is_num(fr):
                errors.append(f"invalid_type:neighborhood.feasible_ratio (line={line_no})")
            else:
                frf = float(fr)
                if frf < 0.0 - 1e-12 or frf > 1.0 + 1e-12:
                    errors.append(f"invalid_range:neighborhood.feasible_ratio (line={line_no})")
                if _is_int(cc) and _is_int(fc) and cc >= 1:
                    expected = fc / max(1, cc)
                    if not _approx_equal(frf, expected, tol=1e-9):
                        # allow tiny float drift but not semantic mismatch
                        errors.append(f"inconsistent:feasible_ratio_mismatch (line={line_no})")
                min_fr = frf if min_fr is None else min(min_fr, frf)
                max_fr = frf if max_fr is None else max(max_fr, frf)

        # graph_optional
        if not isinstance(go, dict):
            errors.append(f"invalid_type:graph_optional (line={line_no})")
        else:
            enabled = go.get("enabled")
            if not isinstance(enabled, bool):
                errors.append(f"invalid_type:graph_optional.enabled (line={line_no})")
            if enabled is False:
                for k in ("feasible_component_count", "largest_feasible_component_ratio", "edge_cut_rate"):
                    if go.get(k) is not None:
                        errors.append(f"graph_optional_disabled_but_non_null:{k} (line={line_no})")

        # death_label_ex_post
        if not isinstance(dl, dict):
            errors.append(f"invalid_type:death_label_ex_post (line={line_no})")
        else:
            enabled = dl.get("enabled")
            if not isinstance(enabled, bool):
                errors.append(f"invalid_type:death_label_ex_post.enabled (line={line_no})")
            if enabled is False:
                if dl.get("dead_at_or_before_tick") is not None:
                    errors.append(f"death_label_disabled_but_non_null (line={line_no})")

        # reason_codes
        if rc is not None and not _is_list_of_str(rc):
            errors.append(f"invalid_type:reason_codes (line={line_no})")

        # soft sanity: state_id format
        if _is_str(sid) and _is_str(aid) and _is_int(ti) and _is_str(stid):
            expected_prefix = f"{sid}:{aid}:{ti}"
            if stid != expected_prefix:
                warnings.append(f"state_id_unexpected_format (line={line_no})")

        if len(errors) > 2000:
            errors.append("too_many_errors_abort")
            break

    stats["feasible_ratio_min"] = min_fr
    stats["feasible_ratio_max"] = max_fr

    verdict = "PASS" if not errors else "FAIL"
    return CheckResult(verdict=verdict, errors=errors, warnings=warnings, stats=stats)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        print(f"FAIL: run_dir not found: {run_dir}", file=sys.stderr)
        return 2

    p = run_dir / "local_reachability.jsonl"
    if not p.exists():
        print(f"FAIL: missing required file: {p}", file=sys.stderr)
        return 2

    try:
        res = _verify_local_reachability_schema(p)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    report = {
        "tool": "verify_local_reachability_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "local_reachability_jsonl": str(p),
        "verdict": res.verdict,
        "stats": res.stats,
        "warnings": res.warnings[:200],
        "errors": res.errors[:200],
        "errors_truncated": len(res.errors) > 200,
        "warnings_truncated": len(res.warnings) > 200,
    }
    print(json.dumps(report, ensure_ascii=False))

    if res.verdict == "PASS":
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

