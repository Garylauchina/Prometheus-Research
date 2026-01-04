#!/usr/bin/env python3
"""
V12 base-dimensions verifier (Research repo, stdlib only).

Purpose:
  Verify that a run_dir contains machine-verifiable evidence for base dimensions:
    - E: market_snapshot.jsonl
    - I: position_snapshots.jsonl
    - M: interaction_impedance.jsonl

Hard rules (fail-closed):
  - required evidence files must exist (even if empty)
  - JSONL must be strict (one valid JSON object per non-empty line; no comments)
  - minimal schema for I/M must hold for every record

Exit codes (frozen):
  - 0: PASS or NOT_MEASURABLE (prints WARNING when NOT_MEASURABLE)
  - 2: FAIL (evidence missing / strict-jsonl broken / schema violation)
  - 1: ERROR (tool crash / invalid usage)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def _count_jsonl_records(path: Path) -> int:
    n = 0
    for _line_no, _obj in _iter_jsonl(path):
        n += 1
    return n


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_str(x: Any) -> bool:
    return isinstance(x, str)


def _is_list_of_str(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _get_first_existing(run_dir: Path, names: List[str]) -> Optional[Path]:
    for n in names:
        p = run_dir / n
        if p.exists():
            return p
    return None


@dataclass
class CheckResult:
    verdict: str  # PASS|NOT_MEASURABLE|FAIL
    errors: List[str]
    warnings: List[str]
    counts: Dict[str, int]


def _check_required_files(run_dir: Path, required: List[str]) -> List[str]:
    missing = []
    for name in required:
        if not (run_dir / name).exists():
            missing.append(name)
    return missing


def _verify_position_snapshots(path: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    required_keys = ["snapshot_id", "ts_utc", "account_id_hash", "inst_id", "evidence_refs"]
    optional_num_or_str_or_null = ["lever", "pos", "avg_px", "upl"]
    optional_str_or_null = ["mgn_mode", "pos_side"]

    for line_no, rec in _iter_jsonl(path):
        for k in required_keys:
            if k not in rec:
                errors.append(f"position_snapshots missing key: {k} at line {line_no}")

        if "snapshot_id" in rec and rec["snapshot_id"] is not None and not _is_str(rec["snapshot_id"]):
            errors.append(f"position_snapshots.snapshot_id must be string at line {line_no}")
        if "ts_utc" in rec and rec["ts_utc"] is not None and not _is_str(rec["ts_utc"]):
            errors.append(f"position_snapshots.ts_utc must be string at line {line_no}")
        if "account_id_hash" in rec and rec["account_id_hash"] is not None and not _is_str(rec["account_id_hash"]):
            errors.append(f"position_snapshots.account_id_hash must be string at line {line_no}")
        if "inst_id" in rec and rec["inst_id"] is not None and not _is_str(rec["inst_id"]):
            errors.append(f"position_snapshots.inst_id must be string at line {line_no}")

        for k in optional_str_or_null:
            if k in rec and rec[k] is not None and not _is_str(rec[k]):
                errors.append(f"position_snapshots.{k} must be string|null at line {line_no}")

        for k in optional_num_or_str_or_null:
            if k in rec and rec[k] is not None and not (_is_str(rec[k]) or _is_num(rec[k])):
                errors.append(f"position_snapshots.{k} must be string|number|null at line {line_no}")

        ev = rec.get("evidence_refs")
        if ev is None:
            # evidence_refs MUST exist; allow empty object, but not null
            errors.append(f"position_snapshots.evidence_refs must be object (not null) at line {line_no}")
        elif not isinstance(ev, dict):
            errors.append(f"position_snapshots.evidence_refs must be object at line {line_no}")
        else:
            if "exchange_api_call_ids" in ev and ev["exchange_api_call_ids"] is not None and not _is_list_of_str(
                ev["exchange_api_call_ids"]
            ):
                errors.append(
                    f"position_snapshots.evidence_refs.exchange_api_call_ids must be array[string] at line {line_no}"
                )

        # Soft warning: missing optional fields is allowed, but becomes NOT_MEASURABLE in measurement sense.
        for k in ["mgn_mode", "pos_side", "lever"]:
            if k in rec and rec[k] is None:
                warnings.append(f"position_snapshots.{k} is null at line {line_no} (NOT_MEASURABLE sample)")

    return errors, warnings


def _verify_interaction_impedance(path: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    required_keys = ["ts_utc", "account_id_hash", "verdict", "reason_codes", "evidence_refs"]
    count_keys = ["attempts", "okx_reject_count", "rate_limited_count", "http_error_count"]

    for line_no, rec in _iter_jsonl(path):
        for k in required_keys:
            if k not in rec:
                errors.append(f"interaction_impedance missing key: {k} at line {line_no}")

        if "ts_utc" in rec and rec["ts_utc"] is not None and not _is_str(rec["ts_utc"]):
            errors.append(f"interaction_impedance.ts_utc must be string at line {line_no}")
        if "account_id_hash" in rec and rec["account_id_hash"] is not None and not _is_str(rec["account_id_hash"]):
            errors.append(f"interaction_impedance.account_id_hash must be string at line {line_no}")

        if "window_ms" in rec and rec["window_ms"] is not None and not _is_num(rec["window_ms"]):
            errors.append(f"interaction_impedance.window_ms must be number|null at line {line_no}")

        for k in count_keys:
            if k in rec and rec[k] is not None and not _is_num(rec[k]):
                errors.append(f"interaction_impedance.{k} must be number at line {line_no}")

        if "avg_latency_ms" in rec and rec["avg_latency_ms"] is not None and not _is_num(rec["avg_latency_ms"]):
            errors.append(f"interaction_impedance.avg_latency_ms must be number|null at line {line_no}")

        v = rec.get("verdict")
        if v is not None:
            if not _is_str(v):
                errors.append(f"interaction_impedance.verdict must be string at line {line_no}")
            elif v not in ("PASS", "NOT_MEASURABLE", "FAIL"):
                errors.append(f"interaction_impedance.verdict invalid value: {v} at line {line_no}")

        rc = rec.get("reason_codes")
        if rc is None:
            errors.append(f"interaction_impedance.reason_codes must be array[string] (not null) at line {line_no}")
        elif not _is_list_of_str(rc):
            errors.append(f"interaction_impedance.reason_codes must be array[string] at line {line_no}")
        elif any(x.startswith("not_measurable:") for x in rc):
            warnings.append(f"interaction_impedance has not_measurable reason_codes at line {line_no}")

        ev = rec.get("evidence_refs")
        if ev is None:
            errors.append(f"interaction_impedance.evidence_refs must be object (not null) at line {line_no}")
        elif not isinstance(ev, dict):
            errors.append(f"interaction_impedance.evidence_refs must be object at line {line_no}")
        else:
            if "exchange_api_call_ids" in ev and ev["exchange_api_call_ids"] is not None and not _is_list_of_str(
                ev["exchange_api_call_ids"]
            ):
                errors.append(
                    f"interaction_impedance.evidence_refs.exchange_api_call_ids must be array[string] at line {line_no}"
                )

    return errors, warnings


def verify(run_dir: Path) -> CheckResult:
    errors: List[str] = []
    warnings: List[str] = []
    counts: Dict[str, int] = {}

    # Required files: fail-closed, even if empty
    required = [
        "run_manifest.json",
        "market_snapshot.jsonl",
        "position_snapshots.jsonl",
        "interaction_impedance.jsonl",
        "errors.jsonl",
    ]
    missing = _check_required_files(run_dir, required)
    if missing:
        errors.extend([f"missing required file: {name}" for name in missing])
        return CheckResult(verdict="FAIL", errors=errors, warnings=warnings, counts=counts)

    # Optional but recommended API call evidence (backward compatibility names)
    api_calls = _get_first_existing(run_dir, ["okx_api_calls.jsonl", "exchange_api_calls.jsonl"])
    if api_calls is None:
        warnings.append("missing api calls evidence file: okx_api_calls.jsonl/exchange_api_calls.jsonl")
    else:
        try:
            counts["api_calls"] = _count_jsonl_records(api_calls)
        except Exception as e:
            errors.append(f"api_calls strict-jsonl failed: {e}")

    # Strict JSONL for E/I/M
    for name in ["market_snapshot.jsonl", "position_snapshots.jsonl", "interaction_impedance.jsonl", "errors.jsonl"]:
        p = run_dir / name
        try:
            counts[name] = _count_jsonl_records(p)
        except Exception as e:
            errors.append(f"{name} strict-jsonl failed: {e}")

    # Schema checks for I/M (E is covered by its own SSOT/verifiers; here we only strict-jsonl + presence)
    try:
        e1, w1 = _verify_position_snapshots(run_dir / "position_snapshots.jsonl")
        errors.extend(e1)
        warnings.extend(w1)
    except Exception as e:
        errors.append(f"position_snapshots schema check crashed: {e}")

    try:
        e2, w2 = _verify_interaction_impedance(run_dir / "interaction_impedance.jsonl")
        errors.extend(e2)
        warnings.extend(w2)
    except Exception as e:
        errors.append(f"interaction_impedance schema check crashed: {e}")

    if errors:
        return CheckResult(verdict="FAIL", errors=errors, warnings=warnings, counts=counts)

    # If there are any NOT_MEASURABLE samples, we surface NOT_MEASURABLE (but still exit 0).
    # This is intentionally conservative: the evidence is valid, but the measurement is degraded.
    not_measurable = any("NOT_MEASURABLE" in w for w in warnings)
    if not_measurable:
        return CheckResult(verdict="NOT_MEASURABLE", errors=errors, warnings=warnings, counts=counts)

    return CheckResult(verdict="PASS", errors=errors, warnings=warnings, counts=counts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="run_dir to verify (scanner / modeling_tool / etc.)")
    ap.add_argument("--output", default="", help="Optional output JSON report path")
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not run_dir.exists():
        print(f"ERROR: run_dir not found: {run_dir}", file=sys.stderr)
        return 1

    try:
        manifest_path = run_dir / "run_manifest.json"
        manifest = _read_json(manifest_path) if manifest_path.exists() else {}
        result = verify(run_dir)
    except Exception as e:
        print(f"ERROR: verifier crashed: {e}", file=sys.stderr)
        return 1

    report: Dict[str, Any] = {
        "tool": "verify_base_dimensions_eim_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "manifest": {
            "run_id": manifest.get("run_id"),
            "run_kind": manifest.get("run_kind"),
            "mode": manifest.get("mode"),
            "truth_profile": manifest.get("truth_profile"),
        },
        "verdict": result.verdict,
        "counts": result.counts,
        "errors": result.errors,
        "warnings": result.warnings,
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Machine output to stdout
    print(json.dumps(report, ensure_ascii=False))

    if result.verdict == "FAIL":
        return 2
    if result.verdict == "NOT_MEASURABLE":
        print("WARNING: verdict=NOT_MEASURABLE (evidence is valid but degraded samples exist)", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


