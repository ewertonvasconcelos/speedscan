#!/bin/bash
# Script completo para instalar o SpeedScan no Manjaro/Arch
# Cria todos os 24 módulos e configura o ambiente

set -e

echo "🚀 Iniciando instalação do SpeedScan (versão Arch/Manjaro)..."

# ============================================================
# 1. Detectar gerenciador de pacotes e preparar instalação
# ============================================================
if command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
    INSTALL_CMD="sudo pacman -S --noconfirm"
    PYTHON_TK_PKG="tk"
elif command -v apt >/dev/null 2>&1; then
    PKG_MANAGER="apt"
    INSTALL_CMD="sudo apt update && sudo apt install -y"
    PYTHON_TK_PKG="python3-tk"
elif command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="sudo dnf install -y"
    PYTHON_TK_PKG="python3-tkinter"
else
    echo "⚠️  Gerenciador de pacotes não detectado."
    echo "Você precisará instalar manualmente: gettext e tk (python-tk)."
    read -p "Pressione Enter para continuar ou Ctrl+C para abortar."
fi

# Função para instalar pacotes
install_pkg() {
    if [ -n "$PKG_MANAGER" ]; then
        echo "📦 Instalando $1..."
        $INSTALL_CMD $1
    else
        echo "⚠️  Por favor, instale $1 manualmente."
    fi
}

# Instalar gettext (para msgfmt) se necessário
if ! command -v msgfmt >/dev/null 2>&1; then
    echo "📦 gettext não encontrado. Instalando..."
    install_pkg "gettext"
fi

# ============================================================
# 2. Remover instalação anterior (fazendo backup)
# ============================================================
if [ -d "core" ]; then
    backup_dir="core.bak.$(date +%s)"
    echo "📦 Movendo core antigo para $backup_dir"
    mv core "$backup_dir"
fi

if [ -d "venv" ]; then
    rm -rf venv
fi

mkdir -p core locale
echo "✅ Pastas core/ e locale/ criadas."

# ============================================================
# 3. Criar todos os módulos (24 arquivos)
# ============================================================

# -------------------- main.py --------------------
cat > core/main.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpeedScan main application module.
Version 1.0.0
"""
import json
import logging
import os
import platform
import re
import subprocess
import sys
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import customtkinter as ctk
import matplotlib
import psutil
from PIL import Image, ImageDraw

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Internal imports
from core import config
from core.actions import CommandRunner, ActionMapper, ActionHandler
from core.ai_proactive import AIProactive
from core.browser_cleaner import BrowserCleaner
from core.chat import ChatFrame
from core.cookie_manager import CookieManager
from core.dashboard import Dashboard
from core.first_run import FirstRunWizard
from core.hardware import HardwareInfo
from core.health_score import HealthScore
from core.historical_metrics import MetricsCollector, MetricsDB
from core.i18n import _, get_translation
from core.lan_cache import LANCacheManager
from core.lan_scanner import LANScanner
from core.process_manager import ProcessManager
from core.scheduler import Scheduler
from core.security_scanner import SecurityScanner
from core.smart_monitor import SmartMonitor
from core.speed_test import SpeedTester
from core.temperature_monitor import TemperatureMonitor
from core.trash_manager import TrashManager
import core.ui as ui

try:
    from core.windows_cleaner import WindowsCleaner
except ImportError:
    WindowsCleaner = None

# Logging configuration
config.LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = config.LOG_DIR / "speedscan.log"
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logging.basicConfig(level=logging.ERROR, handlers=[handler])

# ============================================================================
# Main application class
# ============================================================================

class SpeedScan(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.SO = platform.system()
        self.runner = CommandRunner(self.SO)
        self.hw = HardwareInfo(self.SO, self.runner)
        self.config_data = self._load_config()
        self._ = get_translation(self.config_data.get("language", "pt_BR"))
        self.update_theme_vars()
        self.title(self._("SpeedScan") + f" {config.VERSION}")
        self.configure(fg_color=self.bg_color)
        self.minsize(900, 500)
        self.apply_ui_scale()
        self.turbo_active = False
        self.consoles_visible = {}
        self.ping_active = False
        self.current_module = "dashboard"
        self.sidebar_buttons = {}
        self.detail_buttons = {}
        self.logs = {}

        # Initialize core modules
        self.health_monitor = HealthScore()
        self.health_score_var = ctk.StringVar(value=self._("Calculating..."))
        self.temp_monitor = TemperatureMonitor()
        self.smart_monitor = SmartMonitor()
        self.browser_cleaner = BrowserCleaner()
        self.speed_tester = SpeedTester()
        self.proc_manager = ProcessManager()
        self.metrics_collector = MetricsCollector(interval=5)
        self.metrics_db = MetricsDB()
        self.lan_scanner = LANScanner()
        self.ai_proactive = AIProactive(self.metrics_db, self.health_monitor)
        self.security_scanner = SecurityScanner(self.SO)
        self.lan_cache = LANCacheManager(self.SO)
        self.cookie_manager = CookieManager()
        self.trash_manager = TrashManager()

        if self.SO == "Windows" and WindowsCleaner is not None:
            self.windows_cleaner = WindowsCleaner()
        else:
            self.windows_cleaner = None

        self.metrics_collector.start()
        self.proc_manager.start_monitoring()
        self.action_handler = ActionHandler(self)
        self.action_mapper = ActionMapper(self.SO, self.runner, self.turbo_active)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        for btn in self.detail_buttons.values():
            btn.pack_forget()
        self.consoles_visible = {tag: False for tag in self.detail_buttons.keys()}
        self.show_frame("dashboard")

        self._setup_bindings()
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        self._check_process_queue()
        self.after(200, self._restore_window_state)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.after(500, self._check_first_run)

    # ------------------------------------------------------------------------
    # Configuration management
    # ------------------------------------------------------------------------
    def _load_config(self):
        if config.CONFIG_FILE.exists():
            try:
                with open(config.CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                for key, value in config.DEFAULT_CONFIG.items():
                    if key not in cfg:
                        cfg[key] = value
                return cfg
            except Exception as e:
                logging.error(f"Error loading config: {e}")
                return config.DEFAULT_CONFIG.copy()
        return config.DEFAULT_CONFIG.copy()

    def _save_config(self):
        try:
            with open(config.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    # Theme handling
    def update_theme_vars(self):
        theme_key = self.config_data.get("theme", "default")
        theme_map = {"Still": "grey", "Tecno": "dark", "Snow": "light"}
        internal_key = theme_map.get(theme_key, theme_key)
        t = config.THEMES.get(internal_key, config.THEMES["default"])
        ctk.set_appearance_mode(t["mode"])
        self.bg_color = t["bg"]
        self.side_bg = t["side"]
        self.acc_color = t["acc"]
        self.text_color = t["text"]
        self.light_bg = self._lighter_color(self.bg_color, 0.2)

    def _lighter_color(self, hex_color, factor):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def apply_ui_scale(self):
        scale = self.config_data.get("ui_scale", "auto")
        if scale == "auto":
            ctk.set_widget_scaling(1.0)
        else:
            ctk.set_widget_scaling(float(scale) / 100)

    def round_image(self, path, size=(96,96), radius=20):
        try:
            img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            mask = Image.new("L", size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0,0)+size, radius=radius, fill=255)
            result = Image.new("RGBA", size)
            result.paste(img, (0,0), mask)
            return ctk.CTkImage(result, size=size)
        except:
            return None

    # ------------------------------------------------------------------------
    # Sidebar building
    # ------------------------------------------------------------------------
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.side_bg)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        top = ctk.CTkFrame(sidebar, fg_color="transparent")
        top.pack(pady=(15,0))

        icon = self.round_image(str(config.ICON_PATH)) if config.ICON_PATH.exists() else None
        if icon:
            lbl_icon = ctk.CTkLabel(top, image=icon, text="", width=96, height=96)
        else:
            lbl_icon = ctk.CTkLabel(top, text="⚡", font=("Inter", 48), width=96, height=96, text_color=self.acc_color)
        lbl_icon.pack()

        center = ctk.CTkFrame(sidebar, fg_color="transparent")
        center.pack(expand=False, fill="x", pady=(38,15))

        nav_items = [
            ("📊", self._("Dashboard"), "dashboard"),
            ("⚡", self._("Optimization"), "optimization"),
            ("🌐", self._("Network"), "network"),
            ("🖥️", self._("Drivers"), "drivers"),
        ]

        level_items = {
            1: [],
            2: [self._("Processes")],
            3: [self._("Processes"), self._("History"), self._("Security"), self._("AI Agent"), self._("Windows Cleaner")]
        }

        for icon, text, target in nav_items:
            btn = self._sidebar_btn(center, icon, text, target)
            self.sidebar_buttons[target] = btn

        level = 3
        if level >= 2:
            icon_map = {
                self._("Processes"): ("⚙️", "processes"),
                self._("History"): ("📈", "history"),
                self._("Security"): ("🔒", "security"),
                self._("AI Agent"): ("🤖", "agent"),
                self._("Windows Cleaner"): ("🧹", "windows_cleaner")
            }
            for item in level_items[level]:
                icon, target = icon_map[item]
                btn = self._sidebar_btn(center, icon, item, target)
                self.sidebar_buttons[target] = btn

        for icon, text, target in [("⚙️", self._("Settings"), "settings"), ("ℹ️", self._("About"), "about")]:
            btn = self._sidebar_btn(center, icon, text, target)
            self.sidebar_buttons[target] = btn

        spacer = ctk.CTkLabel(center, text="", height=0)
        spacer.pack(expand=False)

    def _sidebar_btn(self, parent, icon, text, target):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=2, fill="x", padx=10)
        btn = ctk.CTkButton(
            frame,
            text=f"{icon}  {text}",
            anchor="w",
            height=30,
            fg_color="transparent",
            hover_color=self.acc_color,
            font=("Inter", 13),
            corner_radius=10,
            text_color=self.text_color,
            command=lambda: self.show_frame(target),
            cursor="hand2"
        )
        btn.pack(fill="x")
        return btn

    # ------------------------------------------------------------------------
    # Frame management
    # ------------------------------------------------------------------------
    def show_frame(self, target):
        for f in self.frames.values():
            f.pack_forget()

        if target not in self.frames:
            self.frames[target] = self._create_frame(target)

        self.frames[target].pack(fill="both", expand=True)
        self.current_module = target

        for key, btn in self.sidebar_buttons.items():
            btn.configure(fg_color=self.acc_color if key == target else "transparent")

        if target == "processes":
            self._refresh_process_list()
        elif target == "history":
            self._update_graphs()
        elif target == "agent":
            self._update_ai_suggestions()

    def _create_frame(self, target):
        frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        getattr(self, f"_fill_{target}")(frame)
        return frame

    # ------------------------------------------------------------------------
    # Tab content filling methods
    # ------------------------------------------------------------------------
    def _fill_dashboard(self, parent):
        ctk.CTkLabel(parent, text=self._("Dashboard"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        self.dashboard = Dashboard(parent, self, fg_color="transparent")
        self.dashboard.pack(fill="both", expand=True)

    def _fill_optimization(self, parent):
        ctk.CTkLabel(parent, text=self._("Optimization"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("🧹 Cache Cleanup"), "cache", False),
            (self._("🔄 Swap Reset"), "swap", False),
            (self._("🔍 Verify Errors"), "check", False),
            (self._("🚀 Turbo Mode"), "turbo", False),
            (self._("Steam"), "steam", False),
            (self._("Lutris"), "lutris", False),
            (self._("Heroic Launcher"), "heroic", False),
            (self._("Bottles"), "bottles", False),
            (self._("Wine"), "wine", False),
            (self._("MangoHud"), "mangohud", False),
            (self._("Governor"), "governor", False),
            (self._("🐬 Dolphin Emulator"), "dolphin", False),
            (self._("🧹 Browser Cleanup"), "browsers", False),
            (self._("⚙️ Manage Services"), "services", False),
            (self._("🗂️ Log Analysis"), "logs", False),
            (self._("🗑️ Manage Cookies"), "cookies", False),
            (self._("💾 Optimize SSD (TRIM)"), "trim", False),
            (self._("📦 Repair Broken Packages"), "fix_broken", False),
        ]
        level = 3
        if level == 1:
            items = [i for i in items if i[1] not in ["services","logs","cookies","trim","fix_broken"]]
        elif level == 2:
            items = [i for i in items if i[1] not in ["logs","cookies"]]
        ui.create_card_grid(parent, items, "opt", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "opt", self.acc_color, self.toggle_console)
        self.detail_buttons["opt"] = btn
        self.logs["opt"] = log

    def _fill_network(self, parent):
        ctk.CTkLabel(parent, text=self._("Network"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("📡 Ping"), "ping", False),
            (self._("🌩️ Cloudflare DNS"), "1.1.1.1", True),
            (self._("🎛️ Google DNS"), "8.8.8.8", True),
            (self._("🎛️ AdGuard DNS"), "94.140.14.14", True),
            (self._("🔄 DNS Auto"), "auto", True),
            (self._("📊 Speedtest"), "speedtest", False),
            (self._("🕵️ Diagnostic Tool"), "ethtool", False),
            (self._("🔄 Renew IP"), "dhclient", False),
            (self._("🔓 Open Ports"), "ports", False),
            (self._("🌍 Traceroute"), "traceroute", False),
            (self._("📶 Wi-Fi Info"), "wifi", False),
            (self._("🛠️ Test DNS"), "testdns", False),
            (self._("📡 LAN Scanner"), "lanscan", False),
            (self._("📦 LANCache"), "lancache", False),
            (self._("🌍 Public IP"), "public_ip", False),
        ]
        level = 3
        if level == 1:
            items = [i for i in items if i[1] not in ["ports","traceroute","ethtool","dhclient","lanscan","lancache"]]
        elif level == 2:
            items = [i for i in items if i[1] not in ["lanscan","lancache"]]
        ping_labels = ui.create_card_grid(parent, items, "net", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        if ping_labels:
            self.ping_label = ping_labels[0]
        btn, log = ui.add_console(parent, "net", self.acc_color, self.toggle_console)
        self.detail_buttons["net"] = btn
        self.logs["net"] = log

    def _fill_drivers(self, parent):
        ctk.CTkLabel(parent, text=self._("Drivers"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("🖥️ PCI (Video/Net)"), "pci", False),
            (self._("📦 System Update"), "update", False),
            (self._("🔌 USB Devices"), "usb", False),
            (self._("🧩 Kernel Modules"), "modules", False),
            (self._("⚡ CPU Details"), "cpu_info", False),
            (self._("⚡ Firmware Errors"), "firmware", False),
            (self._("🖥️ Video Drivers"), "video_drv", False),
            (self._("🌐 Network Drivers"), "net_drv", False),
            (self._("🔄 Auto Updates"), "auto_update", False),
        ]
        level = 3
        if level == 1:
            items = [i for i in items if i[1] not in ["modules","cpu_info","firmware","video_drv","net_drv","auto_update"]]
        elif level == 2:
            items = [i for i in items if i[1] not in ["video_drv","net_drv","auto_update"]]
        ui.create_card_grid(parent, items, "drv", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "drv", self.acc_color, self.toggle_console)
        self.detail_buttons["drv"] = btn
        self.logs["drv"] = log

    def _fill_processes(self, parent):
        ctk.CTkLabel(parent, text=self._("Process Manager"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))

        control_frame = ctk.CTkFrame(parent, fg_color="transparent")
        control_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(control_frame, text=self._("Filter:"), font=("Inter", 12)).pack(side="left", padx=5)
        self.filter_entry = ctk.CTkEntry(control_frame, placeholder_text=self._("Process name"), width=150)
        self.filter_entry.pack(side="left", padx=5)
        self.filter_entry.bind("<KeyRelease>", self._on_filter_change)

        ctk.CTkLabel(control_frame, text=self._("Sort by:"), font=("Inter", 12)).pack(side="left", padx=5)
        self.sort_var = ctk.StringVar(value="cpu_percent")
        sort_menu = ctk.CTkOptionMenu(control_frame,
                                      values=["cpu_percent", "memory_percent", "name", "pid"],
                                      variable=self.sort_var, command=self._on_sort_change, width=100)
        sort_menu.pack(side="left", padx=5)

        self.reverse_var = ctk.BooleanVar(value=True)
        reverse_check = ctk.CTkCheckBox(control_frame, text=self._("Descending"),
                                         variable=self.reverse_var,
                                         command=self._on_sort_change,
                                         onvalue=True, offvalue=False)
        reverse_check.pack(side="left", padx=5)

        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.pack(fill="x", pady=5)

        ctk.CTkButton(action_frame, text=self._("Kill"), command=self._kill_selected_process,
                      fg_color=self.acc_color, width=80).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text=self._("Suspend"), command=self._suspend_selected_process,
                      fg_color=self.acc_color, width=80).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text=self._("Resume"), command=self._resume_selected_process,
                      fg_color=self.acc_color, width=80).pack(side="left", padx=5)

        ctk.CTkLabel(action_frame, text=self._("Nice:"), font=("Inter", 12)).pack(side="left", padx=5)
        self.nice_var = ctk.IntVar(value=0)
        nice_entry = ctk.CTkEntry(action_frame, textvariable=self.nice_var, width=50)
        nice_entry.pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text=self._("Set"), command=self._set_nice_selected,
                      fg_color=self.acc_color, width=60).pack(side="left", padx=5)

        self.process_text = ctk.CTkTextbox(parent, font=("Courier", 10), wrap="none")
        self.process_text.pack(fill="both", expand=True, padx=10, pady=10)

        self._refresh_process_list()

    def _refresh_process_list(self):
        procs = self.proc_manager.get_process_list()
        filter_text = self.filter_entry.get().lower() if hasattr(self, "filter_entry") else ""
        if filter_text:
            procs = [p for p in procs if filter_text in p["name"].lower()]
        sort_key = self.sort_var.get() if hasattr(self, "sort_var") else "cpu_percent"
        reverse = self.reverse_var.get() if hasattr(self, "reverse_var") else True
        procs.sort(key=lambda x: x.get(sort_key, 0), reverse=reverse)

        self.process_text.configure(state="normal")
        self.process_text.delete("1.0", "end")
        header = f"{'PID':>7} {'CPU%':>6} {'MEM%':>6} {'STATUS':>8} {'NICE':>4} {'USER':<10} {'NAME'}\n"
        self.process_text.insert("end", header)
        self.process_text.tag_add("header", "1.0", "1.end")
        self.process_text.tag_config("header", foreground=self.acc_color)

        for p in procs:
            line = f"{p['pid']:>7d} {p['cpu_percent']:>6.1f}% {p['memory_percent']:>6.1f}% {p['status']:>8} {p['nice']:>4d} {p['username']:<10} {p['name']}\n"
            self.process_text.insert("end", line)

        self.process_text.configure(state="disabled")
        self._current_processes = procs

    def _on_filter_change(self, event=None):
        self._refresh_process_list()

    def _on_sort_change(self, choice=None):
        self._refresh_process_list()

    def _kill_selected_process(self):
        try:
            sel = self.process_text.tag_ranges("sel")
            if sel:
                line_start = self.process_text.index("sel.first linestart")
                line_end = self.process_text.index("sel.first lineend")
                line = self.process_text.get(line_start, line_end)
                pid = int(line.split()[0])
                if self.proc_manager.kill_process(pid):
                    self.show_toast(self._("Process {pid} killed.").format(pid=pid))
                    self._refresh_process_list()
                else:
                    self.show_toast(self._("Failed to kill process {pid}.").format(pid=pid), duration=3000)
            else:
                self.show_toast(self._("Select a process."), duration=2000)
        except:
            self.show_toast(self._("Error killing process."), duration=2000)

    def _suspend_selected_process(self):
        try:
            sel = self.process_text.tag_ranges("sel")
            if sel:
                line_start = self.process_text.index("sel.first linestart")
                line_end = self.process_text.index("sel.first lineend")
                line = self.process_text.get(line_start, line_end)
                pid = int(line.split()[0])
                if self.proc_manager.suspend_process(pid):
                    self.show_toast(self._("Process {pid} suspended.").format(pid=pid))
                    self._refresh_process_list()
                else:
                    self.show_toast(self._("Failed to suspend process {pid}.").format(pid=pid), duration=3000)
            else:
                self.show_toast(self._("Select a process."), duration=2000)
        except:
            self.show_toast(self._("Error suspending process."), duration=2000)

    def _resume_selected_process(self):
        try:
            sel = self.process_text.tag_ranges("sel")
            if sel:
                line_start = self.process_text.index("sel.first linestart")
                line_end = self.process_text.index("sel.first lineend")
                line = self.process_text.get(line_start, line_end)
                pid = int(line.split()[0])
                if self.proc_manager.resume_process(pid):
                    self.show_toast(self._("Process {pid} resumed.").format(pid=pid))
                    self._refresh_process_list()
                else:
                    self.show_toast(self._("Failed to resume process {pid}.").format(pid=pid), duration=3000)
            else:
                self.show_toast(self._("Select a process."), duration=2000)
        except:
            self.show_toast(self._("Error resuming process."), duration=2000)

    def _set_nice_selected(self):
        try:
            sel = self.process_text.tag_ranges("sel")
            if sel:
                line_start = self.process_text.index("sel.first linestart")
                line_end = self.process_text.index("sel.first lineend")
                line = self.process_text.get(line_start, line_end)
                pid = int(line.split()[0])
                nice = self.nice_var.get()
                if self.proc_manager.set_nice(pid, nice):
                    self.show_toast(self._("Nice of process {pid} set to {nice}.").format(pid=pid, nice=nice))
                    self._refresh_process_list()
                else:
                    self.show_toast(self._("Failed to set nice for process {pid}.").format(pid=pid), duration=3000)
            else:
                self.show_toast(self._("Select a process and enter a nice value."), duration=2000)
        except:
            self.show_toast(self._("Error setting nice."), duration=2000)

    def _fill_history(self, parent):
        ctk.CTkLabel(parent, text=self._("Historical Performance"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))

        period_frame = ctk.CTkFrame(parent, fg_color="transparent")
        period_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(period_frame, text=self._("Period:"), font=("Inter", 12)).pack(side="left", padx=5)
        self.period_var = ctk.StringVar(value="1h")
        period_menu = ctk.CTkOptionMenu(period_frame,
                                        values=["1h","6h","12h","24h","7d"],
                                        variable=self.period_var, command=self._update_graphs, width=80)
        period_menu.pack(side="left", padx=5)

        self.graph_frame = ctk.CTkFrame(parent, fg_color=self.bg_color)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._update_graphs()

    def _update_graphs(self, choice=None):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        period_map = {"1h":1, "6h":6, "12h":12, "24h":24, "7d":168}
        hours = period_map.get(self.period_var.get(), 1)

        data = self.metrics_db.get_last_hours(hours=hours, metrics=["timestamp","cpu","memory","disk_usage"])
        if not data or len(data) < 2:
            ctk.CTkLabel(self.graph_frame, text=self._("Not enough data to display.")).pack(expand=True)
            return

        times = [d[0] for d in data]
        cpus = [d[1] for d in data]
        mems = [d[2] for d in data]
        disks = [d[3] for d in data]

        fig = Figure(figsize=(8,6), dpi=100)
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313)

        ax1.plot(times, cpus, label="CPU %", color="#ff6b6b", linewidth=1.5)
        ax1.set_ylabel("CPU %"); ax1.set_ylim(0,100); ax1.legend(); ax1.grid(True, linestyle="--", alpha=0.6)

        ax2.plot(times, mems, label="RAM %", color="#4ecdc4", linewidth=1.5)
        ax2.set_ylabel("RAM %"); ax2.set_ylim(0,100); ax2.legend(); ax2.grid(True, linestyle="--", alpha=0.6)

        ax3.plot(times, disks, label="Disk %", color="#ffe66d", linewidth=1.5)
        ax3.set_xlabel(self._("Time (hours from now)"));
        ax3.set_ylabel("Disk %"); ax3.set_ylim(0,100); ax3.legend(); ax3.grid(True, linestyle="--", alpha=0.6)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _fill_security(self, parent):
        ctk.CTkLabel(parent, text=self._("System Security"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("🛡️ Open Ports"), "ports", False),
            (self._("🛡️ Firewall"), "firewall", False),
            (self._("📦 Security Updates"), "sec_updates", False),
        ]
        level = self.config_data.get("expert_level",1)
        if level == 1:
            items = [i for i in items if i[1] not in ["ports","sec_updates"]]
        ui.create_card_grid(parent, items, "sec", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "sec", self.acc_color, self.toggle_console)
        self.detail_buttons["sec"] = btn
        self.logs["sec"] = log

    def _fill_agent(self, parent):
        ctk.CTkLabel(parent, text=self._("AI Agent"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        self.chat_frame = ChatFrame(parent, self, fg_color="transparent")
        self.chat_frame.pack(fill="both", expand=True)

    def _fill_settings(self, parent):
        ctk.CTkLabel(parent, text=self._("Settings"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,30))

        f_user = ctk.CTkFrame(parent, fg_color="transparent")
        f_user.pack(fill="x", pady=5)
        ctk.CTkLabel(f_user, text=self._("Username:"), font=("Inter", 12)).pack(anchor="w")
        self.entry_user = ctk.CTkEntry(f_user, placeholder_text=self._("Your name"), width=200)
        self.entry_user.pack(anchor="w", pady=2)
        self.entry_user.insert(0, self.config_data.get("username",""))

        f_lang = ctk.CTkFrame(parent, fg_color="transparent")
        f_lang.pack(fill="x", pady=5)
        ctk.CTkLabel(f_lang, text=self._("Language:"), font=("Inter", 12)).pack(anchor="w")
        lang_values = list(config.LANGUAGES.values())
        self.lang_var = ctk.StringVar(value=config.LANGUAGES.get(self.config_data.get("language","pt_BR"), "Português Brasileiro"))
        ctk.CTkOptionMenu(f_lang, values=lang_values, variable=self.lang_var, width=200).pack(anchor="w", pady=2)

        f_scale = ctk.CTkFrame(parent, fg_color="transparent")
        f_scale.pack(fill="x", pady=5)
        ctk.CTkLabel(f_scale, text=self._("UI Scale:"), font=("Inter", 12)).pack(anchor="w")
        scale_values = list(config.SCALES.values())
        self.scale_var = ctk.StringVar(value=config.SCALES.get(self.config_data.get("ui_scale","auto"), "Auto"))
        ctk.CTkOptionMenu(f_scale, values=scale_values, variable=self.scale_var, width=200).pack(anchor="w", pady=2)

        f_theme = ctk.CTkFrame(parent, fg_color="transparent")
        f_theme.pack(fill="x", pady=5)
        ctk.CTkLabel(f_theme, text=self._("Theme:"), font=("Inter", 12)).pack(anchor="w")
        theme_names = ["Still", "Tecno", "Snow"]
        self.theme_var = ctk.StringVar(value=theme_names[0])
        current_theme = self.config_data.get("theme","default")
        theme_display_map = {"grey": "Still", "dark": "Tecno", "light": "Snow"}
        display = theme_display_map.get(current_theme, "Still")
        self.theme_var.set(display)
        ctk.CTkOptionMenu(f_theme, values=theme_names, variable=self.theme_var, width=200).pack(anchor="w", pady=2)

        f_tab = ctk.CTkFrame(parent, fg_color="transparent")
        f_tab.pack(fill="x", pady=5)
        self.tab_var = ctk.BooleanVar(value=self.config_data.get("open_file_in_tab", False))
        ctk.CTkCheckBox(f_tab, text=self._("Open files in new tab"), variable=self.tab_var,
                        onvalue=True, offvalue=False).pack(anchor="w")

        f_level = ctk.CTkFrame(parent, fg_color="transparent")
        f_level.pack(fill="x", pady=5)
        ctk.CTkLabel(f_level, text=self._("Expert level:"), font=("Inter", 12)).pack(anchor="w")
        self.level_var = ctk.IntVar(value=self.config_data.get("expert_level",1))
        r1 = ctk.CTkRadioButton(f_level, text=self._("Beginner"), variable=self.level_var, value=1, cursor="hand2")
        r1.pack(anchor="w", pady=2)
        r2 = ctk.CTkRadioButton(f_level, text=self._("Intermediate"), variable=self.level_var, value=2, cursor="hand2")
        r2.pack(anchor="w", pady=2)
        r3 = ctk.CTkRadioButton(f_level, text=self._("Advanced"), variable=self.level_var, value=3, cursor="hand2")
        r3.pack(anchor="w", pady=2)

        f_sched = ctk.CTkFrame(parent, fg_color="transparent")
        f_sched.pack(fill="x", pady=10)
        self.sched_enabled = ctk.BooleanVar(value=self.config_data.get("schedule",{}).get("enabled", False))
        ctk.CTkCheckBox(f_sched, text=self._("Enable automatic scheduling"), variable=self.sched_enabled,
                        onvalue=True, offvalue=False).pack(anchor="w")

        btn_apply = ctk.CTkButton(parent, text=self._("Apply"), fg_color=self.acc_color,
                                   command=self.apply_config, width=150)
        btn_apply.pack(pady=20)

    def apply_config(self):
        try:
            self.config_data["username"] = self.entry_user.get()
            for k, v in config.LANGUAGES.items():
                if v == self.lang_var.get():
                    self.config_data["language"] = k
                    break
            for k, v in config.SCALES.items():
                if v == self.scale_var.get():
                    self.config_data["ui_scale"] = k
                    break
            theme_map = {"Still": "grey", "Tecno": "dark", "Snow": "light"}
            self.config_data["theme"] = theme_map.get(self.theme_var.get(), "default")
            self.config_data["open_file_in_tab"] = self.tab_var.get()
            self.config_data["expert_level"] = self.level_var.get()
            self.config_data["simple_mode"] = (self.level_var.get() == 1)
            if "schedule" not in self.config_data:
                self.config_data["schedule"] = {}
            self.config_data["schedule"]["enabled"] = self.sched_enabled.get()
            self._save_config()
            self.show_toast(self._("Settings saved! Restarting..."), duration=2000)
            self.after(2000, self._restart_app)
        except Exception as e:
            logging.error(f"Error applying settings: {e}")

    def _restart_app(self):
        python = sys.executable
        subprocess.Popen([python, "-m", "core.main"])
        self.quit()

    def _fill_about(self, parent):
        ctk.CTkLabel(parent, text=self._("About SpeedScan"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        card = ctk.CTkFrame(parent, fg_color=self.light_bg, corner_radius=15,
                            border_width=2, border_color=self.acc_color)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        info = f"""{self._("⚡ SpeedScan")}
{self._("Version")} {config.VERSION}
{self._("Developer: Ewerton Vasconcelos")}
{self._("Technologies: Python, CustomTkinter, psutil")}
{self._("Repository: github.com/ewertonvasconcelos/speedscan")}
{self._("This software is under development.")}
{self._("Main features:")}
{self._("• Dashboard with customizable widgets")}
{self._("• CPU, RAM, disk, GPU and temperature monitoring")}
{self._("• Optimization: cache, swap, turbo mode and browser cleanup")}
{self._("• Network: ping, DNS, speedtest, LAN scanner, LANCache")}
{self._("• Diagnostics for drivers and hardware")}
{self._("• Process manager with actions")}
{self._("• Historical performance graphs")}
{self._("• Security checks (ports, firewall, updates)")}
{self._("• Proactive AI with suggestions and local chat")}
{self._("• Selective cookie manager")}
{self._("• Internal trash for deleted items")}
{self._("• Automatic task scheduling")}
{self._("• Expert levels (Beginner, Intermediate, Advanced)")}
{self._("• Detailed tooltips")}
{self._("• Customizable themes")}
© 2026 Ewerton Vasconcelos. {self._("All rights reserved.")}"""
        label_info = ctk.CTkLabel(card, text=info, font=("Inter", 12), justify="left", text_color=self.text_color)
        label_info.pack(pady=20, padx=30, fill="both", expand=True)

    def _fill_windows_cleaner(self, parent):
        if self.SO != "Windows" or self.windows_cleaner is None:
            ctk.CTkLabel(parent, text=self._("⚠️ This module is exclusive to Windows!\n\nRun SpeedScan on a Windows system to access these features."),
                         font=("Inter", 20), text_color=self.acc_color, justify="center").pack(expand=True)
            return
        ctk.CTkLabel(parent, text=self._("Windows Cleanup"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ctk.CTkFrame(main_frame, fg_color=self.bg_color, corner_radius=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(left_frame, text=self._("Installed Bloatware"), font=("Inter", 16, "bold"),
                     text_color=self.acc_color).pack(anchor="w", padx=10, pady=(10,5))
        self.bloatware_vars = {}
        installed = self.windows_cleaner.get_installed_bloatware()
        if not installed:
            ctk.CTkLabel(left_frame, text=self._("No known bloatware found."), font=("Inter", 12)).pack(anchor="w", padx=20, pady=5)
        else:
            scroll_frame = ctk.CTkScrollableFrame(left_frame, height=200, fg_color="transparent")
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
            for app in installed:
                var = ctk.BooleanVar()
                self.bloatware_vars[app["package"]] = var
                cb = ctk.CTkCheckBox(scroll_frame, text=app["name"], variable=var,
                                      onvalue=True, offvalue=False, cursor="hand2")
                cb.pack(anchor="w", pady=2)
        btn_remove = ctk.CTkButton(left_frame, text=self._("Remove Selected"),
                                   command=self._remove_selected_bloatware,
                                   fg_color=self.acc_color, width=150)
        btn_remove.pack(pady=10)

        right_frame = ctk.CTkFrame(main_frame, fg_color=self.bg_color, corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)
        ctk.CTkLabel(right_frame, text=self._("System Tweaks"), font=("Inter", 16, "bold"),
                     text_color=self.acc_color).pack(anchor="w", padx=10, pady=(10,5))
        self.telemetry_var = ctk.BooleanVar()
        ctk.CTkCheckBox(right_frame, text=self._("Disable Telemetry"), variable=self.telemetry_var,
                        onvalue=True, offvalue=False, cursor="hand2").pack(anchor="w", padx=20, pady=2)
        self.ai_vars = {}
        for comp in self.windows_cleaner.ai_components:
            var = ctk.BooleanVar()
            self.ai_vars[comp["name"]] = var
            ctk.CTkCheckBox(right_frame, text=self._("Disable {name}").format(name=comp["name"]),
                            variable=var, onvalue=True, offvalue=False, cursor="hand2").pack(anchor="w", padx=20, pady=2)
        self.cleanup_var = ctk.BooleanVar()
        ctk.CTkCheckBox(right_frame, text=self._("Clean temporary files and cache"), variable=self.cleanup_var,
                        onvalue=True, offvalue=False, cursor="hand2").pack(anchor="w", padx=20, pady=2)
        btn_exec = ctk.CTkButton(right_frame, text=self._("Execute Selected Actions"),
                                 command=self._execute_windows_cleanup,
                                 fg_color=self.acc_color, width=200)
        btn_exec.pack(pady=20)
        self.windows_console = ctk.CTkTextbox(parent, height=150, fg_color="#1e1e1e", text_color="#ffffff",
                                               font=("Consolas", 10), corner_radius=10)
        self.windows_console.pack(fill="x", padx=10, pady=(0,10))

    def _remove_selected_bloatware(self):
        selected = [pkg for pkg, var in self.bloatware_vars.items() if var.get()]
        if not selected:
            self.show_toast(self._("No bloatware selected."))
            return
        self.windows_console.delete("1.0", "end")
        self.windows_console.insert("end", self._("Removing bloatware...\n"))
        for pkg in selected:
            self.windows_console.insert("end", self._("Removing {pkg}...\n").format(pkg=pkg))
            success = self.windows_cleaner.remove_package(pkg, lambda msg: self.windows_console.insert("end", msg+"\n"))
            self.windows_console.insert("end", self._("✓ {pkg} removed.\n").format(pkg=pkg) if success else self._("✗ Failed to remove {pkg}.\n").format(pkg=pkg))
        self.windows_console.see("end")
        self.show_toast(self._("Removal completed."))

    def _execute_windows_cleanup(self):
        self.windows_console.delete("1.0", "end")
        self.windows_console.insert("end", self._("Executing actions...\n"))
        if self.telemetry_var.get():
            self.windows_console.insert("end", self._("Disabling telemetry...\n"))
            success = self.windows_cleaner.disable_telemetry(lambda msg: self.windows_console.insert("end", msg+"\n"))
            self.windows_console.insert("end", self._("Telemetry disabled.\n") if success else self._("Failed to disable telemetry.\n"))
        for name, var in self.ai_vars.items():
            if var.get():
                self.windows_console.insert("end", self._("Disabling {name}...\n").format(name=name))
                success = self.windows_cleaner.disable_ai_component(name, lambda msg: self.windows_console.insert("end", msg+"\n"))
                self.windows_console.insert("end", self._("{name} disabled.\n").format(name=name) if success else self._("Failed to disable {name}.\n").format(name=name))
        if self.cleanup_var.get():
            self.windows_console.insert("end", self._("Cleaning temporary files...\n"))
            success = self.windows_cleaner.run_cleanup(lambda msg: self.windows_console.insert("end", msg+"\n"))
            self.windows_console.insert("end", self._("Cleanup completed.\n") if success else self._("Cleanup failed.\n"))
        self.windows_console.see("end")
        self.show_toast(self._("Actions executed."))

    # ------------------------------------------------------------------------
    # Card execution and console management
    # ------------------------------------------------------------------------
    def run_card_action(self, cmd, tag, is_dns):
        log = self.logs.get(tag)
        if not log:
            return
        log.delete("1.0", "end")

        # Se o console estiver visível, escondê-lo e resetar o botão
        if tag in self.consoles_visible and self.consoles_visible[tag]:
            log.pack_forget()
            btn = self.detail_buttons.get(tag)
            if btn:
                btn.configure(text=self._("Details ▼"))
            self.consoles_visible[tag] = False

        # Mostra o botão de detalhes no canto direito (aparece imediatamente)
        btn = self.detail_buttons.get(tag)
        if btn and not btn.winfo_ismapped():
            btn.pack(side="right", anchor="e", padx=10, pady=5)

        threading.Thread(target=self._execute_command, args=(cmd, log, tag, is_dns), daemon=True).start()

    def _execute_command(self, cmd, log, tag, is_dns):
        if is_dns:
            self._change_dns(cmd, log)
            return
        action_map = {
            "cache": self.action_handler.run_cache_clean,
            "swap": self.action_handler.run_swap_reset,
            "check": self.action_handler.run_fs_check,
            "turbo": self.action_handler.run_turbo_mode,
            "steam": self.action_handler.run_steam_clean,
            "lutris": self.action_handler.run_lutris_clean,
            "heroic": self.action_handler.run_heroic_clean,
            "bottles": self.action_handler.run_bottles_clean,
            "wine": self.action_handler.run_wine_clean,
            "mangohud": self.action_handler.run_mangohud_config,
            "governor": self.action_handler.run_governor_config,
            "dolphin": self.action_handler.run_dolphin_clean,
            "browsers": self.action_handler.run_browser_clean,
            "services": self.action_handler.run_services_manager,
            "logs": self.action_handler.run_log_analysis,
            "cookies": self.action_handler.run_cookie_manager,
            "trim": self.action_handler.run_trim,
            "fix_broken": self.action_handler.run_fix_broken,
            "ping": self._run_ping,
            "speedtest": self._run_speedtest,
            "ethtool": self._run_ethtool,
            "dhclient": self._run_dhclient,
            "ports": self._run_ports,
            "traceroute": self._run_traceroute,
            "wifi": self._run_wifi,
            "testdns": self._run_testdns,
            "lanscan": self._run_lanscan,
            "lancache": self._run_lancache,
            "public_ip": self._run_public_ip,
            "pci": self._run_pci,
            "update": self._run_update,
            "usb": self._run_usb,
            "modules": self._run_modules,
            "cpu_info": self._run_cpu_info,
            "firmware": self._run_firmware,
            "video_drv": self._run_video_drv,
            "net_drv": self._run_net_drv,
            "auto_update": self._run_auto_update,
            "firewall": self._run_firewall,
            "sec_updates": self._run_sec_updates,
        }
        method = action_map.get(cmd)
        if method:
            try:
                method(log)
            except Exception as e:
                log.insert("end", self._("Error executing command: {e}\n").format(e=e))
        else:
            log.insert("end", self._("Unknown command: {cmd}\n").format(cmd=cmd))

    # ------------------------------------------------------------------------
    # Helper command methods
    # ------------------------------------------------------------------------
    def _run_ping(self, log):
        log.insert("end", self._("Pinging google.com...\n"))
        self._run_subprocess(["ping", "-c", "4", "google.com"], log)

    def _run_speedtest(self, log):
        log.insert("end", self._("Running speed test...\n"))
        def callback(res):
            log.insert("end", self.speed_tester.format_result(res) + "\n")
        self.speed_tester.run_test(callback)

    def _run_ethtool(self, log):
        log.insert("end", self._("Running ethtool...\n"))
        self._run_subprocess(["ethtool", "eth0"], log)

    def _run_dhclient(self, log):
        log.insert("end", self._("Renewing IP via dhclient...\n"))
        self._run_subprocess(["sudo", "dhclient", "-v"], log, use_sudo=True)

    def _run_ports(self, log):
        log.insert("end", self._("Scanning open ports...\n"))
        ports = self.security_scanner.scan_open_ports()
        for p in ports:
            log.insert("end", p + "\n")

    def _run_traceroute(self, log):
        log.insert("end", self._("Running traceroute to google.com...\n"))
        self._run_subprocess(["traceroute", "google.com"], log)

    def _run_wifi(self, log):
        log.insert("end", self._("Wi-Fi info...\n"))
        self._run_subprocess(["iwconfig"], log)

    def _run_testdns(self, log):
        log.insert("end", self._("Testing DNS (google.com)...\n"))
        self._run_subprocess(["nslookup", "google.com"], log)

    def _run_lanscan(self, log):
        log.insert("end", self._("Scanning local network...\n"))
        devices = self.lan_scanner.scan_network()
        for d in devices:
            log.insert("end", f"{d['ip']} - {d['mac']} - {d['hostname']} - {d['vendor']}\n")

    def _run_lancache(self, log):
        log.insert("end", self._("Checking LANCache...\n"))
        log.insert("end", self.lan_cache.get_status() + "\n")

    def _run_public_ip(self, log):
        import requests
        log.insert("end", self._("Obtaining public IP...\n"))
        try:
            ip = requests.get("https://api.ipify.org", timeout=5).text
            log.insert("end", self._("Public IP: {ip}\n").format(ip=ip))
        except:
            log.insert("end", self._("Error obtaining public IP.\n"))

    def _run_pci(self, log):
        self._run_subprocess(["lspci"], log)

    def _run_update(self, log):
        log.insert("end", self._("Updating package list...\n"))
        self._run_subprocess(["sudo", "apt", "update"], log, use_sudo=True)

    def _run_usb(self, log):
        self._run_subprocess(["lsusb"], log)

    def _run_modules(self, log):
        self._run_subprocess(["lsmod"], log)

    def _run_cpu_info(self, log):
        try:
            with open("/proc/cpuinfo") as f:
                log.insert("end", f.read())
        except:
            log.insert("end", self._("Could not read /proc/cpuinfo.\n"))

    def _run_firmware(self, log):
        self._run_subprocess(["dmesg", "|", "grep", "-i", "firmware"], log, shell=True)

    def _run_video_drv(self, log):
        self._run_subprocess(["lspci", "|", "grep", "-i", "vga"], log, shell=True)

    def _run_net_drv(self, log):
        self._run_subprocess(["lspci", "|", "grep", "-i", "network"], log, shell=True)

    def _run_auto_update(self, log):
        log.insert("end", self._("Configuring auto updates (not implemented).\n"))

    def _run_firewall(self, log):
        log.insert("end", self._("Checking firewall...\n"))
        status = self.security_scanner.check_firewall_status()
        log.insert("end", status)

    def _run_sec_updates(self, log):
        log.insert("end", self._("Checking security updates...\n"))
        updates = self.security_scanner.check_security_updates()
        for u in updates:
            log.insert("end", u + "\n")

    def _change_dns(self, dns_ip, log):
        log.insert("end", self._("Changing DNS to {dns_ip}...\n").format(dns_ip=dns_ip))
        if hasattr(self, "action_mapper"):
            cmd = self.action_mapper.dns_command(dns_ip)
            if cmd:
                self._run_subprocess(cmd, log, shell=True)
            else:
                log.insert("end", self._("Could not generate DNS command for this OS.\n"))
        else:
            log.insert("end", self._("ActionMapper not available.\n"))

    def _run_subprocess(self, cmd, log, use_sudo=False, shell=False):
        try:
            if use_sudo and self.SO == "Linux":
                if isinstance(cmd, list):
                    cmd = ["sudo"] + cmd
                else:
                    cmd = "sudo " + cmd
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True,
                                    bufsize=1,
                                    shell=shell)
            for line in proc.stdout:
                log.insert("end", line)
            proc.wait()
        except Exception as e:
            log.insert("end", self._("Error executing command: {e}\n").format(e=e))

    # ------------------------------------------------------------------------
    # Console toggling
    # ------------------------------------------------------------------------
    def toggle_console(self, tag):
        btn = self.detail_buttons.get(tag)
        log = self.logs.get(tag)
        if not btn or not log:
            return
        if self.consoles_visible.get(tag, False):
            log.pack_forget()
            btn.configure(text=self._("Details ▼"))
            self.consoles_visible[tag] = False
        else:
            log.pack(fill="x", expand=True, padx=5, before=btn)
            btn.configure(text=self._("Hide Details ▲"))
            self.consoles_visible[tag] = True

    # ------------------------------------------------------------------------
    # Placeholder methods
    # ------------------------------------------------------------------------
    def _update_ai_suggestions(self):
        pass

    def _check_process_queue(self):
        pass

    # ------------------------------------------------------------------------
    # Window management
    # ------------------------------------------------------------------------
    def _monitor_loop(self):
        while True:
            time.sleep(3)

    def _on_mousewheel(self, event):
        widget = event.widget
        if self.SO == "Linux":
            delta = -1 if event.num == 4 else 1
        else:
            delta = -1 * (event.delta / 120)
        while widget:
            if isinstance(widget, ctk.CTkScrollableFrame):
                if self.SO == "Linux":
                    widget._parent_canvas.yview_scroll(delta, "units")
                else:
                    widget._parent_canvas.yview_scroll(int(delta), "units")
                return
            widget = widget.master

    def _setup_bindings(self):
        if self.SO == "Linux":
            self.bind_all("<Button-4>", self._on_mousewheel)
            self.bind_all("<Button-5>", self._on_mousewheel)
        else:
            self.bind_all("<MouseWheel>", self._on_mousewheel)

    def show_toast(self, message, duration=3000):
        toast = ctk.CTkLabel(self, text=message,
                             fg_color=self.acc_color,
                             text_color="white",
                             corner_radius=10,
                             font=("Inter", 12),
                             padx=20, pady=10)
        toast.place(relx=0.5, rely=0.5, anchor="center")
        self.after(duration, toast.destroy)

    def _check_first_run(self):
        if self.config_data == config.DEFAULT_CONFIG:
            wizard = FirstRunWizard(self, self.config_data)
            self.wait_window(wizard)
            self.config_data = self._load_config()
            self.update_theme_vars()
            self._save_config()
            self.show_toast(self._("Initial settings saved! Some changes may require restart."))

    def _restore_window_state(self):
        ws = self.config_data.get("window_state", config.DEFAULT_CONFIG["window_state"])
        if ws.get("maximized", False):
            self._maximize_window()
        else:
            w = ws.get("width", 1000)
            h = ws.get("height", 700)
            x = ws.get("x")
            y = ws.get("y")
            w = max(w, self.winfo_width())
            h = max(h, self.winfo_height())
            self.update_idletasks()
            if x is not None and y is not None:
                self.geometry(f"{w}x{h}+{x}+{y}")
            else:
                self.geometry(f"{w}x{h}")
            self.update_idletasks()

    def _save_window_state(self):
        ws = {}
        try:
            if self.state() == "zoomed" or self.attributes("-zoomed"):
                ws["maximized"] = True
            else:
                ws["maximized"] = False
                geom = self.geometry()
                match = re.match(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", geom)
                if match:
                    ws["width"] = int(match.group(1))
                    ws["height"] = int(match.group(2))
                    ws["x"] = int(match.group(3))
                    ws["y"] = int(match.group(4))
                else:
                    ws["width"] = self.winfo_width()
                    ws["height"] = self.winfo_height()
                    ws["x"] = self.winfo_x()
                    ws["y"] = self.winfo_y()
        except Exception as e:
            logging.error(f"Error saving window state: {e}")
            ws = config.DEFAULT_CONFIG["window_state"]
        self.config_data["window_state"] = ws
        self._save_config()

    def _on_closing(self):
        self._save_window_state()
        self.metrics_collector.stop()
        self.proc_manager.stop_monitoring()
        self.quit()
        self.destroy()

    def _maximize_window(self):
        try:
            self.attributes("-zoomed", True)
        except:
            try:
                self.state("zoomed")
            except:
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f"{w}x{h}+0+0")
                self.update()

    # ------------------------------------------------------------------------
    # Dashboard widgets (called by Dashboard class)
    # ------------------------------------------------------------------------
    def widget_hostname(self, frame, tag):
        import socket
        hostname = socket.gethostname()
        label = ctk.CTkLabel(frame, text=hostname, font=("Inter", 16))
        label.pack(expand=True)

    def widget_distro(self, frame, tag):
        text = f"{platform.system()} {platform.release()}"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_kernel(self, frame, tag):
        text = platform.version()
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_uptime(self, frame, tag):
        from datetime import datetime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        delta = datetime.now() - boot_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        text = f"{days}d {hours}h {minutes}m"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_cpu(self, frame, tag):
        percent = psutil.cpu_percent(interval=0.1)
        text = f"{percent}%"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_ram(self, frame, tag):
        mem = psutil.virtual_memory()
        text = f"{mem.percent}% ({mem.used // (1024**3)} GB / {mem.total // (1024**3)} GB)"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_gpu(self, frame, tag):
        try:
            result = subprocess.run(["lspci", "|", "grep", "-i", "vga"], capture_output=True, text=True, shell=True)
            text = result.stdout.strip().split("\n")[0][:50] if result.stdout else "N/A"
        except:
            text = "N/A"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_disks(self, frame, tag):
        disk = psutil.disk_usage("/")
        text = f"{disk.percent}% ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_battery(self, frame, tag):
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = self._("Charging") if battery.power_plugged else self._("Discharging")
            text = f"{percent}% ({plugged})"
        else:
            text = self._("No battery")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_temps(self, frame, tag):
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    text = f"{entries[0].current}°C"
                    break
            else:
                text = "N/A"
        else:
            text = "N/A"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_health(self, frame, tag):
        health = self.health_monitor.calculate_health_score()
        text = str(health["score"])
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_realtime_chart(self, frame, tag):
        from core.dashboard import RealTimeChartWidget
        chart = RealTimeChartWidget(frame, tag)
        if not hasattr(self, "_charts"):
            self._charts = []
        self._charts.append(chart)

if __name__ == "__main__":
    app = SpeedScan()
    app.mainloop()
EOF

# -------------------- actions.py --------------------
cat > core/actions.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actions module: command running and mapping for multiple operating systems.
Version 1.0.0
"""
import logging
import os
import subprocess
from core import config

class CommandRunner:
    def __init__(self, so):
        self.so = so
    def run(self, cmd, use_sudo=False, parent=None):
        try:
            if use_sudo and self.so == "Linux":
                if isinstance(cmd, list):
                    cmd = ["pkexec"] + cmd
                else:
                    cmd = f"pkexec {cmd}"
            elif use_sudo and self.so == "Windows":
                if isinstance(cmd, list):
                    cmd = ["runas", "/user:Administrator"] + cmd
                else:
                    cmd = f"runas /user:Administrator {cmd}"
            elif use_sudo and self.so == "Darwin":
                if isinstance(cmd, list):
                    cmd_str = " ".join(cmd)
                else:
                    cmd_str = cmd
                script = f'do shell script "{cmd_str}" with administrator privileges'
                cmd = ["osascript", "-e", script]
            if isinstance(cmd, list):
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, bufsize=1)
            else:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, bufsize=1)
            return proc
        except Exception as e:
            logging.error(f"Error executing command: {e}")
            return None

class ActionMapper:
    def __init__(self, so, runner, turbo_active=False):
        self.so = so
        self.runner = runner
        self.turbo_active = turbo_active
    def get_command(self, action):
        commands = {
            "cache": {
                "Linux": "sudo du -sh /var/cache/apt/archives && sudo apt-get clean",
                "Windows": "cleanmgr /sagerun:1",
                "Darwin": "sudo du -sh ~/Library/Caches && sudo rm -rf ~/Library/Caches/*"
            },
            "swap": {
                "Linux": "sudo swapoff -a && sudo swapon -a",
                "Windows": "echo Swap reset is not applicable on Windows",
                "Darwin": "sudo purge"
            },
            "check": {
                "Linux": "sudo fsck -A -R -y",
                "Windows": "chkdsk /f",
                "Darwin": "sudo fsck -fy"
            },
            "turbo": {
                "Linux": "echo Turbo mode enabled (adjusts performance)",
                "Windows": "powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
                "Darwin": "sudo nvram boot-args=\"keepsyms=1 debug=0x144\""
            },
            "steam": {
                "Linux": "steam",
                "Windows": "start steam://",
                "Darwin": "open -a Steam"
            },
            "lutris": {
                "Linux": "lutris",
                "Windows": "lutris",
                "Darwin": "lutris"
            },
            "heroic": {
                "Linux": "heroic",
                "Windows": "heroic",
                "Darwin": "heroic"
            },
            "bottles": {
                "Linux": "bottles",
                "Windows": "bottles",
                "Darwin": "bottles"
            },
            "wine": {
                "Linux": "wine --version",
                "Windows": "wine --version",
                "Darwin": "wine --version"
            },
            "mangohud": {
                "Linux": "mangohud",
                "Windows": "echo MangoHud is not available on Windows",
                "Darwin": "echo MangoHud is not available on macOS"
            },
            "governor": {
                "Linux": "governor",
                "Windows": "echo Governor is not available on Windows",
                "Darwin": "echo Governor is not available on macOS"
            },
            "dolphin": {
                "Linux": "dolphin-emu",
                "Windows": "start dolphin",
                "Darwin": "open -a Dolphin"
            },
            "pci": {
                "Linux": "lspci",
                "Windows": "wmic path win32_pnpentity get /format:list",
                "Darwin": "system_profiler SPHardwareDataType"
            },
            "update": {
                "Linux": "sudo apt update && sudo apt upgrade -y",
                "Windows": "wuauclt /detectnow /updatenow",
                "Darwin": "softwareupdate -i -a"
            },
            "usb": {
                "Linux": "lsusb",
                "Windows": "wmic path win32_usbcontrollerdevice get /format:list",
                "Darwin": "system_profiler SPUSBDataType"
            },
            "modules": {
                "Linux": "lsmod",
                "Windows": "driverquery",
                "Darwin": "kextstat"
            },
            "cpu_info": {
                "Linux": "lscpu",
                "Windows": "wmic cpu get",
                "Darwin": "sysctl -a | grep machdep.cpu"
            },
            "firmware": {
                "Linux": "sudo dmesg | grep -i firmware",
                "Windows": "wmic bios get",
                "Darwin": "system_profiler SPFirmwareDataType"
            },
            "ethtool": {
                "Linux": "sudo ethtool eth0",
                "Windows": "ipconfig /all",
                "Darwin": "ifconfig"
            },
            "dhclient": {
                "Linux": "sudo dhclient -v",
                "Windows": "ipconfig /renew",
                "Darwin": "sudo dhclient"
            },
            "ports": {
                "Linux": "sudo netstat -tulpn",
                "Windows": "netstat -an",
                "Darwin": "sudo lsof -i -P | grep LISTEN"
            },
            "traceroute": {
                "Linux": "traceroute google.com",
                "Windows": "tracert google.com",
                "Darwin": "traceroute google.com"
            },
            "wifi": {
                "Linux": "iwconfig",
                "Windows": "netsh wlan show interfaces",
                "Darwin": "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I"
            },
            "testdns": {
                "Linux": "nslookup google.com",
                "Windows": "nslookup google.com",
                "Darwin": "nslookup google.com"
            },
            "ping": {
                "Linux": "ping -c 4 google.com",
                "Windows": "ping -n 4 google.com",
                "Darwin": "ping -c 4 google.com"
            },
            "services": {
                "Linux": "systemctl list-units --type=service --state=running --no-pager",
                "Windows": "sc query | findstr /C:\"SERVICE_NAME\" /C:\"STATE\"",
                "Darwin": "launchctl list"
            },
            "logs": {
                "Linux": "journalctl -p 3 -b --no-pager | head -20",
                "Windows": "Get-EventLog -LogName System -EntryType Error -Newest 20 | Format-Table -AutoSize",
                "Darwin": "log show --predicate 'eventMessage contains \"error\"' --last 1h | head -20"
            },
            "trim": {
                "Linux": "sudo fstrim -v /",
                "Windows": "echo TRIM is not applicable on Windows (automatically handled)",
                "Darwin": "sudo trimforce enable"
            },
            "fix_broken": {
                "Linux": "sudo apt --fix-broken install",
                "Windows": "echo Not applicable on Windows",
                "Darwin": "echo Not applicable on macOS"
            },
            "public_ip": {
                "Linux": "curl -s ifconfig.me",
                "Windows": "curl -s ifconfig.me",
                "Darwin": "curl -s ifconfig.me"
            }
        }
        if action in commands:
            return commands[action].get(self.so, "Command not supported on this OS")
        return None
    def dns_command(self, dns_ip):
        if self.so == "Linux":
            return f"echo 'nameserver {dns_ip}' | sudo tee /etc/resolv.conf"
        elif self.so == "Windows":
            return f"netsh interface ip set dns name='Ethernet' static {dns_ip}"
        elif self.so == "Darwin":
            return f"networksetup -setdnsservers Wi-Fi {dns_ip}"
        return None

class ActionHandler:
    def __init__(self, app):
        self.app = app
    def _run_linux_command(self, cmd, log, use_sudo=True):
        proc = self.app.runner.run(cmd, use_sudo=use_sudo, parent=self.app)
        if proc:
            for line in proc.stdout:
                self.app.after(0, lambda l=line: log.insert("end", l))
            proc.wait()
            return True
        return False
    def run_cache_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Cleaning memory cache...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        success = self._run_linux_command(["sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], log, use_sudo=True)
        log.insert("end", "✅ Cache cleaned successfully.\n" if success else "❌ Error cleaning cache.\n")
    def run_swap_reset(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔄 Resetting swap...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        self._run_linux_command(["sudo", "swapoff", "-a"], log, use_sudo=True)
        self._run_linux_command(["sudo", "swapon", "-a"], log, use_sudo=True)
        log.insert("end", "✅ Swap reset.\n")
    def run_fs_check(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔍 Verifying filesystem errors...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        self._run_linux_command(["sudo", "fsck", "-A", "-R", "-y"], log, use_sudo=True)
        log.insert("end", "✅ Verification completed.\n")
    def run_turbo_mode(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🚀 Activating turbo mode...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        self._run_linux_command(["sudo", "cpupower", "frequency-set", "-g", "performance"], log, use_sudo=True)
        log.insert("end", "✅ Turbo mode activated.\n")
    def run_steam_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Cleaning Steam cache...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        paths = ["~/.local/share/Steam", "~/.steam/steam/appcache", "~/.steam/root"]
        for p in paths:
            path = os.path.expanduser(p)
            if os.path.exists(path):
                self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Steam cache cleaned.\n")
    def run_lutris_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Cleaning Lutris cache...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        path = os.path.expanduser("~/.local/share/lutris")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Lutris cache cleaned.\n")
    def run_heroic_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Cleaning Heroic Launcher cache...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        path = os.path.expanduser("~/.config/heroic/cache")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Heroic cache cleaned.\n")
    def run_bottles_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Cleaning Bottles cache...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        path = os.path.expanduser("~/.local/share/bottles")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Bottles cache cleaned.\n")
    def run_wine_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Cleaning Wine cache...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        path = os.path.expanduser("~/.wine")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Wine cache cleaned.\n")
    def run_mangohud_config(self, log):
        log.delete("1.0", "end")
        log.insert("end", "⚙️ Configuring Mangohud...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        if self._run_linux_command(["which", "mangohud"], log, use_sudo=False):
            log.insert("end", "✅ Mangohud is already installed.\n")
        else:
            log.insert("end", "❌ Mangohud not found. Install with: sudo apt install mangohud\n")
    def run_governor_config(self, log):
        log.delete("1.0", "end")
        log.insert("end", "⚙️ Configuring CPU governor...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        if self._run_linux_command(["which", "cpupower"], log, use_sudo=False):
            self._run_linux_command(["sudo", "cpupower", "frequency-set", "-g", "ondemand"], log, use_sudo=True)
            log.insert("end", "✅ Governor configured to ondemand.\n")
        else:
            log.insert("end", "❌ cpupower not found. Install linux-tools-common.\n")
    def run_dolphin_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Cleaning Dolphin Emulator cache...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        path = os.path.expanduser("~/.local/share/dolphin-emu/cache")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Dolphin cache cleaned.\n")
    def run_browser_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "Starting browser cleanup...\n")
        results = self.app.browser_cleaner.clean_all_browsers(preserve_cookies=False, cookie_keep_list=None)
        total_freed = 0
        for browser, data in results.items():
            if data.get("cache_freed") or data.get("cookies_freed") or data.get("history_freed"):
                log.insert("end", f"\n{data['name']}:\n")
                if data.get("cache_freed"):
                    log.insert("end", f"  Cache: {self.app.browser_cleaner.format_bytes(data['cache_freed'])}\n")
                    total_freed += data["cache_freed"]
                if data.get("cookies_freed"):
                    log.insert("end", f"  Cookies: {self.app.browser_cleaner.format_bytes(data['cookies_freed'])}\n")
                    total_freed += data["cookies_freed"]
                if data.get("history_freed"):
                    log.insert("end", f"  History: {self.app.browser_cleaner.format_bytes(data['history_freed'])}\n")
                    total_freed += data["history_freed"]
                if data.get("errors"):
                    log.insert("end", f"  Errors: {', '.join(data['errors'])}\n")
        log.insert("end", f"\n✅ Total freed: {self.app.browser_cleaner.format_bytes(total_freed)}\n")
    def run_services_manager(self, log):
        log.delete("1.0", "end")
        log.insert("end", "⚙️ Service manager (under development)...\n")
    def run_log_analysis(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🗂️ Log analysis (under development)...\n")
    def run_cookie_manager(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🗑️ Cookie Manager\n" + "="*40 + "\n")
        summary = self.app.cookie_manager.get_cookie_summary()
        if not summary:
            log.insert("end", "No cookies found.\n")
            return
        log.insert("end", f"Total domains with cookies: {len(summary)}\n")
        for domain, count in list(summary.items())[:10]:
            log.insert("end", f"{domain}: {count} cookies\n")
        if len(summary) > 10:
            log.insert("end", f"... and {len(summary)-10} more domains.\n")
    def run_trim(self, log):
        log.delete("1.0", "end")
        log.insert("end", "💾 Executing TRIM on SSDs...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        self._run_linux_command(["sudo", "fstrim", "-v", "/"], log, use_sudo=True)
        log.insert("end", "✅ TRIM completed.\n")
    def run_fix_broken(self, log):
        log.delete("1.0", "end")
        log.insert("end", "📦 Repairing broken packages...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operation only for Linux.\n")
            return
        self._run_linux_command(["sudo", "apt", "--fix-broken", "install"], log, use_sudo=True)
        log.insert("end", "✅ Repair completed.\n")
    def special_command(self, cmd, log):
        if cmd == "video_drv":
            log.insert("end", "Detecting GPU...\nFunctionality under development.\n")
        elif cmd == "net_drv":
            log.insert("end", "Detecting network card...\nFunctionality under development.\n")
        elif cmd == "auto_update":
            log.insert("end", "Configuring auto updates...\nFunctionality under development.\n")
        elif cmd == "cookies":
            self.run_cookie_manager(log)
        elif cmd == "empty_trash":
            self.app.trash_manager.empty_trash()
            log.insert("end", "🗑️ Trash emptied.\n")
EOF

# -------------------- ui.py --------------------
cat > core/ui.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI utility functions for the SpeedScan application.
Version 1.0.0
"""
import customtkinter as ctk

def add_tooltip(widget, text):
    tooltip = None
    def enter(event):
        nonlocal tooltip
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        tooltip = ctk.CTkToplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tooltip, text=text, justify="left",
                              fg_color="#2b2b2b", text_color="white",
                              corner_radius=5, padx=5, pady=5)
        label.pack()
    def leave(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

def create_card_grid(parent, items, tag_prefix, acc_color, bg_color, text_color, command_callback):
    grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
    grid_frame.pack(fill="x", pady=5)
    ping_labels = []
    for idx, (label, cmd, is_dns) in enumerate(items):
        row, col = divmod(idx, 3)
        card = ctk.CTkFrame(grid_frame, fg_color=bg_color, corner_radius=10,
                            border_width=1, border_color=acc_color)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        card.grid_propagate(False)
        card.configure(height=150)
        title = ctk.CTkLabel(card, text=label, font=("Inter", 14, "bold"), text_color=acc_color)
        title.pack(pady=(10,5))
        if cmd == "ping":
            ping_label = ctk.CTkLabel(card, text="-- ms", font=("Inter", 18, "bold"), text_color=text_color)
            ping_label.pack(expand=True)
            ping_labels.append(ping_label)
            btn = ctk.CTkButton(card, text="Start", fg_color=acc_color,
                                command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d),
                                cursor="hand2")
            btn.pack(pady=5)
        else:
            btn = ctk.CTkButton(card, text="Run", fg_color=acc_color,
                                command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d),
                                cursor="hand2")
            btn.pack(expand=True)
    for i in range(3):
        grid_frame.columnconfigure(i, weight=1)
    return ping_labels

def add_console(parent, tag_prefix, acc_color, toggle_callback):
    console = ctk.CTkTextbox(parent, height=150, fg_color="#1e1e1e", text_color="#ffffff",
                             font=("Consolas", 10), corner_radius=10)
    btn = ctk.CTkButton(parent, text="Details ▼", fg_color=acc_color,
                        command=lambda: toggle_callback(tag_prefix), cursor="hand2")
    # O botão NÃO é empacotado aqui – será mostrado dinamicamente ao executar um card.
    return btn, console
EOF

# -------------------- i18n.py --------------------
cat > core/i18n.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internationalization (i18n) module for SpeedScan.
Version 1.0.0
"""
import gettext
from pathlib import Path
from core import config

LOCALE_DIR = Path(__file__).parent.parent / "locale"

def get_translation(language=None):
    if language is None:
        try:
            cfg = config.load_config()
            language = cfg.get("language", "pt_BR")
        except Exception:
            language = "pt_BR"
    try:
        translation = gettext.translation(
            "speedscan",
            localedir=str(LOCALE_DIR),
            languages=[language]
        )
        return translation.gettext
    except FileNotFoundError:
        return gettext.gettext

_ = get_translation("pt_BR")
EOF

# -------------------- config.py --------------------
cat > core/config.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Central configuration file for SpeedScan.
"""
import os
from pathlib import Path

VERSION = "1.0.0"

CONFIG_FILE = Path.home() / ".speedscan_config"
ICON_PATH = Path.home() / "speedscan" / "assets" / "icon.png"
LOG_DIR = Path.home() / "speedscan" / "logs"
AGENT_SCRIPT = Path.home() / "speedscan" / "speedscan-agent.py"

DEFAULT_CONFIG = {
    "theme": "default",
    "username": "user",
    "language": "pt_BR",
    "ui_scale": "auto",
    "open_file_in_tab": False,
    "simple_mode": True,
    "expert_level": 1,
    "window_state": {
        "maximized": False,
        "width": 1000,
        "height": 700,
        "x": None,
        "y": None
    },
    "schedule": {
        "enabled": False,
        "frequency": "weekly",
        "hour": "03:00",
        "day_of_week": "monday",
        "day_of_month": 1,
        "interval_days": 7,
        "tasks": ["cache", "swap", "check"],
        "elevated": False
    },
    "ai": {
        "provider": "ollama",
        "model": "llama3.2",
        "api_key": "",
        "endpoint": "http://localhost:11434"
    }
}

THEMES = {
    "default": {"mode": "dark", "bg": "#1e293b", "side": "#0f172a", "acc": "#a855f7", "text": "#ffffff"},
    "grey":   {"mode": "light", "bg": "#d1d5db", "side": "#374151", "acc": "#4b5563", "text": "#111827"},
    "dark":   {"mode": "dark", "bg": "#080808", "side": "#000000", "acc": "#10b981", "text": "#ffffff"},
    "light":  {"mode": "light", "bg": "#ffffff", "side": "#f8fafc", "acc": "#2563eb", "text": "#0f172a"}
}

THEME_DISPLAY_NAMES = {
    "grey": "Still",
    "dark": "Tecno",
    "light": "Snow"
}

LANGUAGES = {
    "pt_BR": "Português Brasileiro",
    "en_US": "English (US)",
    "es_ES": "Español"
}

SCALES = {
    "auto": "Auto",
    "100": "100%",
    "125": "125%",
    "150": "150%"
}

AI_SUGGESTIONS = [
    "Ollama (local)",
    "OpenAI GPT",
    "Google Gemini",
    "Claude (Anthropic)",
    "Llama 3 (Meta)",
    "Mistral AI",
    "Cohere",
    "DeepSeek",
    "Configure Local AI"
]
EOF

# -------------------- dashboard.py --------------------
cat > core/dashboard.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard module with 3 fixed slots and available widgets in two rows (4+4).
Version 1.0.0
"""
import customtkinter as ctk
import json
import logging
from pathlib import Path
from core import config

DASHBOARD_CONFIG = Path.home() / ".speedscan_dashboard.json"

WIDGET_TYPES = [
    {"id": "hostname", "name": "Hostname", "callback": "widget_hostname"},
    {"id": "distro", "name": "Distribution", "callback": "widget_distro"},
    {"id": "kernel", "name": "Kernel", "callback": "widget_kernel"},
    {"id": "uptime", "name": "Uptime", "callback": "widget_uptime"},
    {"id": "cpu", "name": "CPU", "callback": "widget_cpu"},
    {"id": "ram", "name": "RAM", "callback": "widget_ram"},
    {"id": "gpu", "name": "GPU", "callback": "widget_gpu"},
    {"id": "disks", "name": "Disks", "callback": "widget_disks"},
    {"id": "battery", "name": "Battery", "callback": "widget_battery"},
    {"id": "temps", "name": "Temperatures", "callback": "widget_temps"},
    {"id": "health", "name": "Health", "callback": "widget_health"},
]

class SlotWidget(ctk.CTkFrame):
    def __init__(self, parent, slot_index, widget_type, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.slot_index = slot_index
        self.widget_type = widget_type
        self.app = app_instance
        self.content_frame = None
        self.configure(
            fg_color=app_instance.bg_color,
            corner_radius=10,
            border_width=1,
            border_color=app_instance.acc_color,
        )
        self.pack_propagate(False)
        self.configure(height=200)
        self.title_label = ctk.CTkLabel(
            self,
            text=widget_type["name"],
            font=("Inter", 14, "bold"),
            text_color=app_instance.acc_color,
        )
        self.title_label.pack(pady=(5, 0))
        self.update_content()

    def update_content(self):
        if self.content_frame:
            self.content_frame.destroy()
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        callback_name = self.widget_type["callback"]
        callback = getattr(self.app, callback_name)
        callback(self.content_frame, f"slot_{self.slot_index}")

    def set_widget_type(self, new_type):
        self.widget_type = new_type
        self.title_label.configure(text=new_type["name"])
        self.update_content()

class Dashboard(ctk.CTkFrame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.slots = []
        self.available_widgets = []
        self.configure(fg_color="transparent")
        self._build_ui()
        self.load_state()

    def _build_ui(self):
        slots_frame = ctk.CTkFrame(self, fg_color="transparent")
        slots_frame.pack(fill="x", pady=10)
        for i in range(3):
            slot_frame = ctk.CTkFrame(slots_frame, fg_color="transparent")
            slot_frame.pack(side="left", fill="both", expand=True, padx=5)
            self.slots.append(slot_frame)
        available_label = ctk.CTkLabel(
            self,
            text="Available widgets:",
            font=("Inter", 14, "bold"),
            text_color=self.app.acc_color,
        )
        available_label.pack(anchor="center", pady=(20, 10))
        self.available_container = ctk.CTkFrame(self, fg_color="transparent")
        self.available_container.pack(anchor="center", pady=5)
        self.row1_frame = ctk.CTkFrame(self.available_container, fg_color="transparent")
        self.row1_frame.pack(pady=3)
        self.row2_frame = ctk.CTkFrame(self.available_container, fg_color="transparent")
        self.row2_frame.pack(pady=3)

    def load_state(self):
        if DASHBOARD_CONFIG.exists():
            try:
                with open(DASHBOARD_CONFIG) as f:
                    data = json.load(f)
                slot_ids = data.get("slots", [])
                available_ids = data.get("available", [])
            except Exception as e:
                logging.error(f"Error loading dashboard configuration: {e}")
                slot_ids = []
                available_ids = []
        else:
            slot_ids = []
            available_ids = []
        if not slot_ids:
            slot_ids = ["hostname", "distro", "uptime"]
            available_ids = [w["id"] for w in WIDGET_TYPES if w["id"] not in slot_ids]
        def find_widget(wid):
            for w in WIDGET_TYPES:
                if w["id"] == wid:
                    return w
            return WIDGET_TYPES[0]
        slot_widgets = [find_widget(wid) for wid in slot_ids]
        available_widgets = []
        for wid in available_ids:
            w = find_widget(wid)
            if w not in slot_widgets:
                available_widgets.append(w)
        for w in WIDGET_TYPES:
            if w not in slot_widgets and w not in available_widgets:
                available_widgets.append(w)
        self.available_widgets = available_widgets
        for i, slot_frame in enumerate(self.slots):
            if i < len(slot_widgets):
                widget_type = slot_widgets[i]
            else:
                widget_type = WIDGET_TYPES[0]
            slot_widget = SlotWidget(
                slot_frame, i, widget_type, self.app, fg_color=self.app.bg_color
            )
            slot_widget.pack(fill="both", expand=True)
            self.slots[i] = slot_widget
        self._update_available_buttons()
        self.save_state()

    def save_state(self):
        data = {
            "slots": [slot.widget_type["id"] for slot in self.slots],
            "available": [w["id"] for w in self.available_widgets],
        }
        with open(DASHBOARD_CONFIG, "w") as f:
            json.dump(data, f, indent=2)

    def _update_available_buttons(self):
        for child in self.row1_frame.winfo_children():
            child.destroy()
        for child in self.row2_frame.winfo_children():
            child.destroy()
        total = len(self.available_widgets)
        if total >= 8:
            first_half = self.available_widgets[:4]
            second_half = self.available_widgets[4:8]
        else:
            half = (total + 1) // 2
            first_half = self.available_widgets[:half]
            second_half = self.available_widgets[half:]
        for widget in first_half:
            btn = ctk.CTkButton(
                self.row1_frame,
                text=f"➕ {widget['name']}",
                fg_color=self.app.acc_color,
                height=40,
                corner_radius=8,
                command=lambda w=widget: self.add_to_slot(w),
                cursor="hand2",
            )
            btn.pack(side="left", padx=8, pady=5)
        for widget in second_half:
            btn = ctk.CTkButton(
                self.row2_frame,
                text=f"➕ {widget['name']}",
                fg_color=self.app.acc_color,
                height=40,
                corner_radius=8,
                command=lambda w=widget: self.add_to_slot(w),
                cursor="hand2",
            )
            btn.pack(side="left", padx=8, pady=5)
        self.row1_frame.pack_configure(anchor="center")
        self.row2_frame.pack_configure(anchor="center")

    def add_to_slot(self, widget):
        current_slots = [slot.widget_type for slot in self.slots]
        new_slot0 = widget
        new_slot1 = current_slots[0]
        new_slot2 = current_slots[1]
        removed = current_slots[2]
        self.slots[0].set_widget_type(new_slot0)
        self.slots[1].set_widget_type(new_slot1)
        self.slots[2].set_widget_type(new_slot2)
        if widget in self.available_widgets:
            self.available_widgets.remove(widget)
        if removed not in [s.widget_type for s in self.slots]:
            self.available_widgets.append(removed)
        seen = set()
        unique = []
        for w in self.available_widgets:
            if w["id"] not in seen:
                seen.add(w["id"])
                unique.append(w)
        self.available_widgets = unique
        self._update_available_buttons()
        self.save_state()
EOF

# -------------------- ai_proactive.py --------------------
cat > core/ai_proactive.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proactive AI module - Suggests optimizations based on metrics.
Version 1.0.0
"""
import logging
import psutil
import time
from core.cookie_manager import CookieManager
from core.trash_manager import TrashManager
from core import config

class AIProactive:
    def __init__(self, metrics_db, health_monitor):
        self.metrics_db = metrics_db
        self.health_monitor = health_monitor
        self.cookie_mgr = CookieManager()
        self.trash_mgr = TrashManager()

    def analyze(self):
        suggestions = []

        disk_usage = psutil.disk_usage("/")
        if disk_usage.percent > 90:
            suggestions.append({
                "title": "⚠️ Low disk space",
                "description": f"Disk is at {disk_usage.percent:.1f}% usage. Free up space.",
                "action": "browsers",
                "priority": "high"
            })
        elif disk_usage.percent > 75:
            suggestions.append({
                "title": "💿 Disk space",
                "description": f"Disk is at {disk_usage.percent:.1f}% usage. Consider cache clean.",
                "action": "cache",
                "priority": "medium"
            })

        mem = psutil.virtual_memory()
        if mem.percent > 90:
            suggestions.append({
                "title": "⚠️ High RAM memory",
                "description": f"RAM usage is {mem.percent:.1f}%. Close heavy applications.",
                "action": None,
                "priority": "high"
            })
        elif mem.percent > 80:
            suggestions.append({
                "title": "📈 RAM memory",
                "description": f"RAM usage is {mem.percent:.1f}%. Consider restarting.",
                "action": None,
                "priority": "medium"
            })

        try:
            temps = psutil.sensors_temperatures()
            for sensor, entries in temps.items():
                for entry in entries:
                    if entry.current > 80:
                        suggestions.append({
                            "title": "🔥 High temperature",
                            "description": f"{sensor}: {entry.current}°C. Check cooling.",
                            "action": None,
                            "priority": "high"
                        })
                        break
        except Exception as e:
            logging.error(f"Error accessing temperatures: {e}")
            pass

        battery = psutil.sensors_battery()
        if battery and battery.percent < 20 and not battery.power_plugged:
            suggestions.append({
                "title": "🔋 Low battery",
                "description": f"Battery at {battery.percent:.1f}%. Plug in charger.",
                "action": None,
                "priority": "high"
            })

        health = self.health_monitor.calculate_health_score()
        if health["score"] < 50:
            suggestions.append({
                "title": "🩺 System health critical",
                "description": "Health score is low. Run optimizations.",
                "action": "check",
                "priority": "high"
            })
        elif health["score"] < 70:
            suggestions.append({
                "title": "🩺 System health",
                "description": "Health score is medium. Consider cleaning.",
                "action": "cache",
                "priority": "medium"
            })

        stats = self.metrics_db.get_stats(period_hours=24)
        if stats.get("cpu_avg") and stats["cpu_avg"] > 80:
            suggestions.append({
                "title": "📊 CPU consistently high",
                "description": f"Average CPU over last 24h: {stats['cpu_avg']:.1f}%. Check processes.",
                "action": None,
                "priority": "medium"
            })
        if stats.get("mem_avg") and stats["mem_avg"] > 80:
            suggestions.append({
                "title": "📊 Memory consistently high",
                "description": f"Average memory over last 24h: {stats['mem_avg']:.1f}%.",
                "action": None,
                "priority": "medium"
            })

        cookie_sites = self.cookie_mgr.get_cookie_summary()
        if cookie_sites and len(cookie_sites) > 50:
            suggestions.append({
                "title": "🍪 Many cookies stored",
                "description": f"You have cookies from {len(cookie_sites)} sites. Cleaning cookies may free space.",
                "action": "cookies",
                "priority": "low"
            })

        trash_size = self.trash_mgr.get_trash_size()
        if trash_size > 100 * 1024 * 1024:
            suggestions.append({
                "title": "🗑️ Trash is full",
                "description": f"Trash contains {trash_size / (1024*1024):.1f} MB. Empty it?",
                "action": "empty_trash",
                "priority": "medium"
            })

        return suggestions

    def get_summary(self):
        suggestions = self.analyze()
        if not suggestions:
            return "✅ No suggestions at the moment. System is OK!"
        lines = []
        for s in suggestions:
            priority_emojis = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(s["priority"], "⚪")
            lines.append(f"{priority_emojis} {s['title']}: {s['description']}")
        return "\n".join(lines)
EOF

# -------------------- browser_cleaner.py --------------------
cat > core/browser_cleaner.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser cleaner module - cleans cache, cookies, and history from major browsers.
Version 1.0.0
"""
import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional

class BrowserCleaner:
    def __init__(self):
        self.browsers = {
            "chrome": {
                "name": "Google Chrome",
                "cache_paths": [
                    Path.home() / ".cache/google-chrome",
                    Path.home() / ".config/google-chrome/Default/Cache"
                ],
                "cookies_path": Path.home() / ".config/google-chrome/Default/Cookies",
                "history_path": Path.home() / ".config/google-chrome/Default/History"
            },
            "chromium": {
                "name": "Chromium",
                "cache_paths": [
                    Path.home() / ".cache/chromium",
                    Path.home() / ".config/chromium/Default/Cache"
                ],
                "cookies_path": Path.home() / ".config/chromium/Default/Cookies",
                "history_path": Path.home() / ".config/chromium/Default/History"
            },
            "firefox": {
                "name": "Firefox",
                "profile_pattern": Path.home() / ".mozilla/firefox/*.default-release",
                "cache_subdir": "cache2",
                "cookies_file": "cookies.sqlite",
                "places_file": "places.sqlite"
            },
            "brave": {
                "name": "Brave",
                "cache_paths": [
                    Path.home() / ".cache/Brave-Browser",
                    Path.home() / ".config/Brave-Browser/Default/Cache"
                ],
                "cookies_path": Path.home() / ".config/Brave-Browser/Default/Cookies",
                "history_path": Path.home() / ".config/Brave-Browser/Default/History"
            }
        }
    def clean_browser(self, browser_key: str, preserve_cookies: bool = False,
                      cookie_keep_list: Optional[List[str]] = None) -> Dict:
        result = {"cache_freed": 0, "cookies_freed": 0, "history_freed": 0, "errors": []}
        browser = self.browsers.get(browser_key)
        if not browser:
            return result
        if "cache_paths" in browser:
            for path in browser["cache_paths"]:
                if path.exists():
                    try:
                        size = self._get_size(path)
                        shutil.rmtree(path)
                        result["cache_freed"] += size
                    except Exception as e:
                        result["errors"].append(f"Cache: {e}")
        elif browser_key == "firefox":
            profiles = list(Path.home().glob(".mozilla/firefox/*.default-release"))
            if profiles:
                profile = profiles[0]
                cache_dir = profile / browser["cache_subdir"]
                if cache_dir.exists():
                    try:
                        size = self._get_size(cache_dir)
                        shutil.rmtree(cache_dir)
                        result["cache_freed"] += size
                    except Exception as e:
                        result["errors"].append(f"Cache: {e}")
        if not preserve_cookies:
            if "cookies_path" in browser:
                path = browser["cookies_path"]
                if path.exists():
                    try:
                        size = path.stat().st_size
                        path.unlink()
                        result["cookies_freed"] += size
                    except Exception as e:
                        result["errors"].append(f"Cookies: {e}")
            elif browser_key == "firefox":
                profiles = list(Path.home().glob(".mozilla/firefox/*.default-release"))
                if profiles:
                    profile = profiles[0]
                    cookies_file = profile / browser["cookies_file"]
                    if cookies_file.exists():
                        try:
                            size = cookies_file.stat().st_size
                            cookies_file.unlink()
                            result["cookies_freed"] += size
                        except Exception as e:
                            result["errors"].append(f"Cookies: {e}")
        if "history_path" in browser:
            path = browser["history_path"]
            if path.exists():
                try:
                    size = path.stat().st_size
                    path.unlink()
                    result["history_freed"] += size
                except Exception as e:
                    result["errors"].append(f"History: {e}")
        elif browser_key == "firefox":
            profiles = list(Path.home().glob(".mozilla/firefox/*.default-release"))
            if profiles:
                profile = profiles[0]
                places_file = profile / browser["places_file"]
                if places_file.exists():
                    try:
                        size = places_file.stat().st_size
                        places_file.unlink()
                        result["history_freed"] += size
                    except Exception as e:
                        result["errors"].append(f"History: {e}")
        return result
    def clean_all_browsers(self, preserve_cookies: bool = False,
                           cookie_keep_list: Optional[List[str]] = None) -> Dict:
        results = {}
        for key in self.browsers:
            results[key] = self.clean_browser(key, preserve_cookies, cookie_keep_list)
            results[key]["name"] = self.browsers[key]["name"]
        return results
    def _get_size(self, path: Path) -> int:
        total = 0
        try:
            for entry in path.iterdir():
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self._get_size(entry)
        except:
            pass
        return total
    @staticmethod
    def format_bytes(num_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if num_bytes < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} TB"
EOF

# -------------------- chat.py --------------------
cat > core/chat.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat interface for integration with AI providers (Ollama, OpenAI, DeepSeek, etc.)
Version 1.0.0
"""
import customtkinter as ctk
import threading
import requests
import json
import logging
from pathlib import Path
from core import config

class ChatFrame(ctk.CTkFrame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.configure(fg_color="transparent")
        self.history = []
        self.current_ai = app_instance.config_data.get("ai", {}).get("provider", "ollama")
        self.ai_model = app_instance.config_data.get("ai", {}).get("model", "llama3.2")
        self.endpoint = app_instance.config_data.get("ai", {}).get("endpoint", "http://localhost:11434")
        self.api_key = app_instance.config_data.get("ai", {}).get("api_key", "")
        self.chat_display = ctk.CTkTextbox(self, wrap="word", font=("Inter", 12),
                                            fg_color=self.app.light_bg,
                                            text_color=self.app.text_color)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_display.configure(state="disabled")
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0,10))
        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Type your message...")
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        self.send_btn = ctk.CTkButton(input_frame, text="Send", command=self.send_message,
                                      fg_color=self.app.acc_color, cursor="hand2")
        self.send_btn.pack(side="right")
        self._add_message("system", "🤖 Connected to assistant. Type /help for commands.")
    def _add_message(self, role, content):
        self.chat_display.configure(state="normal")
        if role == "user":
            self.chat_display.insert("end", f"You: {content}\n\n")
        elif role == "assistant":
            self.chat_display.insert("end", f"AI: {content}\n\n")
        elif role == "system":
            self.chat_display.insert("end", f"{content}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        self.history.append({"role": role, "content": content})
    def send_message(self):
        msg = self.message_entry.get().strip()
        if not msg:
            return
        self.message_entry.delete(0, "end")
        self._add_message("user", msg)
        if msg.startswith("/"):
            self._handle_command(msg)
            return
        threading.Thread(target=self._get_ai_response, args=(msg,), daemon=True).start()
    def _handle_command(self, cmd):
        if cmd == "/help":
            self._add_message("system", "Available commands:\n/help - show this help\n/clear - clear chat\n/model - show current model\n/trash - list trash items\n/emptytrash - empty trash")
        elif cmd == "/clear":
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
            self.history = []
            self._add_message("system", "🗑️ Chat cleared.")
        elif cmd == "/model":
            self._add_message("system", f"Current model: {self.current_ai} ({self.ai_model})")
        elif cmd == "/trash":
            items = self.app.trash_manager.list_trash()
            if items:
                msg = "Items in trash:\n" + "\n".join([f"{i['name']} (original: {i['original']})" for i in items])
            else:
                msg = "Trash is empty."
            self._add_message("system", msg)
        elif cmd == "/emptytrash":
            self.app.trash_manager.empty_trash()
            self._add_message("system", "🗑️ Trash emptied.")
        else:
            self._add_message("system", f"Unknown command: {cmd}")
    def _get_ai_response(self, user_message):
        if self.current_ai == "ollama":
            self._query_ollama(user_message)
        elif self.current_ai == "openai":
            self._query_openai(user_message)
        elif self.current_ai == "deepseek":
            self._query_deepseek(user_message)
        else:
            self.app.after(0, lambda: self._add_message("system", "⚠️ Provider not supported."))
    def _query_ollama(self, message):
        try:
            messages = [{"role": m["role"], "content": m["content"]} for m in self.history if m["role"] != "system"]
            payload = {
                "model": self.ai_model,
                "messages": messages,
                "stream": False
            }
            response = requests.post(f"{self.endpoint}/api/chat", json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                reply = data.get("message", {}).get("content", "No response.")
                self.app.after(0, lambda: self._add_message("assistant", reply))
            else:
                self.app.after(0, lambda: self._add_message("system", f"Error Ollama: {response.status_code}"))
        except Exception as e:
            logging.error(f"Error querying Ollama: {e}")
            self.app.after(0, lambda e=e: self._add_message("system", f"Error connecting to Ollama: {e}"))
    def _query_openai(self, message):
        self.app.after(0, lambda: self._add_message("system", "⚠️ OpenAI not implemented. Configure your key."))
    def _query_deepseek(self, message):
        self.app.after(0, lambda: self._add_message("system", "⚠️ DeepSeek not implemented."))
EOF

# -------------------- cookie_manager.py --------------------
cat > core/cookie_manager.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie manager for browsers - read, backup, restore, and delete cookies.
Version 1.0.0
"""
import logging
import sqlite3
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from core import config

class CookieManager:
    def __init__(self):
        self.cookie_files = {
            "chrome": Path.home() / ".config/google-chrome/Default/Cookies",
            "chromium": Path.home() / ".config/chromium/Default/Cookies",
            "firefox": Path.home() / ".mozilla/firefox/*.default-release/cookies.sqlite",
            "brave": Path.home() / ".config/Brave-Browser/Default/Cookies",
            "edge": Path.home() / ".config/microsoft-edge/Default/Cookies",
            "opera": Path.home() / ".config/opera/Default/Cookies",
            "chromium-flatpak": Path.home() / ".var/app/org.chromium.Chromium/config/chromium/Default/Cookies",
            "firefox-flatpak": Path.home() / ".var/app/org.mozilla.firefox/.mozilla/firefox/*.default-release/cookies.sqlite",
        }
    def get_cookies_from_browser(self, browser_key: str) -> List[Dict]:
        path = self.cookie_files.get(browser_key)
        if not path:
            return []
        if "*" in str(path):
            paths = list(Path(str(path).replace("*", "")).parent.glob("*.default-release"))
            if not paths:
                return []
            path = paths[0] / "cookies.sqlite"
        if not path.exists():
            return []
        cookies = []
        try:
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, value FROM cookies")
            rows = cursor.fetchall()
            for row in rows:
                cookies.append({"host": row[0], "name": row[1], "value": row[2]})
            conn.close()
            return cookies
        except Exception as e:
            logging.error(f"Error reading cookies from {browser_key}: {e}")
            return []
    def get_cookie_summary(self) -> Dict[str, int]:
        summary = {}
        for browser in self.cookie_files:
            cookies = self.get_cookies_from_browser(browser)
            for c in cookies:
                host = c["host"]
                summary[host] = summary.get(host, 0) + 1
        return summary
    def backup_cookies(self, browser_key: str, backup_path: Path) -> bool:
        src = self.cookie_files.get(browser_key)
        if not src or not src.exists():
            return False
        shutil.copy2(src, backup_path)
        return True
    def restore_cookies(self, backup_path: Path, browser_key: str) -> bool:
        dest = self.cookie_files.get(browser_key)
        if not dest:
            return False
        shutil.copy2(backup_path, dest)
        return True
    def delete_cookies_except(self, browser_key: str, keep_domains: List[str]) -> bool:
        path = self.cookie_files.get(browser_key)
        if not path:
            return False
        if "*" in str(path):
            paths = list(Path(str(path).replace("*", "")).parent.glob("*.default-release"))
            if not paths:
                return False
            path = paths[0] / "cookies.sqlite"
        if not path.exists():
            return False
        try:
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name FROM cookies")
            all_cookies = cursor.fetchall()
            for host, name in all_cookies:
                if host not in keep_domains:
                    cursor.execute("DELETE FROM cookies WHERE host_key=? AND name=?", (host, name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"Error deleting cookies: {e}")
            return False
EOF

# -------------------- first_run.py --------------------
cat > core/first_run.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
First run wizard for SpeedScan - displayed on first start to configure basic settings.
Version 1.0.0
"""
import customtkinter as ctk
from core import config

class FirstRunWizard(ctk.CTkToplevel):
    def __init__(self, parent, config_data):
        super().__init__(parent)
        self.parent = parent
        self.config = config_data
        self.title("Welcome to SpeedScan!")
        self.geometry("600x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        title = ctk.CTkLabel(self, text="⚡ SpeedScan", font=("Inter", 24, "bold"),
                              text_color=parent.acc_color)
        title.grid(row=0, column=0, pady=(20,10))
        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        welcome = ctk.CTkLabel(self.content_frame,
                               text="Thank you for installing SpeedScan! Let's configure your preferences.",
                               font=("Inter", 12), justify="left", wraplength=500)
        welcome.pack(pady=10)
        name_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(name_frame, text="Your name:", font=("Inter", 12)).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="Enter your name")
        self.name_entry.pack(fill="x", pady=5)
        self.name_entry.insert(0, config_data.get("username", ""))
        theme_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(theme_frame, text="Preferred theme:", font=("Inter", 12)).pack(anchor="w")
        self.theme_var = ctk.StringVar(value="Still")
        theme_menu = ctk.CTkOptionMenu(theme_frame, values=["Still", "Tecno", "Snow"],
                                       variable=self.theme_var, cursor="left_ptr")
        theme_menu.pack(anchor="w", pady=5)
        level_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        level_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(level_frame, text="Your experience level:", font=("Inter", 12)).pack(anchor="w")
        self.level_var = ctk.StringVar(value="beginner")
        beginner_radio = ctk.CTkRadioButton(level_frame, text="Beginner (basic features only)",
                                            variable=self.level_var, value="beginner", cursor="hand2")
        beginner_radio.pack(anchor="w", pady=2)
        intermediate_radio = ctk.CTkRadioButton(level_frame, text="Intermediate (basic + some advanced)",
                                                variable=self.level_var, value="intermediate", cursor="hand2")
        intermediate_radio.pack(anchor="w", pady=2)
        advanced_radio = ctk.CTkRadioButton(level_frame, text="Advanced (all features, no restrictions)",
                                            variable=self.level_var, value="advanced", cursor="hand2")
        advanced_radio.pack(anchor="w", pady=2)
        tip = ctk.CTkLabel(self.content_frame,
                           text="💡 You can change these settings later at any time in the 'Settings' tab.",
                           font=("Inter", 10, "italic"), text_color="#888888")
        tip.pack(pady=20)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=20)
        ctk.CTkButton(btn_frame, text="Finish", command=self.save_and_close,
                      fg_color=self.parent.acc_color, width=150, cursor="hand2").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy,
                      fg_color="gray", width=100, cursor="hand2").pack(side="left", padx=10)
    def save_and_close(self):
        self.config["username"] = self.name_entry.get() or "User"
        theme_map = {"Still": "grey", "Tecno": "dark", "Snow": "light"}
        self.config["theme"] = theme_map.get(self.theme_var.get(), "default")
        level = self.level_var.get()
        if level == "beginner":
            self.config["simple_mode"] = True
            self.config["expert_level"] = 1
        elif level == "intermediate":
            self.config["simple_mode"] = False
            self.config["expert_level"] = 2
        else:
            self.config["simple_mode"] = False
            self.config["expert_level"] = 3
        self.parent.config_data.update(self.config)
        self.parent._save_config()
        self.parent.show_toast("Settings saved! Some changes may require restart.")
        self.destroy()
EOF

# -------------------- hardware.py --------------------
cat > core/hardware.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware information collection module.
Version 1.0.0
"""
import platform
import psutil
import subprocess
import logging
from core import config

class HardwareInfo:
    def __init__(self, so, runner):
        self.so = so
        self.runner = runner
    def get_distro(self):
        if self.so == "Linux":
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=")[1].strip().strip('"')
            except Exception as e:
                logging.error(f"Error reading /etc/os-release: {e}")
            return f"{psutil.cpu_count()}-core"
        return platform.system() + " " + platform.release()
    def get_ram(self):
        try:
            mem = psutil.virtual_memory()
            total = mem.total // (1024**3)
            used = mem.used // (1024**3)
            return f"{used} GB / {total} GB"
        except:
            return "N/A"
    def get_gpu(self):
        try:
            if self.so == "Linux":
                out = subprocess.run(["lspci"], capture_output=True, text=True)
                for line in out.stdout.splitlines():
                    if "VGA" in line or "3D" in line:
                        return line.split(":")[2].strip()
            elif self.so == "Windows":
                out = subprocess.run(["wmic", "path", "win32_videocontroller", "get", "name"],
                                     capture_output=True, text=True)
                lines = out.stdout.splitlines()
                if len(lines) >= 2:
                    return lines[1].strip()
            elif self.so == "Darwin":
                out = subprocess.run(["system_profiler", "SPDisplaysDataType"],
                                     capture_output=True, text=True)
                for line in out.stdout.splitlines():
                    if "Chipset Model" in line:
                        return line.split(":")[1].strip()
        except:
            pass
        return "Unknown"
EOF

# -------------------- health_score.py --------------------
cat > core/health_score.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Score calculation module (0-100) for system health.
Version 1.0.0
"""
import psutil
import time
import logging
from core import config

class HealthScore:
    def __init__(self):
        self.last_cpu = psutil.cpu_percent(interval=0.1)
    def calculate_health_score(self):
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime = time.time() - psutil.boot_time()
        battery = psutil.sensors_battery()
        battery_score = 0
        if battery:
            battery_score = battery.percent
        cpu_weight = 0.3
        mem_weight = 0.3
        disk_weight = 0.2
        uptime_weight = 0.1
        battery_weight = 0.1 if battery else 0
        cpu_score = 100 - cpu_percent
        mem_score = 100 - mem.percent
        disk_score = 100 - disk.percent
        uptime_days = uptime / 86400
        uptime_score = min(100, uptime_days * 100 / 7) if uptime_days < 7 else 100
        total_weight = cpu_weight + mem_weight + disk_weight + uptime_weight + battery_weight
        weighted_score = (
            cpu_score * cpu_weight +
            mem_score * mem_weight +
            disk_score * disk_weight +
            uptime_score * uptime_weight +
            battery_score * battery_weight
        ) / total_weight
        score = round(weighted_score, 1)
        return {
            "score": score,
            "details": {
                "cpu": cpu_score,
                "memory": mem_score,
                "disk": disk_score,
                "uptime": uptime_score,
                "battery": battery_score if battery else None
            }
        }
EOF

# -------------------- historical_metrics.py --------------------
cat > core/historical_metrics.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historical metrics collection and storage module (non-blocking).
Version 1.0.0
"""
import sqlite3
import time
import threading
import logging
from pathlib import Path
import psutil
from core import config

DB_PATH = Path.home() / "speedscan" / "metrics.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class MetricsDB:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    cpu REAL,
                    memory REAL,
                    disk_usage REAL,
                    disk_io_read REAL,
                    disk_io_write REAL,
                    net_sent REAL,
                    net_recv REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)")
    def insert(self, cpu=None, memory=None, disk_usage=None,
               disk_io_read=None, disk_io_write=None,
               net_sent=None, net_recv=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO metrics
                    (timestamp, cpu, memory, disk_usage, disk_io_read, disk_io_write, net_sent, net_recv)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (time.time(), cpu, memory, disk_usage, disk_io_read, disk_io_write, net_sent, net_recv))
        except Exception as e:
            logging.error(f"Failed to insert metrics: {e}")
    def get_last_hours(self, hours=1, metrics=None):
        if metrics is None:
            metrics = ["timestamp", "cpu", "memory", "disk_usage"]
        else:
            if "timestamp" not in metrics:
                metrics = ["timestamp"] + metrics
        cols = ", ".join(metrics)
        cutoff = time.time() - hours * 3600
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"SELECT {cols} FROM metrics WHERE timestamp >= ? ORDER BY timestamp", (cutoff,))
            rows = cursor.fetchall()
        return rows
    def prune_old(self, days=7):
        cutoff = time.time() - days * 24 * 3600
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
    def get_stats(self, period_hours=1):
        cutoff = time.time() - period_hours * 3600
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT AVG(cpu), MIN(cpu), MAX(cpu),
                       AVG(memory), MIN(memory), MAX(memory),
                       AVG(disk_usage), MIN(disk_usage), MAX(disk_usage)
                FROM metrics WHERE timestamp >= ?
            """, (cutoff,))
            row = cursor.fetchone()
        return {
            "cpu_avg": row[0], "cpu_min": row[1], "cpu_max": row[2],
            "mem_avg": row[3], "mem_min": row[4], "mem_max": row[5],
            "disk_avg": row[6], "disk_min": row[7], "disk_max": row[8]
        }

class MetricsCollector:
    def __init__(self, interval=5):
        self.interval = interval
        self.db = MetricsDB()
        self._stop_event = threading.Event()
        self._thread = None
        self._last_disk_io = psutil.disk_io_counters()
        self._last_net_io = psutil.net_io_counters()
        self._last_time = time.time()
    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._collect_loop, daemon=True)
            self._thread.start()
            logging.debug("Metrics collector started.")
    def stop(self):
        self._stop_event.set()
        logging.debug("Metrics collector stopping.")
    def _collect_loop(self):
        while not self._stop_event.is_set():
            self._collect_once()
            for _ in range(self.interval * 2):
                if self._stop_event.is_set():
                    return
                time.sleep(0.5)
    def _collect_once(self):
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            now = time.time()
            dt = now - self._last_time
            if disk_io and self._last_disk_io and dt > 0:
                read_bps = (disk_io.read_bytes - self._last_disk_io.read_bytes) / dt
                write_bps = (disk_io.write_bytes - self._last_disk_io.write_bytes) / dt
            else:
                read_bps = write_bps = None
            if net_io and self._last_net_io and dt > 0:
                sent_bps = (net_io.bytes_sent - self._last_net_io.bytes_sent) / dt
                recv_bps = (net_io.bytes_recv - self._last_net_io.bytes_recv) / dt
            else:
                sent_bps = recv_bps = None
            self._last_disk_io = disk_io
            self._last_net_io = net_io
            self._last_time = now
            self.db.insert(
                cpu=cpu,
                memory=mem,
                disk_usage=disk,
                disk_io_read=read_bps,
                disk_io_write=write_bps,
                net_sent=sent_bps,
                net_recv=recv_bps
            )
            if int(now) % 3600 < 5:
                self.db.prune_old(days=7)
        except Exception as e:
            logging.error(f"Error during metrics collection: {e}")
EOF

# -------------------- lan_scanner.py --------------------
cat > core/lan_scanner.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local area network scanner module.
Version 1.0.0
"""
import logging
import subprocess
import re
import ipaddress
import threading
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from core import config

class LANScanner:
    def __init__(self, interface=None):
        self.interface = interface
        self.devices = []
        self.network = None
        self.scan_callback = None
        self._stop_scan = False
    def get_local_network(self) -> Optional[str]:
        try:
            result = subprocess.run(["ip", "route"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "default via" in line:
                    parts = line.split()
                    iface = parts[4] if len(parts) > 4 else None
                    result2 = subprocess.run(["ip", "-4", "addr", "show", iface], capture_output=True, text=True)
                    for line2 in result2.stdout.splitlines():
                        if "inet" in line2:
                            match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", line2)
                            if match:
                                ip = match.group(1)
                                prefix = match.group(2)
                                network = ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
                                return str(network)
            return None
        except Exception as e:
            logging.error(f"Error determining local network: {e}")
            return None
    def ping_host(self, ip: str) -> bool:
        try:
            result = subprocess.run(["ping", "-c", "1", "-W", "1", ip], timeout=2)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error pinging {ip}: {e}")
            return False
    def arp_lookup(self, ip: str) -> Optional[Dict]:
        try:
            result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[0] == ip and "lladdr" in line:
                    mac = parts[3] if len(parts) > 3 else None
                    return {"ip": ip, "mac": mac}
        except Exception as e:
            logging.error(f"Error in arp_lookup for {ip}: {e}")
            pass
        try:
            result = subprocess.run(["ip", "neigh", "show", ip], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if ip in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        mac = parts[4] if re.match(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", parts[4]) else None
                        return {"ip": ip, "mac": mac}
        except Exception as e:
            logging.error(f"Error in arp_lookup (fallback) for {ip}: {e}")
            pass
        return None
    def get_hostname(self, ip: str) -> Optional[str]:
        try:
            result = subprocess.run(["nslookup", ip], capture_output=True, text=True, timeout=2)
            match = re.search(r"name = (.+)\.", result.stdout)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logging.error(f"Error in nslookup for {ip}: {e}")
            return None
    def get_vendor(self, mac: str) -> str:
        if not mac:
            return "Unknown"
        oui = mac.replace(":", "").upper()[:6]
        vendors = {
            "001122": "Fabrikant A",
            "AABBCC": "Fabrikant B",
        }
        return vendors.get(oui, "Unknown")
    def scan_network(self, network_cidr: str = None, progress_callback=None) -> List[Dict]:
        if network_cidr is None:
            network_cidr = self.get_local_network()
            if network_cidr is None:
                return [{"error": "Unable to determine the local network."}]
        self._stop_scan = False
        network = ipaddress.IPv4Network(network_cidr, strict=False)
        hosts = list(network.hosts())
        total = len(hosts)
        devices = []
        max_hosts = 254
        if total > max_hosts:
            hosts = hosts[:max_hosts]
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_ip = {executor.submit(self.ping_host, str(ip)): str(ip) for ip in hosts}
            for i, future in enumerate(as_completed(future_to_ip)):
                if self._stop_scan:
                    executor.shutdown(wait=False)
                    break
                ip = future_to_ip[future]
                try:
                    is_alive = future.result()
                except Exception as e:
                    logging.error(f"Error pinging {ip}: {e}")
                    is_alive = False
                if is_alive:
                    arp_info = self.arp_lookup(ip)
                    mac = arp_info["mac"] if arp_info else None
                    hostname = self.get_hostname(ip)
                    vendor = self.get_vendor(mac) if mac else "Unknown"
                    devices.append({
                        "ip": ip,
                        "mac": mac if mac else "N/A",
                        "hostname": hostname if hostname else "Unknown",
                        "vendor": vendor,
                        "status": "active"
                    })
                if progress_callback:
                    progress_callback(i+1, total, ip, is_alive)
        self.devices = devices
        return devices
    def stop_scan(self):
        self._stop_scan = True
    def get_scan_summary(self) -> str:
        active = len([d for d in self.devices if d.get("status") == "active"])
        total = len(self.devices)
        return f"Active devices: {active}/{total}"
EOF

# -------------------- process_manager.py --------------------
cat > core/process_manager.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process management module (thread-safe with queue).
Version 1.0.0
"""
import logging
import queue
import threading
import time
from typing import List, Dict, Any, Optional
import psutil
from core import config

class ProcessManager:
    def __init__(self):
        self.sort_by = "cpu_percent"
        self.reverse = True
        self.filter_term = ""
        self.update_interval = 2
        self._stop_event = threading.Event()
        self._thread = None
        self.callback_queue = queue.Queue()
    def get_process_list(self) -> List[Dict[str, Any]]:
        process_list = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent",
                                         "status", "create_time", "username", "nice"]):
            try:
                pinfo = proc.info
                pinfo["cpu_percent"] = round(pinfo["cpu_percent"] or 0, 1)
                pinfo["memory_percent"] = round(pinfo["memory_percent"] or 0, 1)
                create_time = pinfo["create_time"]
                if create_time:
                    pinfo["create_time_str"] = time.strftime("%H:%M:%S", time.localtime(create_time))
                else:
                    pinfo["create_time_str"] = ""
                pinfo["nice"] = pinfo["nice"] if pinfo["nice"] is not None else 0
                process_list.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                pid = proc.pid if hasattr(proc, "pid") else "unknown"
                name = proc.name() if hasattr(proc, "name") else "unknown"
                logging.error(f"Failed to access process PID={pid} name={name}: {e}")
                continue
        if self.filter_term:
            term = self.filter_term.lower()
            process_list = [p for p in process_list if term in p["name"].lower()]
        process_list.sort(key=lambda x: x.get(self.sort_by, 0), reverse=self.reverse)
        return process_list
    def kill_process(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            gone, alive = psutil.wait_procs([proc], timeout=3)
            if alive:
                proc.kill()
            logging.info(f"Process PID={pid} terminated successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to terminate process PID={pid}: {e}")
            return False
    def set_nice(self, pid: int, nice_value: int) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.nice(nice_value)
            logging.info(f"Nice value of process PID={pid} set to {nice_value}.")
            return True
        except Exception as e:
            logging.error(f"Failed to set nice for process PID={pid}: {e}")
            return False
    def suspend_process(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.suspend()
            logging.info(f"Process PID={pid} suspended.")
            return True
        except Exception as e:
            logging.error(f"Failed to suspend process PID={pid}: {e}")
            return False
    def resume_process(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.resume()
            logging.info(f"Process PID={pid} resumed.")
            return True
        except Exception as e:
            logging.error(f"Failed to resume process PID={pid}: {e}")
            return False
    def start_monitoring(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            logging.debug("Process monitoring started.")
    def stop_monitoring(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
            logging.debug("Process monitoring stopped.")
    def _monitor_loop(self):
        while not self._stop_event.is_set():
            procs = self.get_process_list()
            self.callback_queue.put(procs)
            time.sleep(self.update_interval)
    def set_sort(self, key: str, reverse: bool = True):
        self.sort_by = key
        self.reverse = reverse
        logging.debug(f"Sort order changed: by={key}, reverse={reverse}")
    def set_filter(self, term: str):
        self.filter_term = term
        logging.debug(f"Filter set to: '{term}'")
    def set_update_interval(self, seconds: int):
        self.update_interval = max(1, seconds)
        logging.debug(f"Update interval set to {self.update_interval}s")
EOF

# -------------------- scheduler.py --------------------
cat > core/scheduler.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic task scheduler module (cron, task scheduler, launchd).
Version 1.0.0
"""
import logging
import subprocess
import os
from pathlib import Path
from core import config

class Scheduler:
    def __init__(self, so, log_dir, agent_script):
        self.so = so
        self.log_dir = log_dir
        self.agent_script = agent_script
    def create_schedule(self, config):
        if not config.get("enabled"):
            self.remove_schedule()
            return
        tasks = config.get("tasks", [])
        hour = config.get("hour", "03:00")
        freq = config.get("frequency", "daily")
        elevated = config.get("elevated", False)
        cmd = f"python3 {self.agent_script} --tasks {','.join(tasks)}"
        if elevated:
            cmd = "sudo " + cmd
        if self.so == "Linux":
            self._create_cron(cmd, freq, hour, config)
        elif self.so == "Windows":
            self._create_task_scheduler(cmd, freq, hour, config)
        elif self.so == "Darwin":
            self._create_launchd(cmd, freq, hour, config)
    def remove_schedule(self):
        if self.so == "Linux":
            subprocess.run("crontab -l | grep -v speedscan-agent | crontab -", shell=True)
        elif self.so == "Windows":
            subprocess.run("schtasks /delete /tn SpeedScanAgent /f", shell=True)
        elif self.so == "Darwin":
            subprocess.run("launchctl unload ~/Library/LaunchAgents/com.speedscan.agent.plist 2>/dev/null", shell=True)
            (Path.home() / "Library/LaunchAgents/com.speedscan.agent.plist").unlink(missing_ok=True)
    def _create_cron(self, cmd, freq, hour, config):
        hour_part, minute_part = hour.split(":")
        if freq == "hourly":
            cron_line = f"{minute_part} * * * * {cmd} >> {self.log_dir}/cron.log 2>&1"
        elif freq == "daily":
            cron_line = f"{minute_part} {hour_part} * * * {cmd} >> {self.log_dir}/cron.log 2>&1"
        elif freq == "weekly":
            dow = config.get("day_of_week", "monday").lower()[:3]
            cron_line = f"{minute_part} {hour_part} * * {dow} {cmd} >> {self.log_dir}/cron.log 2>&1"
        elif freq == "monthly":
            dom = config.get("day_of_month", 1)
            cron_line = f"{minute_part} {hour_part} {dom} * * {cmd} >> {self.log_dir}/cron.log 2>&1"
        else:
            return
        subprocess.run(f"(crontab -l 2>/dev/null; echo \"{cron_line}\") | crontab -", shell=True)
    def _create_task_scheduler(self, cmd, freq, hour, config):
        hour_part, minute_part = hour.split(":")
        if freq == "hourly":
            repetition = "/ri 60"
            sc_daily = "/sc daily"
        elif freq == "daily":
            repetition = ""
            sc_daily = f"/sc daily /st {hour}"
        elif freq == "weekly":
            dow = config.get("day_of_week", "monday").capitalize()
            repetition = ""
            sc_daily = f"/sc weekly /d {dow} /st {hour}"
        elif freq == "monthly":
            dom = config.get("day_of_month", 1)
            repetition = ""
            sc_daily = f"/sc monthly /d {dom} /st {hour}"
        else:
            return
        task_cmd = f"schtasks /create /tn SpeedScanAgent /tr \"{cmd}\" {sc_daily} {repetition} /f"
        subprocess.run(task_cmd, shell=True)
    def _create_launchd(self, cmd, freq, hour, config):
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.speedscan.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>{cmd}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{int(hour.split(":")[0])}</integer>
        <key>Minute</key>
        <integer>{int(hour.split(":")[1])}</integer>"""
        if freq == "weekly":
            dow = config.get("day_of_week", "monday").lower()
            dow_map = {"monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4, "friday": 5, "saturday": 6, "sunday": 0}
            plist_content += f"""
        <key>Weekday</key>
        <integer>{dow_map[dow]}</integer>"""
        elif freq == "monthly":
            dom = config.get("day_of_month", 1)
            plist_content += f"""
        <key>Day</key>
        <integer>{dom}</integer>"""
        plist_content += f"""
    </dict>
    <key>StandardOutPath</key>
    <string>{self.log_dir}/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>{self.log_dir}/launchd.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>"""
        plist_path = Path.home() / "Library/LaunchAgents/com.speedscan.agent.plist"
        plist_path.write_text(plist_content)
        subprocess.run(f"launchctl load {plist_path}", shell=True)
EOF

# -------------------- security_scanner.py --------------------
cat > core/security_scanner.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security scanning module: open ports, firewall status, security updates.
Version 1.0.0
"""
import logging
import subprocess
import re
from core import config

class SecurityScanner:
    def __init__(self, so):
        self.so = so
    def scan_open_ports(self):
        try:
            if self.so == "Linux":
                cmd = ["ss", "-tulpn"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    cmd = ["netstat", "-tulpn"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                lines = result.stdout.splitlines()
                ports = []
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        addr = parts[3] if "LISTEN" in line else None
                        if addr and ":" in addr:
                            ip, port = addr.rsplit(":", 1)
                            ports.append(f"{ip}:{port}")
                return ports
            elif self.so == "Windows":
                cmd = ["netstat", "-an"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                lines = result.stdout.splitlines()
                ports = []
                for line in lines:
                    if "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            addr = parts[1]
                            ports.append(addr)
                return ports
            elif self.so == "Darwin":
                cmd = ["lsof", "-i", "-P", "-n", "|", "grep", "LISTEN"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, shell=True)
                lines = result.stdout.splitlines()
                ports = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 9:
                        addr = parts[8]
                        ports.append(addr)
                return ports
        except Exception as e:
            logging.error(f"Error scanning ports: {e}")
            return [f"Error: {e}"]
        return []
    def check_firewall_status(self):
        try:
            if self.so == "Linux":
                ufw = subprocess.run(["sudo", "ufw", "status"], capture_output=True, text=True, timeout=3)
                if ufw.returncode == 0:
                    return ufw.stdout
                ipt = subprocess.run(["sudo", "iptables", "-L"], capture_output=True, text=True, timeout=3)
                if ipt.returncode == 0:
                    return ipt.stdout
                return "Firewall not detected or no permission."
            elif self.so == "Windows":
                cmd = ["netsh", "advfirewall", "show", "allprofiles"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                return result.stdout
            elif self.so == "Darwin":
                cmd = ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                return result.stdout
        except Exception as e:
            logging.error(f"Error checking firewall: {e}")
            return f"Error checking firewall: {e}"
        return "Unable to fetch firewall status."
    def check_security_updates(self):
        try:
            if self.so == "Linux":
                if subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
                    subprocess.run(["sudo", "apt", "update"], capture_output=True, timeout=10)
                    result = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True, timeout=10)
                    lines = result.stdout.splitlines()
                    updates = [line for line in lines if "security" in line.lower() or (line.strip() and not line.startswith("Listing"))]
                    return updates if updates else ["No security updates found."]
                elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
                    result = subprocess.run(["dnf", "updateinfo", "list", "security"], capture_output=True, text=True, timeout=10)
                    return result.stdout.splitlines()
                elif subprocess.run(["which", "yum"], capture_output=True).returncode == 0:
                    result = subprocess.run(["yum", "updateinfo", "list", "security"], capture_output=True, text=True, timeout=10)
                    return result.stdout.splitlines()
                else:
                    return ["Package manager not supported for security update check."]
            elif self.so == "Windows":
                cmd = ["powershell", "-Command", "Get-WUInstall -ListOnly -MicrosoftUpdate"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                return result.stdout.splitlines()
            elif self.so == "Darwin":
                cmd = ["softwareupdate", "-l"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                lines = result.stdout.splitlines()
                updates = [line for line in lines if "security" in line.lower() or "recommended" in line.lower()]
                return updates if updates else ["No security updates available."]
        except Exception as e:
            logging.error(f"Error checking security updates: {e}")
            return [f"Error checking security updates: {e}"]
        return ["Unable to check security updates."]
EOF

# -------------------- smart_monitor.py --------------------
cat > core/smart_monitor.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S.M.A.R.T. monitoring module for disks.
Version 1.0.0
"""
import logging
import subprocess
import re
from core import config

class SmartMonitor:
    def __init__(self):
        self.disk_status = {}
    def get_smart_info(self, disk="/dev/sda"):
        try:
            result = subprocess.run(
                ["sudo", "smartctl", "-H", disk],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout
        except Exception as e:
            logging.error(f"Error fetching SMART data for disk {disk}: {e}")
            return None
    def get_summary_text(self):
        try:
            out = subprocess.run(["lsblk", "-d", "-o", "NAME"], capture_output=True, text=True)
            disks = out.stdout.splitlines()[1:]
            summary = []
            for disk in disks:
                disk = disk.strip()
                if not disk:
                    continue
                smart = self.get_smart_info(f"/dev/{disk}")
                if smart:
                    match = re.search(r"SMART overall-health self-assessment test result: (\w+)", smart)
                    if match:
                        status = match.group(1)
                        summary.append(f"{disk}: {status}")
                    else:
                        summary.append(f"{disk}: Unknown")
                else:
                    summary.append(f"{disk}: Not supported")
            return "\n".join(summary) if summary else "No disk found"
        except Exception as e:
            logging.error(f"Error generating SMART summary: {e}")
            return "Error fetching S.M.A.R.T. information"
    def get_status_color(self):
        try:
            out = subprocess.run(["lsblk", "-d", "-o", "NAME"], capture_output=True, text=True)
            disks = out.stdout.splitlines()[1:]
            any_failed = False
            any_unknown = False
            for disk in disks:
                disk = disk.strip()
                if not disk:
                    continue
                smart = self.get_smart_info(f"/dev/{disk}")
                if smart:
                    if "FAILED" in smart:
                        any_failed = True
                    elif "PASSED" not in smart:
                        any_unknown = True
                else:
                    any_unknown = True
            if any_failed:
                return "red"
            if any_unknown:
                return "yellow"
            return "green"
        except Exception as e:
            logging.error(f"Error determining SMART status color: {e}")
            return "yellow"
EOF

# -------------------- speed_test.py --------------------
cat > core/speed_test.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internet speed test module.
Version 1.0.0
"""
import logging
import subprocess
import sys
import time
import threading
import os
try:
    import speedtest
except ImportError:
    logging.error("Installing speedtest-cli...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "speedtest-cli"])
    import speedtest
from core import config

class SpeedTester:
    def __init__(self, use_fallback=False):
        self.use_fallback = use_fallback
        self.result = {
            "ping": None,
            "download": None,
            "upload": None,
            "server": None,
            "timestamp": None,
            "error": None
        }
    def test_with_speedtest(self) -> bool:
        try:
            st = speedtest.Speedtest(secure=True)
            st.get_best_server()
            self.result["ping"] = round(st.results.ping, 1)
            self.result["server"] = f"{st.results.server['name']} ({st.results.server['country']})"
            download_bps = st.download()
            self.result["download"] = round(download_bps / 1_000_000, 2)
            upload_bps = st.upload()
            self.result["upload"] = round(upload_bps / 1_000_000, 2)
            self.result["timestamp"] = time.time()
            return True
        except Exception as e:
            logging.error(f"Error in test_with_speedtest: {e}")
            self.result["error"] = str(e)
            return False
    def test_fallback(self) -> bool:
        import requests
        import tempfile
        try:
            start = time.time()
            requests.get("https://www.google.com", timeout=5)
            ping = (time.time() - start) * 1000
            self.result["ping"] = round(ping, 1)
            url_download = "http://speedtest.tele2.net/10MB.zip"
            with tempfile.NamedTemporaryFile() as tmp:
                start = time.time()
                r = requests.get(url_download, stream=True, timeout=30)
                size = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        size += len(chunk)
                        tmp.write(chunk)
                elapsed = time.time() - start
                download_mbps = (size * 8) / elapsed / 1_000_000
                self.result["download"] = round(download_mbps, 2)
            data = os.urandom(5 * 1024 * 1024)
            start = time.time()
            requests.post("https://httpbin.org/post", data=data, timeout=30)
            elapsed = time.time() - start
            upload_mbps = (len(data) * 8) / elapsed / 1_000_000
            self.result["upload"] = round(upload_mbps, 2)
            self.result["server"] = "Fallback (public servers)"
            self.result["timestamp"] = time.time()
            return True
        except Exception as e:
            logging.error(f"Error in test_fallback: {e}")
            self.result["error"] = str(e)
            return False
    def run_test(self, callback=None):
        def _run():
            if self.use_fallback:
                success = self.test_fallback()
            else:
                success = self.test_with_speedtest()
                if not success:
                    self.use_fallback = True
                    success = self.test_fallback()
            if callback:
                callback(self.result)
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread
    def format_result(self, result=None) -> str:
        if result is None:
            result = self.result
        if result.get("error"):
            return f"❌ Error: {result['error']}"
        lines = []
        if result.get("ping") is not None:
            lines.append(f"📶 Ping: {result['ping']} ms")
        if result.get("download") is not None:
            lines.append(f"⬇️ Download: {result['download']} Mbps")
        if result.get("upload") is not None:
            lines.append(f"⬆️ Upload: {result['upload']} Mbps")
        if result.get("server"):
            lines.append(f"🖥️ Server: {result['server']}")
        if result.get("timestamp"):
            from datetime import datetime
            dt = datetime.fromtimestamp(result["timestamp"])
            lines.append(f"🕒 {dt.strftime('%d/%m/%Y %H:%M:%S')}")
        return "\n".join(lines)
EOF

# -------------------- temperature_monitor.py --------------------
cat > core/temperature_monitor.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temperature monitoring module for CPU, GPU, and disks.
Version 1.0.0
"""
import psutil
import subprocess

class TemperatureMonitor:
    def __init__(self):
        self.sensors = {}
    def get_cpu_temperatures(self):
        temps = {}
        try:
            thermal = psutil.sensors_temperatures()
            if "coretemp" in thermal:
                for entry in thermal["coretemp"]:
                    label = entry.label or f"Core {len(temps)}"
                    temps[f"CPU {label}"] = round(entry.current, 1)
            elif "k10temp" in thermal:
                for entry in thermal["k10temp"]:
                    temps["CPU Package"] = round(entry.current, 1)
            else:
                try:
                    with open("/sys/class/thermal/thermal_zone0/temp") as f:
                        temp = int(f.read().strip()) / 1000.0
                        temps["CPU"] = round(temp, 1)
                except:
                    pass
        except:
            pass
        return temps
    def get_gpu_temperatures(self):
        temps = {}
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                                 capture_output=True, text=True, timeout=2)
            if out.returncode == 0:
                lines = out.stdout.strip().split("\n")
                for i, line in enumerate(lines):
                    if line.strip():
                        temps[f"GPU {i}"] = round(float(line.strip()), 1)
        except:
            pass
        return temps
    def get_disk_temperatures(self):
        temps = {}
        try:
            out = subprocess.run(["lsblk", "-d", "-o", "NAME"], capture_output=True, text=True)
            disks = out.stdout.splitlines()[1:]
            for disk in disks:
                disk = disk.strip()
                if disk:
                    try:
                        smart = subprocess.run(["sudo", "smartctl", "-A", f"/dev/{disk}"],
                                               capture_output=True, text=True, timeout=2)
                        for line in smart.stdout.splitlines():
                            if "Temperature_Celsius" in line:
                                parts = line.split()
                                if len(parts) >= 10:
                                    temp = parts[9]
                                    temps[f"Disk {disk}"] = round(float(temp), 1)
                                break
                    except:
                        pass
        except:
            pass
        return temps
    def get_all_temperatures(self):
        temps = {}
        temps.update(self.get_cpu_temperatures())
        temps.update(self.get_gpu_temperatures())
        temps.update(self.get_disk_temperatures())
        return temps
EOF

# -------------------- trash_manager.py --------------------
cat > core/trash_manager.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trash manager for SpeedScan - manages deleted files with metadata.
Version 1.0.0
"""
import shutil
import os
import time
import json
from pathlib import Path
import logging
from core import config

def _get_trash_dir():
    return Path.home() / ".speedscan_trash"
def _get_metadata_path():
    return _get_trash_dir() / "metadata.json"
TRASH_DIR = _get_trash_dir()
TRASH_METADATA = _get_metadata_path()

class TrashManager:
    def __init__(self):
        TRASH_DIR.mkdir(parents=True, exist_ok=True)
        if not TRASH_METADATA.exists():
            self._save_metadata({})
    def _load_metadata(self):
        with open(TRASH_METADATA, "r") as f:
            return json.load(f)
    def _save_metadata(self, metadata):
        with open(TRASH_METADATA, "w") as f:
            json.dump(metadata, f, indent=2)
    def move_to_trash(self, path, original_path):
        if not os.path.exists(path):
            return False
        trash_name = f"{int(time.time())}_{os.path.basename(path)}"
        trash_path = TRASH_DIR / trash_name
        shutil.move(path, trash_path)
        metadata = self._load_metadata()
        metadata[trash_name] = {
            "original": str(original_path),
            "time": time.time()
        }
        self._save_metadata(metadata)
        return True
    def restore(self, trash_name):
        metadata = self._load_metadata()
        if trash_name not in metadata:
            return False
        info = metadata[trash_name]
        trash_path = TRASH_DIR / trash_name
        original = Path(info["original"])
        if not trash_path.exists():
            return False
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(trash_path), str(original))
        del metadata[trash_name]
        self._save_metadata(metadata)
        return True
    def empty_trash(self):
        shutil.rmtree(TRASH_DIR)
        TRASH_DIR.mkdir()
        self._save_metadata({})
    def list_trash(self):
        metadata = self._load_metadata()
        items = []
        for name, info in metadata.items():
            items.append({
                "name": name,
                "original": info["original"],
                "time": info["time"]
            })
        return items
    def get_trash_size(self):
        total = 0
        for root, dirs, files in os.walk(TRASH_DIR):
            for f in files:
                if f == "metadata.json":
                    continue
                fp = Path(root) / f
                total += fp.stat().st_size
        return total
EOF

# -------------------- windows_cleaner.py --------------------
cat > core/windows_cleaner.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows cleaner module (bloatware, telemetry and AI components)
Exclusive for Windows systems.
"""
import subprocess
import logging
import os
from typing import List, Dict, Callable, Optional
from pathlib import Path
from core.i18n import _

class WindowsCleaner:
    def __init__(self):
        self.bloatware_list = self._get_bloatware_list()
        self.ai_components = self._get_ai_components()
        self.telemetry_commands = self._get_telemetry_commands()
        self.cleanup_commands = self._get_cleanup_commands()
    def _get_bloatware_list(self) -> List[Dict[str, str]]:
        return [
            {"name": _("Xbox App"), "package": "Microsoft.XboxApp", "description": _("Xbox application")},
            {"name": _("Xbox Game Bar"), "package": "Microsoft.XboxGamingOverlay", "description": _("Xbox game bar")},
            {"name": _("Xbox Identity Provider"), "package": "Microsoft.XboxIdentityProvider", "description": _("Xbox identity provider")},
            {"name": _("Xbox Speech to Text Overlay"), "package": "Microsoft.XboxSpeechToTextOverlay", "description": _("Xbox speech overlay")},
            {"name": _("Candy Crush"), "package": "king.com.CandyCrushSaga", "description": _("Candy Crush game")},
            {"name": _("Skype"), "package": "Microsoft.SkypeApp", "description": _("Skype")},
            {"name": _("OneDrive"), "package": "Microsoft.OneDrive", "description": _("OneDrive")},
            {"name": _("Bing Weather"), "package": "Microsoft.BingWeather", "description": _("Bing Weather")},
            {"name": _("Bing News"), "package": "Microsoft.BingNews", "description": _("Bing News")},
            {"name": _("Bing Sports"), "package": "Microsoft.BingSports", "description": _("Bing Sports")},
            {"name": _("Bing Finance"), "package": "Microsoft.BingFinance", "description": _("Bing Finance")},
            {"name": _("3D Builder"), "package": "Microsoft.3DBuilder", "description": _("3D Builder")},
            {"name": _("People"), "package": "Microsoft.People", "description": _("People")},
            {"name": _("Zune Music"), "package": "Microsoft.ZuneMusic", "description": _("Zune Music")},
            {"name": _("Zune Video"), "package": "Microsoft.ZuneVideo", "description": _("Zune Video")},
            {"name": _("Mixed Reality Portal"), "package": "Microsoft.MixedReality.Portal", "description": _("Mixed Reality Portal")},
            {"name": _("Office Hub"), "package": "Microsoft.MicrosoftOfficeHub", "description": _("Office Hub")},
            {"name": _("Solitaire Collection"), "package": "Microsoft.MicrosoftSolitaireCollection", "description": _("Solitaire Collection")},
            {"name": _("Sticky Notes"), "package": "Microsoft.MicrosoftStickyNotes", "description": _("Sticky Notes")},
            {"name": _("Windows Camera"), "package": "Microsoft.WindowsCamera", "description": _("Windows Camera")},
            {"name": _("Windows Communications Apps"), "package": "Microsoft.WindowsCommunicationsApps", "description": _("Communications apps")},
            {"name": _("Windows Feedback Hub"), "package": "Microsoft.WindowsFeedbackHub", "description": _("Feedback Hub")},
            {"name": _("Windows Maps"), "package": "Microsoft.WindowsMaps", "description": _("Windows Maps")},
            {"name": _("Windows Sound Recorder"), "package": "Microsoft.WindowsSoundRecorder", "description": _("Sound Recorder")},
            {"name": _("Your Phone"), "package": "Microsoft.YourPhone", "description": _("Your Phone")},
            {"name": _("Get Help"), "package": "Microsoft.GetHelp", "description": _("Get Help")},
            {"name": _("Messaging"), "package": "Microsoft.Messaging", "description": _("Messaging")},
            {"name": _("Office OneNote"), "package": "Microsoft.Office.OneNote", "description": _("OneNote")},
            {"name": _("Outlook for Windows"), "package": "Microsoft.OutlookForWindows", "description": _("Outlook")},
            {"name": _("Paint 3D"), "package": "Microsoft.Paint3D", "description": _("Paint 3D")},
            {"name": _("Print 3D"), "package": "Microsoft.Print3D", "description": _("Print 3D")},
            {"name": _("Snip & Sketch"), "package": "Microsoft.ScreenSketch", "description": _("Snip & Sketch")},
            {"name": _("Teams"), "package": "Microsoft.Teams", "description": _("Microsoft Teams")},
            {"name": _("Todos"), "package": "Microsoft.Todos", "description": _("Microsoft To Do")},
            {"name": _("Wallet"), "package": "Microsoft.Wallet", "description": _("Wallet")},
            {"name": _("Windows Alarms"), "package": "Microsoft.WindowsAlarms", "description": _("Alarms")},
            {"name": _("Windows Calculator"), "package": "Microsoft.WindowsCalculator", "description": _("Calculator")},
            {"name": _("Windows Clock"), "package": "Microsoft.WindowsClock", "description": _("Clock")},
        ]
    def _get_ai_components(self) -> List[Dict[str, str]]:
        return [
            {"name": _("Copilot"), "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f'},
            {"name": _("Windows Recall"), "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI" /v DisableAIDataAnalysis /t REG_DWORD /d 1 /f'},
            {"name": _("Cortana"), "cmd": "Get-AppxPackage *cortana* | Remove-AppxPackage"},
            {"name": _("Web Search in Start"), "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f'},
            {"name": _("News & Interests"), "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Feeds" /v ShellFeedsTaskbarEnabled /t REG_DWORD /d 0 /f'},
            {"name": _("Widgets"), "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarDa /t REG_DWORD /d 0 /f'},
        ]
    def _get_telemetry_commands(self) -> List[str]:
        return [
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
            'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy" /v TailoredExperiencesWithDiagnosticDataEnabled /t REG_DWORD /d 0 /f',
            'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy" /v LetAppsRunInBackground /t REG_DWORD /d 2 /f',
            'schtasks /change /tn "Microsoft\\Windows\\Application Experience\\Microsoft Compatibility Appraiser" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Application Experience\\ProgramDataUpdater" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Customer Experience Improvement Program\\Consolidator" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Customer Experience Improvement Program\\UsbCeip" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\DiskDiagnostic\\Microsoft-Windows-DiskDiagnosticDataCollector" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Feedback\\Siuf\\DmClient" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Feedback\\Siuf\\DmClientOnScenarioDownload" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Location\\Notifications" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\PI\\Sqm-Tasks" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Power Efficiency Diagnostics\\AnalyzeSystem" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Windows Error Reporting\\QueueReporting" /disable',
        ]
    def _get_cleanup_commands(self) -> List[str]:
        return [
            "del /q /f /s %temp%\\*",
            "del /q /f /s C:\\Windows\\Temp\\*",
            "del /q /f /s C:\\Windows\\Prefetch\\*",
            "del /q /f /s C:\\Windows\\SoftwareDistribution\\Download\\*",
            "cleanmgr /sagerun:1 | exit",
        ]
    def get_installed_bloatware(self) -> List[Dict[str, str]]:
        installed = []
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-AppxPackage | Select-Object -ExpandProperty PackageFullName"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore"
            )
            if result.returncode != 0:
                logging.error(_("Error executing PowerShell: {stderr}").format(stderr=result.stderr))
                return installed
            installed_packages = result.stdout.lower()
            for app in self.bloatware_list:
                if app["package"].lower() in installed_packages:
                    installed.append(app)
        except Exception as e:
            logging.error(_("Exception while verifying bloatware: {error}").format(error=e))
        return installed
    def remove_package(self, package_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f'powershell -Command "Get-AppxPackage *{package_name}* | Remove-AppxPackage -ErrorAction SilentlyContinue"'
        return self._run_command(cmd, log_callback)
    def remove_multiple_packages(self, packages: List[str], log_callback: Optional[Callable[[str], None]] = None) -> bool:
        success = True
        for pkg in packages:
            if not self.remove_package(pkg, log_callback):
                success = False
        return success
    def disable_telemetry(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        success = True
        for cmd in self.telemetry_commands:
            if not self._run_command(cmd, log_callback):
                success = False
        return success
    def disable_ai_component(self, component_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        for comp in self.ai_components:
            if comp["name"].lower() == component_name.lower():
                return self._run_command(comp["cmd"], log_callback)
        return False
    def disable_all_ai(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        success = True
        for comp in self.ai_components:
            if not self._run_command(comp["cmd"], log_callback):
                success = False
        return success
    def run_cleanup(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        success = True
        for cmd in self.cleanup_commands:
            if not self._run_command(cmd, log_callback):
                success = False
        return success
    def _run_command(self, cmd: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            stdout, stderr = proc.communicate(timeout=120)
            if log_callback:
                if stdout:
                    log_callback(stdout)
                if stderr:
                    log_callback(_("ERROR: {stderr}").format(stderr=stderr))
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            if log_callback:
                log_callback(_("Command exceeded time limit and was killed."))
            return False
        except Exception as e:
            if log_callback:
                log_callback(_("Exception: {error}").format(error=e))
            return False
EOF

# -------------------- lan_cache.py --------------------
cat > core/lan_cache.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LANCache integration module (game caching server).
Version 1.0.0
"""
import logging
import subprocess
import os
from pathlib import Path
from core import config

class LANCacheManager:
    def __init__(self, so):
        self.so = so
        self.compose_url = "https://github.com/lancachenet/docker-compose/raw/master/docker-compose.yml"
        self.env_url = "https://github.com/lancachenet/docker-compose/raw/master/lancache.env"
    def is_docker_installed(self) -> bool:
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception as e:
            logging.error(f"Error checking Docker installation: {e}")
            return False
    def install_docker(self) -> list:
        if self.so == "Linux":
            if os.path.exists("/etc/debian_version"):
                return [
                    "sudo apt update",
                    "sudo apt install -y docker.io",
                    "sudo systemctl enable --now docker",
                    "sudo usermod -aG docker $USER"
                ]
            elif os.path.exists("/etc/redhat-release"):
                return [
                    "sudo yum install -y yum-utils",
                    "sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo",
                    "sudo yum install -y docker-ce docker-ce-cli containerd.io",
                    "sudo systemctl enable --now docker",
                    "sudo usermod -aG docker $USER"
                ]
            else:
                return ["echo 'Distribution not supported for automatic Docker installation'"]
        elif self.so == "Darwin":
            return [
                'echo "For macOS, install Docker Desktop manually: https://docs.docker.com/desktop/install/mac-install/"'
            ]
        elif self.so == "Windows":
            return [
                'echo "For Windows, install Docker Desktop manually: https://docs.docker.com/desktop/install/windows-install/"'
            ]
        return []
    def get_install_commands(self) -> list:
        home = Path.home()
        lancache_dir = home / "lancache"
        compose_file = lancache_dir / "docker-compose.yml"
        env_file = lancache_dir / "lancache.env"
        commands = []
        commands.append(f"mkdir -p {lancache_dir}")
        commands.append(f"wget -O {compose_file} {self.compose_url}")
        commands.append(f"wget -O {env_file} {self.env_url}")
        commands.append(f"cd {lancache_dir} && sudo docker-compose up -d")
        return commands
    def get_status(self) -> str:
        try:
            result = subprocess.run(["docker", "ps", "--filter", "name=lancache", "--format", "table"],
                                    capture_output=True, text=True)
            if "lancache" in result.stdout:
                return "✅ LANCache is running"
            else:
                return "❌ LANCache is not running"
        except FileNotFoundError:
            return "❌ Docker is not installed"
        except Exception as e:
            logging.error(f"Error checking LANCache status: {e}")
            return "❌ Error checking status"
    def stop(self) -> list:
        home = Path.home()
        lancache_dir = home / "lancache"
        return [f"cd {lancache_dir} && sudo docker-compose down"]
    def configure_dns(self, dns_ip=None) -> str or None:
        if dns_ip is None:
            try:
                result = subprocess.run(["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", "lancache-dns"],
                                        capture_output=True, text=True)
                dns_ip = result.stdout.strip()
            except Exception as e:
                logging.error(f"Error obtaining DNS container IP: {e}")
                dns_ip = "127.0.0.1"
        if self.so == "Linux":
            return f"echo 'nameserver {dns_ip}' | sudo tee /etc/resolv.conf"
        elif self.so == "Windows":
            return f"netsh interface ip set dns name='Ethernet' static {dns_ip}"
        elif self.so == "Darwin":
            return f"networksetup -setdnsservers Wi-Fi {dns_ip}"
        return None
EOF

touch core/__init__.py

# ============================================================
# 4. Gerar traduções (método manual)
# ============================================================
echo "🌐 Gerando arquivos de tradução manualmente..."

mkdir -p locale/pt_BR/LC_MESSAGES
mkdir -p locale/en_US/LC_MESSAGES
mkdir -p locale/es_ES/LC_MESSAGES

cat > locale/pt_BR/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: pt_BR\n"

msgid "Dashboard"
msgstr "Painel"
EOF

cat > locale/en_US/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: en_US\n"

msgid "Dashboard"
msgstr "Dashboard"
EOF

cat > locale/es_ES/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: es_ES\n"

msgid "Dashboard"
msgstr "Tablero"
EOF

msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo
msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo

sudo chown -R $USER:$USER locale 2>/dev/null || true
echo "✅ Traduções geradas."

# ============================================================
# 5. Criar ambiente virtual e instalar dependências
# ============================================================
echo "📦 Configurando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip > /dev/null
pip install customtkinter psutil matplotlib requests speedtest-cli pillow > /dev/null

# Verificar Tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "🖥️ Tkinter não encontrado. Tentando instalar $PYTHON_TK_PKG..."
    if [ -n "$PKG_MANAGER" ]; then
        $INSTALL_CMD $PYTHON_TK_PKG
    else
        echo "⚠️  Instale o pacote $PYTHON_TK_PKG manualmente."
    fi
fi

# ============================================================
# 6. Finalizar
# ============================================================
echo ""
echo "🎉 INSTALAÇÃO COMPLETA CONCLUÍDA!"
echo ""
echo "Agora execute os comandos:"
echo "   cd $(pwd)"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Teste:"
echo "- Clique em um card (ex: 'Cloudflare DNS') – o botão 'Details ▼' aparecerá imediatamente."
echo "- Clique no botão para abrir o console (seta vira ▲), clique novamente para fechar (▼)."
echo "- Ao clicar em outro card, o console anterior será fechado automaticamente."
echo "- Mude o idioma nas Configurações e veja a palavra 'Dashboard' mudar (exemplo)."
