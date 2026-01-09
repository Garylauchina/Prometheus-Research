#!/usr/bin/env python3
"""
Gate — Order-book E-contract provenance (fail-closed) v0

Purpose:
  Prevent "synthetic order-book" (e.g., fixed spread from last_px) from being
  mistaken as an order-book E-contract restoration.

Semantics (fail-closed):
  - PASS only if we can audit provenance as non-synthetic.
  - FAIL if we detect synthesis.
  - NOT_MEASURABLE if provenance evidence is missing/insufficient.

This gate is intentionally strict and minimal: it looks for explicit signals in
dataset_build_manifest.json and/or market_snapshot.jsonl that the order-book is synthetic.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class GateResult:
    tool: str
    generated_at_utc: str
    dataset_dir: str
    manifest_path: str
    market_snapshot_path: str
    sample_lines: int
    verdict: str  # PASS | FAIL | NOT_MEASURABLE
    errors: List[str]
    warnings: List[str]
    notes: Dict[str, Any]

    def to_json(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "generated_at_utc": self.generated_at_utc,
            "dataset_dir": self.dataset_dir,
            "manifest_path": self.manifest_path,
            "market_snapshot_path": self.market_snapshot_path,
            "sample_lines": self.sample_lines,
            "verdict": self.verdict,
            "errors": self.errors,
            "warnings": self.warnings,
            "notes": self.notes,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"manifest_missing:{str(path)}"
    except Exception as e:
        return None, f"manifest_unreadable:{str(path)}:{type(e).__name__}:{e}"


def _scan_market_snapshot_for_synthetic(
    market_snapshot_path: Path, sample_lines: int
) -> Tuple[Optional[bool], List[str], Dict[str, Any]]:
    """
    Returns:
      - synthetic_detected: True/False if determinable from sampled lines, else None
      - errors/warnings: list of strings
      - notes: counters
    """
    notes: Dict[str, Any] = {
        "sampled": 0,
        "has_orderbook_source_field": 0,
        "orderbook_source_synthetic_count": 0,
        "orderbook_source_non_synthetic_count": 0,
    }
    warnings: List[str] = []
    errors: List[str] = []

    try:
        with market_snapshot_path.open("r", encoding="utf-8") as f:
            for _ in range(sample_lines):
                line = f.readline()
                if not line:
                    break
                notes["sampled"] += 1
                try:
                    obj = json.loads(line)
                except Exception:
                    errors.append("market_snapshot_invalid_jsonl")
                    break

                # Heuristic 1: explicit marker used by some builders
                if "orderbook_source" in obj:
                    notes["has_orderbook_source_field"] += 1
                    if str(obj.get("orderbook_source")).lower() == "synthetic":
                        notes["orderbook_source_synthetic_count"] += 1
                    else:
                        notes["orderbook_source_non_synthetic_count"] += 1
    except FileNotFoundError:
        return None, ["market_snapshot_missing"], notes
    except Exception as e:
        return None, [f"market_snapshot_unreadable:{type(e).__name__}:{e}"], notes

    if notes["sampled"] == 0:
        return None, ["market_snapshot_empty"], notes

    if notes["orderbook_source_synthetic_count"] > 0:
        return True, errors + warnings, notes

    # If we saw explicit orderbook_source field and none were synthetic, treat as non-synthetic.
    if notes["has_orderbook_source_field"] > 0 and notes["orderbook_source_synthetic_count"] == 0:
        return False, errors + warnings, notes

    # Otherwise we cannot decide from market_snapshot alone.
    return None, errors + warnings, notes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset_dir", required=True)
    ap.add_argument("--sample_lines", type=int, default=50)
    ap.add_argument("--output_json", required=False, default="")
    args = ap.parse_args()

    dataset_dir = Path(args.dataset_dir)
    manifest_path = dataset_dir / "dataset_build_manifest.json"
    market_snapshot_path = dataset_dir / "market_snapshot.jsonl"

    errors: List[str] = []
    warnings: List[str] = []
    notes: Dict[str, Any] = {}

    manifest, manifest_err = _read_json(manifest_path)
    if manifest_err is not None:
        errors.append(manifest_err)
        verdict = "NOT_MEASURABLE"
        result = GateResult(
            tool="verify_orderbook_e_contract_provenance_gate_v0",
            generated_at_utc=_utc_now(),
            dataset_dir=str(dataset_dir),
            manifest_path=str(manifest_path),
            market_snapshot_path=str(market_snapshot_path),
            sample_lines=int(args.sample_lines),
            verdict=verdict,
            errors=errors,
            warnings=warnings,
            notes=notes,
        )
        out = json.dumps(result.to_json(), ensure_ascii=False, sort_keys=True)
        if args.output_json:
            Path(args.output_json).write_text(out + "\n", encoding="utf-8")
        else:
            print(out)
        return

    # Fail-fast on explicit synthesis markers in manifest
    dataset_version = str(manifest.get("dataset_version", ""))
    if "synthetic" in dataset_version.lower():
        errors.append("synthetic_detected:manifest.dataset_version_contains_synthetic")

    if "synthesis_method" in manifest:
        errors.append("synthetic_detected:manifest.has_synthesis_method")
        notes["synthesis_method"] = manifest.get("synthesis_method")

    if errors:
        verdict = "FAIL"
    else:
        verdict = "NOT_MEASURABLE"
        warnings.append("provenance_insufficient:manifest_has_no_explicit_synthesis_marker_but_no_positive_orderbook_provenance_fields_defined_in_v0_gate")

    # Secondary heuristic scan of market_snapshot
    synthetic_from_snapshot, snap_msgs, snap_notes = _scan_market_snapshot_for_synthetic(
        market_snapshot_path, int(args.sample_lines)
    )
    notes["market_snapshot_scan"] = snap_notes
    for m in snap_msgs:
        # treat scan errors as warnings unless they are hard missing/invalid
        if m.startswith("market_snapshot_missing") or m.startswith("market_snapshot_invalid_jsonl"):
            errors.append(m)
            verdict = "NOT_MEASURABLE"
        else:
            warnings.append(m)

    if synthetic_from_snapshot is True:
        errors.append("synthetic_detected:market_snapshot.orderbook_source==synthetic")
        verdict = "FAIL"
    elif synthetic_from_snapshot is False:
        # If manifest didn't mark synthetic, we still don't have a positive proof; keep NOT_MEASURABLE.
        pass

    result = GateResult(
        tool="verify_orderbook_e_contract_provenance_gate_v0",
        generated_at_utc=_utc_now(),
        dataset_dir=str(dataset_dir),
        manifest_path=str(manifest_path),
        market_snapshot_path=str(market_snapshot_path),
        sample_lines=int(args.sample_lines),
        verdict=verdict,
        errors=errors,
        warnings=warnings,
        notes=notes,
    )

    out = json.dumps(result.to_json(), ensure_ascii=False, sort_keys=True)
    if args.output_json:
        Path(args.output_json).write_text(out + "\n", encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()

