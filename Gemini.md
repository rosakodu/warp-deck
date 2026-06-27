# Gemini.md (Antigravity Developer Guide)

This file provides context and developer guidelines for Gemini (Antigravity) and other AI assistants working in this repository.

## 📋 Project Overview
**warp-deck** is a Decky Loader plugin for Steam Deck that allows users to manage AmneziaWG/WireGuard VPN profiles directly from Gaming Mode. It also features a one-click Cloudflare WARP configuration generator.

- **Frontend**: TypeScript & React (`src/index.tsx`). Interacts with Decky UI components.
- **Backend**: Python 3 (`main.py` + `py_modules/vpn_deck/`).
- **Communication**: Decky's RPC system (`@_rpc` decorator in Python, `serverAPI.call(...)` in React).

---

## 🛠️ Architecture & Core Components

| Path | Purpose |
|------|---------|
| `src/index.tsx` | Main UI. Contains layout, localizations, and RPC bridges. |
| `main.py` | Main RPC entrypoint, client language detection, and WARP config generation logic. |
| `py_modules/vpn_deck/config_manager.py` | Manages importing/deleting configs in `~/.local/share/warp-deck/configs` and symlinking to `/etc/amnezia/amneziawg/`. |
| `py_modules/vpn_deck/service_manager.py` | Handles interface lifecycle (`awg-quick up/down`) and force-delete fallback via `ip link delete`. |
| `py_modules/vpn_deck/diagnostics.py` | Threaded connection check probing `1.1.1.1` (ping), `google.com` (http), and `rutracker.org` (http). |
| `py_modules/vpn_deck/binary_manager.py` | Verifies execution permissions and resolves paths for bundled binaries in `./bin/`. |

---

## ⚡ AmneziaWG & Cloudflare WARP Compatibility (Critical)

To successfully bypass DPI in Russia while maintaining compatibility with Cloudflare WARP endpoints:
1. **Header parameters (`H1`, `H2`, `H3`, `H4`)**: MUST be left at standard values (`1, 2, 3, 4`). Cloudflare Edge servers run standard WireGuard and reject custom packet headers.
2. **Junk parameters (`Jc`, `Jmin`, `Jmax`)**: Used for junk packet obfuscation (`Jc = 4`, `Jmin = 40`, `Jmax = 70`).
3. **Prefix parameters (`S1`, `S2`, `S3`, `S4`)**: MUST be disabled (`0`) as they break the WARP tunnel.
4. **QUIC Handshake Masking (`I1`)**: Required to bypass SNI/handshake blocking. We use a static QUIC Client Hello signature (`I1 = <b 0xce00... >`) to disguise the WireGuard handshake.
5. **CLI Utility (`bin/awg`)**: The bundled `awg` binary must support CPS parameters (`I1`-`I5`). We compile and bundle `amneziawg-tools v1.0.20260618-2` to support this.

---

## 💻 Build & Test Commands

* **Build Frontend**: `npm run build`
* **Package Plugin**: `./cli/decky plugin build` (generates plugin archive at `out/warp-deck.zip`).
* **Run Unit Tests**: `PYTHONPATH=py_modules python3 test_unit.py && PYTHONPATH=py_modules python3 test_simple.py`

---

## 🔍 Debugging & Logs
- Plugin logs (Python backend): `/home/deck/homebrew/logs/warp-deck.log`
- AmneziaWG interface transition logs: `/home/deck/homebrew/logs/warp-deck/awg-quick.log`
- Imported configurations: `/home/deck/.local/share/warp-deck/configs/`
- Active symlinks: `/etc/amnezia/amneziawg/`
