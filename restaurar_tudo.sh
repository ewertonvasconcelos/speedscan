#!/bin/bash
# Script de restauração completa do SpeedScan - Versão Final
# Deve ser executado no diretório ~/speedscan/speedscan

set -e  # para em caso de erro

echo "=== RESTAURAÇÃO COMPLETA DO SPEEDSCAN ==="
echo "Criando backups dos arquivos atuais..."

mkdir -p backups_$(date +%Y%m%d_%H%M%S)
cp core/*.py backups_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true

echo "Backups salvos. Restaurando arquivos..."

# ============================================================================
# core/__init__.py (vazio)
# ============================================================================
cat > core/__init__.py << 'INIT'
# Pacote core
INIT

# ============================================================================
# core/config.py (temas corrigidos)
# ============================================================================
cat > core/config.py << 'CONFIG'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Central configuration file for SpeedScan.
Automatically generated - do not edit manually.
"""

import os
from pathlib import Path

# ============================================================================
# Application version
# ============================================================================
VERSION = "1.0.0"

# ============================================================================
# Directory and file paths
# ============================================================================
CONFIG_FILE = Path.home() / ".speedscan_config"
ICON_PATH = Path.home() / "speedscan" / "assets" / "icon.png"
LOG_DIR = Path.home() / "speedscan" / "logs"
AGENT_SCRIPT = Path.home() / "speedscan" / "speedscan-agent.py"

# ============================================================================
# Default configuration
# ============================================================================
DEFAULT_CONFIG = {
    "theme": "techneon",
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

# ============================================================================
# Themes (corrigido: sem indentação extra)
# ============================================================================
THEMES = {
    "grey": {"mode": "light", "bg": "#d1d5db", "side": "#374151", "acc": "#0066ff", "text": "#111827"},
    "dark": {"mode": "dark", "bg": "#080808", "side": "#000000", "acc": "#0aff00", "text": "#ffffff"},
    "light": {"mode": "light", "bg": "#ffffff", "side": "#f8fafc", "acc": "#00e5ff", "text": "#0f172a"},
    "techneon": {"mode": "dark", "bg": "#0a0b1e", "side": "#1a1b2f", "acc": "#00f2ff", "text": "#ffffff"}
}

# ============================================================================
# Supported languages
# ============================================================================
LANGUAGES = {
    "pt_BR": "Português Brasileiro",
    "en_US": "English (US)",
    "es_ES": "Español"
}

# ============================================================================
# UI scale options
# ============================================================================
SCALES = {
    "auto": "Automatic",
    "100": "100%",
    "125": "125%",
    "150": "150%"
}

# ============================================================================
# AI suggestion list (for display)
# ============================================================================
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
CONFIG

# ============================================================================
# core/i18n.py
# ============================================================================
cat > core/i18n.py << 'I18N'
import gettext
import os
from pathlib import Path
from core import config

LOCALE_DIR = Path(__file__).parent.parent / 'locale'

def get_translation(language=None):
    if language is None:
        language = config.load_config().get('language', 'pt_BR')
    try:
        translation = gettext.translation(
            'speedscan',
            localedir=str(LOCALE_DIR),
            languages=[language]
        )
        return translation.gettext
    except FileNotFoundError:
        return gettext.gettext

_ = get_translation('pt_BR')
I18N

# ============================================================================
# core/actions.py
# ============================================================================
cat > core/actions.py << 'ACTIONS'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actions module: command running and mapping for multiple operating systems.
Version 1.0.0
"""

import subprocess
import logging
import os

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
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            else:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
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
        log.insert("end", "🧹 Limpando cache de memória...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        success = self._run_linux_command(["sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], log, use_sudo=True)
        log.insert("end", "✅ Cache limpo com sucesso.\n" if success else "❌ Erro ao limpar cache.\n")

    def run_swap_reset(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🗄 Resetando swap...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "swapoff", "-a"], log, use_sudo=True)
        self._run_linux_command(["sudo", "swapon", "-a"], log, use_sudo=True)
        log.insert("end", "✅ Swap resetado.\n")

    def run_fs_check(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔍 Verificando erros no sistema de arquivos...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "fsck", "-A", "-R", "-y"], log, use_sudo=True)
        log.insert("end", "✅ Verificação concluída.\n")

    def run_turbo_mode(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔧 Ativando modo turbo (ajusta governador para performance)...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "cpupower", "frequency-set", "-g", "performance"], log, use_sudo=True)
        log.insert("end", "✅ Modo turbo ativado.\n")

    def run_steam_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Steam...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        paths = [
            "~/.local/share/Steam",
            "~/.steam/steam/appcache",
            "~/.steam/root"
        ]
        for p in paths:
            path = os.path.expanduser(p)
            if os.path.exists(path):
                self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Steam limpo.\n")

    def run_lutris_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Lutris...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        path = os.path.expanduser("~/.local/share/lutris")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Lutris limpo.\n")

    def run_heroic_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Heroic Launcher...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        path = os.path.expanduser("~/.config/heroic/cache")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Heroic limpo.\n")

    def run_bottles_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Bottles...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        path = os.path.expanduser("~/.local/share/bottles")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Bottles limpo.\n")

    def run_wine_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Wine...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        path = os.path.expanduser("~/.wine")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Wine limpo.\n")

    def run_mangohud_config(self, log):
        log.delete("1.0", "end")
        log.insert("end", "⚙️ Configurando MangoHud...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        if self._run_linux_command(["which", "mangohud"], log, use_sudo=False):
            log.insert("end", "✅ MangoHud já está instalado.\n")
        else:
            log.insert("end", "❌ MangoHud não encontrado. Instale com: sudo apt install mangohud\n")

    def run_governor_config(self, log):
        log.delete("1.0", "end")
        log.insert("end", "⚙️ Configurando governador da CPU...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        if self._run_linux_command(["which", "cpupower"], log, use_sudo=False):
            self._run_linux_command(["sudo", "cpupower", "frequency-set", "-g", "ondemand"], log, use_sudo=True)
            log.insert("end", "✅ Governador configurado para ondemand.\n")
        else:
            log.insert("end", "❌ cpupower não encontrado. Instale linux-tools-common.\n")

    def run_dolphin_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Dolphin Emulator...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        path = os.path.expanduser("~/.local/share/dolphin-emu/cache")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Dolphin limpo.\n")

    def run_browser_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "Iniciando limpeza de navegadores...\n")
        results = self.app.browser_cleaner.clean_all_browsers(preserve_cookies=False, cookie_keep_list=None)
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
                    log.insert("end", f"  History: {self.app.browser_cleaner.format_bytes(data['history_freed'])}\n")
                    total_freed += data['history_freed']
                if data['errors']:
                    log.insert("end", f"  Errors: {', '.join(data['errors'])}\n")
        log.insert("end", f"\n✅ Total liberado: {self.app.browser_cleaner.format_bytes(total_freed)}\n")

    def run_services_manager(self, log):
        log.delete("1.0", "end")
        log.insert("end", "⚙️ Gerenciador de serviços (em desenvolvimento)...\n")

    def run_log_analysis(self, log):
        log.delete("1.0", "end")
        log.insert("end", "📋 Análise de logs (em desenvolvimento)...\n")

    def run_cookie_manager(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🗑️ Gerenciador de Cookies\n" + "="*40 + "\n")
        summary = self.app.cookie_manager.get_cookie_summary()
        if not summary:
            log.insert("end", "Nenhum cookie encontrado.\n")
            return
        log.insert("end", f"Total de domínios com cookies: {len(summary)}\n")
        for domain, count in list(summary.items())[:10]:
            log.insert("end", f"{domain}: {count} cookies\n")
        if len(summary) > 10:
            log.insert("end", f"... e mais {len(summary)-10} domínios.\n")

    def run_trim(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔧 Executando TRIM em SSDs...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "fstrim", "-v", "/"], log, use_sudo=True)
        log.insert("end", "✅ TRIM concluído.\n")

    def run_fix_broken(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🗄 Reparando pacotes quebrados...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚡ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "apt", "--fix-broken", "install"], log, use_sudo=True)
        log.insert("end", "✅ Reparo concluído.\n")

    def special_command(self, cmd, log):
        if cmd == "video_drv":
            log.insert("end", "Detectando GPU...\nFuncionalidade em desenvolvimento.\n")
        elif cmd == "net_drv":
            log.insert("end", "Detectando placa de rede...\nFuncionalidade em desenvolvimento.\n")
        elif cmd == "auto_update":
            log.insert("end", "Configurando atualizações automáticas...\nFuncionalidade em desenvolvimento.\n")
        elif cmd == "cookies":
            self.run_cookie_manager(log)
        elif cmd == "empty_trash":
            self.app.trash_manager.empty_trash()
            log.insert("end", "🗑️ Lixeira esvaziada.\n")
ACTIONS

# ============================================================================
# core/ai_proactive.py
# ============================================================================
cat > core/ai_proactive.py << 'AIPRO'
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

        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent > 90:
            suggestions.append({
                'title': '⚡ Low disk space',
                'description': f'Disk is at {disk_usage.percent:.1f}% usage. Free up space.',
                'action': 'browsers',
                'priority': 'high'
            })
        elif disk_usage.percent > 75:
            suggestions.append({
                'title': '🔔 Disk space',
                'description': f'Disk is at {disk_usage.percent:.1f}% usage. Consider cache clean.',
                'action': 'cache',
                'priority': 'medium'
            })

        mem = psutil.virtual_memory()
        if mem.percent > 90:
            suggestions.append({
                'title': '⚡ High RAM memory',
                'description': f'RAM usage is {mem.percent:.1f}%. Close heavy applications.',
                'action': None,
                'priority': 'high'
            })
        elif mem.percent > 80:
            suggestions.append({
                'title': '🔔 RAM memory',
                'description': f'RAM usage is {mem.percent:.1f}%. Consider restarting.',
                'action': None,
                'priority': 'medium'
            })

        try:
            temps = psutil.sensors_temperatures()
            for sensor, entries in temps.items():
                for entry in entries:
                    if entry.current > 80:
                        suggestions.append({
                            'title': '🔧 High temperature',
                            'description': f'{sensor}: {entry.current}°C. Check cooling.',
                            'action': None,
                            'priority': 'high'
                        })
                        break
        except Exception as e:
            logging.error(f"Error accessing temperatures: {e}")
            pass

        battery = psutil.sensors_battery()
        if battery and battery.percent < 20 and not battery.power_plugged:
            suggestions.append({
                'title': '🔋 Low battery',
                'description': f'Battery at {battery.percent:.1f}%. Plug in charger.',
                'action': None,
                'priority': 'high'
            })

        health = self.health_monitor.calculate_health_score()
        if health['score'] < 50:
            suggestions.append({
                'title': '🛡 System health critical',
                'description': 'Health score is low. Run optimizations.',
                'action': 'check',
                'priority': 'high'
            })
        elif health['score'] < 70:
            suggestions.append({
                'title': '🔄 System health',
                'description': 'Health score is medium. Consider cleaning.',
                'action': 'cache',
                'priority': 'medium'
            })

        stats = self.metrics_db.get_stats(period_hours=24)
        if stats['cpu_avg'] and stats['cpu_avg'] > 80:
            suggestions.append({
                'title': '📋 CPU consistently high',
                'description': f'Average CPU over last 24h: {stats["cpu_avg"]:.1f}%. Check processes.',
                'action': None,
                'priority': 'medium'
            })
        if stats['mem_avg'] and stats['mem_avg'] > 80:
            suggestions.append({
                'title': '📋 Memory consistently high',
                'description': f'Average memory over last 24h: {stats["mem_avg"]:.1f}%.',
                'action': None,
                'priority': 'medium'
            })

        cookie_sites = self.cookie_mgr.get_cookie_summary()
        if cookie_sites and len(cookie_sites) > 50:
            suggestions.append({
                'title': '🗑️ Many cookies stored',
                'description': f'You have cookies from {len(cookie_sites)} sites. Cleaning cookies may free space.',
                'action': 'cookies',
                'priority': 'low'
            })

        trash_size = self.trash_mgr.get_trash_size()
        if trash_size > 100 * 1024 * 1024:
            suggestions.append({
                'title': '🗑️ Trash is full',
                'description': f'Trash contains {trash_size / (1024*1024):.1f} MB. Empty it?',
                'action': 'empty_trash',
                'priority': 'medium'
            })

        return suggestions

    def get_summary(self):
        suggestions = self.analyze()
        if not suggestions:
            return "✅ No suggestions at the moment. System is OK!"
        lines = []
        for s in suggestions:
            priority_emoji = {
                'high': '🟥',
                'medium': '🟨',
                'low': '🟩'
            }.get(s['priority'], '▪️')
            lines.append(f"{priority_emoji} {s['title']}: {s['description']}")
        return "\n".join(lines)
AIPRO

# ============================================================================
# core/browser_cleaner.py
# ============================================================================
cat > core/browser_cleaner.py << 'BROWSER'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser cleaner module - cleans cache, cookies, and history from multiple browsers.
Version 1.0.0
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional

from core import config


class BrowserCleaner:
    def __init__(self):
        self.browsers = {
            'chrome': {
                'name': 'Google Chrome',
                'cache': Path.home() / '.cache/google-chrome',
                'cookies': Path.home() / '.config/google-chrome/Default/Cookies',
                'history': Path.home() / '.config/google-chrome/Default/History',
            },
            'chromium': {
                'name': 'Chromium',
                'cache': Path.home() / '.cache/chromium',
                'cookies': Path.home() / '.config/chromium/Default/Cookies',
                'history': Path.home() / '.config/chromium/Default/History',
            },
            'firefox': {
                'name': 'Firefox',
                'profile_dir': Path.home() / '.mozilla/firefox',
            },
            'brave': {
                'name': 'Brave',
                'cache': Path.home() / '.cache/Brave-Browser',
                'cookies': Path.home() / '.config/Brave-Browser/Default/Cookies',
                'history': Path.home() / '.config/Brave-Browser/Default/History',
            },
            'edge': {
                'name': 'Microsoft Edge',
                'cache': Path.home() / '.cache/microsoft-edge',
                'cookies': Path.home() / '.config/microsoft-edge/Default/Cookies',
                'history': Path.home() / '.config/microsoft-edge/Default/History',
            },
            'opera': {
                'name': 'Opera',
                'cache': Path.home() / '.cache/opera',
                'cookies': Path.home() / '.config/opera/Default/Cookies',
                'history': Path.home() / '.config/opera/Default/History',
            },
            'vivaldi': {
                'name': 'Vivaldi',
                'cache': Path.home() / '.cache/vivaldi',
                'cookies': Path.home() / '.config/vivaldi/Default/Cookies',
                'history': Path.home() / '.config/vivaldi/Default/History',
            },
        }

    def format_bytes(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names)-1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"

    def get_firefox_profiles(self):
        profiles = []
        profiles_ini = self.browsers['firefox']['profile_dir'] / 'profiles.ini'
        if not profiles_ini.exists():
            return profiles
        with open(profiles_ini) as f:
            lines = f.readlines()
        current_profile = None
        for line in lines:
            if line.startswith('['):
                current_profile = {}
            elif line.startswith('Path='):
                if current_profile is not None:
                    current_profile['path'] = line.split('=')[1].strip()
            elif line.startswith('Default=') and '1' in line:
                if current_profile is not None and 'path' in current_profile:
                    profiles.append(current_profile['path'])
        return profiles

    def clean_firefox(self, profile_path, preserve_cookies=False, cookie_keep_list=None):
        profile_dir = self.browsers['firefox']['profile_dir'] / profile_path
        freed = {'cache': 0, 'cookies': 0, 'history': 0}
        errors = []

        cache_dir = profile_dir / 'cache2'
        if cache_dir.exists():
            try:
                size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                shutil.rmtree(cache_dir)
                freed['cache'] = size
            except Exception as e:
                errors.append(f"Cache: {e}")

        cookies_db = profile_dir / 'cookies.sqlite'
        if cookies_db.exists():
            try:
                size = cookies_db.stat().st_size
                if preserve_cookies and cookie_keep_list:
                    pass
                else:
                    cookies_db.unlink()
                freed['cookies'] = size
            except Exception as e:
                errors.append(f"Cookies: {e}")

        places_db = profile_dir / 'places.sqlite'
        if places_db.exists():
            try:
                size = places_db.stat().st_size
                places_db.unlink()
                freed['history'] = size
            except Exception as e:
                errors.append(f"History: {e}")

        return freed, errors

    def clean_browser(self, browser_key, preserve_cookies=False, cookie_keep_list=None):
        browser = self.browsers.get(browser_key)
        if not browser:
            return None

        freed = {'cache': 0, 'cookies': 0, 'history': 0}
        errors = []

        if browser_key == 'firefox':
            profiles = self.get_firefox_profiles()
            for profile in profiles:
                f, e = self.clean_firefox(profile, preserve_cookies, cookie_keep_list)
                for k in freed:
                    freed[k] += f[k]
                errors.extend(e)
        else:
            if 'cache' in browser and browser['cache'].exists():
                try:
                    size = sum(f.stat().st_size for f in browser['cache'].rglob('*') if f.is_file())
                    shutil.rmtree(browser['cache'])
                    freed['cache'] = size
                except Exception as e:
                    errors.append(f"Cache: {e}")

            if 'cookies' in browser and browser['cookies'].exists():
                try:
                    size = browser['cookies'].stat().st_size
                    if preserve_cookies and cookie_keep_list:
                        pass
                    else:
                        browser['cookies'].unlink()
                    freed['cookies'] = size
                except Exception as e:
                    errors.append(f"Cookies: {e}")

            if 'history' in browser and browser['history'].exists():
                try:
                    size = browser['history'].stat().st_size
                    browser['history'].unlink()
                    freed['history'] = size
                except Exception as e:
                    errors.append(f"History: {e}")

        return freed, errors

    def clean_all_browsers(self, preserve_cookies=False, cookie_keep_list=None):
        results = {}
        for key in self.browsers:
            result = self.clean_browser(key, preserve_cookies, cookie_keep_list)
            if result:
                freed, errors = result
                results[key] = {
                    'name': self.browsers[key]['name'],
                    'cache_freed': freed['cache'],
                    'cookies_freed': freed['cookies'],
                    'history_freed': freed['history'],
                    'errors': errors
                }
        return results
BROWSER

# ============================================================================
# core/chat.py
# ============================================================================
cat > core/chat.py << 'CHAT'
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
        self.current_ai = app_instance.config.get("ai", {}).get("provider", "ollama")
        self.ai_model = app_instance.config.get("ai", {}).get("model", "llama3.2")
        self.endpoint = app_instance.config.get("ai", {}).get("endpoint", "http://localhost:11434")
        self.api_key = app_instance.config.get("ai", {}).get("api_key", "")

        self.chat_display = ctk.CTkTextbox(self, wrap="word", font=("Inter", 12),
                                            fg_color=self.app.light_bg,
                                            text_color=self.app.text_color)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_display.configure(state="disabled")

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0,10))

        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Digite sua mensagem...")
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(input_frame, text="Enviar", command=self.send_message,
                                       fg_color=self.app.acc_color, cursor="hand2")
        self.send_btn.pack(side="right")

        self._add_message("system", "🤖 Conectado ao assistente. Digite /help para comandos.")

    def _add_message(self, role, content):
        self.chat_display.configure(state="normal")
        if role == "user":
            self.chat_display.insert("end", f"Você: {content}\n\n")
        elif role == "assistant":
            self.chat_display.insert("end", f"IA: {content}\n\n")
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
            self._add_message("system", "Comandos disponíveis:\n/help - ajuda\n/clear - limpa chat\n/modelo - mostra modelo atual\n/trash - lista lixeira\n/emptytrash - esvazia lixeira")
        elif cmd == "/clear":
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
            self.history = []
            self._add_message("system", "🧹 Chat limpo.")
        elif cmd == "/modelo":
            self._add_message("system", f"Modelo atual: {self.current_ai} ({self.ai_model})")
        elif cmd == "/trash":
            items = self.app.trash_manager.list_trash()
            if items:
                msg = "Itens na lixeira:\n" + "\n".join([f"{i['name']} (original: {i['original']})" for i in items])
            else:
                msg = "Lixeira vazia."
            self._add_message("system", msg)
        elif cmd == "/emptytrash":
            self.app.trash_manager.empty_trash()
            self._add_message("system", "🗑️ Lixeira esvaziada.")
        else:
            self._add_message("system", f"Comando desconhecido: {cmd}")

    def _get_ai_response(self, user_message):
        if self.current_ai == "ollama":
            self._query_ollama(user_message)
        elif self.current_ai == "openai":
            self._query_openai(user_message)
        elif self.current_ai == "deepseek":
            self._query_deepseek(user_message)
        else:
            self.app.after(0, lambda: self._add_message("system", "⚡ Provider não suportado."))

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
                reply = data.get("message", {}).get("content", "Sem resposta.")
                self.app.after(0, lambda: self._add_message("assistant", reply))
            else:
                self.app.after(0, lambda: self._add_message("system", f"Erro Ollama: {response.status_code}"))
        except Exception as e:
            logging.error(f"Error querying Ollama: {e}")
            self.app.after(0, lambda e=e: self._add_message("system", f"Erro conectando ao Ollama: {e}"))

    def _query_openai(self, message):
        self.app.after(0, lambda: self._add_message("system", "⚡ OpenAI not implemented. Configure your key."))

    def _query_deepseek(self, message):
        self.app.after(0, lambda: self._add_message("system", "⚡ DeepSeek not implemented."))
CHAT

# ============================================================================
# core/cookie_manager.py
# ============================================================================
cat > core/cookie_manager.py << 'COOKIE'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie manager for browsers - read, backup, restore, and delete cookies.
Version 1.0.0
"""

import logging
import sqlite3
import json
from pathlib import Path
import shutil

from core import config


class CookieManager:
    def __init__(self):
        self.cookie_files = {
            'chrome': Path.home() / '.config/google-chrome/Default/Cookies',
            'chromium': Path.home() / '.config/chromium/Default/Cookies',
            'firefox': Path.home() / '.mozilla/firefox/*.default-release/cookies.sqlite',
            'brave': Path.home() / '.config/Brave-Browser/Default/Cookies',
            'edge': Path.home() / '.config/microsoft-edge/Default/Cookies',
            'opera': Path.home() / '.config/opera/Default/Cookies',
            'chromium-flatpak': Path.home() / '.var/app/org.chromium.Chromium/config/chromium/Default/Cookies',
            'firefox-flatpak': Path.home() / '.var/app/org.mozilla.firefox/.mozilla/firefox/*.default-release/cookies.sqlite',
        }

    def get_cookies_from_browser(self, browser_key):
        path = self.cookie_files.get(browser_key)
        if not path:
            return []
        if '*' in str(path):
            paths = list(Path(str(path).replace('*', '')).parent.glob('*.default-release'))
            if not paths:
                return []
            path = paths[0] / 'cookies.sqlite'
        if not path.exists():
            return []
        cookies = []
        try:
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, value FROM cookies")
            rows = cursor.fetchall()
            for row in rows:
                cookies.append({'host': row[0], 'name': row[1], 'value': row[2]})
            conn.close()
            return cookies
        except Exception as e:
            logging.error(f"Error reading cookies from {browser_key}: {e}")
            return []

    def get_cookie_summary(self):
        summary = {}
        for browser in self.cookie_files:
            cookies = self.get_cookies_from_browser(browser)
            for c in cookies:
                host = c['host']
                summary[host] = summary.get(host, 0) + 1
        return summary

    def backup_cookies(self, browser_key, backup_path):
        src = self.cookie_files.get(browser_key)
        if not src or not src.exists():
            return False
        shutil.copy2(src, backup_path)
        return True

    def restore_cookies(self, backup_path, browser_key):
        dest = self.cookie_files.get(browser_key)
        if not dest:
            return False
        shutil.copy2(backup_path, dest)
        return True

    def delete_cookies_except(self, browser_key, keep_domains):
        path = self.cookie_files.get(browser_key)
        if not path:
            return False
        if '*' in str(path):
            paths = list(Path(str(path).replace('*', '')).parent.glob('*.default-release'))
            if not paths:
                return False
            path = paths[0] / 'cookies.sqlite'
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
COOKIE

# ============================================================================
# core/dashboard.py
# ============================================================================
cat > core/dashboard.py << 'DASHBOARD'
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
    {"id": "distro", "name": "Distribuição", "callback": "widget_distro"},
    {"id": "kernel", "name": "Kernel", "callback": "widget_kernel"},
    {"id": "uptime", "name": "Uptime", "callback": "widget_uptime"},
    {"id": "cpu", "name": "CPU", "callback": "widget_cpu"},
    {"id": "ram", "name": "Memória RAM", "callback": "widget_ram"},
    {"id": "gpu", "name": "GPU", "callback": "widget_gpu"},
    {"id": "disks", "name": "Discos", "callback": "widget_disks"},
    {"id": "battery", "name": "Bateria", "callback": "widget_battery"},
    {"id": "temps", "name": "Temperaturas", "callback": "widget_temps"},
    {"id": "health", "name": "Saúde", "callback": "widget_health"},
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
        slots_frame.pack(fill="x", padx=10)

        for i in range(3):
            slot_frame = ctk.CTkFrame(slots_frame, fg_color="transparent")
            slot_frame.pack(side="left", fill="both", expand=True, padx=5)
            self.slots.append(slot_frame)

        available_label = ctk.CTkLabel(
            self,
            text="Widgets disponíveis:",
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
DASHBOARD

# ============================================================================
# core/first_run.py
# ============================================================================
cat > core/first_run.py << 'FIRSTRUN'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
First run wizard for SpeedScan - displayed on first start to configure basic settings.
Version 1.0.0
"""

import customtkinter as ctk

from core import config


class FirstRunWizard(ctk.CTkToplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.title("Bem-vindo ao SpeedScan!")
        self.geometry("600x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(self, text=".SpeedScan", font=("Inter", 24, "bold"),
                              text_color=parent.acc_color)
        title.grid(row=0, column=0, pady=(20,10))

        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        welcome = ctk.CTkLabel(self.content_frame, text="Obrigado por instalar o SpeedScan! Vamos configurar suas preferências.",
                                font=("Inter", 12), justify="left", wraplength=500)
        welcome.pack(pady=10)

        name_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(name_frame, text="Seu nome:", font=("Inter", 12)).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="Digite seu nome")
        self.name_entry.pack(fill="x", pady=5)
        self.name_entry.insert(0, config.get("username", ""))

        theme_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(theme_frame, text="Tema preferido:", font=("Inter", 12)).pack(anchor="w")
        self.theme_var = ctk.StringVar(value="TechNeon")
        theme_menu = ctk.CTkOptionMenu(theme_frame, values=["TechNeon", "Black Neon", "Clean Snow", "Still"],
                                       variable=self.theme_var, cursor="left_ptr")
        theme_menu.pack(anchor="w", pady=5)

        level_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        level_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(level_frame, text="Seu nível de conhecimento:", font=("Inter", 12)).pack(anchor="w")
        self.level_var = ctk.StringVar(value="iniciante")
        iniciante_radio = ctk.CTkRadioButton(level_frame, text="Iniciante (apenas funções básicas)", variable=self.level_var, value="iniciante", cursor="hand2")
        iniciante_radio.pack(anchor="w", pady=2)
        intermediario_radio = ctk.CTkRadioButton(level_frame, text="Intermediário (funções básicas + algumas avançadas)", variable=self.level_var, value="intermediario", cursor="hand2")
        intermediario_radio.pack(anchor="w", pady=2)
        avancado_radio = ctk.CTkRadioButton(level_frame, text="Avançado (todas as funções, sem restrições)", variable=self.level_var, value="avancado", cursor="hand2")
        avancado_radio.pack(anchor="w", pady=2)

        tip = ctk.CTkLabel(self.content_frame, text="🪄 Você pode alterar essas configurações depois a qualquer momento na aba 'Configurações'.",
                            font=("Inter", 10, "italic"), text_color="#888888")
        tip.pack(pady=20)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=20)
        ctk.CTkButton(btn_frame, text="Concluir", command=self.save_and_close,
                      fg_color=self.parent.acc_color, width=150, cursor="hand2").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Pular", command=self.destroy,
                      fg_color="gray", width=100, cursor="hand2").pack(side="left", padx=10)

    def save_and_close(self):
        self.config["username"] = self.name_entry.get() or "Usuário"
        theme_map = {
            "TechNeon": "techneon",
            "Black Neon": "dark",
            "Clean Snow": "light",
            "Still": "grey"
        }
        self.config["theme"] = theme_map.get(self.theme_var.get(), "techneon")
        level = self.level_var.get()
        if level == "iniciante":
            self.config["simple_mode"] = True
            self.config["expert_level"] = 1
        elif level == "intermediario":
            self.config["simple_mode"] = False
            self.config["expert_level"] = 2
        else:
            self.config["simple_mode"] = False
            self.config["expert_level"] = 3
        self.parent.config.update(self.config)
        self.parent._save_config()
        self.parent.show_toast("Configurações salvas! Algumas alterações podem exigir reinício.")
        self.destroy()
FIRSTRUN

# ============================================================================
# core/hardware.py
# ============================================================================
cat > core/hardware.py << 'HARDWARE'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware information collection module.
Version 1.0.0
"""

import platform
import psutil
import subprocess
import re
import time
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
            total = mem.total // (1024 ** 3)
            used = mem.used // (1024 ** 3)
            return f"{used} GB / {total} GB"
        except Exception as e:
            logging.error(f"Error getting RAM info: {e}")
            return "N/A"

    def get_gpu(self):
        try:
            if self.so == "Linux":
                out = subprocess.run(["lspci"], capture_output=True, text=True)
                for line in out.stdout.splitlines():
                    if "VGA" in line or "3D" in line:
                        return line.split(":")[2].strip()
            elif self.so == "Windows":
                out = subprocess.run(["wmic", "path", "win32_videocontroller", "get", "name"], capture_output=True, text=True)
                lines = out.stdout.splitlines()
                if len(lines) >= 2:
                    return lines[1].strip()
            elif self.so == "Darwin":
                out = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True)
                for line in out.stdout.splitlines():
                    if "Chipset Model" in line:
                        return line.split(":")[1].strip()
        except Exception as e:
            logging.error(f"Error in get_gpu: {e}")
            return "Unknown"
HARDWARE

# ============================================================================
# core/health_score.py
# ============================================================================
cat > core/health_score.py << 'HEALTH'
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
        disk = psutil.disk_usage('/')
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
            'score': score,
            'details': {
                'cpu': cpu_score,
                'memory': mem_score,
                'disk': disk_score,
                'uptime': uptime_score,
                'battery': battery_score if battery else None
            }
        }
HEALTH

# ============================================================================
# core/historical_metrics.py
# ============================================================================
cat > core/historical_metrics.py << 'HIST'
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
            conn.execute('''
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
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)')

    def insert(self, cpu=None, memory=None, disk_usage=None,
               disk_io_read=None, disk_io_write=None, net_sent=None, net_recv=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO metrics
                    (timestamp, cpu, memory, disk_usage, disk_io_read, disk_io_write, net_sent, net_recv)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (time.time(), cpu, memory, disk_usage,
                      disk_io_read, disk_io_write, net_sent, net_recv))
        except Exception as e:
            logging.error(f"Failed to insert metrics: {e}")

    def get_last_hours(self, hours=1, metrics=None):
        if metrics is None:
            metrics = ['timestamp', 'cpu', 'memory', 'disk_usage']
        else:
            if 'timestamp' not in metrics:
                metrics = ['timestamp'] + metrics
        cols = ', '.join(metrics)
        cutoff = time.time() - hours * 3600
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f'SELECT {cols} FROM metrics WHERE timestamp >= ? ORDER BY timestamp', (cutoff,))
            rows = cursor.fetchall()
        return rows

    def prune_old(self, days=7):
        cutoff = time.time() - days * 24 * 3600
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff,))

    def get_stats(self, period_hours=1):
        cutoff = time.time() - period_hours * 3600
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT
                    AVG(cpu), MIN(cpu), MAX(cpu),
                    AVG(memory), MIN(memory), MAX(memory),
                    AVG(disk_usage), MIN(disk_usage), MAX(disk_usage)
                FROM metrics WHERE timestamp >= ?
            ''', (cutoff,))
            row = cursor.fetchone()
        return {
            'cpu_avg': row[0], 'cpu_min': row[1], 'cpu_max': row[2],
            'mem_avg': row[3], 'mem_min': row[4], 'mem_max': row[5],
            'disk_avg': row[6], 'disk_min': row[7], 'disk_max': row[8]
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
            disk = psutil.disk_usage('/').percent

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
HIST

# ============================================================================
# core/lan_cache.py
# ============================================================================
cat > core/lan_cache.py << 'LANCACHE'
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

    def is_docker_installed(self):
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception as e:
            logging.error(f"Error checking Docker installation: {e}")
            return False

    def install_docker(self):
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
                "echo \"For macOS, install Docker Desktop manually: https://docs.docker.com/desktop/install/mac-install/\""
            ]
        elif self.so == "Windows":
            return [
                "echo \"For Windows, install Docker Desktop manually: https://docs.docker.com/desktop/install/windows-install/\""
            ]
        return []

    def get_install_commands(self):
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

    def get_status(self):
        try:
            result = subprocess.run(["docker", "ps", "--filter", "name=lancache", "--format", "table"], capture_output=True, text=True)
            if "lancache" in result.stdout:
                return "✅ LANCache is running"
            else:
                return "❌ LANCache is not running"
        except FileNotFoundError:
            return "❌ Docker is not installed"
        except Exception as e:
            logging.error(f"Error checking LANCache status: {e}")
            return "❌ Error checking status"

    def stop(self):
        home = Path.home()
        lancache_dir = home / "lancache"
        return [f"cd {lancache_dir} && sudo docker-compose down"]

    def configure_dns(self, dns_ip=None):
        if dns_ip is None:
            try:
                result = subprocess.run(["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", "lancache-dns"], capture_output=True, text=True)
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
LANCACHE

# ============================================================================
# core/lan_scanner.py
# ============================================================================
cat > core/lan_scanner.py << 'LANSCAN'
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
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if 'default via' in line:
                    parts = line.split()
                    iface = parts[4] if len(parts) > 4 else None
                    result2 = subprocess.run(['ip', '-4', 'addr', 'show', iface], capture_output=True, text=True)
                    for line2 in result2.stdout.splitlines():
                        if 'inet ' in line2:
                            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)(/\d+)', line2)
                            if match:
                                ip = match.group(1)
                                prefix = match.group(2)
                                network = ipaddress.IPv4Network(f"{ip}{prefix}", strict=False)
                                return str(network)
            return None
        except Exception as e:
            logging.error(f"Error determining local network: {e}")
            return None

    def ping_host(self, ip: str) -> bool:
        try:
            result = subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                                     capture_output=True, timeout=2)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error pinging {ip}: {e}")
            return False

    def arp_lookup(self, ip: str) -> Optional[Dict]:
        try:
            result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[0] == ip and 'lladdr' in line:
                    mac = parts[3] if len(parts) > 3 else None
                    return {'ip': ip, 'mac': mac}
        except Exception as e:
            logging.error(f"Error in arp_lookup for {ip}: {e}")
            pass
        try:
            result = subprocess.run(["ip", "neigh", "show", ip], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if ip in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        mac = parts[4] if re.match(r'([0-9a-f]{2}:){5}[0-9a-f]{2}', parts[4]) else None
                        return {'ip': ip, 'mac': mac}
        except Exception as e:
            logging.error(f"Error in arp_lookup (fallback) for {ip}: {e}")
            pass
        return None

    def get_hostname(self, ip: str) -> Optional[str]:
        try:
            result = subprocess.run(["nslookup", ip], capture_output=True, text=True, timeout=2)
            match = re.search(r'name = (.+)\.', result.stdout)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logging.error(f"Error in nslookup for {ip}: {e}")
            return None

    def get_vendor(self, mac: str) -> str:
        if not mac:
            return "Desconhecido"
        oui = mac.replace(':', '').upper()[:6]
        vendors = {
            '001122': 'Fabricante A',
            'AABBCC': 'Fabricante B',
        }
        return vendors.get(oui, "Desconhecido")

    def scan_network(self, network_cidr: str = None, progress_callback=None) -> List[Dict]:
        if network_cidr is None:
            network_cidr = self.get_local_network()
            if network_cidr is None:
                return [{'error': "Unable to determine the local network."}]
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
                    mac = arp_info['mac'] if arp_info else None
                    hostname = self.get_hostname(ip)
                    vendor = self.get_vendor(mac) if mac else "Desconhecido"
                    devices.append({
                        'ip': ip,
                        'mac': mac if mac else 'N/A',
                        'hostname': hostname if hostname else 'Desconhecido',
                        'vendor': vendor,
                        'status': 'active'
                    })
                if progress_callback:
                    progress_callback(i+1, total, ip, is_alive)
        self.devices = devices
        return devices

    def stop_scan(self):
        self._stop_scan = True

    def get_scan_summary(self) -> str:
        active = len([d for d in self.devices if d.get('status') == 'active'])
        total = len(self.devices)
        return f"Active devices: {active}/{total}"
LANSCAN

# ============================================================================
# core/process_manager.py
# ============================================================================
cat > core/process_manager.py << 'PROCESS'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process management module (thread-safe with queue).
Version 1.0.0
"""

import psutil
import time
import threading
import queue
import logging
from typing import List, Dict, Any, Optional

from core import config


class ProcessManager:
    def __init__(self):
        self.sort_by = 'cpu_percent'
        self.reverse = True
        self.filter_term = ""
        self.update_interval = 2
        self._stop_event = threading.Event()
        self._thread = None
        self.callback_queue = queue.Queue()

    def get_process_list(self) -> List[Dict[str, Any]]:
        process_list = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent',
                                         'status', 'create_time', 'username', 'nice']):
            try:
                pinfo = proc.info
                pinfo['cpu_percent'] = round(pinfo['cpu_percent'] or 0, 1)
                pinfo['memory_percent'] = round(pinfo['memory_percent'] or 0, 1)
                create_time = pinfo['create_time']
                if create_time:
                    pinfo['create_time_str'] = time.strftime('%H:%M:%S', time.localtime(create_time))
                else:
                    pinfo['create_time_str'] = ''
                pinfo['nice'] = pinfo['nice'] if pinfo['nice'] is not None else 0
                process_list.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                pid = proc.pid if hasattr(proc, 'pid') else 'unknown'
                name = proc.name() if hasattr(proc, 'name') else 'unknown'
                logging.error(f"Failed to access process PID={pid} name={name}: {e}")
                continue

        if self.filter_term:
            term = self.filter_term.lower()
            process_list = [p for p in process_list if term in p['name'].lower()]

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
            logging.info(f"Process PID?{pid} suspended.")
            return True
        except Exception as e:
            logging.error(f"Failed to suspend process PID?{pid}: {e}")
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
        self._stop_event.clear()
        if self._thread is None or not self._thread.is_alive():
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
PROCESS

# ============================================================================
# core/scheduler.py
# ============================================================================
cat > core/scheduler.py << 'SCHEDULER'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agendador de tarefas automáticas
Versão 1.0.0
"""

import subprocess
import os
from pathlib import Path
import logging

from core import config


class Scheduler:
    def __init__(self, so, log_dir, agent_script):
        self.so = so
        self.log_dir = log_dir
        self.agent_script = agent_script

    def create_schedule(self, config):
        if not config['enabled']:
            self.remove_schedule()
            return

        tasks = config['tasks']
        hour = config['hour']
        freq = config['frequency']
        elevated = config['elevated']

        cmd = f"python3 {self.agent_script} --tasks {','.join(tasks)}"
        if elevated:
            cmd = "sudo " + cmd

        log_file = self.log_dir / "scheduler.log"

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
        cron_line = f"{hour} * * * * {cmd} >> {self.log_dir}/cron.log 2>&1"
        subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron_line}") | crontab -', shell=True)

    def _create_task_scheduler(self, cmd, freq, hour, config):
        subprocess.run(f'schtasks /create /tn SpeedScanAgent /tr "{cmd}" /sc DAILY /st {hour}', shell=True)

    def _create_launchd(self, cmd, freq, hour, config):
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
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
        <integer>{int(hour.split(':')[0])}</integer>
        <key>Minute</key>
        <integer>{int(hour.split(':')[1])}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{self.log_dir}/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>{self.log_dir}/launchd.log</string>
</dict>
</plist>"""
        plist_path = Path.home() / "Library/LaunchAgents/com.speedscan.agent.plist"
        plist_path.write_text(plist)
        subprocess.run(f"launchctl load {plist_path}", shell=True)
SCHEDULER

# ============================================================================
# core/security_scanner.py
# ============================================================================
cat > core/security_scanner.py << 'SECURITY'
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
                        addr = parts[3] if 'LISTEN' in line else None
                        if addr and ':' in addr:
                            ip, port = addr.rsplit(':', 1)
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
                result = subprocess.run(cmd, captureOutput=True, text=True, timeout=5)
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
SECURITY

# ============================================================================
# core/smart_monitor.py
# ============================================================================
cat > core/smart_monitor.py << 'SMART'
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
                    match = re.search(r'SMART overall-health self-assessment test result: (\w+)', smart)
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
SMART

# ============================================================================
# core/speed_test.py
# ============================================================================
cat > core/speed_test.py << 'SPEED'
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
            'ping': None,
            'download': None,
            'upload': None,
            'server': None,
            'timestamp': None,
            'error': None
        }

    def test_with_speedtest(self):
        try:
            st = speedtest.Speedtest(secure=True)
            st.get_best_server()
            self.result['ping'] = round(st.results.ping, 1)
            self.result['server'] = f"{st.results.server['name']} ({st.results.server['country']})"
            download_bps = st.download()
            self.result['download'] = round(download_bps / 1_000_000, 2)
            upload_bps = st.upload()
            self.result['upload'] = round(upload_bps / 1_000_000, 2)
            self.result['timestamp'] = time.time()
            return True
        except Exception as e:
            logging.error(f"Error in test_with_speedtest: {e}")
            self.result['error'] = str(e)
            return False

    def test_fallback(self):
        import requests
        import tempfile
        try:
            start = time.time()
            requests.get("https://www.google.com", timeout=5)
            ping = (time.time() - start) * 1000
            self.result['ping'] = round(ping, 1)

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
                self.result['download'] = round(download_mbps, 2)

            data = os.urandom(5 * 1024 * 1024)
            start = time.time()
            requests.post("https://httpbin.org/post", data=data, timeout=30)
            elapsed = time.time() - start
            upload_mbps = (len(data) * 8) / elapsed / 1_000_000
            self.result['upload'] = round(upload_mbps, 2)

            self.result['server'] = "Fallback (public servers)"
            self.result['timestamp'] = time.time()
            return True
        except Exception as e:
            logging.error(f"Error in test_fallback: {e}")
            self.result['error'] = str(e)
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

    def format_result(self, result=None):
        if result is None:
            result = self.result
        if result.get('error'):
            return f"❌ Error: {result['error']}"
        lines = []
        if result.get('ping') is not None:
            lines.append(f"📡 Ping: {result['ping']} ms")
        if result.get('download') is not None:
            lines.append(f"⬇️ Download: {result['download']} Mbps")
        if result.get('upload') is not None:
            lines.append(f"⬆️ Upload: {result['upload']} Mbps")
        if result.get('server'):
            lines.append(f"🖥️ Server: {result['server']}")
        if result.get('timestamp'):
            from datetime import datetime
            dt = datetime.fromtimestamp(result['timestamp'])
            lines.append(f"🕒 {dt.strftime('%d/%m/%Y %H:%M:%S')}")
        return "\n".join(lines)
SPEED

# ============================================================================
# core/temperature_monitor.py
# ============================================================================
cat > core/temperature_monitor.py << 'TEMP'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# core/temperature_monitor.py

import psutil
import subprocess

class TemperatureMonitor:
    def __init__(self):
        self.sensors = {}

    def get_cpu_temperatures(self):
        temps = {}
        try:
            thermal = psutil.sensors_temperatures()
            if 'coretemp' in thermal:
                for entry in thermal['coretemp']:
                    label = entry.label or f"Core {len(temps)}"
                    temps[f"CPU {label}"] = round(entry.current, 1)
            elif 'k10temp' in thermal:
                for entry in thermal['k10temp']:
                    temps["CPU Package"] = round(entry.current, 1)
            else:
                try:
                    with open("/sys/class/thermal/thermal_zone0/temp") as f:
                        temp = int(f.read().strip()) / 1000.0
                        temps["CPU"] = round(temp, 1)
                except Exception as e:
                    pass
        except Exception as e:
            pass
        return temps

    def get_gpu_temperatures(self):
        temps = {}
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                                 capture_output=True, text=True, timeout=2)
            if out.returncode == 0:
                lines = out.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        temps[f"GPU {i}"] = round(float(line.strip()), 1)
        except Exception as e:
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
TEMP

# ============================================================================
# core/trash_manager.py
# ============================================================================
cat > core/trash_manager.py << 'TRASH'
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
        with open(TRASH_METADATA, 'r') as f:
            return json.load(f)

    def _save_metadata(self, metadata):
        with open(TRASH_METADATA, 'w') as f:
            json.dump(metadata, f, indent=2)

    def move_to_trash(self, path, original_path):
        if not os.path.exists(path):
            return False
        trash_name = f"{int(time.time())}_{os.path.basename(path)}"
        trash_path = TRASH_DIR / trash_name
        shutil.move(path, trash_path)
        metadata = self._load_metadata()
        metadata[trash_name] = {
            'original': str(original_path),
            'time': time.time()
        }
        self._save_metadata(metadata)
        return True

    def restore(self, trash_name):
        metadata = self._load_metadata()
        if trash_name not in metadata:
            return False
        info = metadata[trash_name]
        trash_path = TRASH_DIR / trash_name
        original = Path(info['original'])
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
                'name': name,
                'original': info['original'],
                'time': info['time']
            })
        return items

    def get_trash_size(self):
        total = 0
        for root, dirs, files in os.walk(TRASH_DIR):
            for f in files:
                if f == 'metadata.json':
                    continue
                fp = Path(root) / f
                total += fp.stat().st_size
        return total
TRASH

# ============================================================================
# core/ui.py (MODIFICADO PARA RETORNAR LABELS)
# ============================================================================
cat > core/ui.py << 'UI'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI utility functions for the SpeedScan application.
Version 1.0.0
"""

import customtkinter as ctk
import logging

from core import config


def add_tooltip(widget, text):
    tooltip = None

    def enter(event):
        nonlocal tooltip
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        tooltip = ctk.CTkTopLevel(widget)
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
    result_labels = {}
    for idx, (label, cmd, is_dns) in enumerate(items):
        row, col = divmod(idx, 3)
        card = ctk.CTkFrame(grid_frame, fg_color=bg_color, corner_radius=10,
                             border_width=1, border_color=acc_color)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        card.grid_propagate(False)
        card.configure(height=150)

        title = ctk.CTkLabel(card, text=label, font=("Inter", 14, "bold"),
                              text_color=acc_color)
        title.pack(pady=(10,5))

        if cmd == "ping":
            ping_label = ctk.CTkLabel(card, text="-- ms", font=("Inter", 18, "bold"),
                                       text_color=text_color)
            ping_label.pack(expand=True)
            ping_labels.append(ping_label)
            result_labels[cmd] = ping_label
        else:
            # Label para resultados curtos
            result_label = ctk.CTkLabel(card, text="", font=("Inter", 12), text_color=text_color, wraplength=180)
            result_label.pack(expand=True, fill="both", padx=5, pady=5)
            result_labels[cmd] = result_label

        btn = ctk.CTkButton(card, text="Run", fg_color=acc_color,
                             command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d),
                             cursor="hand2")
        btn.pack(pady=5)

    for i in range(3):
        grid_frame.columnconfigure(i, weight=1)

    return ping_labels, result_labels


def add_console(parent, tag_prefix, acc_color, toggle_callback):
    console = ctk.CTkTextbox(parent, height=150, fg_color="#1e1e1e", text_color="#ffffff",
                              font=("Consolas", 10), corner_radius=10)
    btn = ctk.CTkButton(parent, text="Detalhes ▼", fg_color=acc_color,
                         command=lambda: toggle_callback(tag_prefix), cursor="hand2")
    return btn, console
UI

# ============================================================================
# core/windows_cleaner.py (OPCIONAL)
# ============================================================================
cat > core/windows_cleaner.py << 'WIN'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de limpeza do Windows (bloatware, telemetria e componentes de IA)
Uso exclusivo em sistemas Windows.
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
            {"name": _("Xbox App"), "package": "Microsoft.XboxApp", "description": _("Aplicativo Xbox")},
            {"name": _("Xbox Game Bar"), "package": "Microsoft.XboxGamingOverlay", "description": _("Barra de jogo Xbox")},
            {"name": _("Xbox Identity Provider"), "package": "Microsoft.XboxIdentityProvider", "description": _("Provedor de identidade Xbox")},
            {"name": _("Xbox Speech to Text Overlay"), "package": "Microsoft.XboxSpeechToTextOverlay", "description": _("Sobreposição de fala Xbox")},
            {"name": _("Candy Crush"), "package": "king.com.CandyCrushSaga", "description": _("Jogo Candy Crush")},
            {"name": _("Skype"), "package": "Microsoft.SkypeApp", "description": _("Skype")},
            {"name": _("OneDrive"), "package": "Microsoft.OneDrive", "description": _("OneDrive")},
            {"name": _("Bing Weather"), "package": "Microsoft.BingWeather", "description": _("Clima Bing")},
            {"name": _("Bing News"), "package": "Microsoft.BingNews", "description": _("Notícias Bing")},
            {"name": _("Bing Sports"), "package": "Microsoft.BingSports", "description": _("Esportes Bing")},
            {"name": _("Bing Finance"), "package": "Microsoft.BingFinance", "description": _("Finanças Bing")},
            {"name": _("3D Builder"), "package": "Microsoft.3DBuilder", "description": _("Construtor 3D")},
            {"name": _("People"), "package": "Microsoft.People", "description": _("Pessoas")},
            {"name": _("Zune Music"), "package": "Microsoft.ZuneMusic", "description": _("Música Zune")},
            {"name": _("Zune Video"), "package": "Microsoft.ZuneVideo", "description": _("Vídeo Zune")},
            {"name": _("Mixed Reality Portal"), "package": "Microsoft.MixedReality.Portal", "description": _("Portal Realidade Mista")},
            {"name": _("Office Hub"), "package": "Microsoft.MicrosoftOfficeHub", "description": _("Hub do Office")},
            {"name": _("Solitaire Collection"), "package": "Microsoft.MicrosoftSolitaireCollection", "description": _("Coleção Paciência")},
            {"name": _("Sticky Notes"), "package": "Microsoft.MicrosoftStickyNotes", "description": _("Notas Auto-adesivas")},
            {"name": _("Windows Camera"), "package": "Microsoft.WindowsCamera", "description": _("Câmera do Windows")},
            {"name": _("Windows Communications Apps"), "package": "Microsoft.WindowsCommunicationsApps", "description": _("Aplicativos de Comunicações")},
            {"name": _("Windows Feedback Hub"), "package": "Microsoft.WindowsFeedbackHub", "description": _("Hub de Feedback")},
            {"name": _("Windows Maps"), "package": "Microsoft.WindowsMaps", "description": _("Mapas do Windows")},
            {"name": _("Windows Sound Recorder"), "package": "Microsoft.WindowsSoundRecorder", "description": _("Gravador de Som")},
            {"name": _("Your Phone"), "package": "Microsoft.YourPhone", "description": _("Seu Telefone")},
            {"name": _("Get Help"), "package": "Microsoft.GetHelp", "description": _("Obter Ajuda")},
            {"name": _("Messaging"), "package": "Microsoft.Messaging", "description": _("Mensagens")},
            {"name": _("Office OneNote"), "package": "Microsoft.Office.OneNote", "description": _("OneNote")},
            {"name": _("Outlook for Windows"), "package": "Microsoft.OutlookForWindows", "description": _("Outlook")},
            {"name": _("Paint 3D"), "package": "Microsoft.Paint3D", "description": _("Paint 3D")},
            {"name": _("Print 3D"), "package": "Microsoft.Print3D", "description": _("Impressão 3D")},
            {"name": _("Snip & Sketch"), "package": "Microsoft.ScreenSketch", "description": _("Recorte e Esboço")},
            {"name": _("Teams"), "package": "Microsoft.Teams", "description": _("Microsoft Teams")},
            {"name": _("Todos"), "package": "Microsoft.Todos", "description": _("Microsoft To Do")},
            {"name": _("Wallet"), "package": "Microsoft.Wallet", "description": _("Carteira")},
            {"name": _("Windows Alarms"), "package": "Microsoft.WindowsAlarms", "description": _("Alarmes")},
            {"name": _("Windows Calculator"), "package": "Microsoft.WindowsCalculator", "description": _("Calculadora")},
            {"name": _("Windows Clock"), "package": "Microsoft.WindowsClock", "description": _("Relógio")},
        ]

    def _get_ai_components(self) -> List[Dict[str, str]]:
        return [
            {"name": _("Cortana"), "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f'},
            {"name": _("Windows Recall"), "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI" /v DisableAIDataAnalysis /t REG_DWORD /d 1 /f'},
            {"name": _("Copilot"), "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ShowCopilotButton /t REG_DWORD /d 0 /f'},
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
            'del /q /f /s %temp%\\*',
            'del /q /f /s C:\\Windows\\Temp\\*',
            'del /q /f /s C:\\Windows\\Prefetch\\*',
            'del /q /f /s C:\\Windows\\SoftwareDistribution\\Download\\*',
            'cleanmgr /sagerun:1',
        ]

    def get_installed_bloatware(self) -> List[Dict[str, str]]:
        installed = []
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-AppxPackage | Select-Object -ExpandProperty PackageFullName"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            if result.returncode != 0:
                logging.error(_("Erro ao executar PowerShell: {stderr}").format(stderr=result.stderr))
                return installed
            installed_packages = result.stdout.lower()
            for app in self.bloatware_list:
                if app["package"].lower() in installed_packages:
                    installed.append(app)
        except Exception as e:
            logging.error(_("Exceção ao verificar bloatware: {error}").format(error=e))
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
                encoding='utf-8',
                errors='ignore'
            )
            stdout, stderr = proc.communicate(timeout=120)
            if log_callback:
                if stdout:
                    log_callback(stdout)
                if stderr:
                    log_callback(_("ERRO: {stderr}").format(stderr=stderr))
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            if log_callback:
                log_callback(_("Comando excedeu tempo limite e foi encerrado."))
            return False
        except Exception as e:
            if log_callback:
                log_callback(_("Exceção: {error}").format(error=e))
            return False
WIN

# ============================================================================
# core/main.py (FINAL, COM TODAS AS CORREÇÕES)
# ============================================================================
cat > core/main.py << 'MAIN'
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

# ============================================================================
# Classe principal SpeedScan
# ============================================================================
class SpeedScan(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.SO = platform.system()
        self.runner = CommandRunner(self.SO)
        self.hw = HardwareInfo(self.SO, self.runner)
        self.config = self._load_config()
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
        self.result_labels = {}

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

    def _load_config(self):
        if config.CONFIG_FILE.exists():
            try:
                with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                for key, value in config.DEFAULT_CONFIG.items():
                    if key not in cfg:
                        cfg[key] = value
                return cfg
            except Exception as e:
                logging.error(f"Erro ao carregar config: {e}")
                return config.DEFAULT_CONFIG.copy()
        return config.DEFAULT_CONFIG.copy()

    def _save_config(self):
        try:
            with open(config.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Erro ao salvar config: {e}")

    def update_theme_vars(self):
        t = config.THEMES.get(self.config["theme"], config.THEMES["techneon"])
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
            ("📌", self._("Dashboard"), "dashboard"),
            ("⚡", self._("Otimização"), "otimizacao"),
            ("📀", self._("Rede"), "rede"),
            ("📟", self._("Drivers"), "drivers"),
        ]
        level_items = {
            1: [],
            2: [self._("Processos")],
            3: [self._("Processos"), self._("Histórico"), self._("Segurança"), self._("Agente IA"), self._("Limpeza Win")]
        }
        for icon, text, target in nav_items:
            btn = self._sidebar_btn(center, icon, text, target)
            self.sidebar_buttons[target] = btn
        level = 3
        if level >= 2:
            icon_map = {
                self._("Processos"): ("📋", "processos"),
                self._("Histórico"): ("📊", "historico"),
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

    # ----------- Abas -----------
    def _fill_dashboard(self, parent):
        ctk.CTkLabel(parent, text=self._("Dashboard Rotativo"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        self.dashboard = Dashboard(parent, self, fg_color="transparent")
        self.dashboard.pack(fill="both", expand=True)

    def _fill_otimizacao(self, parent):
        ctk.CTkLabel(parent, text=self._("Otimização"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("🗹 Limpeza de Cache"), "cache", False),
            (self._("🗄 Reset de Swap"), "swap", False),
            (self._("🔍 Verificar Erros"), "check", False),
            (self._("🔧 Modo Turbo"), "turbo", False),
            (self._("Steam"), "steam", False),
            (self._("Lutris"), "lutris", False),
            (self._("Heroic Launcher"), "heroic", False),
            (self._("Bottles"), "bottles", False),
            (self._("Wine"), "wine", False),
            (self._("MangoHud"), "mangohud", False),
            (self._("Governor"), "governer", False),
            (self._("📮 Emulador Dolphin"), "dolphin", False),
            (self._("🗑 Limpeza de Navegadores"), "browsers", False),
            (self._("⚙️ Gerenciar Serviços"), "services", False),
            (self._("📋 Análise de Logs"), "logs", False),
            (self._("🗑️ Gerenciar Cookies"), "cookies", False),
            (self._("🔧 Otimizar SSD (TRIM)"), "trim", False),
            (self._("🗄 Reparar Pacotes Quebrados"), "fix_broken", False),
        ]
        level = 3
        if level == 1:
            items = [item for item in items if item[1] not in ["services","logs","cookies","trim","fix_broken"]]
        elif level == 2:
            items = [item for item in items if item[1] not in ["logs","cookies"]]
        ui.create_card_grid(parent, items, "ot", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "ot", self.acc_color, self.toggle_console)
        btn.pack_forget()
        log.pack_forget()
        self.detail_buttons["ot"] = btn
        self.logs["ot"] = log

    def _fill_rede(self, parent):
        ctk.CTkLabel(parent, text=self._("Rede"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("📟 Ping"), "ping", False),
            (self._("📀 Cloudflare DNS"), "1.1.1.1", True),
            (self._("📡 Google DNS"), "8.8.8.8", True),
            (self._("📡 AdGuard DNS"), "94.140.14.14", True),
            (self._("🔍 DNS Automático"), "auto", True),
            (self._("📊 Testar Velocidade"), "speedtest", False),
            (self._("🕸️ Diagnóstico Placa"), "ethtool", False),
            (self._("🔍 Renovar IP"), "dhclient", False),
            (self._("🔓 Portas Abertas"), "ports", False),
            (self._("🌐 TraceRoute"), "traceroute", False),
            (self._("📡 Informações Wi-Fi"), "wifi", False),
            (self._("🔍 Testar DNS"), "testdns", False),
            (self._("🔎 Scanner LAN"), "lanscan", False),
            (self._("🗄️ LANCache"), "lancache", False),
            (self._("📡 Verificar IP Público"), "public_ip", False),
        ]
        level = 3
        if level == 1:
            items = [item for item in items if item[1] not in ["ports","traceroute","ethtool","dhclient","lanscan","lancache"]]
        elif level == 2:
            items = [item for item in items if item[1] not in ["lanscan","lancache"]]
        ping_labels, result_labels = ui.create_card_grid(parent, items, "net", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        self.result_labels = {}
        if result_labels:
            self.result_labels.update(result_labels)
        if ping_labels:
            self.ping_label = ping_labels[0]
        btn, log = ui.add_console(parent, "net", self.acc_color, self.toggle_console)
        btn.pack_forget()
        log.pack_forget()
        self.detail_buttons["net"] = btn
        self.logs["net"] = log

    def _fill_drivers(self, parent):
        ctk.CTkLabel(parent, text=self._("Drivers"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("📮 PCI (Vídeo/Rede)"), "pci", False),
            (self._("🔧 Atualizar Sistema"), "update", False),
            (self._("🖥️ USB Conectados"), "usb", False),
            (self._("📟 Módulos Kernel"), "modules", False),
            (self._("⚙️ CPU Detalhada"), "cpu_info", False),
            (self._("⚙️ Erros de Firmware"), "firmware", False),
            (self._("📮 Drivers de Vídeo"), "video_drv", False),
            (self._("🔍 Drivers de Rede"), "net_drv", False),
            (self._("🔍 Atualizações Automáticas"), "auto_update", False),
        ]
        level = 3
        if level == 1:
            items = [item for item in items if item[1] not in ["modules","cpu_info","firmware","video_drv","net_drv","auto_update"]]
        elif level == 2:
            items = [item for item in items if item[1] not in ["video_drv","net_drv","auto_update"]]
        ui.create_card_grid(parent, items, "drv", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "drv", self.acc_color, self.toggle_console)
        btn.pack_forget()
        log.pack_forget()
        self.detail_buttons["drv"] = btn
        self.logs["drv"] = log

    def _fill_processos(self, parent):
        ctk.CTkLabel(parent, text=self._("Gerenciador de Processos"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        control_frame = ctk.CTkFrame(parent, fg_color="transparent")
        control_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(control_frame, text=self._("Filtrar:"), font=("Inter",12)).pack(side="left", padx=5)
        self.filter_entry = ctk.CTkEntry(control_frame, placeholder_text=self._("Nome do processo"), width=150)
        self.filter_entry.pack(side="left", padx=5)
        self.filter_entry.bind("<KeyRelease>", self._on_filter_change)
        ctk.CTkLabel(control_frame, text=self._("Ordenar por:"), font=("Inter",12)).pack(side="left", padx=5)
        self.sort_var = ctk.StringVar(value="cpu_percent")
        sort_menu = ctk.CTkOptionMenu(control_frame, values=["cpu_percent","memory_percent","name","pid"],
                                       variable=self.sort_var, command=self._on_sort_change, width=100)
        sort_menu.pack(side="left", padx=5)
        self.reverse_var = ctk.BooleanVar(value=True)
        reverse_check = ctk.CTkCheckBox(control_frame, text=self._("Decrescente"), variable=self.reverse_var,
                                         command=self._on_sort_change, onvalue=True, offvalue=False)
        reverse_check.pack(side="left", padx=5)
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
        self.process_text = ctk.CTkTextbox(parent, font=("Courier",10), wrap="none")
        self.process_text.pack(fill="both", expand=True, padx=10, pady=10)
        self._refresh_process_list()

    def _refresh_process_list(self):
        procs = self.proc_manager.get_process_list()
        filtro = self.filter_entry.get().lower() if hasattr(self,'filter_entry') else ""
        if filtro:
            procs = [p for p in procs if filtro in p['name'].lower()]
        sort_key = self.sort_var.get() if hasattr(self,'sort_var') else "cpu_percent"
        reverse = self.reverse_var.get() if hasattr(self,'reverse_var') else True
        procs.sort(key=lambda x: x.get(sort_key,0), reverse=reverse)
        self.process_text.configure(state="normal")
        self.process_text.delete("1.0","end")
        header = "PID     CPU%   MEM%    STATUS NICE USUÁRIO    NOME\n"
        self.process_text.insert("end", header)
        self.process_text.tag_add("header","1.0","1.end")
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

    def _fill_historico(self, parent):
        ctk.CTkLabel(parent, text=self._("Histórico de Desempenho"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        periodo_frame = ctk.CTkFrame(parent, fg_color="transparent")
        periodo_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(periodo_frame, text=self._("Período:"), font=("Inter",12)).pack(side="left", padx=5)
        self.periodo_var = ctk.StringVar(value="1h")
        periodo_menu = ctk.CTkOptionMenu(periodo_frame, values=["1h","6h","12h","24h","7d"],
                                         variable=self.periodo_var, command=self._update_graphs, width=80)
        periodo_menu.pack(side="left", padx=5)
        self.graph_frame = ctk.CTkFrame(parent, fg_color=self.bg_color)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._update_graphs()

    def _update_graphs(self, choice=None):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        periodo_map = {"1h":1,"6h":6,"12h":12,"24h":24,"7d":168}
        hours = periodo_map.get(self.periodo_var.get(),1)
        dados = self.metrics_db.get_last_hours(hours=hours, metrics=['timestamp','cpu','memory','disk_usage'])
        if not dados or len(dados)<2:
            ctk.CTkLabel(self.graph_frame, text=self._("Sem dados suficientes para exibir.")).pack(expand=True)
            return
        times = [d[0] for d in dados]
        cpus = [d[1] for d in dados]
        mems = [d[2] for d in dados]
        disks = [d[3] for d in dados]
        fig = Figure(figsize=(8,6), dpi=100)
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313)
        ax1.plot(times, cpus, label='CPU %', color='#ff6b6b', linewidth=1.5)
        ax1.set_ylabel('CPU %'); ax1.set_ylim(0,100); ax1.legend(); ax1.grid(True, linestyle='--', alpha=0.6)
        ax2.plot(times, mems, label='RAM %', color='#4ecdc4', linewidth=1.5)
        ax2.set_ylabel('RAM %'); ax2.set_ylim(0,100); ax2.legend(); ax2.grid(True, linestyle='--', alpha=0.6)
        ax3.plot(times, disks, label='Disco %', color='#ffe66d', linewidth=1.5)
        ax3.set_xlabel(self._("Tempo (segundos desde início)")); ax3.set_ylabel('Disco %'); ax3.set_ylim(0,100)
        ax3.legend(); ax3.grid(True, linestyle='--', alpha=0.6)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _fill_seguranca(self, parent):
        ctk.CTkLabel(parent, text=self._("Segurança do Sistema"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        items = [
            (self._("🛡️ Portas Abertas"), "ports", False),
            (self._("🛡️ Firewall"), "firewall", False),
            (self._("🗄 Atualizações de Segurança"), "sec_updates", False),
        ]
        level = self.config.get("expert_level",1)
        if level == 1:
            items = [item for item in items if item[1] not in ["ports","sec_updates"]]
        ui.create_card_grid(parent, items, "sec", self.acc_color, self.bg_color, self.text_color, self.run_card_action)
        btn, log = ui.add_console(parent, "sec", self.acc_color, self.toggle_console)
        btn.pack_forget()
        log.pack_forget()
        self.detail_buttons["sec"] = btn
        self.logs["sec"] = log

    def _fill_agente(self, parent):
        ctk.CTkLabel(parent, text=self._("Agente de IA"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        self.chat_frame = ChatFrame(parent, self, fg_color="transparent")
        self.chat_frame.pack(fill="both", expand=True)

    def _fill_config(self, parent):
        ctk.CTkLabel(parent, text=self._("Configurações"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,30))
        f_user = ctk.CTkFrame(parent, fg_color="transparent")
        f_user.pack(fill="x", pady=5)
        ctk.CTkLabel(f_user, text=self._("Nome de usuário:"), font=("Inter",12)).pack(anchor="w")
        self.entry_user = ctk.CTkEntry(f_user, placeholder_text=self._("Seu nome"), width=200)
        self.entry_user.pack(anchor="w", pady=2)
        self.entry_user.insert(0, self.config.get("username",""))
        f_lang = ctk.CTkFrame(parent, fg_color="transparent")
        f_lang.pack(fill="x", pady=5)
        ctk.CTkLabel(f_lang, text=self._("Idioma:"), font=("Inter",12)).pack(anchor="w")
        lang_values = list(config.LANGUAGES.values())
        self.lang_var = ctk.StringVar(value=config.LANGUAGES.get(self.config.get("language","pt_BR"),"Português Brasileiro"))
        ctk.CTkOptionMenu(f_lang, values=lang_values, variable=self.lang_var, width=200).pack(anchor="w", pady=2)
        f_scale = ctk.CTkFrame(parent, fg_color="transparent")
        f_scale.pack(fill="x", pady=5)
        ctk.CTkLabel(f_scale, text=self._("Escala da interface:"), font=("Inter",12)).pack(anchor="w")
        scale_values = list(config.SCALES.values())
        self.scale_var = ctk.StringVar(value=config.SCALES.get(self.config.get("ui_scale","auto"),"Automático"))
        ctk.CTkOptionMenu(f_scale, values=scale_values, variable=self.scale_var, width=200).pack(anchor="w", pady=2)
        f_theme = ctk.CTkFrame(parent, fg_color="transparent")
        f_theme.pack(fill="x", pady=5)
        ctk.CTkLabel(f_theme, text=self._("Tema:"), font=("Inter",12)).pack(anchor="w")
        theme_names = ["Still", "Black Neon", "Clean Snow", "TechNeon"]
        self.theme_var = ctk.StringVar(value=theme_names[0])
        current_theme = self.config.get("theme","techneon")
        if current_theme == "grey":
            self.theme_var.set(theme_names[0])
        elif current_theme == "dark":
            self.theme_var.set(theme_names[1])
        elif current_theme == "light":
            self.theme_var.set(theme_names[2])
        elif current_theme == "techneon":
            self.theme_var.set(theme_names[3])
        ctk.CTkOptionMenu(f_theme, values=theme_names, variable=self.theme_var, width=200).pack(anchor="w", pady=2)
        f_tab = ctk.CTkFrame(parent, fg_color="transparent")
        f_tab.pack(fill="x", pady=5)
        self.tab_var = ctk.BooleanVar(value=self.config.get("open_file_in_tab",False))
        ctk.CTkCheckBox(f_tab, text=self._("Abrir arquivos em nova guia"), variable=self.tab_var,
                         onvalue=True, offvalue=False).pack(anchor="w")
        f_level = ctk.CTkFrame(parent, fg_color="transparent")
        f_level.pack(fill="x", pady=5)
        ctk.CTkLabel(f_level, text=self._("Nível de conhecimento:"), font=("Inter",12)).pack(anchor="w")
        self.level_var = ctk.IntVar(value=self.config.get("expert_level",1))
        r1 = ctk.CTkRadioButton(f_level, text=self._("Iniciante"), variable=self.level_var, value=1, cursor="hand2")
        r1.pack(anchor="w", pady=2)
        r2 = ctk.CTkRadioButton(f_level, text=self._("Intermediário"), variable=self.level_var, value=2, cursor="hand2")
        r2.pack(anchor="w", pady=2)
        r3 = ctk.CTkRadioButton(f_level, text=self._("Avançado"), variable=self.level_var, value=3, cursor="hand2")
        r3.pack(anchor="w", pady=2)
        f_sched = ctk.CTkFrame(parent, fg_color="transparent")
        f_sched.pack(fill="x", pady=10)
        self.sched_enabled = ctk.BooleanVar(value=self.config.get("schedule",{}).get("enabled",False))
        ctk.CTkCheckBox(f_sched, text=self._("Habilitar agendamento automático"), variable=self.sched_enabled,
                         onvalue=True, offvalue=False).pack(anchor="w")
        btn_apply = ctk.CTkButton(parent, text=self._("Aplicar"), fg_color=self.acc_color,
                                   command=self.apply_config, width=150)
        btn_apply.pack(pady=20)

    def apply_config(self):
        try:
            self.config["username"] = self.entry_user.get()
            for k,v in config.LANGUAGES.items():
                if v == self.lang_var.get():
                    self.config["language"] = k
                    break
            for k,v in config.SCALES.items():
                if v == self.scale_var.get():
                    self.config["ui_scale"] = k
                    break
            theme_map = {"Still": "grey", "Black Neon": "dark", "Clean Snow": "light", "TechNeon": "techneon"}
            self.config["theme"] = theme_map.get(self.theme_var.get(), "techneon")
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

    def _fill_sobre(self, parent):
        ctk.CTkLabel(parent, text=self._("Sobre o SpeedScan"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        card = ctk.CTkFrame(parent, fg_color=self.light_bg, corner_radius=15, border_width=2, border_color=self.acc_color)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        info = (
            self._("⚡ SpeedScan") + "\n\n"
            + self._("Versão") + " " + config.VERSION + "\n\n"
            + self._("Desenvolvedor: Ewerton Vasconcelos") + "\n"
            + self._("Tecnologias: Python, CustomTkinter, psutil") + "\n"
            + self._("Repositório: github.com/ewertonvasconcelos/speedscan") + "\n\n"
            + self._("Este software está em fase de desenvolvimento.") + "\n\n"
            + self._("Principais funcionalidades:") + "\n"
            + self._("• Dashboard com widgets personalizáveis") + "\n"
            + self._("• Monitoramento de CPU, RAM, disco, GPU e temperatura") + "\n"
            + self._("• Otimização: cache, swap, turbo e limpeza de navegadores") + "\n"
            + self._("• Rede: ping, DNS, teste de velocidade, scanner LAN, LANCache") + "\n"
            + self._("• Diagnóstico de drivers e hardware") + "\n"
            + self._("• Gerenciador de processos com ações") + "\n"
            + self._("• Histórico de desempenho com gráficos") + "\n"
            + self._("• Verificações de segurança (portas, firewall, atualizações)") + "\n"
            + self._("• IA proativa com sugestões e chat local") + "\n"
            + self._("• Gerenciador de cookies seletivo") + "\n"
            + self._("• Lixeira interna para arquivos deletados") + "\n"
            + self._("• Agendamento automático de tarefas") + "\n"
            + self._("• Níveis de expertise (Iniciante, Intermediário, Avançado)") + "\n"
            + self._("• Tooltips explicativos") + "\n"
            + self._("• Temas personalizáveis") + "\n\n"
            + "© 2026 Ewerton Vasconcelos. " + self._("Todos os direitos reservados.")
        )
        label_info = ctk.CTkLabel(card, text=info, font=("Inter",12), justify="left", text_color=self.text_color)
        label_info.pack(pady=20, padx=30, fill="both", expand=True)

    def _fill_windows_cleaner(self, parent):
        if self.SO != "Windows" or self.windows_cleaner is None:
            ctk.CTkLabel(parent, text=self._("🧹 Este módulo é exclusivo para Windows!\n\nExecute o SpeedScan em um sistema Windows para acessar estas funcionalidades."),
                         font=("Inter",20), text_color=self.acc_color, justify="center").pack(expand=True)
            return
        ctk.CTkLabel(parent, text=self._("Limpeza do Windows"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        left_frame = ctk.CTkFrame(main_frame, fg_color=self.bg_color, corner_radius=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(left_frame, text=self._("Bloatware Instalado"), font=("Inter",16,"bold"),
                     text_color=self.acc_color).pack(anchor="w", padx=10, pady=(10,5))
        self.bloatware_vars = {}
        installed = self.windows_cleaner.get_installed_bloatware()
        if not installed:
            ctk.CTkLabel(left_frame, text=self._("Nenhum bloatware conhecido encontrado."),
                         font=("Inter",12)).pack(anchor="w", padx=20, pady=5)
        else:
            scroll_frame = ctk.CTkScrollableFrame(left_frame, height=200, fg_color="transparent")
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
            for app in installed:
                var = ctk.BooleanVar()
                self.bloatware_vars[app["package"]] = var
                cb = ctk.CTkCheckBox(scroll_frame, text=app["name"], variable=var,
                                      onvalue=True, offvalue=False, cursor="hand2")
                cb.pack(anchor="w", pady=2)
        btn_remove = ctk.CTkButton(left_frame, text=self._("Remover Selecionados"),
                                    command=self._remove_selected_bloatware,
                                    fg_color=self.acc_color, width=150)
        btn_remove.pack(pady=10)
        right_frame = ctk.CTkFrame(main_frame, fg_color=self.bg_color, corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)
        ctk.CTkLabel(right_frame, text=self._("Ações de Sistema"), font=("Inter",16,"bold"),
                     text_color=self.acc_color).pack(anchor="w", padx=10, pady=(10,5))
        self.telemetry_var = ctk.BooleanVar()
        ctk.CTkCheckBox(right_frame, text=self._("Desabilitar Telemetria"), variable=self.telemetry_var,
                         onvalue=True, offvalue=False, cursor="hand2").pack(anchor="w", padx=20, pady=2)
        self.ai_vars = {}
        for comp in self.windows_cleaner.ai_components:
            var = ctk.BooleanVar()
            self.ai_vars[comp["name"]] = var
            ctk.CTkCheckBox(right_frame, text=self._("Desabilitar {name}").format(name=comp["name"]),
                             variable=var, onvalue=True, offvalue=False, cursor="hand2").pack(anchor="w", padx=20, pady=2)
        self.cleanup_var = ctk.BooleanVar()
        ctk.CTkCheckBox(right_frame, text=self._("Limpar arquivos temporários e cache"), variable=self.cleanup_var,
                         onvalue=True, offvalue=False, cursor="hand2").pack(anchor="w", padx=20, pady=2)
        btn_exec = ctk.CTkButton(right_frame, text=self._("Executar Ações Selecionadas"),
                                   command=self._execute_windows_cleanup,
                                   fg_color=self.acc_color, width=200)
        btn_exec.pack(pady=20)
        self.windows_console = ctk.CTkTextbox(parent, height=150, fg_color="#1e1e1e", text_color="#ffffff",
                                               font=("Consolas",10), corner_radius=10)
        self.windows_console.pack(fill="x", padx=10, pady=(0,10))

    def _remove_selected_bloatware(self):
        selected = [pkg for pkg, var in self.bloatware_vars.items() if var.get()]
        if not selected:
            self.show_toast(self._("Nenhum bloatware selecionado."))
            return
        self.windows_console.delete("1.0","end")
        self.windows_console.insert("end", self._("Removendo bloatware...\n"))
        for pkg in selected:
            self.windows_console.insert("end", self._("Removendo {pkg}...\n").format(pkg=pkg))
            success = self.windows_cleaner.remove_package(pkg, lambda msg: self.windows_console.insert("end", msg+"\n"))
            self.windows_console.insert("end", self._("✓ {pkg} removido.\n") if success else self._("✗ Falha ao remover {pkg}.\n").format(pkg=pkg))
        self.windows_console.see("end")
        self.show_toast(self._("Remoção concluída."))

    def _execute_windows_cleanup(self):
        self.windows_console.delete("1.0","end")
        self.windows_console.insert("end", self._("Executando ações...\n"))
        if self.telemetry_var.get():
            self.windows_console.insert("end", self._("Desabilitando telemetria...\n"))
            success = self.windows_cleaner.disable_telemetry(lambda msg: self.windows_console.insert("end", msg+"\n"))
            self.windows_console.insert("end", self._("Telemetria desabilitada.\n") if success else self._("Falha ao desabilitar telemetria.\n"))
        for name, var in self.ai_vars.items():
            if var.get():
                self.windows_console.insert("end", self._("Desabilitando {name}...\n").format(name=name))
                success = self.windows_cleaner.disable_ai_component(name, lambda msg: self.windows_console.insert("end", msg+"\n"))
                self.windows_console.insert("end", self._("{name} desabilitado.\n") if success else self._("Falha ao desabilitar {name}.\n").format(name=name))
        if self.cleanup_var.get():
            self.windows_console.insert("end", self._("Limpando arquivos temporários...\n"))
            success = self.windows_cleaner.run_cleanup(lambda msg: self.windows_console.insert("end", msg+"\n"))
            self.windows_console.insert("end", self._("Limpeza concluída.\n") if success else self._("Falha na limpeza.\n"))
        self.windows_console.see("end")
        self.show_toast(self._("Ações concluídas."))

    # ============================================================================
    # Execução de comandos
    # ============================================================================
    def run_card_action(self, cmd, tag, is_dns):
        log = self.logs.get(tag)
        if not log:
            return
        log.delete("1.0", "end")
        btn = self.detail_buttons.get(tag)
        if btn and btn.winfo_ismapped():
            btn.pack_forget()
        self.consoles_visible[tag] = False
        threading.Thread(target=self._execute_command, args=(cmd, log, tag, is_dns), daemon=True).start()

    def _execute_command(self, cmd, log, tag, is_dns):
        if is_dns:
            self._change_dns(cmd, log)
            self._after_command(tag, log)
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
            "governer": self.action_handler.run_governor_config,
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
                if cmd == "ping":
                    method(log, tag)
                else:
                    method(log)
                    self._after_command(tag, log)
            except Exception as e:
                log.insert("end", self._("Erro ao executar comando: {e}\n").format(e=e))
                self._after_command(tag, log)
        else:
            log.insert("end", self._("Comando não reconhecido: {cmd}\n").format(cmd=cmd))
            self._after_command(tag, log)

    def _after_command(self, tag, log):
        conteudo = log.get("1.0", "end-1c")
        if len(conteudo) > 200:
            btn = self.detail_buttons.get(tag)
            if btn:
                btn.configure(text="Detalhes ▼")
                if not btn.winfo_ismapped():
                    btn.pack(anchor="e", padx=5, pady=5)

    # ---------- Métodos auxiliares ----------
    def _run_ping(self, log, tag=None):
        import subprocess
        log.insert("end", self._("Executando ping para google.com (5 minutos)...\n"))
        try:
            result = subprocess.run(["ping", "-c", "300", "-i", "1", "google.com"], capture_output=True, text=True, timeout=310)
            output = result.stdout
            log.insert("end", output)
            lines = output.splitlines()
            times = []
            for line in lines:
                if "time=" in line:
                    try:
                        time_str = line.split("time=")[1].split(" ")[0]
                        times.append(float(time_str))
                    except:
                        pass
            if times:
                avg = sum(times) / len(times)
                ping_label = self.result_labels.get("ping")
                if ping_label:
                    ping_label.configure(text=f"{avg:.1f} ms")
            if len(output) > 200:
                btn = self.detail_buttons.get("net")
                if btn and not btn.winfo_ismapped():
                    btn.configure(text="Detalhes ▼")
                    btn.pack(anchor="e", padx=5, pady=5)
            else:
                btn = self.detail_buttons.get("net")
                if btn and btn.winfo_ismapped():
                    btn.pack_forget()
        except Exception as e:
            log.insert("end", self._("Erro no ping: {e}\n").format(e=e))
            self._after_command("net", log)

    def _run_speedtest(self, log):
        log.insert("end", self._("Executando teste de velocidade...\n"))
        def callback(res):
            log.insert("end", self.speed_tester.format_result(res) + "\n")
            self._after_command("net", log)
        self.speed_tester.run_test(callback)

    def _run_ethtool(self, log):
        log.insert("end", self._("Executando ethtool...\n"))
        self._run_subprocess(["ethtool", "eth0"], log)
        self._after_command("net", log)

    def _run_dhclient(self, log):
        log.insert("end", self._("Renovando IP via dhclient...\n"))
        self._run_subprocess(["sudo", "dhclient", "-v"], log, use_sudo=True)
        self._after_command("net", log)

    def _run_ports(self, log):
        log.insert("end", self._("Escaneando portas abertas...\n"))
        ports = self.security_scanner.scan_open_ports()
        for p in ports:
            log.insert("end", p + "\n")
        self._after_command("net", log)

    def _run_traceroute(self, log):
        log.insert("end", self._("Executando traceroute para google.com...\n"))
        self._run_subprocess(["traceroute", "google.com"], log)
        self._after_command("net", log)

    def _run_wifi(self, log):
        log.insert("end", self._("Informações Wi-Fi...\n"))
        self._run_subprocess(["iwconfig"], log)
        self._after_command("net", log)

    def _run_testdns(self, log):
        log.insert("end", self._("Testando DNS (google.com)...\n"))
        self._run_subprocess(["nslookup", "google.com"], log)
        self._after_command("net", log)

    def _run_lanscan(self, log):
        log.insert("end", self._("Escaneando rede local...\n"))
        devices = self.lan_scanner.scan_network(progress_callback=lambda i,t,ip,alive: None)
        for d in devices:
            log.insert("end", f"{d['ip']} - {d['mac']} - {d['hostname']} - {d['vendor']}\n")
        self._after_command("net", log)

    def _run_lancache(self, log):
        log.insert("end", self._("Verificando LANCache...\n"))
        log.insert("end", self.lan_cache.get_status() + "\n")
        self._after_command("net", log)

    def _run_public_ip(self, log):
        import requests
        log.insert("end", self._("Obtendo IP público...\n"))
        try:
            ip = requests.get("https://api.ipify.org", timeout=5).text
            log.insert("end", self._("IP público: {ip}\n").format(ip=ip))
        except:
            log.insert("end", self._("Erro ao obter IP público.\n"))
        self._after_command("net", log)

    def _run_pci(self, log):
        self._run_subprocess(["lspci"], log)
        self._after_command("drv", log)

    def _run_update(self, log):
        log.insert("end", self._("Atualizando lista de pacotes...\n"))
        self._run_subprocess(["sudo", "apt", "update"], log, use_sudo=True)
        self._after_command("drv", log)

    def _run_usb(self, log):
        self._run_subprocess(["lsusb"], log)
        self._after_command("drv", log)

    def _run_modules(self, log):
        self._run_subprocess(["lsmod"], log)
        self._after_command("drv", log)

    def _run_cpu_info(self, log):
        try:
            with open("/proc/cpuinfo") as f:
                log.insert("end", f.read())
        except:
            log.insert("end", self._("Não foi possível ler /proc/cpuinfo.\n"))
        self._after_command("drv", log)

    def _run_firmware(self, log):
        self._run_subprocess(["dmesg", "|", "grep", "-i", "firmware"], log, shell=True)
        self._after_command("drv", log)

    def _run_video_drv(self, log):
        self._run_subprocess(["lspci", "|", "grep", "-i", "vga"], log, shell=True)
        self._after_command("drv", log)

    def _run_net_drv(self, log):
        self._run_subprocess(["lspci", "|", "grep", "-i", "network"], log, shell=True)
        self._after_command("drv", log)

    def _run_auto_update(self, log):
        log.insert("end", self._("Configurando atualizações automáticas (não implementado).\n"))
        self._after_command("drv", log)

    def _run_firewall(self, log):
        log.insert("end", self._("Verificando firewall...\n"))
        status = self.security_scanner.check_firewall_status()
        log.insert("end", status)
        self._after_command("sec", log)

    def _run_sec_updates(self, log):
        log.insert("end", self._("Verificando atualizações de segurança...\n"))
        updates = self.security_scanner.check_security_updates()
        for u in updates:
            log.insert("end", u + "\n")
        self._after_command("sec", log)

    def _change_dns(self, dns_ip, log):
        log.insert("end", self._("Alterando DNS para {dns_ip}...\n").format(dns_ip=dns_ip))
        if hasattr(self, 'action_mapper'):
            cmd = self.action_mapper.dns_command(dns_ip)
            if cmd:
                self._run_subprocess(cmd, log, shell=True)
            else:
                log.insert("end", self._("Não foi possível gerar comando DNS para este SO.\n"))
        else:
            log.insert("end", self._("ActionMapper não disponível.\n"))
        self._after_command("net", log)

    def _run_subprocess(self, cmd, log, use_sudo=False, shell=False):
        import subprocess
        try:
            if use_sudo and self.SO == "Linux":
                if isinstance(cmd, list):
                    cmd = ["sudo"] + cmd
                else:
                    cmd = "sudo " + cmd
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=shell)
            if result.stdout:
                log.insert("end", result.stdout)
            if result.stderr:
                log.insert("end", self._("ERRO: {stderr}\n").format(stderr=result.stderr))
        except Exception as e:
            log.insert("end", self._("Erro ao executar comando: {e}\n").format(e=e))

    # ============================================================================
    # Métodos utilitários
    # ============================================================================
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

    # ============================================================================
    # Gerenciamento da janela
    # ============================================================================
    def _check_first_run(self):
        if self.config == config.DEFAULT_CONFIG:
            wizard = FirstRunWizard(self, self.config)
            self.wait_window(wizard)
            self.config = self._load_config()
            self.update_theme_vars()
            self._save_config()
            self.show_toast(self._("Configurações iniciais salvas! Algumas alterações podem exigir reinicialização."))

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
            logging.error(_("Erro ao salvar estado da janela: {error}").format(error=e))
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

    # ============================================================================
    # Widgets do Dashboard
    # ============================================================================
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
            result = subprocess.run(['lspci', '|', 'grep', '-i', 'vga'], capture_output=True, text=True, shell=True)
            text = result.stdout.strip().split('\n')[0][:50] if result.stdout else self._("N/A")
        except:
            text = self._("N/A")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_disks(self, frame, tag):
        import psutil
        disk = psutil.disk_usage('/')
        text = f"{disk.percent}% ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)"
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

    # ============================================================================
    # Placeholders
    # ============================================================================
    def _update_ai_suggestions(self):
        pass

    def _check_process_queue(self):
        pass

    # ============================================================================
    # Métodos para controle dos consoles
    # ============================================================================
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
            btn.configure(text="Detalhes ▲")
            self.consoles_visible[tag] = True

    def _show_details_button(self, tag):
        btn = self.detail_buttons.get(tag)
        if btn and not btn.winfo_ismapped():
            btn.configure(fg_color=self.acc_color, text_color="white")
            btn.pack(anchor="e", padx=5)
        if btn:
            btn.configure(text="Detalhes ▼")

if __name__ == "__main__":
    app = SpeedScan()
    app.mainloop()
MAIN

echo "✅ Todos os módulos foram restaurados com as correções finais."
echo "Execute 'python -m core.main' para iniciar o SpeedScan."
