#!/usr/bin/env bash
# Run Python smoke tests inside a Steam Deck OS container (holo-base).
# This validates that main.py loads correctly in the actual target environment.
set -euo pipefail

IMAGE="ghcr.io/steamdeckhomebrew/holo-base:latest"

echo "==> Running smoke tests in ${IMAGE}"

docker run --rm \
    --platform linux/amd64 \
    -v "$(pwd):/plugin:ro" \
    -w /plugin \
    "$IMAGE" \
    bash -c "
        set -e
        PYTHONPATH=py_modules python3 test_unit.py
        PYTHONPATH=py_modules python3 test_plugin_smoke.py
    "
