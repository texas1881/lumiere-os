# Sorun Giderme

## Görüntü Sorunları

### Boot sonrası siyah ekran
1. `Ctrl + Alt + F2` ile TTY'ye geçin
2. Giriş yapın
3. `lumiere-hw-detect` çalıştırın
4. `reboot`

### Ekran yırtılması / titreme
- NVIDIA: Kernel parametrelerine `nvidia-drm.modeset=1` ekleyin
- AMD/Intel: `~/.config/hypr/hyprland.conf` → `misc { vfr = true }`

### HiDPI ölçekleme bozuk
```bash
lumiere-hw-detect   # Otomatik ayarlar
# veya manuel:
# ~/.config/hypr/hyprland.conf → monitor = , preferred, auto, 2
```

## Ses Sorunları

### Ses çıkışı yok
```bash
# PipeWire durumunu kontrol et
wpctl status
systemctl --user status pipewire wireplumber

# Servisleri yeniden başlat
systemctl --user restart pipewire wireplumber

# GUI ile ayarla
pavucontrol
```

### Bluetooth kulaklık bağlanmıyor
```bash
bluetoothctl
> power on
> scan on
> pair XX:XX:XX:XX:XX:XX
> connect XX:XX:XX:XX:XX:XX
```

## Ağ Sorunları

### WiFi bağlanmıyor
```bash
nmtui                              # TUI ağ yöneticisi
nmcli device wifi list             # Ağları listele
nmcli device wifi connect "SSID" password "şifre"
```

### DNS çözümleme hatası
```bash
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf
sudo systemctl restart NetworkManager
```

## Paket Sorunları

### "unable to lock database" hatası
```bash
sudo rm /var/lib/pacman/db.lck
```

### PGP key hatası
```bash
sudo pacman-key --init
sudo pacman-key --populate archlinux
sudo pacman -Sy archlinux-keyring
```

### Güncelleme sonrası sistem açılmıyor
```bash
# GRUB/systemd-boot'tan eski çekirdeği seçin
# veya live USB'den boot edip:
lumiere-snapshot list
lumiere-snapshot rollback <son_çalışan_id>
```

## Performans

### Yüksek RAM kullanımı
```bash
# Kompozitör etkilerini azalt
# ~/.config/hypr/hyprland.conf:
decoration {
    blur { enabled = false }
    active_opacity = 1.0
    inactive_opacity = 1.0
}
```

### Yavaş boot
```bash
systemd-analyze                    # Boot süresini gör
systemd-analyze blame              # En yavaş servisleri gör
systemd-analyze critical-chain     # Kritik zincir
```

---

<p align="center"><a href="Home.md">← Wiki Ana Sayfa</a></p>
