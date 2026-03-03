"""
SpeedScan - Scanner de Rede Local (LAN)
========================================
Descobre dispositivos na rede local com IP, MAC,
hostname e fabricante do adaptador de rede.

Dependências:
    pip install scapy  (recomendado, precisar de root/admin)
    Ou: apenas socket e subprocess (sem root)
"""

import socket
import subprocess
import platform
import threading
import re
import ipaddress
import time
import urllib.request
import json
from dataclasses import dataclass, field
from typing import Optional, Callable


@dataclass
class NetworkDevice:
    """Representa um dispositivo descoberto na rede."""
    ip: str
    mac: str
    hostname: str
    vendor: str
    is_local: bool          # True se for a própria máquina
    ports_open: list[int] = field(default_factory=list)
    response_ms: float = 0
    last_seen: float = field(default_factory=time.time)

    @property
    def display_name(self) -> str:
        if self.hostname and self.hostname != self.ip:
            return self.hostname
        if self.vendor:
            return f"[{self.vendor}]"
        return self.ip

    @property
    def icon(self) -> str:
        name = (self.hostname + self.vendor).lower()
        if self.is_local:
            return "🖥️"
        if any(x in name for x in ["router", "gateway", "fritzbox", "tplink", "tp-link"]):
            return "📡"
        if any(x in name for x in ["iphone", "android", "samsung", "xiaomi", "huawei"]):
            return "📱"
        if any(x in name for x in ["printer", "impressora", "hp", "canon", "epson"]):
            return "🖨️"
        if any(x in name for x in ["tv", "chromecast", "roku", "firetv", "appletv"]):
            return "📺"
        if any(x in name for x in ["raspberry", "arduino", "esp32", "esp8266"]):
            return "🔌"
        return "💻"

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "mac": self.mac,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "open_ports": self.ports_open,
            "response_ms": self.response_ms,
        }


class LanScanner:
    """
    Scanner de rede local para descobrir dispositivos.

    Exemplo de uso:
        scanner = LanScanner()
        scanner.scan_network(
            on_device_found=lambda d: print(f"{d.icon} {d.ip} — {d.display_name}"),
            on_complete=lambda devices: print(f"Total: {len(devices)} dispositivos"),
        )
    """

    COMMON_PORTS = [22, 80, 443, 8080, 8443, 3389, 21, 23, 445, 139]

    def __init__(self):
        self._system = platform.system()
        self._vendor_cache: dict[str, str] = {}

    def get_local_ip(self) -> str:
        """Retorna o IP local da máquina."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def get_network_range(self) -> str:
        """Retorna o range da rede local (ex: 192.168.1.0/24)."""
        local_ip = self.get_local_ip()
        # Assume /24 (classe C padrão para redes domésticas)
        parts = local_ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        return "192.168.1.0/24"

    def ping_host(self, ip: str, timeout: float = 1.0) -> Optional[float]:
        """
        Faz ping em um host.

        Returns:
            Tempo de resposta em ms, ou None se não respondeu
        """
        try:
            if self._system == "Windows":
                cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(timeout)), ip]

            start = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=timeout + 0.5
            )
            elapsed = (time.time() - start) * 1000

            if result.returncode == 0:
                return round(elapsed, 1)
        except (subprocess.TimeoutExpired, Exception):
            pass
        return None

    def get_hostname(self, ip: str) -> str:
        """Resolve o hostname de um IP."""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except Exception:
            return ip

    def get_mac_from_arp(self, ip: str) -> str:
        """Obtém o MAC address via tabela ARP."""
        try:
            if self._system == "Windows":
                result = subprocess.run(
                    ["arp", "-a", ip],
                    capture_output=True, text=True, timeout=3
                )
                match = re.search(r"([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}", result.stdout)
            else:
                # Linux/macOS: primeiro faz ping para popular tabela ARP
                result = subprocess.run(
                    ["arp", ip],
                    capture_output=True, text=True, timeout=3
                )
                match = re.search(r"([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}", result.stdout)

            if match:
                return match.group(0).upper()
        except Exception:
            pass
        return "??:??:??:??:??:??"

    def get_vendor(self, mac: str) -> str:
        """
        Identifica o fabricante pelo MAC address.
        Usa uma tabela local básica + API pública como fallback.
        """
        if mac in self._vendor_cache:
            return self._vendor_cache[mac]

        if mac == "??:??:??:??:??:??":
            return ""

        # Tabela local com prefixos comuns (OUI)
        oui = mac[:8].upper().replace("-", ":").replace(".", "")
        local_vendors = {
            "00:50:56": "VMware",
            "00:0C:29": "VMware",
            "00:1C:42": "Parallels",
            "08:00:27": "VirtualBox",
            "DC:A6:32": "Raspberry Pi",
            "B8:27:EB": "Raspberry Pi",
            "E4:5F:01": "Raspberry Pi",
            "FC:AA:14": "TP-Link",
            "00:1D:0F": "ASUS",
            "70:85:C2": "Apple",
            "A4:CF:99": "Apple",
            "34:36:3B": "Apple",
            "1C:36:BB": "Apple",
            "40:9C:28": "Dell",
            "18:66:DA": "Dell",
            "F8:BC:12": "Samsung",
            "78:BD:BC": "Samsung",
            "14:AB:C5": "Xiaomi",
            "20:34:FB": "Xiaomi",
            "74:DA:38": "Edimax",
        }

        oui_key = oui[:8]
        if oui_key in local_vendors:
            vendor = local_vendors[oui_key]
            self._vendor_cache[mac] = vendor
            return vendor

        # API pública (requer internet)
        try:
            mac_encoded = mac.replace(":", "-")[:8]
            url = f"https://api.macvendors.com/{mac_encoded}"
            req = urllib.request.Request(url, headers={"User-Agent": "SpeedScan/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                vendor = resp.read().decode().strip()
                self._vendor_cache[mac] = vendor
                return vendor[:30]
        except Exception:
            pass

        self._vendor_cache[mac] = ""
        return ""

    def check_open_ports(self, ip: str, ports: list[int] = None, timeout: float = 0.5) -> list[int]:
        """Verifica quais portas estão abertas em um host."""
        if ports is None:
            ports = self.COMMON_PORTS
        open_ports = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result == 0:
                    open_ports.append(port)
            except Exception:
                pass
        return open_ports

    def scan_host(self, ip: str, check_ports: bool = False) -> Optional[NetworkDevice]:
        """
        Verifica se um host está ativo e coleta suas informações.

        Returns:
            NetworkDevice se o host respondeu, None caso contrário
        """
        response_ms = self.ping_host(ip)
        if response_ms is None:
            return None

        local_ip = self.get_local_ip()
        mac = self.get_mac_from_arp(ip)
        hostname = self.get_hostname(ip)
        vendor = self.get_vendor(mac)

        ports = []
        if check_ports:
            ports = self.check_open_ports(ip)

        return NetworkDevice(
            ip=ip,
            mac=mac,
            hostname=hostname if hostname != ip else "",
            vendor=vendor,
            is_local=(ip == local_ip),
            ports_open=ports,
            response_ms=response_ms,
        )

    def scan_network(
        self,
        ip_range: Optional[str] = None,
        max_threads: int = 50,
        check_ports: bool = False,
        on_device_found: Optional[Callable[[NetworkDevice], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[list[NetworkDevice]], None]] = None,
    ) -> list[NetworkDevice]:
        """
        Faz um scan completo da rede local.

        Args:
            ip_range: Range CIDR (padrão: detectado automaticamente)
            max_threads: Número máximo de threads paralelas
            check_ports: Se True, verifica portas abertas (mais lento)
            on_device_found: Callback chamado quando um dispositivo é encontrado
            on_progress: Callback(ip_atual, total) para progresso
            on_complete: Callback com lista final de dispositivos

        Returns:
            Lista de NetworkDevice encontrados
        """
        if ip_range is None:
            ip_range = self.get_network_range()

        try:
            network = ipaddress.IPv4Network(ip_range, strict=False)
            hosts = list(network.hosts())
        except ValueError:
            return []

        devices = []
        devices_lock = threading.Lock()
        semaphore = threading.Semaphore(max_threads)
        completed = [0]
        total = len(hosts)

        def scan_host_thread(ip):
            with semaphore:
                device = self.scan_host(str(ip), check_ports)
                with devices_lock:
                    completed[0] += 1
                    if on_progress:
                        on_progress(completed[0], total)
                    if device:
                        devices.append(device)
                        if on_device_found:
                            on_device_found(device)

        threads = [threading.Thread(target=scan_host_thread, args=(ip,), daemon=True)
                   for ip in hosts]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Ordenar por IP
        devices.sort(key=lambda d: [int(x) for x in d.ip.split(".")])

        if on_complete:
            on_complete(devices)

        return devices

    def scan_network_async(self, **kwargs) -> threading.Thread:
        """Executa o scan em background e retorna a thread."""
        thread = threading.Thread(
            target=self.scan_network,
            kwargs=kwargs,
            daemon=True
        )
        thread.start()
        return thread


if __name__ == "__main__":
    print("=== SpeedScan — Scanner de Rede Local ===\n")
    scanner = LanScanner()

    local_ip = scanner.get_local_ip()
    network = scanner.get_network_range()
    print(f"🖥️  IP Local: {local_ip}")
    print(f"🌐 Rede: {network}")
    print(f"\n🔍 Iniciando scan (pode demorar 20-60 segundos)...\n")

    found = []

    def on_found(device: NetworkDevice):
        found.append(device)
        icon = device.icon
        print(f"  {icon} {device.ip:<16} {device.mac:<20} {device.display_name[:30]}")

    def on_progress(current, total):
        if current % 25 == 0:
            pct = current / total * 100
            print(f"  ... {pct:.0f}% concluído ({current}/{total})")

    scanner.scan_network(
        on_device_found=on_found,
        on_progress=on_progress
    )

    print(f"\n✅ Scan completo! {len(found)} dispositivos encontrados.")
