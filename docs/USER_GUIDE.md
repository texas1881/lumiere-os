# ✦ Lumière OS — Kullanıcı Rehberi

Lumière OS'a hoş geldiniz! Bu rehber kurulum, ilk kullanım ve günlük iş akışınız için ihtiyacınız olan her şeyi kapsar.

---

## İçindekiler

1. [Sistem Gereksinimleri](#sistem-gereksinimleri)
2. [Kurulum](#kurulum)
3. [İlk Açılış](#ilk-açılış)
4. [Masaüstü Ortamı](#masaüstü-ortamı)
5. [Sistem Araçları](#sistem-araçları)
6. [Paket Yönetimi](#paket-yönetimi)
7. [Güncelleme & Snapshot](#güncelleme--snapshot)
8. [Sorun Giderme](#sorun-giderme)

---

## Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---|---|---|
| **CPU** | x86_64, 2 çekirdek | 4+ çekirdek |
| **RAM** | 2 GB | 4+ GB |
| **Disk** | 20 GB | 50+ GB (Btrfs) |
| **GPU** | Mesa uyumlu | Vulkan destekli |
| **Boot** | UEFI | UEFI + Secure Boot |
| **Ağ** | Ethernet / WiFi | — |

---

## Kurulum

### 1. ISO İndirme

[Releases](https://github.com/texas1881/lumiere-os/releases) sayfasından en güncel ISO'yu indirin.

### 2. USB'ye Yazma

```bash
# Linux
sudo dd if=lumiere-os-*.iso of=/dev/sdX bs=4M status=progress

# Windows — Rufus veya balenaEtcher kullanın
```

### 3. BIOS/UEFI Ayarları

- Secure Boot: Devre dışı bırakın (veya MOK ile imzalayın)
- Boot sırası: USB ilk sıraya alın

### 4. Kurulum Sihirbazı

USB'den boot ettikten sonra masaüstüne geleceksiniz. İki kurulum seçeneği vardır:

| Yöntem | Komut | Açıklama |
|---|---|---|
| **Grafik** | `lumiere-installer` | GTK4 tabanlı 6 adımlı wizard |
| **Terminal** | `sudo lumiere-install` | TUI tabanlı hızlı kurulum |

Kurulum sihirbazı:
1. Dil ve klavye seçimi
2. Disk bölümleme (otomatik Btrfs alt birimler)
3. Kullanıcı hesabı oluşturma
4. Bootloader kurulumu (systemd-boot)
5. Paket kurulumu
6. Son yapılandırma

---

## İlk Açılış

### Hoş Geldin Uygulaması

İlk açılışta **Lumière Welcome** otomatik olarak başlar:
- Sistem bilgileri
- Temel ayarlar
- Önerilen uygulamalar
- Kısayol rehberi

### Donanım Tespiti

İlk boot'ta `lumiere-hw-detect` otomatik çalışır:
- NVIDIA GPU sürücü kurulumu
- HiDPI ekran ölçekleme
- Bluetooth etkinleştirme
- Yazıcı servisi
- USB otomatik bağlama

---

## Masaüstü Ortamı

### Panel (Waybar)

Ekranın üstündeki panel şunları gösterir:
- Sol: Çalışma alanları
- Orta: Pencere başlığı
- Sağ: Sistem tepsisi (ağ, ses, saat, güncelleme durumu)

### Uygulama Başlatıcı (Rofi)

`Super + D` ile açılır. Aramaya yazmaya başlayın.

### Bildirimler (Mako)

Bildirimler ekranın sağ üst köşesinde belirir. Tıklayarak kapatabilirsiniz.

### Çalışma Alanları

9 sanal çalışma alanı mevcuttur. `Super + 1-9` ile geçiş yapın. Touchpad'de 3 parmak kaydırma da desteklenir.

### Tüm Kısayollar

`Super + /` ile kısayol rehberini açın veya [SHORTCUTS.md](SHORTCUTS.md) dosyasına bakın.

---

## Sistem Araçları

| Araç | Kısayol | Açıklama |
|---|---|---|
| **Ayarlar** | `Super + I` | Tema, masaüstü, giriş ayarları |
| **Sistem Monitörü** | `Super + M` | CPU, RAM, disk, ağ izleme |
| **App Store** | Menüden | Flatpak uygulama mağazası |
| **Snapshot Yöneticisi** | Menüden | Btrfs snapshot oluştur/geri al |
| **Dosya Yöneticisi** | `Super + E` | Thunar |
| **Terminal** | `Super + Enter` | Lumière Terminal |

---

## Paket Yönetimi

### pacman (Sistem paketleri)

```bash
# Paket arama
pacman -Ss paket_adi

# Paket kurma
sudo pacman -S paket_adi

# Sistem güncelleme
sudo pacman -Syu

# Paket kaldırma
sudo pacman -Rns paket_adi
```

### flatpak (Uygulama mağazası)

```bash
# Arama
flatpak search uygulama

# Kurma
flatpak install flathub uygulama

# Kaldırma
flatpak uninstall uygulama
```

### lumiere-pkg (Birleşik CLI)

```bash
lumiere-pkg search paket
lumiere-pkg install paket
lumiere-pkg update
```

---

## Güncelleme & Snapshot

### OTA Güncelleme

Güncellemeler otomatik kontrol edilir (systemd timer). Waybar'da güncelleme sayısı görünür.

```bash
# Manuel güncelleme
lumiere-update

# Sadece kontrol
lumiere-update --check
```

### Btrfs Snapshot

Her güncelleme öncesi otomatik snapshot alınır.

```bash
# Snapshot listele
lumiere-snapshot list

# Manuel snapshot
lumiere-snapshot create "açıklama"

# Geri alma
lumiere-snapshot rollback <snapshot_id>

# Karşılaştırma
lumiere-snapshot diff <id1> <id2>
```

---

## Sorun Giderme

### Sık Karşılaşılan Sorunlar

| Sorun | Çözüm |
|---|---|
| Siyah ekran (NVIDIA) | `lumiere-hw-detect` çalıştırın |
| WiFi bağlanmıyor | `nmtui` ile bağlanın |
| Ses yok | `pavucontrol` ile çıkışı kontrol edin |
| Ölçekleme bozuk (HiDPI) | `lumiere-hw-detect` çalıştırın |
| Ekran yırtılması | Compositor ayarlarını kontrol edin |

### Log Dosyaları

```bash
# Sistem logu
journalctl -b

# Hyprland logu
cat /tmp/hypr/$(ls -t /tmp/hypr/ | head -1)/hyprland.log

# Paket logu
cat /var/log/pacman.log | tail -50
```

### Destek

- [GitHub Issues](https://github.com/texas1881/lumiere-os/issues) — Hata bildirimi
- [GitHub Discussions](https://github.com/texas1881/lumiere-os/discussions) — Soru & tartışma
- [Wiki](https://github.com/texas1881/lumiere-os/wiki) — Kapsamlı dokümantasyon

---

<p align="center"><strong>Lumière OS</strong> — Işığı takip et. ✦</p>
