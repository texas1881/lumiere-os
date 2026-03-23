#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Power Menu                           ║
# ╚══════════════════════════════════════════════════════════════╝
# Rofi ile güç yönetimi menüsü

declare -A ACTIONS=(
    ["⏻  Kapat"]="systemctl poweroff"
    ["🔄  Yeniden başlat"]="systemctl reboot"
    ["🔒  Kilitle"]="swaylock"
    ["💤  Uyku"]="systemctl suspend"
    ["🚪  Çıkış"]="hyprctl dispatch exit"
)

# Rofi modülü olarak çalış
if [[ -n "${1:-}" ]]; then
    # Seçim yapıldı
    if [[ -n "${ACTIONS[$1]:-}" ]]; then
        ${ACTIONS[$1]}
    fi
else
    # Menüyü göster
    for key in "${!ACTIONS[@]}"; do
        echo "$key"
    done | sort
fi
