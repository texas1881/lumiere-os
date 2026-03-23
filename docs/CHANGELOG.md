# Lumière OS — Değişiklik Günlüğü

Tüm önemli değişiklikler bu dosyada belgelenir.

## [1.0.0] — 2026-03-23 — "Tam Işık" ☀️

### Eklenen
- **Lumière Cheatsheet** — GTK4/Adwaita klavye kısayolları overlay'i (Super+/ ile açılır)
- **MIME Associations** — Varsayılan uygulama ilişkileri (Firefox, Thunar, imv, mpv)
- **Hardware Detection** — İlk boot donanım algılama scripti (NVIDIA, HiDPI, CUPS, USB, Bluetooth)
- **User Guide** — Kapsamlı kullanıcı rehberi (kurulum, masaüstü, paket yönetimi, sorun giderme)
- **Shortcuts Reference** — Tüm klavye kısayolları referans tablosu
- **FAQ** — Sık sorulan sorular ve sorun giderme rehberi
- **Customization Guide** — Tema, renk, font, panel özelleştirme rehberi
- **Wiki** — 4 sayfalı wiki (Home, Getting-Started, Troubleshooting, Development)
- **GitHub Issue Templates** — Bug report ve feature request şablonları
- **Code of Conduct** — Contributor Covenant v2.1
- **Security Policy** — Güvenlik açığı bildirme politikası
- **CI/CD Pipeline** — GitHub Actions ile otomatik ISO build, release, lint

### Değişen
- `packages.x86_64` genişletildi: NVIDIA, CUPS, v4l2, udisks2, power-profiles-daemon, Qt Wayland, imv, mpv
- Hyprland konfigürasyonuna `Super+/` kısayolu eklendi
- README.md tamamen güncellendi (v1.0 stack, dokümantasyon, topluluk)
- ARCHITECTURE.md CI/CD katmanı eklendi
- Makefile'a `release` hedefi eklendi
- ISO build script v1.0 bileşenlerini deploy eder

## [0.3.0] — 2026-03-23 — "Aydınlanma" 🌅

### Eklenen
- **Lumière Compositor** — wlroots tabanlı C Wayland compositor (XDG shell, tiling/floating, IPC, INI config)
- **Lumière Terminal** — Rust + wgpu GPU-hızlandırmalı terminal emülatörü (VTE, scrollback, WGSL shader'lar)
- **Lumière App Store** — GTK4/Adwaita flatpak uygulama mağazası (arama, kategori, install/uninstall, toplu güncelleme)
- **OTA Güncelleme** — pacman + flatpak birleşik güncelleme CLI + systemd timer + Waybar modülü
- **Snapshot/Rollback** — btrfs snapshot CLI (create/list/delete/rollback/diff) + pacman hook + GTK4 GUI yöneticisi

### Değişen
- ARCHITECTURE.md güncellendi (compositor katmanı, yeni bileşenler)
- ISO paket listesi güncellendi (wlroots, flatpak, rust, meson)

## [0.2.0] — 2026-03-23 — "Parıltı" ✨

### Eklenen
- **Lumière Icons** — 28 SVG özel ikon seti (apps, places, actions, status, devices)
- **Lumiere-Cursors** — altın/amber vurgulu koyu imleç teması (10 imleç + build script)
- **lumiere-settings** — GTK4/Adwaita ayarlar uygulaması (Görünüm, Masaüstü, Giriş, Hakkında)
- **lumiere-monitor** — GTK4/Adwaita sistem monitörü (CPU/RAM/Disk göstergeleri, işlem yöneticisi, ağ trafiği)
- **Tema Switcher** — koyu/açık tema geçiş sistemi (zamanlayıcı + manual toggle)
- **lumiere-light.json** — açık tema renk paleti
- **gtk-light.css** — açık mod GTK4 stil dosyası
- **Gelişmiş Installer** — GTK4/Adwaita grafik kurulum sihirbazı (disk bölümleme GUI, 6 adımlı wizard)

### Değişen
- Hyprland keybinding'leri: Super+T = tema switcher, Super+I = ayarlar, Super+M = monitör
- ISO paket listesi güncellendi (python-gobject, xcursor-themes, parted)
- ISO build script yeni bileşenleri deploy eder

## [0.1.0] — 2026-03-23 — "İlk Işık" 💡

### Eklenen
- **lumiere-welcome** — GTK4/Adwaita hoş geldin uygulaması (5 sayfalı wizard, autostart)
- **Plymouth boot splash** — animasyonlu boot teması (logo pulse, kayan noktalar)
- **Guided installer** — TUI tabanlı kurulum (btrfs alt birimler, UEFI, systemd-boot)
- **Power menu** — Rofi tabanlı güç yönetimi (kapat, yeniden başlat, kilitle, uyku)
- **Wallpaper picker** — Rofi ile duvar kağıdı seçimi + swww animasyonlu geçiş
- **Screenshot tool** — alan/tam ekran/pencere modları, clipboard, bildirim
- **OSD bildirimleri** — ses/parlaklık değişimlerinde görsel geri bildirim
- **Live environment** — greetd ile otomatik login, live kullanıcı
- **pacman.conf** — renkli çıktı, paralel indirme, multilib
- **CONTRIBUTING.md** — katkı rehberi
- ISO build pipeline güncellendi (tüm v0.1 bileşenlerini deploy eder)

### Değişen
- Hyprland keybinding'leri OSD scriptlerine güncellendi
- Super+W = duvar kağıdı seçici, Super+X = güç menüsü eklendi

## [0.0.1] — 2026-03-23

### Eklenen
- Proje yapısı oluşturuldu
- Lumière Dark renk paleti (`lumiere-dark.json`)
- Hyprland compositor konfigürasyonu
- Waybar panel konfigürasyonu ve CSS teması
- Rofi uygulama başlatıcı teması
- Kitty terminal konfigürasyonu
- zsh + Starship prompt konfigürasyonu
- GTK 3.0/4.0 tema dosyaları
- Mako bildirim konfigürasyonu
- swaylock ekran kilidi konfigürasyonu
- `lumiere-pkg` paket yönetim CLI aracı
- archiso ISO build altyapısı
- Fastfetch branding konfigürasyonu
- Makefile build sistemi
- Mimari ve yol haritası dokümanları
