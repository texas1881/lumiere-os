#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Hoş Geldin Uygulaması               ║
# ╚══════════════════════════════════════════════════════════════╝
"""
lumiere-welcome: İlk açılışta kullanıcıyı karşılayan GTK4 uygulaması.

Özellikler:
  - Lumière OS tanıtımı
  - Hızlı bağlantılar (ayarlar, terminal, dosya yöneticisi)
  - Tema seçici
  - Başlangıçta göster/gösterme seçeneği
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib, Pango
import subprocess
import os

APP_ID = "os.lumiere.welcome"
VERSION = "0.1.0"
CONFIG_DIR = os.path.expanduser("~/.config/lumiere")
CONFIG_FILE = os.path.join(CONFIG_DIR, "welcome.conf")


class WelcomePage:
    """Tek bir karşılama sayfası."""
    def __init__(self, icon, title, description, button_label=None, button_action=None):
        self.icon = icon
        self.title = title
        self.description = description
        self.button_label = button_label
        self.button_action = button_action


PAGES = [
    WelcomePage(
        icon="✦",
        title="Lumière OS'a Hoş Geldiniz",
        description=(
            "Hızlı, güvenli ve estetik bir Linux deneyimine adım attınız.\n\n"
            "Lumière, Fransızca'da \"ışık\" demektir. Bu sistemde her şey "
            "aydınlık, şeffaf ve hızlı olacak şekilde tasarlandı."
        ),
    ),
    WelcomePage(
        icon="🖥️",
        title="Masaüstünüz",
        description=(
            "Hyprland tiling compositor ile güçlü bir Wayland masaüstü kullanıyorsunuz.\n\n"
            "• Super + Return → Terminal aç\n"
            "• Super + D → Uygulama başlatıcı\n"
            "• Super + Q → Pencereyi kapat\n"
            "• Super + 1-9 → Çalışma alanları\n"
            "• Super + V → Yüzen pencere"
        ),
    ),
    WelcomePage(
        icon="📦",
        title="Paket Yönetimi",
        description=(
            "Lumière OS, pacman paket yöneticisini kullanır.\n"
            "Daha kolay kullanım için lumiere-pkg aracını deneyebilirsiniz:\n\n"
            "• lumiere-pkg install <paket>\n"
            "• lumiere-pkg update\n"
            "• lumiere-pkg search <arama>\n"
            "• lumiere-pkg clean"
        ),
        button_label="Terminal'i Aç",
        button_action="kitty",
    ),
    WelcomePage(
        icon="⚙️",
        title="Özelleştirme",
        description=(
            "Lumière OS tamamen özelleştirilebilir:\n\n"
            "• ~/.config/hypr/ → Pencere yöneticisi\n"
            "• ~/.config/waybar/ → Panel\n"
            "• ~/.config/kitty/ → Terminal\n"
            "• ~/.config/starship/ → Prompt\n"
            "• ~/.config/gtk-4.0/ → GTK tema"
        ),
        button_label="Dosya Yöneticisini Aç",
        button_action="thunar ~/.config",
    ),
    WelcomePage(
        icon="🚀",
        title="Başlamaya Hazırsınız!",
        description=(
            "Lumière OS kullanıma hazır.\n\n"
            "Güncelleme: lumiere-pkg update\n"
            "Yardım: https://github.com/lumiere-os\n\n"
            "Işığı takip edin. ✦"
        ),
    ),
]


class LumiereWelcomeWindow(Adw.ApplicationWindow):
    """Ana hoş geldin penceresi."""

    def __init__(self, app):
        super().__init__(application=app, title="Lumière OS — Hoş Geldiniz")
        self.set_default_size(720, 540)
        self.set_resizable(False)
        self.current_page = 0

        # Ana kutu
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(self.main_box)

        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="✦ Lumière OS"))
        header.add_css_class("flat")
        self.main_box.append(header)

        # İçerik alanı
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.content_stack.set_transition_duration(300)
        self.main_box.append(self.content_stack)

        # Sayfaları oluştur
        for i, page in enumerate(PAGES):
            page_widget = self._create_page(page)
            self.content_stack.add_named(page_widget, f"page_{i}")

        # Alt navigasyon
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        nav_box.set_halign(Gtk.Align.CENTER)
        nav_box.set_margin_top(16)
        nav_box.set_margin_bottom(24)

        # Başlangıçta göster checkbox
        self.autostart_check = Gtk.CheckButton(label="Başlangıçta göster")
        self.autostart_check.set_active(True)
        self.autostart_check.set_halign(Gtk.Align.START)
        self.autostart_check.set_margin_start(24)

        # Geri butonu
        self.back_btn = Gtk.Button(label="← Geri")
        self.back_btn.connect("clicked", self._on_back)
        self.back_btn.add_css_class("flat")
        self.back_btn.set_sensitive(False)

        # Sayfa göstergesi
        self.page_label = Gtk.Label()
        self.page_label.add_css_class("dim-label")
        self._update_page_label()

        # İleri butonu
        self.next_btn = Gtk.Button(label="İleri →")
        self.next_btn.connect("clicked", self._on_next)
        self.next_btn.add_css_class("suggested-action")

        nav_box.append(self.back_btn)
        nav_box.append(self.page_label)
        nav_box.append(self.next_btn)

        # Alt bar
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bottom_box.append(self.autostart_check)
        bottom_box.append(nav_box)
        nav_box.set_hexpand(True)

        self.main_box.append(bottom_box)

        # CSS
        self._apply_css()

    def _create_page(self, page: WelcomePage) -> Gtk.Widget:
        """Bir karşılama sayfası oluştur."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_start(48)
        box.set_margin_end(48)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_vexpand(True)

        # İkon
        icon_label = Gtk.Label(label=page.icon)
        icon_label.add_css_class("welcome-icon")
        box.append(icon_label)

        # Başlık
        title_label = Gtk.Label(label=page.title)
        title_label.add_css_class("welcome-title")
        title_label.set_wrap(True)
        title_label.set_justify(Gtk.Justification.CENTER)
        box.append(title_label)

        # Açıklama
        desc_label = Gtk.Label(label=page.description)
        desc_label.add_css_class("welcome-description")
        desc_label.set_wrap(True)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.set_max_width_chars(60)
        box.append(desc_label)

        # Aksiyon butonu (opsiyonel)
        if page.button_label:
            action_btn = Gtk.Button(label=page.button_label)
            action_btn.add_css_class("pill")
            action_btn.add_css_class("suggested-action")
            action_btn.set_halign(Gtk.Align.CENTER)
            action_btn.set_margin_top(8)
            action_btn.connect("clicked", lambda _, cmd=page.button_action: self._run_action(cmd))
            box.append(action_btn)

        return box

    def _apply_css(self):
        """CSS stillerini uygula."""
        css = b"""
        .welcome-icon {
            font-size: 64px;
            margin-bottom: 8px;
        }
        .welcome-title {
            font-size: 24px;
            font-weight: 700;
            color: #F5A623;
            margin-bottom: 8px;
        }
        .welcome-description {
            font-size: 14px;
            color: #A9A6B8;
            line-height: 1.6;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _update_page_label(self):
        """Sayfa numarasını güncelle."""
        self.page_label.set_text(f"{self.current_page + 1} / {len(PAGES)}")

    def _on_next(self, _btn):
        """Sonraki sayfa."""
        if self.current_page < len(PAGES) - 1:
            self.current_page += 1
            self.content_stack.set_visible_child_name(f"page_{self.current_page}")
            self._update_page_label()
            self.back_btn.set_sensitive(True)

            if self.current_page == len(PAGES) - 1:
                self.next_btn.set_label("Bitir ✓")
        else:
            # Son sayfa — kapat
            self._save_preference()
            self.close()

    def _on_back(self, _btn):
        """Önceki sayfa."""
        if self.current_page > 0:
            self.current_page -= 1
            self.content_stack.set_visible_child_name(f"page_{self.current_page}")
            self._update_page_label()
            self.next_btn.set_label("İleri →")

            if self.current_page == 0:
                self.back_btn.set_sensitive(False)

    def _run_action(self, command):
        """Bir komutu arka planda çalıştır."""
        try:
            subprocess.Popen(command.split(), start_new_session=True)
        except Exception as e:
            print(f"Komut çalıştırılamadı: {e}")

    def _save_preference(self):
        """Başlangıçta göster/gösterme tercihini kaydet."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        show_on_startup = self.autostart_check.get_active()
        with open(CONFIG_FILE, "w") as f:
            f.write(f"show_on_startup={str(show_on_startup).lower()}\n")

        # Autostart desktop entry'si yönet
        autostart_dir = os.path.expanduser("~/.config/autostart")
        autostart_file = os.path.join(autostart_dir, "lumiere-welcome.desktop")

        if show_on_startup:
            os.makedirs(autostart_dir, exist_ok=True)
            with open(autostart_file, "w") as f:
                f.write(
                    "[Desktop Entry]\n"
                    "Type=Application\n"
                    "Name=Lumière Welcome\n"
                    "Exec=lumiere-welcome\n"
                    "Icon=lumiere-welcome\n"
                    "Comment=Lumière OS Hoş Geldin\n"
                    "Categories=Utility;\n"
                    "StartupNotify=false\n"
                    "X-GNOME-Autostart-enabled=true\n"
                )
        else:
            if os.path.exists(autostart_file):
                os.remove(autostart_file)


class LumiereWelcomeApp(Adw.Application):
    """Ana uygulama"""

    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        # Tercihi kontrol et
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                content = f.read()
                if "show_on_startup=false" in content:
                    # --force parametresi olmadan çalıştırıldıysa kapat
                    import sys
                    if "--force" not in sys.argv:
                        print("ℹ️  Hoş geldin ekranı devre dışı. --force ile açılabilir.")
                        return

        win = LumiereWelcomeWindow(self)
        win.present()


def main():
    app = LumiereWelcomeApp()
    app.run(None)


if __name__ == "__main__":
    main()
