# lumiere-pkg

Lumière OS paket yönetim aracı. `pacman` ve AUR üzerine kullanıcı dostu bir CLI wrapper.

## Kurulum

```bash
sudo cp lumiere-pkg /usr/local/bin/
sudo chmod +x /usr/local/bin/lumiere-pkg
```

## Komutlar

| Komut | Açıklama |
|---|---|
| `lumiere-pkg install <paket>` | Paket yükle |
| `lumiere-pkg remove <paket>` | Paket kaldır |
| `lumiere-pkg update` | Sistemi güncelle |
| `lumiere-pkg search <arama>` | Paket ara |
| `lumiere-pkg info <paket>` | Paket bilgisi |
| `lumiere-pkg list` | Yüklü paketler |
| `lumiere-pkg clean` | Önbelleği temizle |

## Özellikler

- pacman + AUR (paru/yay) otomatik algılama
- Renkli çıktı
- Yetim paket temizliği
- Basit, hatırlanabilir komutlar
