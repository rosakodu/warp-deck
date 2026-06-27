#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"

echo "==> Building plugin"

./infra/extract-binaries.sh
./cli/decky plugin build

if [[ -n "$VERSION" ]]; then
    mv ./out/warp-deck.zip "./out/warp-deck-v${VERSION}.zip"
    echo "==> Renamed to warp-deck-v${VERSION}.zip"
fi
