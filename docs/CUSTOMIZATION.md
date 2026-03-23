# ✦ Lumière OS — Özelleştirme Rehberi

Bu rehber Lumière OS'u kendi zevkinize göre kişiselleştirmenizi sağlar.

---

## Renk Paleti

Lumière OS merkezi renk paleti kullanır. Tüm bileşenler bu dosyalardan beslenir:

```
theme/colors/lumiere-dark.json   ← Koyu tema renkleri
theme/colors/lumiere-light.json  ← Açık tema renkleri
```

### Renk Yapısı

```json
{
  "name": "Lumière Dark",
  "background": "#0D0D14",
  "surface": "#1E1E32",
  "primary": "#F5A623",
  "secondary": "#FFD080",
  "text": "#E8E8F0",
  "text_secondary": "#9090B0",
  "accent": "#F5A623",
  "error": "#F87171",
  "success": "#4ADE80",
  "border": "#2A2A42"
}
```

Renkleri değiştirdikten sonra `Super + T` ile temayı yeniden yükleyin.

---

## GTK Tema

GTK4 ve GTK3 tema dosyaları:

```
~/.config/gtk-4.0/gtk.css    ← GTK4 uygulamalar
~/.config/gtk-3.0/gtk.css    ← GTK3 uygulamalar
```

Örnek özelleştirme — vurgu rengini değiştirme:

```css
@define-color accent_color #FF6B6B;
@define-color accent_bg_color #FF6B6B;
```

---

## Waybar Panel

Panel konfigürasyonu: `~/.config/waybar/config.jsonc`
Panel stili: `~/.config/waybar/style.css`

### Modül Ekleme/Çıkarma

`config.jsonc` dosyasında `modules-left`, `modules-center`, `modules-right` dizilerini düzenleyin:

```jsonc
{
    "modules-left": ["hyprland/workspaces", "hyprland/window"],
    "modules-center": ["clock"],
    "modules-right": ["pulseaudio", "network", "battery", "tray"]
}
```

---

## Hyprland Compositor

Konfigürasyon: `~/.config/hypr/hyprland.conf`

### Animasyonları Değiştirme

```conf
animations {
    bezier = custom, 0.22, 0.68, 0, 1
    animation = windows, 1, 7, custom, slide
}
```

### Kenar Boşlukları

```conf
general {
    gaps_in = 6       # Pencereler arası
    gaps_out = 12     # Ekran kenarı
    border_size = 3   # Kenar kalınlığı
}
```

### Pencere Kuralları

Belirli uygulamalara özel davranış:

```conf
windowrulev2 = float, class:^(pavucontrol)$
windowrulev2 = size 800 600, class:^(pavucontrol)$
windowrulev2 = opacity 0.9, class:^(firefox)$
```

---

## Rofi Launcher

Tema: `~/.config/rofi/lumiere.rasi`

### Renk Değiştirme

```rasi
* {
    bg: #0D0D14CC;
    fg: #E8E8F0;
    accent: #F5A623;
}
```

---

## Terminal

### Lumière Terminal

Konfigürasyon: `~/.config/lumiere-term/lumiere-term.toml`

```toml
[font]
family = "JetBrains Mono Nerd Font"
size = 13.0

[colors]
background = "#0D0D14"
foreground = "#E8E8F0"

[window]
opacity = 0.92
padding = 10
```

### Starship Prompt

Konfigürasyon: `~/.config/starship/starship.toml`

---

## Duvar Kağıtları

Duvar kağıtlarını `~/wallpapers/` dizinine koyun. Desteklenen formatlar: PNG, JPG, WEBP.

```bash
# Komut satırından değiştirme
swww img ~/wallpapers/yeni-duvar.png --transition-type grow

# Seçici ile
lumiere-wallpaper    # veya Super + W
```

---

## İkon & İmleç Temaları

### İkon Teması Değiştirme

```bash
# GTK ayarları
gsettings set org.gnome.desktop.interface icon-theme "Papirus-Dark"
```

### İmleç Teması Değiştirme

Hyprland'da:
```conf
env = XCURSOR_THEME, Lumiere-Cursors
env = XCURSOR_SIZE, 24
```

---

## Font Değiştirme

Sistem fontları:
```bash
# Mevcut fontları listele
fc-list | grep -i "font adı"

# Yeni font kur
sudo pacman -S ttf-firacode-nerd
```

Hyprland/Waybar'da font belirtme:
```css
* {
    font-family: "Inter", "Noto Sans", sans-serif;
    font-size: 13px;
}
```

---

<p align="center"><strong>Lumière OS</strong> — Işığı takip et. ✦</p>
