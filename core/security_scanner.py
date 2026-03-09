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
    """Scans system for open ports, firewall status, and security updates, cross-platform."""

    def __init__(self, so):
        """Initialize with the operating system name.

        Args:
            so (str): Operating system (Linux, Windows, Darwin).
        """
        self.so = so

    def scan_open_ports(self):
        """Scan for open (listening) ports on the system.

        Returns:
            list of str: Strings representing open ports (e.g., '0.0.0.0:80'), or error messages.
        """
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
        """Check the status of the system firewall.

        Returns:
            str: Firewall status output or error message.
        """
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
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                return result.stdout
        except Exception as e:
            logging.error(f"Error checking firewall: {e}")
            return f"Error checking firewall: {e}"
        return "Unable to fetch firewall status."

    def check_security_updates(self):
        """Check for pending security updates using the system's package manager.

        Returns:
            list of str: List of security updates (or messages).
        """
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
