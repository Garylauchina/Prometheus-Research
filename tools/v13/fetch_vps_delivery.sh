#!/bin/bash
# V13: Fetch delivery files from VPS — 2026-01-12
#
# Usage: ./fetch_vps_delivery.sh <WINDOW_ID> [VPS_HOST] [VPS_USER]
#
# Example:
#   ./fetch_vps_delivery.sh BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h
#   ./fetch_vps_delivery.sh BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h 45.76.97.37 root

set -euo pipefail

WINDOW_ID="${1:-}"
VPS_HOST="${2:-45.76.97.37}"
VPS_USER="${3:-root}"

if [ -z "$WINDOW_ID" ]; then
    echo "Usage: $0 <WINDOW_ID> [VPS_HOST] [VPS_USER]"
    echo ""
    echo "Example:"
    echo "  $0 BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h"
    echo "  $0 BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h 45.76.97.37 root"
    exit 1
fi

WINDOW_DIR="/data/prometheus/live_capture_v13/windows/${WINDOW_ID}"
OUTPUT_DIR="/tmp/v13_${WINDOW_ID}_delivery"

echo "Fetching delivery from VPS..."
echo "  VPS: ${VPS_USER}@${VPS_HOST}"
echo "  Window: ${WINDOW_DIR}"
echo "  Output: ${OUTPUT_DIR}"
echo ""

mkdir -p "${OUTPUT_DIR}"

# Fetch completion report (if exists)
if ssh ${VPS_USER}@${VPS_HOST} "test -f ${WINDOW_DIR}/V13_PHASE1_WINDOW_COMPLETION_REPORT.md" 2>/dev/null; then
    echo "✓ Fetching completion report..."
    ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/V13_PHASE1_WINDOW_COMPLETION_REPORT.md" > "${OUTPUT_DIR}/V13_PHASE1_WINDOW_COMPLETION_REPORT.md"
else
    echo "⚠ Completion report not found (may not exist yet)"
fi

# Fetch required window files (V13 Capture Window Minimal Contract)
echo "✓ Fetching window.meta.yaml..."
if ssh ${VPS_USER}@${VPS_HOST} "test -f ${WINDOW_DIR}/window.meta.yaml" 2>/dev/null; then
    ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/window.meta.yaml" > "${OUTPUT_DIR}/window.meta.yaml"
else
    echo "  ⚠ window.meta.yaml not found"
fi

echo "✓ Fetching phenomena.log.md..."
if ssh ${VPS_USER}@${VPS_HOST} "test -f ${WINDOW_DIR}/phenomena.log.md" 2>/dev/null; then
    ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/phenomena.log.md" > "${OUTPUT_DIR}/phenomena.log.md"
else
    echo "  ⚠ phenomena.log.md not found"
fi

echo "✓ Fetching verdict.md..."
if ssh ${VPS_USER}@${VPS_HOST} "test -f ${WINDOW_DIR}/verdict.md" 2>/dev/null; then
    ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/verdict.md" > "${OUTPUT_DIR}/verdict.md"
else
    echo "  ⚠ verdict.md not found"
fi

# Fetch evidence.json (if exists)
echo "✓ Fetching evidence.json..."
if ssh ${VPS_USER}@${VPS_HOST} "test -f ${WINDOW_DIR}/evidence.json" 2>/dev/null; then
    ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/evidence.json" > "${OUTPUT_DIR}/evidence.json"
    echo "  ✓ evidence.json fetched"
else
    echo "  ⚠ evidence.json not found (may not be generated yet)"
fi

# Fetch verifier JSON (if exists)
echo "✓ Fetching verifier JSON..."
if ssh ${VPS_USER}@${VPS_HOST} "test -f ${WINDOW_DIR}/v13_world_contract_v0_2_verdict.json" 2>/dev/null; then
    ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/v13_world_contract_v0_2_verdict.json" > "${OUTPUT_DIR}/v13_world_contract_v0_2_verdict.json"
    echo "  ✓ verifier JSON fetched"
else
    echo "  ⚠ verifier JSON not found (may not be run yet)"
fi

echo ""
echo "✓ Delivery files fetched to: ${OUTPUT_DIR}/"
ls -lh "${OUTPUT_DIR}/"
