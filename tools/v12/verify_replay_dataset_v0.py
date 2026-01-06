#!/usr/bin/env python3
"""
Verify Replay Dataset v0 (Research repo, stdlib only).

Exit codes (frozen):
  - 0: PASS or NOT_MEASURABLE (prints WARNING when NOT_MEASURABLE)
  - 2: FAIL
  - 1: ERROR
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return obj


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


def _parse_iso_utc(ts: str) -> datetime:
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def verify(dataset_dir: Path, min_ticks: int, max_jitter_ms: int) -> Tuple[str, List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {}

    required = ["dataset_manifest.json", "market_snapshot.jsonl"]
    missing = [x for x in required if not (dataset_dir / x).exists()]
    if missing:
        errors.extend([f"missing required file: {x}" for x in missing])
        return "FAIL", errors, warnings, stats

    try:
        manifest = _read_json(dataset_dir / "dataset_manifest.json")
    except Exception as e:
        return "FAIL", [f"dataset_manifest.json invalid: {e}"], warnings, stats

    if manifest.get("dataset_kind") != "replay_snapshot_v0":
        errors.append(f"dataset_kind must be 'replay_snapshot_v0', got {manifest.get('dataset_kind')!r}")

    wc = manifest.get("world_contract")
    if not isinstance(wc, dict):
        errors.append("world_contract must be an object")
        wc = {}

    if wc.get("truth_profile") != "replay_truth":
        errors.append(f"world_contract.truth_profile must be 'replay_truth', got {wc.get('truth_profile')!r}")

    inst_id_expected = wc.get("inst_id")
    if not isinstance(inst_id_expected, str) or not inst_id_expected:
        errors.append("world_contract.inst_id must be a non-empty string")
        inst_id_expected = None

    tick_ms_expected = wc.get("tick_interval_ms")
    if not isinstance(tick_ms_expected, int) or tick_ms_expected <= 0:
        warnings.append("world_contract.tick_interval_ms missing/invalid; verifier will not enforce interval strictly")
        tick_ms_expected = None

    # Snapshot checks (minimal E fields + replay requirements)
    snapshot_ids = set()
    tick = 0
    prev_ts: Optional[datetime] = None
    inst_id_bad = 0
    missing_fields = 0

    deltas_ms: List[int] = []
    interval_violations = 0

    try:
        for line_no, rec in _iter_jsonl(dataset_dir / "market_snapshot.jsonl"):
            tick += 1
            # minimal required fields from canonical E schema
            for k in ["ts_utc", "inst_id", "snapshot_id", "source_endpoints", "quality"]:
                if k not in rec:
                    missing_fields += 1
                    errors.append(f"market_snapshot missing field {k} at line {line_no}")

            sid = rec.get("snapshot_id")
            if isinstance(sid, str) and sid:
                if sid in snapshot_ids:
                    errors.append(f"duplicate snapshot_id at line {line_no}: {sid}")
                snapshot_ids.add(sid)
            else:
                errors.append(f"snapshot_id missing/invalid at line {line_no}")

            inst = rec.get("inst_id")
            if inst_id_expected is not None and inst != inst_id_expected:
                inst_id_bad += 1

            ts = rec.get("ts_utc")
            if not isinstance(ts, str) or not ts:
                errors.append(f"ts_utc missing/invalid at line {line_no}")
                continue
            try:
                cur_ts = _parse_iso_utc(ts)
            except Exception:
                errors.append(f"ts_utc not isoformat at line {line_no}: {ts!r}")
                continue

            if prev_ts is not None:
                delta_ms = int((cur_ts - prev_ts).total_seconds() * 1000)
                deltas_ms.append(delta_ms)
                if delta_ms < 0:
                    errors.append(f"ts_utc went backward by {delta_ms}ms at line {line_no}")
                if tick_ms_expected is not None:
                    if abs(delta_ms - tick_ms_expected) > max_jitter_ms:
                        interval_violations += 1
            prev_ts = cur_ts
    except Exception as e:
        errors.append(f"market_snapshot.jsonl strict-jsonl failed: {e}")

    stats["tick_count"] = tick
    stats["unique_snapshot_id_count"] = len(snapshot_ids)
    stats["inst_id_bad_count"] = inst_id_bad
    stats["interval_violation_count"] = interval_violations
    if deltas_ms:
        stats["delta_ms_min"] = min(deltas_ms)
        stats["delta_ms_max"] = max(deltas_ms)

    if tick < min_ticks:
        errors.append(f"tick_count < min_ticks: {tick} < {min_ticks}")

    if inst_id_bad > 0:
        errors.append(f"inst_id mismatch for {inst_id_bad} record(s)")

    # Interval quality semantics:
    # - Tick interval stability is a QUALITY signal for replay datasets.
    # - Hard failures are reserved for missing evidence / strict-jsonl / backward time / duplicates / mixed inst_id.
    # - Excessive jitter degrades dataset to NOT_MEASURABLE (still usable for many baselines that only need ordering).
    if tick_ms_expected is not None and deltas_ms:
        violation_ratio = interval_violations / max(1, len(deltas_ms))
        stats["interval_violation_ratio"] = round(violation_ratio, 6)
        if interval_violations > 0:
            # Conservative: baseline dataset should have stable intervals.
            level = "unstable" if violation_ratio > 0.05 else "drift"
            warnings.append(
                f"tick interval {level}: violations={interval_violations} ratio={violation_ratio:.3f} "
                f"(expected {tick_ms_expected}ms ± {max_jitter_ms}ms)"
            )

    if errors:
        return "FAIL", errors, warnings, stats

    if warnings:
        return "NOT_MEASURABLE", errors, warnings, stats

    return "PASS", errors, warnings, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset_dir", required=True, help="Replay dataset directory (contains dataset_manifest.json)")
    ap.add_argument("--min_ticks", type=int, default=1000, help="Minimum ticks required")
    ap.add_argument("--max_jitter_ms", type=int, default=500, help="Allowed tick interval jitter (ms)")
    ap.add_argument("--output", default="", help="Optional report output path")
    args = ap.parse_args()

    dataset_dir = Path(args.dataset_dir).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not dataset_dir.exists():
        print(f"ERROR: dataset_dir not found: {dataset_dir}", file=sys.stderr)
        return 1

    verdict, errors, warnings, stats = verify(dataset_dir, args.min_ticks, args.max_jitter_ms)
    report = {
        "tool": "verify_replay_dataset_v0",
        "generated_at_utc": _ts_utc(),
        "dataset_dir": str(dataset_dir),
        "verdict": verdict,
        "min_ticks": args.min_ticks,
        "max_jitter_ms": args.max_jitter_ms,
        "stats": stats,
        "errors": errors,
        "warnings": warnings,
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))

    if verdict == "FAIL":
        return 2
    if verdict == "NOT_MEASURABLE":
        print("WARNING: verdict=NOT_MEASURABLE (dataset valid but degraded for baseline)", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


