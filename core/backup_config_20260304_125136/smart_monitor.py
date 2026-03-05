#!/usr/bin/env python3
import logging
# Módulo de monitoramento S.M.A.R.T. dos discos
# Versão 1.0.0

import subprocess
import re

class SmartMonitor:
    def __init__(self):
        self.disk_status = {}

    def get_smart_info(self, disk="/dev/sda"):
        try:
            result = subprocess.run(["sudo", "smartctl", "-H", disk], capture_output=True, text=True, timeout=5)
            return result.stdout
        except:
            return None

    def get_summary_text(self):
        try:
            out = subprocess.run(["lsblk", "-d", "-o", "NAME"], capture_output=True, text=True)
            disks = out.stdout.splitlines()[1:]
            summary = []
            for disk in disks:
                disk = disk.strip()
                if disk:
                    smart = self.get_smart_info(f"/dev/{disk}")
                    if smart:
                        match = re.search(r"SMART overall-health self-assessment test result: (\w+)", smart)
                        if match:
                            status = match.group(1)
                            summary.append(f"{disk}: {status}")
                        else:
                            summary.append(f"{disk}: Desconhecido")
                    else:
                        summary.append(f"{disk}: Não suportado")
            return "\n".join(summary) if summary else "Nenhum disco encontrado"
        except:
            return "Erro ao ler discos"

    def get_status_color(self):
        try:
            out = subprocess.run(["lsblk", "-d", "-o", "NAME"], capture_output=True, text=True)
            disks = out.stdout.splitlines()[1:]
            any_failed = False
            any_unknown = False
            for disk in disks:
                disk = disk.strip()
                if disk:
                    smart = self.get_smart_info(f"/dev/{disk}")
                    if smart:
                        if "FAILED" in smart:
                            any_failed = True
                        elif "PASSED" not in smart:
                            any_unknown = True
                    else:
                        any_unknown = True
            if any_failed:
                return "red"
            elif any_unknown:
                return "yellow"
            else:
                return "green"
        except:
            return "yellow"
