# Başlangıç Rehberi

## 1. ISO İndirme

[Releases](https://github.com/texas1881/lumiere-os/releases) sayfasından en güncel ISO'yu indirin.

## 2. Bootable USB Oluşturma

### Linux
```bash
sudo dd if=lumiere-os-*.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

### Windows
- [Rufus](https://rufus.ie) veya [balenaEtcher](https://etcher.balena.io) kullanın
- GPT bölümleme + DD mod seçin

### macOS
```bash
sudo dd if=lumiere-os-*.iso of=/dev/rdiskN bs=4m
```

## 3. Boot Etme

1. USB'yi takın
2. BIOS/UEFI'ye girin (genelde F2, F12, Del)
3. Boot sırasını USB olarak ayarlayın
4. Secure Boot'u devre dışı bırakın
5. Kaydet ve yeniden başlat

## 4. Live Ortam

Boot sonrası doğrudan Lumière OS masaüstüne gelirsiniz (live mod). Kurulumdan önce deneyebilirsiniz.

## 5. Kurulum

Masaüstünde veya menüde **Lumière Installer** uygulamasını çalıştırın.

Adımlar:
1. **Dil seçimi** — Türkçe varsayılan
2. **Klavye düzeni** — TR-Q varsayılan
3. **Disk bölümleme** — Otomatik (tam disk) veya manuel
4. **Kullanıcı** — Ad, şifre, hostname
5. **Paketler** — Ek paket seçimi
6. **Kurulum** — Bekleme süresi ~5-15 dk

## 6. İlk Boot

Kurulum sonrası yeniden başladığınızda:
- greetd login ekranı karşılar
- Kullanıcı adı ve şifrenizle giriş yapın
- Hyprland masaüstü açılır
- **Lumière Welcome** otomatik başlar

## Sonraki Adımlar

- `Super + D` → Uygulama başlatıcı
- `Super + Enter` → Terminal
- `Super + /` → Kısayol rehberi
- `lumiere-update` → Sistem güncelleme

---

<p align="center"><a href="Home.md">← Wiki Ana Sayfa</a></p>
