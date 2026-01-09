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

This gate is intentionally strict and minimal:
- It is a provenance gate, not a coverage gate.
- It can be used for different expected E-contract sources (order-book vs trade-derived).
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
    expected_source: str  # orderbook | trade_derived
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
            "expected_source": self.expected_source,
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


def _scan_market_snapshot_orderbook_source(
    market_snapshot_path: Path, sample_lines: int
) -> Tuple[Optional[Dict[str, int]], List[str], Dict[str, Any]]:
    """
    Returns:
      - orderbook_source_counts: dict if determinable from sampled lines, else None
      - errors/warnings: list of strings
      - notes: counters
    """
    notes: Dict[str, Any] = {
        "sampled": 0,
        "has_orderbook_source_field": 0,
    }
    warnings: List[str] = []
    errors: List[str] = []
    source_counts: Dict[str, int] = {}

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
                    src = str(obj.get("orderbook_source")).strip().lower()
                    if not src:
                        src = "empty"
                    source_counts[src] = source_counts.get(src, 0) + 1
    except FileNotFoundError:
        return None, ["market_snapshot_missing"], notes
    except Exception as e:
        return None, [f"market_snapshot_unreadable:{type(e).__name__}:{e}"], notes

    if notes["sampled"] == 0:
        return None, ["market_snapshot_empty"], notes

    if notes["has_orderbook_source_field"] > 0:
        return source_counts, errors + warnings, notes

    return None, errors + warnings, notes


def _manifest_declared_kind(manifest: Dict[str, Any]) -> str:
    """
    Conservative classification from manifest.
    Returns: synthetic | trade_derived | orderbook | unknown
    """
    dataset_version = str(manifest.get("dataset_version", ""))
    if "synthetic" in dataset_version.lower():
        return "synthetic"
    if "trade" in dataset_version.lower() and "derived" in dataset_version.lower():
        return "trade_derived"
    if "synthesis_method" in manifest:
        return "synthetic"
    if "trade_provenance" in manifest:
        return "trade_derived"
    if "orderbook_provenance" in manifest:
        return "orderbook"
    return "unknown"


def _has_positive_provenance(manifest: Dict[str, Any], expected_source: str) -> bool:
    if expected_source == "orderbook":
        return isinstance(manifest.get("orderbook_provenance"), dict)
    if expected_source == "trade_derived":
        return isinstance(manifest.get("trade_provenance"), dict)
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset_dir", required=True)
    ap.add_argument(
        "--expected_source",
        required=False,
        default="orderbook",
        choices=["orderbook", "trade_derived"],
        help="Expected E-contract source kind. 'orderbook' is Trial-11; 'trade_derived' must be a separate pre-registered contract.",
    )
    ap.add_argument("--sample_lines", type=int, default=50)
    ap.add_argument("--output_json", required=False, default="")
    args = ap.parse_args()

    dataset_dir = Path(args.dataset_dir)
    manifest_path = dataset_dir / "dataset_build_manifest.json"
    market_snapshot_path = dataset_dir / "market_snapshot.jsonl"

    errors: List[str] = []
    warnings: List[str] = []
    notes: Dict[str, Any] = {}
    expected_source = str(args.expected_source)

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
            expected_source=expected_source,
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

    declared_kind = _manifest_declared_kind(manifest)
    notes["manifest_declared_kind"] = declared_kind

    # Hard FAIL on synthesis
    if declared_kind == "synthetic":
        if "synthesis_method" in manifest:
            notes["synthesis_method"] = manifest.get("synthesis_method")
            errors.append("synthetic_detected:manifest.has_synthesis_method")
        errors.append("synthetic_detected:manifest.declared_kind==synthetic")

    # Secondary heuristic scan of market_snapshot
    src_counts, snap_msgs, snap_notes = _scan_market_snapshot_orderbook_source(
        market_snapshot_path, int(args.sample_lines)
    )
    notes["market_snapshot_scan"] = snap_notes
    if src_counts is not None:
        notes["market_snapshot_orderbook_source_counts"] = src_counts
        if src_counts.get("synthetic", 0) > 0:
            errors.append("synthetic_detected:market_snapshot.orderbook_source==synthetic")
        if src_counts.get("trade_derived", 0) > 0:
            notes["trade_derived_seen_in_market_snapshot"] = True

    for m in snap_msgs:
        if m.startswith("market_snapshot_missing") or m.startswith("market_snapshot_invalid_jsonl"):
            errors.append(m)
        else:
            warnings.append(m)

    # If any errors so far, verdict is FAIL unless evidence itself missing => NOT_MEASURABLE
    if any(e.startswith("market_snapshot_missing") for e in errors) or any(
        e.startswith("market_snapshot_invalid_jsonl") for e in errors
    ):
        verdict = "NOT_MEASURABLE"
    elif errors:
        verdict = "FAIL"
    else:
        # No synthetic detected. Now enforce expected source kind.
        if expected_source == "orderbook":
            # Trade-derived is explicitly not acceptable as "order-book restoration".
            if declared_kind == "trade_derived" or bool(notes.get("trade_derived_seen_in_market_snapshot")):
                verdict = "FAIL"
                errors.append("expected_source_mismatch:expected_orderbook_but_trade_derived_detected")
            elif _has_positive_provenance(manifest, expected_source="orderbook"):
                verdict = "PASS"
            else:
                verdict = "NOT_MEASURABLE"
                warnings.append("provenance_insufficient:missing_manifest.orderbook_provenance")
        elif expected_source == "trade_derived":
            if declared_kind == "trade_derived" or _has_positive_provenance(manifest, expected_source="trade_derived"):
                verdict = "PASS"
            else:
                verdict = "NOT_MEASURABLE"
                warnings.append("provenance_insufficient:missing_manifest.trade_provenance_or_trade_derived_dataset_version")
        else:
            verdict = "NOT_MEASURABLE"
            warnings.append("unknown_expected_source")

    result = GateResult(
        tool="verify_orderbook_e_contract_provenance_gate_v0",
        generated_at_utc=_utc_now(),
        dataset_dir=str(dataset_dir),
        manifest_path=str(manifest_path),
        market_snapshot_path=str(market_snapshot_path),
        expected_source=expected_source,
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

