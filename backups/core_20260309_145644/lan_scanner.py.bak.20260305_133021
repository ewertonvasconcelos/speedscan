from core import config
#!/usr/bin/env python3
import logging
# Módulo de scanner de rede local
# Versão 1.0.0

import subprocess
import re
import ipaddress
import threading
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

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
                            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', line2)
                            if match:
                                ip = match.group(1)
                                prefix = match.group(2)
                                network = ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
                                return str(network)
            return None
except Exception as e:
    logging.error(f"Exceção em lan_scanner.py:39: {e}")
            logging.error(f"Erro ao obter rede local: {e}")
            return None

    def ping_host(self, ip: str) -> bool:
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                    capture_output=True, timeout=2)
            return result.returncode == 0
except Exception as e:
    logging.error(f"Exceção em lan_scanner.py:48: {e}")
            return False

    def arp_lookup(self, ip: str) -> Optional[Dict]:
        try:
            result = subprocess.run(['ip', 'neigh', 'show', ip], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[0] == ip and 'lladdr' in line:
                    mac = parts[4] if len(parts) > 4 else None
                    return {'ip': ip, 'mac': mac}
except Exception as e:
    logging.error(f"Exceção em lan_scanner.py:59: {e}")
            pass
        try:
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if ip in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        mac = parts[2] if re.match(r'([0-9a-f]{2}:){5}[0-9a-f]{2}', parts[2]) else None
                        return {'ip': ip, 'mac': mac}
except Exception as e:
    logging.error(f"Exceção em lan_scanner.py:69: {e}")
            pass
        return None

    def get_hostname(self, ip: str) -> Optional[str]:
        try:
            result = subprocess.run(['nslookup', ip], capture_output=True, text=True, timeout=2)
            match = re.search(r'name = (.+)\.', result.stdout)
            if match:
                return match.group(1)
except Exception as e:
    logging.error(f"Exceção em lan_scanner.py:79: {e}")
            pass
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
                return [{'error': 'Não foi possível determinar a rede local.'}]
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
    logging.error(f"Exceção em lan_scanner.py:115: {e}")
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
                        'status': 'ativo'
                    })
                if progress_callback:
                    progress_callback(i+1, total, ip, is_alive)
        self.devices = devices
        return devices

    def stop_scan(self):
        self._stop_scan = True

    def get_scan_summary(self) -> str:
        active = len([d for d in self.devices if d.get('status') == 'ativo'])
        total = len(self.devices)
        return f"Dispositivos ativos: {active}/{total}"
