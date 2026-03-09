#!/usr/bin/env python3
import logging
# Módulo de monitoramento de temperaturas (CPU, GPU, discos)
# Versão 0.3.1-beta

import psutil
import subprocess

class TemperatureMonitor:
    def __init__(self):
        self.sensors = {}

    def get_cpu_temperatures(self):
        temps = {}
        try:
            thermal = psutil.sensors_temperatures()
            if 'coretemp' in thermal:
                for entry in thermal['coretemp']:
                    label = entry.label or f"Core {len(temps)}"
                    temps[f"CPU {label}"] = round(entry.current, 1)
            elif 'k10temp' in thermal:
                for entry in thermal['k10temp']:
                    temps["CPU Package"] = round(entry.current, 1)
            else:
                try:
                    with open("/sys/class/thermal/thermal_zone0/temp") as f:
                        temp = int(f.read().strip()) / 1000.0
                        temps["CPU"] = round(temp, 1)
                except:
                    pass
        except Exception as e:
            logging.error(f"Erro ao obter temperaturas da CPU: {e}")
        return temps

    def get_gpu_temperatures(self):
        temps = {}
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"], 
                                 capture_output=True, text=True, timeout=2)
            if out.returncode == 0:
                lines = out.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        temps[f"GPU {i}"] = round(float(line.strip()), 1)
        except:
            pass
        return temps

    def get_disk_temperatures(self):
        temps = {}
        try:
            out = subprocess.run(["lsblk", "-d", "-o", "NAME"], capture_output=True, text=True)
            disks = out.stdout.splitlines()[1:]
            for disk in disks:
                disk = disk.strip()
                if disk:
                    smart = subprocess.run(["sudo", "smartctl", "-A", f"/dev/{disk}"], 
                                          capture_output=True, text=True, timeout=2)
                    for line in smart.stdout.splitlines():
                        if "Temperature_Celsius" in line:
                            parts = line.split()
                            if len(parts) >= 10:
                                temp = parts[9]
                                temps[f"Disk {disk}"] = round(float(temp), 1)
                                break
        except:
            pass
        return temps

    def get_all_temperatures(self):
        temps = {}
        temps.update(self.get_cpu_temperatures())
        temps.update(self.get_gpu_temperatures())
        temps.update(self.get_disk_temperatures())
        return temps
