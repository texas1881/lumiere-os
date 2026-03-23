#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Sistem Monitörü                      ║
# ╚══════════════════════════════════════════════════════════════╝
"""
lumiere-monitor: GTK4/Adwaita tabanlı sistem monitör uygulaması.

Özellikler:
  - CPU / RAM / Disk kullanım göstergeleri (cairo ile dairesel)
  - İşlem listesi (sıralama, sonlandırma)
  - Ağ trafik bilgisi
  - 2 saniyelik otomatik yenileme
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import subprocess
import os
import math
import signal
import time

APP_ID = "os.lumiere.monitor"
VERSION = "0.2.0"

# — Lumière Renk Paleti —
COLORS = {
    "bg_base": (0.051, 0.051, 0.078),    # #0D0D14
    "bg_surface": (0.075, 0.075, 0.118),    # #13131E
    "bg_overlay": (0.102, 0.102, 0.180),    # #1A1A2E
    "fg_primary": (0.910, 0.902, 0.941),    # #E8E6F0
    "fg_muted": (0.420, 0.408, 0.502),    # #6B6880
    "gold": (0.961, 0.651, 0.137),    # #F5A623
    "gold_light": (1.000, 0.816, 0.502),    # #FFD080
    "green": (0.290, 0.871, 0.502),    # #4ADE80
    "blue": (0.376, 0.647, 0.980),    # #60A5FA
    "red": (0.973, 0.443, 0.443),    # #F87171
    "cyan": (0.133, 0.827, 0.933),    # #22D3EE
    "border": (0.165, 0.165, 0.259),    # #2A2A42
}


def read_proc(path):
    """Proc dosyasını oku."""
    try:
        with open(path) as f:
            return f.read()
    except (IOError, OSError):
        return ""


def get_cpu_usage():
    """CPU kullanım yüzdesini hesapla."""
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        parts = line.split()
        idle = int(parts[4])
        total = sum(int(x) for x in parts[1:])

        if not hasattr(get_cpu_usage, "_prev"):
            get_cpu_usage._prev = (idle, total)
            return 0.0

        prev_idle, prev_total = get_cpu_usage._prev
        diff_idle = idle - prev_idle
        diff_total = total - prev_total
        get_cpu_usage._prev = (idle, total)

        if diff_total == 0:
            return 0.0
        return (1.0 - diff_idle / diff_total) * 100
    except (IOError, OSError, ZeroDivisionError):
        return 0.0


def get_memory_usage():
    """RAM kullanım bilgilerini al."""
    try:
        content = read_proc("/proc/meminfo")
        info = {}
        for line in content.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                info[parts[0].rstrip(":")] = int(parts[1])

        total = info.get("MemTotal", 1)
        available = info.get("MemAvailable", 0)
        used = total - available
        return {
            "total_gb": total / 1048576,
            "used_gb": used / 1048576,
            "percent": (used / total) * 100 if total > 0 else 0,
        }
    except (KeyError, ValueError):
        return {"total_gb": 0, "used_gb": 0, "percent": 0}


def get_disk_usage():
    """Disk kullanım bilgilerini al."""
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        used = total - free
        return {
            "total_gb": total / (1024**3),
            "used_gb": used / (1024**3),
            "percent": (used / total) * 100 if total > 0 else 0,
        }
    except OSError:
        return {"total_gb": 0, "used_gb": 0, "percent": 0}


def get_processes():
    """İşlem listesini al."""
    processes = []
    try:
        result = subprocess.run(
            ["ps", "aux", "--sort=-%cpu"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().splitlines()
        for line in lines[1:51]:  # İlk 50 işlem
            parts = line.split(None, 10)
            if len(parts) >= 11:
                processes.append({
                    "user": parts[0],
                    "pid": int(parts[1]),
                    "cpu": float(parts[2]),
                    "mem": float(parts[3]),
                    "command": parts[10][:60],
                })
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return processes


def get_network_stats():
    """Ağ istatistiklerini al."""
    try:
        content = read_proc("/proc/net/dev")
        total_rx = 0
        total_tx = 0
        for line in content.splitlines()[2:]:
            parts = line.split()
            if len(parts) >= 10 and not parts[0].startswith("lo"):
                total_rx += int(parts[1])
                total_tx += int(parts[9])

        if not hasattr(get_network_stats, "_prev"):
            get_network_stats._prev = (total_rx, total_tx, time.time())
            return {"rx_speed": 0, "tx_speed": 0, "rx_total": total_rx, "tx_total": total_tx}

        prev_rx, prev_tx, prev_time = get_network_stats._prev
        elapsed = time.time() - prev_time
        get_network_stats._prev = (total_rx, total_tx, time.time())

        if elapsed <= 0:
            return {"rx_speed": 0, "tx_speed": 0, "rx_total": total_rx, "tx_total": total_tx}

        return {
            "rx_speed": (total_rx - prev_rx) / elapsed,
            "tx_speed": (total_tx - prev_tx) / elapsed,
            "rx_total": total_rx,
            "tx_total": total_tx,
        }
    except (IOError, ValueError):
        return {"rx_speed": 0, "tx_speed": 0, "rx_total": 0, "tx_total": 0}


def format_bytes(b):
    """Byte değerini okunabilir formata çevir."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


class CircularGauge(Gtk.DrawingArea):
    """Cairo ile dairesel gösterge widget'ı."""

    def __init__(self, label="", color_key="gold", size=140):
        super().__init__()
        self.set_size_request(size, size + 30)
        self.label = label
        self.value = 0
        self.subtitle = ""
        self.color_key = color_key
        self.gauge_size = size
        self.set_draw_func(self._draw)

    def update(self, value, subtitle=""):
        self.value = min(max(value, 0), 100)
        self.subtitle = subtitle
        self.queue_draw()

    def _draw(self, area, cr, width, height):
        size = self.gauge_size
        cx = width / 2
        cy = size / 2 + 4
        radius = (size - 20) / 2
        line_width = 8

        # Arkaplan halkası
        cr.set_line_width(line_width)
        r, g, b = COLORS["border"]
        cr.set_source_rgba(r, g, b, 0.6)
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.stroke()

        # Değer halkası
        r, g, b = COLORS[self.color_key]
        cr.set_source_rgb(r, g, b)
        start_angle = -math.pi / 2
        end_angle = start_angle + (2 * math.pi * self.value / 100)
        cr.arc(cx, cy, radius, start_angle, end_angle)
        cr.stroke()

        # Yüzde metni
        cr.select_font_face("Inter", 0, 1)  # bold
        cr.set_font_size(22)
        text = f"{int(self.value)}%"
        extents = cr.text_extents(text)
        cr.move_to(cx - extents.width / 2, cy + extents.height / 3)
        r, g, b = COLORS["fg_primary"]
        cr.set_source_rgb(r, g, b)
        cr.show_text(text)

        # Etiket (alt)
        cr.select_font_face("Inter", 0, 0)  # normal
        cr.set_font_size(12)
        extents = cr.text_extents(self.label)
        cr.move_to(cx - extents.width / 2, cy + radius + 18)
        r, g, b = COLORS["fg_muted"]
        cr.set_source_rgb(r, g, b)
        cr.show_text(self.label)

        # Alt bilgi
        if self.subtitle:
            cr.set_font_size(10)
            extents = cr.text_extents(self.subtitle)
            cr.move_to(cx - extents.width / 2, cy + radius + 32)
            cr.show_text(self.subtitle)


class OverviewTab(Gtk.Box):
    """Genel bakış sekmesi."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.set_margin_start(24)
        self.set_margin_end(24)
        self.set_margin_top(20)
        self.set_margin_bottom(20)

        title = Gtk.Label(label="Sistem Durumu")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        # Göstergeler kutusu
        gauges_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=32)
        gauges_box.set_halign(Gtk.Align.CENTER)
        gauges_box.set_margin_top(16)

        self.cpu_gauge = CircularGauge(label="CPU", color_key="gold", size=140)
        self.ram_gauge = CircularGauge(label="RAM", color_key="blue", size=140)
        self.disk_gauge = CircularGauge(label="Disk", color_key="green", size=140)

        gauges_box.append(self.cpu_gauge)
        gauges_box.append(self.ram_gauge)
        gauges_box.append(self.disk_gauge)
        self.append(gauges_box)

        # Ağ bilgisi
        net_group = Adw.PreferencesGroup(title="Ağ")
        net_group.set_margin_top(8)

        self.net_download_row = Adw.ActionRow(title="İndirme", subtitle="0 B/s")
        self.net_download_row.add_prefix(Gtk.Label(label="⬇"))
        net_group.add(self.net_download_row)

        self.net_upload_row = Adw.ActionRow(title="Yükleme", subtitle="0 B/s")
        self.net_upload_row.add_prefix(Gtk.Label(label="⬆"))
        net_group.add(self.net_upload_row)

        self.append(net_group)

    def update(self):
        cpu = get_cpu_usage()
        mem = get_memory_usage()
        disk = get_disk_usage()
        net = get_network_stats()

        self.cpu_gauge.update(cpu)
        self.ram_gauge.update(mem["percent"], f"{mem['used_gb']:.1f} / {mem['total_gb']:.1f} GB")
        self.disk_gauge.update(disk["percent"], f"{disk['used_gb']:.1f} / {disk['total_gb']:.1f} GB")

        self.net_download_row.set_subtitle(f"{format_bytes(net['rx_speed'])}/s")
        self.net_upload_row.set_subtitle(f"{format_bytes(net['tx_speed'])}/s")


class ProcessesTab(Gtk.Box):
    """İşlemler sekmesi."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(16)
        self.set_margin_bottom(16)

        # Başlık
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title = Gtk.Label(label="İşlemler")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        header.append(title)

        # Arama
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("İşlem ara...")
        self.search_entry.connect("search-changed", self._on_search)
        header.append(self.search_entry)

        self.append(header)

        # İşlem listesi
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        # ColumnView yerine basit ListBox kullanıyoruz (daha kolay)
        self.process_list = Gtk.ListBox()
        self.process_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.process_list.add_css_class("boxed-list")
        scrolled.set_child(self.process_list)

        self.append(scrolled)

        # Kill butonu
        kill_btn = Gtk.Button(label="İşlemi Sonlandır")
        kill_btn.add_css_class("destructive-action")
        kill_btn.set_halign(Gtk.Align.END)
        kill_btn.connect("clicked", self._on_kill)
        self.append(kill_btn)

        self.all_processes = []
        self.filter_text = ""

    def update(self):
        self.all_processes = get_processes()
        self._refresh_list()

    def _refresh_list(self):
        # Eski satırları kaldır
        while True:
            row = self.process_list.get_row_at_index(0)
            if row is None:
                break
            self.process_list.remove(row)

        for proc in self.all_processes:
            if self.filter_text and self.filter_text.lower() not in proc["command"].lower():
                continue

            row = Adw.ActionRow(
                title=proc["command"],
                subtitle=f"PID: {proc['pid']} | Kullanıcı: {proc['user']}"
            )

            cpu_label = Gtk.Label(label=f"CPU: {proc['cpu']:.1f}%")
            cpu_label.add_css_class("dim-label")
            cpu_label.set_margin_end(8)
            row.add_suffix(cpu_label)

            mem_label = Gtk.Label(label=f"RAM: {proc['mem']:.1f}%")
            mem_label.add_css_class("dim-label")
            row.add_suffix(mem_label)

            # PID'yi sakla
            row._pid = proc["pid"]
            self.process_list.append(row)

    def _on_search(self, entry):
        self.filter_text = entry.get_text()
        self._refresh_list()

    def _on_kill(self, _btn):
        row = self.process_list.get_selected_row()
        if row and hasattr(row, "_pid"):
            try:
                os.kill(row._pid, signal.SIGTERM)
                # Listeyi güncelle
                GLib.timeout_add(500, self.update)
            except (ProcessLookupError, PermissionError):
                pass


class LumiereMonitorWindow(Adw.ApplicationWindow):
    """Ana monitör penceresi."""

    def __init__(self, app):
        super().__init__(application=app, title="Lumière Sistem Monitörü")
        self.set_default_size(800, 600)

        # Ana layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_box)

        # Header
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="✦ Sistem Monitörü"))
        main_box.append(header)

        # Tab view
        self.tab_view = Adw.ViewStack()

        self.overview_tab = OverviewTab()
        self.tab_view.add_titled(self.overview_tab, "overview", "Genel Bakış")

        self.processes_tab = ProcessesTab()
        self.tab_view.add_titled(self.processes_tab, "processes", "İşlemler")

        # Tab switcher bar
        switcher = Adw.ViewSwitcherBar()
        switcher.set_stack(self.tab_view)
        switcher.set_reveal(True)

        # Header'a da switcher ekle
        header_switcher = Adw.ViewSwitcher()
        header_switcher.set_stack(self.tab_view)
        header_switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(header_switcher)

        main_box.append(self.tab_view)
        main_box.append(switcher)

        # 2 saniyelik yenileme
        self._update()
        GLib.timeout_add_seconds(2, self._update)

    def _update(self):
        self.overview_tab.update()
        self.processes_tab.update()
        return True  # GLib.SOURCE_CONTINUE


class LumiereMonitorApp(Adw.Application):
    """Ana uygulama."""

    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        win = LumiereMonitorWindow(self)
        win.present()


def main():
    app = LumiereMonitorApp()
    app.run(None)


if __name__ == "__main__":
    main()
