"""
SpeedScan - Módulo de Monitoramento de Temperatura
====================================================
Monitora temperatura de CPU, GPU (NVIDIA/AMD) e discos.
Compatível com Linux, Windows e macOS.

Dependências:
    pip install psutil GPUtil pynvml
"""

import psutil
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional
import threading
import time


@dataclass
class TempSensor:
    """Representa um sensor de temperatura."""
    name: str
    label: str
    current: float
    high: Optional[float] = None
    critical: Optional[float] = None
    status: str = "normal"  # normal | warning | critical

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "label": self.label,
            "current": self.current,
            "high": self.high,
            "critical": self.critical,
            "status": self.status
        }


class TemperatureMonitor:
    """
    Monitora temperatura de CPU, GPU e sensores do sistema.

    Exemplo de uso:
        monitor = TemperatureMonitor()
        temps = monitor.get_all_temps()
        for sensor in temps:
            print(f"{sensor.label}: {sensor.current}°C [{sensor.status}]")
    """

    WARN_THRESHOLD = 75.0   # °C — aviso
    CRIT_THRESHOLD = 90.0   # °C — crítico

    def __init__(self, warn_threshold: float = 75.0, crit_threshold: float = 90.0):
        self.warn_threshold = warn_threshold
        self.crit_threshold = crit_threshold
        self._cache = []
        self._last_update = 0
        self._cache_ttl = 2  # segundos

    def _classify(self, current: float, high: Optional[float], critical: Optional[float]) -> str:
        """Classifica o status do sensor."""
        crit = critical or self.crit_threshold
        warn = high or self.warn_threshold
        if current >= crit:
            return "critical"
        if current >= warn:
            return "warning"
        return "normal"

    # ------------------------------------------------------------------
    # CPU
    # ------------------------------------------------------------------
    def get_cpu_temps(self) -> list[TempSensor]:
        """Retorna temperaturas de CPU via psutil."""
        sensors = []
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return self._fallback_cpu_temp()

            priority = ["coretemp", "k10temp", "cpu_thermal", "acpitz", "zenpower"]
            ordered_keys = sorted(temps.keys(), key=lambda k: priority.index(k) if k in priority else 99)

            for name in ordered_keys:
                for entry in temps[name]:
                    label = entry.label or name
                    sensor = TempSensor(
                        name=name,
                        label=label,
                        current=round(entry.current, 1),
                        high=entry.high,
                        critical=entry.critical,
                    )
                    sensor.status = self._classify(sensor.current, sensor.high, sensor.critical)
                    sensors.append(sensor)

        except (AttributeError, Exception):
            return self._fallback_cpu_temp()
        return sensors

    def _fallback_cpu_temp(self) -> list[TempSensor]:
        """Fallback para Windows via WMI ou outros métodos."""
        system = platform.system()
        if system == "Windows":
            return self._windows_cpu_temp()
        elif system == "Darwin":
            return self._macos_cpu_temp()
        return []

    def _windows_cpu_temp(self) -> list[TempSensor]:
        """Tenta obter temperatura no Windows via WMI."""
        try:
            import wmi
            w = wmi.WMI(namespace="root\\wmi")
            temp_info = w.MSAcpi_ThermalZoneTemperature()
            sensors = []
            for i, t in enumerate(temp_info):
                celsius = (t.CurrentTemperature / 10.0) - 273.15
                sensor = TempSensor(
                    name="thermal_zone",
                    label=f"Thermal Zone {i}",
                    current=round(celsius, 1)
                )
                sensor.status = self._classify(celsius, None, None)
                sensors.append(sensor)
            return sensors
        except Exception:
            return []

    def _macos_cpu_temp(self) -> list[TempSensor]:
        """Tenta obter temperatura no macOS via osx-cpu-temp."""
        try:
            result = subprocess.run(
                ["osx-cpu-temp"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                temp_str = result.stdout.strip().replace("°C", "").strip()
                celsius = float(temp_str)
                sensor = TempSensor(
                    name="cpu",
                    label="CPU Temperature",
                    current=celsius
                )
                sensor.status = self._classify(celsius, None, None)
                return [sensor]
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    # GPU
    # ------------------------------------------------------------------
    def get_gpu_temps(self) -> list[TempSensor]:
        """Retorna temperaturas de GPU (NVIDIA via pynvml, AMD via psutil)."""
        sensors = []

        # Tenta NVIDIA via pynvml
        sensors.extend(self._nvidia_temps())

        # Tenta AMD via psutil (amdgpu)
        if not sensors:
            sensors.extend(self._amd_temps())

        return sensors

    def _nvidia_temps(self) -> list[TempSensor]:
        """GPU NVIDIA via pynvml."""
        try:
            import pynvml
            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            sensors = []
            for i in range(count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode()
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                sensor = TempSensor(
                    name="nvidia_gpu",
                    label=f"GPU {i}: {name}",
                    current=float(temp),
                    high=85.0,
                    critical=95.0
                )
                sensor.status = self._classify(float(temp), 85.0, 95.0)
                sensors.append(sensor)
            pynvml.nvmlShutdown()
            return sensors
        except Exception:
            pass

        # Fallback: GPUtil
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            sensors = []
            for gpu in gpus:
                if gpu.temperature is not None:
                    sensor = TempSensor(
                        name="nvidia_gpu",
                        label=f"GPU: {gpu.name}",
                        current=float(gpu.temperature),
                        high=85.0,
                        critical=95.0
                    )
                    sensor.status = self._classify(float(gpu.temperature), 85.0, 95.0)
                    sensors.append(sensor)
            return sensors
        except Exception:
            return []

    def _amd_temps(self) -> list[TempSensor]:
        """GPU AMD via psutil sensors."""
        sensors = []
        try:
            temps = psutil.sensors_temperatures()
            amd_keys = [k for k in temps if "amdgpu" in k.lower() or "radeon" in k.lower()]
            for key in amd_keys:
                for entry in temps[key]:
                    sensor = TempSensor(
                        name=key,
                        label=entry.label or "GPU AMD",
                        current=round(entry.current, 1),
                        high=entry.high,
                        critical=entry.critical
                    )
                    sensor.status = self._classify(sensor.current, sensor.high, sensor.critical)
                    sensors.append(sensor)
        except Exception:
            pass
        return sensors

    # ------------------------------------------------------------------
    # Todos os sensores
    # ------------------------------------------------------------------
    def get_all_temps(self) -> list[TempSensor]:
        """Retorna todos os sensores de temperatura (CPU + GPU)."""
        now = time.time()
        if now - self._last_update < self._cache_ttl and self._cache:
            return self._cache

        sensors = self.get_cpu_temps() + self.get_gpu_temps()
        self._cache = sensors
        self._last_update = now
        return sensors

    def get_max_cpu_temp(self) -> Optional[float]:
        """Retorna a temperatura máxima de CPU encontrada."""
        cpu_sensors = self.get_cpu_temps()
        if not cpu_sensors:
            return None
        return max(s.current for s in cpu_sensors)

    def get_max_gpu_temp(self) -> Optional[float]:
        """Retorna a temperatura máxima de GPU encontrada."""
        gpu_sensors = self.get_gpu_temps()
        if not gpu_sensors:
            return None
        return max(s.current for s in gpu_sensors)

    def has_critical_temp(self) -> bool:
        """Retorna True se qualquer sensor estiver em estado crítico."""
        return any(s.status == "critical" for s in self.get_all_temps())

    def start_monitoring(self, callback, interval: float = 3.0):
        """
        Inicia monitoramento em background em thread separada.

        Args:
            callback: Função chamada com lista de TempSensor a cada atualização
            interval: Intervalo em segundos entre leituras
        """
        def _loop():
            while self._running:
                sensors = self.get_all_temps()
                callback(sensors)
                time.sleep(interval)

        self._running = True
        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        """Para o monitoramento em background."""
        self._running = False


# -----------------------------------------------------------------------
# Exemplo de integração com CustomTkinter
# -----------------------------------------------------------------------
INTEGRATION_EXAMPLE = '''
import customtkinter as ctk
from temperature_monitor import TemperatureMonitor

class TempTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.monitor = TemperatureMonitor()
        self.labels = {}
        self._build_ui()
        self.monitor.start_monitoring(self._on_update, interval=3)

    def _build_ui(self):
        ctk.CTkLabel(self, text="🌡️ Temperatura do Sistema",
                     font=("Arial", 16, "bold")).pack(pady=10)
        self.frame = ctk.CTkScrollableFrame(self)
        self.frame.pack(fill="both", expand=True, padx=10, pady=5)

    def _on_update(self, sensors):
        # Atualiza UI na thread principal
        self.after(0, self._refresh_labels, sensors)

    def _refresh_labels(self, sensors):
        for widget in self.frame.winfo_children():
            widget.destroy()
        for sensor in sensors:
            color = {"normal": "#00ff88", "warning": "#ffaa00", "critical": "#ff4444"}
            row = ctk.CTkFrame(self.frame)
            row.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(row, text=sensor.label, width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{sensor.current}°C",
                         text_color=color.get(sensor.status, "white"),
                         font=("Arial", 13, "bold")).pack(side="left", padx=5)
'''

if __name__ == "__main__":
    monitor = TemperatureMonitor()
    print("=== SpeedScan — Monitor de Temperatura ===\n")

    cpu_temps = monitor.get_cpu_temps()
    if cpu_temps:
        print("🖥️  CPU:")
        for s in cpu_temps:
            icon = "🔴" if s.status == "critical" else "🟡" if s.status == "warning" else "🟢"
            print(f"  {icon} {s.label}: {s.current}°C (high={s.high}, crit={s.critical})")
    else:
        print("⚠️  Temperatura de CPU não disponível nesta plataforma.")

    gpu_temps = monitor.get_gpu_temps()
    if gpu_temps:
        print("\n🎮  GPU:")
        for s in gpu_temps:
            icon = "🔴" if s.status == "critical" else "🟡" if s.status == "warning" else "🟢"
            print(f"  {icon} {s.label}: {s.current}°C")
    else:
        print("\n🎮  GPU: Não detectada ou sem suporte.")

    print(f"\n⚠️  Temp Crítica Detectada: {monitor.has_critical_temp()}")
