# ✦ Lumière OS — Sık Sorulan Sorular (SSS)

---

## Genel

### Lumière OS nedir?
Lumière OS, Arch Linux tabanlı, Wayland-native, modern ve estetik bir masaüstü işletim sistemidir. Kendi Wayland compositor'ü, terminal emülatörü, uygulama mağazası ve araç setine sahiptir.

### Hangi donanımları destekler?
- **CPU**: x86_64 mimarisi (Intel / AMD)
- **GPU**: Mesa (Intel/AMD), NVIDIA (nvidia-dkms otomatik kurulur)
- **Disk**: Btrfs (varsayılan), ext4, NTFS (okuma)
- **Ağ**: WiFi, Ethernet, Bluetooth
- **Çevre**: Yazıcı (CUPS), Webcam (v4l2), USB cihazlar

### Arch Linux bilmem gerekiyor mu?
Hayır. Lumière OS grafik kurulum sihirbazı ve kullanıcı dostu araçlarla gelir. Ancak terminal deneyimi de güçlüdür.

---

## Kurulum

### UEFI mi yoksa Legacy BIOS mu gerekli?
Lumière OS yalnızca **UEFI** modunu destekler. Legacy BIOS desteği bulunmaz.

### Dual boot yapabilir miyim?
Evet. Kurulum sihirbazında diski manuel bölümleyerek Windows veya başka bir Linux ile dual boot yapabilirsiniz. systemd-boot diğer işletim sistemlerini otomatik algılar.

### Minimum disk alanı ne kadar?
En az 20 GB önerilir. Btrfs snapshot'lar için 50+ GB ideal.

---

## Masaüstü

### Neden Hyprland?
Hyprland, Wayland-native bir tiling compositor olarak şunları sunar:
- Güzel animasyonlar
- Esnek tiling + floating mod
- Düşük kaynak tüketimi
- Aktif geliştirme

### Tema nasıl değiştirilir?
`Super + T` ile koyu/açık tema arasında geçiş yapın. Veya **Ayarlar** (`Super + I`) → **Görünüm** sekmesinden özelleştirin.

### Duvar kağıdını nasıl değiştiririm?
`Super + W` ile duvar kağıdı seçicisini açın. `~/wallpapers/` dizinine kendi resimlerinizi koyabilirsiniz.

### Çoklu monitör nasıl ayarlanır?
Monitörler otomatik algılanır. Manuel ayar için `~/.config/hypr/hyprland.conf` dosyasındaki `monitor` satırını düzenleyin:
```
monitor = HDMI-A-1, 1920x1080@60, 1920x0, 1
monitor = eDP-1, 2560x1440@120, 0x0, 1.5
```

---

## Paketler & Güncellemeler

### Nasıl güncelleme yaparım?
```bash
lumiere-update          # pacman + flatpak birleşik güncelleme
sudo pacman -Syu        # sadece sistem paketleri
flatpak update          # sadece flatpak uygulamalar
```

### Güncelleme sonrası sorun çıkarsa ne yapayım?
Her güncelleme öncesi otomatik Btrfs snapshot alınır:
```bash
lumiere-snapshot list           # snapshot'ları listele
lumiere-snapshot rollback <id>  # geri al
```

### AUR paketlerini nasıl kurarım?
Lumière OS varsayılan olarak AUR helper içermez. Önerilen yöntem:
```bash
sudo pacman -S --needed base-devel git
git clone https://aur.archlinux.org/yay.git /tmp/yay
cd /tmp/yay && makepkg -si
```

---

## Sorun Giderme

### "Siyah ekran" — Boot sonrası görüntü yok
1. `Ctrl + Alt + F2` ile TTY'ye geçin
2. `lumiere-hw-detect` çalıştırın (NVIDIA sürücülerini kurar)
3. `reboot`

### WiFi listesi boş
```bash
nmtui                    # TUI ile ağ yönetimi
nmcli device wifi list   # WiFi ağlarını listele
nmcli device wifi connect "SSID" password "şifre"
```

### Ses gelmiyor
```bash
pavucontrol              # Ses ayarları GUI
wpctl status             # PipeWire durumu
systemctl --user restart pipewire wireplumber
```

### HiDPI ekranda her şey çok küçük
```bash
lumiere-hw-detect        # Otomatik ölçekleme ayarlar
```
Veya manuel: `~/.config/hypr/hyprland.conf` → `monitor = , preferred, auto, 2`

### Flatpak uygulamalar tema kullanmıyor
```bash
flatpak override --filesystem=~/.config/gtk-4.0:ro --user
flatpak override --filesystem=~/.config/gtk-3.0:ro --user
```

---

<p align="center"><strong>Lumière OS</strong> — Işığı takip et. ✦</p>
