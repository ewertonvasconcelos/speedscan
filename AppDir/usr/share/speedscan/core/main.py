#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SpeedScan - Versão 1.0.0
# Desenvolvedor: Ewerton Vasconcelos

from logging.handlers import RotatingFileHandler
from pathlib import Path
import logging
import os
import platform
import threading
import json
import sys
import re
import time
import subprocess
from PIL import Image, ImageDraw
import psutil
import customtkinter as ctk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Importações dos módulos internos
from core import config
from core.i18n import _, get_translation
from core.hardware import HardwareInfo
from core.actions import CommandRunner, ActionMapper, ActionHandler
from core.scheduler import Scheduler
from core.health_score import HealthScore
from core.temperature_monitor import TemperatureMonitor
from core.smart_monitor import SmartMonitor
from core.browser_cleaner import BrowserCleaner
from core.speed_test import SpeedTester
from core.process_manager import ProcessManager
from core.historical_metrics import MetricsCollector, MetricsDB
from core.lan_scanner import LANScanner
from core.ai_proactive import AIProactive
from core.security_scanner import SecurityScanner
from core.dashboard import Dashboard
from core.lan_cache import LANCacheManager
from core.chat import ChatFrame
from core.first_run import FirstRunWizard
from core.cookie_manager import CookieManager
from core.trash_manager import TrashManager
import core.ui as ui

# Módulo de limpeza do Windows (apenas se for Windows)
try:
    from core.windows_cleaner import WindowsCleaner
except ImportError:
    WindowsCleaner = None

# Configuração de logging
config.LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = config.LOG_DIR / "speedscan.log"
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logging.basicConfig(level=logging.ERROR, handlers=[handler])

# =============================================================================
# Configuração padrão unificada
# =============================================================================
DEFAULT_CONFIG = {
    "theme": "grey",
    "username": "ewerton",
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

# Definição de temas (apenas 3)
THEMES = {
    "grey":    {"mode": "light", "bg": "#d1d5db", "side": "#374151", "acc": "#4b5563", "text": "#111827"},
    "dark":    {"mode": "dark",  "bg": "#080808", "side": "#000000", "acc": "#10b981", "text": "#ffffff"},
    "light":   {"mode": "light", "bg": "#ffffff", "side": "#f8fafc", "acc": "#2563eb", "text": "#0f172a"}
}

LANGUAGES = {
    "pt_BR": "Português Brasileiro",
    "en_US": "English (US)",
    "es_ES": "Español"
}

SCALES = {
    "auto": "Automático",
    "100": "100%",
    "125": "125%",
    "150": "150%"
}

AI_SUGGESTIONS = [
    "Ollama (local)", "OpenAI GPT", "Google Gemini", "Claude (Anthropic)",
    "Llama 3 (Meta)", "Mistral AI", "Cohere", "DeepSeek", "Configure Local AI"
]

# =============================================================================
# Classe principal SpeedScan
# =============================================================================
class SpeedScan(ctk.CTk):
    """Janela principal do aplicativo."""

    def __init__(self):
        super().__init__()
        self.SO = platform.system()
        self.runner = CommandRunner(self.SO)
        self.hw = HardwareInfo(self.SO, self.runner)
        self.config = self._load_config()
        
        # Inicializa tradução com o idioma da config
        self._ = get_translation(self.config.get('language', 'pt_BR'))
        
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

        self.health_monitor = HealthScore()
        self.health_score_var = ctk.StringVar(value=self._("Calculando..."))
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

    # =========================================================================
    # Métodos de configuração e tema
    # =========================================================================
    def _load_config(self):
        if config.CONFIG_FILE.exists():
            try:
                with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in cfg:
                        cfg[key] = value
                if cfg.get("theme") == "default":
                    cfg["theme"] = "grey"
                return cfg
            except Exception as e:
                logging.error(_("Erro ao carregar config: {error}").format(error=e))
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def _save_config(self):
        try:
            with open(config.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(_("Erro ao salvar config: {error}").format(error=e))

    def update_theme_vars(self):
        t = THEMES.get(self.config["theme"], THEMES["grey"])
        ctk.set_appearance_mode(t["mode"])
        self.bg_color = t["bg"]
        self.side_bg = t["side"]
        self.acc_color = t["acc"]
        self.text_color = t["text"]
        self.light_bg = self._lighten_color(self.bg_color, 0.2)

    def _lighten_color(self, hex_color, factor):
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def apply_ui_scale(self):
        scale = self.config.get("ui_scale", "auto")
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

    # =========================================================================
    # Sidebar e navegação
    # =========================================================================
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.side_bg)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        top = ctk.CTkFrame(sidebar, fg_color="transparent")
        top.pack(pady=(15, 0))
        icon = self.round_image(str(config.ICON_PATH)) if config.ICON_PATH.exists() else None
        if icon:
            lbl_icon = ctk.CTkLabel(top, image=icon, text="", width=96, height=96)
        else:
            lbl_icon = ctk.CTkLabel(top, text="⚡", font=("Inter", 48), width=96, height=96, text_color=self.acc_color)
        lbl_icon.pack()

        center = ctk.CTkFrame(sidebar, fg_color="transparent")
        center.pack(expand=False, fill="x", pady=(38, 15))

        nav_items = [
            ("📊", self._("Dashboard"), "dashboard"),
            ("⚡", self._("Otimização"), "otimizacao"),
            ("📀", self._("Rede"), "rede"),
            ("📝", self._("Drivers"), "drivers"),
        ]

        level_items = {
            1: [],
            2: [self._("Processos")],
            3: [self._("Processos"), self._("Histórico"), self._("Segurança"), self._("Agente IA"), self._("Limpeza Win")]
        }

        for icon, text, target in nav_items:
            btn = self._sidebar_btn(center, icon, text, target)
            self.sidebar_buttons[target] = btn

        level = self.config.get("expert_level", 1)
        if level >= 2:
            icon_map = {
                self._("Processos"): ("📋", "processos"),
                self._("Histórico"): ("📈", "historico"),
                self._("Segurança"): ("🛡️", "seguranca"),
                self._("Agente IA"): ("🤖", "agente"),
                self._("Limpeza Win"): ("🧹", "windows_cleaner")
            }
            for item in level_items[level]:
                icon, target = icon_map[item]
                btn = self._sidebar_btn(center, icon, item, target)
                self.sidebar_buttons[target] = btn

        for icon, text, target in [("⚙️", self._("Configurações"), "config"), ("ℹ️", self._("Sobre"), "sobre")]:
            btn = self._sidebar_btn(center, icon, text, target)
            self.sidebar_buttons[target] = btn

        spacer = ctk.CTkLabel(center, text="", height=0)
        spacer.pack(expand=False)

    def _sidebar_btn(self, parent, icon, text, target):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=2, fill="x", padx=10)
        btn = ctk.CTkButton(frame, text=f"{icon}  {text}", anchor="w", height=30,
                            fg_color="transparent", hover_color=self.acc_color,
                            font=("Inter", 13), corner_radius=10,
                            text_color=self.text_color,
                            command=lambda: self.show_frame(target),
                            cursor="hand2")
        btn.pack(fill="x")
        return btn

    def show_frame(self, target):
        for f in self.frames.values():
            f.pack_forget()
        if target not in self.frames:
            self.frames[target] = self._create_frame(target)
        self.frames[target].pack(fill="both", expand=True)
        self.current_module = target
        for key, btn in self.sidebar_buttons.items():
            btn.configure(fg_color=self.acc_color if key == target else "transparent")
        if target == "processos":
            self._refresh_process_list()
        elif target == "historico":
            self._update_graphs()
        elif target == "agente":
            self._update_ai_suggestions()

    def _create_frame(self, target):
        frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        getattr(self, f"_fill_{target}")(frame)
        return frame

    # =========================================================================
    # Métodos de preenchimento das abas
    # =========================================================================
    def _fill_dashboard(self, parent):
        ctk.CTkLabel(parent, text=self._("Dashboard Rotativo"), font=("Inter", 28, "bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0, 20))
        self.dashboard = Dashboard(parent, self, fg_color="transparent")
        self.dashboard.pack(fill="both", expand=True)

    def _fill_otimizacao(self, parent):
        ctk.CTkLabel(parent, text=self._("Otimização"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("🧹 Limpeza de Cache"), "cache", False),
            (self._("📄 Reset de Swap"), "swap", False),
            (self._("🔍 Verificar Erros"), "check", False),
            (self._("🔥 Modo Turbo"), "turbo", False),
            (self._("Steam"), "steam", False),
            (self._("Lutris"), "lutris", False),
            (self._("Heroic Launcher"), "heroic", False),
            (self._("Bottles"), "bottles", False),
            (self._("Wine"), "wine", False),
            (self._("MangoHud"), "mangohud", False),
            (self._("Governor"), "governor", False),
            (self._("🎮 Emulador Dolphin"), "dolphin", False),
            (self._("🧹 Limpeza de Navegadores"), "browsers", False),
            (self._("⚙️ Gerenciar Serviços"), "services", False),
            (self._("📋 Análise de Logs"), "logs", False),
            (self._("🗑️ Gerenciar Cookies"), "cookies", False),
            (self._("🔧 Otimizar SSD (TRIM)"), "trim", False),
            (self._("📄 Reparar Pacotes Quebrados"), "fix_broken", False),
        ]
        level = self.config.get("expert_level", 1)
        if level == 1:
            items = [item for item in items if item[1] not in ["services", "logs", "cookies", "trim", "fix_broken"]]
        elif level == 2:
            items = [item for item in items if item[1] not in ["logs", "cookies"]]
        ui.create_card_grid(parent, items, "ot", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "ot", self.acc_color, self.toggle_console)
        self.detail_buttons["ot"] = btn
        self.logs["ot"] = log

    def _fill_rede(self, parent):
        ctk.CTkLabel(parent, text=self._("Rede"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("🏓 Ping"), "ping", False),
            (self._("🌐 Cloudflare DNS"), "1.1.1.1", True),
            (self._("📡 Google DNS"), "8.8.8.8", True),
            (self._("📡 AdGuard DNS"), "94.140.14.14", True),
            (self._("🔄 DNS Automático"), "auto", True),
            (self._("📊 Testar Velocidade"), "speedtest", False),
            (self._("🕹️ Diagnóstico Placa"), "ethtool", False),
            (self._("🔄 Renovar IP"), "dhclient", False),
            (self._("🔓 Portas Abertas"), "ports", False),
            (self._("🛰️ TraceRoute"), "traceroute", False),
            (self._("📶 Informações Wi-Fi"), "wifi", False),
            (self._("📝 Testar DNS"), "testdns", False),
            (self._("🔎 Scanner LAN"), "lanscan", False),
            (self._("🗄️ LANCache"), "lancache", False),
            (self._("📡 Verificar IP Público"), "public_ip", False),
        ]
        level = self.config.get("expert_level", 1)
        if level == 1:
            items = [item for item in items if item[1] not in ["ports", "traceroute", "ethtool", "dhclient", "lanscan", "lancache"]]
        elif level == 2:
            items = [item for item in items if item[1] not in ["lanscan", "lancache"]]
        ping_labels = ui.create_card_grid(parent, items, "net", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        if ping_labels:
            self.ping_label = ping_labels[0]
        btn, log = ui.add_console(parent, "net", self.acc_color, self.toggle_console)
        self.detail_buttons["net"] = btn
        self.logs["net"] = log

    def _fill_drivers(self, parent):
        ctk.CTkLabel(parent, text=self._("Drivers"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("🎥 PCI (Vídeo/Rede)"), "pci", False),
            (self._("🔧 Atualizar Sistema"), "update", False),
            (self._("🖥️ USB Conectados"), "usb", False),
            (self._("🧠 Módulos Kernel"), "modules", False),
            (self._("⚙️ CPU Detalhada"), "cpu_info", False),
            (self._("⚙️ Erros de Firmware"), "firmware", False),
            (self._("🎥 Drivers de Vídeo"), "video_drv", False),
            (self._("🔄 Drivers de Rede"), "net_drv", False),
            (self._("🔄 Atualizações Automáticas"), "auto_update", False),
        ]
        level = self.config.get("expert_level", 1)
        if level == 1:
            items = [item for item in items if item[1] not in ["modules", "cpu_info", "firmware", "video_drv", "net_drv", "auto_update"]]
        elif level == 2:
            items = [item for item in items if item[1] not in ["video_drv", "net_drv", "auto_update"]]
        ui.create_card_grid(parent, items, "drv", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "drv", self.acc_color, self.toggle_console)
        self.detail_buttons["drv"] = btn
        self.logs["drv"] = log

    # ---------- ABA PROCESSOS (COMPLETA) ----------
    def _fill_processos(self, parent):
        ctk.CTkLabel(parent, text=self._("Gerenciador de Processos"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))

        # Frame de filtro e ordenação
        control_frame = ctk.CTkFrame(parent, fg_color="transparent")
        control_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(control_frame, text=self._("Filtrar:"), font=("Inter",12)).pack(side="left", padx=5)
        self.filter_entry = ctk.CTkEntry(control_frame, placeholder_text=self._("Nome do processo"), width=150)
        self.filter_entry.pack(side="left", padx=5)
        self.filter_entry.bind("<KeyRelease>", self._on_filter_change)

        ctk.CTkLabel(control_frame, text=self._("Ordenar por:"), font=("Inter",12)).pack(side="left", padx=5)
        self.sort_var = ctk.StringVar(value="cpu_percent")
        sort_menu = ctk.CTkOptionMenu(control_frame, values=["cpu_percent", "memory_percent", "name", "pid"],
                                       variable=self.sort_var, command=self._on_sort_change, width=100)
        sort_menu.pack(side="left", padx=5)

        self.reverse_var = ctk.BooleanVar(value=True)
        reverse_check = ctk.CTkCheckBox(control_frame, text=self._("Decrescente"), variable=self.reverse_var,
                                         command=self._on_sort_change, onvalue=True, offvalue=False)
        reverse_check.pack(side="left", padx=5)

        # Botões de ação
        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.pack(fill="x", pady=5)
        ctk.CTkButton(action_frame, text=self._("Matar"), command=self._kill_selected_process,
                      fg_color=self.acc_color, width=80).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text=self._("Suspender"), command=self._suspend_selected_process,
                      fg_color=self.acc_color, width=80).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text=self._("Continuar"), command=self._resume_selected_process,
                      fg_color=self.acc_color, width=80).pack(side="left", padx=5)
        ctk.CTkLabel(action_frame, text=self._("Nice:"), font=("Inter",12)).pack(side="left", padx=5)
        self.nice_var = ctk.IntVar(value=0)
        nice_entry = ctk.CTkEntry(action_frame, textvariable=self.nice_var, width=50)
        nice_entry.pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text=self._("Alterar"), command=self._set_nice_selected,
                      fg_color=self.acc_color, width=60).pack(side="left", padx=5)

        # Textbox para listar processos (fonte monoespaçada)
        self.process_text = ctk.CTkTextbox(parent, font=("Courier", 10), wrap="none")
        self.process_text.pack(fill="both", expand=True, padx=10, pady=10)

        self._refresh_process_list()

    def _refresh_process_list(self):
        procs = self.proc_manager.get_process_list()
        filtro = self.filter_entry.get().lower() if hasattr(self, 'filter_entry') else ""
        if filtro:
            procs = [p for p in procs if filtro in p['name'].lower()]
        sort_key = self.sort_var.get() if hasattr(self, 'sort_var') else "cpu_percent"
        reverse = self.reverse_var.get() if hasattr(self, 'reverse_var') else True
        procs.sort(key=lambda x: x.get(sort_key, 0), reverse=reverse)

        self.process_text.configure(state="normal")
        self.process_text.delete("1.0", "end")
        # Cabeçalho
        header = f"{'PID':>7} {'CPU%':>6} {'MEM%':>6} {'STATUS':>8} {'NICE':>4} {'USUÁRIO':<10} {'NOME'}\n"
        self.process_text.insert("end", header)
        self.process_text.tag_add("header", "1.0", "1.end")
        self.process_text.tag_config("header", foreground=self.acc_color)

        for p in procs:
            linha = f"{p['pid']:7d} {p['cpu_percent']:6.1f} {p['memory_percent']:6.1f} {p['status']:>8} {p['nice']:4d} {p['username']:<10} {p['name']}\n"
            self.process_text.insert("end", linha)
        self.process_text.configure(state="disabled")
        self._current_processes = procs

    def _on_filter_change(self, event=None):
        self._refresh_process_list()

    def _on_sort_change(self, choice=None):
        self._refresh_process_list()

    def _kill_selected_process(self):
        try:
            linha = self.process_text.get("insert linestart", "insert lineend")
            pid = int(linha.split()[0])
            if self.proc_manager.kill_process(pid):
                self.show_toast(self._("Processo {pid} finalizado.").format(pid=pid))
                self._refresh_process_list()
            else:
                self.show_toast(self._("Erro ao finalizar processo {pid}.").format(pid=pid), duration=3000)
        except:
            self.show_toast(self._("Selecione um processo."), duration=2000)

    def _suspend_selected_process(self):
        try:
            linha = self.process_text.get("insert linestart", "insert lineend")
            pid = int(linha.split()[0])
            if self.proc_manager.suspend_process(pid):
                self.show_toast(self._("Processo {pid} suspenso.").format(pid=pid))
                self._refresh_process_list()
            else:
                self.show_toast(self._("Erro ao suspender processo {pid}.").format(pid=pid), duration=3000)
        except:
            self.show_toast(self._("Selecione um processo."), duration=2000)

    def _resume_selected_process(self):
        try:
            linha = self.process_text.get("insert linestart", "insert lineend")
            pid = int(linha.split()[0])
            if self.proc_manager.resume_process(pid):
                self.show_toast(self._("Processo {pid} continuado.").format(pid=pid))
                self._refresh_process_list()
            else:
                self.show_toast(self._("Erro ao continuar processo {pid}.").format(pid=pid), duration=3000)
        except:
            self.show_toast(self._("Selecione um processo."), duration=2000)

    def _set_nice_selected(self):
        try:
            linha = self.process_text.get("insert linestart", "insert lineend")
            pid = int(linha.split()[0])
            nice = self.nice_var.get()
            if self.proc_manager.set_nice(pid, nice):
                self.show_toast(self._("Nice do processo {pid} alterado para {nice}.").format(pid=pid, nice=nice))
                self._refresh_process_list()
            else:
                self.show_toast(self._("Erro ao alterar nice do processo {pid}.").format(pid=pid), duration=3000)
        except:
            self.show_toast(self._("Selecione um processo e informe um nice válido."), duration=2000)

    # ---------- ABA HISTÓRICO (COMPLETA) ----------
    def _fill_historico(self, parent):
        ctk.CTkLabel(parent, text=self._("Histórico de Desempenho"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))

        # Frame para seleção de período
        period_frame = ctk.CTkFrame(parent, fg_color="transparent")
        period_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(period_frame, text=self._("Período:"), font=("Inter",12)).pack(side="left", padx=5)
        self.period_var = ctk.StringVar(value="1h")
        period_menu = ctk.CTkOptionMenu(period_frame,
                                         values=["1h", "6h", "12h", "24h", "7d"],
                                         variable=self.period_var,
                                         command=self._update_graphs,
                                         width=80)
        period_menu.pack(side="left", padx=5)

        # Frame para gráficos
        self.graph_frame = ctk.CTkFrame(parent, fg_color=self.bg_color)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._update_graphs()

    def _update_graphs(self, choice=None):
        # Limpa o frame de gráficos
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        # Determina o período em horas
        period_map = {"1h": 1, "6h": 6, "12h": 12, "24h": 24, "7d": 168}
        hours = period_map.get(self.period_var.get(), 1)

        # Busca dados
        dados = self.metrics_db.get_last_hours(hours=hours, metrics=['timestamp', 'cpu', 'memory', 'disk_usage'])

        if not dados or len(dados) < 2:
            label = ctk.CTkLabel(self.graph_frame, text=self._("Sem dados suficientes para exibir."))
            label.pack(expand=True)
            return

        # Prepara dados
        times = [d[0] for d in dados]
        cpus = [d[1] for d in dados]
        mems = [d[2] for d in dados]
        disks = [d[3] for d in dados]

        # Cria figura com dois subplots
        fig = Figure(figsize=(8, 6), dpi=100)
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313)

        # CPU
        ax1.plot(times, cpus, label='CPU %', color='#ff6b6b', linewidth=1.5)
        ax1.set_ylabel('CPU %')
        ax1.set_ylim(0, 100)
        ax1.legend(loc='upper right')
        ax1.grid(True, linestyle='--', alpha=0.6)

        # RAM
        ax2.plot(times, mems, label='RAM %', color='#4ecdc4', linewidth=1.5)
        ax2.set_ylabel('RAM %')
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper right')
        ax2.grid(True, linestyle='--', alpha=0.6)

        # Disco
        ax3.plot(times, disks, label='Disco %', color='#ffe66d', linewidth=1.5)
        ax3.set_xlabel(self._("Tempo (segundos desde o início)"))
        ax3.set_ylabel('Disco %')
        ax3.set_ylim(0, 100)
        ax3.legend(loc='upper right')
        ax3.grid(True, linestyle='--', alpha=0.6)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---------- ABA SEGURANÇA ----------
    def _fill_seguranca(self, parent):
        ctk.CTkLabel(parent, text=self._("Segurança do Sistema"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("🛡️ Portas Abertas"), "ports", False),
            (self._("🛡️ Firewall"), "firewall", False),
            (self._("📄 Atualizações de Segurança"), "sec_updates", False),
        ]
        level = self.config.get("expert_level", 1)
        if level == 1:
            items = [item for item in items if item[1] not in ["ports", "sec_updates"]]
        ui.create_card_grid(parent, items, "sec", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "sec", self.acc_color, self.toggle_console)
        self.detail_buttons["sec"] = btn
        self.logs["sec"] = log

    # ---------- ABA AGENTE IA (COMPLETA) ----------
    def _fill_agente(self, parent):
        ctk.CTkLabel(parent, text=self._("Agente de IA"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        self.chat_frame = ChatFrame(parent, self, fg_color="transparent")
        self.chat_frame.pack(fill="both", expand=True)

    # ---------- ABA CONFIGURAÇÕES (COMPLETA) ----------
    def _fill_config(self, parent):
        ctk.CTkLabel(parent, text=self._("Configurações"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,30))

        # Usuário
        f_user = ctk.CTkFrame(parent, fg_color="transparent")
        f_user.pack(fill="x", pady=5)
        ctk.CTkLabel(f_user, text=self._("Nome de usuário:"), font=("Inter",12)).pack(anchor="w")
        self.entry_user = ctk.CTkEntry(f_user, placeholder_text=self._("Seu nome"), width=200)
        self.entry_user.pack(anchor="w", pady=2)
        self.entry_user.insert(0, self.config.get("username", ""))

        # Idioma
        f_lang = ctk.CTkFrame(parent, fg_color="transparent")
        f_lang.pack(fill="x", pady=5)
        ctk.CTkLabel(f_lang, text=self._("Idioma:"), font=("Inter",12)).pack(anchor="w")
        lang_values = list(LANGUAGES.values())
        self.lang_var = ctk.StringVar(value=LANGUAGES.get(self.config.get("language", "pt_BR"), "Português Brasileiro"))
        ctk.CTkOptionMenu(f_lang, values=lang_values, variable=self.lang_var, width=200).pack(anchor="w", pady=2)

        # Escala
        f_scale = ctk.CTkFrame(parent, fg_color="transparent")
        f_scale.pack(fill="x", pady=5)
        ctk.CTkLabel(f_scale, text=self._("Escala da interface:"), font=("Inter",12)).pack(anchor="w")
        scale_values = list(SCALES.values())
        self.scale_var = ctk.StringVar(value=SCALES.get(self.config.get("ui_scale", "auto"), "Automático"))
        ctk.CTkOptionMenu(f_scale, values=scale_values, variable=self.scale_var, width=200).pack(anchor="w", pady=2)

        # Tema
        f_theme = ctk.CTkFrame(parent, fg_color="transparent")
        f_theme.pack(fill="x", pady=5)
        ctk.CTkLabel(f_theme, text=self._("Tema:"), font=("Inter",12)).pack(anchor="w")
        theme_names = [self._("Cinza Profissional"), self._("Escuro"), self._("Claro")]
        self.theme_var = ctk.StringVar(value=theme_names[0])
        current_theme = self.config.get("theme", "grey")
        if current_theme == "grey":
            self.theme_var.set(theme_names[0])
        elif current_theme == "dark":
            self.theme_var.set(theme_names[1])
        elif current_theme == "light":
            self.theme_var.set(theme_names[2])
        ctk.CTkOptionMenu(f_theme, values=theme_names, variable=self.theme_var, width=200).pack(anchor="w", pady=2)

        # Abrir arquivo em nova guia
        f_tab = ctk.CTkFrame(parent, fg_color="transparent")
        f_tab.pack(fill="x", pady=5)
        self.tab_var = ctk.BooleanVar(value=self.config.get("open_file_in_tab", False))
        ctk.CTkCheckBox(f_tab, text=self._("Abrir arquivos em nova guia"), variable=self.tab_var,
                         onvalue=True, offvalue=False).pack(anchor="w")

        # Nível de conhecimento
        f_level = ctk.CTkFrame(parent, fg_color="transparent")
        f_level.pack(fill="x", pady=5)
        ctk.CTkLabel(f_level, text=self._("Nível de conhecimento:"), font=("Inter",12)).pack(anchor="w")
        self.level_var = ctk.IntVar(value=self.config.get("expert_level", 1))
        r1 = ctk.CTkRadioButton(f_level, text=self._("Iniciante"), variable=self.level_var, value=1, cursor="hand2")
        r1.pack(anchor="w", pady=2)
        r2 = ctk.CTkRadioButton(f_level, text=self._("Intermediário"), variable=self.level_var, value=2, cursor="hand2")
        r2.pack(anchor="w", pady=2)
        r3 = ctk.CTkRadioButton(f_level, text=self._("Avançado"), variable=self.level_var, value=3, cursor="hand2")
        r3.pack(anchor="w", pady=2)

        # Agendamento (simplificado)
        f_sched = ctk.CTkFrame(parent, fg_color="transparent")
        f_sched.pack(fill="x", pady=10)
        self.sched_enabled = ctk.BooleanVar(value=self.config.get("schedule", {}).get("enabled", False))
        ctk.CTkCheckBox(f_sched, text=self._("Habilitar agendamento automático"), variable=self.sched_enabled,
                         onvalue=True, offvalue=False).pack(anchor="w")

        # Botão aplicar
        btn_apply = ctk.CTkButton(parent, text=self._("Aplicar"), fg_color=self.acc_color,
                                   command=self.apply_config, width=150)
        btn_apply.pack(pady=20)

    def apply_config(self):
        try:
            self.config["username"] = self.entry_user.get()
            for k, v in LANGUAGES.items():
                if v == self.lang_var.get():
                    self.config["language"] = k
                    break
            for k, v in SCALES.items():
                if v == self.scale_var.get():
                    self.config["ui_scale"] = k
                    break
            theme_map = {self._("Cinza Profissional"): "grey", self._("Escuro"): "dark", self._("Claro"): "light"}
            self.config["theme"] = theme_map.get(self.theme_var.get(), "grey")
            self.config["open_file_in_tab"] = self.tab_var.get()
            self.config["expert_level"] = self.level_var.get()
            self.config["simple_mode"] = (self.level_var.get() == 1)
            if "schedule" not in self.config:
                self.config["schedule"] = {}
            self.config["schedule"]["enabled"] = self.sched_enabled.get()

            self._save_config()
            self.show_toast(self._("Configurações salvas! Reiniciando..."), duration=2000)
            self.after(2000, self._restart_app)
        except Exception as e:
            logging.error(f"Erro ao aplicar configurações: {e}")

    def _restart_app(self):
        python = sys.executable
        subprocess.Popen([python, "-m", "core.main"])
        self.quit()

    # ---------- Aba Sobre ----------
    def _fill_sobre(self, parent):
        ctk.CTkLabel(parent, text=self._("Sobre o SpeedScan"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        card = ctk.CTkFrame(parent, fg_color=self.light_bg, corner_radius=15, border_width=2, border_color=self.acc_color)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        info = f"""
{self._("⚡ SpeedScan")}

{self._("Versão")} {config.VERSION}

{self._("Desenvolvedor: Ewerton Vasconcelos")}
{self._("Tecnologias: Python, CustomTkinter, psutil")}
{self._("Repositório: github.com/ewertonvasconcelos/speedscan")}

{self._("Este software está em fase de desenvolvimento.")}

{self._("Principais funcionalidades:")}
{self._("• Dashboard com widgets personalizáveis")}
{self._("• Monitoramento de CPU, RAM, disco, GPU e temperatura")}
{self._("• Otimização: cache, swap, turbo e limpeza de navegadores")}
{self._("• Rede: ping, DNS, teste de velocidade, scanner LAN, LANCache")}
{self._("• Diagnóstico de drivers e hardware")}
{self._("• Gerenciador de processos com ações")}
{self._("• Histórico de desempenho com gráficos")}
{self._("• Verificações de segurança (portas, firewall, atualizações)")}
{self._("• IA proativa com sugestões e chat local")}
{self._("• Gerenciador de cookies seletivo")}
{self._("• Lixeira interna para arquivos deletados")}
{self._("• Agendamento automático de tarefas")}
{self._("• Níveis de expertise (Iniciante, Intermediário, Avançado)")}
{self._("• Tooltips explicativos")}
{self._("• Temas personalizáveis")}

© 2026 Ewerton Vasconcelos. {self._("Todos os direitos reservados.")}"""
        label_info = ctk.CTkLabel(card, text=info, font=("Inter",12), justify="left", text_color=self.text_color)
        label_info.pack(pady=20, padx=30, fill="both", expand=True)

    def _fill_windows_cleaner(self, parent):
        if self.SO != "Windows" or self.windows_cleaner is None:
            ctk.CTkLabel(
                parent,
                text=self._("🧹 Este módulo é exclusivo para Windows!\n\nExecute o SpeedScan em um sistema Windows para acessar estas funcionalidades."),
                font=("Inter", 20),
                text_color=self.acc_color,
                justify="center"
            ).pack(expand=True)
            return
        # Implementação real a ser adicionada

    # =========================================================================
    # Execução de comandos
    # =========================================================================
    def run_card_action(self, cmd, tag, is_dns):
        log = self.logs.get(tag)
        if not log:
            return
        log.delete("1.0", "end")
        if tag in self.detail_buttons:
            self.detail_buttons[tag].pack_forget()
        self.consoles_visible[tag] = False
        threading.Thread(target=self._execute_command, args=(cmd, log, tag, is_dns), daemon=True).start()

    def _execute_command(self, cmd, log, tag, is_dns):
        log.insert("end", self._("Comando executado: ") + str(cmd) + "\n")

    def _show_details_button(self, tag):
        btn = self.detail_buttons.get(tag)
        if btn and not btn.winfo_ismapped():
            btn.configure(fg_color=self.acc_color, text_color="white")
            btn.pack(anchor="e", padx=5)
        if btn:
            btn.configure(text=self._("Details ▾"))

    def toggle_console(self, tag):
        btn = self.detail_buttons.get(tag)
        log = self.logs.get(tag)
        if not btn or not log:
            return
        if self.consoles_visible.get(tag, False):
            log.pack_forget()
            btn.pack_forget()
            self.consoles_visible[tag] = False
        else:
            log.pack(fill="x", padx=5, before=btn)
            btn.configure(text=self._("Details ▴"))
            self.consoles_visible[tag] = True

    # =========================================================================
    # Métodos utilitários
    # =========================================================================
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

    # =========================================================================
    # Gerenciamento da janela
    # =========================================================================
    def _check_first_run(self):
        if self.config == DEFAULT_CONFIG:
            wizard = FirstRunWizard(self, self.config)
            self.wait_window(wizard)
            self.config = self._load_config()
            self.update_theme_vars()
            self._save_config()
            self.show_toast(self._("Configurações iniciais salvas! Algumas alterações podem exigir reinicialização."))

    def _restore_window_state(self):
        ws = self.config.get("window_state", DEFAULT_CONFIG["window_state"])
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
            if self.state() == 'zoomed' or self.attributes('-zoomed'):
                ws['maximized'] = True
            else:
                ws['maximized'] = False
                geom = self.geometry()
                match = re.match(r'(\d+)x(\d+)([+-]\d+)([+-]\d+)', geom)
                if match:
                    ws['width'] = int(match.group(1))
                    ws['height'] = int(match.group(2))
                    ws['x'] = int(match.group(3))
                    ws['y'] = int(match.group(4))
                else:
                    ws['width'] = self.winfo_width()
                    ws['height'] = self.winfo_height()
                    ws['x'] = self.winfo_x()
                    ws['y'] = self.winfo_y()
        except Exception as e:
            logging.error(_("Erro ao salvar estado da janela: {error}").format(error=e))
            ws = DEFAULT_CONFIG["window_state"]
        self.config['window_state'] = ws
        self._save_config()

    def _on_closing(self):
        self._save_window_state()
        self.metrics_collector.stop()
        self.proc_manager.stop_monitoring()
        self.quit()
        self.destroy()

    def _maximize_window(self):
        try:
            self.attributes('-zoomed', True)
        except:
            try:
                self.state('zoomed')
            except:
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f"{w}x{h}+0+0")
                self.update()

    # =========================================================================
    # Widgets do Dashboard
    # =========================================================================
    def widget_hostname(self, frame, tag):
        import socket
        hostname = socket.gethostname()
        label = ctk.CTkLabel(frame, text=hostname, font=("Inter", 16))
        label.pack(expand=True)

    def widget_distro(self, frame, tag):
        import platform
        text = f"{platform.system()} {platform.release()}"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_kernel(self, frame, tag):
        import platform
        text = platform.version()
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_uptime(self, frame, tag):
        import psutil
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
        import psutil
        text = f"{psutil.cpu_percent(interval=0.1)}%"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_ram(self, frame, tag):
        import psutil
        mem = psutil.virtual_memory()
        text = f"{mem.percent}% ({mem.used // (1024**3)} GB / {mem.total // (1024**3)} GB)"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_gpu(self, frame, tag):
        try:
            import subprocess
            result = subprocess.run(['lspci', '|', 'grep', '-i', 'vga'], 
                                     capture_output=True, text=True, shell=True)
            if result.stdout:
                text = result.stdout.strip().split('\n')[0][:50]
            else:
                text = self._("N/A")
        except:
            text = self._("N/A")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_disks(self, frame, tag):
        import psutil
        disks = psutil.disk_usage('/')
        text = f"{disks.percent}% ({disks.used // (1024**3)} GB / {disks.total // (1024**3)} GB)"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_battery(self, frame, tag):
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = self._("Carregando") if battery.power_plugged else self._("Descarregando")
            text = f"{percent}% ({plugged})"
        else:
            text = self._("Sem bateria")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_temps(self, frame, tag):
        import psutil
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    text = f"{entries[0].current}°C"
                    break
            else:
                text = self._("N/A")
        else:
            text = self._("N/A")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_health(self, frame, tag):
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem_percent = psutil.virtual_memory().percent
        if cpu_percent < 50 and mem_percent < 50:
            text = self._("Bom")
        elif cpu_percent < 80 and mem_percent < 80:
            text = self._("Ok")
        else:
            text = self._("Alto uso")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_realtime_chart(self, frame, tag):
        from core.dashboard import RealTimeChartWidget
        chart = RealTimeChartWidget(frame, tag)
        if not hasattr(self, '_charts'):
            self._charts = []
        self._charts.append(chart)

    # =========================================================================
    # Placeholders para métodos chamados
    # =========================================================================
    def _update_ai_suggestions(self):
        # Atualiza sugestões da IA (pode ser implementado depois)
        pass

    def _check_process_queue(self):
        pass

if __name__ == "__main__":
    app = SpeedScan()
    app.mainloop()
    print("DEBUG: Criando app...")
    app = SpeedScan()
    print("DEBUG: Entrando no mainloop...")
    app.mainloop()
    print("DEBUG: mainloop encerrado")
