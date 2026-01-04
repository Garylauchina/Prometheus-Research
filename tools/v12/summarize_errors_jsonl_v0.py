#!/usr/bin/env python3
"""
Summarize errors.jsonl (Research repo, stdlib only).

This tool is for evidence review: it reads errors.jsonl (strict JSONL) and produces:
  - total count
  - counts by error_type
  - coarse buckets by message prefix (optional)

Exit codes:
  0: PASS (report produced)
  2: FAIL (strict JSONL broken)
  1: ERROR (IO)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--errors_jsonl", required=True, help="Path to errors.jsonl")
    ap.add_argument("--output", default="", help="Optional output json path")
    ap.add_argument("--message_prefix_len", type=int, default=0, help="If >0, bucket by message prefix length")
    args = ap.parse_args()

    p = Path(args.errors_jsonl).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not p.exists():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        return 1

    by_type: Dict[str, int] = {}
    by_prefix: Dict[str, int] = {}
    total = 0

    try:
        for _ln, rec in _iter_jsonl(p):
            total += 1
            et = rec.get("error_type", "unknown")
            et = str(et) if et is not None else "unknown"
            by_type[et] = by_type.get(et, 0) + 1

            if args.message_prefix_len > 0:
                msg = rec.get("message", "")
                msg = str(msg) if msg is not None else ""
                pref = msg[: args.message_prefix_len]
                by_prefix[pref] = by_prefix.get(pref, 0) + 1
    except ValueError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    report = {
        "tool": "summarize_errors_jsonl_v0",
        "generated_at_utc": _ts_utc(),
        "path": str(p),
        "total": total,
        "by_error_type": dict(sorted(by_type.items(), key=lambda x: (-x[1], x[0]))),
        "by_message_prefix": dict(sorted(by_prefix.items(), key=lambda x: (-x[1], x[0]))) if args.message_prefix_len > 0 else {},
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


