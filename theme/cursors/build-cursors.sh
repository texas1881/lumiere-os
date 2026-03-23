#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║      ✦ Lumière Cursors — SVG → X11 Cursor Build Script      ║
# ╚══════════════════════════════════════════════════════════════╝
# Gereksinimler: inkscape, xcursorgen
# Kullanım: ./build-cursors.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SVG_DIR="$SCRIPT_DIR/Lumiere-Cursors/svg"
OUT_DIR="$SCRIPT_DIR/Lumiere-Cursors/cursors"
TMP_DIR="/tmp/lumiere-cursor-build"
SIZES=(24 32 48 64)

echo "✦ Lumière Cursors — Build başlatılıyor..."
mkdir -p "$TMP_DIR" "$OUT_DIR"

# İmleç isim eşlemesi: SVG dosya adı → X11 cursor adı
declare -A CURSOR_MAP=(
    ["default"]="left_ptr"
    ["pointer"]="hand2"
    ["text"]="xterm"
    ["wait"]="watch"
    ["crosshair"]="crosshair"
    ["move"]="fleur"
    ["ns-resize"]="sb_v_double_arrow"
    ["ew-resize"]="sb_h_double_arrow"
    ["nwse-resize"]="bottom_right_corner"
    ["nesw-resize"]="bottom_left_corner"
)

# Simge bağlantıları (symlinks)
declare -A CURSOR_LINKS=(
    ["left_ptr"]="arrow default top_left_arrow"
    ["hand2"]="pointer hand1 pointing_hand"
    ["xterm"]="text ibeam"
    ["watch"]="wait progress left_ptr_watch"
    ["fleur"]="move all-scroll grabbing"
    ["sb_v_double_arrow"]="n-resize s-resize ns-resize row-resize"
    ["sb_h_double_arrow"]="e-resize w-resize ew-resize col-resize"
    ["bottom_right_corner"]="nw-resize se-resize nwse-resize"
    ["bottom_left_corner"]="ne-resize sw-resize nesw-resize"
)

for svg_name in "${!CURSOR_MAP[@]}"; do
    svg_file="$SVG_DIR/${svg_name}.svg"
    cursor_name="${CURSOR_MAP[$svg_name]}"

    if [[ ! -f "$svg_file" ]]; then
        echo "⚠️  SVG bulunamadı: $svg_file — atlanıyor"
        continue
    fi

    echo "🔨 İşleniyor: $svg_name → $cursor_name"

    # xcursorgen config dosyası oluştur
    config_file="$TMP_DIR/${cursor_name}.cfg"
    true > "$config_file"

    # Hotspot: varsayılan imleceler için (1,1), diğerleri merkez
    hotspot_x=1
    hotspot_y=1
    case "$svg_name" in
        text|crosshair|move|*-resize)
            hotspot_x=16
            hotspot_y=16
            ;;
        pointer)
            hotspot_x=6
            hotspot_y=2
            ;;
    esac

    for size in "${SIZES[@]}"; do
        png_file="$TMP_DIR/${cursor_name}_${size}.png"

        # SVG → PNG (Inkscape)
        inkscape "$svg_file" \
            --export-type=png \
            --export-filename="$png_file" \
            --export-width="$size" \
            --export-height="$size" \
            2>/dev/null

        # Hotspot'u boyuta göre ölçekle
        scaled_hx=$(( hotspot_x * size / 32 ))
        scaled_hy=$(( hotspot_y * size / 32 ))

        echo "$size $scaled_hx $scaled_hy $png_file" >> "$config_file"
    done

    # xcursorgen ile X11 cursor oluştur
    xcursorgen "$config_file" "$OUT_DIR/$cursor_name"

    # Symlink'leri oluştur
    if [[ -n "${CURSOR_LINKS[$cursor_name]:-}" ]]; then
        for link_name in ${CURSOR_LINKS[$cursor_name]}; do
            ln -sf "$cursor_name" "$OUT_DIR/$link_name"
        done
    fi
done

# Temizlik
rm -rf "$TMP_DIR"

echo ""
echo "✅ Lumière Cursors başarıyla oluşturuldu!"
echo "📁 Çıktı: $OUT_DIR"
echo ""
echo "Kurulum:"
echo "  cp -r Lumiere-Cursors ~/.local/share/icons/"
echo "  veya"
echo "  sudo cp -r Lumiere-Cursors /usr/share/icons/"
