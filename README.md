# WARP Deck

[Русский](README.ru.md)

A Decky Loader plugin for Steam Deck that allows you to easily connect to Cloudflare WARP via AmneziaWG (DPI-resistant WireGuard protocol) in one click, or import your custom AmneziaWG/WireGuard configurations.

> **Note:** This plugin requires the official [Amnezia VPN Client](https://github.com/amnezia-vpn/amnezia-client) to be installed on your system to function properly.
![Screenshot](assets/screenshot.jpeg)

## 📋 Features

- **One-click Cloudflare WARP**: Generate and update a fully working WARP VPN config directly from the UI without manual setup.
- **DPI Bypass (AmneziaWG)**: Built-in support for AmneziaWG protocol headers and junk packets to bypass ISP blocks.
- **Custom Config Import**: Import and manage your own `.conf` files (AmneziaWG or WireGuard).
- **Diagnostics Check**: Built-in connectivity test verifying connection to 1.1.1.1, Google, and RuTracker.
- **Multiple Profiles**: Store and switch between different configuration profiles.
- **No Dependencies Needed**: All necessary AmneziaWG binaries are pre-packaged within the plugin.

> [!IMPORTANT]
> The built-in Cloudflare WARP generator automatically configures all bypass parameters (including the `I1` QUIC signature). However, if you import **custom VPN profiles**, they should be exported from the official [Amnezia VPN Client](https://github.com/amnezia-vpn/amnezia-client) in **"AmneziaWG native format"** (a WireGuard-like `.conf` file containing `Jc`, `Jmin`, `Jmax` fields) to bypass network blocks.

## 📥 Installation

1. Download the latest release (`warp-deck.zip`) from [Releases](https://github.com/rosakodu/warp-deck/releases).
2. Copy the ZIP file to your Steam Deck.
3. Enable **Developer Mode** in Steam Settings, then in Decky Loader settings, enable **Developer mode** and choose "Install plugin from file" (or upload/drag-and-drop the ZIP).

## 🚀 How to Use

### 1. Generating Cloudflare WARP (Recommended)
After installation, open the plugin menu and click **"Update"** (or it will create the `warp-deck` profile automatically on first launch). This will query the Warp keys generators, create a working profile with AmneziaWG obfuscation parameters, and you can immediately turn it on.

### 2. Importing Custom Configs
Click **"Import config"** and select any `.conf` file from your device (e.g., from `/home/deck/Downloads/`).

## ⚙️ How it Works
The plugin stores imported configurations in `~/.local/share/warp-deck/configs` and creates symlinks in `/etc/amnezia/amneziawg/`. VPN connections are brought up using a bundled, modified `awg-quick` script.

## ⚖️ License & Credits
Based on the original [vpn-deck](https://github.com/mrwaip/vpn-deck) plugin by mrwaip.
This fork is licensed under the BSD-3-Clause License.
