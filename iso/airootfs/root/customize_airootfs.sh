#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Live Environment Setup               ║
# ╚══════════════════════════════════════════════════════════════╝
# archiso customize_airootfs scripti — ISO boot sırasında çalışır

set -euo pipefail

# ─── Locale ─────────────────────────────────────────────────────
cat > /etc/locale.gen << EOF
en_US.UTF-8 UTF-8
tr_TR.UTF-8 UTF-8
EOF
locale-gen
echo "LANG=en_US.UTF-8" > /etc/locale.conf

# ─── Klavye ─────────────────────────────────────────────────────
echo "KEYMAP=tr" > /etc/vconsole.conf

# ─── Hostname ──────────────────────────────────────────────────
echo "lumiere-live" > /etc/hostname

# ─── Live Kullanıcı ────────────────────────────────────────────
useradd -m -G wheel,audio,video,network,storage -s /usr/bin/zsh lumiere 2>/dev/null || true
echo "lumiere:lumiere" | chpasswd
echo "root:lumiere" | chpasswd

# sudoers
sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers
echo "lumiere ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# ─── Varsayılan Shell ──────────────────────────────────────────
chsh -s /usr/bin/zsh lumiere

# ─── Servisler ─────────────────────────────────────────────────
systemctl enable NetworkManager
systemctl enable bluetooth
systemctl enable greetd

# ─── greetd (Live) ─────────────────────────────────────────────
mkdir -p /etc/greetd
cat > /etc/greetd/config.toml << EOF
[terminal]
vt = 1

[default_session]
command = "tuigreet --time --remember --remember-session --asterisks --greeting 'Lumière OS ✦ Live' --cmd Hyprland"
user = "greeter"
EOF

# ─── Lumière Araçları ──────────────────────────────────────────
chmod +x /usr/local/bin/lumiere-pkg 2>/dev/null || true
chmod +x /usr/local/bin/lumiere-welcome 2>/dev/null || true
chmod +x /usr/local/bin/lumiere-install 2>/dev/null || true

# ─── Plymouth ──────────────────────────────────────────────────
if [[ -f /usr/share/lumiere/plymouth/lumiere.plymouth ]]; then
    mkdir -p /usr/share/plymouth/themes/lumiere
    cp /usr/share/lumiere/plymouth/* /usr/share/plymouth/themes/lumiere/
    plymouth-set-default-theme lumiere 2>/dev/null || true
fi

# ─── fastfetch ─────────────────────────────────────────────────
if [[ -f /usr/share/lumiere/fastfetch/config.jsonc ]]; then
    mkdir -p /home/lumiere/.config/fastfetch
    cp /usr/share/lumiere/fastfetch/config.jsonc /home/lumiere/.config/fastfetch/
fi

# ─── Sahiplik ──────────────────────────────────────────────────
chown -R lumiere:lumiere /home/lumiere
