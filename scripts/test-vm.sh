#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — VM Test Script                       ║
# ╚══════════════════════════════════════════════════════════════╝
# QEMU ile en son ISO'yu test et
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUT_DIR="${PROJECT_ROOT}/out"

ISO=$(ls -t "${OUT_DIR}"/*.iso 2>/dev/null | head -1)

if [[ -z "$ISO" ]]; then
    echo "❌ ISO bulunamadı: ${OUT_DIR}/"
    echo "   Önce 'make build-iso' çalıştırın."
    exit 1
fi

echo "🖥️  Lumière OS başlatılıyor..."
echo "   ISO: ${ISO}"
echo ""

qemu-system-x86_64 \
    -enable-kvm \
    -m 2G \
    -cpu host \
    -smp 2 \
    -bios /usr/share/ovmf/x64/OVMF.fd \
    -cdrom "${ISO}" \
    -vga virtio \
    -display gtk \
    -device virtio-net-pci,netdev=net0 \
    -netdev user,id=net0 \
    -device intel-hda \
    -device hda-duplex
