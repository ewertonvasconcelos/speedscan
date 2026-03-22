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
from core.dashboard import Dashboard, get_usage_color, get_temp_color, get_temp_icon, get_battery_color, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_COLD
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

# Inline translations dictionary (fallback when .mo files not available)
INLINE_TRANSLATIONS = {
    "pt_BR": {
        # Tab names
        "Dashboard": "Painel",
        "Settings": "Configurações",
        "AI Agent": "Agente IA",
        "System Security": "Segurança do Sistema",
        "Optimization": "Otimização",
        "Network": "Rede",
        "Hardware": "Hardware",
        "Processes": "Processos",
        "History": "Histórico",
        "About": "Sobre",
        
        # Common buttons and labels
        "Run": "Executar",
        "Start": "Iniciar",
        "Stop": "Parar",
        "Details ▼": "Detalhes ▼",
        "Details ▲": "Detalhes ▲",
        "Hide Details ▲": "Ocultar Detalhes ▲",
        "Username:": "Usuário:",
        "Your name": "Seu nome",
        "Language:": "Idioma:",
        "UI Scale:": "Escala da UI:",
        "Theme:": "Tema:",
        
        # Network cards
        "🛡️ Open Ports": "🛡️ Portas Abertas",
        "🛡️ Firewall": "🛡️ Firewall",
        "📦 Security Updates": "📦 Atualizações de Segurança",
        
        # Messages
        "Executing:": "Executando:",
        "Error executing command": "Erro ao executar comando",
        "Unknown command": "Comando desconhecido",
        "Not enough data to display.": "Dados insuficientes para exibir.",
        "Time (hours from now)": "Tempo (horas atrás)",
        
        # AI
        "AI suggestions:": "Sugestões IA:",
        
        # Dashboard
        "Available widgets:": "Widgets disponíveis:",
        
        # Settings
        "Expert Mode": "Modo Experto",
        "Basic Mode": "Modo Básico",
        "Light": "Claro",
        "Dark": "Escuro",
        "System": "Sistema",
        "Auto": "Auto",
        
        # About
        "SpeedScan": "SpeedScan",
        "Version:": "Versão:",
        "About SpeedScan": "Sobre o SpeedScan",
        "System Information": "Informações do Sistema",
        
        # Optimization
        "Cache Cleaner": "Limpeza de Cache",
        "Swap Reset": "Resetar Swap",
        "Filesystem Check": "Verificar Sistema de Arquivos",
        "Turbo Mode": "Modo Turbo",
        
        # History
        "CPU %": "CPU %",
        "RAM %": "RAM %",
        "Disk %": "Disco %",
        
        # Errors
        "Error:": "Erro:",
        "Warning:": "Aviso:",
        "Success:": "Sucesso:",
    },
    "es_ES": {
        # Tab names
        "Dashboard": "Panel",
        "Settings": "Configuración",
        "AI Agent": "Agente IA",
        "System Security": "Seguridad del Sistema",
        "Optimization": "Optimización",
        "Network": "Red",
        "Hardware": "Hardware",
        "Processes": "Procesos",
        "History": "Historial",
        "About": "Acerca de",
        
        # Common buttons and labels
        "Run": "Ejecutar",
        "Start": "Iniciar",
        "Stop": "Detener",
        "Details ▼": "Detalles ▼",
        "Details ▲": "Detalles ▲",
        "Hide Details ▲": "Ocultar Detalles ▲",
        "Username:": "Usuario:",
        "Your name": "Tu nombre",
        "Language:": "Idioma:",
        "UI Scale:": "Escala UI:",
        "Theme:": "Tema:",
        
        # Network cards
        "🛡️ Open Ports": "🛡️ Puertos Abiertos",
        "🛡️ Firewall": "🛡️ Firewall",
        "📦 Security Updates": "📦 Actualizaciones de Seguridad",
        
        # Messages
        "Executing:": "Ejecutando:",
        "Error executing command": "Error al ejecutar comando",
        "Unknown command": "Comando desconocido",
        "Not enough data to display.": "Datos insuficientes para mostrar.",
        "Time (hours from now)": "Tiempo (horas atrás)",
        
        # AI
        "AI suggestions:": "Sugerencias IA:",
        
        # Dashboard
        "Available widgets:": "Widgets disponibles:",
        
        # Settings
        "Expert Mode": "Modo Experto",
        "Basic Mode": "Modo Básico",
        "Light": "Claro",
        "Dark": "Oscuro",
        "System": "Sistema",
        "Auto": "Auto",
        
        # About
        "SpeedScan": "SpeedScan",
        "Version:": "Versión:",
        "About SpeedScan": "Acerca de SpeedScan",
        "System Information": "Información del Sistema",
    },
    "en_US": {
        # English is the default
        "About": "About",
    }
}

def get_translation_with_fallback(language):
    """Get translation function with inline dictionary fallback."""
    # Try gettext first
    try:
        t = get_translation(language)
        # Test if it actually translates something
        test = t("Dashboard")
        if test != "Dashboard":  # gettext is working
            return t
    except:
        pass
    
    # Fallback to inline dictionary
    translations = INLINE_TRANSLATIONS.get(language, {})
    
    def translate(s):
        return translations.get(s, s)
    
    return translate

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
        self._ = get_translation_with_fallback(self.config_data.get("language", "pt_BR"))
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
        self._btn_shown = False

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
        logging.info(f"Loading theme: {theme_key}")
        theme_map = {"Still": "grey", "Tecno": "dark", "Snow": "light"}
        internal_key = theme_map.get(theme_key, theme_key)
        t = config.THEMES.get(internal_key, config.THEMES["default"])
        logging.info(f"Using internal theme key: {internal_key}, colors: {t}")
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
        scale = self.config_data.get("ui_scale", "125")
        if scale == "auto" or scale == "Auto":
            ctk.set_widget_scaling(1.25)  # Default to 125% instead of 100%
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
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.side_bg,
                            border_width=2, border_color=self.acc_color)
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
        # Close all detail panels when switching tabs
        for tag in list(self.logs.keys()):
            log = self.logs.get(tag)
            btn = self.detail_buttons.get(tag)
            if log and btn:
                log.pack_forget()
                btn.pack_forget()
                btn.configure(text=self._("Details ▼"))
            self.consoles_visible[tag] = False
        
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
        # Destroy existing frame before creating new one to avoid duplicates
        if target in self.frames:
            old_frame = self.frames[target]
            old_frame.destroy()
        
        # Use regular frame for tabs that don't need scrolling
        # to avoid scrollbar appearing when not needed
        no_scroll_tabs = ["about", "dashboard"]
        if target in no_scroll_tabs:
            frame = ctk.CTkFrame(self.container, fg_color="transparent")
        else:
            frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        getattr(self, f"_fill_{target}")(frame)
        self.frames[target] = frame
        return frame

    # ------------------------------------------------------------------------
    # Tab content filling methods
    # ------------------------------------------------------------------------
    def _fill_dashboard(self, parent):
        self.dashboard = Dashboard(parent, self, fg_color="transparent")
        self.dashboard.pack(fill="both", expand=True)

    def _fill_optimization(self, parent):
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

        self.process_text = ctk.CTkTextbox(parent, font=("Courier", 11), wrap="none")
        self.process_text.pack(fill="both", expand=True, padx=10, pady=10)
        # Configurar para só mostrar scrollbar quando necessário
        self.process_text.configure(scrollbar_button_color=self.acc_color, scrollbar_button_hover_color=self.light_bg)

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

    def _update_ai_suggestions(self):
        """Atualiza sugestões de IA quando a aba Agent é exibida."""
        if hasattr(self, 'ai_proactive'):
            try:
                suggestions = self.ai_proactive.analyze()
                print(f"AI suggestions: {len(suggestions)} suggestions found")
                
                # MOSTRAR AS SUGESTÕES NA UI
                if hasattr(self, 'chat_frame'):
                    summary = self.ai_proactive.get_summary()
                    self.chat_frame._add_message("system", "💡 " + summary.replace("\n", "\n💡 "))
            except Exception as e:
                print(f"Error updating AI suggestions: {e}")

    def _fill_security(self, parent):
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
        self.chat_frame = ChatFrame(parent, self, fg_color="transparent")
        self.chat_frame.pack(fill="both", expand=True)

    def _fill_settings(self, parent):
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
        ctk.CTkOptionMenu(f_lang, values=lang_values, variable=self.lang_var, width=200,
                          fg_color=self.bg_color, button_color=self.acc_color, button_hover_color=self.light_bg,
                          border_width=1, border_color=self.acc_color).pack(anchor="w", pady=2)

        f_scale = ctk.CTkFrame(parent, fg_color="transparent")
        f_scale.pack(fill="x", pady=5)
        ctk.CTkLabel(f_scale, text=self._("UI Scale:"), font=("Inter", 12)).pack(anchor="w")
        scale_values = list(config.SCALES.values())
        self.scale_var = ctk.StringVar(value=config.SCALES.get(self.config_data.get("ui_scale","auto"), "Auto"))
        ctk.CTkOptionMenu(f_scale, values=scale_values, variable=self.scale_var, width=200,
                          fg_color=self.bg_color, button_color=self.acc_color, button_hover_color=self.light_bg).pack(anchor="w", pady=2)

        f_theme = ctk.CTkFrame(parent, fg_color="transparent")
        f_theme.pack(fill="x", pady=5)
        ctk.CTkLabel(f_theme, text=self._("Theme:"), font=("Inter", 12)).pack(anchor="w")
        theme_names = ["Still", "Tecno", "Snow"]
        self.theme_var = ctk.StringVar(value=theme_names[0])
        current_theme = self.config_data.get("theme","default")
        theme_display_map = {"grey": "Still", "dark": "Tecno", "light": "Snow"}
        display = theme_display_map.get(current_theme, "Still")
        self.theme_var.set(display)
        ctk.CTkOptionMenu(f_theme, values=theme_names, variable=self.theme_var, width=200,
                          fg_color=self.bg_color, button_color=self.acc_color, button_hover_color=self.light_bg,
                          border_width=1, border_color=self.acc_color).pack(anchor="w", pady=2)

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
        ctk.CTkLabel(f_sched, text=self._("Automation:"), font=("Inter", 14, "bold"), text_color=self.acc_color).pack(anchor="w", pady=(0,5))
        
        self.auto_cache = ctk.BooleanVar(value=self.config_data.get("automation",{}).get("auto_cache", False))
        ctk.CTkCheckBox(f_sched, text=self._("Auto cache cleanup"), variable=self.auto_cache,
                        onvalue=True, offvalue=False).pack(anchor="w")
        
        self.auto_swap = ctk.BooleanVar(value=self.config_data.get("automation",{}).get("auto_swap", False))
        ctk.CTkCheckBox(f_sched, text=self._("Auto swap reset"), variable=self.auto_swap,
                        onvalue=True, offvalue=False).pack(anchor="w")
        
        self.auto_trim = ctk.BooleanVar(value=self.config_data.get("automation",{}).get("auto_trim", False))
        ctk.CTkCheckBox(f_sched, text=self._("Auto SSD trim"), variable=self.auto_trim,
                        onvalue=True, offvalue=False).pack(anchor="w")
        
        interval_frame = ctk.CTkFrame(f_sched, fg_color="transparent")
        interval_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(interval_frame, text=self._("Interval (hours):"), font=("Inter", 12)).pack(side="left")
        self.auto_interval = ctk.IntVar(value=self.config_data.get("automation",{}).get("interval", 24))
        interval_entry = ctk.CTkEntry(interval_frame, textvariable=self.auto_interval, width=80)
        interval_entry.pack(side="left", padx=5)
        
        self.sched_enabled = ctk.BooleanVar(value=self.config_data.get("schedule",{}).get("enabled", False))
        ctk.CTkCheckBox(f_sched, text=self._("Enable automation"), variable=self.sched_enabled,
                        onvalue=True, offvalue=False).pack(anchor="w", pady=(10,0))

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
            
            # Save automation settings
            if "automation" not in self.config_data:
                self.config_data["automation"] = {}
            self.config_data["automation"]["auto_cache"] = self.auto_cache.get()
            self.config_data["automation"]["auto_swap"] = self.auto_swap.get()
            self.config_data["automation"]["auto_trim"] = self.auto_trim.get()
            self.config_data["automation"]["interval"] = self.auto_interval.get()
            
            logging.info(f"Saving config with theme: {self.config_data['theme']}")
            self._save_config()
            self.show_toast(self._("Settings saved! Restarting..."), duration=2000)
            self.after(2000, self._restart_app)
        except Exception as e:
            logging.error(f"Error applying settings: {e}")

    def _restart_app(self):
        # Use os.execv to replace the current process with a new one
        # This is more reliable than subprocess for restarting
        python = sys.executable
        script = os.path.join(os.getcwd(), "run_speedscan.sh")
        if os.path.exists(script):
            os.execv(script, [script] + sys.argv[1:])
        else:
            # Fallback: try running directly
            main_py = os.path.join(os.getcwd(), "core", "main.py")
            if os.path.exists(main_py):
                os.execv(python, [python, main_py] + sys.argv[1:])
            else:
                # Last resort: use subprocess
                subprocess.Popen([python, "-m", "core.main"])
                self.quit()

    def _fill_about(self, parent):
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
    def _show_detail_button(self, tag):
        # Usa a tag do console (net, opt, drv, sec) para mostrar o botão correto
        btn = self.detail_buttons.get(tag)
        if btn and not btn.winfo_ismapped():
            btn.pack(side="right", anchor="e", padx=10, pady=5)

    def run_card_action(self, cmd, tag, is_dns):
        # tag aqui é a tag do console (net, opt, drv, sec), não do comando
        print(f"DEBUG run_card_action: cmd={cmd}, tag={tag}, is_dns={is_dns}")
        
        # Garantir que consoles_visible tem a chave
        if tag not in self.consoles_visible:
            self.consoles_visible[tag] = False
        
        log = self.logs.get(tag)
        print(f"DEBUG run_card_action: log={log}, logs keys={list(self.logs.keys())}")
        if not log:
            print(f"ERRO: log não encontrado para tag={tag}")
            # Criar log se não existir (para qualquer tag)
            if tag in ["opt", "net", "drv", "sec"]:
                print(f"DEBUG: Criando log para {tag}...")
                # Obtém o frame correspondente
                frame_key = {
                    "opt": "optimization",
                    "net": "network",
                    "drv": "hardware",
                    "sec": "security"
                }.get(tag, tag)
                
                if frame_key in self.frames:
                    parent = self.frames[frame_key]
                    from core import ui
                    btn, new_log = ui.add_console(parent, tag, self.acc_color, self.toggle_console)
                    self.detail_buttons[tag] = btn
                    self.logs[tag] = new_log
                    log = new_log
                    print(f"DEBUG: Log criado: {log}")
                else:
                    print(f"ERRO: Frame {frame_key} não encontrado")
                    return
            else:
                return
        log.delete("1.0", "end")
        log.insert("end", f"Executando: {cmd}...\n")
        log.see("end")
        self._btn_shown = False

        # Se o console estiver visível, escondê-lo e resetar o botão
        if tag in self.consoles_visible and self.consoles_visible[tag]:
            log.pack_forget()
            btn = self.detail_buttons.get(tag)
            if btn:
                btn.pack_forget()
                btn.configure(text=self._("Details ▼"))
            self.consoles_visible[tag] = False

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
            "ping": lambda log: self._run_ping(log, tag),
            "speedtest": lambda log: self._run_speedtest(log, tag),
            "ethtool": lambda log: self._run_ethtool(log, tag),
            "dhclient": lambda log: self._run_dhclient(log, tag),
            "ports": lambda log: self._run_ports(log, tag),
            "traceroute": lambda log: self._run_traceroute(log, tag),
            "wifi": lambda log: self._run_wifi(log, tag),
            "testdns": lambda log: self._run_testdns(log, tag),
            "lanscan": lambda log: self._run_lanscan(log, tag),
            "lancache": lambda log: self._run_lancache(log, tag),
            "public_ip": lambda log: self._run_public_ip(log, tag),
            "firewall": lambda log: self._run_firewall(log, tag),
            "sec_updates": lambda log: self._run_sec_updates(log, tag),
            "pci": lambda log: self._run_pci(log, "drv"),
            "update": lambda log: self._run_update(log, "drv"),
            "usb": lambda log: self._run_usb(log, "drv"),
            "modules": lambda log: self._run_modules(log, "drv"),
            "cpu_info": lambda log: self._run_cpu_info(log, "drv"),
            "firmware": lambda log: self._run_firmware(log, "drv"),
            "video_drv": lambda log: self._run_video_drv(log, "drv"),
            "net_drv": lambda log: self._run_net_drv(log, "drv"),
            "auto_update": lambda log: self._run_auto_update(log, "drv"),
        }
        method = action_map.get(cmd)
        print(f"DEBUG _execute_command: cmd={cmd}, method found: {method is not None}")
        if method:
            try:
                method(log)
                log.update()  # Force UI refresh after method execution
            except Exception as e:
                log.insert("end", self._("Error executing command: {e}\n").format(e=e))
                log.update()
        else:
            log.insert("end", self._("Unknown command: {cmd}\n").format(cmd=cmd))
            log.update()

    # ------------------------------------------------------------------------
    # Helper command methods
    # ------------------------------------------------------------------------
    def _run_speedtest(self, log, tag):
        self.action_handler.run_speedtest(log)

    def _run_ping(self, log, tag):
        log.insert("end", "🏓 Pinging google.com...\n")
        log.see("end")
        log.update()
        
        def callback(res):
            if res and res.returncode == 0:
                output_lines = []
                for line in res.stdout.splitlines():
                    if "time=" in line:
                        time_ms = line.split("time=")[1].split()[0]
                        log.insert("end", f"📶 Ping: {time_ms}ms\n")
                        break
                log.update()
                if not self._btn_shown:
                    self._show_detail_button(tag)
                    self._btn_shown = True
            elif res:
                log.insert("end", "❌ Ping failed\n")
                log.update()
        
        self._run_subprocess(["ping", "-c", "4", "google.com"], log, tag=tag, callback=callback)

    def _run_testdns(self, log, tag):
        log.insert("end", "🔍 Testing DNS resolution...\n")
        log.see("end")
        log.update()
        self._run_subprocess(["nslookup", "google.com"], log, tag=tag)

    def _run_change_dns(self, dns_ip, log):
        cmd = self.action_mapper.dns_command(dns_ip)
        log.insert("end", f"🌐 Changing DNS to {dns_ip}...\n")
        log.see("end")
        log.update()
        self._run_subprocess(cmd.split() if isinstance(cmd, str) else cmd, log, use_sudo=True, tag="net")

    def _run_firewall(self, log, tag):
        log.insert("end", "🛡️ Checking firewall status...\n")
        log.see("end")
        log.update()
        self._run_subprocess(["sudo", "ufw", "status"], log, tag=tag)

    def _run_sec_updates(self, log, tag):
        log.insert("end", "📦 Checking for security updates...\n")
        log.see("end")
        log.update()
        self._run_subprocess(["sudo", "apt", "update"], log, tag=tag)

    def _run_video_drv(self, log, tag):
        log.insert("end", "🖥️ Checking video drivers...\n")
        log.see("end")
        log.update()
        
        driver_info = self.hw.get_driver_info()
        
        if driver_info.get("nvidia_driver"):
            log.insert("end", f"🟢 NVIDIA Driver: {driver_info['nvidia_driver']}\n")
            if driver_info.get("nvidia_update"):
                log.insert("end", "⚠️ Update available! Check NVIDIA website.\n")
            else:
                log.insert("end", "✅ Driver is up to date.\n")
        elif driver_info.get("amd_driver"):
            log.insert("end", f"🔴 AMD Driver: {driver_info['amd_driver']}\n")
            log.insert("end", "💡 Check AMD website for updates.\n")
        else:
            log.insert("end", f"🟢 Intel/Other: {driver_info.get('intel_driver', 'Unknown')}\n")
            log.insert("end", "💡 Updates come with kernel updates.\n")
        
        log.update()

    def _run_net_drv(self, log, tag):
        log.insert("end", "🌐 Checking network drivers...\n")
        log.see("end")
        log.update()
        
        driver_info = self.hw.get_driver_info()
        
        if driver_info.get("network_drivers"):
            log.insert("end", "📡 Network Controllers:\n")
            for driver in driver_info["network_drivers"][:5]:
                log.insert("end", f"  {driver}\n")
        else:
            log.insert("end", "❌ No network drivers found.\n")
        
        log.update()

    def _run_auto_update(self, log, tag):
        log.insert("end", "🔄 Configuring automatic updates...\n")
        log.see("end")
        log.update()
        
        log.insert("end", "⚠️ Auto-update configuration varies by distribution.\n")
        log.insert("end", "💡 For Ubuntu/Debian: sudo dpkg-reconfigure -plow unattended-upgrades\n")
        log.insert("end", "💡 For Fedora: sudo dnf install dnf-automatic\n")
        log.insert("end", "💡 For Arch: sudo pacman -S pacman-contrib\n")
        log.update()

    def _run_ethtool(self, log, tag="net"):
        log.insert("end", "🕵️ Running network diagnostic...\n")
        log.see("end")
        log.update()
        self._run_subprocess(["ethtool", "eth0"], log, tag=tag)

    def _run_dhclient(self, log, tag="net"):
        log.insert("end", "🔄 Renewing IP address...\n")
        log.see("end")
        log.update()
        self._run_subprocess(["sudo", "dhclient", "-v"], log, use_sudo=True, tag=tag)

    def _run_ports(self, log, tag="net"):
        print("DEBUG: _run_ports called")
        log.insert("end", "🔓 Scanning open ports...\n")
        log.see("end")
        log.update()
        ports = self.security_scanner.scan_open_ports()
        for p in ports:
            log.insert("end", p + "\n")
        log.update()

    def _run_traceroute(self, log, tag="net"):
        print("DEBUG: _run_traceroute called")
        log.insert("end", "🌍 Running traceroute...\n")
        log.see("end")
        log.update()
        self._run_subprocess(["traceroute", "google.com"], log, tag=tag)

    def _run_wifi(self, log, tag="net"):
        print("DEBUG: _run_wifi called")
        log.insert("end", "📶 Getting Wi-Fi info...\n")
        log.see("end")
        log.update()
        self._run_subprocess(["iwconfig"], log, tag=tag)

    def _run_testdns(self, log, tag="net"):
        print("DEBUG: _run_testdns called")
        log.insert("end", "🎛️ Testing DNS...\n")
        log.see("end")
        log.update()
        self._run_subprocess(["nslookup", "google.com"], log, tag=tag)

    def _run_lanscan(self, log, tag="net"):
        print("DEBUG: _run_lanscan called")
        log.insert("end", "🌐 Scanning local network...\n")
        log.see("end")
        log.update()
        devices = self.lan_scanner.scan_network()
        for d in devices:
            log.insert("end", f"{d['ip']} - {d['mac']} - {d['hostname']} - {d['vendor']}\n")
        log.update()

    def _run_lancache(self, log, tag="net"):
        print("DEBUG: _run_lancache called")
        log.insert("end", "💾 Getting LAN cache status...\n")
        log.see("end")
        log.update()
        log.insert("end", self.lan_cache.get_status() + "\n")
        log.update()

    def _run_public_ip(self, log, tag="net"):
        print("DEBUG: _run_public_ip called")
        log.insert("end", "🌍 Getting public IP...\n")
        log.see("end")
        log.update()
        import requests
        try:
            ip = requests.get("https://api.ipify.org", timeout=5).text
            log.insert("end", self._("Public IP: {ip}\n").format(ip=ip))
        except:
            log.insert("end", self._("Error obtaining public IP.\n"))
        log.update()

    def _run_pci(self, log, tag="drv"):
        print("DEBUG: _run_pci called")
        self._run_subprocess(["lspci"], log, tag=tag)

    def _run_update(self, log, tag="drv"):
        print("DEBUG: _run_update called")
        self._run_subprocess(["sudo", "apt", "update"], log, use_sudo=True, tag=tag)

    def _run_usb(self, log, tag="drv"):
        print("DEBUG: _run_usb called")
        self._run_subprocess(["lsusb"], log, tag=tag)

    def _run_modules(self, log, tag="drv"):
        print("DEBUG: _run_modules called")
        self._run_subprocess(["lsmod"], log, tag=tag)

    def _run_cpu_info(self, log, tag="drv"):
        print("DEBUG: _run_cpu_info called")
        try:
            with open("/proc/cpuinfo") as f:
                log.insert("end", f.read())
        except:
            log.insert("end", self._("Could not read /proc/cpuinfo.\n"))
        log.update()

    def _run_firmware(self, log, tag="drv"):
        print("DEBUG: _run_firmware called")
        self._run_subprocess(["dmesg", "|", "grep", "-i", "firmware"], log, shell=True, tag=tag)

    def _run_video_drv(self, log, tag="drv"):
        print("DEBUG: _run_video_drv called")
        # List video devices
        self._run_subprocess(["lspci", "-k", "-d", "::0300"], log, tag=tag)
        log.insert("end", "\n--- Driver Status ---\n")
        # Check if driver is loaded
        import subprocess
        try:
            result = subprocess.run(["lsmod"], capture_output=True, text=True)
            video_modules = [line.split()[0] for line in result.stdout.split('\n') 
                           if any(m in line.lower() for m in ['nvidia', 'amd', 'i915', 'radeon', ' nouveau'])]
            if video_modules:
                log.insert("end", f"✅ Loaded video modules: {', '.join(video_modules)}\n")
                # Check for proprietary drivers
                if 'nvidia' in video_modules:
                    subprocess.run(["nvidia-smi"], capture_output=True, text=True)
                    if result.returncode == 0:
                        log.insert("end", "✅ NVIDIA driver is active\n")
                    else:
                        log.insert("end", "⚠️ NVIDIA driver may need update\n")
            else:
                log.insert("end", "⚠️ No proprietary video driver detected\n")
        except Exception as e:
            log.insert("end", f"Info: {e}\n")
        log.update()

    def _run_net_drv(self, log, tag="drv"):
        print("DEBUG: _run_net_drv called")
        # List network devices
        self._run_subprocess(["lspci", "-k", "-d", "::0200"], log, tag=tag)
        log.insert("end", "\n--- Driver Status ---\n")
        # Check network drivers loaded
        import subprocess
        try:
            result = subprocess.run(["lsmod"], capture_output=True, text=True)
            net_modules = [line.split()[0] for line in result.stdout.split('\n') 
                          if any(m in line for m in ['e1000', 'rtl', 'ath', 'iwl', 'brcm', 'mt']) and line.split()]
            if net_modules:
                log.insert("end", f"✅ Network drivers loaded: {', '.join(net_modules)}\n")
            else:
                log.insert("end", "✅ Using built-in kernel drivers\n")
        except Exception as e:
            log.insert("end", f"Info: {e}\n")
        log.update()

    def _run_auto_update(self, log, tag="drv"):
        print("DEBUG: _run_auto_update called")
        log.insert("end", self._("Configuring auto updates (not implemented).\n"))
        log.update()

    def _run_firewall(self, log, tag="sec"):
        print("DEBUG: _run_firewall called")
        status = self.security_scanner.check_firewall_status()
        log.insert("end", status)
        log.update()

    def _run_sec_updates(self, log, tag="sec"):
        print("DEBUG: _run_sec_updates called")
        updates = self.security_scanner.check_security_updates()
        for u in updates:
            log.insert("end", u + "\n")
        log.update()

    def _change_dns(self, dns_ip, log):
        if hasattr(self, "action_mapper"):
            cmd = self.action_mapper.dns_command(dns_ip)
            if cmd:
                self._run_subprocess(cmd, log, shell=True, tag="dns")
            else:
                log.insert("end", self._("Could not generate DNS command for this OS.\n"))
        else:
            log.insert("end", self._("ActionMapper not available.\n"))

    def _run_subprocess(self, cmd, log, use_sudo=False, shell=False, tag=None):
        try:
            if use_sudo and self.SO == "Linux":
                if isinstance(cmd, list):
                    cmd = ["sudo"] + cmd  # Use sudo instead of pkexec
                else:
                    cmd = "sudo " + cmd
            print(f"DEBUG: _run_subprocess executing: {cmd}")
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True,
                                    bufsize=1,
                                    shell=shell)
            # Ler stdout linha por linha com update da UI
            output_lines = []
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line:
                    output_lines.append(line)
                    if not self._btn_shown:
                        self._show_detail_button(tag)
                        self._btn_shown = True
                    log.insert("end", line)
                    log.see("end")  # Auto-scroll
                    log.update_idletasks()  # Atualizar UI
            proc.wait()
            
            # Se não houve saída, mostrar mensagem
            if not output_lines:
                cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
                # Verificar se o comando existe
                cmd_to_check = cmd[0] if isinstance(cmd, list) else cmd.split()[0]
                check = subprocess.run(["which", cmd_to_check], capture_output=True)
                if check.returncode != 0:
                    log.insert("end", f"⚠️ Command not found: {cmd_to_check}\n")
                else:
                    log.insert("end", f"⚠️ Command executed but no output: {cmd_str}\n")
            
            log.update()  # Force UI refresh
        except Exception as e:
            log.insert("end", self._("Error executing command: {e}\n").format(e=e))
            log.update()

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
            btn.pack_forget()
            btn.configure(text=self._("Details ▼"))
            self.consoles_visible[tag] = False
        else:
            log.pack(fill="x", expand=True, padx=5, before=btn)
            btn.configure(text=self._("Hide Details ▲"))
            self.consoles_visible[tag] = True

    # ------------------------------------------------------------------------
    # Window management
    # ------------------------------------------------------------------------
    def _monitor_loop(self):
        # Dashboard auto-update disabled for now - causes widget duplication
        # Can be re-enabled after fixing the issue
        update_counter = 0
        while True:
            time.sleep(10)  # Longer interval to reduce overhead
            # Disabled: causes widget duplication issues
            pass

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
    
    def widget_title(self, widget_type):
        """Get title for a widget type."""
        titles = {
            "cpu": "CPU",
            "ram": "Memória RAM",
            "disks": "Discos",
            "battery": "Bateria",
            "gpu": "GPU",
            "temps": "Temperaturas",
            "uptime": "Uptime",
            "kernel": "Kernel",
            "distro": "Distribuição",
            "hostname": "Hostname",
            "health": "Saúde",
        }
        # Handle both id and full dict
        if isinstance(widget_type, dict):
            widget_id = widget_type.get("id", "")
            return titles.get(widget_id, widget_id.capitalize())
        return titles.get(widget_type, widget_type.capitalize())
    
    def widget_hostname(self, frame, tag):
        # Clear previous content
        for child in frame.winfo_children():
            child.destroy()
        
        import socket
        hostname = socket.gethostname()
        
        # Adjust font size based on widget size
        is_small = tag.startswith("small_")
        
        if is_small:
            # Small widget: icon + hostname
            icon_label = ctk.CTkLabel(
                frame,
                text="💻",
                font=("Inter", 14)
            )
            icon_label.pack(pady=(5, 0))
            
            label = ctk.CTkLabel(
                frame, 
                text=hostname, 
                font=("Inter", 12, "bold"),
                text_color=("gray10", "gray90")
            )
            label.pack(anchor="center")
        else:
            # Big widget
            label = ctk.CTkLabel(
                frame, 
                text=f"💻 {hostname}", 
                font=("Inter", 18, "bold"),
                text_color=("gray10", "gray90")
            )
            label.pack(anchor="center")

    def widget_distro(self, frame, tag):
        # Clear previous content
        for child in frame.winfo_children():
            child.destroy()
        
        is_small = tag.startswith("small_")
        
        # Try to get distribution name from os-release
        distro_name = "Linux"
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        full_distro = line.split("=")[1].strip().strip('"')
                        # Simplify name
                        if "Arch" in full_distro:
                            distro_name = "Arch Linux"
                        elif "Ubuntu" in full_distro:
                            distro_name = "Ubuntu"
                        elif "Debian" in full_distro:
                            distro_name = "Debian"
                        elif "Fedora" in full_distro:
                            distro_name = "Fedora"
                        elif "openSUSE" in full_distro:
                            distro_name = "openSUSE"
                        elif "Mint" in full_distro:
                            distro_name = "Linux Mint"
                        elif "Manjaro" in full_distro:
                            distro_name = "Manjaro"
                        elif "Pop" in full_distro:
                            distro_name = "Pop!_OS"
                        else:
                            distro_name = full_distro.split()[0]
                        break
        except:
            pass
        
        if is_small:
            # Small widget: icon + distro name
            icon_label = ctk.CTkLabel(
                frame,
                text="🐧",
                font=("Inter", 14)
            )
            icon_label.pack(pady=(5, 0))
            
            label = ctk.CTkLabel(
                frame, 
                text=distro_name, 
                font=("Inter", 11, "bold"),
                text_color=("gray10", "gray90")
            )
            label.pack(anchor="center")
        else:
            # Big widget
            label = ctk.CTkLabel(
                frame, 
                text=f"🐧 {distro_name}", 
                font=("Inter", 16, "bold"),
                text_color=("gray10", "gray90")
            )
            label.pack(anchor="center")

    def widget_kernel(self, frame, tag):
        # Clear previous content
        for child in frame.winfo_children():
            child.destroy()
        
        is_small = tag.startswith("small_")
        
        full_version = platform.release().split("-")[0]
        
        # Get main version number (e.g., "6.14")
        version_parts = full_version.split(".")
        if len(version_parts) >= 2:
            main_version = f"{version_parts[0]}.{version_parts[1]}"
        else:
            main_version = full_version
        
        if is_small:
            # Small widget: icon + version
            icon_label = ctk.CTkLabel(
                frame,
                text="🐧",
                font=("Inter", 12)
            )
            icon_label.pack(pady=(5, 0))
            
            label = ctk.CTkLabel(
                frame, 
                text=main_version, 
                font=("Inter", 12, "bold"),
                text_color=("gray10", "gray90")
            )
            label.pack(anchor="center")
        else:
            # Big widget: "Kernel Linux X.Y"
            label = ctk.CTkLabel(
                frame, 
                text=f"⚙️ Kernel Linux {main_version}", 
                font=("Inter", 14, "bold"),
                text_color=("gray10", "gray90")
            )
            label.pack(anchor="center")

    def widget_uptime(self, frame, tag):
        # Clear previous content
        for child in frame.winfo_children():
            child.destroy()
        
        is_small = tag.startswith("small_")
        
        from datetime import datetime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        delta = datetime.now() - boot_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        # Format time - don't show "0d" if days = 0
        if days == 0:
            # Less than 1 day - show hours or minutes
            if hours == 0:
                # Less than 1 hour - show minutes with 1 decimal
                total_hours = minutes / 60
                time_text = f"{total_hours:.1f}h"  # e.g., "0.5h"
            else:
                time_text = f"{hours}h"
        else:
            # More than 1 day
            time_text = f"{days}d {hours}h"
        
        if is_small:
            # Small widget: animated icon + time
            # Create container frame
            container = ctk.CTkFrame(frame, fg_color="transparent")
            container.pack(expand=True)
            
            # Icon label
            icon_label = ctk.CTkLabel(
                container,
                text="⏳",
                font=("Inter", 12),
                text_color=("gray10", "gray90")
            )
            icon_label.pack(side="left", padx=2)
            
            # Time label
            time_label = ctk.CTkLabel(
                container, 
                text=time_text, 
                font=("Inter", 12, "bold"),
                text_color=("gray10", "gray90")
            )
            time_label.pack(side="left", padx=2)
            
            # Store reference for animation
            frame._uptime_icon = icon_label
            frame._uptime_anim_counter = 0
            
            # Start animation
            self._animate_uptime(frame)
        else:
            # Big widget: static icon + time
            label = ctk.CTkLabel(
                frame, 
                text=f"⏳ {time_text}", 
                font=("Inter", 18, "bold"),
                text_color=("gray10", "gray90")
            )
            label.pack(anchor="center")

    def _animate_uptime(self, frame):
        """Animate uptime icon between ⏳ and ⌛"""
        if hasattr(frame, '_uptime_icon') and frame._uptime_icon.winfo_exists():
            frame._uptime_anim_counter = (frame._uptime_anim_counter + 1) % 2
            new_icon = "⌛" if frame._uptime_anim_counter == 0 else "⏳"
            frame._uptime_icon.configure(text=new_icon)
            # Schedule next update after 1 second
            frame.after(1000, lambda: self._animate_uptime(frame))

    def widget_cpu(self, frame, tag):
        # Clear previous content
        for child in frame.winfo_children():
            child.destroy()
        
        percent = psutil.cpu_percent(interval=0.1)
        color = get_usage_color(percent)
        
        # Check if this is a small widget
        is_small = tag.startswith("small_")
        
        if is_small:
            # Small widget - icon + percentage
            icon_label = ctk.CTkLabel(
                frame,
                text="🖥️",
                font=("Inter", 16),
                text_color=("gray10", "white")
            )
            icon_label.pack(pady=(5, 0))
            
            label = ctk.CTkLabel(
                frame, 
                text=f"{percent}%", 
                font=("Inter", 20, "bold"),
                text_color=color
            )
            label.pack(anchor="center")
        else:
            # Big widget - model name + progress bar and details
            # Get CPU model name
            try:
                cpu_model = "CPU"
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            cpu_model = line.split(":")[1].strip()
                            # Shorten for display
                            if "Intel" in cpu_model:
                                # e.g., "Intel i7-1165G7"
                                parts = cpu_model.split()
                                for p in parts:
                                    if p.startswith("i") and "-" in p:
                                        cpu_model = "Intel " + p
                                        break
                            elif "AMD" in cpu_model:
                                parts = cpu_model.split()
                                if len(parts) >= 4:
                                    cpu_model = " ".join(parts[:4])
                            break
            except:
                cpu_model = "CPU"
            
            # Model name label
            model_label = ctk.CTkLabel(
                frame,
                text=cpu_model,
                font=("Inter", 11),
                text_color=("gray40", "gray70")
            )
            model_label.pack(pady=(5, 0))
            
            # Progress bar
            progress = ctk.CTkProgressBar(frame, orientation="horizontal")
            progress.set(percent / 100)
            progress.configure(
                progress_color=color,
                fg_color="#3B3B3B",
                height=20
            )
            progress.pack(fill="x", padx=10, pady=(5, 5))
            
            # Percentage label
            label = ctk.CTkLabel(
                frame, 
                text=f"{percent}%", 
                font=("Inter", 28, "bold"),
                text_color=color
            )
            label.pack(anchor="center")
            
            # Status text
            status = "Normal" if percent <= 60 else "Alto" if percent <= 85 else "Crítico"
            status_label = ctk.CTkLabel(
                frame,
                text=status,
                font=("Inter", 12),
                text_color=color
            )
            status_label.pack(pady=(0, 10))

    def widget_ram(self, frame, tag):
        # Clear previous content
        for child in frame.winfo_children():
            child.destroy()
        
        mem = psutil.virtual_memory()
        percent = mem.percent
        color = get_usage_color(percent)
        is_small = tag.startswith("small_")
        
        if is_small:
            # Small widget - simple percentage display
            label = ctk.CTkLabel(
                frame, 
                text=f"{percent}%", 
                font=("Inter", 24, "bold"),
                text_color=color
            )
            label.pack(anchor="center")
        else:
            # Big widget - progress bar and details
            # Progress bar
            progress = ctk.CTkProgressBar(frame, orientation="horizontal")
            progress.set(percent / 100)
            progress.configure(
                progress_color=color,
                fg_color="#3B3B3B",
                height=20
            )
            progress.pack(fill="x", padx=10, pady=(10, 5))
            
            # Percentage label
            label = ctk.CTkLabel(
                frame, 
                text=f"{percent}%", 
                font=("Inter", 28, "bold"),
                text_color=color
            )
            label.pack(anchor="center")
            
            # Memory details
            used_gb = mem.used // (1024**3)
            total_gb = mem.total // (1024**3)
            details_label = ctk.CTkLabel(
                frame,
                text=f"{used_gb} GB / {total_gb} GB",
                font=("Inter", 12),
                text_color=("gray40", "gray70")
            )
            details_label.pack(pady=(0, 10))

    def widget_gpu(self):
        return "Intel HD Graphics 4000"

    def widget_battery(self):
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            return "No battery"
        percent = int(battery.percent)
        plugged = battery.power_plugged
        status = "Carregando" if plugged else "Descarregando"
        return {'percent': percent, 'plugged': plugged, 'status': status}


    def widget_disks(self):
        import psutil
        root = psutil.disk_usage('/')
        home = psutil.disk_usage('/home')
        return {
            'root': {'name': 'Sistema (/)', 'percent': root.percent, 'used': root.used, 'total': root.total},
            'home': {'name': 'Home (/home)', 'percent': home.percent, 'used': home.used, 'total': home.total},
        }


    def widget_temps(self, frame, tag):
        # Clear previous content
        for child in frame.winfo_children():
            child.destroy()
        
        is_small = tag.startswith("small_")
        temps = psutil.sensors_temperatures()
        
        # Get the first available temperature
        temp_value = None
        if temps:
            for name, entries in temps.items():
                if entries:
                    temp_value = entries[0].current
                    break
        
        if temp_value is not None:
            color = get_temp_color(temp_value)
            icon = get_temp_icon(temp_value)
            
            if is_small:
                # Small widget - icon and temperature
                label = ctk.CTkLabel(
                    frame, 
                    text=f"{icon} {temp_value}°C", 
                    font=("Inter", 20, "bold"),
                    text_color=color
                )
                label.pack(anchor="center")
            else:
                # Big widget - icon, temperature, and status
                # Icon
                icon_label = ctk.CTkLabel(
                    frame,
                    text=icon,
                    font=("Inter", 50)
                )
                icon_label.pack(pady=(10, 5))
                
                # Temperature label
                label = ctk.CTkLabel(
                    frame, 
                    text=f"{temp_value}°C", 
                    font=("Inter", 32, "bold"),
                    text_color=color
                )
                label.pack(anchor="center")
                
                # Status
                if temp_value < 30:
                    status = "Frio"
                elif temp_value <= 50:
                    status = "Normal"
                elif temp_value <= 70:
                    status = "Morno"
                else:
                    status = "Quente"
                
                status_label = ctk.CTkLabel(
                    frame,
                    text=status,
                    font=("Inter", 14),
                    text_color=color
                )
                status_label.pack(pady=(0, 10))
        else:
            # No temperature data
            label = ctk.CTkLabel(
                frame, 
                text="N/A", 
                font=("Inter", 16),
                text_color=("gray40", "gray70")
            )
            label.pack(anchor="center")

    def widget_health(self, frame, tag):
        # Clear previous content
        for child in frame.winfo_children():
            child.destroy()
        
        is_small = tag.startswith("small_")
        
        health = self.health_monitor.calculate_health_score()
        score = health["score"]
        
        # Get color based on health score
        if score >= 80:
            color = COLOR_SUCCESS
            status_text = "Bom"
        elif score >= 50:
            color = COLOR_WARNING
            status_text = "Regular"
        else:
            color = COLOR_DANGER
            status_text = "Ruim"
        
        font_size = 20 if is_small else 28
        
        # Icon based on health
        icon = "❤️" if score >= 80 else "⚠️" if score >= 50 else "🚨"
        
        if is_small:
            # Small widget: icon + percentage
            label = ctk.CTkLabel(
                frame, 
                text=f"{icon} {score}%", 
                font=("Inter", font_size, "bold"),
                text_color=color
            )
            label.pack(anchor="center")
        else:
            # Big widget: icon + percentage + status text
            label = ctk.CTkLabel(
                frame, 
                text=f"{icon} {score}%", 
                font=("Inter", font_size, "bold"),
                text_color=color
            )
            label.pack(pady=(10, 5))
            
            status_label = ctk.CTkLabel(
                frame,
                text=status_text,
                font=("Inter", 16, "bold"),
                text_color=color
            )
            status_label.pack(pady=(0, 10))

    def widget_realtime_chart(self, frame, tag):
        from core.dashboard import RealTimeChartWidget
        chart = RealTimeChartWidget(frame, tag)
        if not hasattr(self, "_charts"):
            self._charts = []
        self._charts.append(chart)

    # =========================================================================
    # Dashboard Widget Data Getters
    # =========================================================================
    
    def get_widget_cpu(self):
        """Get CPU data for dashboard widget."""
        import platform
        # Get CPU model
        model = "CPU"
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("model name"):
                        model = line.split(":")[1].strip()
                        # Shorten
                        if "Intel" in model:
                            parts = model.split()
                            for p in parts:
                                if p.startswith("i") and "-" in p:
                                    model = "Intel " + p
                                    break
                        elif "AMD" in model:
                            parts = model.split()
                            if len(parts) >= 4:
                                model = " ".join(parts[:4])
                        break
        except:
            pass
        
        # Get usage
        percent = int(psutil.cpu_percent(interval=0.1))
        
        return {
            "model": model,
            "percent": percent,
        }
    
    def get_widget_ram(self):
        """Get RAM data for dashboard widget."""
        mem = psutil.virtual_memory()
        percent = int(mem.percent)
        used_gb = mem.used / (1024**3)
        total_gb = mem.total / (1024**3)
        
        return {
            "percent": percent,
            "used_gb": used_gb,
            "total_gb": total_gb,
        }
    
    def get_widget_disks(self):
        """Get disk data for dashboard widget."""
        partitions = []
        
        # Try common mount points
        mount_points = ['/', '/home']
        
        for mp in mount_points:
            try:
                usage = psutil.disk_usage(mp)
                if usage.total > 0:
                    if mp == '/':
                        name = "System (/)"
                    elif mp == '/home':
                        name = "Home (/home)"
                    else:
                        name = mp
                    partitions.append({
                        "name": name,
                        "mount": mp,
                        "percent": int(usage.percent),
                        "used_gb": usage.used // (1024**3),
                        "total_gb": usage.total // (1024**3),
                    })
            except:
                pass
        
        return {"partitions": partitions}
    
    def get_widget_battery(self):
        """Get battery data for dashboard widget."""
        battery = psutil.sensors_battery()
        if battery:
            return {
                "percent": int(battery.percent),
                "plugged": battery.power_plugged,
            }
        return {"percent": 0, "plugged": False}
    
    def get_widget_gpu(self):
        """Get GPU data for dashboard widget."""
        # Try lspci
        gpu_name = "N/A"
        try:
            result = subprocess.run(["lspci"], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if "vga" in line.lower() or "display" in line.lower():
                    # Extract name after colon
                    if ":" in line:
                        gpu_name = line.split(":", 1)[1].strip()
                    # Clean up
                    gpu_name = gpu_name.replace("VGA compatible controller", "").strip()
                    gpu_name = gpu_name.replace("3D controller", "").strip()
                    break
        except:
            pass
        
        return {"name": gpu_name}
    
    def get_widget_temps(self):
        """Get temperature data for dashboard widget."""
        temp = 0
        try:
            temps = psutil.sensors_temperatures()
            # Get CPU temp
            for name, entries in temps.items():
                if "cpu" in name.lower() or "k10" in name.lower():
                    for entry in entries:
                        if hasattr(entry, 'current') and entry.current:
                            temp = int(entry.current)
                            break
                    if temp:
                        break
        except:
            pass
        
        return {"temp": temp}
    
    def get_widget_uptime(self):
        """Get uptime data for dashboard widget."""
        from datetime import datetime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        delta = datetime.now() - boot_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        
        if days == 0:
            if hours == 0:
                text = f"{delta.seconds // 60}m"
            else:
                text = f"{hours}h"
        else:
            text = f"{days}d {hours}h"
        
        return {"text": text}
    
    def get_widget_kernel(self):
        """Get kernel data for dashboard widget."""
        version = platform.uname().release
        # Get just X.Y
        parts = version.split(".")
        if len(parts) >= 2:
            version = f"{parts[0]}.{parts[1]}"
        
        return {"version": version}
    
    def get_widget_distro(self):
        """Get distribution data for dashboard widget."""
        name = "Linux"
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        name = line.split("=")[1].strip().strip('"')
                        break
        except:
            pass
        
        return {"name": name}
    
    def get_widget_hostname(self):
        """Get hostname data for dashboard widget."""
        import socket
        return {"hostname": socket.gethostname()}
    
    def get_widget_health(self):
        """Get health score for dashboard widget."""
        # Calculate based on CPU, RAM, disk
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            
            # Get disk usage
            disk = 0
            try:
                disk = psutil.disk_usage('/').percent
            except:
                pass
            
            # Weighted average
            health = 100 - ((cpu * 0.3) + (ram * 0.3) + (disk * 0.4))
            health = max(0, min(100, health))
            
            return {"score": int(health)}
        except:
            return {"score": 0}


        from core.dashboard import RealTimeChartWidget
        chart = RealTimeChartWidget(frame, tag)
        if not hasattr(self, "_charts"):
            self._charts = []
        self._charts.append(chart)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - run all cards from command line
        print("=" * 50)
        print("SPEEDSCAN TEST MODE")
        print("=" * 50)
        # Create minimal app instance for testing
        class TestRunner:
            def __init__(self):
                self.SO = "Linux"
                from core.actions import CommandRunner, ActionHandler, ActionMapper
                self.runner = CommandRunner(self.SO)
                self.action_handler = ActionHandler(self)
                self.action_mapper = ActionMapper(self.SO, self.runner, False)
                
                # Mock the _() function
                def _(s): return s
                self._ = _
                
                # Import other modules needed
                from core.hardware import HardwareInfo
                from core.health_score import HealthScore
                from core.security_scanner import SecurityScanner
                from core.lan_scanner import LANScanner
                from core.lan_cache import LANCacheManager
                from core.browser_cleaner import BrowserCleaner
                from core.speed_test import SpeedTester
                
                self.hw = HardwareInfo(self.SO, self.runner)
                self.health_monitor = HealthScore()
                self.security_scanner = SecurityScanner(self.SO)
                self.lan_scanner = LANScanner()
                self.lan_cache = LANCacheManager(self.SO)
                self.browser_cleaner = BrowserCleaner()
                self.speed_tester = SpeedTester()
            
            def run_test(self, test_name, func, *args):
                print(f"\n--- Testing: {test_name} ---")
                try:
                    # Create a StringIO to capture output
                    import io
                    from unittest.mock import MagicMock
                    log = MagicMock()
                    log_lines = []
                    def mock_insert(end, text):
                        log_lines.append(text)
                    log.insert = mock_insert
                    log.delete = lambda *a: None
                    log.update = lambda: None
                    
                    func(log, *args)
                    
                    if log_lines:
                        for line in log_lines:
                            print(f"  OUTPUT: {line.strip()}")
                    else:
                        print("  (no output)")
                except Exception as e:
                    print(f"  ERROR: {e}")
        
        runner = TestRunner()
        
        # Test all optimization cards
        print("\n=== OPTIMIZATION CARDS ===")
        runner.run_test("cache", runner.action_handler.run_cache_clean)
        runner.run_test("swap", runner.action_handler.run_swap_reset)
        runner.run_test("check", runner.action_handler.run_fs_check)
        runner.run_test("turbo", runner.action_handler.run_turbo_mode)
        runner.run_test("browsers", runner.action_handler.run_browser_clean)
        
        # Test network cards
        print("\n=== NETWORK CARDS ===")
        # These need the actual main.py methods
        # We'll test what we can without GUI
        
        print("\n=== DRIVER CARDS ===")
        
        print("\n=== SECURITY CARDS ===")
        runner.run_test("ports", runner.security_scanner.scan_open_ports)
        runner.run_test("firewall", runner.security_scanner.check_firewall_status)
        runner.run_test("sec_updates", runner.security_scanner.check_security_updates)
        
        print("\n" + "=" * 50)
        print("TEST COMPLETE")
        print("=" * 50)
    else:
        app = SpeedScan()
        app.mainloop()
