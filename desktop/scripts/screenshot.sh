#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Screenshot Tool                      ║
# ╚══════════════════════════════════════════════════════════════╝
# Ekran görüntüsü aracı — alan seçimi, tam ekran, pencere

SCREENSHOT_DIR="${HOME}/Pictures/Screenshots"
mkdir -p "$SCREENSHOT_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FILENAME="${SCREENSHOT_DIR}/screenshot-${TIMESTAMP}.png"

case "${1:-area}" in
    area)
        # Alan seçimi
        grim -g "$(slurp -d)" "$FILENAME"
        ;;
    full)
        # Tam ekran
        grim "$FILENAME"
        ;;
    window)
        # Aktif pencere
        ACTIVE=$(hyprctl activewindow -j | jq -r '"\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"')
        grim -g "$ACTIVE" "$FILENAME"
        ;;
    *)
        echo "Kullanım: lumiere-screenshot [area|full|window]"
        exit 1
        ;;
esac

# Panoya kopyala
wl-copy < "$FILENAME"

# Bildirim
notify-send "Ekran Görüntüsü" "Kaydedildi: $(basename "$FILENAME")" \
    -i "$FILENAME" \
    -t 3000
