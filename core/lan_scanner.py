#!/usr/bin/env python3
# core/lan_scanner.py
# Módulo de scanner de rede local

import subprocess
import re
import ipaddress
import threading
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

class LANScanner:
    """
    Escaneia a rede local para encontrar dispositivos ativos.
    Utiliza ping e ARP para detecção.
    """
    
    def __init__(self, interface=None):
        self.interface = interface
        self.devices = []
        self.network = None
        self.scan_callback = None
        self._stop_scan = False
    
    def get_local_network(self) -> Optional[str]:
        """Obtém a rede local (CIDR) baseada no IP e máscara da interface padrão."""
        try:
            # Tenta obter via comando 'ip route' (Linux)
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if 'default via' in line:
                    # Pega a interface
                    parts = line.split()
                    iface = parts[4] if len(parts) > 4 else None
                    # Agora pega a rede associada a essa interface
                    result2 = subprocess.run(['ip', '-4', 'addr', 'show', iface], capture_output=True, text=True)
                    for line2 in result2.stdout.splitlines():
                        if 'inet ' in line2:
                            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', line2)
                            if match:
                                ip = match.group(1)
                                prefix = match.group(2)
                                # Converte para rede CIDR
                                network = ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
                                return str(network)
            return None
        except Exception as e:
            print(f"Erro ao obter rede local: {e}")
            return None
    
    def ping_host(self, ip: str) -> bool:
        """Verifica se um IP responde a ping."""
        try:
            # Comando ping: 1 pacote, timeout 1 segundo
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                    capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False
    
    def arp_lookup(self, ip: str) -> Optional[Dict]:
        """
        Tenta obter o MAC e hostname via ARP (consulta a tabela ARP local).
        Em Linux, usa 'ip neigh' ou 'arp -n'.
        """
        try:
            # Usa 'ip neigh' (mais moderno)
            result = subprocess.run(['ip', 'neigh', 'show', ip], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[0] == ip and 'lladdr' in line:
                    mac = parts[4] if len(parts) > 4 else None
                    state = parts[6] if len(parts) > 6 else ''
                    return {'ip': ip, 'mac': mac, 'state': state}
        except:
            pass
        
        # Fallback para arp -n
        try:
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if ip in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        mac = parts[2] if re.match(r'([0-9a-f]{2}:){5}[0-9a-f]{2}', parts[2]) else None
                        return {'ip': ip, 'mac': mac}
        except:
            pass
        return None
    
    def get_hostname(self, ip: str) -> Optional[str]:
        """Tenta obter o hostname via DNS reverso."""
        try:
            result = subprocess.run(['nslookup', ip], capture_output=True, text=True, timeout=2)
            match = re.search(r'name = (.+)\.', result.stdout)
            if match:
                return match.group(1)
        except:
            pass
        return None
    
    def get_vendor(self, mac: str) -> str:
        """
        Retorna o fabricante com base no prefixo OUI do MAC.
        Usa uma lista local simples (pode ser expandida).
        """
        if not mac:
            return "Desconhecido"
        # Normaliza MAC: remove ':' e pega os primeiros 6 caracteres (OUI)
        oui = mac.replace(':', '').upper()[:6]
        # Dicionário básico de fabricantes (pode ser carregado de um arquivo externo)
        vendors = {
            '001122': 'Fabricante A',
            'AABBCC': 'Fabricante B',
            # Adicione mais conforme necessário
        }
        return vendors.get(oui, "Desconhecido")
    
    def scan_network(self, network_cidr: str = None, progress_callback=None) -> List[Dict]:
        """
        Escaneia toda a rede especificada.
        Se network_cidr for None, tenta detectar automaticamente.
        Retorna lista de dicionários com ip, mac, hostname, vendor, status.
        """
        if network_cidr is None:
            network_cidr = self.get_local_network()
            if network_cidr is None:
                return [{'error': 'Não foi possível determinar a rede local.'}]
        
        self._stop_scan = False
        network = ipaddress.IPv4Network(network_cidr, strict=False)
        hosts = list(network.hosts())
        total = len(hosts)
        devices = []
        
        # Limita a scan para não sobrecarregar (opcional)
        max_hosts = 254  # /24
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
                except:
                    is_alive = False
                
                if is_alive:
                    # Se respondeu ping, tenta obter mais informações
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
        """Interrompe o escaneamento em andamento."""
        self._stop_scan = True
    
    def get_scan_summary(self) -> str:
        """Retorna um resumo do último scan."""
        active = len([d for d in self.devices if d.get('status') == 'ativo'])
        total = len(self.devices)
        return f"Dispositivos ativos: {active}/{total}"
