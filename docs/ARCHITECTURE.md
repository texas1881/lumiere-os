# Lumière OS — Mimari Dokümanı

## Genel Bakış

Lumière OS, Arch Linux taban üzerine inşa edilmiş, Wayland-native bir masaüstü işletim sistemidir.

## Katman Mimarisi

```
┌─────────────────────────────────────────────────────┐
│                   KULLANICI KATMANI                  │
│  lumiere-store · lumiere-settings · lumiere-monitor  │
│  lumiere-snapshot · lumiere-update · lumiere-welcome  │
│  lumiere-cheatsheet                                  │
├─────────────────────────────────────────────────────┤
│                  MASAÜSTÜ KATMANI                    │
│  Waybar Panel · Rofi Launcher · Mako Notifications   │
│  Theme Switcher · OSD Scripts · MIME Defaults         │
├─────────────────────────────────────────────────────┤
│                 GRAFİK KATMANI                       │
│  Wayland · Lumière Compositor (wlroots) · XWayland   │
│  Lumière Terminal (wgpu) · GTK4 / Adwaita            │
├─────────────────────────────────────────────────────┤
│                 SİSTEM SERVİSLERİ                    │
│  systemd · NetworkManager · PipeWire · greetd        │
│  Btrfs Snapshots · OTA Update Timer · CUPS           │
│  power-profiles-daemon · udisks2                     │
├─────────────────────────────────────────────────────┤
│                    TEMEL SİSTEM                      │
│  Linux Kernel · pacman · flatpak · GNU Coreutils     │
├─────────────────────────────────────────────────────┤
│                     DONANIM                          │
│  x86_64 · UEFI · GPU (Mesa/NVIDIA/wgpu)             │
│  Peripherals · CUPS · Bluetooth · USB · Webcam       │
├─────────────────────────────────────────────────────┤
│                    CI/CD                             │
│  GitHub Actions · ISO Build · Release · Lint         │
└─────────────────────────────────────────────────────┘
```

## Bileşen Tablosu

| Bileşen | Seçim | Durum |
|---|---|---|
| Kernel | Linux (mainline) | Hazır |
| Init | systemd | Hazır |
| Compositor | Lumière Compositor (wlroots) | v0.3 |
| Compositor (eski) | Hyprland (Wayland) | v0.1-v0.2 |
| Terminal | Lumière Terminal (Rust+wgpu) | v0.3 |
| Terminal (eski) | Kitty + zsh + Starship | v0.1-v0.2 |
| Panel | Waybar | Hazır |
| Launcher | Rofi (wayland) | Hazır |
| Bildirim | Mako | Hazır |
| Ses | PipeWire + WirePlumber | Hazır |
| Ağ | NetworkManager | Hazır |
| Login | greetd + tuigreet | Hazır |
| Boot | systemd-boot | Hazır |
| Paket | pacman + flatpak + lumiere-pkg | Özel |
| Tema | GTK4 + Lumière Dark/Light | Özel |
| İkonlar | Lumière Icons (28 SVG) | v0.2 |
| İmleçler | Lumiere-Cursors | v0.2 |
| App Store | lumiere-store (flatpak GUI) | v0.3 |
| Güncelleme | lumiere-update (OTA) | v0.3 |
| Snapshot | lumiere-snapshot (btrfs) | v0.3 |
| Ayarlar | lumiere-settings (GTK4) | v0.2 |
| Monitör | lumiere-monitor (GTK4) | v0.2 |
| Installer | lumiere-installer (GTK4) | v0.2 |
| Cheatsheet | lumiere-cheatsheet (GTK4) | v1.0 |
| HW Detect | lumiere-hw-detect (bash) | v1.0 |
| Yazıcı | CUPS + system-config-printer | v1.0 |
| Güç | power-profiles-daemon | v1.0 |
| USB | udisks2 + udiskie | v1.0 |
| CI/CD | GitHub Actions (build/release/lint) | v1.0 |

## Konfigürasyon Akışı

```
theme/colors/lumiere-dark.json  (merkezi renk paleti)
        │
        ├── compositor/         → Compositor renkleri
        ├── lumiere-term/       → Terminal renkleri
        ├── desktop/waybar/     → Panel renkleri
        ├── desktop/rofi/       → Launcher renkleri
        ├── terminal/kitty/     → Kitty renkleri (legacy)
        ├── terminal/starship/  → Prompt renkleri
        └── theme/gtk-4.0/     → GTK widget renkleri
```

## Dizin Yapısı

Kullanıcı dosyaları XDG standartlarına uyar:
- `~/.config/` — konfigürasyon
- `~/.local/share/` — veri
- `~/.cache/` — önbellek
- `/.snapshots/` — btrfs snapshot'lar
