<p align="center">
  <h1 align="center">✦ Lumière OS</h1>
  <p align="center"><em>Fransızca'da "ışık" — Hızlı, şeffaf, aydınlık bir işletim sistemi deneyimi.</em></p>
</p>

---

## Vizyon

Lumière OS, Linux çekirdeği üzerine inşa edilmiş, kendi marka kimliği, masaüstü deneyimi, terminal hissi ve araç setine sahip modern bir işletim sistemidir. Hedef sıradan bir remaster değil; **özgün bir kullanıcı deneyimi** sunmaktır.

## Teknoloji Stack'i

| Katman | Teknoloji |
|---|---|
| **Taban** | Arch Linux (Rolling Release) |
| **Kernel** | Linux (mainline stable) |
| **Init** | systemd |
| **Compositor** | Lumière Compositor (wlroots) / Hyprland |
| **Panel** | Waybar |
| **Ses** | PipeWire + WirePlumber |
| **Ağ** | NetworkManager |
| **Terminal** | Lumière Terminal (Rust + wgpu) |
| **Bootloader** | systemd-boot |
| **Login** | greetd + tuigreet |
| **Paket** | pacman + flatpak + lumiere-pkg |
| **App Store** | Lumière Store (Flatpak GUI) |
| **Güncelleme** | OTA Update (pacman + flatpak) |
| **Snapshot** | Btrfs snapshot/rollback |

## Tasarım Prensipleri

- **Minimalist ama güçlü** — gereksiz şey yok, her şey amacına hizmet eder
- **Keyboard-first** — her işlem klavyeyle yapılabilir
- **Hızlı** — boot < 5sn, idle RAM < 500MB
- **Modüler** — her bileşen bağımsız, değiştirilebilir
- **Güzel** — koyu tema, altın aksanlar, modern tipografi

## Proje Yapısı

```
lumiere-os/
├── iso/              # archiso tabanlı ISO builder
├── compositor/       # Lumière Compositor (C + wlroots)
├── lumiere-term/     # Lumière Terminal (Rust + wgpu)
├── desktop/          # Masaüstü konfigürasyonları (Hyprland, Waybar, Rofi...)
├── apps/             # Lumière özel uygulamalar
│   ├── lumiere-welcome/    # Hoş geldin uygulaması
│   ├── lumiere-settings/   # Ayarlar
│   ├── lumiere-monitor/    # Sistem monitörü
│   ├── lumiere-store/      # App Store
│   ├── lumiere-snapshot/   # Snapshot yöneticisi
│   ├── lumiere-update/     # OTA güncelleme
│   ├── lumiere-cheatsheet/ # Kısayol rehberi
│   └── lumiere-pkg/        # Paket yönetimi CLI
├── theme/            # Tema dosyaları (GTK, renkler, ikonlar, imleçler)
├── branding/         # Logo, wallpaper, boot splash
├── installer/        # Kurulum sihirbazı
├── scripts/          # Yardımcı scriptler
└── docs/             # Dokümantasyon
```

## Hızlı Başlangıç

### Gereksinimler
- Arch Linux ortamı (native, VM veya WSL2)
- `archiso` paketi
- `git`

### ISO Build
```bash
git clone https://github.com/texas1881/lumiere-os.git
cd lumiere-os
sudo make build-iso
```

### VM'de Test
```bash
make test-vm
```

## Dokümantasyon

- [Kullanıcı Rehberi](docs/USER_GUIDE.md)
- [Klavye Kısayolları](docs/SHORTCUTS.md)
- [SSS / Sorun Giderme](docs/FAQ.md)
- [Özelleştirme](docs/CUSTOMIZATION.md)
- [Mimari](docs/ARCHITECTURE.md)
- [Katkı Rehberi](CONTRIBUTING.md)
- [Değişiklik Günlüğü](docs/CHANGELOG.md)

## Topluluk

- [GitHub Discussions](https://github.com/texas1881/lumiere-os/discussions) — Soru & tartışma
- [GitHub Issues](https://github.com/texas1881/lumiere-os/issues) — Hata bildirimi
- [Wiki](https://github.com/texas1881/lumiere-os/wiki) — Kapsamlı dokümantasyon
- [Davranış Kuralları](CODE_OF_CONDUCT.md)
- [Güvenlik Politikası](SECURITY.md)

## Yol Haritası

- [x] v0.0 — Proje yapısı ve temel konfigürasyonlar
- [x] v0.1 "İlk Işık" — Bootable ISO, çalışan masaüstü, temel araçlar
- [x] v0.2 "Parıltı" — İkon seti, tema switcher, ayarlar, monitör, installer
- [x] v0.3 "Aydınlanma" — Kendi compositor, terminal, app store, OTA, snapshot
- [x] v1.0 "Tam Işık" — Stabil sürüm, donanım desteği, dokümantasyon, CI/CD

## Lisans

Bu proje [GPL-3.0](LICENSE) lisansı altında dağıtılmaktadır.

---

<p align="center">
  <strong>Lumière OS</strong> — Işığı takip et. ✦
</p>
