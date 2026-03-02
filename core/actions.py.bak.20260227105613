# core/actions.py
import subprocess
import os

class CommandRunner:
    """Executa comandos com verificação de existência e tratamento de erros."""
    def __init__(self, so):
        self.so = so

    def exists(self, cmd):
        """Verifica se um comando existe no sistema."""
        if self.so == "Windows":
            return subprocess.run(f"where {cmd}", shell=True, capture_output=True).returncode == 0
        return subprocess.run(f"which {cmd}", shell=True, capture_output=True).returncode == 0

    def run(self, cmd, use_sudo=False, timeout=None):
        """Executa um comando e retorna o processo (para leitura em tempo real)."""
        if self.so == "Linux" and use_sudo and "sudo" in cmd:
            full_cmd = f"pkexec bash -c '{cmd}'"
        else:
            full_cmd = cmd
        try:
            proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True)
            return proc
        except Exception as e:
            return None

    def check_output(self, cmd):
        """Executa um comando e retorna a saída (string) ou None."""
        try:
            return subprocess.check_output(cmd, shell=True, text=True).strip()
        except:
            return None

class ActionMapper:
    """Mapeia comandos simbólicos para comandos reais baseados no SO."""
    def __init__(self, so, runner, turbo_active=False):
        self.so = so
        self.runner = runner
        self.turbo_active = turbo_active

    def get_command(self, symbolic, **kwargs):
        """Retorna o comando real para um dado simbólico."""
        # Otimização
        if symbolic == "cache":
            if self.so == "Linux" and self.runner.exists("eopkg"):
                return "sudo eopkg dc && sudo eopkg clean"
            return None
        if symbolic == "swap":
            return "sudo swapoff -a && sudo swapon -a" if self.so == "Linux" else None
        if symbolic == "check":
            if self.so == "Linux" and self.runner.exists("eopkg"):
                return "sudo eopkg check"
            return None
        if symbolic == "turbo":
            if self.so == "Linux":
                mode = "performance" if self.turbo_active else "powersave"
                return f"sudo cpupower frequency-set -g {mode}"
            if self.so == "Windows":
                guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" if self.turbo_active else "381b4222-f694-41f0-9685-ff5bb260df2e"
                return f"powercfg /setactive {guid}"
            return None
        # Instalação de pacotes
        if symbolic in ["steam", "lutris", "heroic", "bottles", "wine", "mangohud", "goverlay"]:
            return self._install_pkg(symbolic)
        # Rede
        if symbolic == "ping":
            return None  # tratado separadamente
        if symbolic == "speedtest":
            if self.runner.exists("speedtest-cli"):
                return "speedtest-cli"
            return "curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3 -"
        if symbolic == "ethtool":
            if self.so != "Linux":
                return None
            iface = self.runner.check_output("ip route | grep default | awk '{print $5}' | head -1")
            return f"ethtool {iface}" if iface else None
        if symbolic == "dhclient":
            return "sudo dhclient -v -r && sudo dhclient -v" if self.so == "Linux" else None
        if symbolic == "ports":
            if self.so == "Linux":
                return "ss -tuln"
            if self.so == "Windows":
                return "netstat -an | findstr LISTENING"
            if self.so == "Darwin":
                return "lsof -i -P -n | grep LISTEN"
            return None
        if symbolic == "traceroute":
            return "tracert 8.8.8.8" if self.so == "Windows" else "traceroute 8.8.8.8"
        if symbolic == "wifi":
            if self.so == "Linux":
                return "nmcli -t -f GENERAL.STATE,IP4.ADDRESS,IP4.GATEWAY,WIFI.SSID,WIFI.SIGNAL,WIFI.CHANNEL dev show"
            if self.so == "Windows":
                return "netsh wlan show interfaces"
            if self.so == "Darwin":
                return "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I"
            return None
        if symbolic == "testdns":
            return "nslookup google.com" if self.so == "Windows" else "dig google.com +short"
        # Drivers
        if symbolic == "pci":
            if self.so == "Linux":
                return "lspci -nnk"
            if self.so == "Darwin":
                return "system_profiler SPHardwareDataType"
            if self.so == "Windows":
                return "wmic path win32_VideoController get name"
            return None
        if symbolic == "update":
            if self.so == "Linux":
                # Tenta dnf, apt, etc.
                if self.runner.exists("dnf"):
                    return "sudo dnf upgrade -y"
                if self.runner.exists("apt"):
                    return "sudo apt upgrade -y"
                return None
            if self.so == "Windows" and self.runner.exists("winget"):
                return "winget upgrade --all"
            if self.so == "Darwin" and self.runner.exists("brew"):
                return "brew upgrade"
            return None
        if symbolic == "usb":
            if self.so == "Linux":
                return "lsusb"
            if self.so == "Darwin":
                return "system_profiler SPUSBDataType"
            if self.so == "Windows":
                return "wmic path Win32_USBControllerDevice get *"
            return None
        if symbolic == "modules":
            if self.so == "Linux":
                return "lsmod"
            if self.so == "Darwin":
                return "kextstat"
            if self.so == "Windows":
                return "driverquery"
            return None
        if symbolic == "cpu_info":
            if self.so == "Linux":
                return "lscpu"
            if self.so == "Darwin":
                return "sysctl -a | grep machdep.cpu"
            if self.so == "Windows":
                return "wmic cpu get name"
            return None
        if symbolic == "firmware":
            if self.so == "Linux":
                return "sudo dmesg | grep -i firmware"
            if self.so == "Darwin":
                return "ioreg -l | grep -i firmware"
            return None
        # Comandos especiais (tratados por funções internas)
        if symbolic in ["video_drv", "net_drv", "auto_update"]:
            return symbolic  # indicador para tratamento especial
        return None

    def _install_pkg(self, pkg):
        if self.so == "Linux":
            if self.runner.exists("eopkg"):
                return f"sudo eopkg it {pkg} -y"
            if self.runner.exists("apt"):
                return f"sudo apt install -y {pkg}"
            if self.runner.exists("dnf"):
                return f"sudo dnf install -y {pkg}"
            return None
        if self.so == "Windows" and self.runner.exists("winget"):
            return f"winget install {pkg}"
        if self.so == "Darwin" and self.runner.exists("brew"):
            return f"brew install {pkg}"
        return None

    def dns_command(self, dns):
        """Retorna comando de configuração de DNS."""
        if self.so == "Linux":
            iface = self.runner.check_output("nmcli -t -f DEVICE,STATE dev | grep connected | cut -d: -f1 | head -n1")
            if not iface:
                return "echo 'Interface não encontrada'"
            if dns == "auto":
                return f"nmcli dev mod {iface} ipv4.dns ''"
            return f"nmcli dev mod {iface} ipv4.dns '{dns}'"
        elif self.so == "Windows":
            iface = self.runner.check_output("wmic nic where netenabled=true get NetConnectionID | findstr /v NetConnectionID")
            iface = iface.strip() if iface else None
            if not iface:
                return "echo 'Interface não encontrada'"
            if dns == "auto":
                return f'netsh interface ip set dns "{iface}" dhcp'
            return f'netsh interface ip set dns "{iface}" static {dns}'
        elif self.so == "Darwin":
            service = self.runner.check_output("networksetup -listallnetworkservices | grep -v 'An asterisk' | head -1")
            if not service:
                return "echo 'Serviço não encontrado'"
            if dns == "auto":
                return f"networksetup -setdnsservers '{service}' empty"
            return f"networksetup -setdnsservers '{service}' {dns}"
        return "echo 'DNS não suportado'"
