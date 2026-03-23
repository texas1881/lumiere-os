#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Keyboard Shortcuts Cheatsheet        ║
# ╚══════════════════════════════════════════════════════════════╝
"""
Translucent overlay showing all keyboard shortcuts.
Launch: Super+? or lumiere-cheatsheet
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, Pango

SHORTCUTS = [
    ("Genel", [
        ("Super + Enter", "Terminal aç"),
        ("Super + D", "Uygulama başlatıcı"),
        ("Super + Q", "Pencereyi kapat"),
        ("Super + Shift + Q", "Oturumu sonlandır"),
        ("Super + L", "Ekranı kilitle"),
        ("Super + X", "Güç menüsü"),
        ("Super + ?", "Bu kısayol rehberi"),
    ]),
    ("Pencere Yönetimi", [
        ("Super + F", "Tam ekran"),
        ("Super + V", "Yüzen pencere"),
        ("Super + P", "Pseudotile"),
        ("Super + J", "Bölme yönünü değiştir"),
        ("Super + Yön tuşları", "Pencere odağı"),
        ("Super + Shift + Yön", "Pencereyi taşı"),
        ("Super + Ctrl + Yön", "Pencere boyutu"),
        ("Super + Fare sol", "Pencereyi sürükle"),
        ("Super + Fare sağ", "Pencereyi boyutlandır"),
    ]),
    ("Çalışma Alanları", [
        ("Super + 1-9", "Çalışma alanına git"),
        ("Super + Shift + 1-9", "Pencereyi taşı"),
        ("Super + S", "Özel alan (scratchpad)"),
        ("Super + Shift + S", "Özel alana taşı"),
        ("3 parmak kaydırma", "Alan değiştir (touchpad)"),
    ]),
    ("Araçlar", [
        ("Super + E", "Dosya yöneticisi"),
        ("Super + W", "Duvar kağıdı seçici"),
        ("Super + T", "Tema değiştir (koyu/açık)"),
        ("Super + I", "Ayarlar"),
        ("Super + M", "Sistem monitörü"),
        ("Super + Shift + V", "Pano geçmişi"),
        ("Print", "Ekran görüntüsü (alan)"),
        ("Shift + Print", "Tam ekran görüntüsü"),
        ("Super + Print", "Pencere görüntüsü"),
    ]),
    ("Multimedya", [
        ("Ses +/-", "Ses seviyesi (OSD)"),
        ("Ses Kapat", "Sessiz/Sesli"),
        ("Parlaklık +/-", "Ekran parlaklığı (OSD)"),
    ]),
]

# ─── Lumière Renk Paleti ────────────────────────────────────────
BG_COLOR = "rgba(13, 13, 20, 0.92)"
CARD_BG = "rgba(30, 30, 50, 0.85)"
GOLD = "#F5A623"
TEXT = "#E8E8F0"
SUBTLE = "#9090B0"

CSS = f"""
window {{
    background-color: {BG_COLOR};
}}
.cheatsheet-title {{
    font-size: 28px;
    font-weight: 700;
    color: {GOLD};
    margin-bottom: 8px;
}}
.cheatsheet-subtitle {{
    font-size: 13px;
    color: {SUBTLE};
    margin-bottom: 20px;
}}
.category-title {{
    font-size: 16px;
    font-weight: 700;
    color: {GOLD};
    margin-bottom: 6px;
    margin-top: 12px;
}}
.shortcut-card {{
    background-color: {CARD_BG};
    border-radius: 10px;
    padding: 14px;
    margin: 4px;
}}
.shortcut-key {{
    font-family: 'JetBrains Mono Nerd Font', monospace;
    font-size: 12px;
    font-weight: 700;
    color: {GOLD};
    background-color: rgba(245, 166, 35, 0.12);
    border-radius: 5px;
    padding: 3px 8px;
}}
.shortcut-desc {{
    font-size: 13px;
    color: {TEXT};
}}
"""


class CheatsheetWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Lumière Kısayollar")
        self.set_default_size(900, 680)
        self.set_resizable(True)

        # ESC ile kapat
        esc_controller = Gtk.EventControllerKey()
        esc_controller.connect("key-pressed", self._on_key)
        self.add_controller(esc_controller)

        # Ana scroll
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.set_margin_top(30)
        main_box.set_margin_bottom(30)
        main_box.set_margin_start(40)
        main_box.set_margin_end(40)

        # Başlık
        title = Gtk.Label(label="✦ Lumière OS Kısayolları")
        title.add_css_class("cheatsheet-title")
        main_box.append(title)

        subtitle = Gtk.Label(label="Kapatmak için ESC · Tüm kısayollar aşağıda")
        subtitle.add_css_class("cheatsheet-subtitle")
        main_box.append(subtitle)

        # 2 sütunlu grid
        columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        columns_box.set_homogeneous(True)

        left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        for i, (category, shortcuts) in enumerate(SHORTCUTS):
            col = left_col if i % 2 == 0 else right_col
            cat_label = Gtk.Label(label=category, xalign=0)
            cat_label.add_css_class("category-title")
            col.append(cat_label)

            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.add_css_class("shortcut-card")

            for key, desc in shortcuts:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                row.set_margin_top(3)
                row.set_margin_bottom(3)

                key_label = Gtk.Label(label=key)
                key_label.add_css_class("shortcut-key")
                row.append(key_label)

                desc_label = Gtk.Label(label=desc, xalign=0, hexpand=True)
                desc_label.add_css_class("shortcut-desc")
                row.append(desc_label)

                card.append(row)

            col.append(card)

        columns_box.append(left_col)
        columns_box.append(right_col)
        main_box.append(columns_box)

        scroll.set_child(main_box)
        self.set_content(scroll)

    def _on_key(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False


class CheatsheetApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.lumiere.cheatsheet")
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        win = CheatsheetWindow(app)
        win.present()


if __name__ == "__main__":
    app = CheatsheetApp()
    app.run()
