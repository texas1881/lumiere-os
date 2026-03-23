#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Wallpaper Picker                     ║
# ╚══════════════════════════════════════════════════════════════╝
# Duvar kağıdı seçici — rofi ile

WALLPAPER_DIR="${HOME}/wallpapers"

if [[ ! -d "$WALLPAPER_DIR" ]]; then
    echo "Duvar kağıtları dizini bulunamadı: $WALLPAPER_DIR"
    exit 1
fi

# Duvar kağıtlarını listele
SELECTED=$(find "$WALLPAPER_DIR" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.webp" \) -printf "%f\n" | sort | rofi -dmenu -p "🖼️  Duvar Kağıdı" -theme ~/.config/rofi/lumiere.rasi)

if [[ -n "$SELECTED" ]]; then
    WALLPAPER="${WALLPAPER_DIR}/${SELECTED}"
    swww img "$WALLPAPER" \
        --transition-type grow \
        --transition-pos center \
        --transition-duration 1 \
        --transition-fps 60

    # Tercihini kaydet
    mkdir -p ~/.config/lumiere
    echo "$WALLPAPER" > ~/.config/lumiere/current-wallpaper
fi
