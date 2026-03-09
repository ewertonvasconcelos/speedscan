#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from logging.handlers import RotatingFileHandler
from pathlib import Path
import logging

# Configuração do logging
LOG_DIR = Path.home() / "speedscan" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / "speedscan.log"
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logging.basicConfig(level=logging.ERROR, handlers=[handler])

import customtkinter as ctk
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

from core import config  # configurações centralizadas
from core.hardware import HardwareInfo
from core.actions import CommandRunner, ActionMapper
from core.scheduler import Scheduler
from core import ui
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
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# =============================================================================
# Classes auxiliares (ActionHandler)
# =============================================================================
class ActionHandler:
    def __init__(self, app):
        self.app = app

    def run_browser_clean(self, log, preserve_cookies=False, cookie_keep_list=None):
        log.delete("1.0", "end")
        log.insert("end", "Iniciando limpeza de navegadores...\n")
        results = self.app.browser_cleaner.clean_all_browsers(preserve_cookies, cookie_keep_list)
        total_freed = 0
        for browser, data in results.items():
            if data['cache_freed'] or data['cookies_freed'] or data['history_freed']:
                log.insert("end", f"\n{data['name']}:\n")
                if data['cache_freed']:
                    log.insert("end", f"  Cache: {self.app.browser_cleaner.format_bytes(data['cache_freed'])}\n")
                    total_freed += data['cache_freed']
                if data['cookies_freed']:
                    log.insert("end", f"  Cookies: {self.app.browser_cleaner.format_bytes(data['cookies_freed'])}\n")
                    total_freed += data['cookies_freed']
                if data['history_freed']:
                    log.insert("end", f"  Histórico: {self.app.browser_cleaner.format_bytes(data['history_freed'])}\n")
                    total_freed += data['history_freed']
                if data['errors']:
                    log.insert("end", f"  Erros: {', '.join(data['errors'])}\n")
        log.insert("end", f"\n✅ Total liberado: {self.app.browser_cleaner.format_bytes(total_freed)}\n")

    def run_speed_test(self, log):
        log.delete("1.0", "end")
        log.insert("end", "Iniciando teste de velocidade...\n")
        log.insert("end", "Isso pode levar alguns segundos.\n\n")
        def update_log(result):
            self.app.after(0, lambda: log.insert("end", "\n" + self.app.speed_tester.format_result(result) + "\n"))
            self.app.after(0, lambda: log.insert("end", "\n✅ Teste concluído.\n"))
        self.app.speed_tester.run_test(callback=update_log)

    def run_lan_scan(self, log):
        log.delete("1.0", "end")
        log.insert("end", "Iniciando scanner de rede...\n")
        log.insert("end", "Isso pode levar alguns segundos.\n\n")
        def update_progress(current, total, ip, is_alive):
            if is_alive:
                self.app.after(0, lambda: log.insert("end", f"  {ip} - ativo\n"))
        def scan_thread():
            devices = self.app.lan_scanner.scan_network(progress_callback=update_progress)
            self.app.after(0, lambda: self._display_scan_results(devices, log))
        threading.Thread(target=scan_thread, daemon=True).start()

    def _display_scan_results(self, devices, log):
        log.insert("end", "\n" + "="*50 + "\n")
        log.insert("end", "RESULTADO DO SCAN:\n")
        log.insert("end", "="*50 + "\n")
        for d in devices:
            if 'error' in d:
                log.insert("end", f"Erro: {d['error']}\n")
                continue
            log.insert("end", f"IP: {d['ip']}\n")
            log.insert("end", f"MAC: {d['mac']}\n")
            log.insert("end", f"Hostname: {d['hostname']}\n")
            log.insert("end", f"Fabricante: {d['vendor']}\n")
            log.insert("end", "-"*30 + "\n")
        log.insert("end", f"\nTotal de dispositivos ativos: {len(devices)}\n")
        log.insert("end", "✅ Scan concluído.\n")

    def run_port_scan(self, log):
        log.delete("1.0", "end")
        log.insert("end", "Escaneando portas abertas...\n")
        ports = self.app.security_scanner.scan_open_ports()
        if not ports:
            log.insert("end", "Nenhuma porta aberta encontrada.\n")
        else:
            log.insert("end", "\n".join(ports))
        log.insert("end", "\n✅ Scan concluído.\n")

    def run_firewall_check(self, log):
        log.delete("1.0", "end")
        log.insert("end", "Verificando status do firewall...\n")
        status = self.app.security_scanner.check_firewall_status()
        log.insert("end", status)
        log.insert("end", "\n✅ Verificação concluída.\n")

    def run_security_updates(self, log):
        log.delete("1.0", "end")
        log.insert("end", "Verificando atualizações de segurança...\n")
        updates = self.app.security_scanner.check_security_updates()
        log.insert("end", "\n".join(updates))
        log.insert("end", "\n✅ Verificação concluída.\n")

    def run_lan_cache_setup(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔄 Verificando Docker...\n")
        if not self.app.lan_cache.is_docker_installed():
            log.insert("end", "Docker não encontrado. Tentando instalar...\n")
            cmds = self.app.lan_cache.install_docker()
            for cmd in cmds:
                log.insert("end", f"Executando: {cmd}\n")
                proc = self.app.runner.run(cmd, use_sudo=True, parent=self.app)
                if proc:
                    for line in proc.stdout:
                        self.app.after(0, lambda l=line: log.insert("end", l))
                    proc.wait()
        else:
            log.insert("end", "✅ Docker já instalado.\n")

        log.insert("end", "\n📦 Baixando e iniciando LANCache...\n")
        cmds = self.app.lan_cache.get_install_commands()
        for cmd in cmds:
            log.insert("end", f"Executando: {cmd}\n")
            if cmd.startswith("mkdir"):
                parts = cmd.split()
                proc = self.app.runner.run(parts, use_sudo=False)
            elif cmd.startswith("wget"):
                parts = cmd.split()
                proc = self.app.runner.run(parts, use_sudo=False)
            elif "docker-compose" in cmd:
                proc = self.app.runner.run(cmd, use_sudo=True, parent=self.app)
            else:
                proc = self.app.runner.run(cmd, use_sudo=True, parent=self.app)
            if proc:
                for line in proc.stdout:
                    self.app.after(0, lambda l=line: log.insert("end", l))
                proc.wait()

        log.insert("end", "\n🔍 Status do LANCache:\n")
        status = self.app.lan_cache.get_status()
        log.insert("end", status + "\n")

        log.insert("end", "\n✅ Configuração concluída.\n")
        log.insert("end", "Agora você pode acessar http://lancache:80 para ver a interface web.\n")
        log.insert("end", "Para usar o cache, configure o DNS da sua rede para o IP deste servidor.\n")

    def run_services_manager(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔍 Analisando serviços em execução...\n\n")
        if self.app.SO == "Linux":
            log.insert("end", "Serviços ativos (systemctl):\n")
            log.insert("end", "="*40 + "\n")
            proc = self.app.runner.run(["systemctl", "list-units", "--type=service", "--state=running", "--no-pager"], use_sudo=False)
            if proc:
                for line in proc.stdout:
                    log.insert("end", line)
                proc.wait()
        elif self.app.SO == "Windows":
            log.insert("end", "Serviços do Windows (via sc query):\n")
            log.insert("end", "="*40 + "\n")
            proc = self.app.runner.run("sc query | findstr /C:\"SERVICE_NAME\" /C:\"STATE\"", use_sudo=False)
            if proc:
                for line in proc.stdout:
                    log.insert("end", line)
                proc.wait()
        elif self.app.SO == "Darwin":
            log.insert("end", "Serviços macOS (launchctl):\n")
            log.insert("end", "="*40 + "\n")
            proc = self.app.runner.run(["launchctl", "list"], use_sudo=False)
            if proc:
                for line in proc.stdout:
                    log.insert("end", line)
                proc.wait()
        else:
            log.insert("end", "Sistema não suportado para gerenciamento de serviços.\n")
        log.insert("end", "\n✅ Análise concluída.\n")

    def run_log_analysis(self, log):
        log.delete("1.0", "end")
        log.insert("end", "📋 Analisando logs do sistema (últimos erros)...\n\n")
        if self.app.SO == "Linux":
            log.insert("end", "Erros recentes (journalctl):\n")
            log.insert("end", "="*40 + "\n")
            proc = self.app.runner.run("journalctl -p 3 -b --no-pager | head -20", use_sudo=False)
            if proc:
                for line in proc.stdout:
                    log.insert("end", line)
                proc.wait()
        elif self.app.SO == "Windows":
            log.insert("end", "Erros no Log de Eventos (PowerShell):\n")
            log.insert("end", "="*40 + "\n")
            cmd = 'powershell -Command "Get-EventLog -LogName System -EntryType Error -Newest 20 | Format-Table -AutoSize"'
            proc = self.app.runner.run(cmd, use_sudo=False)
            if proc:
                for line in proc.stdout:
                    log.insert("end", line)
                proc.wait()
        elif self.app.SO == "Darwin":
            log.insert("end", "Erros recentes (log show):\n")
            log.insert("end", "="*40 + "\n")
            proc = self.app.runner.run('log show --predicate \'eventMessage contains "error"\' --last 1h | head -20', use_sudo=False)
            if proc:
                for line in proc.stdout:
                    log.insert("end", line)
                proc.wait()
        else:
            log.insert("end", "Sistema não suportado para análise de logs.\n")
        log.insert("end", "\n✅ Análise concluída.\n")

    def special_command(self, cmd, log):
        if cmd == "video_drv":
            log.insert("end", "Detectando GPU...\n")
            log.insert("end", "Funcionalidade em desenvolvimento.\n")
        elif cmd == "net_drv":
            log.insert("end", "Detectando placa de rede...\n")
            log.insert("end", "Funcionalidade em desenvolvimento.\n")
        elif cmd == "auto_update":
            log.insert("end", "Configurando atualizações automáticas...\n")
            log.insert("end", "Funcionalidade em desenvolvimento.\n")
        elif cmd == "cookies":
            self.run_cookie_manager(log)
        elif cmd == "empty_trash":
            self.app.trash_manager.empty_trash()
            log.insert("end", "🗑 Lixeira esvaziada.\n")

    def run_cookie_manager(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🍪 Gerenciador de Cookies\n")
        log.insert("end", "="*40 + "\n")
        summary = self.app.cookie_manager.get_cookie_summary()
        if not summary:
            log.insert("end", "Nenhum cookie encontrado.\n")
            return
        log.insert("end", f"Total de domínios com cookies: {len(summary)}\n")
        for domain, count in list(summary.items())[:10]:
            log.insert("end", f"{domain}: {count} cookies\n")
        if len(summary) > 10:
            log.insert("end", f"... e mais {len(summary)-10} domínios.\n")


# =============================================================================
# Classe principal SpeedScan
# =============================================================================
class SpeedScan(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.SO = platform.system()
        self.runner = CommandRunner(self.SO)
        self.hw = HardwareInfo(self.SO, self.runner)
        self.config = self._load_config()
        self.update_theme_vars()
        self.title(f"SpeedScan {config.VERSION}")
        self.configure(fg_color=self.bg_color)
        self.minsize(900, 600)

        self.apply_ui_scale()
        self.turbo_active = False
        self.consoles_visible = {}
        self.ping_active = False
        self.current_module = "dashboard"
        self.sidebar_buttons = {}
        self.detail_buttons = {}
        self.logs = {}

        self.health_monitor = HealthScore()
        self.health_score_var = ctk.StringVar(value="Calculando...")
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

    def _check_first_run(self):
        if self.config == config.DEFAULT_CONFIG:
            wizard = FirstRunWizard(self, self.config)
            self.wait_window(wizard)
            self.config = self._load_config()
            self.update_theme_vars()
            self._save_config()
            self.show_toast("Configurações iniciais salvas! Algumas alterações podem exigir reinicialização.")

    def _restore_window_state(self):
        ws = self.config.get("window_state", config.DEFAULT_CONFIG["window_state"])
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
            logging.error(f"Erro ao salvar estado da janela: {e}")
            ws = config.DEFAULT_CONFIG["window_state"]
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

    def _load_config(self):
        if config.CONFIG_FILE.exists():
            try:
                with open(config.CONFIG_FILE) as f:
                    cfg = json.load(f)
                    if 'window_state' not in cfg:
                        cfg['window_state'] = config.DEFAULT_CONFIG['window_state']
                    if 'simple_mode' not in cfg:
                        cfg['simple_mode'] = config.DEFAULT_CONFIG['simple_mode']
                    if 'expert_level' not in cfg:
                        cfg['expert_level'] = config.DEFAULT_CONFIG['expert_level']
                    if 'ai' not in cfg:
                        cfg['ai'] = config.DEFAULT_CONFIG['ai']
                    return cfg
            except:
                pass
        return config.DEFAULT_CONFIG.copy()

    def _save_config(self):
        with open(config.CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    def update_theme_vars(self):
        t = config.THEMES.get(self.config["theme"], config.THEMES["default"])
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
        ctk.set_widget_scaling(1.0 if scale == "auto" else float(scale)/100)

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

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.side_bg)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        top = ctk.CTkFrame(sidebar, fg_color="transparent")
        top.pack(pady=(30, 5))
        icon = self.round_image(str(config.ICON_PATH)) if config.ICON_PATH.exists() else None
        if icon:
            lbl_icon = ctk.CTkLabel(top, image=icon, text="", width=96, height=96)
        else:
            lbl_icon = ctk.CTkLabel(top, text="⚡", font=("Inter",48), width=96, height=96,
                                     text_color=self.acc_color)
        lbl_icon.pack()

        center = ctk.CTkFrame(sidebar, fg_color="transparent")
        center.pack(expand=False, fill="x", pady=(19, 0))

        nav_items = [
            ("📊", "Dashboard", "dashboard"),
            ("🚀", "Otimização", "otimizacao"),
            ("🌐", "Rede", "rede"),
            ("🛠", "Drivers", "drivers"),
        ]
        level_items = {
            1: [],
            2: [("📊", "Processos", "processos")],
            3: [
                ("📊", "Processos", "processos"),
                ("📈", "Histórico", "historico"),
                ("🔒", "Segurança", "seguranca"),
                ("🤖", "Agente IA", "agente"),
            ]
        }

        for icon, text, target in nav_items:
            btn = self._sidebar_btn(center, icon, text, target)
            self.sidebar_buttons[target] = btn

        level = self.config.get("expert_level", 1)
        if level >= 2:
            spacer = ctk.CTkLabel(center, text="", height=10)
            spacer.pack(expand=False)
            for icon, text, target in level_items.get(level, []):
                btn = self._sidebar_btn(center, icon, text, target)
                self.sidebar_buttons[target] = btn

        spacer = ctk.CTkLabel(center, text="", height=20)
        spacer.pack(expand=False)

        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", pady=(5, 20))
        for icon, text, target in [("⚙", "Configurações", "config"), ("ℹ", "Sobre", "sobre")]:
            btn = self._sidebar_btn(bottom, icon, text, target)
            self.sidebar_buttons[target] = btn

    def _sidebar_btn(self, parent, icon, text, target):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=5, fill="x", padx=10)
        btn = ctk.CTkButton(frame, text=f"{icon}  {text}", anchor="w", height=40,
                             fg_color="transparent", hover_color=self.acc_color,
                             font=("Inter",13), corner_radius=10,
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

    # ---------- Dashboard ----------
    def _fill_dashboard(self, parent):
        ctk.CTkLabel(parent, text="Dashboard", font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        self.dashboard = Dashboard(parent, self, fg_color="transparent")
        self.dashboard.pack(fill="both", expand=True)

    # ---------- Widgets ----------
    def widget_hostname(self, parent, widget_id):
        lbl = ctk.CTkLabel(parent, text=platform.node(), font=("Inter", 18, "bold"), text_color=self.acc_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Nome do computador na rede")

    def widget_distro(self, parent, widget_id):
        lbl = ctk.CTkLabel(parent, text=self.hw.get_distro(), font=("Inter", 18, "bold"), text_color=self.acc_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Sistema operacional e versão")

    def widget_kernel(self, parent, widget_id):
        lbl = ctk.CTkLabel(parent, text=platform.release(), font=("Inter", 18, "bold"), text_color=self.acc_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Versão do kernel")

    def widget_uptime(self, parent, widget_id):
        lbl = ctk.CTkLabel(parent, text=self.hw.get_uptime(), font=("Inter", 18, "bold"), text_color=self.acc_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Tempo desde a última inicialização")

    def widget_cpu(self, parent, widget_id):
        info = self.hw.get_cpu()
        percent = psutil.cpu_percent()
        text = f"{info}\nUso: {percent}%"
        lbl = ctk.CTkLabel(parent, text=text, font=("Inter", 14), justify="center", text_color=self.text_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Processador: modelo e uso atual")

    def widget_ram(self, parent, widget_id):
        mem = psutil.virtual_memory()
        info = self.hw.get_ram()
        text = f"{info}\nUso: {mem.percent}%"
        lbl = ctk.CTkLabel(parent, text=text, font=("Inter", 14), justify="center", text_color=self.text_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Memória RAM: usada/total e percentual")

    def widget_gpu(self, parent, widget_id):
        info = self.hw.get_gpu()
        lbl = ctk.CTkLabel(parent, text=info, font=("Inter", 14), justify="center", wraplength=250, text_color=self.text_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Placa de vídeo detectada")

    def widget_disks(self, parent, widget_id):
        info = self.hw.get_disks_detailed()
        lbl = ctk.CTkLabel(parent, text=info, font=("Inter", 12), justify="center", wraplength=250, text_color=self.text_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Discos e partições com uso percentual")

    def widget_battery(self, parent, widget_id):
        info = self.hw.get_battery()
        lbl = ctk.CTkLabel(parent, text=info, font=("Inter", 14), justify="center", text_color=self.text_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Status da bateria")

    def widget_temps(self, parent, widget_id):
        temps = self.temp_monitor.get_all_temperatures()
        text = "\n".join([f"{s}: {t}°C" for s, t in temps.items()])
        lbl = ctk.CTkLabel(parent, text=text, font=("Inter", 12), justify="center", text_color=self.text_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Temperaturas de CPU, GPU e discos")

    def widget_health(self, parent, widget_id):
        score = self.health_monitor.calculate_health_score()['score']
        lbl = ctk.CTkLabel(parent, text=f"Saúde: {score}/100", font=("Inter", 18, "bold"), text_color=self.acc_color)
        lbl.pack(expand=True)
        ui.add_tooltip(lbl, "Pontuação geral de saúde do sistema (0-100)")

    # ---------- Aba Otimização ----------
    def _fill_otimizacao(self, parent):
        ctk.CTkLabel(parent, text="Otimização", font=("Inter",28,"bold"), text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            ("🧹 Limpeza de Cache", "cache", False),
            ("🔄 Reset de Swap", "swap", False),
            ("✅ Verificar Erros", "check", False),
            ("🔥 Modo Turbo", "turbo", False),
            ("Steam", "steam", False),
            ("Lutris", "lutris", False),
            ("Heroic Launcher", "heroic", False),
            ("Bottles", "bottles", False),
            ("Wine", "wine", False),
            ("MangoHud", "mangohud", False),
            ("Goverlay", "goverlay", False),
            ("🎮 Emulador Dolphin", "dolphin", False),
            ("🧹 Limpeza de Navegadores", "browsers", False),
            ("⚙ Gerenciar Serviços", "services", False),
            ("📊 Análise de Logs", "logs", False),
            ("🍪 Gerenciar Cookies", "cookies", False),
            ("⚙ Otimizar SSD (TRIM)", "trim", False),
            ("🔧 Reparar Pacotes Quebrados", "fix_broken", False),
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

    # ---------- Aba Rede ----------
    def _fill_rede(self, parent):
        ctk.CTkLabel(parent, text="Rede", font=("Inter",28,"bold"), text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            ("📡 Ping", "ping", False),
            ("☁ Cloudflare DNS", "1.1.1.1", True),
            ("🔵 Google DNS", "8.8.8.8", True),
            ("🛡 AdGuard DNS", "94.140.14.14", True),
            ("🔄 DNS Automático", "auto", True),
            ("🌐 Testar Velocidade", "speedtest", False),
            ("🔌 Diagnóstico Placa", "ethtool", False),
            ("🔄 Renovar IP", "dhclient", False),
            ("🧭 Portas Abertas", "ports", False),
            ("📶 Traceroute", "traceroute", False),
            ("📶 Informações Wi-Fi", "wifi", False),
            ("🌍 Testar DNS", "testdns", False),
            ("🔍 Scanner LAN", "lanscan", False),
            ("🚀 LANCache", "lancache", False),
            ("🌍 Verificar IP Público", "public_ip", False),
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

    # ---------- Aba Drivers ----------
    def _fill_drivers(self, parent):
        ctk.CTkLabel(parent, text="Drivers", font=("Inter",28,"bold"), text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            ("🖥 PCI (Vídeo/Rede)", "pci", False),
            ("📦 Atualizar Sistema", "update", False),
            ("🔌 USB Conectados", "usb", False),
            ("🧩 Módulos Kernel", "modules", False),
            ("⚙ CPU Detalhada", "cpu_info", False),
            ("⚠ Erros de Firmware", "firmware", False),
            ("🎮 Drivers de Vídeo", "video_drv", False),
            ("🌐 Drivers de Rede", "net_drv", False),
            ("🔄 Atualizações Automáticas", "auto_update", False)
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

    # ---------- Aba Processos ----------
    def _fill_processos(self, parent):
        ctk.CTkLabel(parent, text="Gerenciador de Processos", font=("Inter",28,"bold"), text_color=self.acc_color).pack(anchor="center", pady=(0,20))

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(toolbar, text="Filtrar:", font=("Inter",12)).pack(side="left", padx=(0,5))
        self.filter_entry = ctk.CTkEntry(toolbar, placeholder_text="Nome do processo", width=150)
        self.filter_entry.pack(side="left", padx=(0,10))
        self.filter_entry.bind("<KeyRelease>", self._on_filter_change)

        ctk.CTkLabel(toolbar, text="Ordenar por:", font=("Inter",12)).pack(side="left", padx=(10,5))
        self.sort_var = ctk.StringVar(value="cpu_percent")
        sort_menu = ctk.CTkOptionMenu(toolbar, values=["cpu_percent", "memory_percent", "name", "pid"],
                                       variable=self.sort_var, command=self._on_sort_change, width=120,
                                       cursor="left_ptr")
        sort_menu.pack(side="left", padx=(0,10))

        self.reverse_var = ctk.BooleanVar(value=True)
        reverse_check = ctk.CTkCheckBox(toolbar, text="Decrescente", variable=self.reverse_var, command=self._on_sort_change)
        reverse_check.pack(side="left", padx=(0,10))

        refresh_btn = ctk.CTkButton(toolbar, text="🔄 Atualizar", command=self._refresh_process_list, width=100, fg_color=self.acc_color, cursor="hand2")
        refresh_btn.pack(side="right", padx=5)

        from tkinter import ttk
        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, pady=10)

        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        columns = ('pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'username', 'nice', 'create_time_str')
        self.process_tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                         yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=20)
        vsb.config(command=self.process_tree.yview)
        hsb.config(command=self.process_tree.xview)

        headings = {
            'pid': 'PID', 'name': 'Nome', 'cpu_percent': 'CPU %', 'memory_percent': 'MEM %',
            'status': 'Status', 'username': 'Usuário', 'nice': 'Nice', 'create_time_str': 'Início'
        }
        widths = {'pid':60, 'name':200, 'cpu_percent':70, 'memory_percent':70,
                  'status':80, 'username':100, 'nice':60, 'create_time_str':80}
        for col in columns:
            self.process_tree.heading(col, text=headings[col], command=lambda c=col: self._sort_by_column(c))
            self.process_tree.column(col, width=widths[col], minwidth=50, anchor='center')

        self.process_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.process_tree.bind('<Double-1>', self._on_process_double_click)

        action_frame = ctk.CTkFrame(parent, fg_color="transparent")
        action_frame.pack(fill="x", pady=10)

        kill_btn = ctk.CTkButton(action_frame, text="Finalizar processo", fg_color="#d32f2f",
                                  command=self._kill_selected_process, width=150, cursor="hand2")
        kill_btn.pack(side="left", padx=5)

        suspend_btn = ctk.CTkButton(action_frame, text="Suspender", fg_color="#f57c00",
                                     command=self._suspend_selected_process, width=100, cursor="hand2")
        suspend_btn.pack(side="left", padx=5)

        resume_btn = ctk.CTkButton(action_frame, text="Continuar", fg_color="#388e3c",
                                    command=self._resume_selected_process, width=100, cursor="hand2")
        resume_btn.pack(side="left", padx=5)

        ctk.CTkLabel(action_frame, text="Nice:", font=("Inter",12)).pack(side="left", padx=(20,5))
        self.nice_var = ctk.IntVar(value=0)
        nice_spin = ctk.CTkEntry(action_frame, textvariable=self.nice_var, width=50)
        nice_spin.pack(side="left", padx=(0,5))
        set_nice_btn = ctk.CTkButton(action_frame, text="Definir", command=self._set_nice_selected,
                                      width=70, fg_color=self.acc_color, cursor="hand2")
        set_nice_btn.pack(side="left", padx=5)

        self._refresh_process_list()

    def _on_filter_change(self, event=None):
        term = self.filter_entry.get()
        self.proc_manager.set_filter(term)

    def _on_sort_change(self, choice=None):
        key = self.sort_var.get()
        reverse = self.reverse_var.get()
        self.proc_manager.set_sort(key, reverse)

    def _sort_by_column(self, col):
        current_sort = self.proc_manager.sort_by
        if current_sort == col:
            self.proc_manager.reverse = not self.proc_manager.reverse
        else:
            self.proc_manager.sort_by = col
            self.proc_manager.reverse = True
        self.sort_var.set(col)
        self.reverse_var.set(self.proc_manager.reverse)

    def _refresh_process_list(self):
        procs = self.proc_manager.get_process_list()
        self._update_process_tree(procs)

    def _update_process_tree(self, procs):
        for row in self.process_tree.get_children():
            self.process_tree.delete(row)
        for p in procs:
            values = (
                p['pid'], p['name'],
                f"{p['cpu_percent']:.1f}",
                f"{p['memory_percent']:.1f}",
                p['status'], p['username'] or '', p['nice'],
                p.get('create_time_str', '')
            )
            self.process_tree.insert('', 'end', values=values, iid=str(p['pid']))

    def _check_process_queue(self):
        try:
            while True:
                procs = self.proc_manager.callback_queue.get_nowait()
                self._update_process_tree(procs)
        except:
            pass
        self.after(500, self._check_process_queue)

    def _kill_selected_process(self):
        selected = self.process_tree.selection()
        if not selected: return
        pid = int(selected[0])
        if self.proc_manager.kill_process(pid):
            self._refresh_process_list()
            self.show_toast(f"Processo {pid} finalizado.")
        else:
            self.show_toast(f"Erro ao finalizar processo {pid}.", duration=3000)

    def _suspend_selected_process(self):
        selected = self.process_tree.selection()
        if not selected: return
        pid = int(selected[0])
        if self.proc_manager.suspend_process(pid):
            self._refresh_process_list()
            self.show_toast(f"Processo {pid} suspenso.")
        else:
            self.show_toast(f"Erro ao suspender processo {pid}.", duration=3000)

    def _resume_selected_process(self):
        selected = self.process_tree.selection()
        if not selected: return
        pid = int(selected[0])
        if self.proc_manager.resume_process(pid):
            self._refresh_process_list()
            self.show_toast(f"Processo {pid} continuado.")
        else:
            self.show_toast(f"Erro ao continuar processo {pid}.", duration=3000)

    def _set_nice_selected(self):
        selected = self.process_tree.selection()
        if not selected: return
        pid = int(selected[0])
        nice_val = self.nice_var.get()
        if self.proc_manager.set_nice(pid, nice_val):
            self._refresh_process_list()
            self.show_toast(f"Nice do processo {pid} alterado para {nice_val}.")
        else:
            self.show_toast(f"Erro ao alterar nice do processo {pid}.", duration=3000)

    def _on_process_double_click(self, event):
        selected = self.process_tree.selection()
        if not selected: return
        pid = int(selected[0])
        self.show_toast(f"Detalhes do PID {pid} em breve.", duration=2000)

    # ---------- Aba Histórico ----------
    def _fill_historico(self, parent):
        ctk.CTkLabel(parent, text="Histórico de Desempenho", font=("Inter",28,"bold"), text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        control_frame = ctk.CTkFrame(parent, fg_color="transparent")
        control_frame.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(control_frame, text="Período:", font=("Inter",12)).pack(side="left", padx=(0,5))
        self.period_var = ctk.StringVar(value="1h")
        period_menu = ctk.CTkOptionMenu(control_frame, values=["1h", "6h", "24h", "7d"],
                                        variable=self.period_var, command=self._on_period_change, width=100,
                                        cursor="left_ptr")
        period_menu.pack(side="left", padx=(0,10))

        ctk.CTkLabel(control_frame, text="Métrica:", font=("Inter",12)).pack(side="left", padx=(10,5))
        self.metric_var = ctk.StringVar(value="cpu")
        metric_menu = ctk.CTkOptionMenu(control_frame, values=["cpu", "memory", "disk"],
                                        variable=self.metric_var, command=self._on_metric_change, width=100,
                                        cursor="left_ptr")
        metric_menu.pack(side="left", padx=(0,10))

        refresh_btn = ctk.CTkButton(control_frame, text="🔄 Atualizar", command=self._update_graphs, width=100, fg_color=self.acc_color, cursor="hand2")
        refresh_btn.pack(side="right", padx=5)

        self.graph_frame = ctk.CTkFrame(parent, fg_color=self.bg_color, corner_radius=10)
        self.graph_frame.pack(fill="both", expand=True, pady=10)

        self.figure = Figure(figsize=(8, 4), dpi=100, facecolor=self.bg_color)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(self.light_bg)
        self.ax.tick_params(colors=self.text_color)
        self.ax.xaxis.label.set_color(self.text_color)
        self.ax.yaxis.label.set_color(self.text_color)
        self.ax.title.set_color(self.acc_color)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=10)

        self.stats_labels = {}
        for label in ["Média", "Mínimo", "Máximo"]:
            f = ctk.CTkFrame(self.stats_frame, fg_color=self.bg_color, corner_radius=5)
            f.pack(side="left", expand=True, fill="x", padx=5)
            ctk.CTkLabel(f, text=label, font=("Inter",10,"bold"), text_color=self.acc_color).pack()
            lbl = ctk.CTkLabel(f, text="-", font=("Inter",12), text_color=self.text_color)
            lbl.pack()
            self.stats_labels[label.lower()] = lbl

    def _on_period_change(self, choice):
        self._update_graphs()

    def _on_metric_change(self, choice):
        self._update_graphs()

    def _update_graphs(self):
        period_map = {"1h": 1, "6h": 6, "24h": 24, "7d": 168}
        hours = period_map.get(self.period_var.get(), 1)
        metric = self.metric_var.get()
        rows = self.metrics_db.get_last_hours(hours=hours, metrics=['timestamp', metric])
        if not rows:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "Sem dados suficientes", ha='center', va='center',
                         transform=self.ax.transAxes, color=self.text_color)
            self.canvas.draw()
            return
        timestamps = [time.strftime('%H:%M', time.localtime(r[0])) for r in rows]
        values = [r[1] for r in rows]
        self.ax.clear()
        self.ax.plot(timestamps, values, marker='o', linestyle='-', color=self.acc_color, markersize=3)
        self.ax.set_title(f"{metric.upper()} (%) - Últimas {hours} horas", color=self.acc_color)
        self.ax.set_xlabel("Tempo", color=self.text_color)
        self.ax.set_ylabel("%", color=self.text_color)
        self.ax.tick_params(colors=self.text_color)
        self.ax.set_facecolor(self.light_bg)
        self.figure.tight_layout()
        self.canvas.draw()
        stats = self.metrics_db.get_stats(period_hours=hours)
        if metric == 'cpu':
            self.stats_labels['média'].configure(text=f"{stats['cpu_avg']:.1f}%")
            self.stats_labels['mínimo'].configure(text=f"{stats['cpu_min']:.1f}%")
            self.stats_labels['máximo'].configure(text=f"{stats['cpu_max']:.1f}%")
        elif metric == 'memory':
            self.stats_labels['média'].configure(text=f"{stats['mem_avg']:.1f}%")
            self.stats_labels['mínimo'].configure(text=f"{stats['mem_min']:.1f}%")
            self.stats_labels['máximo'].configure(text=f"{stats['mem_max']:.1f}%")
        else:
            self.stats_labels['média'].configure(text=f"{stats['disk_avg']:.1f}%")
            self.stats_labels['mínimo'].configure(text=f"{stats['disk_min']:.1f}%")
            self.stats_labels['máximo'].configure(text=f"{stats['disk_max']:.1f}%")

    # ---------- Aba Segurança ----------
    def _fill_seguranca(self, parent):
        ctk.CTkLabel(parent, text="Segurança do Sistema", font=("Inter",28,"bold"), text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            ("🔍 Portas Abertas", "ports", False),
            ("🛡 Firewall", "firewall", False),
            ("🔎 Atualizações de Segurança", "sec_updates", False)
        ]
        level = self.config.get("expert_level", 1)
        if level == 1:
            items = [item for item in items if item[1] not in ["ports", "sec_updates"]]
        ui.create_card_grid(parent, items, "sec", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "sec", self.acc_color, self.toggle_console)
        self.detail_buttons["sec"] = btn
        self.logs["sec"] = log

    # ---------- Aba Agente IA ----------
    def _fill_agente(self, parent):
        ctk.CTkLabel(parent, text="Agente de IA", font=("Inter",28,"bold"), text_color=self.acc_color).pack(anchor="center", pady=(0,20))

        main_frame = ctk.CTkFrame(parent, fg_color=self.bg_color, corner_radius=10,
                                   border_width=1, border_color=self.acc_color)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tabview = ctk.CTkTabview(main_frame, fg_color=self.light_bg)
        tabview.pack(fill="both", expand=True, padx=5, pady=5)

        tab_sugestoes = tabview.add("Sugestões")
        tab_chat = tabview.add("Chat")

        self.ai_sugestoes_text = ctk.CTkTextbox(tab_sugestoes, height=200, fg_color=self.light_bg,
                                                 text_color=self.text_color, font=("Consolas",11), wrap="word")
        self.ai_sugestoes_text.pack(fill="both", expand=True, padx=10, pady=10)
        btn_atualizar = ctk.CTkButton(tab_sugestoes, text="🔄 Analisar Agora", fg_color=self.acc_color,
                                       command=self._update_ai_suggestions, cursor="hand2")
        btn_atualizar.pack(pady=10)

        self.chat_frame = ChatFrame(tab_chat, self, fg_color="transparent")
        self.chat_frame.pack(fill="both", expand=True)

        config_btn, config_panel = self._create_config_panel(parent)
        self.detail_buttons["ai_config"] = config_btn
        self.logs["ai_config"] = config_panel

        self._update_ai_suggestions()

    def _create_config_panel(self, parent):
        btn = ctk.CTkButton(parent, text="⚙ Configurar IA ⌄", fg_color=self.acc_color,
                            command=lambda: self.toggle_config_panel(), cursor="hand2")
        btn.pack(anchor="e", padx=10, pady=5)

        panel = ctk.CTkFrame(parent, fg_color=self.light_bg, corner_radius=10)
        panel.pack_forget()

        inner_frame = ctk.CTkFrame(panel, fg_color="transparent")
        inner_frame.pack(fill="both", expand=True, padx=10, pady=10)

        provider_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        provider_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(provider_frame, text="Provedor:", font=("Inter",12), text_color=self.text_color).pack(side="left", padx=5)
        self.ai_provider_var = ctk.StringVar(value=self.config.get("ai", {}).get("provider", "ollama"))
        provider_menu = ctk.CTkOptionMenu(provider_frame, values=["ollama", "openai", "deepseek"],
                                          variable=self.ai_provider_var, width=150, cursor="left_ptr")
        provider_menu.pack(side="left", padx=5)

        model_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        model_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(model_frame, text="Modelo:", font=("Inter",12), text_color=self.text_color).pack(side="left", padx=5)
        self.ai_model_var = ctk.StringVar(value=self.config.get("ai", {}).get("model", "llama3.2"))
        model_entry = ctk.CTkEntry(model_frame, textvariable=self.ai_model_var, width=200)
        model_entry.pack(side="left", padx=5)

        endpoint_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        endpoint_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(endpoint_frame, text="Endpoint:", font=("Inter",12), text_color=self.text_color).pack(side="left", padx=5)
        self.ai_endpoint_var = ctk.StringVar(value=self.config.get("ai", {}).get("endpoint", "http://localhost:11434"))
        endpoint_entry = ctk.CTkEntry(endpoint_frame, textvariable=self.ai_endpoint_var, width=250)
        endpoint_entry.pack(side="left", padx=5)

        key_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        key_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(key_frame, text="API Key:", font=("Inter",12), text_color=self.text_color).pack(side="left", padx=5)
        self.ai_key_var = ctk.StringVar(value=self.config.get("ai", {}).get("api_key", ""))
        key_entry = ctk.CTkEntry(key_frame, textvariable=self.ai_key_var, width=250, show="*")
        key_entry.pack(side="left", padx=5)

        save_btn = ctk.CTkButton(inner_frame, text="Salvar configurações", fg_color=self.acc_color,
                                  command=self._save_ai_config, width=200, cursor="hand2")
        save_btn.pack(pady=10)

        return btn, panel

    def toggle_config_panel(self):
        panel = self.logs.get("ai_config")
        btn = self.detail_buttons.get("ai_config")
        if not panel or not btn:
            return
        if self.consoles_visible.get("ai_config", False):
            panel.pack_forget()
            btn.configure(text="⚙ Configurar IA ⌄")
            self.consoles_visible["ai_config"] = False
        else:
            panel.pack(fill="x", padx=10, pady=5, after=btn)
            btn.configure(text="⚙ Configurar IA ⌃")
            self.consoles_visible["ai_config"] = True

    def _save_ai_config(self):
        self.config["ai"] = {
            "provider": self.ai_provider_var.get(),
            "model": self.ai_model_var.get(),
            "endpoint": self.ai_endpoint_var.get(),
            "api_key": self.ai_key_var.get()
        }
        self._save_config()
        self.show_toast("Configurações de IA salvas!")
        if hasattr(self, 'chat_frame'):
            self.chat_frame.current_ai = self.config["ai"]["provider"]
            self.chat_frame.ai_model = self.config["ai"]["model"]
            self.chat_frame.endpoint = self.config["ai"]["endpoint"]
            self.chat_frame.api_key = self.config["ai"]["api_key"]

    def _update_ai_suggestions(self):
        sugestoes = self.ai_proactive.get_summary()
        self.ai_sugestoes_text.delete("1.0", "end")
        self.ai_sugestoes_text.insert("1.0", sugestoes)

    # ---------- Execução de comandos ----------
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
        if is_dns:
            mapper = ActionMapper(self.SO, self.runner, self.turbo_active)
            real_cmd = mapper.dns_command(cmd)
        else:
            if cmd == "speedtest":
                self.action_handler.run_speed_test(log)
                self._show_details_button(tag)
                return
            elif cmd == "browsers":
                self.action_handler.run_browser_clean(log)
                self._show_details_button(tag)
                return
            elif cmd == "lanscan":
                self.action_handler.run_lan_scan(log)
                self._show_details_button(tag)
                return
            elif cmd == "ports":
                self.action_handler.run_port_scan(log)
                self._show_details_button(tag)
                return
            elif cmd == "firewall":
                self.action_handler.run_firewall_check(log)
                self._show_details_button(tag)
                return
            elif cmd == "sec_updates":
                self.action_handler.run_security_updates(log)
                self._show_details_button(tag)
                return
            elif cmd == "lancache":
                self.action_handler.run_lan_cache_setup(log)
                self._show_details_button(tag)
                return
            elif cmd == "services":
                self.action_handler.run_services_manager(log)
                self._show_details_button(tag)
                return
            elif cmd == "logs":
                self.action_handler.run_log_analysis(log)
                self._show_details_button(tag)
                return
            elif cmd in ["video_drv", "net_drv", "auto_update", "cookies", "empty_trash"]:
                self.action_handler.special_command(cmd, log)
                self._show_details_button(tag)
                return
            mapper = ActionMapper(self.SO, self.runner, self.turbo_active)
            real_cmd = mapper.get_command(cmd)
            if real_cmd is None:
                self.after(0, lambda: log.insert("end", f"Comando {cmd} não suportado neste SO.\n"))
                self.after(0, lambda: self._show_details_button(tag))
                return
        use_sudo = False
        if real_cmd and real_cmd.startswith("sudo "):
            use_sudo = True
            real_cmd = real_cmd[5:]
        proc = self.runner.run(real_cmd, use_sudo=use_sudo, parent=self)
        if proc:
            for line in proc.stdout:
                self.after(0, lambda l=line: log.insert("end", l))
            proc.wait()
            self.after(0, lambda: log.insert("end", "\n-- COMANDO FINALIZADO --\n"))
        else:
            self.after(0, lambda: log.insert("end", "Erro ao executar comando.\n"))
        self.after(0, lambda: self._show_details_button(tag))

    def _show_details_button(self, tag):
        btn = self.detail_buttons.get(tag)
        if btn and not btn.winfo_ismapped():
            btn.configure(fg_color=self.acc_color, text_color="white")
            btn.pack(anchor="e", pady=5)
        if btn:
            btn.configure(text="Detalhes ⌄")

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
            log.pack(fill="x", pady=5, before=btn)
            btn.configure(text="Detalhes ⌃")
            self.consoles_visible[tag] = True

    def toggle_ping(self):
        if not self.ping_active:
            self.ping_active = True
            threading.Thread(target=self._ping_loop, daemon=True).start()
        else:
            self.ping_active = False

    def _ping_loop(self):
        param = "-n" if self.SO == "Windows" else "-c"
        while self.ping_active:
            try:
                p = subprocess.run(["ping", param, "1", "-W", "1", "8.8.8.8"],
                                    capture_output=True, text=True, timeout=2)
                match = re.search(r'time[=<](\d+\.?\d*)', p.stdout, re.I) or re.search(r'(\d+\.?\d*) ?ms', p.stdout)
                res = match.group(1) if match else "Erro"
                self.after(0, lambda r=res: self.ping_label.configure(text=f"{r} ms"))
            except:
                self.after(0, lambda: self.ping_label.configure(text="-- ms"))
            time.sleep(2)

    def _monitor_loop(self):
        while True:
            if self.current_module == "dashboard" and hasattr(self, 'dashboard'):
                pass
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

    # ---------- Configurações ----------
    def _fill_config(self, parent):
        ctk.CTkLabel(parent, text="Configurações", font=("Inter",28,"bold"), text_color=self.acc_color).pack(anchor="center", pady=(0,30))
        f_user = ctk.CTkFrame(parent, fg_color="transparent")
        f_user.pack(fill="x", pady=10)
        ctk.CTkLabel(f_user, text="Nome de usuário", font=("Inter",14), text_color=self.text_color).pack(anchor="w")
        self.entry_user = ctk.CTkEntry(f_user, placeholder_text="Seu nome", width=300)
        self.entry_user.pack(anchor="w", pady=5)
        ctk.CTkButton(f_user, text="Voltar para o padrão", fg_color="transparent",
                      text_color=self.acc_color,
                      command=lambda: self.entry_user.delete(0,"end") or self.entry_user.insert(0,"ewerton"),
                      cursor="hand2")
        f_user.pack(anchor="w")

        f_lang = ctk.CTkFrame(parent, fg_color="transparent")
        f_lang.pack(fill="x", pady=10)
        ctk.CTkLabel(f_lang, text="Idioma de Interface", font=("Inter",14), text_color=self.text_color).pack(anchor="w")
        self.lang_var = ctk.StringVar(value=config.LANGUAGES.get(self.config.get("language","pt_BR"), "Português Brasileiro"))
        ctk.CTkOptionMenu(f_lang, values=list(config.LANGUAGES.values()), variable=self.lang_var, width=300, cursor="left_ptr").pack(anchor="w")

        f_scale = ctk.CTkFrame(parent, fg_color="transparent")
        f_scale.pack(fill="x", pady=10)
        ctk.CTkLabel(f_scale, text="Escala da interface *", font=("Inter",14), text_color=self.text_color).pack(anchor="w")
        self.scale_var = ctk.StringVar(value=config.SCALES.get(self.config.get("ui_scale","auto"), "Automático"))
        ctk.CTkOptionMenu(f_scale, values=list(config.SCALES.values()), variable=self.scale_var, width=300, cursor="left_ptr").pack(anchor="w")

        f_theme = ctk.CTkFrame(parent, fg_color="transparent")
        f_theme.pack(fill="x", pady=10)
        ctk.CTkLabel(f_theme, text="Tema da interface", font=("Inter",14), text_color=self.text_color).pack(anchor="w")
        theme_names = ["Padrão (Roxo)", "Cinza Profissional", "Escuro Total", "Claro Clean"]
        theme_keys = ["default", "grey", "dark", "light"]
        current = theme_keys.index(self.config.get("theme","default"))
        self.theme_name_var = ctk.StringVar(value=theme_names[current])
        ctk.CTkOptionMenu(f_theme, values=theme_names, variable=self.theme_name_var, width=300, cursor="left_ptr").pack(anchor="w")

        f_tab = ctk.CTkFrame(parent, fg_color="transparent")
        f_tab.pack(fill="x", pady=10)
        ctk.CTkLabel(f_tab, text="Abrir arquivo", font=("Inter",14), text_color=self.text_color).pack(anchor="w")
        self.tab_var = ctk.StringVar(value="Na guia" if self.config.get("open_file_in_tab") else "Nova janela")
        ctk.CTkOptionMenu(f_tab, values=["Na guia", "Nova janela"], variable=self.tab_var, width=300, cursor="left_ptr").pack(anchor="w")

        f_level = ctk.CTkFrame(parent, fg_color="transparent")
        f_level.pack(fill="x", pady=10)
        ctk.CTkLabel(f_level, text="Nível de conhecimento", font=("Inter",14), text_color=self.text_color).pack(anchor="w")
        self.level_var = ctk.IntVar(value=self.config.get("expert_level", 1))
        iniciante_radio = ctk.CTkRadioButton(f_level, text="Iniciante (apenas funções básicas)", variable=self.level_var, value=1, cursor="hand2")
        iniciante_radio.pack(anchor="w", pady=2)
        intermediario_radio = ctk.CTkRadioButton(f_level, text="Intermediário (funções básicas + algumas avançadas)", variable=self.level_var, value=2, cursor="hand2")
        intermediario_radio.pack(anchor="w", pady=2)
        avancado_radio = ctk.CTkRadioButton(f_level, text="Avançado (todas as funções)", variable=self.level_var, value=3, cursor="hand2")
        avancado_radio.pack(anchor="w", pady=2)

        separator = ctk.CTkFrame(parent, height=2, fg_color=self.acc_color)
        separator.pack(fill="x", pady=20)

        ctk.CTkLabel(parent, text="Agendamento Automático", font=("Inter",20,"bold"), text_color=self.acc_color).pack(anchor="w", pady=(0,10))

        self.schedule_enabled_var = ctk.BooleanVar(value=self.config.get("schedule", {}).get("enabled", False))
        schedule_check = ctk.CTkCheckBox(parent, text="Executar tarefas de otimização automaticamente",
                                          variable=self.schedule_enabled_var, onvalue=True, offvalue=False,
                                          command=self.toggle_schedule_options, cursor="hand2")
        schedule_check.pack(anchor="w", pady=5)

        self.schedule_options_frame = ctk.CTkFrame(parent, fg_color="transparent")

        freq_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        freq_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(freq_frame, text="Frequência:", font=("Inter",13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_freq_var = ctk.StringVar(value=self.config.get("schedule", {}).get("frequency", "weekly"))
        freq_menu = ctk.CTkOptionMenu(freq_frame, values=["Diário", "Semanal", "Mensal", "Personalizado"],
                                      variable=self.schedule_freq_var,
                                      command=self.update_schedule_visibility, width=150, cursor="left_ptr")
        freq_menu.pack(side="left", padx=5)

        time_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        time_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(time_frame, text="Horário (HH:MM):", font=("Inter",13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_hour_var = ctk.StringVar(value=self.config.get("schedule", {}).get("hour", "03:00"))
        hour_entry = ctk.CTkEntry(time_frame, textvariable=self.schedule_hour_var, placeholder_text="03:00", width=100)
        hour_entry.pack(side="left", padx=5)

        self.weekday_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        self.weekday_frame.pack_forget()
        ctk.CTkLabel(self.weekday_frame, text="Dia da semana:", font=("Inter",13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_weekday_var = ctk.StringVar(value=self.config.get("schedule", {}).get("day_of_week", "monday"))
        weekday_menu = ctk.CTkOptionMenu(self.weekday_frame,
                                         values=["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"],
                                         variable=self.schedule_weekday_var, width=150, cursor="left_ptr")
        weekday_menu.pack(side="left", padx=5)

        self.monthday_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        self.monthday_frame.pack_forget()
        ctk.CTkLabel(self.monthday_frame, text="Dia do mês:", font=("Inter",13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_monthday_var = ctk.IntVar(value=self.config.get("schedule", {}).get("day_of_month", 1))
        monthday_entry = ctk.CTkEntry(self.monthday_frame, textvariable=self.schedule_monthday_var, placeholder_text="1", width=50)
        monthday_entry.pack(side="left", padx=5)

        self.custom_interval_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        self.custom_interval_frame.pack_forget()
        ctk.CTkLabel(self.custom_interval_frame, text="Intervalo (dias):", font=("Inter",13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_interval_var = ctk.IntVar(value=self.config.get("schedule", {}).get("interval_days", 7))
        interval_entry = ctk.CTkEntry(self.custom_interval_frame, textvariable=self.schedule_interval_var, placeholder_text="7", width=50)
        interval_entry.pack(side="left", padx=5)

        tasks_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        tasks_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(tasks_frame, text="Tarefas a executar:", font=("Inter",13,"bold"), text_color=self.acc_color).pack(anchor="w", pady=5)

        self.schedule_tasks = {}
        task_list = [
            ("cache", "🧹 Limpeza de Cache"),
            ("swap", "🔄 Reset de Swap"),
            ("check", "✅ Verificar Erros"),
            ("update", "📦 Atualizar Sistema (requer privilégios)"),
            ("turbo", "🔥 Modo Turbo (temporário)")
        ]
        saved_tasks = self.config.get("schedule", {}).get("tasks", ["cache", "swap", "check"])
        for task_key, task_label in task_list:
            var = ctk.BooleanVar(value=task_key in saved_tasks)
            cb = ctk.CTkCheckBox(tasks_frame, text=task_label, variable=var, onvalue=True, offvalue=False, cursor="hand2")
            cb.pack(anchor="w", padx=20, pady=2)
            self.schedule_tasks[task_key] = var

        self.schedule_elevated_var = ctk.BooleanVar(value=self.config.get("schedule", {}).get("elevated", False))
        elevated_check = ctk.CTkCheckBox(self.schedule_options_frame, text="Executar com privilégios de administrador (quando necessário)",
                                          variable=self.schedule_elevated_var, onvalue=True, offvalue=False, cursor="hand2")
        elevated_check.pack(anchor="w", pady=5)

        log_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        log_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(log_frame, text=f"Logs salvos em: {LOG_DIR}", font=("Inter",11), text_color=self.text_color).pack(side="left", padx=5)
        btn_open_logs = ctk.CTkButton(log_frame, text="Abrir pasta", command=self.open_logs_folder, width=100, height=25, cursor="hand2")
        btn_open_logs.pack(side="left", padx=5)

        btn_save_schedule = ctk.CTkButton(self.schedule_options_frame, text="Salvar configurações de agendamento",
                                          fg_color=self.acc_color, command=self.save_schedule_config, width=300, height=40, cursor="hand2")
        btn_save_schedule.pack(pady=15)

        self.toggle_schedule_options()
        self.update_schedule_visibility(self.schedule_freq_var.get())
        self.schedule_options_frame.pack(fill="x", pady=10)

        separator2 = ctk.CTkFrame(parent, height=2, fg_color=self.acc_color)
        separator2.pack(fill="x", pady=20)

        ctk.CTkLabel(parent, text="* - As alterações de escala e tema serão aplicadas após reiniciar o aplicativo",
                     font=("Inter",10), text_color="#888888").pack(anchor="w", pady=20)

        btn_apply = ctk.CTkButton(parent, text="Aplicar", fg_color=self.acc_color, command=self.apply_config,
                                  width=200, height=40, cursor="hand2")
        btn_apply.pack(pady=20)

    def toggle_schedule_options(self):
        if self.schedule_enabled_var.get():
            for child in self.schedule_options_frame.winfo_children():
                self._enable_widget(child)
        else:
            for child in self.schedule_options_frame.winfo_children():
                self._disable_widget(child)

    def _enable_widget(self, widget):
        if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
            for child in widget.winfo_children():
                self._enable_widget(child)
        else:
            try:
                widget.configure(state="normal")
            except:
                pass

    def _disable_widget(self, widget):
        if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
            for child in widget.winfo_children():
                self._disable_widget(child)
        else:
            try:
                widget.configure(state="disabled")
            except:
                pass

    def update_schedule_visibility(self, choice):
        self.weekday_frame.pack_forget()
        self.monthday_frame.pack_forget()
        self.custom_interval_frame.pack_forget()
        if choice == "Semanal":
            self.weekday_frame.pack(fill="x", pady=5)
        elif choice == "Mensal":
            self.monthday_frame.pack(fill="x", pady=5)
        elif choice == "Personalizado":
            self.custom_interval_frame.pack(fill="x", pady=5)

    def open_logs_folder(self):
        try:
            if self.SO == "Windows":
                os.startfile(LOG_DIR)
            elif self.SO == "Darwin":
                subprocess.run(["open", LOG_DIR])
            else:
                subprocess.run(["xdg-open", LOG_DIR])
        except Exception as e:
            logging.error(f"Erro ao abrir pasta de logs: {e}")

    def save_schedule_config(self):
        # Mapeamento de valores em português para inglês
        freq_map = {
            "Diário": "daily",
            "Semanal": "weekly",
            "Mensal": "monthly",
            "Personalizado": "custom"
        }
        day_map = {
            "segunda": "monday",
            "terça": "tuesday",
            "quarta": "wednesday",
            "quinta": "thursday",
            "sexta": "friday",
            "sábado": "saturday",
            "domingo": "sunday"
        }

        schedule = {
            "enabled": self.schedule_enabled_var.get(),
            "frequency": freq_map[self.schedule_freq_var.get()],
            "hour": self.schedule_hour_var.get(),
            "day_of_week": day_map[self.schedule_weekday_var.get()],
            "day_of_month": self.schedule_monthday_var.get(),
            "interval_days": self.schedule_interval_var.get(),
            "tasks": [key for key, var in self.schedule_tasks.items() if var.get()],
            "elevated": self.schedule_elevated_var.get()
        }
        self.config["schedule"] = schedule
        self._save_config()
        scheduler = Scheduler(self.SO, LOG_DIR, config.AGENT_SCRIPT)
        scheduler.create_schedule(schedule)
        self.show_toast("Configurações salvas!")

    def show_toast(self, message, duration=3000):
        toast = ctk.CTkLabel(self, text=message,
                             fg_color=self.acc_color,
                             text_color="white",
                             corner_radius=10,
                             font=("Inter",12),
                             padx=20, pady=10)
        toast.place(relx=0.5, rely=0.5, anchor="center")
        self.after(duration, toast.destroy)

    def apply_config(self):
        self.config["username"] = self.entry_user.get()
        for k,v in config.LANGUAGES.items():
            if v == self.lang_var.get():
                self.config["language"] = k; break
        for k,v in config.SCALES.items():
            if v == self.scale_var.get():
                self.config["ui_scale"] = k; break
        theme_names = ["Padrão (Roxo)", "Cinza Profissional", "Escuro Total", "Claro Clean"]
        theme_keys = ["default", "grey", "dark", "light"]
        self.config["theme"] = theme_keys[theme_names.index(self.theme_name_var.get())]
        self.config["open_file_in_tab"] = (self.tab_var.get() == "Na guia")
        self.config["expert_level"] = self.level_var.get()
        self.config["simple_mode"] = (self.level_var.get() == 1)
        self._save_config()

        restart_script = Path.home() / "speedscan" / "restart_speedscan.sh"
        subprocess.Popen([str(restart_script), str(os.getpid())], start_new_session=True)
        self.quit()

    # ---------- Aba Sobre ----------
    def _fill_sobre(self, parent):
        ctk.CTkLabel(parent, text="Sobre o SpeedScan", font=("Inter",28,"bold"), text_color=self.acc_color).pack(anchor="center", pady=(0,20))

        card = ctk.CTkFrame(parent, fg_color=self.light_bg, corner_radius=15,
                             border_width=2, border_color=self.acc_color)
        card.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(card, text="⚡ SpeedScan", font=("Inter",36,"bold"), text_color=self.acc_color).pack(pady=(40,10))
        ctk.CTkLabel(card, text=f"Versão {config.VERSION}", font=("Inter",14), text_color="#888888").pack()

        info = (
            "Desenvolvedor: Ewerton Vasconcelos\n"
            "Tecnologias: Python, CustomTkinter, psutil\n"
            "Repositório: github.com/ewertonvasconcelos/speedscan\n\n"
            "Este software está em fase de desenvolvimento.\n\n"
            "Principais funcionalidades:\n"
            "• Dashboard com widgets personalizáveis\n"
            "• Monitoramento de CPU, RAM, disco, GPU e temperatura\n"
            "• Otimização: cache, swap, turbo e limpeza de navegadores\n"
            "• Rede: ping, DNS, teste de velocidade, scanner LAN, LANCache\n"
            "• Diagnóstico de drivers e hardware\n"
            "• Gerenciamento de processos\n"
            "• Histórico de desempenho com gráficos\n"
            "• Verificações de segurança (portas, firewall, atualizações)\n"
            "• IA proativa com sugestões inteligentes\n"
            "• Chat com IA local (Ollama) e suporte a outras APIs\n"
            "• Gerenciador de cookies seletivo\n"
            "• Lixeira interna para arquivos deletados\n"
            "• Agendamento automático de tarefas\n"
            "• Níveis de expertise (Iniciante, Intermediário, Avançado)\n"
            "• Tooltips explicativos\n"
            "• Temas personalizáveis\n\n"
            "© 2026 Ewerton Vasconcelos. Todos os direitos reservados."
        )
        label_info = ctk.CTkLabel(card, text=info, font=("Inter",12), justify="left", text_color=self.text_color)
        label_info.pack(pady=20, padx=30, fill="both", expand=True)


if __name__ == "__main__":
    app = SpeedScan()
    app.mainloop()
