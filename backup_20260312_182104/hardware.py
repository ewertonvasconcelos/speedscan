#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware information collection module.
Version 1.0.0
"""

import platform
import psutil
import subprocess
import re
import time
import logging

from core import config


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
            total = mem.total // (1024 ** 3)
            used = mem.used // (1024 ** 3)
            return f"{used} GB / {total} GB"
        except Exception as e:
            logging.error(f"Error getting RAM info: {e}")
            return "N/A"

    def get_gpu(self):
        try:
            if self.so == "Linux":
                out = subprocess.run(["lspci"], capture_output=True, text=True)
                for line in out.stdout.splitlines():
                    if "VGA" in line or "3D" in line:
                        return line.split(":")[2].strip()
            elif self.so == "Windows":
                out = subprocess.run(["wmic", "path", "win32_videocontroller", "get", "name"], capture_output=True, text=True)
                lines = out.stdout.splitlines()
                if len(lines) >= 2:
                    return lines[1].strip()
            elif self.so == "Darwin":
                out = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True)
                for line in out.stdout.splitlines():
                    if "Chipset Model" in line:
                        return line.split(":")[1].strip()
        except Exception as e:
            logging.error(f"Error in get_gpu: {e}")
            return "Unknown"
