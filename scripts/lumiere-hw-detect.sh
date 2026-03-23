#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║     ✦ Lumière OS — Hardware Detection & Auto-Configuration   ║
# ╚══════════════════════════════════════════════════════════════╝
# İlk boot'ta çalışır, donanımı algılar ve optimal ayarları uygular.
set -euo pipefail

GOLD='\033[38;2;245;166;35m'
GREEN='\033[38;2;74;222;128m'
RED='\033[38;2;248;113;113m'
RESET='\033[0m'

info()  { echo -e "${GREEN}[✓]${RESET} $*"; }
warn()  { echo -e "${GOLD}[!]${RESET} $*"; }
error() { echo -e "${RED}[✗]${RESET} $*" >&2; }
step()  { echo -e "${GOLD}[→]${RESET} $*"; }

# ─── NVIDIA GPU Algılama ────────────────────────────────────────
detect_nvidia() {
    step "GPU kontrol ediliyor..."

    if lspci -k 2>/dev/null | grep -iA 2 "vga\|3d\|display" | grep -qi "nvidia"; then
        info "NVIDIA GPU algılandı."

        if ! pacman -Q nvidia-dkms &>/dev/null; then
            warn "NVIDIA sürücüleri kuruluyor..."
            sudo pacman -S --noconfirm nvidia-dkms nvidia-utils nvidia-settings \
                lib32-nvidia-utils egl-wayland
            info "NVIDIA sürücüleri kuruldu."
        else
            info "NVIDIA sürücüleri zaten kurulu."
        fi

        # Kernel parametreleri
        local boot_conf="/boot/loader/entries/lumiere.conf"
        if [[ -f "$boot_conf" ]] && ! grep -q "nvidia" "$boot_conf"; then
            sudo sed -i 's/^options.*/& nvidia-drm.modeset=1 nvidia-drm.fbdev=1/' "$boot_conf"
            info "Kernel parametreleri güncellendi."
        fi

        # Modprobe
        echo -e "options nvidia-drm modeset=1 fbdev=1" | sudo tee /etc/modprobe.d/nvidia.conf > /dev/null

        # mkinitcpio MODULES
        if ! grep -q "nvidia" /etc/mkinitcpio.conf 2>/dev/null; then
            sudo sed -i 's/^MODULES=(\(.*\))/MODULES=(\1 nvidia nvidia_modeset nvidia_uvm nvidia_drm)/' /etc/mkinitcpio.conf
            sudo mkinitcpio -P
            info "initramfs yeniden oluşturuldu."
        fi
    else
        info "NVIDIA GPU bulunamadı (Mesa/Intel/AMD kullanılacak)."
    fi
}

# ─── HiDPI Algılama ────────────────────────────────────────────
detect_hidpi() {
    step "Ekran çözünürlüğü kontrol ediliyor..."

    local scale=1
    # wayland altında wlr-randr ile kontrol
    if command -v wlr-randr &>/dev/null; then
        local res
        res=$(wlr-randr 2>/dev/null | grep -oP '\d+x\d+' | head -1 || echo "1920x1080")
        local width height
        width=$(echo "$res" | cut -dx -f1)
        height=$(echo "$res" | cut -dx -f2)

        if (( width >= 3840 )); then
            scale=2
        elif (( width >= 2560 )); then
            scale=1.5
        fi
    fi

    if (( $(echo "$scale > 1" | bc -l) )); then
        info "HiDPI ekran algılandı (Ölçek: ${scale}x)."

        local hypr_conf="$HOME/.config/hypr/hyprland.conf"
        if [[ -f "$hypr_conf" ]] && ! grep -q "^monitor.*,${scale}" "$hypr_conf"; then
            sed -i "s/^monitor = , preferred, auto, .*/monitor = , preferred, auto, ${scale}/" "$hypr_conf"
            info "Hyprland ölçek ayarlandı: ${scale}x"
        fi

        # GDK / Qt ölçek
        local env_file="$HOME/.config/hypr/env.conf"
        mkdir -p "$(dirname "$env_file")"
        cat > "$env_file" <<EOF
env = GDK_SCALE, ${scale}
env = QT_SCALE_FACTOR, ${scale}
env = XCURSOR_SIZE, $(( 24 * ${scale%.*} ))
EOF
        info "HiDPI ortam değişkenleri ayarlandı."
    else
        info "Standart çözünürlük ekran."
    fi
}

# ─── Bluetooth ──────────────────────────────────────────────────
enable_bluetooth() {
    step "Bluetooth servisi kontrol ediliyor..."
    if systemctl is-enabled bluetooth.service &>/dev/null; then
        info "Bluetooth zaten etkin."
    else
        sudo systemctl enable --now bluetooth.service
        info "Bluetooth etkinleştirildi."
    fi
}

# ─── Yazıcı Desteği ────────────────────────────────────────────
enable_printing() {
    step "Yazıcı servisi kontrol ediliyor..."
    if pacman -Q cups &>/dev/null; then
        if ! systemctl is-enabled cups.service &>/dev/null; then
            sudo systemctl enable --now cups.service
            info "CUPS yazıcı servisi etkinleştirildi."
        else
            info "CUPS zaten etkin."
        fi
    else
        warn "CUPS kurulu değil. Kurulum: sudo pacman -S cups cups-pdf"
    fi
}

# ─── USB Otomatik Bağlama ──────────────────────────────────────
enable_automount() {
    step "USB otomatik bağlama kontrol ediliyor..."
    if pacman -Q udisks2 &>/dev/null; then
        if pacman -Q udiskie &>/dev/null; then
            # Autostart entry oluştur
            local autostart_dir="$HOME/.config/autostart"
            mkdir -p "$autostart_dir"
            if [[ ! -f "$autostart_dir/udiskie.desktop" ]]; then
                cat > "$autostart_dir/udiskie.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=udiskie
Comment=Automount removable media
Exec=udiskie --tray
NoDisplay=true
EOF
                info "USB otomatik bağlama etkinleştirildi (udiskie)."
            else
                info "USB otomatik bağlama zaten ayarlı."
            fi
        fi
    fi
}

# ─── Güç Yönetimi ──────────────────────────────────────────────
configure_power() {
    step "Güç yönetimi kontrol ediliyor..."
    if pacman -Q power-profiles-daemon &>/dev/null; then
        if ! systemctl is-enabled power-profiles-daemon.service &>/dev/null; then
            sudo systemctl enable --now power-profiles-daemon.service
            info "Güç profilleri servisi etkinleştirildi."
        else
            info "Güç profilleri zaten etkin."
        fi
    fi
}

# ─── Ana Akış ───────────────────────────────────────────────────
main() {
    echo -e "${GOLD}"
    echo "  ╔══════════════════════════════════════╗"
    echo "  ║   ✦ Lumière OS Hardware Detect       ║"
    echo "  ╚══════════════════════════════════════╝"
    echo -e "${RESET}"

    detect_nvidia
    detect_hidpi
    enable_bluetooth
    enable_printing
    enable_automount
    configure_power

    echo ""
    info "Donanım konfigürasyonu tamamlandı!"
    echo ""
}

main "$@"
