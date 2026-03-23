# Geliştirme Rehberi

## Geliştirme Ortamı

### Gereksinimler

- Arch Linux (native, VM veya WSL2)
- `git`, `base-devel`

### Hızlı Kurulum

```bash
git clone https://github.com/texas1881/lumiere-os.git
cd lumiere-os
./scripts/setup-dev.sh
```

Bu script şunları kurar: `archiso`, `qemu-full`, `ovmf`, `shellcheck`

## Proje Yapısı

```
lumiere-os/
├── iso/              # archiso ISO builder
│   ├── airootfs/     # Dosya sistemi overlay
│   ├── build.sh      # Build script
│   ├── packages.x86_64  # Paket listesi
│   └── profiledef.sh
├── desktop/          # Masaüstü konfigürasyonları
│   ├── hyprland/     # Compositor ayarları
│   ├── waybar/       # Panel
│   ├── rofi/         # Launcher
│   ├── mako/         # Bildirimler
│   ├── scripts/      # Yardımcı scriptler
│   └── swaylock/     # Ekran kilidi
├── compositor/       # Lumière Compositor (C + wlroots)
├── lumiere-term/     # Lumière Terminal (Rust + wgpu)
├── apps/             # Özel uygulamalar
│   ├── lumiere-welcome/
│   ├── lumiere-settings/
│   ├── lumiere-monitor/
│   ├── lumiere-store/
│   ├── lumiere-snapshot/
│   ├── lumiere-update/
│   ├── lumiere-cheatsheet/
│   └── lumiere-pkg/
├── theme/            # Tema dosyaları
├── branding/         # Logo, wallpaper, boot splash
├── installer/        # Kurulum sihirbazı
├── scripts/          # Build & yardımcı scriptler
└── docs/             # Dokümantasyon
```

## Build Komutları

```bash
make help          # Tüm komutları göster
make build-iso     # ISO oluştur (sudo gerektirir)
make test-vm       # QEMU'da test et
make lint          # shellcheck çalıştır
make clean         # Build dosyalarını temizle
make release       # Release build (etiketli)
```

## Geliştirme İş Akışı

1. Fork + clone
2. Feature branch oluştur: `git checkout -b feature/yeni-ozellik`
3. Değişiklikleri yap
4. `make lint` ile kontrol et
5. Commit: `git commit -m "feat: yeni özellik açıklaması"`
6. Push + PR aç

## Commit Mesajı Formatı

```
<type>: <açıklama>

Tipler:
  feat     → Yeni özellik
  fix      → Hata düzeltme
  docs     → Dokümantasyon
  style    → Stil/format değişikliği
  refactor → Yeniden yapılandırma
  test     → Test ekleme
  chore    → Bakım işleri
```

## Test

### ISO Build Test

```bash
sudo make build-iso
make test-vm
```

### Shellcheck

```bash
make lint
# veya tek dosya:
shellcheck scripts/lumiere-hw-detect.sh
```

---

<p align="center"><a href="Home.md">← Wiki Ana Sayfa</a></p>
