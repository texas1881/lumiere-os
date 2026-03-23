#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — archiso Profil Tanımı                ║
# ╚══════════════════════════════════════════════════════════════╝

iso_name="lumiere-os"
iso_label="LUMIERE_$(date +%Y%m)"
iso_publisher="Lumière OS Project"
iso_application="Lumière OS Live/Install ISO"
iso_version="$(date +%Y.%m.%d)"
install_dir="lumiere"
buildmodes=('iso')
bootmodes=(
    'uefi.systemd-boot.esp'
    'uefi.systemd-boot.eltorito'
)
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '15')
file_permissions=(
    ["/etc/shadow"]="0:0:400"
    ["/etc/gshadow"]="0:0:400"
    ["/usr/local/bin/lumiere-pkg"]="0:0:755"
)
