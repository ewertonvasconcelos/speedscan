#!/usr/bin/env python3
# core/smart_monitor.py

import subprocess
from typing import List, Dict, Any

class SmartMonitor:
    """
    Classe para obter informações S.M.A.R.T. dos discos.
    Utiliza smartctl (smartmontools) via subprocess.
    """

    def __init__(self):
        self.drives = []
        self.smart_data = {}
        self._scan_drives()

    def _scan_drives(self):
        """Lista todos os discos do sistema (via lsblk ou smartctl --scan)."""
        try:
            output = subprocess.check_output(["smartctl", "--scan"], universal_newlines=True)
            lines = output.strip().split('\n')
            for line in lines:
                parts = line.split()
                if parts and parts[0].startswith('/dev/'):
                    dev = parts[0]
                    self.drives.append(dev)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                output = subprocess.check_output(["lsblk", "-d", "-n", "-o", "NAME"], universal_newlines=True)
                for name in output.strip().split('\n'):
                    if name:
                        dev = f"/dev/{name}"
                        self.drives.append(dev)
            except:
                self.drives = []

    def get_smart_summary(self) -> List[Dict[str, Any]]:
        summary = []
        for dev in self.drives:
            info = self._get_smart_info(dev)
            if info:
                summary.append(info)
        return summary

    def _get_smart_info(self, device: str) -> Dict[str, Any]:
        try:
            output = subprocess.check_output(
                ["smartctl", "-i", "-H", "-A", device],
                universal_newlines=True,
                stderr=subprocess.STDOUT
            )
            return self._parse_smartctl_output(device, output)
        except subprocess.CalledProcessError as e:
            # smartctl retornou erro, mas pode ter saída útil
            return self._parse_smartctl_output(device, e.output)
        except FileNotFoundError:
            return {"device": device, "error": "smartctl não encontrado", "status": "UNKNOWN"}

    def _parse_smartctl_output(self, device: str, output: str) -> Dict[str, Any]:
        info = {
            "device": device,
            "model": "Desconhecido",
            "serial": "N/A",
            "status": "UNKNOWN",
            "temperature": None,
            "attributes": {}
        }

        lines = output.split('\n')
        for line in lines:
            if "Device Model" in line or "Model Number" in line:
                info["model"] = line.split(':', 1)[1].strip()
            elif "Serial Number" in line or "Serial number" in line:
                info["serial"] = line.split(':', 1)[1].strip()
            elif "SMART overall-health self-assessment test result" in line:
                status = line.split(':', 1)[1].strip()
                info["status"] = "PASSED" if "PASSED" in status else "FAILED" if "FAILED" in status else "UNKNOWN"
            elif "Temperature_Celsius" in line:
                parts = line.split()
                if len(parts) >= 10:
                    info["temperature"] = parts[9]
            elif "194 Temperature_Celsius" in line:
                parts = line.split()
                if len(parts) >= 10:
                    info["temperature"] = parts[9]

        if info["status"] == "UNKNOWN":
            for line in lines:
                if "SMART Health Status" in line:
                    status = line.split(':', 1)[1].strip()
                    info["status"] = "PASSED" if "OK" in status else "FAILED"
                    break

        return info

    def get_detailed_report(self) -> str:
        summary = self.get_smart_summary()
        if not summary:
            return "Nenhum disco encontrado ou smartctl não disponível."

        lines = []
        lines.append("=" * 60)
        lines.append("RELATÓRIO S.M.A.R.T. DETALHADO")
        lines.append("=" * 60)

        for disk in summary:
            lines.append(f"\nDispositivo: {disk['device']}")
            lines.append(f"Modelo: {disk['model']}")
            lines.append(f"Nº Série: {disk['serial']}")
            lines.append(f"Status: {disk.get('status', 'UNKNOWN')}")
            if disk.get('temperature'):
                lines.append(f"Temperatura: {disk['temperature']}°C")
            else:
                lines.append("Temperatura: N/A")
            lines.append("-" * 40)

        return "\n".join(lines)

    def get_summary_text(self) -> str:
        summary = self.get_smart_summary()
        total = len(summary)
        if total == 0:
            return "Nenhum disco detectado"

        passed = sum(1 for d in summary if d.get('status') == "PASSED")
        failed = sum(1 for d in summary if d.get('status') == "FAILED")
        unknown = total - passed - failed

        if failed > 0:
            return f"⚠️ {total} discos, {failed} com falha!"
        elif unknown > 0:
            return f"ℹ️ {total} discos, {unknown} não avaliados"
        else:
            return f"✅ {total} discos, todos OK"

    def get_status_color(self) -> str:
        summary = self.get_smart_summary()
        if not summary:
            return "gray"
        if any(d.get('status') == "FAILED" for d in summary):
            return "red"
        if any(d.get('status') == "UNKNOWN" for d in summary):
            return "yellow"
        return "green"
