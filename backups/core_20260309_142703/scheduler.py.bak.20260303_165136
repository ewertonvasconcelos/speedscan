#!/usr/bin/env python3
# core/scheduler.py
# =============================================================================
#   ███████╗██████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ █████╗ ███╗   ██╗
#   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║
#   ███████╗██████╔╝█████╗  █████╗  ██║  ██║█████╗  ██║     ███████║██╔██╗ ██║
#   ╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║  ██║██╔══╝  ██║     ██╔══██║██║╚██╗██║
#   ███████║██║     ███████╗███████╗██████╔╝███████╗╚██████╗██║  ██║██║ ╚████║
#   ╚══════╝╚═╝     ╚══════╝╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
# =============================================================================
# Agendador de tarefas automáticas
# Versão 0.3.1-beta
# =============================================================================

import subprocess
import os
from pathlib import Path

class Scheduler:
    def __init__(self, so, log_dir, agent_script):
        self.so = so
        self.log_dir = log_dir
        self.agent_script = agent_script

    def create_schedule(self, config):
        if not config['enabled']:
            self.remove_schedule()
            return

        tasks = config['tasks']
        hour = config['hour']
        freq = config['frequency']
        elevated = config['elevated']

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
        if self.so == "Linux":
            subprocess.run("crontab -l | grep -v speedscan-agent | crontab -", shell=True)
        elif self.so == "Windows":
            subprocess.run("schtasks /delete /tn SpeedScanAgent /f", shell=True)
        elif self.so == "Darwin":
            subprocess.run("launchctl unload ~/Library/LaunchAgents/com.speedscan.agent.plist 2>/dev/null", shell=True)
            (Path.home() / "Library/LaunchAgents/com.speedscan.agent.plist").unlink(missing_ok=True)

    def _create_cron(self, cmd, freq, hour, config):
        cron_line = f"{hour} * * * * {cmd} >> {self.log_dir}/cron.log 2>&1"
        subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron_line}") | crontab -', shell=True)

    def _create_task_scheduler(self, cmd, freq, hour, config):
        subprocess.run(f'schtasks /create /tn SpeedScanAgent /tr "{cmd}" /sc DAILY /st {hour}', shell=True)

    def _create_launchd(self, cmd, freq, hour, config):
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
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
        <integer>{int(hour.split(':')[0])}</integer>
        <key>Minute</key>
        <integer>{int(hour.split(':')[1])}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{self.log_dir}/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>{self.log_dir}/launchd.log</string>
</dict>
</plist>"""
        plist_path = Path.home() / "Library/LaunchAgents/com.speedscan.agent.plist"
        plist_path.write_text(plist)
        subprocess.run(f"launchctl load {plist_path}", shell=True)
