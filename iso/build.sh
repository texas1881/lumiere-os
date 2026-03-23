#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — ISO Build Script                     ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="/tmp/lumiere-build"
OUT_DIR="${PROJECT_ROOT}/out"

# Renk tanımları
GOLD='\033[38;2;245;166;35m'
GREEN='\033[38;2;74;222;128m'
RED='\033[38;2;248;113;113m'
RESET='\033[0m'

banner() {
    echo -e "${GOLD}"
    echo "  ╔══════════════════════════════════════╗"
    echo "  ║       ✦ Lumière OS ISO Builder       ║"
    echo "  ╚══════════════════════════════════════╝"
    echo -e "${RESET}"
}

info()    { echo -e "${GREEN}[✓]${RESET} $*"; }
error()   { echo -e "${RED}[✗]${RESET} $*" >&2; }
step()    { echo -e "${GOLD}[→]${RESET} $*"; }

# ─── Ön kontroller ──────────────────────────────────────────────
check_requirements() {
    step "Gereksinimler kontrol ediliyor..."

    if [[ $EUID -ne 0 ]]; then
        error "Bu script root olarak çalıştırılmalıdır."
        echo "  Kullanım: sudo $0"
        exit 1
    fi

    if ! command -v mkarchiso &>/dev/null; then
        error "archiso bulunamadı. Yükleyin: pacman -S archiso"
        exit 1
    fi

    info "Tüm gereksinimler karşılanıyor."
}

# ─── Airootfs hazırlığı ─────────────────────────────────────────
prepare_airootfs() {
    step "Airootfs hazırlanıyor..."

    local skel="${SCRIPT_DIR}/airootfs/etc/skel"

    # Masaüstü konfigürasyonları
    mkdir -p "${skel}/.config/hypr"
    cp "${PROJECT_ROOT}/desktop/hyprland/hyprland.conf" "${skel}/.config/hypr/"

    # Hyprland yardımcı scriptler
    mkdir -p "${skel}/.config/hypr/scripts"
    cp "${PROJECT_ROOT}/desktop/scripts/osd.sh" "${skel}/.config/hypr/scripts/"
    cp "${PROJECT_ROOT}/desktop/scripts/screenshot.sh" "${skel}/.config/hypr/scripts/"
    chmod +x "${skel}/.config/hypr/scripts/"*.sh

    mkdir -p "${skel}/.config/waybar"
    cp "${PROJECT_ROOT}/desktop/waybar/config.jsonc" "${skel}/.config/waybar/"
    cp "${PROJECT_ROOT}/desktop/waybar/style.css" "${skel}/.config/waybar/"

    mkdir -p "${skel}/.config/rofi"
    cp "${PROJECT_ROOT}/desktop/rofi/config.rasi" "${skel}/.config/rofi/"
    cp "${PROJECT_ROOT}/desktop/rofi/lumiere.rasi" "${skel}/.config/rofi/"

    mkdir -p "${skel}/.config/mako"
    cp "${PROJECT_ROOT}/desktop/mako/config" "${skel}/.config/mako/"

    mkdir -p "${skel}/.config/swaylock"
    cp "${PROJECT_ROOT}/desktop/swaylock/config" "${skel}/.config/swaylock/"

    # Terminal konfigürasyonları
    mkdir -p "${skel}/.config/kitty"
    cp "${PROJECT_ROOT}/terminal/kitty/kitty.conf" "${skel}/.config/kitty/"

    mkdir -p "${skel}/.config/starship"
    cp "${PROJECT_ROOT}/terminal/starship/starship.toml" "${skel}/.config/starship/"
    # Starship config path
    echo 'export STARSHIP_CONFIG="$HOME/.config/starship/starship.toml"' > "${skel}/.zshenv"
    cat "${PROJECT_ROOT}/terminal/zsh/.zshenv" >> "${skel}/.zshenv"
    cp "${PROJECT_ROOT}/terminal/zsh/.zshrc" "${skel}/.zshrc"

    # GTK tema
    mkdir -p "${skel}/.config/gtk-4.0"
    cp "${PROJECT_ROOT}/theme/gtk-4.0/gtk.css" "${skel}/.config/gtk-4.0/"
    mkdir -p "${skel}/.config/gtk-3.0"
    cp "${PROJECT_ROOT}/theme/gtk-3.0/gtk.css" "${skel}/.config/gtk-3.0/"

    # Duvar kağıtları
    mkdir -p "${skel}/wallpapers"
    if [[ -d "${PROJECT_ROOT}/branding/wallpapers" ]]; then
        cp -r "${PROJECT_ROOT}/branding/wallpapers/"* "${skel}/wallpapers/" 2>/dev/null || true
    fi

    # ─── Lumière CLI araçları ───────────────────────────────────────
    local bin_dir="${SCRIPT_DIR}/airootfs/usr/local/bin"
    mkdir -p "${bin_dir}"

    # lumiere-pkg
    if [[ -f "${PROJECT_ROOT}/apps/lumiere-pkg/lumiere-pkg" ]]; then
        cp "${PROJECT_ROOT}/apps/lumiere-pkg/lumiere-pkg" "${bin_dir}/"
        chmod +x "${bin_dir}/lumiere-pkg"
    fi

    # lumiere-welcome
    if [[ -f "${PROJECT_ROOT}/apps/lumiere-welcome/lumiere-welcome" ]]; then
        cp "${PROJECT_ROOT}/apps/lumiere-welcome/lumiere-welcome" "${bin_dir}/"
        chmod +x "${bin_dir}/lumiere-welcome"
    fi

    # lumiere-install
    if [[ -f "${PROJECT_ROOT}/installer/install.sh" ]]; then
        cp "${PROJECT_ROOT}/installer/install.sh" "${bin_dir}/lumiere-install"
        chmod +x "${bin_dir}/lumiere-install"
    fi

    # ─── Share dosyaları ────────────────────────────────────────────
    local share_dir="${SCRIPT_DIR}/airootfs/usr/share/lumiere"

    # Welcome app dosyaları
    mkdir -p "${share_dir}/welcome"
    cp "${PROJECT_ROOT}/apps/lumiere-welcome/welcome.py" "${share_dir}/welcome/"
    cp "${PROJECT_ROOT}/apps/lumiere-welcome/lumiere-welcome.desktop" "${share_dir}/welcome/"

    # Plymouth tema
    mkdir -p "${share_dir}/plymouth"
    cp "${PROJECT_ROOT}/branding/plymouth/lumiere.plymouth" "${share_dir}/plymouth/"
    cp "${PROJECT_ROOT}/branding/plymouth/lumiere.script" "${share_dir}/plymouth/"

    # fastfetch
    mkdir -p "${share_dir}/fastfetch"
    cp "${PROJECT_ROOT}/branding/fastfetch/config.jsonc" "${share_dir}/fastfetch/"

    # Skel dizinine ek dosyalar
    # Autostart — welcome app
    mkdir -p "${skel}/.config/autostart"
    cp "${PROJECT_ROOT}/apps/lumiere-welcome/lumiere-welcome.desktop" "${skel}/.config/autostart/"

    # fastfetch config
    mkdir -p "${skel}/.config/fastfetch"
    cp "${PROJECT_ROOT}/branding/fastfetch/config.jsonc" "${skel}/.config/fastfetch/"

    # Power menu + wallpaper picker
    cp "${PROJECT_ROOT}/desktop/rofi/power-menu.sh" "${skel}/.config/rofi/"
    chmod +x "${skel}/.config/rofi/power-menu.sh"

    if [[ -f "${PROJECT_ROOT}/desktop/scripts/wallpaper-picker.sh" ]]; then
        cp "${PROJECT_ROOT}/desktop/scripts/wallpaper-picker.sh" "${bin_dir}/lumiere-wallpaper"
        chmod +x "${bin_dir}/lumiere-wallpaper"
    fi

    # ─── Desktop entries ────────────────────────────────────────────
    local apps_dir="${SCRIPT_DIR}/airootfs/usr/share/applications"
    mkdir -p "${apps_dir}"
    cp "${PROJECT_ROOT}/apps/lumiere-welcome/lumiere-welcome.desktop" "${apps_dir}/"

    # Installer desktop entry
    cat > "${apps_dir}/lumiere-install.desktop" << 'ENTRY_EOF'
[Desktop Entry]
Type=Application
Name=Lumière OS Installer
Comment=Lumière OS kurulumu
Exec=kitty --title "Lumière Installer" sudo lumiere-install
Icon=system-software-install
Terminal=false
Categories=System;
ENTRY_EOF

    # ─── v0.2 Parıltı Bileşenleri ──────────────────────────────────

    # Lumière Icons
    if [[ -d "${PROJECT_ROOT}/theme/icons/lumiere-icons" ]]; then
        local icon_dir="${SCRIPT_DIR}/airootfs/usr/share/icons/lumiere-icons"
        cp -r "${PROJECT_ROOT}/theme/icons/lumiere-icons" "${SCRIPT_DIR}/airootfs/usr/share/icons/"
        info "Lumière Icons kopyalandı."
    fi

    # Lumiere-Cursors
    if [[ -d "${PROJECT_ROOT}/theme/cursors/Lumiere-Cursors" ]]; then
        cp -r "${PROJECT_ROOT}/theme/cursors/Lumiere-Cursors" "${SCRIPT_DIR}/airootfs/usr/share/icons/"
        info "Lumiere-Cursors kopyalandı."
    fi

    # lumiere-settings
    mkdir -p "${share_dir}/settings"
    if [[ -f "${PROJECT_ROOT}/apps/lumiere-settings/settings.py" ]]; then
        cp "${PROJECT_ROOT}/apps/lumiere-settings/settings.py" "${share_dir}/settings/"
        cp "${PROJECT_ROOT}/apps/lumiere-settings/lumiere-settings" "${bin_dir}/"
        chmod +x "${bin_dir}/lumiere-settings"
        cp "${PROJECT_ROOT}/apps/lumiere-settings/lumiere-settings.desktop" "${apps_dir}/"
        info "lumiere-settings kopyalandı."
    fi

    # lumiere-monitor
    mkdir -p "${share_dir}/monitor"
    if [[ -f "${PROJECT_ROOT}/apps/lumiere-monitor/monitor.py" ]]; then
        cp "${PROJECT_ROOT}/apps/lumiere-monitor/monitor.py" "${share_dir}/monitor/"
        cp "${PROJECT_ROOT}/apps/lumiere-monitor/lumiere-monitor" "${bin_dir}/"
        chmod +x "${bin_dir}/lumiere-monitor"
        cp "${PROJECT_ROOT}/apps/lumiere-monitor/lumiere-monitor.desktop" "${apps_dir}/"
        info "lumiere-monitor kopyalandı."
    fi

    # Tema switcher
    if [[ -f "${PROJECT_ROOT}/desktop/scripts/theme-switcher.sh" ]]; then
        cp "${PROJECT_ROOT}/desktop/scripts/theme-switcher.sh" "${skel}/.config/hypr/scripts/"
        chmod +x "${skel}/.config/hypr/scripts/theme-switcher.sh"
        info "Tema switcher kopyalandı."
    fi

    # Açık tema dosyaları
    mkdir -p "${share_dir}/themes"
    if [[ -f "${PROJECT_ROOT}/theme/gtk-4.0/gtk-light.css" ]]; then
        cp "${PROJECT_ROOT}/theme/gtk-4.0/gtk.css" "${share_dir}/themes/gtk-dark.css"
        cp "${PROJECT_ROOT}/theme/gtk-4.0/gtk-light.css" "${share_dir}/themes/gtk-light.css"
    fi
    if [[ -f "${PROJECT_ROOT}/theme/colors/lumiere-light.json" ]]; then
        cp "${PROJECT_ROOT}/theme/colors/lumiere-light.json" "${share_dir}/"
        cp "${PROJECT_ROOT}/theme/colors/lumiere-dark.json" "${share_dir}/"
    fi

    # Gelişmiş installer
    mkdir -p "${share_dir}/installer"
    if [[ -f "${PROJECT_ROOT}/installer/lumiere-installer/installer.py" ]]; then
        cp "${PROJECT_ROOT}/installer/lumiere-installer/installer.py" "${share_dir}/installer/"
        cp "${PROJECT_ROOT}/installer/install.sh" "${share_dir}/installer/"
        cp "${PROJECT_ROOT}/installer/lumiere-installer/lumiere-installer" "${bin_dir}/"
        chmod +x "${bin_dir}/lumiere-installer"
        cp "${PROJECT_ROOT}/installer/lumiere-installer/lumiere-installer.desktop" "${apps_dir}/"
        info "Gelişmiş installer kopyalandı."
    fi

    # ─── v1.0 Tam Işık Bileşenleri ─────────────────────────────────

    # lumiere-cheatsheet
    mkdir -p "${share_dir}/cheatsheet"
    if [[ -f "${PROJECT_ROOT}/apps/lumiere-cheatsheet/cheatsheet.py" ]]; then
        cp "${PROJECT_ROOT}/apps/lumiere-cheatsheet/cheatsheet.py" "${share_dir}/cheatsheet/"
        cp "${PROJECT_ROOT}/apps/lumiere-cheatsheet/lumiere-cheatsheet" "${bin_dir}/"
        chmod +x "${bin_dir}/lumiere-cheatsheet"
        cp "${PROJECT_ROOT}/apps/lumiere-cheatsheet/lumiere-cheatsheet.desktop" "${apps_dir}/"
        info "lumiere-cheatsheet kopyalandı."
    fi

    # MIME associations
    if [[ -f "${PROJECT_ROOT}/desktop/mimeapps.list" ]]; then
        cp "${PROJECT_ROOT}/desktop/mimeapps.list" "${skel}/.config/mimeapps.list"
        info "MIME ilişkileri kopyalandı."
    fi

    # Hardware detection script
    if [[ -f "${PROJECT_ROOT}/scripts/lumiere-hw-detect.sh" ]]; then
        cp "${PROJECT_ROOT}/scripts/lumiere-hw-detect.sh" "${bin_dir}/lumiere-hw-detect"
        chmod +x "${bin_dir}/lumiere-hw-detect"
        info "lumiere-hw-detect kopyalandı."
    fi

    info "Airootfs hazır."
}

# ─── Servis konfigürasyonları ───────────────────────────────────
configure_services() {
    step "Systemd servisleri konfigüre ediliyor..."

    local systemd_dir="${SCRIPT_DIR}/airootfs/etc/systemd/system"
    mkdir -p "${systemd_dir}/multi-user.target.wants"
    mkdir -p "${systemd_dir}/sockets.target.wants"

    # NetworkManager
    ln -sf /usr/lib/systemd/system/NetworkManager.service \
        "${systemd_dir}/multi-user.target.wants/NetworkManager.service"

    # Bluetooth
    ln -sf /usr/lib/systemd/system/bluetooth.service \
        "${systemd_dir}/multi-user.target.wants/bluetooth.service"

    # greetd
    ln -sf /usr/lib/systemd/system/greetd.service \
        "${systemd_dir}/multi-user.target.wants/greetd.service"

    # CUPS (v1.0)
    ln -sf /usr/lib/systemd/system/cups.service \
        "${systemd_dir}/multi-user.target.wants/cups.service"

    # Power Profiles (v1.0)
    ln -sf /usr/lib/systemd/system/power-profiles-daemon.service \
        "${systemd_dir}/multi-user.target.wants/power-profiles-daemon.service"

    # PipeWire (kullanıcı başına etkinleştirilir)

    # greetd konfigürasyonu
    local greetd_dir="${SCRIPT_DIR}/airootfs/etc/greetd"
    mkdir -p "${greetd_dir}"
    cat > "${greetd_dir}/config.toml" << 'EOF'
[terminal]
vt = 1

[default_session]
command = "tuigreet --time --remember --remember-session --asterisks --greeting 'Lumière OS ✦' --cmd Hyprland"
user = "greeter"
EOF

    info "Servisler konfigüre edildi."
}

# ─── ISO Build ──────────────────────────────────────────────────
build_iso() {
    step "ISO oluşturuluyor... (bu biraz sürebilir)"

    mkdir -p "${OUT_DIR}"
    rm -rf "${BUILD_DIR}"

    mkarchiso -v -w "${BUILD_DIR}" -o "${OUT_DIR}" "${SCRIPT_DIR}"

    info "ISO başarıyla oluşturuldu!"
    echo ""
    echo -e "  ${GOLD}📀 ISO dosyası:${RESET}"
    ls -lh "${OUT_DIR}"/*.iso 2>/dev/null || echo "  ISO bulunamadı."
    echo ""
}

# ─── Ana akış ───────────────────────────────────────────────────
main() {
    banner
    check_requirements
    prepare_airootfs
    configure_services
    build_iso

    echo -e "${GREEN}"
    echo "  ╔══════════════════════════════════════╗"
    echo "  ║        ✦ Build Tamamlandı! ✦         ║"
    echo "  ╚══════════════════════════════════════╝"
    echo -e "${RESET}"
    echo "  Test için: make test-vm"
}

main "$@"
