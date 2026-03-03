#!/usr/bin/env python3
# core/temperature_monitor.py

import psutil
import platform
import subprocess
import re
from typing import Dict, Optional

class TemperatureMonitor:
    """
    Monitora temperaturas de CPU, GPU e discos.
    Utiliza psutil, nvidia-smi, smartctl e sensores do sistema.
    """

    def __init__(self):
        self.system = platform.system()
        self.has_nvidia = self._check_nvidia()
        self.has_smart = self._check_smartctl()

    def _check_nvidia(self) -> bool:
        """Verifica se há GPU NVIDIA e nvidia-smi disponível."""
        try:
            subprocess.run(['nvidia-smi', '--version'],
                           capture_output=True, check=True)
            return True
        except:
            return False

    def _check_smartctl(self) -> bool:
        """Verifica se smartctl está disponível."""
        try:
            subprocess.run(['smartctl', '--version'],
                           capture_output=True, check=True)
            return True
        except:
            return False

    def get_all_temperatures(self) -> Dict[str, Optional[float]]:
        """
        Retorna um dicionário com temperaturas disponíveis.
        Ex: {'cpu': 45.0, 'gpu': 52.0, 'sda': 35.0, ...}
        """
        temps = {}

        # CPU via psutil
        cpu_temps = self._get_cpu_temperatures()
        if cpu_temps:
            temps.update(cpu_temps)

        # GPU NVIDIA
        if self.has_nvidia:
            gpu_temp = self._get_nvidia_gpu_temp()
            if gpu_temp is not None:
                temps['gpu'] = gpu_temp

        # Discos via smartctl
        if self.has_smart:
            disk_temps = self._get_disk_temperatures()
            temps.update(disk_temps)

        # Fallback: sensores Linux
        if not temps and self.system == 'Linux':
            temps = self._get_linux_sensors()

        return temps

    def _get_cpu_temperatures(self) -> Dict[str, float]:
        """Obtém temperaturas da CPU via psutil."""
        temps = {}
        try:
            sensors = psutil.sensors_temperatures()
            if 'coretemp' in sensors:
                for i, entry in enumerate(sensors['coretemp']):
                    temps[f'cpu_core{i}'] = entry.current
            elif 'cpu_thermal' in sensors:  # Raspberry Pi
                temps['cpu'] = sensors['cpu_thermal'][0].current
            elif 'acpitz' in sensors:
                temps['cpu'] = sensors['acpitz'][0].current
        except:
            pass
        return temps

    def _get_nvidia_gpu_temp(self) -> Optional[float]:
        """Obtém temperatura da GPU NVIDIA via nvidia-smi."""
        try:
            output = subprocess.check_output(
                ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
                universal_newlines=True
            ).strip()
            return float(output.split('\n')[0])
        except:
            return None

    def _get_disk_temperatures(self) -> Dict[str, float]:
        """Obtém temperaturas de discos via smartctl."""
        temps = {}
        try:
            # Listar discos
            output = subprocess.check_output(['smartctl', '--scan'], universal_newlines=True)
            for line in output.split('\n'):
                if '/dev/' in line:
                    dev = line.split()[0]
                    try:
                        # Obter temperatura
                        out = subprocess.check_output(
                            ['smartctl', '-A', dev],
                            universal_newlines=True,
                            stderr=subprocess.DEVNULL
                        )
                        # Procurar por linhas com Temperature_Celsius
                        for line2 in out.split('\n'):
                            if 'Temperature_Celsius' in line2:
                                parts = line2.split()
                                if len(parts) >= 10:
                                    temp = float(parts[9])
                                    temps[dev.replace('/dev/', '')] = temp
                                    break
                    except:
                        continue
        except:
            pass
        return temps

    def _get_linux_sensors(self) -> Dict[str, float]:
        """Fallback: usa o comando 'sensors' do Linux."""
        temps = {}
        try:
            output = subprocess.check_output(['sensors'], universal_newlines=True)
            # Procurar por linhas com +XX.0°C ou similar
            for line in output.split('\n'):
                match = re.search(r'([+-]\d+\.\d+)°C', line)
                if match:
                    # Pega o primeiro sensor encontrado
                    temps['sensor'] = float(match.group(1))
                    break
        except:
            pass
        return temps
