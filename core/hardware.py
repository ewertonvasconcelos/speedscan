# core/hardware.py
import platform
import psutil
import subprocess
import time
from datetime import datetime
from functools import lru_cache

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
        disks = []
        for part in psutil.disk_partitions():
            if part.fstype and not part.mountpoint.startswith("/snap/"):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append(f"{part.device} ({usage.total//1073741824}G, usado {usage.used//1073741824}G)")
                except:
                    continue
        return "\n".join(disks[:3]) if disks else "Nenhum disco detectado"

    def get_uptime(self):
        return str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time())))

    def get_battery(self):
        bat = psutil.sensors_battery()
        return f"{bat.percent:.1f}%" if bat else "AC Power"
