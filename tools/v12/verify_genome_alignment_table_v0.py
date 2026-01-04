#!/usr/bin/env python3
"""
V12.2 verifier: Genome Alignment Table v0 (Research repo, stdlib only).

This verifies a machine-readable alignment table is:
  - structurally valid
  - uses the frozen control_class vocabulary
  - does not invent fields outside declared parameter spaces
  - contains evidence_sources / not_measurable_rules arrays

Input is a JSON file (genome_alignment_table.json or the template).

Exit codes (frozen):
  - 0: PASS
  - 2: FAIL (schema/contract violation)
  - 1: ERROR (tool crash / IO)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


ALLOWED_CONTROL_CLASS = {"system_fact", "agent_expressible", "agent_proposable", "system_controlled"}


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("root JSON must be an object")
    return obj


def _is_str(x: Any) -> bool:
    return isinstance(x, str)


def _is_bool(x: Any) -> bool:
    return isinstance(x, bool)


def _is_list_of_str(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _require_keys(d: Dict[str, Any], keys: List[str], errors: List[str], ctx: str) -> None:
    for k in keys:
        if k not in d:
            errors.append(f"{ctx} missing key: {k}")


def _dedupe(seq: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for x in seq:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out


def verify_table(path: Path) -> Tuple[bool, List[str], Dict[str, Any]]:
    errors: List[str] = []
    table = _read_json(path)

    # top-level required
    _require_keys(table, ["exchange", "inst_id", "table_version", "alignment"], errors, "root")

    if "exchange" in table and not _is_str(table["exchange"]):
        errors.append("root.exchange must be string")
    if "inst_id" in table and not _is_str(table["inst_id"]):
        errors.append("root.inst_id must be string")
    if "table_version" in table and not _is_str(table["table_version"]):
        errors.append("root.table_version must be string")

    alignment = table.get("alignment")
    if not isinstance(alignment, list):
        errors.append("root.alignment must be array[object]")
        alignment = []

    order_space = table.get("order_api_parameter_space", [])
    if order_space is not None and not (isinstance(order_space, list) and all(isinstance(x, str) for x in order_space)):
        errors.append("root.order_api_parameter_space must be array[string] if present")
        order_space = []
    order_space_set = set(order_space or [])

    # optional non-order spaces (template may include these)
    # We accept both shapes:
    #   - write_api_space/truth_read_space (arrays)
    #   - or a nested section (additive)

    field_names: List[str] = []

    for i, rec in enumerate(alignment):
        ctx = f"alignment[{i}]"
        if not isinstance(rec, dict):
            errors.append(f"{ctx} must be object")
            continue

        _require_keys(
            rec,
            [
                "field_name",
                "field_type",
                "required_rule",
                "control_class",
                "agent_expressible",
                "system_default_or_derived",
                "gate_controlled",
                "not_measurable_rules",
                "evidence_sources",
            ],
            errors,
            ctx,
        )

        fn = rec.get("field_name")
        if fn is not None:
            if not _is_str(fn) or not fn.strip():
                errors.append(f"{ctx}.field_name must be non-empty string")
            else:
                field_names.append(fn)

        ft = rec.get("field_type")
        if ft is not None and (not _is_str(ft) or not ft.strip()):
            errors.append(f"{ctx}.field_type must be non-empty string")

        rr = rec.get("required_rule")
        if rr is not None and (not _is_str(rr) or not rr.strip()):
            errors.append(f"{ctx}.required_rule must be non-empty string")

        cc = rec.get("control_class")
        if cc is not None:
            if not _is_str(cc):
                errors.append(f"{ctx}.control_class must be string")
            elif cc not in ALLOWED_CONTROL_CLASS:
                errors.append(f"{ctx}.control_class invalid: {cc} (allowed={sorted(ALLOWED_CONTROL_CLASS)})")

        for bk in ["agent_expressible", "system_default_or_derived", "gate_controlled"]:
            if bk in rec and not _is_bool(rec[bk]):
                errors.append(f"{ctx}.{bk} must be bool")

        nmr = rec.get("not_measurable_rules")
        if nmr is not None and not _is_list_of_str(nmr):
            errors.append(f"{ctx}.not_measurable_rules must be array[string]")

        es = rec.get("evidence_sources")
        if es is not None and not _is_list_of_str(es):
            errors.append(f"{ctx}.evidence_sources must be array[string]")
        elif isinstance(es, list) and len(es) == 0:
            errors.append(f"{ctx}.evidence_sources must be non-empty (no unanchored knobs)")

        # enum_values is optional but if present must be array[string]
        ev = rec.get("enum_values")
        if ev is not None and not _is_list_of_str(ev):
            errors.append(f"{ctx}.enum_values must be array[string] if present")

    # basic uniqueness
    dups = [x for x in set(field_names) if field_names.count(x) > 1]
    if dups:
        errors.append(f"duplicate field_name(s) in alignment: {sorted(dups)}")

    # "no invented knobs" (soft in v0): if order_api_parameter_space exists, every element must appear in alignment
    if order_space_set:
        aligned = set(field_names)
        missing = sorted(list(order_space_set - aligned))
        if missing:
            errors.append(f"order_api_parameter_space not fully covered by alignment: missing={missing}")

    report = {
        "tool": "verify_genome_alignment_table_v0",
        "generated_at_utc": _ts_utc(),
        "input_path": str(path),
        "exchange": table.get("exchange"),
        "inst_id": table.get("inst_id"),
        "table_version": table.get("table_version"),
        "alignment_count": len(alignment),
        "unique_field_name_count": len(set(field_names)),
        "errors": errors,
        "error_count": len(errors),
    }

    ok = len(errors) == 0
    return ok, errors, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Alignment table JSON path")
    ap.add_argument("--output", default="", help="Optional report output path")
    args = ap.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not in_path.exists():
        print(f"ERROR: input not found: {in_path}", file=sys.stderr)
        return 1

    try:
        ok, _errors, report = verify_table(in_path)
    except Exception as e:
        print(f"ERROR: verifier crashed: {e}", file=sys.stderr)
        return 1

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())


