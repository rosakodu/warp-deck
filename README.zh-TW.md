# WARP Deck

[English](README.md) | [Русский](README.ru.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [العربية](README.ar.md) | [فارسی](README.fa.md) | [Türkçe](README.tr.md)

一款適用於 Steam Deck 的 Decky Loader 外掛程式，可讓您一鍵輕鬆連線至基於 AmneziaWG（抗 DPI 封鎖的 WireGuard 協定）的 Cloudflare WARP，或匯入自訂的 AmneziaWG/WireGuard 設定檔。

> **注意：** 此外掛程式需要您的系統上安裝官方 [Amnezia VPN 客戶端](https://github.com/amnezia-vpn/amnezia-client) 才能正常運作。

![Screenshot](assets/screenshot.jpeg)

## 📋 功能特色

- **一鍵 Cloudflare WARP**：直接在使用者介面中產生和更新可正常運作的 WARP VPN 設定，無需手動設定。
- **繞過 DPI (AmneziaWG)**：內建支援 AmneziaWG 協定標頭和垃圾封包，以繞過 ISP 封鎖。
- **匯入自訂設定**：匯入並管理您自己的 `.conf` 檔案（AmneziaWG 或 WireGuard）。
- **網路診斷**：內建連線測試，用於驗證與 1.1.1.1、Google 和 RuTracker 的連線。
- **多設定檔**：儲存並在不同的設定檔之間切換。
- **無需額外依賴**：所有必要的 AmneziaWG 二進位檔案皆已打包在外掛程式中。

> [!IMPORTANT]
> 內建的 Cloudflare WARP 產生器會自動設定所有繞過參數（包括 `I1` QUIC 簽章）。但是，如果您匯入**自訂 VPN 設定檔**，建議使用官方的 [Amnezia VPN 客戶端](https://github.com/amnezia-vpn/amnezia-client) 匯出為**「AmneziaWG 原生格式」**（包含 `Jc`、`Jmin`、`Jmax` 等欄位的類 WireGuard `.conf` 檔案），以確保繞過網路封鎖。

## 📥 安裝

1. 從 [Releases](https://github.com/rosakodu/warp-deck/releases) 下載最新版本（`warp-deck.zip`）。
2. 將 ZIP 檔案複製到您的 Steam Deck。
3. 在 Steam 設定中啟用**開發者模式**，然後在 Decky Loader 設定中啟用**開發者模式**，並選擇「從檔案安裝外掛程式」（或上傳/拖曳 ZIP 檔案）。

## 🚀 使用方法

### 1. 產生 Cloudflare WARP（推薦）
安裝後，打開外掛程式選單並點擊**「更新」**（首次啟動時它會自動建立 `warp-deck` 設定檔）。它將查詢 Warp 金鑰產生器，建立一個包含 AmneziaWG 混淆參數的設定檔，然後您可以立即開啟它。

### 2. 匯入自訂設定
點擊**「匯入配置」**並從您的裝置中選擇任何 `.conf` 檔案（例如，從 `/home/deck/Downloads/`）。

## ⚙️ 運作原理
外掛程式將匯入的設定檔儲存在 `~/.local/share/warp-deck/configs` 並在 `/etc/amnezia/amneziawg/` 中建立符號連結。VPN 連線將使用內附的、經過修改的 `awg-quick` 指令碼啟動。

## ⚖️ 授權與鳴謝
基於 mrwaip 的原始 [vpn-deck](https://github.com/mrwaip/vpn-deck) 外掛程式。
此分支版本基於 BSD-3-Clause 授權條款。
