#!/usr/bin/env python3
"""
V12.4 helper (Research repo): scan a Quant V12 broker run_dir for "dangling knobs"
by comparing observed fields against the frozen alignment table template.

This tool is read-only: it never modifies the run_dir unless --output is provided.
It is intended to be run on the same machine that has the Quant run_dir.

Usage:
  python3 tools/v12/scan_alignment_drift_v0.py \
    --run_dir /path/to/quant/runs_v12/run_broker_uplink_v0_* \
    --template docs/v12/V12_GENOME_ALIGNMENT_TABLE_V0_TEMPLATE_20260103.json \
    --output /path/to/report.json

Exit codes:
  0: scan completed (even if issues found)
  2: --strict and issues found
  1: invalid usage / IO error
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
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at {path} line {line_no}: {e}") from e


def _get_nested(obj: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    cur: Any = obj
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def _collect_exchange_order_param_keys(exchange_api_calls_path: Path) -> Set[str]:
    """
    Collect keys under request params for order placement calls.
    Robust to schema drift; best-effort extraction.
    """
    keys: Set[str] = set()
    for rec in _iter_jsonl(exchange_api_calls_path):
        endpoint = str(rec.get("endpoint", ""))
        method = str(rec.get("method", ""))
        if "/api/v5/trade/order" not in endpoint and "trade/order" not in endpoint and "order" not in method:
            continue

        params = rec.get("params")
        if isinstance(params, dict):
            keys.update(params.keys())
            continue

        params2 = _get_nested(rec, ["request", "params"])
        if isinstance(params2, dict):
            keys.update(params2.keys())
            continue

        params3 = _get_nested(rec, ["request_data"])
        if isinstance(params3, dict):
            keys.update(params3.keys())
            continue

    return keys


def _collect_order_attempt_fields(order_attempts_path: Path) -> Set[str]:
    keys: Set[str] = set()
    for rec in _iter_jsonl(order_attempts_path):
        if isinstance(rec, dict):
            keys.update(rec.keys())
    return keys


def _load_template(template_path: Path) -> Tuple[Set[str], Dict[str, Any]]:
    tpl = _read_json(template_path)
    order_space = tpl.get("order_api_parameter_space", [])
    if not isinstance(order_space, list) or not all(isinstance(x, str) for x in order_space):
        raise ValueError("template.order_api_parameter_space must be an array[string]")
    return set(order_space), tpl


@dataclass(frozen=True)
class Mapping:
    source_field: str
    mapped_field: str
    note: str


def _default_field_mappings() -> List[Mapping]:
    # V12 evidence snake_case ↔ OKX order param camelCase
    return [
        Mapping("inst_id", "instId", "snake_case_to_camel"),
        Mapping("td_mode", "tdMode", "snake_case_to_camel"),
        Mapping("pos_side", "posSide", "snake_case_to_camel"),
        Mapping("order_type", "ordType", "snake_case_to_camel"),
        Mapping("requested_sz", "sz", "semantic_mapping"),
        Mapping("limit_px", "px", "semantic_mapping"),
        Mapping("client_order_id", "clOrdId", "semantic_mapping"),
        Mapping("reduce_only", "reduceOnly", "snake_case_to_camel"),
        Mapping("exp_time", "expTime", "snake_case_to_camel"),
    ]


def _filter_observed_keys(raw: Set[str]) -> Set[str]:
    # Drop obvious non-parameter/metadata keys to reduce noise.
    drop_prefixes = (
        "_",
    )
    drop_exact = {
        "ts_utc",
        "run_id",
        "run_dir",
        "mode",
        "submitted",
        "exchange_order_id",
        "account_id_hash",
        "agent_id_hash",
        "decision_ref",
        "gate_name",
        "gate_decision",
        "gate_reason_code",
        "intent_source",
        "lifecycle_scope",
        "error",
        "error_type",
        "notes",
    }
    out: Set[str] = set()
    for k in raw:
        if k in drop_exact:
            continue
        if any(k.startswith(p) for p in drop_prefixes):
            continue
        out.add(k)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="Quant run_dir to scan (broker run)")
    ap.add_argument("--template", required=True, help="Alignment table template JSON path")
    ap.add_argument("--output", default="", help="Optional output report json path")
    ap.add_argument("--strict", action="store_true", help="Exit 2 if issues found")
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    template_path = Path(args.template).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not run_dir.exists():
        print(f"ERROR: run_dir not found: {run_dir}", file=sys.stderr)
        return 1
    if not template_path.exists():
        print(f"ERROR: template not found: {template_path}", file=sys.stderr)
        return 1

    template_fields, tpl = _load_template(template_path)

    exchange_api_calls = run_dir / "exchange_api_calls.jsonl"
    if not exchange_api_calls.exists():
        # Backward compatibility: Quant may call it okx_api_calls.jsonl
        exchange_api_calls = run_dir / "okx_api_calls.jsonl"

    order_attempts = run_dir / "order_attempts.jsonl"

    observed_exchange_keys = _collect_exchange_order_param_keys(exchange_api_calls)
    observed_attempt_keys = _collect_order_attempt_fields(order_attempts)

    observed_attempt_keys_filtered = _filter_observed_keys(observed_attempt_keys)

    mappings = _default_field_mappings()
    mapping_dict = {m.source_field: m.mapped_field for m in mappings}

    mapped_from_attempts = {mapping_dict[k] for k in observed_attempt_keys_filtered if k in mapping_dict}
    unmapped_attempts = sorted(k for k in observed_attempt_keys_filtered if k not in mapping_dict and k not in template_fields)

    missing_template = sorted(k for k in template_fields if k not in observed_exchange_keys and k not in mapped_from_attempts)

    # Known "not in order params but important" knobs we expect to show up elsewhere.
    important_non_order_knobs = []
    for k in ("leverage_target", "leverage_source", "leverage_reason_code"):
        if k in observed_attempt_keys:
            important_non_order_knobs.append(k)

    issues: List[str] = []
    if unmapped_attempts:
        issues.append(f"unmapped_attempt_fields={len(unmapped_attempts)}")
    # missing_template is not always an error (optional/conditional), but worth surfacing.

    report: Dict[str, Any] = {
        "tool": "scan_alignment_drift_v0",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "template_path": str(template_path),
        "template": {
            "exchange": tpl.get("exchange"),
            "inst_id": tpl.get("inst_id"),
            "table_version": tpl.get("table_version"),
            "order_api_parameter_space_count": len(template_fields),
        },
        "observed": {
            "exchange_order_param_keys": sorted(observed_exchange_keys),
            "order_attempt_keys_filtered": sorted(observed_attempt_keys_filtered),
            "order_attempt_keys_raw_count": len(observed_attempt_keys),
        },
        "mapping": {
            "attempt_to_order_param_mappings": [m.__dict__ for m in mappings],
            "mapped_order_params_from_attempts": sorted(mapped_from_attempts),
        },
        "diff": {
            "unmapped_attempt_fields": unmapped_attempts,
            "missing_template_order_params": missing_template,
            "important_non_order_knobs_observed": important_non_order_knobs,
        },
        "issues": issues,
        "issue_count": len(issues),
        "notes": [
            "missing_template_order_params may include optional/conditional fields not used in this run.",
            "important_non_order_knobs are not order params; they should be covered by separate parameter spaces (future v0+).",
        ],
    }

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.strict and report["issue_count"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


