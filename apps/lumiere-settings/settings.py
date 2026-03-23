#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Ayarlar Uygulaması                   ║
# ╚══════════════════════════════════════════════════════════════╝
"""
lumiere-settings: GTK4/Adwaita tabanlı sistem ayarları uygulaması.

Paneller:
  - Görünüm: Tema modu, accent renk, yazı tipi, opaklık
  - Masaüstü: Duvar kağıdı, gap, border, blur, animasyonlar
  - Giriş: Klavye, fare, touchpad ayarları
  - Hakkında: Sistem bilgileri ve lisans
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib, Pango
import subprocess
import json
import os
import re

APP_ID = "os.lumiere.settings"
VERSION = "0.2.0"
CONFIG_DIR = os.path.expanduser("~/.config/lumiere")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
HYPRLAND_CONF = os.path.expanduser("~/.config/hypr/hyprland.conf")


def load_settings():
    """Ayarları JSON dosyasından yükle."""
    defaults = {
        "theme_mode": "dark",
        "accent_color": "#F5A623",
        "ui_font": "Inter",
        "mono_font": "JetBrains Mono",
        "opacity_active": 0.95,
        "opacity_inactive": 0.85,
        "gaps_in": 4,
        "gaps_out": 8,
        "border_size": 2,
        "border_radius": 8,
        "blur_enabled": True,
        "blur_size": 6,
        "blur_passes": 3,
        "animations_enabled": True,
        "animation_speed": "normal",
        "kb_layout": "tr",
        "mouse_sensitivity": 0,
        "natural_scroll": True,
        "tap_to_click": True,
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                saved = json.load(f)
                defaults.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
    return defaults


def save_settings(settings):
    """Ayarları JSON dosyasına kaydet."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def apply_hyprland_setting(key, value):
    """Hyprland config'inde bir ayarı güncelle."""
    try:
        subprocess.run(["hyprctl", "keyword", key, str(value)], capture_output=True)
    except FileNotFoundError:
        pass


class AppearancePage(Gtk.Box):
    """Görünüm ayarları paneli."""

    def __init__(self, settings, save_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.settings = settings
        self.save_callback = save_callback
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(16)
        self.set_margin_bottom(16)

        # Başlık
        title = Gtk.Label(label="Görünüm")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        # ── Tema Modu ──
        theme_group = Adw.PreferencesGroup(title="Tema Modu")

        theme_row = Adw.ActionRow(title="Renk Şeması", subtitle="Açık, koyu veya otomatik mod")
        self.theme_combo = Gtk.DropDown.new_from_strings(["Koyu", "Açık", "Otomatik"])
        modes = {"dark": 0, "light": 1, "auto": 2}
        self.theme_combo.set_selected(modes.get(settings["theme_mode"], 0))
        self.theme_combo.set_valign(Gtk.Align.CENTER)
        self.theme_combo.connect("notify::selected", self._on_theme_changed)
        theme_row.add_suffix(self.theme_combo)
        theme_group.add(theme_row)
        self.append(theme_group)

        # ── Accent Renk ──
        accent_group = Adw.PreferencesGroup(title="Vurgu Rengi")

        accent_row = Adw.ActionRow(title="Accent Renk", subtitle="Ana vurgu rengi seçin")
        self.color_btn = Gtk.ColorButton()
        color = Gtk.gdk.RGBA()
        color.parse(settings["accent_color"])
        self.color_btn.set_rgba(color)
        self.color_btn.set_valign(Gtk.Align.CENTER)
        self.color_btn.connect("color-set", self._on_accent_changed)
        accent_row.add_suffix(self.color_btn)
        accent_group.add(accent_row)
        self.append(accent_group)

        # ── Yazı Tipleri ──
        font_group = Adw.PreferencesGroup(title="Yazı Tipleri")

        ui_font_row = Adw.ActionRow(title="Arayüz Yazı Tipi", subtitle=settings["ui_font"])
        font_group.add(ui_font_row)

        mono_font_row = Adw.ActionRow(title="Monospace Yazı Tipi", subtitle=settings["mono_font"])
        font_group.add(mono_font_row)
        self.append(font_group)

        # ── Opaklık ──
        opacity_group = Adw.PreferencesGroup(title="Pencere Opaklığı")

        active_row = Adw.ActionRow(title="Aktif Pencere", subtitle=f"{int(settings['opacity_active']*100)}%")
        self.active_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 1.0, 0.05)
        self.active_scale.set_value(settings["opacity_active"])
        self.active_scale.set_size_request(200, -1)
        self.active_scale.set_valign(Gtk.Align.CENTER)
        self.active_scale.connect("value-changed", self._on_opacity_changed, "opacity_active")
        active_row.add_suffix(self.active_scale)
        opacity_group.add(active_row)

        inactive_row = Adw.ActionRow(title="Pasif Pencere", subtitle=f"{int(settings['opacity_inactive']*100)}%")
        self.inactive_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.3, 1.0, 0.05)
        self.inactive_scale.set_value(settings["opacity_inactive"])
        self.inactive_scale.set_size_request(200, -1)
        self.inactive_scale.set_valign(Gtk.Align.CENTER)
        self.inactive_scale.connect("value-changed", self._on_opacity_changed, "opacity_inactive")
        inactive_row.add_suffix(self.inactive_scale)
        opacity_group.add(inactive_row)

        self.append(opacity_group)

    def _on_theme_changed(self, dropdown, _param):
        modes = {0: "dark", 1: "light", 2: "auto"}
        self.settings["theme_mode"] = modes.get(dropdown.get_selected(), "dark")
        self.save_callback()
        # Tema değiştirici script'i çağır
        try:
            mode = self.settings["theme_mode"]
            if mode == "auto":
                subprocess.Popen(["bash", os.path.expanduser("~/.config/hypr/scripts/theme-switcher.sh"), "auto"])
            else:
                subprocess.Popen(["bash", os.path.expanduser("~/.config/hypr/scripts/theme-switcher.sh"), mode])
        except FileNotFoundError:
            pass

    def _on_accent_changed(self, btn):
        rgba = btn.get_rgba()
        self.settings["accent_color"] = f"#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}"
        self.save_callback()

    def _on_opacity_changed(self, scale, key):
        self.settings[key] = round(scale.get_value(), 2)
        self.save_callback()
        if key == "opacity_active":
            apply_hyprland_setting("decoration:active_opacity", self.settings[key])
        elif key == "opacity_inactive":
            apply_hyprland_setting("decoration:inactive_opacity", self.settings[key])


class DesktopPage(Gtk.Box):
    """Masaüstü ayarları paneli."""

    def __init__(self, settings, save_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.settings = settings
        self.save_callback = save_callback
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(16)
        self.set_margin_bottom(16)

        title = Gtk.Label(label="Masaüstü")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        # ── Duvar Kağıdı ──
        wallpaper_group = Adw.PreferencesGroup(title="Duvar Kağıdı")

        wp_row = Adw.ActionRow(title="Duvar Kağıdı Seç", subtitle="Duvar kağıdını değiştirmek için tıklayın")
        wp_btn = Gtk.Button(label="Seç...")
        wp_btn.set_valign(Gtk.Align.CENTER)
        wp_btn.connect("clicked", self._on_wallpaper_pick)
        wp_row.add_suffix(wp_btn)
        wallpaper_group.add(wp_row)
        self.append(wallpaper_group)

        # ── Boşluklar ──
        gap_group = Adw.PreferencesGroup(title="Pencere Boşlukları")

        gap_in_row = Adw.ActionRow(title="İç Boşluk", subtitle=f"{settings['gaps_in']}px")
        self.gap_in_spin = Gtk.SpinButton.new_with_range(0, 20, 1)
        self.gap_in_spin.set_value(settings["gaps_in"])
        self.gap_in_spin.set_valign(Gtk.Align.CENTER)
        self.gap_in_spin.connect("value-changed", self._on_gap_changed, "gaps_in")
        gap_in_row.add_suffix(self.gap_in_spin)
        gap_group.add(gap_in_row)

        gap_out_row = Adw.ActionRow(title="Dış Boşluk", subtitle=f"{settings['gaps_out']}px")
        self.gap_out_spin = Gtk.SpinButton.new_with_range(0, 40, 2)
        self.gap_out_spin.set_value(settings["gaps_out"])
        self.gap_out_spin.set_valign(Gtk.Align.CENTER)
        self.gap_out_spin.connect("value-changed", self._on_gap_changed, "gaps_out")
        gap_out_row.add_suffix(self.gap_out_spin)
        gap_group.add(gap_out_row)

        self.append(gap_group)

        # ── Kenarlıklar ──
        border_group = Adw.PreferencesGroup(title="Kenarlıklar")

        border_size_row = Adw.ActionRow(title="Kenarlık Kalınlığı", subtitle=f"{settings['border_size']}px")
        self.border_spin = Gtk.SpinButton.new_with_range(0, 6, 1)
        self.border_spin.set_value(settings["border_size"])
        self.border_spin.set_valign(Gtk.Align.CENTER)
        self.border_spin.connect("value-changed", self._on_border_changed)
        border_size_row.add_suffix(self.border_spin)
        border_group.add(border_size_row)

        radius_row = Adw.ActionRow(title="Köşe Yuvarlaklığı", subtitle=f"{settings['border_radius']}px")
        self.radius_spin = Gtk.SpinButton.new_with_range(0, 24, 2)
        self.radius_spin.set_value(settings["border_radius"])
        self.radius_spin.set_valign(Gtk.Align.CENTER)
        self.radius_spin.connect("value-changed", self._on_radius_changed)
        radius_row.add_suffix(self.radius_spin)
        border_group.add(radius_row)

        self.append(border_group)

        # ── Blur ──
        blur_group = Adw.PreferencesGroup(title="Bulanıklık Efekti")

        blur_toggle_row = Adw.ActionRow(title="Bulanıklık", subtitle="Pencere arkaplanı bulanıklığı")
        self.blur_switch = Gtk.Switch()
        self.blur_switch.set_active(settings["blur_enabled"])
        self.blur_switch.set_valign(Gtk.Align.CENTER)
        self.blur_switch.connect("state-set", self._on_blur_toggle)
        blur_toggle_row.add_suffix(self.blur_switch)
        blur_group.add(blur_toggle_row)

        blur_size_row = Adw.ActionRow(title="Bulanıklık Yoğunluğu", subtitle=f"{settings['blur_size']}")
        self.blur_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 16, 1)
        self.blur_scale.set_value(settings["blur_size"])
        self.blur_scale.set_size_request(200, -1)
        self.blur_scale.set_valign(Gtk.Align.CENTER)
        self.blur_scale.connect("value-changed", self._on_blur_size_changed)
        blur_size_row.add_suffix(self.blur_scale)
        blur_group.add(blur_size_row)

        self.append(blur_group)

        # ── Animasyonlar ──
        anim_group = Adw.PreferencesGroup(title="Animasyonlar")

        anim_toggle_row = Adw.ActionRow(title="Animasyonlar", subtitle="Pencere geçiş animasyonları")
        self.anim_switch = Gtk.Switch()
        self.anim_switch.set_active(settings["animations_enabled"])
        self.anim_switch.set_valign(Gtk.Align.CENTER)
        self.anim_switch.connect("state-set", self._on_anim_toggle)
        anim_toggle_row.add_suffix(self.anim_switch)
        anim_group.add(anim_toggle_row)

        self.append(anim_group)

    def _on_wallpaper_pick(self, _btn):
        try:
            subprocess.Popen(["bash", os.path.expanduser("~/.config/hypr/scripts/wallpaper-picker.sh")])
        except FileNotFoundError:
            pass

    def _on_gap_changed(self, spin, key):
        self.settings[key] = int(spin.get_value())
        self.save_callback()
        apply_hyprland_setting(f"general:{key}", self.settings[key])

    def _on_border_changed(self, spin):
        self.settings["border_size"] = int(spin.get_value())
        self.save_callback()
        apply_hyprland_setting("general:border_size", self.settings["border_size"])

    def _on_radius_changed(self, spin):
        self.settings["border_radius"] = int(spin.get_value())
        self.save_callback()
        apply_hyprland_setting("decoration:rounding", self.settings["border_radius"])

    def _on_blur_toggle(self, switch, state):
        self.settings["blur_enabled"] = state
        self.save_callback()
        apply_hyprland_setting("decoration:blur:enabled", "true" if state else "false")

    def _on_blur_size_changed(self, scale):
        self.settings["blur_size"] = int(scale.get_value())
        self.save_callback()
        apply_hyprland_setting("decoration:blur:size", self.settings["blur_size"])

    def _on_anim_toggle(self, switch, state):
        self.settings["animations_enabled"] = state
        self.save_callback()
        apply_hyprland_setting("animations:enabled", "true" if state else "false")


class InputPage(Gtk.Box):
    """Giriş cihazları ayarları paneli."""

    def __init__(self, settings, save_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.settings = settings
        self.save_callback = save_callback
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(16)
        self.set_margin_bottom(16)

        title = Gtk.Label(label="Giriş Cihazları")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        # ── Klavye ──
        kb_group = Adw.PreferencesGroup(title="Klavye")

        layout_row = Adw.ActionRow(title="Klavye Düzeni", subtitle=settings["kb_layout"].upper())
        self.layout_combo = Gtk.DropDown.new_from_strings(["TR", "US", "DE", "FR", "ES", "RU"])
        layouts = {"tr": 0, "us": 1, "de": 2, "fr": 3, "es": 4, "ru": 5}
        self.layout_combo.set_selected(layouts.get(settings["kb_layout"], 0))
        self.layout_combo.set_valign(Gtk.Align.CENTER)
        self.layout_combo.connect("notify::selected", self._on_layout_changed)
        layout_row.add_suffix(self.layout_combo)
        kb_group.add(layout_row)

        self.append(kb_group)

        # ── Fare ──
        mouse_group = Adw.PreferencesGroup(title="Fare")

        sens_row = Adw.ActionRow(title="Hassasiyet", subtitle="Fare hızı ayarı")
        self.sens_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -1.0, 1.0, 0.1)
        self.sens_scale.set_value(settings["mouse_sensitivity"])
        self.sens_scale.set_size_request(200, -1)
        self.sens_scale.set_valign(Gtk.Align.CENTER)
        self.sens_scale.connect("value-changed", self._on_sensitivity_changed)
        sens_row.add_suffix(self.sens_scale)
        mouse_group.add(sens_row)

        self.append(mouse_group)

        # ── Touchpad ──
        tp_group = Adw.PreferencesGroup(title="Touchpad")

        natural_row = Adw.ActionRow(title="Doğal Kaydırma", subtitle="İçerik parmak yönünde kayar")
        self.natural_switch = Gtk.Switch()
        self.natural_switch.set_active(settings["natural_scroll"])
        self.natural_switch.set_valign(Gtk.Align.CENTER)
        self.natural_switch.connect("state-set", self._on_natural_toggle)
        natural_row.add_suffix(self.natural_switch)
        tp_group.add(natural_row)

        tap_row = Adw.ActionRow(title="Dokunarak Tıklama", subtitle="Dokunma ile tıklama")
        self.tap_switch = Gtk.Switch()
        self.tap_switch.set_active(settings["tap_to_click"])
        self.tap_switch.set_valign(Gtk.Align.CENTER)
        self.tap_switch.connect("state-set", self._on_tap_toggle)
        tap_row.add_suffix(self.tap_switch)
        tp_group.add(tap_row)

        self.append(tp_group)

    def _on_layout_changed(self, dropdown, _param):
        layouts = {0: "tr", 1: "us", 2: "de", 3: "fr", 4: "es", 5: "ru"}
        self.settings["kb_layout"] = layouts.get(dropdown.get_selected(), "tr")
        self.save_callback()
        apply_hyprland_setting("input:kb_layout", self.settings["kb_layout"])

    def _on_sensitivity_changed(self, scale):
        self.settings["mouse_sensitivity"] = round(scale.get_value(), 1)
        self.save_callback()
        apply_hyprland_setting("input:sensitivity", self.settings["mouse_sensitivity"])

    def _on_natural_toggle(self, switch, state):
        self.settings["natural_scroll"] = state
        self.save_callback()
        apply_hyprland_setting("input:touchpad:natural_scroll", "true" if state else "false")

    def _on_tap_toggle(self, switch, state):
        self.settings["tap_to_click"] = state
        self.save_callback()
        apply_hyprland_setting("input:touchpad:tap-to-click", "true" if state else "false")


class AboutPage(Gtk.Box):
    """Hakkında paneli."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_vexpand(True)

        # Logo
        logo = Gtk.Label(label="✦")
        logo.add_css_class("about-logo")
        self.append(logo)

        # İsim
        name_label = Gtk.Label(label="Lumière OS")
        name_label.add_css_class("title-1")
        self.append(name_label)

        # Versiyon
        ver_label = Gtk.Label(label=f"v{VERSION} \"Parıltı\"")
        ver_label.add_css_class("dim-label")
        self.append(ver_label)

        # Açıklama
        desc = Gtk.Label(label="Hızlı, güvenli ve estetik bir Linux deneyimi.")
        desc.set_margin_top(12)
        self.append(desc)

        # Sistem bilgileri
        info_group = Adw.PreferencesGroup(title="Sistem Bilgileri")
        info_group.set_margin_top(24)

        # Kernel
        try:
            kernel = subprocess.check_output(["uname", "-r"], text=True).strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            kernel = "Bilinmiyor"
        kernel_row = Adw.ActionRow(title="Kernel", subtitle=kernel)
        info_group.add(kernel_row)

        # DE
        de_row = Adw.ActionRow(title="Masaüstü", subtitle="Hyprland (Wayland)")
        info_group.add(de_row)

        # Shell
        shell_row = Adw.ActionRow(title="Kabuk", subtitle=os.environ.get("SHELL", "/bin/zsh"))
        info_group.add(shell_row)

        self.append(info_group)

        # Lisans
        license_label = Gtk.Label(label="MIT Lisansı ile dağıtılmaktadır.")
        license_label.add_css_class("dim-label")
        license_label.set_margin_top(16)
        self.append(license_label)


class LumiereSettingsWindow(Adw.ApplicationWindow):
    """Ana ayarlar penceresi."""

    def __init__(self, app):
        super().__init__(application=app, title="Lumière Ayarlar")
        self.set_default_size(900, 640)

        self.settings = load_settings()

        # Ana layout: NavigationSplitView
        split_view = Adw.NavigationSplitView()
        self.set_content(split_view)

        # ── Sidebar ──
        sidebar_page = Adw.NavigationPage(title="Ayarlar")
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_page.set_child(sidebar_box)

        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_title_widget(Gtk.Label(label="✦ Lumière Ayarlar"))
        sidebar_box.append(sidebar_header)

        # Kategori listesi
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class("navigation-sidebar")
        self.listbox.connect("row-selected", self._on_category_selected)

        categories = [
            ("🎨", "Görünüm"),
            ("🖥️", "Masaüstü"),
            ("⌨️", "Giriş Cihazları"),
            ("ℹ️", "Hakkında"),
        ]

        for icon, label_text in categories:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.set_margin_start(12)
            hbox.set_margin_end(12)
            hbox.set_margin_top(10)
            hbox.set_margin_bottom(10)

            icon_label = Gtk.Label(label=icon)
            icon_label.set_size_request(24, -1)
            hbox.append(icon_label)

            text_label = Gtk.Label(label=label_text)
            text_label.set_halign(Gtk.Align.START)
            hbox.append(text_label)

            row.set_child(hbox)
            self.listbox.append(row)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.listbox)
        sidebar_box.append(scrolled)

        split_view.set_sidebar(sidebar_page)

        # ── Content ──
        self.content_page = Adw.NavigationPage(title="Görünüm")
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content_page.set_child(self.content_box)

        self.content_header = Adw.HeaderBar()
        self.content_box.append(self.content_header)

        self.content_scroll = Gtk.ScrolledWindow()
        self.content_scroll.set_vexpand(True)
        self.content_box.append(self.content_scroll)

        split_view.set_content(self.content_page)

        # Sayfaları oluştur
        self.pages = {
            0: AppearancePage(self.settings, self._save),
            1: DesktopPage(self.settings, self._save),
            2: InputPage(self.settings, self._save),
            3: AboutPage(),
        }

        # İlk sayfayı göster
        self.content_scroll.set_child(self.pages[0])
        self.listbox.select_row(self.listbox.get_row_at_index(0))

        # CSS
        self._apply_css()

    def _on_category_selected(self, listbox, row):
        if row is None:
            return
        index = row.get_index()
        titles = {0: "Görünüm", 1: "Masaüstü", 2: "Giriş Cihazları", 3: "Hakkında"}
        self.content_page.set_title(titles.get(index, ""))

        if index in self.pages:
            self.content_scroll.set_child(self.pages[index])

    def _save(self):
        save_settings(self.settings)

    def _apply_css(self):
        css = b"""
        .about-logo {
            font-size: 72px;
            margin-bottom: 8px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class LumiereSettingsApp(Adw.Application):
    """Ana uygulama."""

    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        win = LumiereSettingsWindow(self)
        win.present()


def main():
    app = LumiereSettingsApp()
    app.run(None)


if __name__ == "__main__":
    main()
