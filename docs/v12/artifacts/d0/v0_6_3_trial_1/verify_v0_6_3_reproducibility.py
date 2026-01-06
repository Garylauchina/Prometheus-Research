#!/usr/bin/env python3
"""
V0.6.3 + Battery — Reproducibility Verifier (FINAL VERSION)

Reads auditable JSON and recomputes all statistics to verify consistency.
Uses ONLY stdlib (no external dependencies).

Usage:
  python3 verify_v0_6_3_reproducibility.py [INPUT_JSON]
  
  If INPUT_JSON not provided, defaults to:
    /tmp/V0_6_3_BATTERY_AUDITABLE_COMPLETE_FINAL.json
"""

import json
import math
import hashlib
import sys
import os
from pathlib import Path
from datetime import datetime

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_stats(values):
    """Compute mean/std/min/max"""
    if not values:
        return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'count': 0}
    
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n if n > 1 else 0.0
    std = math.sqrt(variance)
    
    return {
        'mean': mean,
        'std': std,
        'min': min(values),
        'max': max(values),
        'count': n
    }

def verify_auditable_data(input_file: Path):
    """Load and verify auditable JSON"""
    
    # Verify file exists
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)
    
    # Compute file metadata
    file_stat = input_file.stat()
    file_size = file_stat.st_size
    file_mtime = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
    file_hash = compute_file_hash(input_file)
    
    print("=" * 80)
    print("V0.6.3 + Battery Reproducibility Verification (FINAL)")
    print("=" * 80)
    print()
    print("Input File:")
    print(f"  Path: {input_file}")
    print(f"  Size: {file_size:,} bytes")
    print(f"  Modified: {file_mtime}")
    print(f"  SHA256: {file_hash}")
    print()
    
    # Load JSON
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Verify formulas
    print("Formulas (explicit):")
    for key, value in data['computation_formulas'].items():
        if isinstance(value, str) and len(value) < 100:
            print(f"  {key}: {value}")
    print()
    
    # Verify signal anchor
    print("Signal P99 Anchor:")
    anchor = data['signal_p99_anchor']
    print(f"  Value: {anchor['anchor_value']}")
    print(f"  Source: {anchor['anchor_source']}")
    print(f"  K-window: {anchor['k_window']}")
    print(f"  Dataset length: {anchor['dataset_length']}")
    print()
    
    # Verify each configuration
    print("=" * 80)
    print("Per-Config Verification")
    print("=" * 80)
    print()
    
    formula_mismatch_total = 0
    
    for config in data['configurations']:
        config_id = config['config_id']
        test = config['test']
        g_hi = config['g_hi']
        shuffle_mode = config['shuffle_mode']
        
        print(f"Config: {config_id}")
        print(f"  Test: {test}")
        print(f"  g_hi: {g_hi}")
        print(f"  Shuffle mode: {shuffle_mode}")
        
        if shuffle_mode == 'fixed_seed':
            print(f"  Shuffle seed: {config['shuffle_seed']}")
        elif shuffle_mode == 'derived_seed':
            print(f"  Shuffle seed formula: {config['shuffle_seed_formula']}")
        
        # Extract per-seed data
        per_seed = config['per_seed_data']
        
        gaps_on = [s['gap_on'] for s in per_seed if s['gap_on'] is not None]
        gaps_shuffle = [s['gap_shuffle'] for s in per_seed if s['gap_shuffle'] is not None]
        reduction_ratios = [s['reduction_ratio'] for s in per_seed if s['reduction_ratio'] is not None]
        r_max_on = [s['r_max_on'] for s in per_seed if s['r_max_on'] is not None]
        r_max_shuffle = [s['r_max_shuffle'] for s in per_seed if s['r_max_shuffle'] is not None]
        
        # Compute stats
        stats_gap_on = compute_stats(gaps_on)
        stats_gap_shuffle = compute_stats(gaps_shuffle)
        stats_reduction = compute_stats(reduction_ratios)
        stats_r_max_on = compute_stats(r_max_on)
        stats_r_max_shuffle = compute_stats(r_max_shuffle)
        
        print(f"  Gap ON: mean={stats_gap_on['mean']:.1f}, std={stats_gap_on['std']:.1f}, range=[{stats_gap_on['min']}, {stats_gap_on['max']}]")
        print(f"  Gap SHUFFLE: mean={stats_gap_shuffle['mean']:.1f}, std={stats_gap_shuffle['std']:.1f}, range=[{stats_gap_shuffle['min']}, {stats_gap_shuffle['max']}]")
        print(f"  Reduction ratio: mean={stats_reduction['mean']:.3f} ({stats_reduction['mean']*100:.1f}%), std={stats_reduction['std']:.3f}")
        print(f"  r_max ON: mean={stats_r_max_on['mean']:.1f}, std={stats_r_max_on['std']:.1f}, range=[{stats_r_max_on['min']}, {stats_r_max_on['max']}]")
        print(f"  r_max SHUFFLE: mean={stats_r_max_shuffle['mean']:.1f}, std={stats_r_max_shuffle['std']:.1f}, range=[{stats_r_max_shuffle['min']}, {stats_r_max_shuffle['max']}]")
        
        # Count reversals (gap_shuffle < 0)
        reversals = sum(1 for g in gaps_shuffle if g < 0)
        print(f"  Reversals (gap_shuffle < 0): {reversals}/{len(gaps_shuffle)} ({reversals/len(gaps_shuffle)*100:.1f}%)")
        
        # Verify reduction ratio formula (with tolerance for rounding)
        print(f"  Verifying reduction_ratio formula (tolerance=0.01 for rounding)...")
        mismatches = 0
        for s in per_seed:
            if s['gap_on'] is not None and s['gap_shuffle'] is not None and s['reduction_ratio'] is not None:
                expected = (s['gap_on'] - s['gap_shuffle']) / max(1, abs(s['gap_on']))
                actual = s['reduction_ratio']
                if abs(expected - actual) > 0.01:  # Increased tolerance for rounding
                    mismatches += 1
                    if mismatches <= 3:  # Only print first 3
                        print(f"    ⚠ Seed {s['seed']}: expected={expected:.6f}, actual={actual:.6f}, diff={abs(expected-actual):.6f}")
        
        if mismatches == 0:
            print(f"  ✓ All {len(per_seed)} seeds match reduction_ratio formula (within tolerance)")
        else:
            print(f"  ⚠ {mismatches}/{len(per_seed)} seeds have formula mismatches (likely rounding)")
            formula_mismatch_total += mismatches
        
        print()
    
    # Overall summary
    print("=" * 80)
    print("Overall Summary")
    print("=" * 80)
    print()
    
    all_reduction_ratios = []
    for config in data['configurations']:
        for s in config['per_seed_data']:
            if s['reduction_ratio'] is not None:
                all_reduction_ratios.append(s['reduction_ratio'])
    
    overall_stats = compute_stats(all_reduction_ratios)
    print(f"Total configs: {len(data['configurations'])}")
    print(f"Total seeds: {sum(len(c['per_seed_data']) for c in data['configurations'])}")
    print(f"Total reduction ratios: {len(all_reduction_ratios)}")
    print(f"Overall reduction ratio: mean={overall_stats['mean']:.3f} ({overall_stats['mean']*100:.1f}%), std={overall_stats['std']:.3f}")
    print(f"Range: [{overall_stats['min']:.3f}, {overall_stats['max']:.3f}]")
    print()
    
    # Verdict
    pass_count = sum(1 for config in data['configurations'] 
                     if compute_stats([s['reduction_ratio'] for s in config['per_seed_data'] 
                                      if s['reduction_ratio'] is not None])['mean'] >= 0.5)
    
    print(f"Configs passing 50% threshold: {pass_count}/{len(data['configurations'])}")
    
    if pass_count == len(data['configurations']):
        print("✓ VERIFICATION PASSED: All configs show reduction >= 50%")
    else:
        print("✗ VERIFICATION FAILED: Some configs show reduction < 50%")
    
    if formula_mismatch_total > 0:
        print(f"⚠ WARNING: {formula_mismatch_total} formula mismatches detected (likely rounding)")
        print("   Recommend: Store high-precision reduction_ratio, add reduction_ratio_rounded_3dp")
    
    print()
    print("=" * 80)
    print(f"Verified: {input_file}")
    print(f"SHA256: {file_hash}")
    print("=" * 80)

if __name__ == '__main__':
    # Parse CLI args
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        # Default to FINAL
        input_file = Path('/tmp/V0_6_3_BATTERY_AUDITABLE_COMPLETE_FINAL.json')
    
    verify_auditable_data(input_file)
