from core import config
#!/usr/bin/env python3
import logging
# Módulo de coleta de informações de hardware
# Versão 1.0.0

import platform
import psutil
import subprocess
import re
import time

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
            except:
                pass
            return "Linux"
        elif self.so == "Windows":
            return platform.win32_ver()[0] or "Windows"
        elif self.so == "Darwin":
            return f"macOS {platform.mac_ver()[0]}"
        return self.so

    def get_cpu(self):
        try:
            if self.so == "Linux":
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":")[1].strip()
            elif self.so == "Windows":
                return platform.processor()
            elif self.so == "Darwin":
                out = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True)
                return out.stdout.strip()
        except:
            pass
        return f"{psutil.cpu_count()} núcleos"

    def get_ram(self):
        try:
            mem = psutil.virtual_memory()
            total = mem.total // (1024**3)
            usado = mem.used // (1024**3)
            return f"{usado} GB / {total} GB"
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
                out = subprocess.run(["wmic", "path", "win32_videocontroller", "get", "name"], capture_output=True, text=True)
                lines = out.stdout.splitlines()
                if len(lines) >= 2:
                    return lines[1].strip()
            elif self.so == "Darwin":
                out = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True)
                for line in out.stdout.splitlines():
                    if "Chipset Model" in line:
                        return line.split(":")[1].strip()
        except:
            pass
        return "Desconhecida"

    def get_disks_detailed(self):
        try:
            partitions = psutil.disk_partitions()
            devices = {}
            for p in partitions:
                device = p.device
                physical_disk = re.sub(r'\d+$', '', device)
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    if physical_disk not in devices:
                        devices[physical_disk] = usage.percent
                except:
                    pass
            disk_info = [f"{dev} {percent}%" for dev, percent in devices.items()]
            return ", ".join(disk_info) if disk_info else "N/A"
        except Exception as e:
            logging.error(f"Erro ao obter discos: {e}")
            return "N/A"

    def get_uptime(self):
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "N/A"

    def get_battery(self):
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = round(battery.percent, 1)
                plugged = "Conectado" if battery.power_plugged else "Desconectado"
                return f"{percent}% ({plugged})"
            else:
                return "Sem bateria"
        except:
            return "N/A"
