#!/usr/bin/env python3
"""
V12 Scanner E-schema verifier (Research repo, stdlib only).

Scope:
  Verify a scanner run_dir contains a machine-verifiable, strict-JSONL
  `market_snapshot.jsonl` that conforms to:
    docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md

Hard rules (fail-closed):
  - required evidence files must exist (even if empty where allowed)
  - JSONL must be strict
  - each market_snapshot record must contain required fields + types
  - inst_id must be BTC-USDT-SWAP
  - unknown must be null (NOT "0" / empty string); must be explainable via quality.reason_codes
  - source_endpoints must be replayable against okx_api_calls.jsonl (best-effort endpoint matching)

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
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


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


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _check_required_files(run_dir: Path, required: List[str]) -> List[str]:
    missing = []
    for name in required:
        if not (run_dir / name).exists():
            missing.append(name)
    return missing


def _extract_okx_endpoints(okx_api_calls_path: Path) -> Set[str]:
    """
    Best-effort: extract endpoint identifiers from okx_api_calls.jsonl to validate replayability.
    We accept either:
      - endpoint: '/api/v5/market/ticker'
      - method: 'get_ticker' (Quant-style)
    """
    out: Set[str] = set()
    for _line_no, rec in _iter_jsonl(okx_api_calls_path):
        ep = rec.get("endpoint")
        m = rec.get("method")
        if isinstance(ep, str) and ep.strip():
            out.add(ep.strip())
        if isinstance(m, str) and m.strip():
            out.add(m.strip())
    return out


def _bad_unknown_value(v: Any) -> bool:
    # For px-like fields, unknown must not be '0' or ''.
    if v is None:
        return False
    if v == "":
        return True
    if v == 0:
        return True
    if v == "0":
        return True
    if v == "0.0":
        return True
    return False


@dataclass
class CheckResult:
    verdict: str  # PASS|NOT_MEASURABLE|FAIL
    errors: List[str]
    warnings: List[str]
    counts: Dict[str, int]
    field_coverage: Dict[str, Dict[str, Any]]


def _verify_market_snapshot(
    market_snapshot_path: Path, okx_api_calls_path: Path
) -> Tuple[List[str], List[str], Dict[str, Dict[str, Any]]]:
    errors: List[str] = []
    warnings: List[str] = []
    coverage: Dict[str, Dict[str, Any]] = {}

    required_fields = ["ts_utc", "inst_id", "snapshot_id", "source_endpoints", "quality"]

    market_fields = [
        "last_px",
        "bid_px_1",
        "ask_px_1",
        "bid_sz_1",
        "ask_sz_1",
        "mark_px",
        "index_px",
        "funding_rate",
        "next_funding_ts_ms",
    ]

    okx_endpoints = _extract_okx_endpoints(okx_api_calls_path)
    seen = 0

    # coverage counters
    present_cnt = {k: 0 for k in required_fields + market_fields}
    null_cnt = {k: 0 for k in market_fields}
    not_measurable_cnt = {k: 0 for k in market_fields}
    reason_counts: Dict[str, int] = {}

    for line_no, rec in _iter_jsonl(market_snapshot_path):
        seen += 1

        for k in required_fields:
            if k not in rec:
                errors.append(f"market_snapshot missing required field: {k} at line {line_no}")
            else:
                present_cnt[k] += 1

        # ts_utc
        if "ts_utc" in rec and rec["ts_utc"] is not None and not _is_str(rec["ts_utc"]):
            errors.append(f"market_snapshot.ts_utc must be string at line {line_no}")

        # inst_id
        inst_id = rec.get("inst_id")
        if inst_id is None or not _is_str(inst_id):
            errors.append(f"market_snapshot.inst_id must be string at line {line_no}")
        elif inst_id != "BTC-USDT-SWAP":
            errors.append(f"market_snapshot.inst_id must be BTC-USDT-SWAP, got {inst_id} at line {line_no}")

        # snapshot_id
        if "snapshot_id" in rec and rec["snapshot_id"] is not None and not _is_str(rec["snapshot_id"]):
            errors.append(f"market_snapshot.snapshot_id must be string at line {line_no}")

        # source_endpoints
        se = rec.get("source_endpoints")
        if se is None or not _is_list_of_str(se) or len(se) == 0:
            errors.append(f"market_snapshot.source_endpoints must be non-empty array[string] at line {line_no}")
        else:
            # replayability (best-effort): each endpoint must be seen in okx_api_calls by method or endpoint
            missing_eps = [x for x in se if x not in okx_endpoints]
            if missing_eps:
                errors.append(
                    f"market_snapshot.source_endpoints not replayable via okx_api_calls (missing={missing_eps}) at line {line_no}"
                )

        # quality
        q = rec.get("quality")
        if q is None or not isinstance(q, dict):
            errors.append(f"market_snapshot.quality must be object at line {line_no}")
            q = {}
        else:
            overall = q.get("overall")
            if overall is None or not _is_str(overall) or overall not in ("ok", "degraded", "not_measurable"):
                errors.append(f"market_snapshot.quality.overall must be ok|degraded|not_measurable at line {line_no}")
            rcs = q.get("reason_codes")
            if rcs is None or not _is_list_of_str(rcs):
                errors.append(f"market_snapshot.quality.reason_codes must be array[string] at line {line_no}")
            else:
                for rc in rcs:
                    reason_counts[rc] = reason_counts.get(rc, 0) + 1

        # market fields type + mask discipline
        for k in market_fields:
            if k in rec:
                present_cnt[k] += 1
            v = rec.get(k)

            if k == "next_funding_ts_ms":
                if v is None:
                    null_cnt[k] += 1
                    not_measurable_cnt[k] += 1
                elif not _is_int(v):
                    errors.append(f"market_snapshot.next_funding_ts_ms must be integer|null at line {line_no}")
                continue

            # px/rate fields: must be string|null
            if v is None:
                null_cnt[k] += 1
                not_measurable_cnt[k] += 1
                continue
            if not _is_str(v):
                errors.append(f"market_snapshot.{k} must be string|null at line {line_no}")
                continue
            # unknown must not be faked as 0/empty
            if _bad_unknown_value(v):
                errors.append(f"market_snapshot.{k} violates mask discipline (bad unknown value={v!r}) at line {line_no}")

    # coverage summary
    if seen == 0:
        errors.append("market_snapshot.jsonl is empty (no records)")
        return errors, warnings, {}

    for k in market_fields:
        coverage[k] = {
            "present_ratio": (present_cnt.get(k, 0) / seen),
            "not_measurable_ratio": (not_measurable_cnt.get(k, 0) / seen),
            "top_reason_codes": [],
        }
    coverage["required_fields_present_ratio"] = {
        "seen": seen,
        "missing_any_required": int(any(present_cnt[k] < seen for k in required_fields)),
    }
    # attach top reason codes (global)
    top_rcs = sorted(reason_counts.items(), key=lambda x: -x[1])[:10]
    for k in market_fields:
        coverage[k]["top_reason_codes"] = [rc for rc, _n in top_rcs]

    # NOT_MEASURABLE verdict suggestion: if quality.overall is not_measurable for all records.
    # We don't parse per-record overall here into ratios; it will be inferred by caller via warnings if needed.
    return errors, warnings, coverage


def verify(run_dir: Path) -> CheckResult:
    errors: List[str] = []
    warnings: List[str] = []
    counts: Dict[str, int] = {}
    coverage: Dict[str, Dict[str, Any]] = {}

    # strict JSON / JSONL
    manifest: Dict[str, Any] = {}
    try:
        manifest = _read_json(run_dir / "run_manifest.json")
    except Exception as e:
        errors.append(f"run_manifest.json invalid json: {e}")
        return CheckResult(verdict="FAIL", errors=errors, warnings=warnings, counts=counts, field_coverage=coverage)

    # Required files depend on run_kind:
    # - modeling_tool (scanner): requires scanner_report.json
    # - production (tick loop): does NOT require scanner_report.json
    run_kind = manifest.get("run_kind")
    required = [
        "run_manifest.json",
        "okx_api_calls.jsonl",
        "errors.jsonl",
        "market_snapshot.jsonl",
    ]
    if run_kind == "modeling_tool":
        required.append("scanner_report.json")

    missing = _check_required_files(run_dir, required)
    if missing:
        errors.extend([f"missing required file: {name}" for name in missing])
        return CheckResult(verdict="FAIL", errors=errors, warnings=warnings, counts=counts, field_coverage=coverage)

    for name in ["okx_api_calls.jsonl", "errors.jsonl", "market_snapshot.jsonl"]:
        try:
            counts[name] = _count_jsonl_records(run_dir / name)
        except Exception as e:
            errors.append(f"{name} strict-jsonl failed: {e}")

    if counts.get("market_snapshot.jsonl", 0) <= 0:
        errors.append("market_snapshot.jsonl must be non-empty")
        return CheckResult(verdict="FAIL", errors=errors, warnings=warnings, counts=counts, field_coverage=coverage)

    # schema rules
    e2, w2, cov = _verify_market_snapshot(run_dir / "market_snapshot.jsonl", run_dir / "okx_api_calls.jsonl")
    errors.extend(e2)
    warnings.extend(w2)
    coverage = cov

    if errors:
        return CheckResult(verdict="FAIL", errors=errors, warnings=warnings, counts=counts, field_coverage=coverage)

    # If coverage indicates pervasive not_measurable (e.g., all key px null), we can downgrade to NOT_MEASURABLE.
    # v0 conservative heuristic: if last_px is always null, mark NOT_MEASURABLE.
    last_cov = coverage.get("last_px", {})
    if isinstance(last_cov, dict) and last_cov.get("not_measurable_ratio") == 1.0:
        return CheckResult(
            verdict="NOT_MEASURABLE", errors=errors, warnings=["last_px always null"], counts=counts, field_coverage=coverage
        )

    return CheckResult(verdict="PASS", errors=errors, warnings=warnings, counts=counts, field_coverage=coverage)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="Scanner run_dir to verify")
    ap.add_argument("--output", default="", help="Optional output JSON report path")
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not run_dir.exists():
        print(f"ERROR: run_dir not found: {run_dir}", file=sys.stderr)
        return 1

    try:
        manifest = _read_json(run_dir / "run_manifest.json") if (run_dir / "run_manifest.json").exists() else {}
        result = verify(run_dir)
    except Exception as e:
        print(f"ERROR: verifier crashed: {e}", file=sys.stderr)
        return 1

    report: Dict[str, Any] = {
        "tool": "verify_scanner_e_schema_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "manifest": {
            "run_id": manifest.get("run_id"),
            "run_kind": manifest.get("run_kind"),
            "mode": manifest.get("mode"),
            "inst_id": manifest.get("inst_id") or manifest.get("world_parameters", {}).get("inst_id"),
            "schema_contract": manifest.get("schema_contract"),
        },
        "verdict": result.verdict,
        "counts": result.counts,
        "errors": result.errors,
        "warnings": result.warnings,
        "field_coverage": result.field_coverage,
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))

    if result.verdict == "FAIL":
        return 2
    if result.verdict == "NOT_MEASURABLE":
        print("WARNING: verdict=NOT_MEASURABLE (evidence is valid but key field coverage is 0)", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


