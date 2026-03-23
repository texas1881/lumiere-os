#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Guided Installer                     ║
# ╚══════════════════════════════════════════════════════════════╝
# Arch Linux tabanlı kurulum scripti — btrfs + UEFI
set -euo pipefail

# ─── Renk Tanımları ─────────────────────────────────────────────
GOLD='\033[38;2;245;166;35m'
GREEN='\033[38;2;74;222;128m'
RED='\033[38;2;248;113;113m'
BLUE='\033[38;2;96;165;250m'
MUTED='\033[38;2;107;104;128m'
WHITE='\033[38;2;232;230;240m'
BOLD='\033[1m'
RESET='\033[0m'

# ─── Yardımcılar ────────────────────────────────────────────────
banner() {
    clear
    echo -e "${GOLD}"
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║       ✦ Lumière OS Installer v0.1        ║"
    echo "  ╚══════════════════════════════════════════╝"
    echo -e "${RESET}"
    echo ""
}

info()    { echo -e "  ${GREEN}✓${RESET} $*"; }
warn()    { echo -e "  ${GOLD}!${RESET} $*"; }
error()   { echo -e "  ${RED}✗${RESET} $*"; }
step()    { echo -e "  ${BLUE}→${RESET} ${BOLD}$*${RESET}"; }
prompt()  { echo -en "  ${GOLD}?${RESET} $* "; }
divider() { echo -e "  ${MUTED}─────────────────────────────────────${RESET}"; }

confirm() {
    prompt "$1 [E/h]"
    read -r answer
    [[ "${answer,,}" != "h" ]]
}

# ─── Ön Kontroller ──────────────────────────────────────────────
preflight() {
    step "Ön kontroller yapılıyor..."

    if [[ $EUID -ne 0 ]]; then
        error "Bu script root olarak çalıştırılmalıdır."
        echo -e "  ${MUTED}Kullanım: sudo lumiere-install${RESET}"
        exit 1
    fi

    if ! ping -c 1 archlinux.org &>/dev/null; then
        error "İnternet bağlantısı yok!"
        echo -e "  ${MUTED}WiFi için: nmtui${RESET}"
        exit 1
    fi

    if [[ ! -d /sys/firmware/efi ]]; then
        error "UEFI modu gerekli! Legacy BIOS desteklenmez."
        exit 1
    fi

    info "Tüm kontroller başarılı."
}

# ─── Disk Seçimi ─────────────────────────────────────────────────
select_disk() {
    step "Kullanılabilir diskler:"
    echo ""
    lsblk -d -o NAME,SIZE,MODEL,TYPE | grep disk | nl
    echo ""

    prompt "Kurulum diski numarasını seçin:"
    read -r disk_num

    TARGET_DISK=$(lsblk -d -o NAME,TYPE | grep disk | sed -n "${disk_num}p" | awk '{print $1}')

    if [[ -z "$TARGET_DISK" ]]; then
        error "Geçersiz seçim!"
        exit 1
    fi

    TARGET_DISK="/dev/${TARGET_DISK}"
    echo ""
    warn "SEÇİLEN DİSK: ${TARGET_DISK}"
    lsblk "${TARGET_DISK}" -o NAME,SIZE,FSTYPE,MOUNTPOINT
    echo ""

    echo -e "  ${RED}⚠ DİKKAT: Bu diskteki TÜM VERİLER SİLİNECEK!${RESET}"
    prompt "Devam etmek istiyor musunuz? (evet yazın):"
    read -r confirmation

    if [[ "$confirmation" != "evet" ]]; then
        info "Kurulum iptal edildi."
        exit 0
    fi
}

# ─── Kullanıcı Bilgileri ────────────────────────────────────────
get_user_info() {
    step "Kullanıcı bilgileri"
    echo ""

    prompt "Hostname (bilgisayar adı):"
    read -r HOSTNAME
    HOSTNAME="${HOSTNAME:-lumiere}"

    prompt "Kullanıcı adı:"
    read -r USERNAME
    USERNAME="${USERNAME:-lumiere}"

    echo ""
    prompt "Kullanıcı parolası:"
    read -rs USER_PASS
    echo ""

    prompt "Parolayı tekrarlayın:"
    read -rs USER_PASS_CONFIRM
    echo ""

    if [[ "$USER_PASS" != "$USER_PASS_CONFIRM" ]]; then
        error "Parolalar eşleşmiyor!"
        exit 1
    fi

    echo ""
    prompt "Root parolası (boş = kullanıcı ile aynı):"
    read -rs ROOT_PASS
    echo ""
    ROOT_PASS="${ROOT_PASS:-$USER_PASS}"

    # Zaman dilimi
    prompt "Zaman dilimi (varsayılan: Europe/Istanbul):"
    read -r TIMEZONE
    TIMEZONE="${TIMEZONE:-Europe/Istanbul}"

    # Klavye düzeni
    prompt "Klavye düzeni (varsayılan: tr):"
    read -r KEYMAP
    KEYMAP="${KEYMAP:-tr}"

    echo ""
    divider
    echo -e "  ${BOLD}Özet:${RESET}"
    echo -e "  Disk:     ${GOLD}${TARGET_DISK}${RESET}"
    echo -e "  Hostname: ${GOLD}${HOSTNAME}${RESET}"
    echo -e "  Kullanıcı:${GOLD}${USERNAME}${RESET}"
    echo -e "  Zaman:    ${GOLD}${TIMEZONE}${RESET}"
    echo -e "  Klavye:   ${GOLD}${KEYMAP}${RESET}"
    divider
    echo ""

    if ! confirm "Kurulum başlasın mı?"; then
        info "İptal edildi."
        exit 0
    fi
}

# ─── Disk Bölümleme ─────────────────────────────────────────────
partition_disk() {
    step "Disk bölümleniyor: ${TARGET_DISK}"

    # Mevcut bölümleri temizle
    wipefs -af "${TARGET_DISK}"
    sgdisk -Z "${TARGET_DISK}"

    # GPT bölümleme
    # 1: EFI System Partition (512MB)
    # 2: Root Partition (kalan)
    sgdisk -n 1:0:+512M -t 1:ef00 -c 1:"EFI" "${TARGET_DISK}"
    sgdisk -n 2:0:0     -t 2:8300 -c 2:"Lumiere" "${TARGET_DISK}"

    # Partition yenileme
    partprobe "${TARGET_DISK}"
    sleep 2

    # Bölüm adlarını belirle
    if [[ "${TARGET_DISK}" == *"nvme"* ]] || [[ "${TARGET_DISK}" == *"mmcblk"* ]]; then
        EFI_PART="${TARGET_DISK}p1"
        ROOT_PART="${TARGET_DISK}p2"
    else
        EFI_PART="${TARGET_DISK}1"
        ROOT_PART="${TARGET_DISK}2"
    fi

    info "Disk bölümlendi."
}

# ─── Dosya Sistemi ──────────────────────────────────────────────
format_partitions() {
    step "Dosya sistemleri oluşturuluyor..."

    # EFI → FAT32
    mkfs.fat -F 32 -n "LUMIERE_EFI" "${EFI_PART}"

    # Root → Btrfs
    mkfs.btrfs -f -L "LUMIERE" "${ROOT_PART}"

    # Btrfs alt birimler
    mount "${ROOT_PART}" /mnt
    btrfs subvolume create /mnt/@
    btrfs subvolume create /mnt/@home
    btrfs subvolume create /mnt/@snapshots
    btrfs subvolume create /mnt/@cache
    btrfs subvolume create /mnt/@log
    umount /mnt

    # Alt birimleri mount et
    mount -o noatime,compress=zstd:3,space_cache=v2,subvol=@ "${ROOT_PART}" /mnt

    mkdir -p /mnt/{boot/efi,home,.snapshots,var/cache,var/log}

    mount -o noatime,compress=zstd:3,space_cache=v2,subvol=@home "${ROOT_PART}" /mnt/home
    mount -o noatime,compress=zstd:3,space_cache=v2,subvol=@snapshots "${ROOT_PART}" /mnt/.snapshots
    mount -o noatime,compress=zstd:3,space_cache=v2,subvol=@cache "${ROOT_PART}" /mnt/var/cache
    mount -o noatime,compress=zstd:3,space_cache=v2,subvol=@log "${ROOT_PART}" /mnt/var/log

    mount "${EFI_PART}" /mnt/boot/efi

    info "Dosya sistemleri hazır."
}

# ─── Temel Kurulum ──────────────────────────────────────────────
install_base() {
    step "Temel sistem kuruluyor... (bu biraz sürebilir)"

    # Pacman mirror'ları güncelle
    reflector --country Turkey,Germany,Netherlands \
        --protocol https \
        --sort rate \
        --latest 10 \
        --save /etc/pacman.d/mirrorlist 2>/dev/null || true

    # pacstrap ile temel sistemi kur
    pacstrap -K /mnt \
        base base-devel linux linux-firmware linux-headers \
        btrfs-progs dosfstools efibootmgr reflector \
        networkmanager network-manager-applet iwd \
        bluez bluez-utils \
        pipewire pipewire-alsa pipewire-pulse pipewire-jack wireplumber pavucontrol \
        mesa vulkan-icd-loader \
        wayland xorg-xwayland hyprland xdg-desktop-portal-hyprland \
        waybar rofi-wayland mako swww wl-clipboard cliphist grim slurp \
        greetd greetd-tuigreet \
        kitty zsh starship fzf zoxide bat eza ripgrep fd \
        inter-font ttf-jetbrains-mono-nerd noto-fonts noto-fonts-cjk noto-fonts-emoji \
        papirus-icon-theme gtk4 gtk3 \
        firefox thunar thunar-volman gvfs nano fastfetch htop brightnessctl \
        git python python-pip python-gobject \
        polkit polkit-gnome \
        plymouth \
        ntfs-3g unzip p7zip

    info "Temel sistem kuruldu."
}

# ─── fstab ──────────────────────────────────────────────────────
generate_fstab() {
    step "fstab oluşturuluyor..."
    genfstab -U /mnt >> /mnt/etc/fstab
    info "fstab hazır."
}

# ─── Chroot İçi Konfigürasyon ───────────────────────────────────
configure_system() {
    step "Sistem konfigüre ediliyor..."

    # Chroot scripti oluştur
    cat > /mnt/tmp/lumiere-chroot.sh << CHROOT_EOF
#!/usr/bin/env bash
set -euo pipefail

# Zaman dilimi
ln -sf /usr/share/zoneinfo/${TIMEZONE} /etc/localtime
hwclock --systohc

# Dil
cat > /etc/locale.gen << EOF
en_US.UTF-8 UTF-8
tr_TR.UTF-8 UTF-8
EOF
locale-gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf

# Klavye
echo "KEYMAP=${KEYMAP}" > /etc/vconsole.conf

# Hostname
echo "${HOSTNAME}" > /etc/hostname
cat > /etc/hosts << EOF
127.0.0.1   localhost
::1         localhost
127.0.1.1   ${HOSTNAME}.localdomain ${HOSTNAME}
EOF

# Root parolası
echo "root:${ROOT_PASS}" | chpasswd

# Kullanıcı
useradd -m -G wheel,audio,video,network,storage -s /usr/bin/zsh ${USERNAME}
echo "${USERNAME}:${USER_PASS}" | chpasswd

# Sudo
sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers

# ─── Bootloader: systemd-boot ──────────────────────────────────
bootctl install --esp-path=/boot/efi

# Loader konfigürasyonu
cat > /boot/efi/loader/loader.conf << EOF
default lumiere.conf
timeout 3
console-mode max
editor no
EOF

# Root partition UUID
ROOT_UUID=\$(blkid -s UUID -o value ${ROOT_PART})

cat > /boot/efi/loader/entries/lumiere.conf << EOF
title   ✦ Lumière OS
linux   /vmlinuz-linux
initrd  /initramfs-linux.img
options root=UUID=\${ROOT_UUID} rootflags=subvol=@ rw quiet splash loglevel=3 systemd.show_status=auto
EOF

cat > /boot/efi/loader/entries/lumiere-fallback.conf << EOF
title   ✦ Lumière OS (Fallback)
linux   /vmlinuz-linux
initrd  /initramfs-linux-fallback.img
options root=UUID=\${ROOT_UUID} rootflags=subvol=@ rw
EOF

# ─── mkinitcpio ─────────────────────────────────────────────────
sed -i 's/^HOOKS=.*/HOOKS=(base systemd autodetect microcode modconf kms keyboard sd-vconsole block filesystems fsck plymouth)/' /etc/mkinitcpio.conf
mkinitcpio -P

# ─── Servisler ──────────────────────────────────────────────────
systemctl enable NetworkManager
systemctl enable bluetooth
systemctl enable greetd

# ─── greetd konfigürasyonu ──────────────────────────────────────
cat > /etc/greetd/config.toml << EOF
[terminal]
vt = 1

[default_session]
command = "tuigreet --time --remember --remember-session --asterisks --greeting 'Lumière OS ✦' --cmd Hyprland"
user = "greeter"
EOF

# ─── Plymouth ──────────────────────────────────────────────────
if [[ -d /usr/share/lumiere/plymouth ]]; then
    mkdir -p /usr/share/plymouth/themes/lumiere
    cp /usr/share/lumiere/plymouth/* /usr/share/plymouth/themes/lumiere/
    plymouth-set-default-theme lumiere
fi

# ─── Zsh varsayılan shell ───────────────────────────────────────
chsh -s /usr/bin/zsh ${USERNAME}

CHROOT_EOF

    chmod +x /mnt/tmp/lumiere-chroot.sh
    arch-chroot /mnt /tmp/lumiere-chroot.sh
    rm /mnt/tmp/lumiere-chroot.sh

    info "Sistem konfigüre edildi."
}

# ─── Lumière Dosyaları ──────────────────────────────────────────
install_lumiere_files() {
    step "Lumière OS dosyaları kuruluyor..."

    local user_home="/mnt/home/${USERNAME}"

    # Konfigürasyon dosyaları (ISO'dan veya live ortamdan kopyala)
    local source_config=""
    if [[ -d "/usr/share/lumiere/skel" ]]; then
        source_config="/usr/share/lumiere/skel"
    elif [[ -d "/etc/skel/.config" ]]; then
        source_config="/etc/skel"
    fi

    if [[ -n "$source_config" ]]; then
        cp -rT "${source_config}" "${user_home}/"
    fi

    # lumiere-pkg
    if [[ -f "/usr/local/bin/lumiere-pkg" ]]; then
        cp /usr/local/bin/lumiere-pkg /mnt/usr/local/bin/
        chmod +x /mnt/usr/local/bin/lumiere-pkg
    fi

    # lumiere-welcome
    if [[ -d "/usr/share/lumiere/welcome" ]]; then
        mkdir -p /mnt/usr/share/lumiere/welcome
        cp -r /usr/share/lumiere/welcome/* /mnt/usr/share/lumiere/welcome/
        cp /usr/local/bin/lumiere-welcome /mnt/usr/local/bin/ 2>/dev/null || true
        chmod +x /mnt/usr/local/bin/lumiere-welcome 2>/dev/null || true

        # Autostart
        mkdir -p "${user_home}/.config/autostart"
        cp /usr/share/lumiere/welcome/lumiere-welcome.desktop \
            "${user_home}/.config/autostart/" 2>/dev/null || true
    fi

    # Plymouth tema
    if [[ -d "/usr/share/lumiere/plymouth" ]]; then
        mkdir -p /mnt/usr/share/lumiere/plymouth
        cp -r /usr/share/lumiere/plymouth/* /mnt/usr/share/lumiere/plymouth/
    fi

    # fastfetch konfigürasyonu
    if [[ -f "/usr/share/lumiere/fastfetch/config.jsonc" ]]; then
        mkdir -p "${user_home}/.config/fastfetch"
        cp /usr/share/lumiere/fastfetch/config.jsonc "${user_home}/.config/fastfetch/"
    fi

    # Sahipliği düzelt
    arch-chroot /mnt chown -R "${USERNAME}:${USERNAME}" "/home/${USERNAME}"

    info "Lumière OS dosyaları kuruldu."
}

# ─── Temizlik & Tamamlama ──────────────────────────────────────
finalize() {
    step "Kurulum tamamlanıyor..."

    # Unmount
    sync
    umount -R /mnt

    echo ""
    echo -e "${GREEN}"
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║     ✦ Lumière OS Kurulumu Tamamlandı!    ║"
    echo "  ╚══════════════════════════════════════════╝"
    echo -e "${RESET}"
    echo ""
    echo -e "  ${MUTED}Sisteminizi yeniden başlatabilirsiniz:${RESET}"
    echo -e "  ${GOLD}reboot${RESET}"
    echo ""
}

# ─── Ana Akış ───────────────────────────────────────────────────
main() {
    banner
    preflight
    echo ""

    select_disk
    echo ""

    get_user_info
    echo ""

    partition_disk
    echo ""

    format_partitions
    echo ""

    install_base
    echo ""

    generate_fstab
    echo ""

    configure_system
    echo ""

    install_lumiere_files
    echo ""

    finalize
}

main "$@"
