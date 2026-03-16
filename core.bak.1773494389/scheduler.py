#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic task scheduler module (cron, task scheduler, launchd).
Version 1.0.0
"""
import logging
import subprocess
import os
from pathlib import Path

from core import config


class Scheduler:
    """
    Manages scheduled tasks using the native system scheduler:
    - Linux: cron
    - Windows: Task Scheduler
    - macOS: launchd
    """
    def __init__(self, so, log_dir, agent_script):
        """
        Initialize the scheduler.

        Args:
            so (str): Operating system ("Linux", "Windows", "Darwin").
            log_dir (Path): Directory where scheduler logs will be stored.
            agent_script (Path): Path to the speedscan-agent.py script.
        """
        self.so = so
        self.log_dir = log_dir
        self.agent_script = agent_script

    def create_schedule(self, config):
        """
        Create a scheduled task based on the given configuration.

        Args:
            config (dict): Schedule configuration with keys:
                enabled (bool)
                tasks (list of str)
                hour (str) in "HH:MM" format
                frequency (str): "hourly", "daily", "weekly", "monthly"
                day_of_week (str): for weekly (e.g., "monday")
                day_of_month (int): for monthly
                interval_days (int): for custom interval
                elevated (bool): whether to run with admin privileges
        """
        if not config.get("enabled"):
            self.remove_schedule()
            return

        tasks = config.get("tasks", [])
        hour = config.get("hour", "03:00")
        freq = config.get("frequency", "daily")
        elevated = config.get("elevated", False)

        # Build command line
        cmd = f"python3 {self.agent_script} --tasks {','.join(tasks)}"
        if elevated:
            cmd = "sudo " + cmd
        log_file = self.log_dir / "scheduler.log"

        if self.so == "Linux":
            self._create_cron(cmd, freq, hour, config)
        elif self.so == "Windows":
            self._create_task_scheduler(cmd, freq, hour, config)
        elif self.so == "Darwin":
            self._create_launchd(cmd, freq, hour, config)

    def remove_schedule(self):
        """Remove any existing scheduled task for SpeedScan."""
        if self.so == "Linux":
            subprocess.run("crontab -l | grep -v speedscan-agent | crontab -", shell=True)
        elif self.so == "Windows":
            subprocess.run("schtasks /delete /tn SpeedScanAgent /f", shell=True)
        elif self.so == "Darwin":
            subprocess.run("launchctl unload ~/Library/LaunchAgents/com.speedscan.agent.plist 2>/dev/null", shell=True)
            (Path.home() / "Library/LaunchAgents/com.speedscan.agent.plist").unlink(missing_ok=True)

    def _create_cron(self, cmd, freq, hour, config):
        """Create a cron job on Linux."""
        hour_part, minute_part = hour.split(":")

        if freq == "hourly":
            cron_line = f"{minute_part} * * * * {cmd} >> {self.log_dir}/cron.log 2>&1"
        elif freq == "daily":
            cron_line = f"{minute_part} {hour_part} * * * {cmd} >> {self.log_dir}/cron.log 2>&1"
        elif freq == "weekly":
            dow = config.get("day_of_week", "monday").lower()[:3]  # mon, tue, etc.
            cron_line = f"{minute_part} {hour_part} * * {dow} {cmd} >> {self.log_dir}/cron.log 2>&1"
        elif freq == "monthly":
            dom = config.get("day_of_month", 1)
            cron_line = f"{minute_part} {hour_part} {dom} * * {cmd} >> {self.log_dir}/cron.log 2>&1"
        else:
            return

        # Append to crontab
        subprocess.run(f"(crontab -l 2>/dev/null; echo \"{cron_line}\") | crontab -", shell=True)

    def _create_task_scheduler(self, cmd, freq, hour, config):
        """Create a task in Windows Task Scheduler."""
        hour_part, minute_part = hour.split(":")

        if freq == "hourly":
            repetition = "/ri 60"  # repeat every 60 minutes
            sc_daily = "/sc daily"  # base daily with repetition
        elif freq == "daily":
            repetition = ""
            sc_daily = f"/sc daily /st {hour}"
        elif freq == "weekly":
            dow = config.get("day_of_week", "monday").capitalize()
            repetition = ""
            sc_daily = f"/sc weekly /d {dow} /st {hour}"
        elif freq == "monthly":
            dom = config.get("day_of_month", 1)
            repetition = ""
            sc_daily = f"/sc monthly /d {dom} /st {hour}"
        else:
            return

        # Create task
        task_cmd = f"schtasks /create /tn SpeedScanAgent /tr \"{cmd}\" {sc_daily} {repetition} /f"
        subprocess.run(task_cmd, shell=True)

    def _create_launchd(self, cmd, freq, hour, config):
        """Create a launchd plist on macOS."""
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.speedscan.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>{cmd}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{int(hour.split(":")[0])}</integer>
        <key>Minute</key>
        <integer>{int(hour.split(":")[1])}</integer>"""

        if freq == "weekly":
            dow = config.get("day_of_week", "monday").lower()
            dow_map = {"monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4, "friday": 5, "saturday": 6, "sunday": 0}
            plist_content += f"""
        <key>Weekday</key>
        <integer>{dow_map[dow]}</integer>"""
        elif freq == "monthly":
            dom = config.get("day_of_month", 1)
            plist_content += f"""
        <key>Day</key>
        <integer>{dom}</integer>"""

        plist_content += f"""
    </dict>
    <key>StandardOutPath</key>
    <string>{self.log_dir}/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>{self.log_dir}/launchd.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>"""

        plist_path = Path.home() / "Library/LaunchAgents/com.speedscan.agent.plist"
        plist_path.write_text(plist_content)
        subprocess.run(f"launchctl load {plist_path}", shell=True)
