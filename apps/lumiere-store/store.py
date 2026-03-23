#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║       ✦ Lumière App Store — Flatpak Uygulama Mağazası        ║
# ╚══════════════════════════════════════════════════════════════╝
"""
lumiere-store: GTK4/Adwaita flatpak tabanlı uygulama mağazası.

Özellikler:
  - Flatpak uygulama arama ve yükleme
  - Kategorizasyon
  - Uygulama detay sayfası
  - Toplu güncelleme
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Pango
import subprocess
import threading

APP_ID = "os.lumiere.store"
VERSION = "0.3.0"

CATEGORIES = {
    "all": ("Tümü", "view-app-grid-symbolic"),
    "productivity": ("Üretkenlik", "x-office-document-symbolic"),
    "internet": ("İnternet", "network-wireless-symbolic"),
    "development": ("Geliştirme", "utilities-terminal-symbolic"),
    "games": ("Oyunlar", "input-gaming-symbolic"),
    "graphics": ("Grafik", "applications-graphics-symbolic"),
    "multimedia": ("Multimedya", "applications-multimedia-symbolic"),
    "utilities": ("Araçlar", "applications-utilities-symbolic"),
}


def run_flatpak(args, timeout=30):
    """Flatpak komutunu çalıştır."""
    try:
        result = subprocess.run(
            ["flatpak"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "", False


def search_apps(query):
    """Flatpak uygulamalarını ara."""
    output, ok = run_flatpak(["search", "--columns=application,name,description,version", query])
    if not ok or not output:
        return []

    apps = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            apps.append({
                "id": parts[0].strip(),
                "name": parts[1].strip(),
                "description": parts[2].strip() if len(parts) > 2 else "",
                "version": parts[3].strip() if len(parts) > 3 else "",
            })
    return apps


def list_installed():
    """Yüklü uygulamaları listele."""
    output, ok = run_flatpak(["list", "--app", "--columns=application,name,version,size"])
    if not ok:
        return []

    apps = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            apps.append({
                "id": parts[0].strip(),
                "name": parts[1].strip(),
                "version": parts[2].strip() if len(parts) > 2 else "",
                "size": parts[3].strip() if len(parts) > 3 else "",
            })
    return apps


def check_updates():
    """Güncelleme bekleyen uygulamaları kontrol et."""
    output, ok = run_flatpak(["remote-ls", "--updates", "--columns=application,name"])
    if not ok:
        return []

    updates = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            updates.append({
                "id": parts[0].strip(),
                "name": parts[1].strip(),
            })
    return updates


class AppCard(Gtk.Box):
    """Uygulama kartı widget'ı."""

    def __init__(self, app_data, installed=False, on_action=None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.app_data = app_data

        # Uygulama bilgisi
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)

        name_label = Gtk.Label(label=app_data.get("name", "?"))
        name_label.add_css_class("heading")
        name_label.set_halign(Gtk.Align.START)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        info_box.append(name_label)

        desc = app_data.get("description", app_data.get("id", ""))
        desc_label = Gtk.Label(label=desc)
        desc_label.add_css_class("dim-label")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_ellipsize(Pango.EllipsizeMode.END)
        desc_label.set_max_width_chars(50)
        info_box.append(desc_label)

        if app_data.get("version"):
            ver_label = Gtk.Label(label=f"v{app_data['version']}")
            ver_label.add_css_class("caption")
            ver_label.add_css_class("dim-label")
            ver_label.set_halign(Gtk.Align.START)
            info_box.append(ver_label)

        self.append(info_box)

        # Aksiyon butonu
        if installed:
            btn = Gtk.Button(label="Kaldır")
            btn.add_css_class("destructive-action")
        else:
            btn = Gtk.Button(label="Yükle")
            btn.add_css_class("suggested-action")

        btn.set_valign(Gtk.Align.CENTER)
        if on_action:
            btn.connect("clicked", lambda b: on_action(app_data, installed, b))
        self.append(btn)


class LumiereStoreWindow(Adw.ApplicationWindow):
    """Ana mağaza penceresi."""

    def __init__(self, app):
        super().__init__(application=app, title="Lumière App Store")
        self.set_default_size(900, 650)

        self.installed_ids = set()

        # Ana layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)

        # Header
        header = Adw.HeaderBar()

        # Arama
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Uygulama ara...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("activate", self._on_search)
        header.set_title_widget(self.search_entry)

        # Güncelle butonu
        update_btn = Gtk.Button(icon_name="software-update-available-symbolic")
        update_btn.set_tooltip_text("Güncellemeleri Kontrol Et")
        update_btn.connect("clicked", self._on_check_updates)
        header.pack_end(update_btn)

        main_box.append(header)

        # Split view
        split = Adw.NavigationSplitView()

        # Sidebar — kategoriler
        sidebar_page = Adw.NavigationPage(title="Kategoriler")
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        cat_list = Gtk.ListBox()
        cat_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        cat_list.add_css_class("navigation-sidebar")
        cat_list.connect("row-selected", self._on_category_selected)

        for key, (name, icon) in CATEGORIES.items():
            row = Adw.ActionRow(title=name)
            row.add_prefix(Gtk.Image.new_from_icon_name(icon))
            row._category_key = key
            cat_list.append(row)

        # Yüklü uygulamalar
        installed_row = Adw.ActionRow(title="Yüklü Uygulamalar")
        installed_row.add_prefix(Gtk.Image.new_from_icon_name("emblem-ok-symbolic"))
        installed_row._category_key = "installed"
        cat_list.append(installed_row)

        sidebar_box.append(cat_list)
        sidebar_page.set_child(sidebar_box)
        split.set_sidebar(sidebar_page)

        # Content
        content_page = Adw.NavigationPage(title="Uygulamalar")
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.status_label = Gtk.Label(label="✦ Uygulama aramak için yukarıdaki arama kutusunu kullanın")
        self.status_label.add_css_class("dim-label")
        self.status_label.set_margin_top(48)
        self.content_box.append(self.status_label)

        self.app_list_scroll = Gtk.ScrolledWindow()
        self.app_list_scroll.set_vexpand(True)

        self.app_list = Gtk.ListBox()
        self.app_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.app_list.add_css_class("boxed-list")
        self.app_list_scroll.set_child(self.app_list)
        self.content_box.append(self.app_list_scroll)

        content_page.set_child(self.content_box)
        split.set_content(content_page)

        main_box.append(split)

        # Yüklü uygulamaları yükle
        self._load_installed()

    def _load_installed(self):
        """Yüklü uygulama ID'lerini cache et."""
        def worker():
            installed = list_installed()
            self.installed_ids = {a["id"] for a in installed}
            self._installed_list = installed

        threading.Thread(target=worker, daemon=True).start()

    def _on_search(self, entry):
        query = entry.get_text().strip()
        if not query:
            return

        self.status_label.set_text("Aranıyor...")
        self._clear_list()

        def worker():
            results = search_apps(query)
            GLib.idle_add(self._populate_results, results)

        threading.Thread(target=worker, daemon=True).start()

    def _on_category_selected(self, listbox, row):
        if row is None:
            return

        key = row._category_key
        if key == "installed":
            self._show_installed()
        elif key == "all":
            self.status_label.set_text("✦ Arama kutusunu kullanarak uygulama bulun")
            self._clear_list()

    def _show_installed(self):
        self._clear_list()
        self.status_label.set_text("Yüklü uygulamalar yükleniyor...")

        def worker():
            installed = list_installed()
            GLib.idle_add(self._populate_installed, installed)

        threading.Thread(target=worker, daemon=True).start()

    def _populate_results(self, apps):
        self._clear_list()
        if not apps:
            self.status_label.set_text("Sonuç bulunamadı.")
            return

        self.status_label.set_text(f"{len(apps)} uygulama bulundu")

        for app in apps:
            installed = app["id"] in self.installed_ids
            card = AppCard(app, installed=installed, on_action=self._on_app_action)
            self.app_list.append(card)

    def _populate_installed(self, apps):
        self._clear_list()
        self.status_label.set_text(f"{len(apps)} yüklü uygulama")

        for app in apps:
            card = AppCard(app, installed=True, on_action=self._on_app_action)
            self.app_list.append(card)

    def _on_app_action(self, app_data, is_installed, button):
        app_id = app_data["id"]
        button.set_sensitive(False)

        def worker():
            if is_installed:
                run_flatpak(["uninstall", "-y", app_id], timeout=120)
                GLib.idle_add(button.set_label, "Kaldırıldı ✓")
            else:
                run_flatpak(["install", "-y", app_id], timeout=300)
                GLib.idle_add(button.set_label, "Yüklendi ✓")

            self._load_installed()

        threading.Thread(target=worker, daemon=True).start()

    def _on_check_updates(self, _btn):
        self._clear_list()
        self.status_label.set_text("Güncellemeler kontrol ediliyor...")

        def worker():
            updates = check_updates()
            GLib.idle_add(self._show_updates, updates)

        threading.Thread(target=worker, daemon=True).start()

    def _show_updates(self, updates):
        self._clear_list()
        if not updates:
            self.status_label.set_text("✓ Tüm uygulamalar güncel!")
            return

        self.status_label.set_text(f"{len(updates)} güncelleme mevcut")

        # Tümünü güncelle butonu
        update_all_btn = Gtk.Button(label=f"✦ Tümünü Güncelle ({len(updates)})")
        update_all_btn.add_css_class("suggested-action")
        update_all_btn.set_margin_start(12)
        update_all_btn.set_margin_end(12)
        update_all_btn.set_margin_top(12)
        update_all_btn.connect("clicked", self._on_update_all)
        self.app_list.append(update_all_btn)

        for u in updates:
            row = Adw.ActionRow(title=u["name"], subtitle=u["id"])
            self.app_list.append(row)

    def _on_update_all(self, btn):
        btn.set_sensitive(False)
        btn.set_label("Güncelleniyor...")

        def worker():
            run_flatpak(["update", "-y"], timeout=600)
            GLib.idle_add(btn.set_label, "✓ Güncelleme tamamlandı!")

        threading.Thread(target=worker, daemon=True).start()

    def _clear_list(self):
        while True:
            child = self.app_list.get_row_at_index(0)
            if child is None:
                break
            self.app_list.remove(child)


class LumiereStoreApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        win = LumiereStoreWindow(self)
        win.present()


def main():
    app = LumiereStoreApp()
    app.run(None)


if __name__ == "__main__":
    main()
