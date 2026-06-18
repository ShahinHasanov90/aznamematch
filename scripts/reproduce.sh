#!/usr/bin/env bash
# Reproduce the full AzNameMatch pipeline end-to-end from the committed seeds.
#   1. generate the frozen v1.0 dataset (data/full + data/sample + data/adversarial)
#   2. report blocking metrics (RR / PQ / PC)
#   3. run all matchers and write the reference results/ (accuracy + perf views)
#
# Requires: uv (https://docs.astral.sh/uv/). The semantic tier downloads model weights on
# first run (CPU only; no GPU required).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> [1/3] generate dataset"
uv run aznamematch generate --config configs/generation.yaml

echo "==> [2/3] blocking metrics"
uv run aznamematch block --config configs/generation.yaml --cap 6

echo "==> [3/3] benchmark matchers -> results/"
uv run aznamematch bench --config configs/benchmark.yaml

echo "==> done. See results/SUMMARY.md"
