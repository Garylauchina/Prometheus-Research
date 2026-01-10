#!/usr/bin/env python3
"""
V13 World Contract Verifier v0.2 (fail-closed)

Properties (frozen):
- idempotent (read-only)
- self-contained (all rules come from spec JSON)
- fail-closed (first failing gate produces a verdict)
- no narrative (reasons are gate-derived only; enum-checked)

Gate order (cannot change):
  1) Required Files
  2) Evidence Parse
  3) Schema Verification
  4) Join Closure
  5) Channel Availability
  6) Reason Consistency
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Verdict:
    tool: str
    generated_at_utc: str
    spec_path: str
    contract_version: str
    run_dir: str
    evidence_path: str
    verdict: str  # PASS | NOT_MEASURABLE | FAIL
    reason_codes: List[str]
    stats: Dict[str, Any]

    def to_json(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "generated_at_utc": self.generated_at_utc,
            "spec_path": self.spec_path,
            "contract_version": self.contract_version,
            "run_dir": self.run_dir,
            "evidence_path": self.evidence_path,
            "verdict": self.verdict,
            "reason_codes": self.reason_codes,
            "stats": self.stats,
        }


def _load_spec(spec_path: Path) -> Dict[str, Any]:
    with spec_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _fail(verdict: str, reason_code: str, allowed: List[str]) -> Tuple[str, List[str]]:
    # Reason codes must always be enum-valid (fail-closed).
    if reason_code not in allowed:
        return "FAIL", ["fail:invalid_reason_code"]
    return verdict, [reason_code]


def _type_ok(value: Any, t: str) -> bool:
    if t == "str":
        return isinstance(value, str)
    if t == "list":
        return isinstance(value, list)
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="Directory containing evidence.json")
    ap.add_argument(
        "--spec_json",
        required=False,
        default="/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/spec/world_contract_v0_2_spec.json",
    )
    ap.add_argument("--output_json", required=False, default="")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    spec_path = Path(args.spec_json)
    spec = _load_spec(spec_path)

    allowed_reason_codes: List[str] = list(spec["reason_codes_enum"])
    required_files: List[str] = list(spec["required_files"])
    required_fields: List[str] = list(spec["canonical_schema"]["required_fields"])
    types: Dict[str, str] = dict(spec["canonical_schema"]["types"])
    required_join_keys: List[str] = list(spec["required_join_keys"])
    required_channels: List[str] = list(spec["required_channels"])

    evidence_path = run_dir / "evidence.json"

    stats: Dict[str, Any] = {
        "gate": None,
        "records": None,
        "unique_strategy_id_count": None,
        "missing_channels_counts": {},
    }

    # Gate 1) Required Files
    stats["gate"] = "Required Files"
    for rf in required_files:
        p = run_dir / rf
        if not p.exists():
            v, rc = _fail("FAIL", "fail:evidence_file_missing", allowed_reason_codes)
            out = Verdict(
                tool="verify_world_contract_v0_2",
                generated_at_utc=_utc_now(),
                spec_path=str(spec_path),
                contract_version=str(spec["contract_version"]),
                run_dir=str(run_dir),
                evidence_path=str(evidence_path),
                verdict=v,
                reason_codes=rc,
                stats=stats,
            )
            s = json.dumps(out.to_json(), ensure_ascii=False, sort_keys=True)
            if args.output_json:
                Path(args.output_json).write_text(s + "\n", encoding="utf-8")
            else:
                print(s)
            return

    # Gate 2) Evidence Parse
    stats["gate"] = "Evidence Parse"
    try:
        raw = evidence_path.read_text(encoding="utf-8")
        evidence = json.loads(raw)
    except Exception:
        v, rc = _fail("FAIL", "fail:evidence_parse_error", allowed_reason_codes)
        out = Verdict(
            tool="verify_world_contract_v0_2",
            generated_at_utc=_utc_now(),
            spec_path=str(spec_path),
            contract_version=str(spec["contract_version"]),
            run_dir=str(run_dir),
            evidence_path=str(evidence_path),
            verdict=v,
            reason_codes=rc,
            stats=stats,
        )
        s = json.dumps(out.to_json(), ensure_ascii=False, sort_keys=True)
        if args.output_json:
            Path(args.output_json).write_text(s + "\n", encoding="utf-8")
        else:
            print(s)
        return

    if not isinstance(evidence, list):
        v, rc = _fail("FAIL", "fail:schema_type_mismatch", allowed_reason_codes)
        out = Verdict(
            tool="verify_world_contract_v0_2",
            generated_at_utc=_utc_now(),
            spec_path=str(spec_path),
            contract_version=str(spec["contract_version"]),
            run_dir=str(run_dir),
            evidence_path=str(evidence_path),
            verdict=v,
            reason_codes=rc,
            stats=stats,
        )
        s = json.dumps(out.to_json(), ensure_ascii=False, sort_keys=True)
        if args.output_json:
            Path(args.output_json).write_text(s + "\n", encoding="utf-8")
        else:
            print(s)
        return

    stats["records"] = len(evidence)

    # Gate 3) Schema Verification
    stats["gate"] = "Schema Verification"
    for obj in evidence:
        if not isinstance(obj, dict):
            v, rc = _fail("FAIL", "fail:schema_type_mismatch", allowed_reason_codes)
            break
        missing = [k for k in required_fields if k not in obj]
        if missing:
            v, rc = _fail("FAIL", "fail:schema_field_missing", allowed_reason_codes)
            break
        bad_types = []
        for k in required_fields:
            if k in types and not _type_ok(obj.get(k), types[k]):
                bad_types.append(k)
        if bad_types:
            v, rc = _fail("FAIL", "fail:schema_type_mismatch", allowed_reason_codes)
            break
    else:
        v, rc = "PASS", []

    if v != "PASS":
        out = Verdict(
            tool="verify_world_contract_v0_2",
            generated_at_utc=_utc_now(),
            spec_path=str(spec_path),
            contract_version=str(spec["contract_version"]),
            run_dir=str(run_dir),
            evidence_path=str(evidence_path),
            verdict=v,
            reason_codes=rc,
            stats=stats,
        )
        s = json.dumps(out.to_json(), ensure_ascii=False, sort_keys=True)
        if args.output_json:
            Path(args.output_json).write_text(s + "\n", encoding="utf-8")
        else:
            print(s)
        return

    # Gate 4) Join Closure
    stats["gate"] = "Join Closure"
    join_key = required_join_keys[0] if required_join_keys else "strategy_id"
    strategy_ids: List[str] = []
    for obj in evidence:
        sid = obj.get(join_key)
        if not isinstance(sid, str) or not sid.strip():
            v, rc = _fail("FAIL", "fail:join_key_missing", allowed_reason_codes)
            out = Verdict(
                tool="verify_world_contract_v0_2",
                generated_at_utc=_utc_now(),
                spec_path=str(spec_path),
                contract_version=str(spec["contract_version"]),
                run_dir=str(run_dir),
                evidence_path=str(evidence_path),
                verdict=v,
                reason_codes=rc,
                stats=stats,
            )
            s = json.dumps(out.to_json(), ensure_ascii=False, sort_keys=True)
            if args.output_json:
                Path(args.output_json).write_text(s + "\n", encoding="utf-8")
            else:
                print(s)
            return
        strategy_ids.append(sid)
    stats["unique_strategy_id_count"] = len(set(strategy_ids))

    # Gate 5) Channel Availability
    stats["gate"] = "Channel Availability"
    missing_counts: Dict[str, int] = {c: 0 for c in required_channels}
    for obj in evidence:
        channels = obj.get("channels", [])
        if not isinstance(channels, list):
            # schema gate should have caught, but keep fail-closed
            v, rc = _fail("FAIL", "fail:schema_type_mismatch", allowed_reason_codes)
            out = Verdict(
                tool="verify_world_contract_v0_2",
                generated_at_utc=_utc_now(),
                spec_path=str(spec_path),
                contract_version=str(spec["contract_version"]),
                run_dir=str(run_dir),
                evidence_path=str(evidence_path),
                verdict=v,
                reason_codes=rc,
                stats=stats,
            )
            s = json.dumps(out.to_json(), ensure_ascii=False, sort_keys=True)
            if args.output_json:
                Path(args.output_json).write_text(s + "\n", encoding="utf-8")
            else:
                print(s)
            return

        ch_set = {str(x) for x in channels}
        for c in required_channels:
            if c not in ch_set:
                missing_counts[c] += 1

    stats["missing_channels_counts"] = missing_counts
    for c in required_channels:
        if missing_counts[c] > 0:
            # NOT_MEASURABLE is world refusal/silence channel missing.
            rc_code = f"not_measurable:channel_missing:{c}"
            v, rc = _fail("NOT_MEASURABLE", rc_code, allowed_reason_codes)
            out = Verdict(
                tool="verify_world_contract_v0_2",
                generated_at_utc=_utc_now(),
                spec_path=str(spec_path),
                contract_version=str(spec["contract_version"]),
                run_dir=str(run_dir),
                evidence_path=str(evidence_path),
                verdict=v,
                reason_codes=rc,
                stats=stats,
            )
            s = json.dumps(out.to_json(), ensure_ascii=False, sort_keys=True)
            if args.output_json:
                Path(args.output_json).write_text(s + "\n", encoding="utf-8")
            else:
                print(s)
            return

    # Gate 6) Reason Consistency
    stats["gate"] = "Reason Consistency"
    # Rule: if all gates passed but evidence carries any reason codes, FAIL.
    for obj in evidence:
        rcs = obj.get("contract_reason_codes", [])
        if not isinstance(rcs, list):
            v, rc = _fail("FAIL", "fail:schema_type_mismatch", allowed_reason_codes)
            break
        # enum-check any provided codes
        for code in rcs:
            if str(code) not in allowed_reason_codes:
                v, rc = _fail("FAIL", "fail:invalid_reason_code", allowed_reason_codes)
                break
        else:
            # enum ok, now consistency check
            if len(rcs) > 0:
                v, rc = _fail("FAIL", "fail:invalid_reason_code", allowed_reason_codes)
                break
            continue
        break
    else:
        v, rc = "PASS", []

    out = Verdict(
        tool="verify_world_contract_v0_2",
        generated_at_utc=_utc_now(),
        spec_path=str(spec_path),
        contract_version=str(spec["contract_version"]),
        run_dir=str(run_dir),
        evidence_path=str(evidence_path),
        verdict=v,
        reason_codes=rc,
        stats=stats,
    )
    s = json.dumps(out.to_json(), ensure_ascii=False, sort_keys=True)
    if args.output_json:
        Path(args.output_json).write_text(s + "\n", encoding="utf-8")
    else:
        print(s)


if __name__ == "__main__":
    main()

