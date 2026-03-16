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
    """Scans the local area network for active devices using ping and ARP."""

    def __init__(self, interface=None):
        """Initialize the scanner.

        Args:
            interface (str optional): Network interface to scan (e.g., 'eth0'). If None, auto-detect.
        """
        self.interface = interface
        self.devices = []
        self.network = None
        self.scan_callback = None
        self._stop_scan = False

    def get_local_network(self) -> Optional[str]:
        """Determine the local network CIDR (e.g., "192.168.1.0/24").

        Returns:
            Optional string representing the network, or None.
        """
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
        """Ping a host to check if it is alive.

        Args:
            ip (str): IP address to ping.

        Returns:
            bool: True if host responds, False otherwise.
        """
        try:
            result = subprocess.run(["ping", "-c", "1", "-W", "1", ip],
                                     capture_output=True, timeout=2)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error pinging {ip}: {e}")
            return False

    def arp_lookup(self, ip: str) -> Optional[Dict]:
        """Retrieve MAC address for an IP using ARP.

        Args:
            ip (str): IP address to look up.

        Returns:
            Optional dict with 'ip' and 'mac' keys, or None.
        """
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
        """Perform a DNS lookup to find the hostname for an IP.

        Args:
            ip (str): IP address.

        Returns:
            Optional string containing the hostname, or None.
        """
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
        """Attempt to determine the vendor from a MAC address (OUI lookup).

        Args:
            mac (str): MAC address in standard format.

        Returns:
            str: Vendor name or "Desconhecido".
        """
        if not mac:
            return "Desconhecido"
        oui = mac.replace(':', '').upper()[:6]
        vendors = {
            '001122': 'Fabricante A',
            'AABBCC': 'Fabricante B',
        }
        return vendors.get(oui, "Desconhecido")

    def scan_network(self, network_cidr: str = None, progress_callback=None) -> List[Dict]:
        """Scan the network for active devices.

        Args:
            network_cidr (str optional): Network in CIDR format (e.g., "192.168.1.0/24"). If None, auto-detect.
            progress_callback (callable(current, total, ip, is_alive) optional).

        Returns:
            List of dicts, each containing 'ip', 'mac', 'hostname', 'vendor', 'status'.
        """
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
        """Stop the scanning process."""
        self._stop_scan = True

    def get_scan_summary(self) -> str:
        """Return a summary string of the scan results.

        Returns:
            str: A formatted string showing number of active devices.
        """
        active = len([d for d in self.devices if d.get('status') == 'active'])
        total = len(self.devices)
        return f"Active devices: {active}/{total}"
