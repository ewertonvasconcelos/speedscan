# core/hardware.py
import platform
import psutil
import subprocess
import time
import json
from datetime import datetime, timedelta
from functools import lru_cache
import os

class HardwareInfo:
    """Coleta informações de hardware de forma unificada com fallbacks."""
    def __init__(self, so, runner):
        self.so = so
        self.runner = runner

    @lru_cache(maxsize=1)
    def get_distro(self):
        if self.so == "Linux":
            out = self.runner.check_output("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2")
            return out.strip('"') if out else "Linux"
        return platform.system() + " " + platform.release()

    @lru_cache(maxsize=1)
    def get_cpu(self):
        try:
            if self.so == "Linux":
                out = self.runner.check_output("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2")
                return out or f"{psutil.cpu_count()} núcleos"
            elif self.so == "Windows":
                out = self.runner.check_output("wmic cpu get name")
                return out or f"{psutil.cpu_count()} núcleos"
            elif self.so == "Darwin":
                out = self.runner.check_output("sysctl -n machdep.cpu.brand_string")
                return out or f"{psutil.cpu_count()} núcleos"
        except:
            return f"{psutil.cpu_count()} núcleos"

    def get_ram(self):
        mem = psutil.virtual_memory()
        return f"{mem.used//1048576} MB / {mem.total//1048576} MB ({mem.percent}%)"

    @lru_cache(maxsize=1)
    def get_gpu(self):
        try:
            if self.so == "Linux":
                return self.runner.check_output("lspci | grep -i 'vga\\|3d' | cut -d: -f3-") or "Não detectado"
            elif self.so == "Windows":
                return self.runner.check_output("wmic path win32_VideoController get name") or "Não detectado"
            elif self.so == "Darwin":
                return self.runner.check_output("system_profiler SPDisplaysDataType | grep Chipset") or "Não detectado"
        except:
            return "Não detectado"

    def get_disks_detailed(self):
        """Retorna uma lista de discos físicos com tamanho total e espaço usado, sem duplicações."""
        try:
            # Tenta usar lsblk para obter discos físicos (mais limpo)
            if self.so == "Linux" and self.runner.exists("lsblk"):
                output = self.runner.check_output("lsblk -d -o NAME,SIZE,MODEL,TYPE -J 2>/dev/null")
                if output:
                    data = json.loads(output)
                    disks = []
                    for disk in data.get('blockdevices', []):
                        if disk.get('type') == 'disk':
                            name = disk.get('name')
                            size = disk.get('size', '0B')
                            model = disk.get('model', '')
                            # Tenta obter uso do disco (não é trivial, podemos mostrar apenas tamanho)
                            disks.append(f"{model} ({name}) - {size}")
                    if disks:
                        return "\n".join(disks[:3])  # limita a 3 discos
            # Fallback: usa psutil mas filtra pontos de montagem irrelevantes
            exclude = ('/snap', '/boot', '/sys', '/proc', '/dev', '/run')
            seen = set()
            disks = []
            for part in psutil.disk_partitions():
                if part.mountpoint.startswith(exclude):
                    continue
                if part.device in seen:
                    continue
                seen.add(part.device)
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    total_gb = usage.total // 1073741824
                    used_gb = usage.used // 1073741824
                    disks.append(f"{part.device} ({total_gb}G, usado {used_gb}G)")
                except:
                    continue
            return "\n".join(disks[:3]) if disks else "Nenhum disco detectado"
        except Exception as e:
            return f"Erro ao ler discos: {e}"

    def get_uptime(self):
        return str(timedelta(seconds=int(time.time() - psutil.boot_time())))

    def get_battery(self):
        bat = psutil.sensors_battery()
        return f"{bat.percent:.1f}%" if bat else "AC Power"
