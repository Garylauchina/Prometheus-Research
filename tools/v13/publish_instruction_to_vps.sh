#!/bin/bash
# V13: Publish instruction files to VPS — 2026-01-12
#
# Usage: ./publish_instruction_to_vps.sh <INSTRUCTION_FILE> [VPS_HOST] [VPS_USER]
#
# Example:
#   ./publish_instruction_to_vps.sh docs/v13/deliveries/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md
#   ./publish_instruction_to_vps.sh docs/v13/deliveries/V13_XXX_EXEC_YYYYMMDD.md 45.76.97.37 root

set -euo pipefail

INSTRUCTION_FILE="${1:-}"
VPS_HOST="${2:-45.76.97.37}"
VPS_USER="${3:-root}"

if [ -z "$INSTRUCTION_FILE" ]; then
    echo "Usage: $0 <INSTRUCTION_FILE> [VPS_HOST] [VPS_USER]"
    echo ""
    echo "Example:"
    echo "  $0 docs/v13/deliveries/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md"
    echo "  $0 docs/v13/deliveries/V13_XXX_EXEC_YYYYMMDD.md 45.76.97.37 root"
    exit 1
fi

if [ ! -f "$INSTRUCTION_FILE" ]; then
    echo "Error: Instruction file not found: $INSTRUCTION_FILE"
    exit 1
fi

# VPS instruction directory (frozen)
VPS_INSTRUCTION_DIR="/data/prometheus/v13_instructions"

# Get filename
FILENAME=$(basename "$INSTRUCTION_FILE")

echo "Publishing instruction to VPS..."
echo "  VPS: ${VPS_USER}@${VPS_HOST}"
echo "  Local file: $INSTRUCTION_FILE"
echo "  VPS directory: ${VPS_INSTRUCTION_DIR}"
echo "  VPS filename: ${FILENAME}"
echo ""

# Create instruction directory on VPS (if not exists)
echo "Creating instruction directory on VPS..."
ssh ${VPS_USER}@${VPS_HOST} "mkdir -p ${VPS_INSTRUCTION_DIR}"

# Upload instruction file
echo "Uploading instruction file..."
scp "$INSTRUCTION_FILE" ${VPS_USER}@${VPS_HOST}:${VPS_INSTRUCTION_DIR}/${FILENAME}

# Verify upload
if ssh ${VPS_USER}@${VPS_HOST} "test -f ${VPS_INSTRUCTION_DIR}/${FILENAME}"; then
    echo ""
    echo "✓ Instruction file published successfully!"
    echo "  VPS path: ${VPS_INSTRUCTION_DIR}/${FILENAME}"
    echo ""
    echo "Programmer can read it with:"
    echo "  cat ${VPS_INSTRUCTION_DIR}/${FILENAME}"
else
    echo "Error: Upload verification failed"
    exit 1
fi
