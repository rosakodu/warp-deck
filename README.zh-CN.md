# WARP Deck

[English](README.md) | [Русский](README.ru.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [العربية](README.ar.md) | [فارسی](README.fa.md) | [Türkçe](README.tr.md)

一款适用于 Steam Deck 的 Decky Loader 插件，允许您一键轻松连接基于 AmneziaWG（抗 DPI 干扰的 WireGuard 协议）的 Cloudflare WARP，或导入您自定义的 AmneziaWG/WireGuard 配置文件。

> **注意：** 此插件要求您的系统上安装官方 [Amnezia VPN 客户端](https://github.com/amnezia-vpn/amnezia-client) 才能正常工作。

![Screenshot](assets/screenshot.jpeg)

## 📋 功能特点

- **一键 Cloudflare WARP**：直接在用户界面中生成和更新可正常工作的 WARP VPN 配置，无需手动设置。
- **绕过 DPI (AmneziaWG)**：内置支持 AmneziaWG 协议头和垃圾数据包，以绕过 ISP 屏蔽。
- **导入自定义配置**：导入并管理您自己的 `.conf` 文件（AmneziaWG 或 WireGuard）。
- **网络诊断**：内置连接测试，用于验证与 1.1.1.1、Google 和 RuTracker 的连接。
- **多配置文件**：保存并在不同的配置文件之间切换。
- **无需额外依赖**：所有必需的 AmneziaWG 二进制文件都已打包在插件中。

> [!IMPORTANT]
> 内置的 Cloudflare WARP 生成器会自动配置所有绕过参数（包括 `I1` QUIC 签名）。但是，如果您导入**自定义 VPN 配置文件**，建议使用官方的 [Amnezia VPN 客户端](https://github.com/amnezia-vpn/amnezia-client) 导出为**“AmneziaWG 原生格式”**（包含 `Jc`、`Jmin`、`Jmax` 等字段的类 WireGuard `.conf` 文件），以确保绕过网络封锁。

## 📥 安装

1. 从 [Releases](https://github.com/rosakodu/warp-deck/releases) 下载最新版本（`warp-deck.zip`）。
2. 将 ZIP 文件复制到您的 Steam Deck。
3. 在 Steam 设置中启用**开发者模式**，然后在 Decky Loader 设置中启用**开发者模式**，并选择“从文件安装插件”（或上传/拖放 ZIP）。

## 🚀 使用方法

### 1. 生成 Cloudflare WARP（推荐）
安装后，打开插件菜单并点击**“更新”**（首次启动时它会自动创建 `warp-deck` 配置文件）。它将查询 Warp 密钥生成器，创建一个包含 AmneziaWG 混淆参数的配置文件，然后您可以立即开启它。

### 2. 导入自定义配置
点击**“导入配置”**并从您的设备中选择任何 `.conf` 文件（例如，从 `/home/deck/Downloads/`）。

## ⚙️ 工作原理
插件将导入的配置文件存储在 `~/.local/share/warp-deck/configs` 并在 `/etc/amnezia/amneziawg/` 中创建符号链接。VPN 连接将使用捆绑的、经过修改的 `awg-quick` 脚本启动。

## ⚖️ 许可与鸣谢
基于 mrwaip 的原始 [vpn-deck](https://github.com/mrwaip/vpn-deck) 插件。
此复刻版本基于 BSD-3-Clause 许可证获得许可。
