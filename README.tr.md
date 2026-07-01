# WARP Deck

[English](README.md) | [Русский](README.ru.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [العربية](README.ar.md) | [فارسی](README.fa.md) | [Türkçe](README.tr.md)

Steam Deck için bir Decky Loader eklentisi. AmneziaWG (DPI engellemelerine karşı dayanıklı WireGuard protokolü) aracılığıyla Cloudflare WARP'a tek tıklamayla kolayca bağlanmanızı veya kendi AmneziaWG/WireGuard yapılandırmalarınızı içe aktarmanızı sağlar.

> **Not:** Bu eklentinin düzgün çalışması için resmi [Amnezia VPN İstemcisinin](https://github.com/amnezia-vpn/amnezia-client) sisteminizde kurulu olması gerekir.

![Screenshot](assets/screenshot.jpeg)

## 📋 Özellikler

- **Tek Tıkla Cloudflare WARP**: Tamamen çalışan bir WARP VPN yapılandırmasını manuel ayara gerek kalmadan doğrudan arayüzden oluşturun ve güncelleyin.
- **DPI Atlatma (AmneziaWG)**: ISS (İnternet Servis Sağlayıcı) engellemelerini aşmak için AmneziaWG protokol başlıkları ve çöp paketleri (junk packets) desteği.
- **Özel Yapılandırma İçe Aktarma**: Kendi `.conf` dosyalarınızı (AmneziaWG veya standart WireGuard) içe aktarın ve yönetin.
- **Bağlantı Tanılama**: 1.1.1.1, Google ve RuTracker'a erişimi doğrulayan yerleşik bağlantı testi.
- **Çoklu Profiller**: Farklı VPN profillerini kaydedin ve aralarında kolayca geçiş yapın.
- **Ekstra Bağımlılık Gerekmez**: Tüm gerekli AmneziaWG bileşenleri eklenti paketine dahil edilmiştir.

> [!IMPORTANT]
> Yerleşik Cloudflare WARP oluşturucu, DPI atlatma parametrelerini ( `I1` QUIC imzası dahil) otomatik olarak ayarlar. Ancak, **özel VPN profilleri** içe aktarıyorsanız, engellemeleri aşabilmek için bunların resmi [Amnezia VPN](https://github.com/amnezia-vpn/amnezia-client) uygulamasından **"AmneziaWG native format"** olarak (`Jc`, `Jmin`, `Jmax` gibi alanları içeren bir `.conf` dosyası) dışa aktarılması önerilir.

## 📥 Kurulum

1. En son sürümü (`warp-deck.zip`) [Releases](https://github.com/rosakodu/warp-deck/releases) sayfasından indirin.
2. ZIP dosyasını Steam Deck'inize kopyalayın.
3. Steam Ayarlarından **Geliştirici Modunu (Developer Mode)** etkinleştirin, ardından Decky Loader ayarlarında **Geliştirici modunu** açın ve "Dosyadan eklenti kur" seçeneğini seçin (veya ZIP dosyasını yükleyin/sürükleyip bırakın).

## 🚀 Nasıl Kullanılır

### 1. Cloudflare WARP Oluşturma (Önerilen)
Kurulumdan sonra eklenti menüsünü açın ve **"Güncelle (Update)"** düğmesine tıklayın (ilk açılışta `warp-deck` profilini otomatik oluşturacaktır). Bu işlem Warp anahtarlarını çekecek, AmneziaWG gizleme parametrelerini içeren bir yapılandırma oluşturacak ve hemen bağlanabileceksiniz.

### 2. Özel Yapılandırmaları İçe Aktarma
**"Yapılandırmayı İçe Aktar (Import config)"** düğmesine tıklayın ve cihazınızdan herhangi bir `.conf` dosyasını seçin (örneğin `/home/deck/Downloads/` klasöründen).

## ⚙️ Nasıl Çalışır
Eklenti, içe aktarılan yapılandırmaları `~/.local/share/warp-deck/configs` dizininde depolar ve `/etc/amnezia/amneziawg/` altında sembolik bağlantılar (symlink) oluşturur. VPN bağlantıları, eklenti içindeki değiştirilmiş `awg-quick` betiği ile başlatılır.

## ⚖️ Lisans & Teşekkür
mrwaip tarafından oluşturulan orijinal [vpn-deck](https://github.com/mrwaip/vpn-deck) eklentisine dayanmaktadır.
Bu çatal sürüm (fork) BSD-3-Clause lisansı altındadır.
