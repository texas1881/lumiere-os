# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Katkı Rehberi                        ║
# ╚══════════════════════════════════════════════════════════════╝

# Lumière OS'a Katkıda Bulunma

## Başlarken

1. Repo'yu fork edin
2. Feature branch oluşturun: `git checkout -b feature/yeni-ozellik`
3. Değişikliklerinizi commit edin: `git commit -m "feat: yeni özellik eklendi"`
4. Branch'inizi push edin: `git push origin feature/yeni-ozellik`
5. Pull Request açın

## Commit Mesajları

[Conventional Commits](https://www.conventionalcommits.org/) standardını kullanıyoruz:

| Prefix | Açıklama |
|---|---|
| `feat:` | Yeni özellik |
| `fix:` | Hata düzeltme |
| `docs:` | Dokümantasyon |
| `style:` | Tema/CSS değişiklikleri |
| `refactor:` | Yeniden yapılandırma |
| `chore:` | Build/araç güncellemeleri |

## Proje Yapısı

- `desktop/` — Masaüstü konfigürasyonları
- `terminal/` — Terminal ayarları
- `theme/` — Tema ve renkler
- `apps/` — Lumière uygulamaları
- `iso/` — ISO build altyapısı
- `installer/` — Kurulum scripti
- `branding/` — Logo, wallpaper, splash

## Geliştirme Ortamı

```bash
# Bağımlılıklar (Arch Linux)
make setup

# ISO build
sudo make build-iso

# Test
make test-vm

# Lint
make lint
```

## Renk Paleti

Tüm bileşenlerde `theme/colors/lumiere-dark.json` dosyasındaki renkleri kullanın. Yeni renk ekleme gerekiyorsa önce paleti güncelleyin.

## Kurallar

- Shell scriptleri `shellcheck` ile kontrol edilmeli
- Python kodu PEP 8 standardına uymalı
- Her PR tek bir özellik/düzeltme içermeli
- Testler yazılmalı veya mevcut testler güncelleneli
