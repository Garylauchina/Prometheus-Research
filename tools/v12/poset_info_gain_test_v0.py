#!/usr/bin/env python3
"""
Survival Space Poset §3 — No-Informational-Gain test v0 (Research repo, stdlib only).

Compares:
  - Baseline (M-only) predictor from no_e: y_hat = [order_attempts_count(no_e) > 0]
  - Poset monotone predictor using configurable dims from full: (x1_field, x2_field)

Label (frozen v0):
  y_full = [order_attempts_count(full) > 0]

Train/test split (frozen v0): seed parity
  train: seed % 2 == 0
  test:  seed % 2 == 1

Poset predictor family (supported models):
  - per_level_threshold (legacy; designed for discrete x2 like block_rate):
      * define x1 threshold per x2 level with monotone constraint across levels
      * predict y_hat=0 (cannot act) if x1 >= threshold(level)
  - axis_or (Round-2 friendly; continuous x2 like downshift_rate):
      * predict y_hat=0 if (x1 >= t1) OR (x2 >= t2)
      * monotone under (higher=harder) without weights/scoring

Exit codes:
  0: PASS (report produced; verdict in JSON)
  2: FAIL (input invalid / missing data)
  1: ERROR (tool crash)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


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


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


@dataclass(frozen=True)
class Pair:
    seed: int
    # label from full
    y_full: int
    # baseline from no_e
    y_hat_baseline: int
    # poset dims from full
    suppression_ratio: float
    x2: float


def _acc(y_true: List[int], y_hat: List[int]) -> float:
    if not y_true:
        return 0.0
    ok = 0
    for a, b in zip(y_true, y_hat):
        if a == b:
            ok += 1
    return ok / len(y_true)


def _load_pairs(per_run_metrics_jsonl: Path, x1_field: str, x2_field: str) -> List[Pair]:
    # index by (mode, seed)
    by_mode_seed: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for _ln, rec in _iter_jsonl(per_run_metrics_jsonl):
        mode = rec.get("mode")
        seed = rec.get("seed")
        if not isinstance(mode, str) or mode not in ("full", "no_e"):
            continue
        if not _is_int(seed):
            continue
        by_mode_seed[(mode, int(seed))] = rec

    out: List[Pair] = []
    seeds = sorted(set(s for (m, s) in by_mode_seed.keys() if m == "full"))
    for s in seeds:
        full = by_mode_seed.get(("full", s))
        noe = by_mode_seed.get(("no_e", s))
        if full is None or noe is None:
            continue

        oa_full = full.get("order_attempts_count")
        oa_noe = noe.get("order_attempts_count")
        if not (_is_int(oa_full) and _is_int(oa_noe)):
            continue

        y_full = 1 if int(oa_full) > 0 else 0
        y_hat_baseline = 1 if int(oa_noe) > 0 else 0

        x1 = full.get(x1_field)
        x2 = full.get(x2_field)
        if not (_is_num(x1) and _is_num(x2)):
            continue

        out.append(
            Pair(
                seed=s,
                y_full=y_full,
                y_hat_baseline=y_hat_baseline,
                suppression_ratio=float(x1),
                x2=float(x2),
            )
        )
    return out


def _x2_levels(pairs: List[Pair]) -> List[float]:
    xs = sorted(set(p.x2 for p in pairs))
    return xs


def _candidate_thresholds(values: List[float]) -> List[float]:
    # thresholds on suppression_ratio; include extremes
    xs = sorted(set(values))
    if not xs:
        return [0.0, 1.0]
    out = [xs[0] - 1e-12]
    out.extend(xs)
    out.append(xs[-1] + 1e-12)
    # Ensure feasibility under monotone constraints across discrete block_rate levels.
    # suppression_ratio is bounded in [0,1], but a level might need a threshold at 1.0 even if not present in this slice.
    if 1.0 not in out:
        out.append(1.0)
    out.append(1.0 + 1e-12)
    return out


def _predict_poset_per_level(pairs: List[Pair], thresholds_by_level: Dict[float, float]) -> List[int]:
    yhat: List[int] = []
    for p in pairs:
        th = thresholds_by_level[p.x2]
        # y_hat=0 if too hard (suppression >= th), else 1
        yhat.append(0 if p.suppression_ratio >= th else 1)
    return yhat


def _fit_thresholds_monotone_per_level(train: List[Pair]) -> Dict[str, Any]:
    levels = _x2_levels(train)
    # collect candidate thresholds per level
    cand_by_level: Dict[float, List[float]] = {}
    for lv in levels:
        vals = [p.suppression_ratio for p in train if p.x2 == lv]
        cand_by_level[lv] = _candidate_thresholds(vals)

    # brute-force search over small number of levels (empirically 2)
    best = None

    def rec(i: int, prev_th: Optional[float], cur: Dict[float, float]) -> None:
        nonlocal best
        if i >= len(levels):
            y_true = [p.y_full for p in train]
            y_hat = _predict_poset_per_level(train, cur)
            acc = _acc(y_true, y_hat)
            if best is None or acc > best["train_accuracy"]:
                best = {"thresholds": dict(cur), "train_accuracy": acc}
            return
        lv = levels[i]
        for th in cand_by_level[lv]:
            # monotone constraint: for higher block_rate (harder), threshold must be <= prev threshold
            if prev_th is not None and th > prev_th:
                continue
            cur[lv] = th
            rec(i + 1, th, cur)
            del cur[lv]

    rec(0, None, {})
    assert best is not None
    return {"x2_levels": levels, **best}


def _predict_poset_axis_or(pairs: List[Pair], t1: float, t2: float) -> List[int]:
    yhat: List[int] = []
    for p in pairs:
        yhat.append(0 if (p.suppression_ratio >= t1 or p.x2 >= t2) else 1)
    return yhat


def _fit_thresholds_axis_or(train: List[Pair]) -> Dict[str, Any]:
    cand_t1 = _candidate_thresholds([p.suppression_ratio for p in train])
    cand_t2 = _candidate_thresholds([p.x2 for p in train])
    best = None
    y_true = [p.y_full for p in train]
    for t1 in cand_t1:
        for t2 in cand_t2:
            y_hat = _predict_poset_axis_or(train, float(t1), float(t2))
            acc = _acc(y_true, y_hat)
            if best is None or acc > best["train_accuracy"]:
                best = {"t1": float(t1), "t2": float(t2), "train_accuracy": acc}
    assert best is not None
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per_run_metrics_jsonl", required=True)
    ap.add_argument("--x1_field", default="suppression_ratio", help="x1 field name in per_run_metrics (default: suppression_ratio)")
    ap.add_argument("--x2_field", default="block_rate", help="x2 field name in per_run_metrics (default: block_rate)")
    ap.add_argument(
        "--model",
        default="per_level_threshold",
        choices=["per_level_threshold", "axis_or"],
        help="Poset predictor model family (default: per_level_threshold)",
    )
    ap.add_argument("--output_json", required=True)
    ap.add_argument("--output_md", required=True)
    args = ap.parse_args()

    src = Path(args.per_run_metrics_jsonl).expanduser().resolve()
    if not src.exists():
        print(f"FAIL: per_run_metrics_jsonl not found: {src}", file=sys.stderr)
        return 2

    try:
        pairs = _load_pairs(src, str(args.x1_field), str(args.x2_field))
    except Exception as e:
        print(f"FAIL: load pairs: {e}", file=sys.stderr)
        return 2

    if len(pairs) < 50:
        report = {
            "tool": "poset_info_gain_test_v0",
            "generated_at_utc": _ts_utc(),
            "verdict": "NOT_MEASURABLE",
            "reason": "insufficient_pairs",
            "pairs_count": len(pairs),
        }
        Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        Path(args.output_md).write_text("# NOT_MEASURABLE: insufficient pairs\n", encoding="utf-8")
        return 0

    train = [p for p in pairs if (p.seed % 2) == 0]
    test = [p for p in pairs if (p.seed % 2) == 1]

    if args.model == "per_level_threshold":
        fit = _fit_thresholds_monotone_per_level(train)
        thresholds_by_level: Optional[Dict[float, float]] = fit["thresholds"]
    else:
        fit = _fit_thresholds_axis_or(train)
        thresholds_by_level = None

    y_train = [p.y_full for p in train]
    y_test = [p.y_full for p in test]

    yhat_baseline_train = [p.y_hat_baseline for p in train]
    yhat_baseline_test = [p.y_hat_baseline for p in test]

    if args.model == "per_level_threshold":
        yhat_poset_train = _predict_poset_per_level(train, thresholds_by_level or {})
        yhat_poset_test = _predict_poset_per_level(test, thresholds_by_level or {})
    else:
        yhat_poset_train = _predict_poset_axis_or(train, float(fit["t1"]), float(fit["t2"]))
        yhat_poset_test = _predict_poset_axis_or(test, float(fit["t1"]), float(fit["t2"]))

    acc_baseline_train = _acc(y_train, yhat_baseline_train)
    acc_baseline_test = _acc(y_test, yhat_baseline_test)
    acc_poset_train = _acc(y_train, yhat_poset_train)
    acc_poset_test = _acc(y_test, yhat_poset_test)

    # Falsification rule (frozen in pre-reg): if poset not strictly better on test => FAIL (no info gain)
    verdict = "PASS" if acc_poset_test > acc_baseline_test else "FAIL"

    report = {
        "tool": "poset_info_gain_test_v0",
        "generated_at_utc": _ts_utc(),
        "per_run_metrics_jsonl": str(src),
        "label": {"y_full": "order_attempts_count(full) > 0"},
        "baseline": {"y_hat_baseline": "order_attempts_count(no_e) > 0"},
        "poset_dims": {
            "x1": f"{args.x1_field}(full)",
            "x2": f"{args.x2_field}(full)",
            "direction": "higher=harder",
            "model": str(args.model),
        },
        "split": {"train": "seed%2==0", "test": "seed%2==1"},
        "fit": fit,
        "metrics": {
            "pairs_count": len(pairs),
            "train_count": len(train),
            "test_count": len(test),
            "accuracy_baseline_train": acc_baseline_train,
            "accuracy_baseline_test": acc_baseline_test,
            "accuracy_poset_train": acc_poset_train,
            "accuracy_poset_test": acc_poset_test,
        },
        "verdict": verdict,
        "interpretation": "FAIL means no informational gain over M-only baseline under §3; PASS means poset survives this knife only.",
    }

    out_json = Path(args.output_json).expanduser().resolve()
    out_md = Path(args.output_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = []
    md.append("# Survival Space Poset §3 — No-Informational-Gain Test v0\n\n")
    md.append(f"- generated_at_utc: {report['generated_at_utc']}\n")
    md.append(f"- pairs_count: {len(pairs)} (train={len(train)}, test={len(test)})\n")
    md.append(f"- verdict: **{verdict}**\n\n")
    md.append("## Accuracies\n\n")
    md.append(f"- baseline_test_accuracy: {acc_baseline_test}\n")
    md.append(f"- poset_test_accuracy: {acc_poset_test}\n")
    md.append("\n## Fitted thresholds (monotone)\n\n")
    if args.model == "per_level_threshold":
        for lv in fit["x2_levels"]:
            md.append(f"- {args.x2_field}={lv}: {args.x1_field}_threshold={thresholds_by_level[lv]}\n")
    else:
        md.append(f"- {args.x1_field}_threshold(t1)={fit['t1']}\n")
        md.append(f"- {args.x2_field}_threshold(t2)={fit['t2']}\n")
    out_md.write_text("".join(md), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

