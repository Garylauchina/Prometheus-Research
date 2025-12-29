#!/usr/bin/env python3
"""
V11 Step 27 - Step 26 Evidence minimal verifier (fail-closed).

This tool is intentionally small and dependency-free (stdlib only).

Exit codes (frozen):
  0 = PASS
  1 = FAIL (evidence gap / inconsistent fields / broken refs)
  2 = ERROR (tool crash / unreadable inputs)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REQUIRED_FILES = [
    "run_manifest.json",
    "decision_trace.jsonl",
    "e_probes.jsonl",
    "mf_stats_ticks.jsonl",
    "comfort_ticks.jsonl",
    "FILELIST.ls.txt",
    "SHA256SUMS.txt",
]


@dataclass(frozen=True)
class Ref:
    file: str
    line: int


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_jsonl_line(path: Path, line_1based: int) -> Dict[str, Any]:
    if line_1based <= 0:
        raise ValueError(f"line must be 1-based positive int, got {line_1based}")
    with path.open("r", encoding="utf-8") as f:
        for i, raw in enumerate(f, start=1):
            if i == line_1based:
                return json.loads(raw)
    raise IndexError(f"line out of range: {path.name}:{line_1based}")


def _filelist_contains(filelist_path: Path, required: List[str]) -> List[str]:
    present = set()
    with filelist_path.open("r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            # accept either bare filename or relative path ending
            present.add(s)
            present.add(os.path.basename(s))
    missing = [name for name in required if name not in present]
    return missing


def _sha256sums_contains(sha_path: Path, required: List[str]) -> List[str]:
    present = set()
    with sha_path.open("r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            # common formats: "<hash>  <file>" or "<hash> *<file>"
            parts = s.split()
            if len(parts) < 2:
                continue
            file_part = parts[-1].lstrip("*")
            present.add(file_part)
            present.add(os.path.basename(file_part))
    missing = [name for name in required if name not in present]
    return missing


def _find_key(d: Dict[str, Any], candidate_keys: List[str]) -> Optional[str]:
    for k in candidate_keys:
        if k in d:
            return k
    return None


def _extract_evidence_refs(obj: Dict[str, Any]) -> List[Ref]:
    refs_raw = obj.get("evidence_refs")
    if refs_raw is None:
        return []
    if isinstance(refs_raw, dict):
        refs_raw = [refs_raw]
    refs: List[Ref] = []
    if not isinstance(refs_raw, list):
        return []
    for item in refs_raw:
        if not isinstance(item, dict):
            continue
        file_key = _find_key(item, ["file", "evidence_file", "path"])
        line_key = _find_key(item, ["line", "evidence_line"])
        if file_key is None or line_key is None:
            continue
        try:
            refs.append(Ref(file=str(item[file_key]), line=int(item[line_key])))
        except Exception:
            continue
    return refs


def verify(run_dir: Path) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    # 1) required files exist
    for name in REQUIRED_FILES:
        p = run_dir / name
        if not p.exists():
            errors.append(f"missing required file: {name}")

    if errors:
        return False, errors

    # 2) FILELIST + SHA256SUMS must cover required files
    missing_in_filelist = _filelist_contains(run_dir / "FILELIST.ls.txt", REQUIRED_FILES)
    if missing_in_filelist:
        errors.append(f"FILELIST missing: {missing_in_filelist}")

    missing_in_sha = _sha256sums_contains(run_dir / "SHA256SUMS.txt", REQUIRED_FILES)
    if missing_in_sha:
        errors.append(f"SHA256SUMS missing: {missing_in_sha}")

    # 3) manifest feature_contract integrity
    manifest = _read_json(run_dir / "run_manifest.json")
    fc = manifest.get("feature_contract")
    if not isinstance(fc, dict):
        errors.append("run_manifest.json missing feature_contract (dict)")
        return False, errors

    for k in ["contract_version", "dimension", "probe_order", "probe_categories"]:
        if k not in fc:
            errors.append(f"feature_contract missing key: {k}")

    probe_order = fc.get("probe_order")
    dimension = fc.get("dimension")
    if isinstance(probe_order, list) and isinstance(dimension, int):
        if len(probe_order) != dimension:
            errors.append(f"feature_contract.dimension != len(probe_order): {dimension} vs {len(probe_order)}")

    # 4) decision_trace tick summaries must reference e/mf/comfort
    dt_path = run_dir / "decision_trace.jsonl"
    needed_ref_files = {"e_probes.jsonl", "mf_stats_ticks.jsonl", "comfort_ticks.jsonl"}

    # parse decision_trace line-by-line (lightweight)
    with dt_path.open("r", encoding="utf-8") as f:
        for idx, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except Exception as e:
                errors.append(f"decision_trace.jsonl line {idx} invalid json: {e}")
                continue

            # We only enforce on tick summary-like records (best effort):
            if "tick" not in rec:
                continue

            # Required scalar fields (best effort; allow naming differences)
            if "feature_contract_version" not in rec:
                # tolerate older naming if present
                pass

            tf = rec.get("total_features_count")
            ef = rec.get("effective_features_count")
            if isinstance(tf, int) and isinstance(ef, int):
                if ef < 0 or tf < 0 or ef > tf:
                    errors.append(f"tick={rec.get('tick')}: invalid effective/total counts: {ef}/{tf}")

            refs = _extract_evidence_refs(rec)
            if not refs:
                # if a tick exists but has no refs, it's an evidence gap for Step26 claims
                errors.append(f"tick={rec.get('tick')}: missing evidence_refs (decision_trace line {idx})")
                continue

            ref_files = {os.path.basename(r.file) for r in refs}
            missing = sorted(list(needed_ref_files - ref_files))
            if missing:
                errors.append(f"tick={rec.get('tick')}: evidence_refs missing {missing} (decision_trace line {idx})")
                continue

            # verify referenced lines are addressable
            for r in refs:
                base = os.path.basename(r.file)
                if base not in needed_ref_files:
                    continue
                try:
                    _ = _read_jsonl_line(run_dir / base, r.line)
                except Exception as e:
                    errors.append(f"tick={rec.get('tick')}: broken ref {base}:{r.line} ({e})")

    ok = len(errors) == 0
    return ok, errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="Path to run_dir containing manifest and evidence jsonl files.")
    args = ap.parse_args()

    try:
        run_dir = Path(args.run_dir).expanduser().resolve()
        if not run_dir.exists() or not run_dir.is_dir():
            print(f"ERROR: run-dir is not a directory: {run_dir}", file=sys.stderr)
            return 2

        ok, errs = verify(run_dir)
        if ok:
            print("PASS: Step26 minimal evidence checklist satisfied")
            return 0

        print("FAIL: Step26 minimal evidence checklist NOT satisfied", file=sys.stderr)
        for e in errs:
            print(f"- {e}", file=sys.stderr)
        return 1
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: verifier crashed: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


