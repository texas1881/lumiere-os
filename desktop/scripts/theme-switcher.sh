#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║       ✦ Lumière OS — Otomatik Tema Değiştirici               ║
# ╚══════════════════════════════════════════════════════════════╝
# Kullanım:
#   theme-switcher.sh toggle  — Mevcut temayı değiştir
#   theme-switcher.sh dark    — Koyu temaya geç
#   theme-switcher.sh light   — Açık temaya geç
#   theme-switcher.sh auto    — Saate göre otomatik seç (07-19 açık)

set -euo pipefail

CONFIG_DIR="$HOME/.config/lumiere"
STATE_FILE="$CONFIG_DIR/theme-state"
HYPR_DIR="$HOME/.config/hypr"
GTK4_DIR="$HOME/.config/gtk-4.0"
KITTY_DIR="$HOME/.config/kitty"

# ── Mevcut Durumu Oku ──
get_current_theme() {
    if [[ -f "$STATE_FILE" ]]; then
        cat "$STATE_FILE"
    else
        echo "dark"
    fi
}

# ── Durumu Kaydet ──
save_theme_state() {
    mkdir -p "$CONFIG_DIR"
    echo "$1" > "$STATE_FILE"
}

# ── Koyu Tema Uygula ──
apply_dark() {
    echo "🌙 Koyu tema uygulanıyor..."

    # Hyprland renkleri
    hyprctl keyword general:col.active_border "rgba(F5A623ee) rgba(FFD080ee) 45deg" 2>/dev/null || true
    hyprctl keyword general:col.inactive_border "rgba(2A2A4288)" 2>/dev/null || true
    hyprctl keyword decoration:active_opacity 0.95 2>/dev/null || true
    hyprctl keyword decoration:inactive_opacity 0.85 2>/dev/null || true

    # GTK4 tema
    if [[ -f "$HOME/.local/share/lumiere/themes/gtk-dark.css" ]]; then
        cp "$HOME/.local/share/lumiere/themes/gtk-dark.css" "$GTK4_DIR/gtk.css"
    fi

    # GTK prefer-color-scheme
    gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
    gsettings set org.gnome.desktop.interface gtk-theme 'Lumiere-Dark' 2>/dev/null || true

    # Kitty
    if command -v kitty &>/dev/null; then
        kitty +kitten themes --reload-in=all "Lumiere Dark" 2>/dev/null || true
    fi

    # Waybar yeniden yükle
    pkill -SIGUSR2 waybar 2>/dev/null || true

    # Mako bildirim
    notify-send -t 2000 "🌙 Koyu Tema" "Lumière koyu tema etkinleştirildi"

    save_theme_state "dark"
}

# ── Açık Tema Uygula ──
apply_light() {
    echo "☀️ Açık tema uygulanıyor..."

    # Hyprland renkleri
    hyprctl keyword general:col.active_border "rgba(D48E1Aee) rgba(F5A623ee) 45deg" 2>/dev/null || true
    hyprctl keyword general:col.inactive_border "rgba(D5D2E088)" 2>/dev/null || true
    hyprctl keyword decoration:active_opacity 1.0 2>/dev/null || true
    hyprctl keyword decoration:inactive_opacity 0.92 2>/dev/null || true

    # GTK4 tema
    if [[ -f "$HOME/.local/share/lumiere/themes/gtk-light.css" ]]; then
        cp "$HOME/.local/share/lumiere/themes/gtk-light.css" "$GTK4_DIR/gtk.css"
    fi

    # GTK prefer-color-scheme
    gsettings set org.gnome.desktop.interface color-scheme 'prefer-light' 2>/dev/null || true
    gsettings set org.gnome.desktop.interface gtk-theme 'Lumiere-Light' 2>/dev/null || true

    # Kitty
    if command -v kitty &>/dev/null; then
        kitty +kitten themes --reload-in=all "Lumiere Light" 2>/dev/null || true
    fi

    # Waybar yeniden yükle
    pkill -SIGUSR2 waybar 2>/dev/null || true

    # Mako bildirim
    notify-send -t 2000 "☀️ Açık Tema" "Lumière açık tema etkinleştirildi"

    save_theme_state "light"
}

# ── Auto Mod ──
auto_select() {
    HOUR=$(date +%H)
    if (( HOUR >= 7 && HOUR < 19 )); then
        apply_light
    else
        apply_dark
    fi
}

# ── Ana Mantık ──
case "${1:-toggle}" in
    toggle)
        CURRENT=$(get_current_theme)
        if [[ "$CURRENT" == "dark" ]]; then
            apply_light
        else
            apply_dark
        fi
        ;;
    dark)
        apply_dark
        ;;
    light)
        apply_light
        ;;
    auto)
        auto_select
        ;;
    *)
        echo "Kullanım: $(basename "$0") [toggle|dark|light|auto]"
        exit 1
        ;;
esac
