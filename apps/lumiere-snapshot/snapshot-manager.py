#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║       ✦ Lumière OS — Snapshot Yöneticisi GUI                 ║
# ╚══════════════════════════════════════════════════════════════╝

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import subprocess
import json
import os
import threading

APP_ID = "os.lumiere.snapshot"
VERSION = "0.3.0"
SNAPSHOT_DIR = "/.snapshots"
METADATA_DIR = f"{SNAPSHOT_DIR}/.metadata"


def run_cmd(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout, shell=isinstance(cmd, str))
        return result.stdout.strip(), result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "", False


def get_snapshots():
    """Snapshot listesini al."""
    snapshots = []
    if not os.path.isdir(METADATA_DIR):
        return snapshots

    for f in sorted(os.listdir(METADATA_DIR), reverse=True):
        if f.endswith(".json"):
            path = os.path.join(METADATA_DIR, f)
            try:
                with open(path) as fp:
                    data = json.load(fp)
                    snap_path = os.path.join(SNAPSHOT_DIR, data["id"])
                    if os.path.isdir(snap_path):
                        # Boyut
                        size_out, _ = run_cmd(["du", "-sh", snap_path])
                        data["size"] = size_out.split()[0] if size_out else "?"
                        snapshots.append(data)
            except (json.JSONDecodeError, KeyError, IOError):
                continue
    return snapshots


class SnapshotManagerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Lumière Snapshot Yöneticisi")
        self.set_default_size(700, 500)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)

        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="✦ Snapshot Yöneticisi"))

        # Yeni snapshot butonu
        create_btn = Gtk.Button(label="+ Yeni Snapshot")
        create_btn.add_css_class("suggested-action")
        create_btn.connect("clicked", self._on_create)
        header.pack_end(create_btn)

        # Yenile
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.connect("clicked", lambda b: self._load_snapshots())
        header.pack_start(refresh_btn)

        main_box.append(header)

        # Snapshot listesi
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        self.snapshot_list = Gtk.ListBox()
        self.snapshot_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.snapshot_list.add_css_class("boxed-list")
        scrolled.set_child(self.snapshot_list)
        main_box.append(scrolled)

        # Aksiyon butonları
        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions.set_halign(Gtk.Align.END)
        actions.set_margin_top(8)
        actions.set_margin_bottom(12)
        actions.set_margin_end(16)

        self.rollback_btn = Gtk.Button(label="Geri Al")
        self.rollback_btn.add_css_class("destructive-action")
        self.rollback_btn.connect("clicked", self._on_rollback)
        actions.append(self.rollback_btn)

        self.delete_btn = Gtk.Button(label="Sil")
        self.delete_btn.connect("clicked", self._on_delete)
        actions.append(self.delete_btn)

        main_box.append(actions)

        self._load_snapshots()

    def _load_snapshots(self):
        # Temizle
        while True:
            row = self.snapshot_list.get_row_at_index(0)
            if row is None:
                break
            self.snapshot_list.remove(row)

        def worker():
            snapshots = get_snapshots()
            GLib.idle_add(self._populate, snapshots)

        threading.Thread(target=worker, daemon=True).start()

    def _populate(self, snapshots):
        if not snapshots:
            row = Adw.ActionRow(title="Snapshot bulunamadı",
                                subtitle="Yeni bir snapshot oluşturun")
            self.snapshot_list.append(row)
            return

        for snap in snapshots:
            row = Adw.ActionRow(
                title=snap["id"],
                subtitle=f"{snap.get('description', '')} — {snap.get('size', '?')}"
            )

            # Tip etiketi
            snap_type = snap.get("type", "manual")
            if snap_type == "pre-rollback":
                badge = Gtk.Label(label="🔄")
            elif snap_type == "pacman":
                badge = Gtk.Label(label="📦")
            else:
                badge = Gtk.Label(label="📸")

            row.add_prefix(badge)

            ts_label = Gtk.Label(label=snap.get("timestamp", "")[:19])
            ts_label.add_css_class("dim-label")
            ts_label.add_css_class("caption")
            row.add_suffix(ts_label)

            row._snap_id = snap["id"]
            self.snapshot_list.append(row)

    def _get_selected_id(self):
        row = self.snapshot_list.get_selected_row()
        if row and hasattr(row, "_snap_id"):
            return row._snap_id
        return None

    def _on_create(self, _btn):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Yeni Snapshot",
            body="Snapshot açıklaması girin:"
        )
        entry = Gtk.Entry()
        entry.set_placeholder_text("Snapshot açıklaması...")
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "İptal")
        dialog.add_response("create", "Oluştur")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)

        def on_response(dialog, response):
            if response == "create":
                desc = entry.get_text() or "manuel snapshot"
                threading.Thread(
                    target=lambda: (
                        run_cmd(["sudo", "lumiere-snapshot", "create", desc]),
                        GLib.idle_add(self._load_snapshots)
                    ),
                    daemon=True
                ).start()

        dialog.connect("response", on_response)
        dialog.present()

    def _on_delete(self, _btn):
        snap_id = self._get_selected_id()
        if not snap_id:
            return

        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Snapshot Sil",
            body=f"'{snap_id}' silinecek. Emin misiniz?"
        )
        dialog.add_response("cancel", "İptal")
        dialog.add_response("delete", "Sil")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_response(dialog, response):
            if response == "delete":
                threading.Thread(
                    target=lambda: (
                        run_cmd(["sudo", "lumiere-snapshot", "delete", snap_id]),
                        GLib.idle_add(self._load_snapshots)
                    ),
                    daemon=True
                ).start()

        dialog.connect("response", on_response)
        dialog.present()

    def _on_rollback(self, _btn):
        snap_id = self._get_selected_id()
        if not snap_id:
            return

        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="⚠ Rollback",
            body=f"Sistem '{snap_id}' durumuna geri alınacak.\nBu işlem geri alınamaz!"
        )
        dialog.add_response("cancel", "İptal")
        dialog.add_response("rollback", "Geri Al")
        dialog.set_response_appearance("rollback", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_response(dialog, response):
            if response == "rollback":
                threading.Thread(
                    target=lambda: run_cmd(
                        f"echo evet | sudo lumiere-snapshot rollback {snap_id}"),
                    daemon=True
                ).start()

        dialog.connect("response", on_response)
        dialog.present()


class SnapshotApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        win = SnapshotManagerWindow(self)
        win.present()


def main():
    app = SnapshotApp()
    app.run(None)


if __name__ == "__main__":
    main()
