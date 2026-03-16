#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de limpeza do Windows (bloatware, telemetria e componentes de IA)
Uso exclusivo em sistemas Windows.
"""

import subprocess
import logging
import os
from typing import List, Dict, Callable, Optional
from pathlib import Path

from core.i18n import _


class WindowsCleaner:
    """Gerencia a remoção de bloatware, telemetria e componentes de IA do Windows."""

    def __init__(self):
        self.bloatware_list = self._get_bloatware_list()
        self.ai_components = self._get_ai_components()
        self.telemetry_commands = self._get_telemetry_commands()
        self.cleanup_commands = self._get_cleanup_commands()

    def _get_bloatware_list(self) -> List[Dict[str, str]]:
        """Retorna lista de bloatware conhecidos com nome e pacote."""
        return [
            {"name": _("Xbox App"), "package": "Microsoft.XboxApp", "description": _("Aplicativo Xbox")},
            {"name": _("Xbox Game Bar"), "package": "Microsoft.XboxGamingOverlay", "description": _("Barra de jogo Xbox")},
            {"name": _("Xbox Identity Provider"), "package": "Microsoft.XboxIdentityProvider", "description": _("Provedor de identidade Xbox")},
            {"name": _("Xbox Speech to Text Overlay"), "package": "Microsoft.XboxSpeechToTextOverlay", "description": _("Sobreposição de fala Xbox")},
            {"name": _("Candy Crush"), "package": "king.com.CandyCrushSaga", "description": _("Jogo Candy Crush")},
            {"name": _("Skype"), "package": "Microsoft.SkypeApp", "description": _("Skype")},
            {"name": _("OneDrive"), "package": "Microsoft.OneDrive", "description": _("OneDrive")},
            {"name": _("Bing Weather"), "package": "Microsoft.BingWeather", "description": _("Clima Bing")},
            {"name": _("Bing News"), "package": "Microsoft.BingNews", "description": _("Notícias Bing")},
            {"name": _("Bing Sports"), "package": "Microsoft.BingSports", "description": _("Esportes Bing")},
            {"name": _("Bing Finance"), "package": "Microsoft.BingFinance", "description": _("Finanças Bing")},
            {"name": _("3D Builder"), "package": "Microsoft.3DBuilder", "description": _("Construtor 3D")},
            {"name": _("People"), "package": "Microsoft.People", "description": _("Pessoas")},
            {"name": _("Zune Music"), "package": "Microsoft.ZuneMusic", "description": _("Música Zune")},
            {"name": _("Zune Video"), "package": "Microsoft.ZuneVideo", "description": _("Vídeo Zune")},
            {"name": _("Mixed Reality Portal"), "package": "Microsoft.MixedReality.Portal", "description": _("Portal Realidade Mista")},
            {"name": _("Office Hub"), "package": "Microsoft.MicrosoftOfficeHub", "description": _("Hub do Office")},
            {"name": _("Solitaire Collection"), "package": "Microsoft.MicrosoftSolitaireCollection", "description": _("Coleção Paciência")},
            {"name": _("Sticky Notes"), "package": "Microsoft.MicrosoftStickyNotes", "description": _("Notas Auto-adesivas")},
            {"name": _("Windows Camera"), "package": "Microsoft.WindowsCamera", "description": _("Câmera do Windows")},
            {"name": _("Windows Communications Apps"), "package": "Microsoft.WindowsCommunicationsApps", "description": _("Aplicativos de Comunicações")},
            {"name": _("Windows Feedback Hub"), "package": "Microsoft.WindowsFeedbackHub", "description": _("Hub de Feedback")},
            {"name": _("Windows Maps"), "package": "Microsoft.WindowsMaps", "description": _("Mapas do Windows")},
            {"name": _("Windows Sound Recorder"), "package": "Microsoft.WindowsSoundRecorder", "description": _("Gravador de Som")},
            {"name": _("Your Phone"), "package": "Microsoft.YourPhone", "description": _("Seu Telefone")},
            {"name": _("Get Help"), "package": "Microsoft.GetHelp", "description": _("Obter Ajuda")},
            {"name": _("Messaging"), "package": "Microsoft.Messaging", "description": _("Mensagens")},
            {"name": _("Office OneNote"), "package": "Microsoft.Office.OneNote", "description": _("OneNote")},
            {"name": _("Outlook for Windows"), "package": "Microsoft.OutlookForWindows", "description": _("Outlook")},
            {"name": _("Paint 3D"), "package": "Microsoft.Paint3D", "description": _("Paint 3D")},
            {"name": _("Print 3D"), "package": "Microsoft.Print3D", "description": _("Impressão 3D")},
            {"name": _("Snip & Sketch"), "package": "Microsoft.ScreenSketch", "description": _("Recorte e Esboço")},
            {"name": _("Teams"), "package": "Microsoft.Teams", "description": _("Microsoft Teams")},
            {"name": _("Todos"), "package": "Microsoft.Todos", "description": _("Microsoft To Do")},
            {"name": _("Wallet"), "package": "Microsoft.Wallet", "description": _("Carteira")},
            {"name": _("Windows Alarms"), "package": "Microsoft.WindowsAlarms", "description": _("Alarmes")},
            {"name": _("Windows Calculator"), "package": "Microsoft.WindowsCalculator", "description": _("Calculadora")},
            {"name": _("Windows Clock"), "package": "Microsoft.WindowsClock", "description": _("Relógio")},
        ]

    def _get_ai_components(self) -> List[Dict[str, str]]:
        """Lista componentes de IA do Windows 11 e comandos para desabilitar."""
        return [
            {"name": _("Cortana"), "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f'},
            {"name": _("Windows Recall"), "cmd": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI" /v DisableAIDataAnalysis /t REG_DWORD /d 1 /f'},
            {"name": _("Copilot"), "cmd": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ShowCopilotButton /t REG_DWORD /d 0 /f'},
        ]

    def _get_telemetry_commands(self) -> List[str]:
        """Comandos para desabilitar telemetria e coleta de dados."""
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
        """Comandos para limpeza de arquivos temporários e cache."""
        return [
            'del /q /f /s %temp%\\*',
            'del /q /f /s C:\\Windows\\Temp\\*',
            'del /q /f /s C:\\Windows\\Prefetch\\*',
            'del /q /f /s C:\\Windows\\SoftwareDistribution\\Download\\*',
            'cleanmgr /sagerun:1',  # Executa limpeza de disco com configurações padrão
        ]

    def get_installed_bloatware(self) -> List[Dict[str, str]]:
        """Verifica quais bloatwares da lista estão instalados."""
        installed = []
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-AppxPackage | Select-Object -ExpandProperty PackageFullName"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            if result.returncode != 0:
                logging.error(_("Erro ao executar PowerShell: {stderr}").format(stderr=result.stderr))
                return installed
            installed_packages = result.stdout.lower()
            for app in self.bloatware_list:
                if app["package"].lower() in installed_packages:
                    installed.append(app)
        except Exception as e:
            logging.error(_("Exceção ao verificar bloatware: {error}").format(error=e))
        return installed

    def remove_package(self, package_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Remove um pacote Appx pelo nome."""
        cmd = f'powershell -Command "Get-AppxPackage *{package_name}* | Remove-AppxPackage -ErrorAction SilentlyContinue"'
        return self._run_command(cmd, log_callback)

    def remove_multiple_packages(self, packages: List[str], log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Remove múltiplos pacotes."""
        success = True
        for pkg in packages:
            if not self.remove_package(pkg, log_callback):
                success = False
        return success

    def disable_telemetry(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Executa todos os comandos de desabilitação de telemetria."""
        success = True
        for cmd in self.telemetry_commands:
            if not self._run_command(cmd, log_callback):
                success = False
        return success

    def disable_ai_component(self, component_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Desabilita um componente de IA específico."""
        for comp in self.ai_components:
            if comp["name"].lower() == component_name.lower():
                return self._run_command(comp["cmd"], log_callback)
        return False

    def disable_all_ai(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Desabilita todos os componentes de IA."""
        success = True
        for comp in self.ai_components:
            if not self._run_command(comp["cmd"], log_callback):
                success = False
        return success

    def run_cleanup(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Executa comandos de limpeza de arquivos temporários."""
        success = True
        for cmd in self.cleanup_commands:
            if not self._run_command(cmd, log_callback):
                success = False
        return success

    def _run_command(self, cmd: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Executa um comando no shell e retorna True se bem-sucedido."""
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            stdout, stderr = proc.communicate(timeout=120)
            if log_callback:
                if stdout:
                    log_callback(stdout)
                if stderr:
                    log_callback(_("ERRO: {stderr}").format(stderr=stderr))
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            if log_callback:
                log_callback(_("Comando excedeu tempo limite e foi encerrado."))
            return False
        except Exception as e:
            if log_callback:
                log_callback(_("Exceção: {error}").format(error=e))
            return False
