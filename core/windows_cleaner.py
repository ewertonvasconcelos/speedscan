#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows cleaner module (bloatware, telemetry and AI components)
Exclusive for Windows systems.
"""
import subprocess
import logging
from typing import List, Dict, Callable, Optional

class WindowsCleaner:
    def __init__(self):
        self.bloatware_list = self._get_bloatware_list()
        self.ai_components = self._get_ai_components()
        self.telemetry_commands = self._get_telemetry_commands()
        self.cleanup_commands = self._get_cleanup_commands()

    def _get_bloatware_list(self) -> List[Dict[str, str]]:
        return [
            {"name": "Xbox App", "package": "Microsoft.XboxApp", "description": "Xbox application"},
            {"name": "Xbox Game Bar", "package": "Microsoft.XboxGamingOverlay", "description": "Xbox game bar"},
            {"name": "Xbox Identity Provider", "package": "Microsoft.XboxIdentityProvider", "description": "Xbox identity provider"},
            {"name": "Xbox Speech to Text Overlay", "package": "Microsoft.XboxSpeechToTextOverlay", "description": "Xbox speech overlay"},
            {"name": "Candy Crush", "package": "king.com.CandyCrushSaga", "description": "Candy Crush game"},
            {"name": "Skype", "package": "Microsoft.SkypeApp", "description": "Skype"},
            {"name": "OneDrive", "package": "Microsoft.OneDrive", "description": "OneDrive"},
            {"name": "Bing Weather", "package": "Microsoft.BingWeather", "description": "Bing Weather"},
            {"name": "Bing News", "package": "Microsoft.BingNews", "description": "Bing News"},
            {"name": "Bing Sports", "package": "Microsoft.BingSports", "description": "Bing Sports"},
            {"name": "Bing Finance", "package": "Microsoft.BingFinance", "description": "Bing Finance"},
            {"name": "3D Builder", "package": "Microsoft.3DBuilder", "description": "3D Builder"},
            {"name": "People", "package": "Microsoft.People", "description": "People"},
            {"name": "Zune Music", "package": "Microsoft.ZuneMusic", "description": "Zune Music"},
            {"name": "Zune Video", "package": "Microsoft.ZuneVideo", "description": "Zune Video"},
            {"name": "Mixed Reality Portal", "package": "Microsoft.MixedReality.Portal", "description": "Mixed Reality Portal"},
            {"name": "Office Hub", "package": "Microsoft.MicrosoftOfficeHub", "description": "Office Hub"},
            {"name": "Solitaire Collection", "package": "Microsoft.MicrosoftSolitaireCollection", "description": "Solitaire Collection"},
            {"name": "Sticky Notes", "package": "Microsoft.MicrosoftStickyNotes", "description": "Sticky Notes"},
            {"name": "Windows Camera", "package": "Microsoft.WindowsCamera", "description": "Windows Camera"},
            {"name": "Windows Communications Apps", "package": "Microsoft.WindowsCommunicationsApps", "description": "Communications apps"},
            {"name": "Windows Feedback Hub", "package": "Microsoft.WindowsFeedbackHub", "description": "Feedback Hub"},
            {"name": "Windows Maps", "package": "Microsoft.WindowsMaps", "description": "Windows Maps"},
            {"name": "Windows Sound Recorder", "package": "Microsoft.WindowsSoundRecorder", "description": "Sound Recorder"},
            {"name": "Your Phone", "package": "Microsoft.YourPhone", "description": "Your Phone"},
            {"name": "Get Help", "package": "Microsoft.GetHelp", "description": "Get Help"},
            {"name": "Messaging", "package": "Microsoft.Messaging", "description": "Messaging"},
            {"name": "Office OneNote", "package": "Microsoft.Office.OneNote", "description": "OneNote"},
            {"name": "Outlook for Windows", "package": "Microsoft.OutlookForWindows", "description": "Outlook"},
            {"name": "Paint 3D", "package": "Microsoft.Paint3D", "description": "Paint 3D"},
            {"name": "Print 3D", "package": "Microsoft.Print3D", "description": "Print 3D"},
            {"name": "Snip & Sketch", "package": "Microsoft.ScreenSketch", "description": "Snip & Sketch"},
            {"name": "Teams", "package": "Microsoft.Teams", "description": "Microsoft Teams"},
            {"name": "Todos", "package": "Microsoft.Todos", "description": "Microsoft To Do"},
            {"name": "Wallet", "package": "Microsoft.Wallet", "description": "Wallet"},
            {"name": "Windows Alarms", "package": "Microsoft.WindowsAlarms", "description": "Alarms"},
            {"name": "Windows Calculator", "package": "Microsoft.WindowsCalculator", "description": "Calculator"},
            {"name": "Windows Clock", "package": "Microsoft.WindowsClock", "description": "Clock"},
        ]

    def _get_ai_components(self) -> List[Dict[str, str]]:
        return [
            {"name": "Copilot", "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f'},
            {"name": "Windows Recall", "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI" /v DisableAIDataAnalysis /t REG_DWORD /d 1 /f'},
            {"name": "Cortana", "cmd": "Get-AppxPackage *cortana* | Remove-AppxPackage"},
            {"name": "Web Search in Start", "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f'},
            {"name": "News & Interests", "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Feeds" /v ShellFeedsTaskbarEnabled /t REG_DWORD /d 0 /f'},
            {"name": "Widgets", "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarDa /t REG_DWORD /d 0 /f'},
        ]

    def _get_telemetry_commands(self) -> List[str]:
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
        return [
            "del /q /f /s %temp%\\*",
            "del /q /f /s C:\\Windows\\Temp\\*",
            "del /q /f /s C:\\Windows\\Prefetch\\*",
            "del /q /f /s C:\\Windows\\SoftwareDistribution\\Download\\*",
            "cleanmgr /sagerun:1 | exit",
        ]

    def get_installed_bloatware(self) -> List[Dict[str, str]]:
        installed = []
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-AppxPackage | Select-Object -ExpandProperty PackageFullName"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore"
            )
            if result.returncode != 0:
                logging.error(f"Error executing PowerShell: {result.stderr}")
                return installed

            installed_packages = result.stdout.lower()
            for app in self.bloatware_list:
                if app["package"].lower() in installed_packages:
                    installed.append(app)
        except Exception as e:
            logging.error(f"Exception while verifying bloatware: {e}")
        return installed

    def remove_package(self, package_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        cmd = f'powershell -Command "Get-AppxPackage *{package_name}* | Remove-AppxPackage -ErrorAction SilentlyContinue"'
        return self._run_command(cmd, log_callback)

    def remove_multiple_packages(self, packages: List[str], log_callback: Optional[Callable[[str], None]] = None) -> bool:
        success = True
        for pkg in packages:
            if not self.remove_package(pkg, log_callback):
                success = False
        return success

    def disable_telemetry(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        success = True
        for cmd in self.telemetry_commands:
            if not self._run_command(cmd, log_callback):
                success = False
        return success

    def disable_ai_component(self, component_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        for comp in self.ai_components:
            if comp["name"].lower() == component_name.lower():
                return self._run_command(comp["cmd"], log_callback)
        return False

    def disable_all_ai(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        success = True
        for comp in self.ai_components:
            if not self._run_command(comp["cmd"], log_callback):
                success = False
        return success

    def run_cleanup(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        success = True
        for cmd in self.cleanup_commands:
            if not self._run_command(cmd, log_callback):
                success = False
        return success

    def _run_command(self, cmd: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
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
                    log_callback(f"ERROR: {stderr}")
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            if log_callback:
                log_callback("Command exceeded time limit and was killed.")
            return False
        except Exception as e:
            if log_callback:
                log_callback(f"Exception: {e}")
            return False
