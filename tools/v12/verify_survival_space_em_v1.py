#!/usr/bin/env python3
"""
V12 Survival Space (E+M) verifier v1 (Research repo, stdlib only).

Purpose (fail-closed):
  - Verify `survival_space.jsonl` exists and follows strict JSONL + SSOT schema.
  - Verify ablation semantics when enabled (full/no_m/no_e/null).
  - Verify gate hard-constraint fields exist (action_allowed + reason codes).
  - Verify minimal join integrity:
      * survival_space.snapshot_id ∈ market_snapshot.snapshot_id
      * decision_trace.market_snapshot_id ∈ market_snapshot.snapshot_id
      * survival_space.account_id_hash can be joined with decision_trace/order_attempts

Exit codes (frozen):
  - 0: PASS or NOT_MEASURABLE (prints WARNING when NOT_MEASURABLE)
  - 2: FAIL (evidence missing / strict-jsonl broken / schema violation / join broken)
  - 1: ERROR (tool crash / invalid usage)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
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


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_str(x: Any) -> bool:
    return isinstance(x, str)


def _is_list_of_str(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _check_required_files(run_dir: Path, required: List[str]) -> List[str]:
    return [name for name in required if not (run_dir / name).exists()]


def _get_first_existing(run_dir: Path, names: List[str]) -> Optional[Path]:
    for n in names:
        p = run_dir / n
        if p.exists():
            return p
    return None


def _safe_get(d: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in d:
            return d.get(k)
    return None


@dataclass
class CheckResult:
    verdict: str  # PASS|NOT_MEASURABLE|FAIL
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]


def _verify_survival_space_schema(path: Path) -> Tuple[List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {"records": 0}

    required = [
        "ts_utc",
        "snapshot_id",
        "account_id_hash",
        "L_liq",
        "L_liq_mask",
        "L_liq_reason_codes",
        "L_imp",
        "L_imp_mask",
        "L_imp_reason_codes",
        "L",
        "L_mask",
        "L_reason_codes",
    ]

    bad_range = 0
    masked_not_null = 0
    unmasked_null = 0

    for line_no, rec in _iter_jsonl(path):
        stats["records"] += 1
        for k in required:
            if k not in rec:
                errors.append(f"survival_space missing key: {k} at line {line_no}")

        for k in ["ts_utc", "snapshot_id", "account_id_hash"]:
            if k in rec and rec[k] is not None and not _is_str(rec[k]):
                errors.append(f"survival_space.{k} must be string at line {line_no}")

        for k in ["L_liq_mask", "L_imp_mask", "L_mask"]:
            v = rec.get(k)
            if v is None:
                continue
            if v not in (0, 1):
                errors.append(f"survival_space.{k} must be 0|1 at line {line_no}")

        for k in ["L_liq_reason_codes", "L_imp_reason_codes", "L_reason_codes"]:
            v = rec.get(k)
            if v is None:
                errors.append(f"survival_space.{k} must be array[string] (not null) at line {line_no}")
            elif not _is_list_of_str(v):
                errors.append(f"survival_space.{k} must be array[string] at line {line_no}")

        # Mask discipline + numeric range
        for base in ["L_liq", "L_imp", "L"]:
            v = rec.get(base)
            m = rec.get(f"{base}_mask")
            if m == 0:
                if v is not None:
                    masked_not_null += 1
                    errors.append(f"survival_space.{base} must be null when {base}_mask=0 at line {line_no}")
            if m == 1:
                if v is None:
                    unmasked_null += 1
                    errors.append(f"survival_space.{base} must be number when {base}_mask=1 at line {line_no}")
                elif not _is_num(v):
                    errors.append(f"survival_space.{base} must be number|null at line {line_no}")
                else:
                    fv = float(v)
                    if fv < 0.0 or fv > 1.0:
                        bad_range += 1
                        errors.append(f"survival_space.{base} out of [0,1] at line {line_no}: {fv}")

        # Hard SSOT ban: forbid fixed-spread fallback derived from last_px
        # (see V12_SSOT_SURVIVAL_SPACE_EM_V1 §9)
        liq_rc = rec.get("L_liq_reason_codes", [])
        if isinstance(liq_rc, list) and "liq:spread_bps_from_last_px_fallback" in liq_rc:
            errors.append(
                f"forbidden_liq_fallback: liq:spread_bps_from_last_px_fallback at line {line_no} (SSOT §9)"
            )

    stats["masked_not_null_count"] = masked_not_null
    stats["unmasked_null_count"] = unmasked_null
    stats["out_of_range_count"] = bad_range
    return errors, warnings, stats


def _verify_ablation_semantics(
    manifest: Dict[str, Any],
    survival_space_path: Path,
) -> Tuple[List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {}

    ab = manifest.get("ablation", {})
    ss = ab.get("survival_space", {}) if isinstance(ab, dict) else {}
    enabled = bool(ss.get("enabled")) if isinstance(ss, dict) else False
    mode = ss.get("mode") if isinstance(ss, dict) else None

    stats["ablation_survival_space_enabled"] = enabled
    stats["ablation_survival_space_mode"] = mode

    if not enabled:
        return errors, warnings, stats

    if mode not in ("full", "no_m", "no_e", "null"):
        errors.append(f"run_manifest.ablation.survival_space.mode must be one of full/no_m/no_e/null, got {mode!r}")
        return errors, warnings, stats

    # Validate per-record semantics (best-effort, fail-closed on mismatch)
    checked = 0
    mismatches = 0
    for line_no, rec in _iter_jsonl(survival_space_path):
        checked += 1
        liq = rec.get("L_liq")
        liq_m = rec.get("L_liq_mask")
        liq_rc = rec.get("L_liq_reason_codes", [])
        imp = rec.get("L_imp")
        imp_m = rec.get("L_imp_mask")
        imp_rc = rec.get("L_imp_reason_codes", [])
        L = rec.get("L")
        L_m = rec.get("L_mask")
        L_rc = rec.get("L_reason_codes", [])

        def _must_have_ab_reason(rc: Any, code: str) -> bool:
            return isinstance(rc, list) and code in rc

        if mode == "no_m":
            if not (imp is None and imp_m == 0 and _must_have_ab_reason(imp_rc, "ablation:M_off")):
                mismatches += 1
                errors.append(f"ablation(no_m) violated at line {line_no}: L_imp must be null/mask=0/reason ablation:M_off")
            # L must equal L_liq when measurable; if L_mask=0, skip equality
            if L_m == 1 and liq_m == 1 and _is_num(L) and _is_num(liq) and float(L) != float(liq):
                mismatches += 1
                errors.append(f"ablation(no_m) violated at line {line_no}: L must equal L_liq")

        if mode == "no_e":
            if not (liq is None and liq_m == 0 and _must_have_ab_reason(liq_rc, "ablation:E_off")):
                mismatches += 1
                errors.append(f"ablation(no_e) violated at line {line_no}: L_liq must be null/mask=0/reason ablation:E_off")
            if L_m == 1 and imp_m == 1 and _is_num(L) and _is_num(imp) and float(L) != float(imp):
                mismatches += 1
                errors.append(f"ablation(no_e) violated at line {line_no}: L must equal L_imp")

        if mode == "null":
            # All masks must be 0 (values null)
            if not (liq is None and liq_m == 0 and imp is None and imp_m == 0 and L is None and L_m == 0):
                mismatches += 1
                errors.append(f"ablation(null) violated at line {line_no}: all L_* must be null with masks=0")
            # SSOT requires an explicit frozen reason code for null ablation
            if not _must_have_ab_reason(L_rc, "ablation:survival_space_null"):
                mismatches += 1
                errors.append(
                    f"ablation(null) violated at line {line_no}: L_reason_codes must include ablation:survival_space_null"
                )

        if mode == "full":
            # no explicit constraints beyond schema; still ensure not silently ablated
            if _must_have_ab_reason(liq_rc, "ablation:E_off") or _must_have_ab_reason(imp_rc, "ablation:M_off"):
                warnings.append(f"ablation(full) contains ablation reason_code at line {line_no}")

        if len(errors) > 1000:
            errors.append("too_many_errors:ablation_semantics (truncated)")
            break

    stats["ablation_checked_records"] = checked
    stats["ablation_mismatch_count"] = mismatches
    return errors, warnings, stats


def _load_snapshot_ids(market_snapshot_path: Path, max_collect: int = 200_000) -> Tuple[Optional[set], List[str], Dict[str, Any]]:
    errors: List[str] = []
    stats: Dict[str, Any] = {"snapshot_id_count": 0, "truncated": False}
    ids: set = set()
    try:
        for line_no, rec in _iter_jsonl(market_snapshot_path):
            sid = rec.get("snapshot_id")
            if not isinstance(sid, str) or not sid:
                errors.append(f"market_snapshot.snapshot_id missing/invalid at line {line_no}")
                continue
            ids.add(sid)
            if len(ids) >= max_collect:
                stats["truncated"] = True
                break
    except Exception as e:
        return None, [f"market_snapshot.jsonl strict-jsonl failed: {e}"], stats
    stats["snapshot_id_count"] = len(ids)
    return ids, errors, stats


def _verify_join_integrity(
    run_dir: Path,
    snapshot_ids: set,
    survival_space_path: Path,
    decision_trace_path: Path,
    order_attempts_path: Path,
) -> Tuple[List[str], List[str], Dict[str, Any]]:
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {}

    # 1) survival_space.snapshot_id must exist in market_snapshot
    ss_bad = 0
    ss_total = 0
    ss_accounts: set = set()
    try:
        for line_no, rec in _iter_jsonl(survival_space_path):
            ss_total += 1
            sid = rec.get("snapshot_id")
            if not isinstance(sid, str) or sid not in snapshot_ids:
                ss_bad += 1
                errors.append(f"survival_space.snapshot_id not found in market_snapshot at line {line_no}: {sid!r}")
            aid = rec.get("account_id_hash")
            if isinstance(aid, str) and aid:
                ss_accounts.add(aid)
            if ss_bad > 1000:
                errors.append("too_many_errors:survival_space_snapshot_id_join (truncated)")
                break
    except Exception as e:
        errors.append(f"survival_space.jsonl strict-jsonl failed: {e}")

    stats["survival_space_records"] = ss_total
    stats["survival_space_bad_snapshot_id_count"] = ss_bad
    stats["survival_space_unique_account_id_hash_count"] = len(ss_accounts)

    # 2) decision_trace.market_snapshot_id must exist in market_snapshot
    dt_bad = 0
    dt_total = 0
    dt_accounts: set = set()
    dt_has_gate_fields = False
    dt_has_intensity = False
    try:
        for line_no, rec in _iter_jsonl(decision_trace_path):
            dt_total += 1
            msid = _safe_get(rec, ["market_snapshot_id", "market_snapshot", "snapshot_id"])
            if not isinstance(msid, str) or msid not in snapshot_ids:
                dt_bad += 1
                errors.append(f"decision_trace.market_snapshot_id not found in market_snapshot at line {line_no}: {msid!r}")
            aid = _safe_get(rec, ["account_id_hash", "subaccount_id_hash"])
            if isinstance(aid, str) and aid:
                dt_accounts.add(aid)
            if isinstance(rec.get("action_allowed"), bool) and _is_list_of_str(rec.get("gate_reason_codes", [])):
                dt_has_gate_fields = True
            if _safe_get(rec, ["interaction_intensity", "intensity", "action_intensity"]) is not None:
                dt_has_intensity = True
            if dt_bad > 1000:
                errors.append("too_many_errors:decision_trace_snapshot_id_join (truncated)")
                break
    except Exception as e:
        errors.append(f"decision_trace.jsonl strict-jsonl failed: {e}")

    stats["decision_trace_records"] = dt_total
    stats["decision_trace_bad_market_snapshot_id_count"] = dt_bad
    stats["decision_trace_unique_account_id_hash_count"] = len(dt_accounts)
    stats["decision_trace_has_gate_fields"] = dt_has_gate_fields
    stats["decision_trace_has_intensity_field"] = dt_has_intensity

    # 3) order_attempts must have account anchor, and may carry gate fields if not in decision_trace
    oa_total = 0
    oa_missing_account = 0
    oa_has_gate_fields = False
    try:
        for line_no, rec in _iter_jsonl(order_attempts_path):
            oa_total += 1
            aid = _safe_get(rec, ["account_id_hash", "subaccount_id_hash"])
            if not isinstance(aid, str) or not aid:
                oa_missing_account += 1
                errors.append(f"order_attempts.account_id_hash missing/invalid at line {line_no}")
            if isinstance(rec.get("action_allowed"), bool) and _is_list_of_str(rec.get("gate_reason_codes", [])):
                oa_has_gate_fields = True
            if oa_missing_account > 1000:
                errors.append("too_many_errors:order_attempts_account_anchor (truncated)")
                break
    except Exception as e:
        errors.append(f"order_attempts.jsonl strict-jsonl failed: {e}")

    stats["order_attempts_records"] = oa_total
    stats["order_attempts_missing_account_id_hash_count"] = oa_missing_account
    stats["order_attempts_has_gate_fields"] = oa_has_gate_fields

    # Gate fields must exist in at least one place (hard constraint evidence).
    if not (dt_has_gate_fields or oa_has_gate_fields):
        errors.append("missing_gate_fields: require action_allowed(bool) + gate_reason_codes(array[string]) in decision_trace or order_attempts")

    # Account join sanity: survival_space accounts should intersect decision_trace/order_attempts
    if ss_accounts and dt_accounts and ss_accounts.isdisjoint(dt_accounts):
        warnings.append("account_id_hash mismatch: survival_space and decision_trace have disjoint account sets")

    return errors, warnings, stats


def verify(run_dir: Path) -> CheckResult:
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {}

    required = [
        "run_manifest.json",
        "market_snapshot.jsonl",
        "interaction_impedance.jsonl",
        "survival_space.jsonl",
        "decision_trace.jsonl",
        "order_attempts.jsonl",
        "errors.jsonl",
    ]
    missing = _check_required_files(run_dir, required)
    if missing:
        errors.extend([f"missing required file: {x}" for x in missing])
        return CheckResult(verdict="FAIL", errors=errors, warnings=warnings, stats=stats)

    try:
        manifest = _read_json(run_dir / "run_manifest.json")
    except Exception as e:
        return CheckResult(verdict="FAIL", errors=[f"run_manifest.json invalid: {e}"], warnings=warnings, stats=stats)

    rk = manifest.get("run_kind")
    if rk != "modeling_tool":
        errors.append(f"run_manifest.run_kind must be 'modeling_tool' for Survival Space experiments, got {rk!r}")

    # Optional: api_calls evidence, warn only (impedance may still be measurable but degraded)
    api_calls = _get_first_existing(run_dir, ["okx_api_calls.jsonl", "exchange_api_calls.jsonl"])
    stats["api_calls_file"] = str(api_calls) if api_calls is not None else ""
    if api_calls is None:
        warnings.append("missing api calls evidence file: okx_api_calls.jsonl/exchange_api_calls.jsonl")

    # strict jsonl + schema for survival_space
    ss_path = run_dir / "survival_space.jsonl"
    try:
        e_ss, w_ss, st_ss = _verify_survival_space_schema(ss_path)
        errors.extend(e_ss)
        warnings.extend(w_ss)
        stats["survival_space_schema"] = st_ss
    except Exception as e:
        errors.append(f"survival_space.jsonl strict-jsonl/schema failed: {e}")

    # ablation semantics (only when enabled)
    try:
        e_ab, w_ab, st_ab = _verify_ablation_semantics(manifest, ss_path)
        errors.extend(e_ab)
        warnings.extend(w_ab)
        stats["ablation"] = st_ab
    except Exception as e:
        errors.append(f"ablation semantics check crashed: {e}")

    # SSOT §9: If L_liq is NOT_MEASURABLE in full mode, then the run is NOT_MEASURABLE (degraded),
    # because L = min(L_liq, L_imp) implies L is also NOT_MEASURABLE (mask=0) at those ticks.
    # This is an evidence-valid but degraded condition (NOT_MEASURABLE), not a schema FAIL.
    try:
        ab = manifest.get("ablation", {})
        ss_ab = ab.get("survival_space", {}) if isinstance(ab, dict) else {}
        enabled = bool(ss_ab.get("enabled")) if isinstance(ss_ab, dict) else False
        mode = ss_ab.get("mode") if isinstance(ss_ab, dict) else None
        stats["ssot9_mode"] = mode
        if enabled and mode == "full":
            liq_not_meas = 0
            checked = 0
            for _ln, rec in _iter_jsonl(ss_path):
                checked += 1
                if rec.get("L_liq_mask") == 0:
                    liq_not_meas += 1
                    # stop early once we know it's degraded
                    if liq_not_meas > 0:
                        break
                if checked > 50_000:
                    break
            stats["ssot9_liq_not_measurable_seen"] = liq_not_meas > 0
            if liq_not_meas > 0:
                warnings.append("SSOT§9: L_liq NOT_MEASURABLE in full mode -> verdict=NOT_MEASURABLE")
                # Do not return yet if there are hard FAIL errors; we only degrade when errors==[]
                # (handled after the main error gate below)
    except Exception as e:
        errors.append(f"SSOT§9 measurability check crashed: {e}")

    # Join integrity
    ms_path = run_dir / "market_snapshot.jsonl"
    snapshot_ids, e_sid, st_sid = _load_snapshot_ids(ms_path)
    stats["market_snapshot"] = st_sid
    if snapshot_ids is None:
        errors.extend(e_sid)
    else:
        errors.extend(e_sid)
        try:
            e_join, w_join, st_join = _verify_join_integrity(
                run_dir=run_dir,
                snapshot_ids=snapshot_ids,
                survival_space_path=ss_path,
                decision_trace_path=run_dir / "decision_trace.jsonl",
                order_attempts_path=run_dir / "order_attempts.jsonl",
            )
            errors.extend(e_join)
            warnings.extend(w_join)
            stats["join"] = st_join
        except Exception as e:
            errors.append(f"join integrity check crashed: {e}")

    if errors:
        return CheckResult(verdict="FAIL", errors=errors, warnings=warnings, stats=stats)

    # Apply SSOT§9 degradation (after hard FAIL errors cleared)
    if stats.get("ssot9_liq_not_measurable_seen") is True:
        return CheckResult(verdict="NOT_MEASURABLE", errors=errors, warnings=warnings, stats=stats)

    # Degrade to NOT_MEASURABLE if errors.jsonl is non-empty (same spirit as verify_tick_loop_v0)
    try:
        err_count = 0
        for _ln, _rec in _iter_jsonl(run_dir / "errors.jsonl"):
            err_count += 1
            if err_count > 0:
                break
        stats["errors_jsonl_non_empty"] = err_count > 0
        if err_count > 0:
            warnings.append("errors.jsonl non-empty: degraded run (NOT_MEASURABLE)")
            return CheckResult(verdict="NOT_MEASURABLE", errors=errors, warnings=warnings, stats=stats)
    except Exception as e:
        return CheckResult(verdict="FAIL", errors=[f"errors.jsonl strict-jsonl failed: {e}"], warnings=warnings, stats=stats)

    return CheckResult(verdict="PASS", errors=errors, warnings=warnings, stats=stats)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True, help="Run dir containing v12 evidence files")
    ap.add_argument("--output", default="", help="Optional report output path (json)")
    args = ap.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    if not run_dir.exists():
        print(f"ERROR: run_dir not found: {run_dir}", file=sys.stderr)
        return 1

    res = verify(run_dir)

    report = {
        "tool": "verify_survival_space_em_v1",
        "generated_at_utc": _ts_utc(),
        "run_dir": str(run_dir),
        "verdict": res.verdict,
        "errors": res.errors,
        "warnings": res.warnings,
        "stats": res.stats,
    }

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))

    if res.verdict == "FAIL":
        return 2
    if res.verdict == "NOT_MEASURABLE":
        print("WARNING: verdict=NOT_MEASURABLE (evidence valid but degraded)", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # Allow piping to `head` without crashing the verifier output path.
        raise SystemExit(0)

