#!/bin/bash
# Script universal de instalação do SpeedScan
# Funciona em Debian/Ubuntu, Fedora, Arch, etc.

set -e

echo "🚀 Iniciando instalação do SpeedScan (versão universal)..."

# ============================================================
# 1. Detectar gerenciador de pacotes e preparar instalação
# ============================================================
PKG_MANAGER=""
INSTALL_CMD=""
PYTHON_TK_PKG=""

if command -v apt >/dev/null 2>&1; then
    PKG_MANAGER="apt"
    INSTALL_CMD="sudo apt update && sudo apt install -y"
    PYTHON_TK_PKG="python3-tk"
elif command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="sudo dnf install -y"
    PYTHON_TK_PKG="python3-tkinter"
elif command -v yum >/dev/null 2>&1; then
    PKG_MANAGER="yum"
    INSTALL_CMD="sudo yum install -y"
    PYTHON_TK_PKG="python3-tkinter"
elif command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
    INSTALL_CMD="sudo pacman -S --noconfirm"
    PYTHON_TK_PKG="tk"
else
    echo "⚠️  Não foi possível detectar o gerenciador de pacotes."
    echo "Você precisará instalar manualmente: gettext e $PYTHON_TK_PKG"
    read -p "Pressione Enter para continuar mesmo assim, ou Ctrl+C para abortar."
fi

# Função para instalar pacotes se necessário
install_pkg() {
    if [ -n "$PKG_MANAGER" ]; then
        echo "📦 Instalando $1..."
        $INSTALL_CMD $1
    else
        echo "⚠️  Por favor, instale $1 manualmente."
    fi
}

# Verificar e instalar gettext (para msgfmt)
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

        # Mostra o botão de detalhes no canto direito (aparece imediatamente, mas é a única forma)
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

# ============================================================
# 4. Gerar traduções (método manual, sem dependência de msginit)
# ============================================================
echo "🌐 Gerando arquivos de tradução manualmente..."

# Criar estrutura de diretórios
mkdir -p locale/pt_BR/LC_MESSAGES
mkdir -p locale/en_US/LC_MESSAGES
mkdir -p locale/es_ES/LC_MESSAGES

# Criar arquivo .po para português
cat > locale/pt_BR/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: pt_BR\n"

msgid "Dashboard"
msgstr "Painel"
EOF

# Criar arquivo .po para inglês
cat > locale/en_US/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: en_US\n"

msgid "Dashboard"
msgstr "Dashboard"
EOF

# Criar arquivo .po para espanhol
cat > locale/es_ES/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: es_ES\n"

msgid "Dashboard"
msgstr "Tablero"
EOF

# Compilar os arquivos .mo
msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo
msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo

sudo chown -R $USER:$USER locale 2>/dev/null || true
echo "✅ Traduções geradas com sucesso."

# ============================================================
# 5. Criar ambiente virtual e instalar dependências
# ============================================================
echo "📦 Configurando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip > /dev/null
pip install customtkinter psutil matplotlib requests speedtest-cli pillow > /dev/null

# Verificar Tkinter (pode ser necessário instalar no sistema)
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
echo "🎉 INSTALAÇÃO CONCLUÍDA!"
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
