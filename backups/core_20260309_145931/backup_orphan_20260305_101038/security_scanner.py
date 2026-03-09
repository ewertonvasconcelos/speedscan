from core import config
#!/usr/bin/env python3
import logging
# Módulo de segurança: portas, firewall, atualizações
# Versão 1.0.0

import subprocess
import re

class SecurityScanner:
    def __init__(self, so):
        self.so = so

    def scan_open_ports(self):
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
    logging.error(f"Exceção em security_scanner.py:55: {e}")
            return [f"Erro: {e}"]
        return []

    def check_firewall_status(self):
        try:
            if self.so == "Linux":
                ufw = subprocess.run(["sudo", "ufw", "status"], capture_output=True, text=True, timeout=3)
                if ufw.returncode == 0:
                    return ufw.stdout
                ipt = subprocess.run(["sudo", "iptables", "-L"], capture_output=True, text=True, timeout=3)
                if ipt.returncode == 0:
                    return ipt.stdout
                return "Firewall não detectado ou sem permissão."
            elif self.so == "Windows":
                cmd = ["netsh", "advfirewall", "show", "allprofiles"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                return result.stdout
            elif self.so == "Darwin":
                cmd = ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                return result.stdout
except Exception as e:
    logging.error(f"Exceção em security_scanner.py:77: {e}")
            return f"Erro ao verificar firewall: {e}"
        return "Não foi possível obter status do firewall."

    def check_security_updates(self):
        try:
            if self.so == "Linux":
                if subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
                    subprocess.run(["sudo", "apt", "update"], capture_output=True, timeout=10)
                    result = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True, timeout=10)
                    lines = result.stdout.splitlines()
                    updates = [line for line in lines if "security" in line.lower() or line.strip() and not line.startswith("Listing")]
                    return updates if updates else ["Nenhuma atualização de segurança encontrada."]
                elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
                    result = subprocess.run(["dnf", "updateinfo", "list", "security"], capture_output=True, text=True, timeout=10)
                    return result.stdout.splitlines()
                elif subprocess.run(["which", "yum"], capture_output=True).returncode == 0:
                    result = subprocess.run(["yum", "updateinfo", "list", "security"], capture_output=True, text=True, timeout=10)
                    return result.stdout.splitlines()
                else:
                    return ["Gerenciador de pacotes não suportado para verificação de segurança."]
            elif self.so == "Windows":
                cmd = ["powershell", "-Command", "Get-WUInstall -ListOnly -MicrosoftUpdate"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                return result.stdout.splitlines()
            elif self.so == "Darwin":
                cmd = ["softwareupdate", "-l"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                lines = result.stdout.splitlines()
                updates = [line for line in lines if "security" in line.lower() or "recommended" in line.lower()]
                return updates if updates else ["Nenhuma atualização de segurança disponível."]
except Exception as e:
    logging.error(f"Exceção em security_scanner.py:108: {e}")
            return [f"Erro ao verificar atualizações: {e}"]
        return ["Não foi possível verificar atualizações de segurança."]
