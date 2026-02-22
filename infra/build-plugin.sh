#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"

echo "==> Building plugin"

./infra/extract-binaries.sh
./cli/decky plugin build

if [[ -n "$VERSION" ]]; then
    mv ./out/vpn-deck.zip "./out/vpn-deck-v${VERSION}.zip"
    echo "==> Renamed to vpn-deck-v${VERSION}.zip"
fi
