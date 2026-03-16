#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows cleaner module (bloatware, telemetry and AI components)
Exclusive for Windows systems.
"""
import subprocess
import logging
import os
from typing import List, Dict, Callable, Optional
from pathlib import Path

from core.i18n import _


class WindowsCleaner:
    """
    Handles removal of bloatware, telemetry and AI components from Windows.
    """
    def __init__(self):
        self.bloatware_list = self._get_bloatware_list()
        self.ai_components = self._get_ai_components()
        self.telemetry_commands = self._get_telemetry_commands()
        self.cleanup_commands = self._get_cleanup_commands()

    def _get_bloatware_list(self) -> List[Dict[str, str]]:
        """Return a list of known bloatware with name and package name."""
        return [
            {"name": _("Xbox App"), "package": "Microsoft.XboxApp", "description": _("Xbox application")},
            {"name": _("Xbox Game Bar"), "package": "Microsoft.XboxGamingOverlay", "description": _("Xbox game bar")},
            {"name": _("Xbox Identity Provider"), "package": "Microsoft.XboxIdentityProvider", "description": _("Xbox identity provider")},
            {"name": _("Xbox Speech to Text Overlay"), "package": "Microsoft.XboxSpeechToTextOverlay", "description": _("Xbox speech overlay")},
            {"name": _("Candy Crush"), "package": "king.com.CandyCrushSaga", "description": _("Candy Crush game")},
            {"name": _("Skype"), "package": "Microsoft.SkypeApp", "description": _("Skype")},
            {"name": _("OneDrive"), "package": "Microsoft.OneDrive", "description": _("OneDrive")},
            {"name": _("Bing Weather"), "package": "Microsoft.BingWeather", "description": _("Bing Weather")},
            {"name": _("Bing News"), "package": "Microsoft.BingNews", "description": _("Bing News")},
            {"name": _("Bing Sports"), "package": "Microsoft.BingSports", "description": _("Bing Sports")},
            {"name": _("Bing Finance"), "package": "Microsoft.BingFinance", "description": _("Bing Finance")},
            {"name": _("3D Builder"), "package": "Microsoft.3DBuilder", "description": _("3D Builder")},
            {"name": _("People"), "package": "Microsoft.People", "description": _("People")},
            {"name": _("Zune Music"), "package": "Microsoft.ZuneMusic", "description": _("Zune Music")},
            {"name": _("Zune Video"), "package": "Microsoft.ZuneVideo", "description": _("Zune Video")},
            {"name": _("Mixed Reality Portal"), "package": "Microsoft.MixedReality.Portal", "description": _("Mixed Reality Portal")},
            {"name": _("Office Hub"), "package": "Microsoft.MicrosoftOfficeHub", "description": _("Office Hub")},
            {"name": _("Solitaire Collection"), "package": "Microsoft.MicrosoftSolitaireCollection", "description": _("Solitaire Collection")},
            {"name": _("Sticky Notes"), "package": "Microsoft.MicrosoftStickyNotes", "description": _("Sticky Notes")},
            {"name": _("Windows Camera"), "package": "Microsoft.WindowsCamera", "description": _("Windows Camera")},
            {"name": _("Windows Communications Apps"), "package": "Microsoft.WindowsCommunicationsApps", "description": _("Communications apps")},
            {"name": _("Windows Feedback Hub"), "package": "Microsoft.WindowsFeedbackHub", "description": _("Feedback Hub")},
            {"name": _("Windows Maps"), "package": "Microsoft.WindowsMaps", "description": _("Windows Maps")},
            {"name": _("Windows Sound Recorder"), "package": "Microsoft.WindowsSoundRecorder", "description": _("Sound Recorder")},
            {"name": _("Your Phone"), "package": "Microsoft.YourPhone", "description": _("Your Phone")},
            {"name": _("Get Help"), "package": "Microsoft.GetHelp", "description": _("Get Help")},
            {"name": _("Messaging"), "package": "Microsoft.Messaging", "description": _("Messaging")},
            {"name": _("Office OneNote"), "package": "Microsoft.Office.OneNote", "description": _("OneNote")},
            {"name": _("Outlook for Windows"), "package": "Microsoft.OutlookForWindows", "description": _("Outlook")},
            {"name": _("Paint 3D"), "package": "Microsoft.Paint3D", "description": _("Paint 3D")},
            {"name": _("Print 3D"), "package": "Microsoft.Print3D", "description": _("Print 3D")},
            {"name": _("Snip & Sketch"), "package": "Microsoft.ScreenSketch", "description": _("Snip & Sketch")},
            {"name": _("Teams"), "package": "Microsoft.Teams", "description": _("Microsoft Teams")},
            {"name": _("Todos"), "package": "Microsoft.Todos", "description": _("Microsoft To Do")},
            {"name": _("Wallet"), "package": "Microsoft.Wallet", "description": _("Wallet")},
            {"name": _("Windows Alarms"), "package": "Microsoft.WindowsAlarms", "description": _("Alarms")},
            {"name": _("Windows Calculator"), "package": "Microsoft.WindowsCalculator", "description": _("Calculator")},
            {"name": _("Windows Clock"), "package": "Microsoft.WindowsClock", "description": _("Clock")},
        ]

    def _get_ai_components(self) -> List[Dict[str, str]]:
        """
        List Windows 11 AI components and commands to disable them.
        """
        return [
            {"name": _("Copilot"), "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f'},
            {"name": _("Windows Recall"), "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI" /v DisableAIDataAnalysis /t REG_DWORD /d 1 /f'},
            {"name": _("Cortana"), "cmd": "Get-AppxPackage *cortana* | Remove-AppxPackage"},
            {"name": _("Web Search in Start"), "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f'},
            {"name": _("News & Interests"), "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Feeds" /v ShellFeedsTaskbarEnabled /t REG_DWORD /d 0 /f'},
            {"name": _("Widgets"), "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarDa /t REG_DWORD /d 0 /f'},
        ]

    def _get_telemetry_commands(self) -> List[str]:
        """
        Commands to disable telemetry and data collection.
        """
        return [
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
            'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy" /v TailoredExperiencesWithDiagnosticDataEnabled /t REG_DWORD /d 0 /f',
            'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy" /v LetAppsRunInBackground /t REG_DWORD /d 2 /f',
            'schtasks /change /tn "Microsoft\\Windows\\Application Experience\\Microsoft Compatibility Appraiser" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Application Experience\\ProgramDataUpdater" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Customer Experience Improvement Program\\Consolidator" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Customer Experience Improvement Program\\UsbCeip" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\DiskDiagnostic\\Microsoft-Windows-DiskDiagnosticDataCollector" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Feedback\\Siuf\\DmClient" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Feedback\\Siuf\\DmClientOnScenarioDownload" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Location\\Notifications" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\PI\\Sqm-Tasks" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Power Efficiency Diagnostics\\AnalyzeSystem" /disable',
            'schtasks /change /tn "Microsoft\\Windows\\Windows Error Reporting\\QueueReporting" /disable',
        ]

    def _get_cleanup_commands(self) -> List[str]:
        """
        Commands to clean temporary files and cache.
        """
        return [
            "del /q /f /s %temp%\\*",
            "del /q /f /s C:\\Windows\\Temp\\*",
            "del /q /f /s C:\\Windows\\Prefetch\\*",
            "del /q /f /s C:\\Windows\\SoftwareDistribution\\Download\\*",
            "cleanmgr /sagerun:1 | exit",  # Executes disk cleanup with default settings
        ]

    def get_installed_bloatware(self) -> List[Dict[str, str]]:
        """
        Verify which bloatware from the list is installed.
        """
        installed = []
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-AppxPackage | Select-Object -ExpandProperty PackageFullName"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore"
            )
            if result.returncode != 0:
                logging.error(_("Error executing PowerShell: {stderr}").format(stderr=result.stderr))
                return installed

            installed_packages = result.stdout.lower()
            for app in self.bloatware_list:
                if app["package"].lower() in installed_packages:
                    installed.append(app)
        except Exception as e:
            logging.error(_("Exception while verifying bloatware: {error}").format(error=e))
        return installed

    def remove_package(self, package_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Remove an Appx package by name.
        """
        cmd = f'powershell -Command "Get-AppxPackage *{package_name}* | Remove-AppxPackage -ErrorAction SilentlyContinue"'
        return self._run_command(cmd, log_callback)

    def remove_multiple_packages(self, packages: List[str], log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Remove multiple packages.
        """
        success = True
        for pkg in packages:
            if not self.remove_package(pkg, log_callback):
                success = False
        return success

    def disable_telemetry(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Execute all telemetry disable commands.
        """
        success = True
        for cmd in self.telemetry_commands:
            if not self._run_command(cmd, log_callback):
                success = False
        return success

    def disable_ai_component(self, component_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Disable a specific AI component.
        """
        for comp in self.ai_components:
            if comp["name"].lower() == component_name.lower():
                return self._run_command(comp["cmd"], log_callback)
        return False

    def disable_all_ai(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Disable all AI components.
        """
        success = True
        for comp in self.ai_components:
            if not self._run_command(comp["cmd"], log_callback):
                success = False
        return success

    def run_cleanup(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Execute temporary file cleanup commands.
        """
        success = True
        for cmd in self.cleanup_commands:
            if not self._run_command(cmd, log_callback):
                success = False
        return success

    def _run_command(self, cmd: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Execute a command in the shell and return True if successful.
        """
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            stdout, stderr = proc.communicate(timeout=120)
            if log_callback:
                if stdout:
                    log_callback(stdout)
                if stderr:
                    log_callback(_("ERROR: {stderr}").format(stderr=stderr))
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            if log_callback:
                log_callback(_("Command exceeded time limit and was killed."))
            return False
        except Exception as e:
            if log_callback:
                log_callback(_("Exception: {error}").format(error=e))
            return False
