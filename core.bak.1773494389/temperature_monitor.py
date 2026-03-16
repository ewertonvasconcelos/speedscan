#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temperature monitoring module for CPU, GPU, and disks.
Version 1.0.0
"""
import psutil
import subprocess


class TemperatureMonitor:
    """
    Monitors temperatures of CPU, GPU, and disks.
    """
    def __init__(self):
        self.sensors = {}

    def get_cpu_temperatures(self):
        """
        Get CPU temperatures using psutil sensors_temperatures().

        Returns:
            dict: A dictionary with labels like "CPU Core 0" and temperature values.
        """
        temps = {}
        try:
            thermal = psutil.sensors_temperatures()
            if "coretemp" in thermal:
                for entry in thermal["coretemp"]:
                    label = entry.label or f"Core {len(temps)}"
                    temps[f"CPU {label}"] = round(entry.current, 1)
            elif "k10temp" in thermal:
                for entry in thermal["k10temp"]:
                    temps["CPU Package"] = round(entry.current, 1)
            else:
                # Fallback: try reading from /sys/class/thermal/thermal_zone0/temp
                try:
                    with open("/sys/class/thermal/thermal_zone0/temp") as f:
                        temp = int(f.read().strip()) / 1000.0
                        temps["CPU"] = round(temp, 1)
                except Exception:
                    # Ignore errors
                    pass
        except Exception:
            # Log error
            pass
        return temps

    def get_gpu_temperatures(self):
        """
        Get GPU temperatures using nvidia-smi if available.

        Returns:
            dict: Dictionary with GPU indices and temperatures.
        """
        temps = {}
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                                 capture_output=True, text=True, timeout=2)
            if out.returncode == 0:
                lines = out.stdout.strip().split("\n")
                for i, line in enumerate(lines):
                    if line.strip():
                        temps[f"GPU {i}"] = round(float(line.strip()), 1)
        except Exception:
            # If nvidia-smi not available, ignore
            pass
        return temps

    def get_disk_temperatures(self):
        """
        Get disk temperatures using smartctl (requires sudo).

        Returns:
            dict: Dictionary with disk names and temperatures.
        """
        temps = {}
        try:
            out = subprocess.run(["lsblk", "-d", "-o", "NAME"], capture_output=True, text=True)
            disks = out.stdout.splitlines()[1:]  # skip header
            for disk in disks:
                disk = disk.strip()
                if disk:
                    try:
                        smart = subprocess.run(["sudo", "smartctl", "-A", f"/dev/{disk}"],
                                               capture_output=True, text=True, timeout=2)
                        for line in smart.stdout.splitlines():
                            if "Temperature_Celsius" in line:
                                parts = line.split()
                                if len(parts) >= 10:
                                    temp = parts[9]
                                    temps[f"Disk {disk}"] = round(float(temp), 1)
                                break
                    except Exception:
                        pass
        except Exception:
            pass
        return temps

    def get_all_temperatures(self):
        """
        Get all temperatures from CPU, GPU, and disks.

        Returns:
            dict: Combined dictionary of all temperature readings.
        """
        temps = {}
        temps.update(self.get_cpu_temperatures())
        temps.update(self.get_gpu_temperatures())
        temps.update(self.get_disk_temperatures())
        return temps
