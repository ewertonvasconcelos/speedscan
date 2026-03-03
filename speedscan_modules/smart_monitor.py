"""
SpeedScan - Módulo S.M.A.R.T. (Saúde dos Discos)
===================================================
Lê dados S.M.A.R.T. de HDDs e SSDs para diagnosticar
a saúde do armazenamento.

Dependências:
    pip install pySMART
    Linux/macOS: sudo apt install smartmontools  /  brew install smartmontools
    Windows: Instalar smartmontools de https://www.smartmontools.org/
"""

import subprocess
import platform
import json
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DiskHealth:
    """Resultado do diagnóstico S.M.A.R.T. de um disco."""
    device: str
    model: str
    serial: str
    firmware: str
    capacity_gb: float
    smart_status: str          # PASS | FAIL | UNKNOWN
    temperature_c: Optional[float]
    power_on_hours: Optional[int]
    reallocated_sectors: Optional[int]
    pending_sectors: Optional[int]
    uncorrectable_errors: Optional[int]
    health_score: int          # 0-100
    warnings: list[str] = field(default_factory=list)
    raw_attributes: dict = field(default_factory=dict)

    @property
    def health_label(self) -> str:
        if self.health_score >= 90:
            return "Excelente"
        elif self.health_score >= 70:
            return "Bom"
        elif self.health_score >= 50:
            return "Regular"
        elif self.health_score >= 30:
            return "Ruim"
        return "Crítico"

    @property
    def health_color(self) -> str:
        colors = {
            "Excelente": "#00ff88",
            "Bom": "#88ff00",
            "Regular": "#ffaa00",
            "Ruim": "#ff5500",
            "Crítico": "#ff0000",
        }
        return colors.get(self.health_label, "#ffffff")

    def to_dict(self) -> dict:
        return {
            "device": self.device,
            "model": self.model,
            "serial": self.serial,
            "capacity_gb": self.capacity_gb,
            "smart_status": self.smart_status,
            "temperature_c": self.temperature_c,
            "power_on_hours": self.power_on_hours,
            "reallocated_sectors": self.reallocated_sectors,
            "health_score": self.health_score,
            "health_label": self.health_label,
            "warnings": self.warnings,
        }


class SmartMonitor:
    """
    Monitora a saúde de discos via S.M.A.R.T.

    Exemplo de uso:
        monitor = SmartMonitor()
        for disk in monitor.get_all_disks_health():
            print(f"{disk.model} — Score: {disk.health_score} ({disk.health_label})")
    """

    def __init__(self):
        self._system = platform.system()
        self._smartctl_path = self._find_smartctl()

    def _find_smartctl(self) -> Optional[str]:
        """Localiza o executável smartctl."""
        paths = []
        if self._system == "Windows":
            paths = [
                r"C:\Program Files\smartmontools\bin\smartctl.exe",
                r"C:\Program Files (x86)\smartmontools\bin\smartctl.exe",
            ]
        else:
            paths = ["/usr/sbin/smartctl", "/usr/bin/smartctl", "/usr/local/bin/smartctl"]

        for path in paths:
            try:
                result = subprocess.run([path, "--version"],
                                        capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return None

    def is_available(self) -> bool:
        """Retorna True se smartctl está disponível."""
        return self._smartctl_path is not None

    def get_devices(self) -> list[str]:
        """Lista dispositivos de armazenamento disponíveis."""
        if not self._smartctl_path:
            return self._fallback_devices()

        try:
            result = subprocess.run(
                [self._smartctl_path, "--scan"],
                capture_output=True, text=True, timeout=10
            )
            devices = []
            for line in result.stdout.splitlines():
                parts = line.split()
                if parts:
                    devices.append(parts[0])
            return devices
        except Exception:
            return self._fallback_devices()

    def _fallback_devices(self) -> list[str]:
        """Fallback para listar discos sem smartctl."""
        import psutil
        devices = set()
        for disk in psutil.disk_partitions():
            if self._system == "Windows":
                # Extrai letra da unidade, ex: C:\
                devices.add(disk.device)
            else:
                # Remove números no final: /dev/sda1 -> /dev/sda
                device = re.sub(r'\d+$', '', disk.device)
                if device.startswith("/dev/"):
                    devices.add(device)
        return list(devices)

    def get_disk_health(self, device: str) -> DiskHealth:
        """
        Retorna diagnóstico S.M.A.R.T. completo de um disco.

        Args:
            device: Caminho do dispositivo (ex: /dev/sda, /dev/nvme0)
        """
        if self._smartctl_path:
            return self._smartctl_health(device)
        return self._basic_health(device)

    def _smartctl_health(self, device: str) -> DiskHealth:
        """Usa smartctl para obter dados S.M.A.R.T."""
        try:
            # Obter info geral + atributos
            info_result = subprocess.run(
                [self._smartctl_path, "-i", "-H", "-A", "--json", device],
                capture_output=True, text=True, timeout=15
            )

            try:
                data = json.loads(info_result.stdout)
            except json.JSONDecodeError:
                return self._parse_smartctl_text(device, info_result.stdout)

            return self._parse_smartctl_json(device, data)

        except Exception as e:
            return self._basic_health(device)

    def _parse_smartctl_json(self, device: str, data: dict) -> DiskHealth:
        """Faz parse do JSON do smartctl."""
        device_info = data.get("device", {})
        model_name = data.get("model_name", "Desconhecido")
        serial = data.get("serial_number", "N/A")
        firmware = data.get("firmware_version", "N/A")

        # Capacidade
        user_capacity = data.get("user_capacity", {})
        capacity_bytes = user_capacity.get("bytes", 0)
        capacity_gb = round(capacity_bytes / (1024 ** 3), 1)

        # Status S.M.A.R.T.
        smart_status_obj = data.get("smart_status", {})
        passed = smart_status_obj.get("passed", None)
        smart_status = "PASS" if passed else "FAIL" if passed is False else "UNKNOWN"

        # Temperatura
        temperature = data.get("temperature", {})
        temp_c = temperature.get("current", None)

        # Power-on hours
        power_on = data.get("power_on_time", {})
        power_hours = power_on.get("hours", None)

        # Atributos SMART
        reallocated = None
        pending = None
        uncorrectable = None
        warnings = []
        raw_attributes = {}

        ata_attributes = data.get("ata_smart_attributes", {}).get("table", [])
        for attr in ata_attributes:
            attr_id = attr.get("id", 0)
            attr_name = attr.get("name", "")
            raw_val = attr.get("raw", {}).get("value", 0)
            raw_attributes[attr_name] = raw_val

            if attr_id == 5:   # Reallocated_Sector_Ct
                reallocated = int(raw_val)
                if reallocated > 0:
                    warnings.append(f"⚠️ {reallocated} setores realocados detectados")
            elif attr_id == 197:  # Current_Pending_Sector
                pending = int(raw_val)
                if pending > 0:
                    warnings.append(f"⚠️ {pending} setores pendentes de realocação")
            elif attr_id == 198:  # Offline_Uncorrectable
                uncorrectable = int(raw_val)
                if uncorrectable > 0:
                    warnings.append(f"🔴 {uncorrectable} erros irrecuperáveis encontrados")

        # Temperatura alta
        if temp_c and temp_c >= 55:
            warnings.append(f"🌡️ Temperatura elevada: {temp_c}°C")

        # Calcular score
        health_score = self._calculate_score(
            smart_status, reallocated, pending, uncorrectable, temp_c, power_hours
        )

        return DiskHealth(
            device=device,
            model=model_name,
            serial=serial,
            firmware=firmware,
            capacity_gb=capacity_gb,
            smart_status=smart_status,
            temperature_c=temp_c,
            power_on_hours=power_hours,
            reallocated_sectors=reallocated,
            pending_sectors=pending,
            uncorrectable_errors=uncorrectable,
            health_score=health_score,
            warnings=warnings,
            raw_attributes=raw_attributes,
        )

    def _parse_smartctl_text(self, device: str, text: str) -> DiskHealth:
        """Parse de saída em texto quando JSON não está disponível."""
        model = re.search(r"Device Model:\s+(.+)", text)
        serial = re.search(r"Serial Number:\s+(\S+)", text)
        firmware = re.search(r"Firmware Version:\s+(\S+)", text)
        smart_ok = "PASSED" in text or "OK" in text
        temp_match = re.search(r"Temperature_Celsius.*?(\d+)$", text, re.MULTILINE)
        hours_match = re.search(r"Power_On_Hours.*?(\d+)$", text, re.MULTILINE)
        realloc_match = re.search(r"Reallocated_Sector.*?(\d+)$", text, re.MULTILINE)

        temp_c = float(temp_match.group(1)) if temp_match else None
        power_hours = int(hours_match.group(1)) if hours_match else None
        reallocated = int(realloc_match.group(1)) if realloc_match else 0

        warnings = []
        if reallocated > 0:
            warnings.append(f"⚠️ {reallocated} setores realocados")
        if temp_c and temp_c >= 55:
            warnings.append(f"🌡️ Temperatura elevada: {temp_c}°C")

        score = self._calculate_score(
            "PASS" if smart_ok else "UNKNOWN",
            reallocated, None, None, temp_c, power_hours
        )

        return DiskHealth(
            device=device,
            model=model.group(1).strip() if model else "Desconhecido",
            serial=serial.group(1) if serial else "N/A",
            firmware=firmware.group(1) if firmware else "N/A",
            capacity_gb=0,
            smart_status="PASS" if smart_ok else "UNKNOWN",
            temperature_c=temp_c,
            power_on_hours=power_hours,
            reallocated_sectors=reallocated,
            pending_sectors=None,
            uncorrectable_errors=None,
            health_score=score,
            warnings=warnings,
        )

    def _basic_health(self, device: str) -> DiskHealth:
        """Diagnóstico básico sem smartctl (apenas uso de disco)."""
        import psutil
        try:
            usage = psutil.disk_usage(device if "/" in device or "\\" in device else "/")
            percent_used = usage.percent
            # Score reduz conforme disco enche
            score = max(10, 100 - max(0, percent_used - 70) * 3)
            warnings = []
            if percent_used >= 90:
                warnings.append(f"🔴 Disco com {percent_used:.0f}% de uso!")
            elif percent_used >= 80:
                warnings.append(f"⚠️ Disco com {percent_used:.0f}% de uso")
            return DiskHealth(
                device=device,
                model="Desconhecido (smartctl indisponível)",
                serial="N/A",
                firmware="N/A",
                capacity_gb=round(usage.total / (1024 ** 3), 1),
                smart_status="UNKNOWN",
                temperature_c=None,
                power_on_hours=None,
                reallocated_sectors=None,
                pending_sectors=None,
                uncorrectable_errors=None,
                health_score=int(score),
                warnings=warnings,
            )
        except Exception:
            return DiskHealth(
                device=device, model="N/A", serial="N/A", firmware="N/A",
                capacity_gb=0, smart_status="UNKNOWN", temperature_c=None,
                power_on_hours=None, reallocated_sectors=None,
                pending_sectors=None, uncorrectable_errors=None,
                health_score=50, warnings=["Não foi possível obter dados do disco"]
            )

    def _calculate_score(
        self,
        smart_status: str,
        reallocated: Optional[int],
        pending: Optional[int],
        uncorrectable: Optional[int],
        temp_c: Optional[float],
        power_hours: Optional[int],
    ) -> int:
        """Calcula score de saúde do disco de 0 a 100."""
        score = 100

        # Status geral S.M.A.R.T.
        if smart_status == "FAIL":
            score -= 50
        elif smart_status == "UNKNOWN":
            score -= 10

        # Setores realocados (cada setor realocado é grave)
        if reallocated:
            if reallocated >= 50:
                score -= 40
            elif reallocated >= 10:
                score -= 25
            elif reallocated >= 1:
                score -= 10

        # Setores pendentes
        if pending:
            score -= min(20, pending * 2)

        # Erros irrecuperáveis (muito grave)
        if uncorrectable:
            score -= min(30, uncorrectable * 5)

        # Temperatura
        if temp_c:
            if temp_c >= 65:
                score -= 20
            elif temp_c >= 55:
                score -= 10

        # Horas de uso (vida útil estimada de 50.000h)
        if power_hours:
            if power_hours >= 50000:
                score -= 20
            elif power_hours >= 30000:
                score -= 10
            elif power_hours >= 20000:
                score -= 5

        return max(0, min(100, score))

    def get_all_disks_health(self) -> list[DiskHealth]:
        """Retorna diagnóstico de todos os discos encontrados."""
        devices = self.get_devices()
        results = []
        seen = set()
        for dev in devices:
            # Evita duplicatas (ex: /dev/sda1 e /dev/sda)
            base = re.sub(r'\d+$', '', dev)
            if base in seen:
                continue
            seen.add(base)
            results.append(self.get_disk_health(base if base else dev))
        return results


if __name__ == "__main__":
    monitor = SmartMonitor()
    print("=== SpeedScan — Monitor S.M.A.R.T. ===\n")

    if not monitor.is_available():
        print("⚠️  smartctl não encontrado. Usando diagnóstico básico.\n")

    disks = monitor.get_all_disks_health()
    for disk in disks:
        print(f"💾 {disk.device} — {disk.model}")
        print(f"   Serial: {disk.serial} | Firmware: {disk.firmware}")
        print(f"   Capacidade: {disk.capacity_gb} GB")
        print(f"   S.M.A.R.T.: {disk.smart_status}")
        if disk.temperature_c:
            print(f"   Temperatura: {disk.temperature_c}°C")
        if disk.power_on_hours:
            print(f"   Horas de uso: {disk.power_on_hours}h ({disk.power_on_hours // 24} dias)")
        if disk.reallocated_sectors is not None:
            print(f"   Setores realocados: {disk.reallocated_sectors}")
        print(f"   Score de Saúde: {disk.health_score}/100 [{disk.health_label}]")
        for w in disk.warnings:
            print(f"   {w}")
        print()
