#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Dev Environment Setup                ║
# ╚══════════════════════════════════════════════════════════════╝
# Geliştirme ortamı bağımlılıklarını kurar (Arch Linux)
set -euo pipefail

echo "✦ Lumière OS geliştirme ortamı kuruluyor..."

# Temel araçlar
sudo pacman -S --needed \
    archiso \
    qemu-full \
    ovmf \
    shellcheck \
    git \
    python \
    python-pip

echo ""
echo "✅ Geliştirme ortamı hazır!"
echo ""
echo "Sonraki adımlar:"
echo "  1. make build-iso    → ISO oluştur"
echo "  2. make test-vm      → VM'de test et"
echo "  3. make lint         → Script'leri kontrol et"
