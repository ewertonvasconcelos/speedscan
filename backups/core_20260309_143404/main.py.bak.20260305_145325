from core import config
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from logging.handlers import RotatingFileHandler
from pathlib import Path
import logging

# Configuração do logging
config.LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = config.LOG_DIR / "speedscan.log"
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

    def _run_scanner_action(self, log, action):
        """Executa ações de scanner de forma genérica."""
        log.delete("1.0", "end")
        log.insert("end", f"Executando {action}...\n")
        # Mapeamento de ações para métodos do security_scanner
        scanner_map = {
            'port_scan': self.app.security_scanner.scan_open_ports,
            'firewall_check': self.app.security_scanner.check_firewall_status,
            'security_updates': self.app.security_scanner.check_security_updates,
            'services_manager': self._run_services_manager_impl,
            'log_analysis': self._run_log_analysis_impl,
        }
        if action in scanner_map:
            result = scanner_map[action]()
            if isinstance(result, list):
                log.insert("end", "\n".join(result))
            else:
                log.insert("end", str(result))
        else:
            log.insert("end", f"Ação desconhecida: {action}\n")
        log.insert("end", "\n✅ Ação concluída.\n")

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
        self._run_scanner_action(log, 'port_scan')
    def run_firewall_check(self, log):
        self._run_scanner_action(log, 'firewall_check')
    def run_security_updates(self, log):
        self._run_scanner_action(log, 'security_updates')
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
            logging.error(f"Erro em _save_window_state: {e}")
            ws = config.DEFAULT_CONFIG["window_state"]
if __name__ == "__main__":
    app = SpeedScan()
    app.mainloop()
