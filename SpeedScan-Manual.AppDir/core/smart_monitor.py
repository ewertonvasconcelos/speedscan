#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S.M.A.R.T. monitoring module for disks.
Version 1.0.0
"""
import logging
import subprocess
import re

class SmartMonitor:
    def __init__(self):
        self.disk_status = {}

    def get_smart_info(self, disk="/dev/sda"):
        try:
            result = subprocess.run(
                ["sudo", "smartctl", "-H", disk],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout
        except Exception as e:
            logging.error(f"Error fetching SMART data for disk {disk}: {e}")
            return None

    def get_summary_text(self):
        try:
            out = subprocess.run(["lsblk", "-d", "-o", "NAME"], capture_output=True, text=True)
            disks = out.stdout.splitlines()[1:]
            summary = []
            for disk in disks:
                disk = disk.strip()
                if not disk:
                    continue
                smart = self.get_smart_info(f"/dev/{disk}")
                if smart:
                    match = re.search(r"SMART overall-health self-assessment test result: (\w+)", smart)
                    if match:
                        status = match.group(1)
                        summary.append(f"{disk}: {status}")
                    else:
                        summary.append(f"{disk}: Unknown")
                else:
                    summary.append(f"{disk}: Not supported")
            return "\n".join(summary) if summary else "No disk found"
        except Exception as e:
            logging.error(f"Error generating SMART summary: {e}")
            return "Error fetching S.M.A.R.T. information"

    def get_status_color(self):
        try:
            out = subprocess.run(["lsblk", "-d", "-o", "NAME"], capture_output=True, text=True)
            disks = out.stdout.splitlines()[1:]
            any_failed = False
            any_unknown = False
            for disk in disks:
                disk = disk.strip()
                if not disk:
                    continue
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
            if any_unknown:
                return "yellow"
            return "green"
        except Exception as e:
            logging.error(f"Error determining SMART status color: {e}")
            return "yellow"
