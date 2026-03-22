#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware information collection module.
Version 1.0.0
"""
import platform
import psutil
import subprocess
import logging

class HardwareInfo:
    def __init__(self, so, runner):
        self.so = so
        self.runner = runner

    def get_distro(self):
        if self.so == "Linux":
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=")[1].strip().strip('"')
            except Exception as e:
                logging.error(f"Error reading /etc/os-release: {e}")
            return f"{psutil.cpu_count()}-core"
        return platform.system() + " " + platform.release()

    def get_ram(self):
        try:
            mem = psutil.virtual_memory()
            total = mem.total // (1024**3)
            used = mem.used // (1024**3)
            return f"{used} GB / {total} GB"
        except:
            return "N/A"

    def get_gpu(self):
        try:
            if self.so == "Linux":
                out = subprocess.run(["lspci"], capture_output=True, text=True)
                for line in out.stdout.splitlines():
                    if "VGA" in line or "3D" in line:
                        return line.split(":")[2].strip()
            elif self.so == "Windows":
                out = subprocess.run(["wmic", "path", "win32_videocontroller", "get", "name"],
                                     capture_output=True, text=True)
                lines = out.stdout.splitlines()
                if len(lines) >= 2:
                    return lines[1].strip()
            elif self.so == "Darwin":
                out = subprocess.run(["system_profiler", "SPDisplaysDataType"],
                                     capture_output=True, text=True)
                for line in out.stdout.splitlines():
                    if "Chipset Model" in line:
                        return line.split(":")[1].strip()
        except:
            pass
        return "Unknown"

    def get_driver_info(self):
        """Get driver information and version checks"""
        info = {}
        
        if self.so == "Linux":
            # GPU drivers
            try:
                out = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], 
                                  capture_output=True, text=True)
                if out.returncode == 0:
                    info["nvidia_driver"] = out.stdout.strip()
                    info["nvidia_update"] = self._check_nvidia_update(out.stdout.strip())
            except:
                pass
            
            try:
                out = subprocess.run(["amdgpu-pro", "--version"], capture_output=True, text=True)
                if out.returncode == 0:
                    info["amd_driver"] = out.stdout.strip()
            except:
                pass
            
            # Intel drivers usually come with kernel
            info["intel_driver"] = f"Kernel {platform.release().split('-')[0]}"
            
            # Network drivers
            try:
                out = subprocess.run(["lspci", "-nn"], capture_output=True, text=True)
                network_drivers = []
                for line in out.stdout.splitlines():
                    if "Network controller" in line or "Ethernet" in line:
                        network_drivers.append(line.strip())
                info["network_drivers"] = network_drivers
            except:
                pass
                
        return info
    
    def _check_nvidia_update(self, current_version):
        """Check if NVIDIA driver has updates available"""
        # Simplified check - in real implementation would query NVIDIA servers
        latest_known = "550.90"  # This would be fetched from NVIDIA API
        try:
            current_parts = [int(x) for x in current_version.split('.')]
            latest_parts = [int(x) for x in latest_known.split('.')]
            return latest_parts > current_parts
        except:
            return False
