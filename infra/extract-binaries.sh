#!/usr/bin/env bash
set -euo pipefail

IMAGE="ghcr.io/mrwaip/vpn-deck-builder:latest"

docker run --rm -v "./bin:/out" "$IMAGE" sh -c "cp /binaries/* /out/"

echo "==> Binaries extracted to ./bin/"
ls -lh ./bin/
