#!/usr/bin/env bash
# One command that reproduces every offline check this package claims.
#
#   ./verify.sh [BUNDLE] [BENCHMARK_JSON]
#
# BUNDLE          path to r033-recon-bundle/bundle (needed for the patch-chain check)
# BENCHMARK_JSON  path to an r019-style benchmark.json (for the formula check)
#
# Without arguments it still runs the 30-odd checks that need no repo artefacts.
set -euo pipefail
cd "$(dirname "$0")"

args=()
if [ "${1:-}" != "" ]; then args+=(--bundle "$1"); fi
if [ "${2:-}" != "" ]; then args+=(--r019 "$2"); fi

python3 tools/verify_offline.py "${args[@]}"
