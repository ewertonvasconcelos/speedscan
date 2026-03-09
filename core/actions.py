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
    """Runs commands on the native shell, with optional sudo privileges."""

    def __init__(self, so):
        """Initialize with the operating system.

        Args:
            so (str): Operating system (Linux, Windows, Darwin).
        """
        self.so = so

    def run(self, cmd, use_sudo=False, parent=None):
        """Execute a command and return a subprocess.Popen object.

        Args:
            cmd (str or list): Command to execute.
            use_sudo (bool): If True, attempt to run with administrative privileges.
            parent: Optional parent window (for dialogs).

        Returns:
            subprocess.Popen object or None on error.
        """
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
    """Maps generic actions to platform-specific commands."""

    def __init__(self, so, runner, turbo_active=False):
        """Initialize with system info and runner.

        Args:
            so (str): Operating system.
            runner (CommandRunner): Instance for executing commands.
            turbo_active (bool): Whether turbo mode is enabled (may affect commands).
        """
        self.so = so
        self.runner = runner
        self.turbo_active = turbo_active

    def get_command(self, action):
        """Return the command string for a given action and current OS.

        Args:
            action (str): The action name (e.g., "cache", "swap").

        Returns:
            str or None: Command string or None if unsupported.
        """
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
                "Linux": "sudo dmseg | grep -i firmware",
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
        """Return a command to change the system DNS to the given IP.

        Args:
            dns_ip (str): IP address of the desired DNS server.

        Returns:
            str or None: Command to run or None if unsupported.
        """
        if self.so == "Linux":
            return f"echo 'nameserver {dns_ip}' | sudo tee /etc/resolv.conf"
        elif self.so == "Windows":
            return f"netsh interface ip set dns name='Ethernet' static {dns_ip}"
        elif self.so == "Darwin":
            return f"networksetup -setdnsservers Wi-Fi {dns_ip}"
        return None


class ActionHandler:
    """Executes the actions of the cards: cache cleaning, swap reset, error checking, etc."""

    def __init__(self, app):
        self.app = app

    # ----- Utility to run Linux commands with sudo -----
    def _run_linux_command(self, cmd, log, use_sudo=True):
        proc = self.app.runner.run(cmd, use_sudo=use_sudo, parent=self.app)
        if proc:
            for line in proc.stdout:
                self.app.after(0, lambda l=line: log.insert("end", l))
            proc.wait()
            return True
        return False

    # ----- Otimização tab cards -----
    def run_cache_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache de memória...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        success = self._run_linux_command(["sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"], log, use_sudo=True)
        log.insert("end", "✅ Cache limpo com sucesso.\n" if success else "❌ Erro ao limpar cache.\n")

    def run_swap_reset(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔄 Resetando swap...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "swapoff", "-a"], log, use_sudo=True)
        self._run_linux_command(["sudo", "swapon", "-a"], log, use_sudo=True)
        log.insert("end", "✅ Swap resetado.\n")

    def run_fs_check(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔍 Verificando erros no sistema de arquivos...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "fsck", "-A", "-R", "-y"], log, use_sudo=True)
        log.insert("end", "✅ Verificação concluída.\n")

    def run_turbo_mode(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔥 Ativando modo turbo (ajusta governador para performance)...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "cpupower", "frequency-set", "-g", "performance"], log, use_sudo=True)
        log.insert("end", "✅ Modo turbo ativado.\n")

    def run_steam_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Steam...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
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
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        path = os.path.expanduser("~/.local/share/lutris")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Lutris limpo.\n")

    def run_heroic_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Heroic Launcher...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        path = os.path.expanduser("~/.config/heroic/cache")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Heroic limpo.\n")

    def run_bottles_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Bottles...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        path = os.path.expanduser("~/.local/share/bottles")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Bottles limpo.\n")

    def run_wine_clean(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🧹 Limpando cache do Wine...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        path = os.path.expanduser("~/.wine")
        if os.path.exists(path):
            self._run_linux_command(["rm", "-rf", f"{path}/*"], log, use_sudo=False)
        log.insert("end", "✅ Cache do Wine limpo.\n")

    def run_mangohud_config(self, log):
        log.delete("1.0", "end")
        log.insert("end", "⚙️ Configurando MangoHud...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        if self._run_linux_command(["which", "mangohud"], log, use_sudo=False):
            log.insert("end", "✅ MangoHud já está instalado.\n")
        else:
            log.insert("end", "❌ MangoHud não encontrado. Instale com: sudo apt install mangohud\n")

    def run_governor_config(self, log):
        log.delete("1.0", "end")
        log.insert("end", "⚙️ Configurando governador da CPU...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
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
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
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
        log.insert("end", "🍪 Gerenciador de Cookies\n" + "="*40 + "\n")
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
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "fstrim", "-v", "/"], log, use_sudo=True)
        log.insert("end", "✅ TRIM concluído.\n")

    def run_fix_broken(self, log):
        log.delete("1.0", "end")
        log.insert("end", "🔄 Reparando pacotes quebrados...\n")
        if self.app.SO != "Linux":
            log.insert("end", "⚠️ Operação apenas para Linux.\n")
            return
        self._run_linux_command(["sudo", "apt", "--fix-broken", "install"], log, use_sudo=True)
        log.insert("end", "✅ Reparo concluído.\n")

    # ----- Special commands (for cards not directly mapped) -----
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
