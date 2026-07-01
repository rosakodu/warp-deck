# WARP Deck

[English](README.md) | [Русский](README.ru.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [العربية](README.ar.md) | [فارسی](README.fa.md) | [Türkçe](README.tr.md)

إضافة Decky Loader لجهاز Steam Deck تتيح لك الاتصال بسهولة بشبكة Cloudflare WARP عبر AmneziaWG (بروتوكول WireGuard المقاوم لحجب مزود الخدمة) بنقرة واحدة، أو استيراد إعدادات AmneziaWG/WireGuard المخصصة.

> **ملاحظة:** تتطلب هذه الإضافة تثبيت [تطبيق Amnezia VPN](https://github.com/amnezia-vpn/amnezia-client) الرسمي على نظامك لتعمل بشكل صحيح.

![Screenshot](assets/screenshot.jpeg)

## 📋 المميزات

- **Cloudflare WARP بنقرة واحدة**: إنشاء وتحديث ملف إعداد WARP VPN يعمل بالكامل مباشرة من واجهة المستخدم بدون إعداد يدوي.
- **تخطي الحجب (AmneziaWG)**: دعم مدمج لترويسات AmneziaWG وحزم البيانات الوهمية لتخطي حظر مزود الخدمة (DPI).
- **استيراد ملفات الإعداد**: استيراد وإدارة ملفات `.conf` الخاصة بك (AmneziaWG أو WireGuard).
- **تشخيص الاتصال**: فحص اتصال مدمج للتأكد من الوصول إلى 1.1.1.1، Google، و RuTracker.
- **ملفات شخصية متعددة**: حفظ التبديل بين ملفات إعداد مختلفة.
- **لا يتطلب اعتمادات خارجية**: جميع ملفات AmneziaWG التنفيذية مدمجة مسبقاً في الإضافة.

> [!IMPORTANT]
> يقوم مولد Cloudflare WARP المدمج تلقائيًا بضبط كافة إعدادات التخطي (بما في ذلك توقيع `I1` QUIC). ومع ذلك، إذا قمت باستيراد **إعدادات VPN مخصصة**، يُنصح بتصديرها من التطبيق الرسمي [Amnezia VPN](https://github.com/amnezia-vpn/amnezia-client) **"بتنسيق AmneziaWG الأصلي"** (ملف `.conf` يحتوي على حقول `Jc`، `Jmin`، `Jmax`) لضمان تخطي الحجب بنجاح.

## 📥 التثبيت

1. قم بتنزيل أحدث إصدار (`warp-deck.zip`) من [الإصدارات](https://github.com/rosakodu/warp-deck/releases).
2. انسخ ملف ZIP إلى جهاز Steam Deck الخاص بك.
3. فعّل **وضع المطور (Developer Mode)** في إعدادات Steam، ثم في إعدادات Decky Loader فعّل **وضع المطور** واختر "Install plugin from file" (تثبيت إضافة من ملف) لاختيار ملف ZIP.

## 🚀 كيفية الاستخدام

### 1. إنشاء Cloudflare WARP (موصى به)
بعد التثبيت، افتح قائمة الإضافة واضغط على **"تحديث (Update)"** (أو سيتم إنشاء ملف `warp-deck` تلقائياً عند التشغيل الأول). سيقوم هذا بجلب مفاتيح Warp وإنشاء ملف إعداد يحتوي على معلمات تخويف AmneziaWG، ويمكنك تشغيله فوراً.

### 2. استيراد إعدادات مخصصة
اضغط على **"استيراد إعداد (Import config)"** واختر أي ملف `.conf` من جهازك (مثلاً من مجلد `/home/deck/Downloads/`).

## ⚙️ كيف يعمل
تقوم الإضافة بحفظ الإعدادات المستوردة في `~/.local/share/warp-deck/configs` وتُنشئ روابط رمزية في `/etc/amnezia/amneziawg/`. يتم تشغيل الاتصال باستخدام سكريبت `awg-quick` معدل ومدمج.

## ⚖️ الترخيص والشكر
مبني على إضافة [vpn-deck](https://github.com/mrwaip/vpn-deck) الأصلية بواسطة mrwaip.
هذه النسخة المعدلة مرخصة بموجب ترخيص BSD-3-Clause.
