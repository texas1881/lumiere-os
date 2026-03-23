#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║       ✦ Lumière OS — Gelişmiş Kurulum Sihirbazı              ║
# ╚══════════════════════════════════════════════════════════════╝
"""
lumiere-installer: GTK4/Adwaita tabanlı grafik kurulum sihirbazı.

Adımlar:
  1. Hoş Geldiniz + Dil seçimi
  2. Klavye düzeni
  3. Disk bölümleme (otomatik / manuel)
  4. Kullanıcı bilgileri
  5. Özet
  6. Kurulum ilerlemesi
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import subprocess
import json
import threading
import math

APP_ID = "os.lumiere.installer"
VERSION = "0.2.0"

# — Lumière Renk Paleti —
GOLD = "#F5A623"
GOLD_LIGHT = "#FFD080"
BG_SURFACE = "#13131E"
BG_OVERLAY = "#1A1A2E"
FG_MUTED = "#A9A6B8"


def run_cmd(cmd, check=False):
    """Komut çalıştır ve çıktıyı al."""
    try:
        result = subprocess.run(
            cmd, shell=isinstance(cmd, str),
            capture_output=True, text=True, timeout=30
        )
        if check and result.returncode != 0:
            return None
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def get_disks():
    """Disk ve bölüm bilgilerini JSON olarak al."""
    output = run_cmd(["lsblk", "-J", "-b", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL"])
    if output:
        try:
            data = json.loads(output)
            return data.get("blockdevices", [])
        except json.JSONDecodeError:
            pass
    return []


def format_size(size_bytes):
    """Byte'ı okunabilir birime çevir."""
    if size_bytes is None:
        return "?"
    size = int(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


class DiskVisualizer(Gtk.DrawingArea):
    """Disk bölümlerini görselleştiren widget."""

    def __init__(self):
        super().__init__()
        self.set_size_request(-1, 60)
        self.set_hexpand(True)
        self.disk_data = None
        self.set_draw_func(self._draw)

    def set_disk(self, disk):
        self.disk_data = disk
        self.queue_draw()

    def _draw(self, area, cr, width, height):
        if not self.disk_data:
            return

        total_size = int(self.disk_data.get("size", 1))
        if total_size == 0:
            total_size = 1

        children = self.disk_data.get("children", [])
        partition_colors = [
            (0.961, 0.651, 0.137),  # Gold
            (0.376, 0.647, 0.980),  # Blue
            (0.290, 0.871, 0.502),  # Green
            (0.753, 0.518, 0.988),  # Purple
            (0.133, 0.827, 0.933),  # Cyan
            (0.973, 0.443, 0.443),  # Red
        ]

        # Arkaplan
        cr.set_source_rgba(0.165, 0.165, 0.259, 0.6)
        self._rounded_rect(cr, 0, 0, width, height - 16, 8)
        cr.fill()

        x_offset = 2
        bar_height = height - 20
        usable_width = width - 4

        if not children:
            # Bölümlenmemiş
            cr.set_source_rgba(0.42, 0.408, 0.502, 0.4)
            self._rounded_rect(cr, x_offset, 2, usable_width, bar_height - 4, 6)
            cr.fill()

            cr.set_source_rgb(0.91, 0.902, 0.941)
            cr.set_font_size(11)
            cr.select_font_face("Inter", 0, 0)
            text = "Bölümlenmemiş Alan"
            extents = cr.text_extents(text)
            cr.move_to(width / 2 - extents.width / 2, bar_height / 2 + 4)
            cr.show_text(text)
        else:
            for i, part in enumerate(children):
                part_size = int(part.get("size", 0))
                part_width = max(20, (part_size / total_size) * usable_width)

                r, g, b = partition_colors[i % len(partition_colors)]
                cr.set_source_rgba(r, g, b, 0.8)
                self._rounded_rect(cr, x_offset, 2, part_width - 2, bar_height - 4, 4)
                cr.fill()

                # Etiket
                if part_width > 50:
                    cr.set_source_rgb(1, 1, 1)
                    cr.set_font_size(9)
                    label = part.get("name", "?")
                    extents = cr.text_extents(label)
                    if extents.width < part_width - 8:
                        cr.move_to(x_offset + (part_width - extents.width) / 2, bar_height / 2 + 4)
                        cr.show_text(label)

                x_offset += part_width

        # Disk adı altında
        cr.set_source_rgb(0.663, 0.651, 0.753)
        cr.set_font_size(10)
        disk_label = f"/dev/{self.disk_data.get('name', '?')} — {format_size(self.disk_data.get('size', 0))}"
        if self.disk_data.get("model"):
            disk_label += f" ({self.disk_data['model'].strip()})"
        cr.move_to(4, height - 2)
        cr.show_text(disk_label)

    def _rounded_rect(self, cr, x, y, w, h, r):
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()


# ═══════════════════════════════════════════════════════════════
#  Wizard Sayfaları
# ═══════════════════════════════════════════════════════════════

class WelcomePage(Gtk.Box):
    """Hoş geldiniz sayfası."""

    def __init__(self, config):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.config = config
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_vexpand(True)

        logo = Gtk.Label(label="✦")
        logo.add_css_class("installer-logo")
        self.append(logo)

        title = Gtk.Label(label="Lumière OS Kurulumu")
        title.add_css_class("installer-title")
        self.append(title)

        desc = Gtk.Label(label="Hızlı, güvenli ve estetik bir Linux deneyimine hoş geldiniz.\nKurulum sihirbazı sizi adım adım yönlendirecektir.")
        desc.set_wrap(True)
        desc.set_justify(Gtk.Justification.CENTER)
        desc.add_css_class("dim-label")
        desc.set_max_width_chars(50)
        self.append(desc)

        # Dil seçimi
        lang_group = Adw.PreferencesGroup(title="Sistem Dili")
        lang_group.set_margin_top(24)

        lang_row = Adw.ActionRow(title="Dil", subtitle="Kurulum ve sistem dili")
        self.lang_combo = Gtk.DropDown.new_from_strings([
            "Türkçe (tr_TR)", "English (en_US)", "Deutsch (de_DE)",
            "Français (fr_FR)", "Español (es_ES)"
        ])
        self.lang_combo.set_valign(Gtk.Align.CENTER)
        lang_row.add_suffix(self.lang_combo)
        lang_group.add(lang_row)
        self.append(lang_group)

    def collect(self):
        locales = ["tr_TR.UTF-8", "en_US.UTF-8", "de_DE.UTF-8", "fr_FR.UTF-8", "es_ES.UTF-8"]
        self.config["locale"] = locales[self.lang_combo.get_selected()]


class KeyboardPage(Gtk.Box):
    """Klavye düzeni sayfası."""

    def __init__(self, config):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.config = config
        self.set_margin_start(32)
        self.set_margin_end(32)
        self.set_margin_top(24)

        title = Gtk.Label(label="Klavye Düzeni")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        kb_group = Adw.PreferencesGroup()

        layouts = [
            ("tr", "Türkçe Q"), ("us", "İngilizce (US)"),
            ("de", "Almanca"), ("fr", "Fransızca"),
            ("es", "İspanyolca"), ("ru", "Rusça"),
        ]

        self.layout_combo = Gtk.DropDown.new_from_strings([lay[1] for lay in layouts])
        self.layout_codes = [lay[0] for lay in layouts]

        layout_row = Adw.ActionRow(title="Düzen", subtitle="Klavye tuş yerleşimi")
        self.layout_combo.set_valign(Gtk.Align.CENTER)
        layout_row.add_suffix(self.layout_combo)
        kb_group.add(layout_row)

        self.append(kb_group)

        # Test alanı
        test_group = Adw.PreferencesGroup(title="Test Alanı")
        test_entry = Gtk.Entry()
        test_entry.set_placeholder_text("Klavyenizi burada test edebilirsiniz...")
        test_entry.set_margin_start(12)
        test_entry.set_margin_end(12)
        test_entry.set_margin_top(8)
        test_entry.set_margin_bottom(8)
        test_group.add(test_entry)
        self.append(test_group)

    def collect(self):
        self.config["kb_layout"] = self.layout_codes[self.layout_combo.get_selected()]


class DiskPage(Gtk.Box):
    """Disk bölümleme sayfası."""

    def __init__(self, config):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.config = config
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(16)

        title = Gtk.Label(label="Disk Bölümleme")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        desc = Gtk.Label(label="Lumière OS'u kurmak için bir disk seçin. Otomatik bölümleme önerilir.")
        desc.set_halign(Gtk.Align.START)
        desc.add_css_class("dim-label")
        self.append(desc)

        # Bölümleme modu
        mode_group = Adw.PreferencesGroup(title="Bölümleme Modu")

        self.auto_radio = Gtk.CheckButton(label="Otomatik Bölümleme (Önerilen)")
        self.auto_radio.set_active(True)
        auto_row = Adw.ActionRow(title="Otomatik", subtitle="Disk otomatik olarak EFI + BTRFS + Swap olarak bölümlenir")
        auto_row.add_prefix(self.auto_radio)
        auto_row.set_activatable_widget(self.auto_radio)
        mode_group.add(auto_row)

        self.manual_radio = Gtk.CheckButton(label="Manuel Bölümleme")
        self.manual_radio.set_group(self.auto_radio)
        manual_row = Adw.ActionRow(title="Manuel", subtitle="Kendi bölümlerinizi oluşturun ve yapılandırın")
        manual_row.add_prefix(self.manual_radio)
        manual_row.set_activatable_widget(self.manual_radio)
        mode_group.add(manual_row)

        self.append(mode_group)

        # Disk listesi
        disk_group = Adw.PreferencesGroup(title="Disk Seçimi")

        self.disk_visualizer = DiskVisualizer()
        disk_group.add(self.disk_visualizer)

        self.disk_listbox = Gtk.ListBox()
        self.disk_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.disk_listbox.add_css_class("boxed-list")
        self.disk_listbox.connect("row-selected", self._on_disk_selected)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_max_content_height(200)
        scrolled.set_propagate_natural_height(True)
        scrolled.set_child(self.disk_listbox)
        disk_group.add(scrolled)

        self.append(disk_group)

        # Diskleri yükle
        self._load_disks()

    def _load_disks(self):
        disks = get_disks()
        self.available_disks = []

        for dev in disks:
            if dev.get("type") == "disk":
                self.available_disks.append(dev)
                name = dev.get("name", "?")
                size = format_size(dev.get("size"))
                model = dev.get("model", "").strip() or "Bilinmeyen Disk"
                parts = len(dev.get("children", []))

                row = Adw.ActionRow(
                    title=f"/dev/{name}",
                    subtitle=f"{model} — {size} — {parts} bölüm"
                )
                row.add_prefix(Gtk.Label(label="💾"))
                self.disk_listbox.append(row)

        if self.available_disks:
            self.disk_listbox.select_row(self.disk_listbox.get_row_at_index(0))

    def _on_disk_selected(self, listbox, row):
        if row:
            idx = row.get_index()
            if idx < len(self.available_disks):
                self.disk_visualizer.set_disk(self.available_disks[idx])

    def collect(self):
        row = self.disk_listbox.get_selected_row()
        if row:
            idx = row.get_index()
            if idx < len(self.available_disks):
                self.config["target_disk"] = f"/dev/{self.available_disks[idx]['name']}"
        self.config["auto_partition"] = self.auto_radio.get_active()


class UserPage(Gtk.Box):
    """Kullanıcı bilgileri sayfası."""

    def __init__(self, config):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.config = config
        self.set_margin_start(32)
        self.set_margin_end(32)
        self.set_margin_top(24)

        title = Gtk.Label(label="Kullanıcı Bilgileri")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        user_group = Adw.PreferencesGroup(title="Kullanıcı Hesabı")

        # Hostname
        hostname_row = Adw.EntryRow(title="Bilgisayar Adı")
        hostname_row.set_text("lumiere")
        self.hostname_entry = hostname_row
        user_group.add(hostname_row)

        # Kullanıcı adı
        username_row = Adw.EntryRow(title="Kullanıcı Adı")
        username_row.set_text("")
        self.username_entry = username_row
        user_group.add(username_row)

        # Şifre
        password_row = Adw.PasswordEntryRow(title="Şifre")
        self.password_entry = password_row
        user_group.add(password_row)

        # Şifre tekrar
        password2_row = Adw.PasswordEntryRow(title="Şifre (Tekrar)")
        self.password2_entry = password2_row
        user_group.add(password2_row)

        self.append(user_group)

        # Root şifre
        root_group = Adw.PreferencesGroup(title="Yönetici (Root)")

        self.same_password_check = Gtk.CheckButton(label="Kullanıcı ile aynı şifre")
        self.same_password_check.set_active(True)
        same_row = Adw.ActionRow(title="Root Şifresi")
        same_row.add_suffix(self.same_password_check)
        root_group.add(same_row)

        self.append(root_group)

    def collect(self):
        self.config["hostname"] = self.hostname_entry.get_text() or "lumiere"
        self.config["username"] = self.username_entry.get_text() or "user"
        self.config["password"] = self.password_entry.get_text()
        self.config["root_same_password"] = self.same_password_check.get_active()


class SummaryPage(Gtk.Box):
    """Kurulum özeti sayfası."""

    def __init__(self, config):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.config = config
        self.set_margin_start(32)
        self.set_margin_end(32)
        self.set_margin_top(24)

        title = Gtk.Label(label="Kurulum Özeti")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        self.summary_group = Adw.PreferencesGroup(title="Seçimleriniz")
        self.append(self.summary_group)

        warning = Gtk.Label()
        warning.set_markup(
            '<span foreground="#F87171" weight="bold">⚠ Dikkat:</span> '
            '<span foreground="#A9A6B8">Hedef disk tamamen silinecektir. '
            'Devam etmeden önce verilerinizi yedekleyin.</span>'
        )
        warning.set_wrap(True)
        warning.set_margin_top(16)
        self.append(warning)

    def refresh(self):
        """Özet bilgilerini güncelle."""
        # Eski satırları temizle
        while True:
            child = self.summary_group.get_first_child()
            if child is None:
                break
            # Skip the title
            if isinstance(child, Adw.ActionRow):
                self.summary_group.remove(child)
            else:
                break

        rows = [
            ("Dil", self.config.get("locale", "tr_TR.UTF-8")),
            ("Klavye", self.config.get("kb_layout", "tr")),
            ("Hedef Disk", self.config.get("target_disk", "Seçilmedi")),
            ("Bölümleme", "Otomatik" if self.config.get("auto_partition", True) else "Manuel"),
            ("Bilgisayar Adı", self.config.get("hostname", "lumiere")),
            ("Kullanıcı", self.config.get("username", "user")),
        ]

        for title, subtitle in rows:
            row = Adw.ActionRow(title=title, subtitle=subtitle)
            self.summary_group.add(row)


class InstallPage(Gtk.Box):
    """Kurulum ilerleme sayfası."""

    def __init__(self, config):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.config = config
        self.set_margin_start(32)
        self.set_margin_end(32)
        self.set_margin_top(48)
        self.set_valign(Gtk.Align.CENTER)

        logo = Gtk.Label(label="✦")
        logo.add_css_class("installer-logo")
        self.append(logo)

        self.status_label = Gtk.Label(label="Kurulum başlatılıyor...")
        self.status_label.add_css_class("title-2")
        self.append(self.status_label)

        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        self.progress.set_margin_top(16)
        self.append(self.progress)

        self.detail_label = Gtk.Label(label="")
        self.detail_label.add_css_class("dim-label")
        self.detail_label.set_margin_top(8)
        self.append(self.detail_label)

    def start_install(self, on_complete):
        """Kurulumu arka planda başlat."""
        self.on_complete = on_complete
        thread = threading.Thread(target=self._run_install, daemon=True)
        thread.start()

    def _update_ui(self, fraction, status, detail=""):
        GLib.idle_add(self.progress.set_fraction, fraction)
        GLib.idle_add(self.progress.set_text, f"{int(fraction * 100)}%")
        GLib.idle_add(self.status_label.set_text, status)
        GLib.idle_add(self.detail_label.set_text, detail)

    def _run_install(self):
        """Kurulum adımlarını çalıştır."""
        steps = [
            (0.05, "Disk hazırlanıyor...", "Bölümler oluşturuluyor"),
            (0.15, "Dosya sistemi oluşturuluyor...", "BTRFS formatlanıyor"),
            (0.20, "Alt birimler oluşturuluyor...", "@, @home, @snapshots, @var_log"),
            (0.25, "Bağlama noktaları ayarlanıyor...", "mount işlemleri"),
            (0.40, "Temel sistem kuruluyor...", "pacstrap çalıştırılıyor"),
            (0.60, "Sistem yapılandırılıyor...", "fstab, hostname, locale"),
            (0.70, "Önyükleyici kuruluyor...", "systemd-boot yapılandırması"),
            (0.80, "Lumière paketleri kuruluyor...", "Masaüstü ortamı"),
            (0.90, "Kullanıcı oluşturuluyor...", self.config.get("username", "user")),
            (0.95, "Son ayarlamalar...", "Servisler etkinleştiriliyor"),
            (1.00, "Kurulum tamamlandı!", "Bilgisayarınızı yeniden başlatabilirsiniz"),
        ]

        # install_script varsayılan konum

        for fraction, status, detail in steps:
            self._update_ui(fraction, status, detail)

            # Gerçek kurulumda her adım install.sh'nin ilgili fonksiyonunu çağırır
            # Şimdilik simüle ediyoruz
            import time
            time.sleep(1.5)

        GLib.idle_add(self.on_complete)


# ═══════════════════════════════════════════════════════════════
#  Ana Pencere
# ═══════════════════════════════════════════════════════════════

class LumiereInstallerWindow(Adw.ApplicationWindow):
    """Ana installer penceresi."""

    def __init__(self, app):
        super().__init__(application=app, title="Lumière OS Kurulumu")
        self.set_default_size(820, 620)
        self.set_resizable(False)

        self.config = {}
        self.current_step = 0

        # Ana kutu
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)

        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="✦ Lumière OS Kurulumu"))
        header.add_css_class("flat")
        main_box.append(header)

        # Adım göstergesi
        self.step_indicator = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.step_indicator.set_halign(Gtk.Align.CENTER)
        self.step_indicator.set_margin_top(8)
        self.step_indicator.set_margin_bottom(8)

        step_names = ["Hoş Geldiniz", "Klavye", "Disk", "Kullanıcı", "Özet", "Kurulum"]
        self.step_labels = []
        for i, name in enumerate(step_names):
            label = Gtk.Label(label=name)
            label.add_css_class("caption")
            if i == 0:
                label.add_css_class("accent")
            else:
                label.add_css_class("dim-label")
            self.step_labels.append(label)
            self.step_indicator.append(label)

            if i < len(step_names) - 1:
                sep = Gtk.Label(label="→")
                sep.add_css_class("dim-label")
                self.step_indicator.append(sep)

        main_box.append(self.step_indicator)
        main_box.append(Gtk.Separator())

        # İçerik
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)
        self.stack.set_vexpand(True)

        # Sayfaları oluştur
        self.pages = [
            WelcomePage(self.config),
            KeyboardPage(self.config),
            DiskPage(self.config),
            UserPage(self.config),
            SummaryPage(self.config),
            InstallPage(self.config),
        ]

        for i, page in enumerate(self.pages):
            self.stack.add_named(page, f"step_{i}")

        main_box.append(self.stack)

        # Navigasyon
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        nav_box.set_halign(Gtk.Align.END)
        nav_box.set_margin_top(12)
        nav_box.set_margin_bottom(16)
        nav_box.set_margin_end(24)

        self.back_btn = Gtk.Button(label="← Geri")
        self.back_btn.add_css_class("flat")
        self.back_btn.connect("clicked", self._on_back)
        self.back_btn.set_sensitive(False)
        nav_box.append(self.back_btn)

        self.next_btn = Gtk.Button(label="İleri →")
        self.next_btn.add_css_class("suggested-action")
        self.next_btn.connect("clicked", self._on_next)
        nav_box.append(self.next_btn)

        main_box.append(Gtk.Separator())
        main_box.append(nav_box)

        # CSS
        self._apply_css()

    def _on_next(self, _btn):
        # Mevcut sayfanın verilerini topla
        self.pages[self.current_step].collect()

        if self.current_step < len(self.pages) - 1:
            self.current_step += 1
            self.stack.set_visible_child_name(f"step_{self.current_step}")
            self.back_btn.set_sensitive(True)

            # Adım göstergesini güncelle
            self._update_step_indicator()

            if self.current_step == 4:
                # Özet sayfası — verileri göster
                self.pages[4].refresh()
                self.next_btn.set_label("Kur ✦")
                self.next_btn.add_css_class("destructive-action")

            elif self.current_step == 5:
                # Kurulumu başlat
                self.next_btn.set_sensitive(False)
                self.back_btn.set_sensitive(False)
                self.pages[5].start_install(self._on_install_complete)

    def _on_back(self, _btn):
        if self.current_step > 0:
            self.current_step -= 1
            self.stack.set_visible_child_name(f"step_{self.current_step}")

            if self.current_step == 0:
                self.back_btn.set_sensitive(False)

            self.next_btn.set_label("İleri →")
            self.next_btn.remove_css_class("destructive-action")
            self._update_step_indicator()

    def _on_install_complete(self):
        self.next_btn.set_label("Yeniden Başlat")
        self.next_btn.set_sensitive(True)
        self.next_btn.remove_css_class("destructive-action")
        self.next_btn.add_css_class("suggested-action")
        self.next_btn.disconnect_by_func(self._on_next)
        self.next_btn.connect("clicked", self._on_reboot)

    def _on_reboot(self, _btn):
        try:
            subprocess.run(["systemctl", "reboot"])
        except FileNotFoundError:
            pass

    def _update_step_indicator(self):
        for i, label in enumerate(self.step_labels):
            label.remove_css_class("accent")
            label.remove_css_class("dim-label")
            if i == self.current_step:
                label.add_css_class("accent")
            elif i < self.current_step:
                pass  # Tamamlanan adımlar normal görünür
            else:
                label.add_css_class("dim-label")

    def _apply_css(self):
        css = b"""
        .installer-logo {
            font-size: 64px;
            margin-bottom: 8px;
        }
        .installer-title {
            font-size: 28px;
            font-weight: 700;
            color: #F5A623;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class LumiereInstallerApp(Adw.Application):
    """Ana uygulama."""

    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        win = LumiereInstallerWindow(self)
        win.present()


def main():
    app = LumiereInstallerApp()
    app.run(None)


if __name__ == "__main__":
    main()
