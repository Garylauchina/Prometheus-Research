#!/usr/bin/env python3
"""
Build a Replay Dataset v0 directory from a Quant run_dir (stdlib only).

This is a packaging tool for offline replay (replay_truth baseline).
It DOES NOT talk to exchanges. It only copies/verifies local evidence files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


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


def _count_jsonl(path: Path) -> int:
    n = 0
    for _ln, _rec in _iter_jsonl(path):
        n += 1
    return n


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Avoid shutil dependency quirks; do a streaming copy.
    with src.open("rb") as fsrc, dst.open("wb") as fdst:
        for chunk in iter(lambda: fsrc.read(1024 * 1024), b""):
            fdst.write(chunk)


def _compact_ts(ts: str) -> str:
    # Best-effort; keep original if unknown format.
    s = ts.strip()
    return (
        s.replace("-", "")
        .replace(":", "")
        .replace(".000", "")
        .replace(".000000", "")
        .replace("+00:00", "Z")
    )


def build_dataset(source_run_dir: Path, output_root: Path, dataset_id: str | None, tick_interval_ms: int | None) -> Path:
    required = ["market_snapshot.jsonl"]
    for name in required:
        if not (source_run_dir / name).exists():
            raise FileNotFoundError(f"missing required source file: {name}")

    # Strict-jsonl + infer inst_id and tick count
    inst_id: str | None = None
    for _ln, rec in _iter_jsonl(source_run_dir / "market_snapshot.jsonl"):
        if inst_id is None:
            v = rec.get("inst_id")
            if isinstance(v, str) and v:
                inst_id = v
        # We do not fully validate E schema here (verifier does it); only ensure strict JSONL.
    if inst_id is None:
        inst_id = "UNKNOWN"

    tick_count = _count_jsonl(source_run_dir / "market_snapshot.jsonl")
    if tick_count <= 0:
        raise ValueError("market_snapshot.jsonl is empty (no records)")

    source_manifest_path = source_run_dir / "run_manifest.json"
    source_manifest: Dict[str, Any] = _read_json(source_manifest_path) if source_manifest_path.exists() else {}

    # Infer tick_interval_ms from manifest when possible
    inferred_tick_ms = None
    tl = source_manifest.get("tick_loop")
    if isinstance(tl, dict):
        v = tl.get("tick_interval_ms")
        if isinstance(v, int) and v > 0:
            inferred_tick_ms = v
    tick_ms = tick_interval_ms or inferred_tick_ms or 1000

    # Infer start/end from manifest when possible
    start_utc = None
    end_utc = None
    if isinstance(tl, dict):
        su = tl.get("start_ts_utc")
        eu = tl.get("end_ts_utc")
        if isinstance(su, str) and su:
            start_utc = su
        if isinstance(eu, str) and eu:
            end_utc = eu

    if dataset_id is None:
        s0 = _compact_ts(start_utc) if start_utc else "UNKNOWN_START"
        s1 = _compact_ts(end_utc) if end_utc else "UNKNOWN_END"
        dataset_id = f"dataset_replay_v0_{inst_id}_{s0}_{s1}_{tick_ms}ms"

    dataset_dir = (output_root / dataset_id).expanduser().resolve()
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # Copy files
    _copy_file(source_run_dir / "market_snapshot.jsonl", dataset_dir / "market_snapshot.jsonl")

    if (source_run_dir / "okx_api_calls.jsonl").exists():
        _copy_file(source_run_dir / "okx_api_calls.jsonl", dataset_dir / "okx_api_calls.jsonl")
    elif (source_run_dir / "exchange_api_calls.jsonl").exists():
        _copy_file(source_run_dir / "exchange_api_calls.jsonl", dataset_dir / "exchange_api_calls.jsonl")

    if (source_run_dir / "errors.jsonl").exists():
        _copy_file(source_run_dir / "errors.jsonl", dataset_dir / "errors.jsonl")

    if source_manifest_path.exists():
        _copy_file(source_manifest_path, dataset_dir / "source_run_manifest.json")

    # Manifest
    files: Dict[str, Any] = {}
    ms_path = dataset_dir / "market_snapshot.jsonl"
    files["market_snapshot.jsonl"] = {
        "path": "market_snapshot.jsonl",
        "sha256": _sha256_file(ms_path),
        "record_count": _count_jsonl(ms_path),
    }

    for opt in ["okx_api_calls.jsonl", "exchange_api_calls.jsonl", "errors.jsonl", "source_run_manifest.json"]:
        p = dataset_dir / opt
        if p.exists():
            if p.suffix == ".jsonl":
                # Strict jsonl check by counting
                rc = _count_jsonl(p)
            else:
                rc = None
            files[opt] = {"path": opt, "sha256": _sha256_file(p), "record_count": rc}

    ds_manifest = {
        "dataset_kind": "replay_snapshot_v0",
        "dataset_id": dataset_id,
        "created_at_utc": _ts_utc(),
        "source": {
            "source_run_dir": str(source_run_dir),
            "source_run_id": source_manifest.get("run_id"),
            "source_run_kind": source_manifest.get("run_kind"),
        },
        "world_contract": {
            "truth_profile": "replay_truth",
            "inst_id": inst_id,
            "tick_interval_ms": tick_ms,
            "schema_contract": "docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md",
        },
        "files": files,
    }

    (dataset_dir / "dataset_manifest.json").write_text(
        json.dumps(ds_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    return dataset_dir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source_run_dir", required=True, help="Quant run_dir containing market_snapshot.jsonl")
    ap.add_argument("--output_root", default="./datasets_v12", help="Output root directory (local artifact)")
    ap.add_argument("--dataset_id", default="", help="Optional dataset_id override")
    ap.add_argument("--tick_interval_ms", type=int, default=0, help="Optional override (default from manifest or 1000)")
    args = ap.parse_args()

    source_run_dir = Path(args.source_run_dir).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()

    if not source_run_dir.exists():
        print(f"ERROR: source_run_dir not found: {source_run_dir}", file=sys.stderr)
        return 1

    try:
        ds_dir = build_dataset(
            source_run_dir=source_run_dir,
            output_root=output_root,
            dataset_id=(args.dataset_id.strip() or None),
            tick_interval_ms=(args.tick_interval_ms if args.tick_interval_ms > 0 else None),
        )
    except Exception as e:
        print(f"ERROR: build failed: {e}", file=sys.stderr)
        return 2

    print(json.dumps({"tool": "build_replay_dataset_v0", "dataset_dir": str(ds_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


