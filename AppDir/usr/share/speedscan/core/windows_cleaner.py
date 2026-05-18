"""
Módulo de limpeza do Windows (bloatware, telemetria e componentes de IA)
Uso exclusivo em sistemas Windows.
"""

import subprocess
import logging
from typing import List, Dict, Callable, Optional

class WindowsCleaner:
    """Gerencia a remoção de bloatware, telemetria e componentes de IA do Windows."""

    def __init__(self):
        self.bloatware_list = self._get_bloatware_list()
        self.ai_components = self._get_ai_components()
        self.telemetry_commands = self._get_telemetry_commands()

    def _get_bloatware_list(self) -> List[Dict[str, str]]:
        """Retorna lista de bloatware conhecidos com nome e padrão de busca."""
        return [
            {"name": "Xbox App", "pattern": "xbox", "package": "Microsoft.XboxApp"},
            {"name": "Candy Crush", "pattern": "candycrush", "package": "king.com.CandyCrushSaga"},
            {"name": "Skype", "pattern": "skype", "package": "Microsoft.SkypeApp"},
            {"name": "OneDrive", "pattern": "onedrive", "package": "Microsoft.OneDrive"},
            {"name": "Bing Weather", "pattern": "bingweather", "package": "Microsoft.BingWeather"},
            {"name": "Bing News", "pattern": "bingnews", "package": "Microsoft.BingNews"},
            {"name": "Bing Sports", "pattern": "bingsports", "package": "Microsoft.BingSports"},
            {"name": "Bing Finance", "pattern": "bingfinance", "package": "Microsoft.BingFinance"},
            {"name": "3D Builder", "pattern": "3dbuilder", "package": "Microsoft.3DBuilder"},
            {"name": "People", "pattern": "people", "package": "Microsoft.People"},
            {"name": "Zune Music", "pattern": "zunemusic", "package": "Microsoft.ZuneMusic"},
            {"name": "Zune Video", "pattern": "zunevideo", "package": "Microsoft.ZuneVideo"},
            {"name": "Mixed Reality Portal", "pattern": "mixedreality", "package": "Microsoft.MixedReality.Portal"},
            {"name": "Office Hub", "pattern": "officehub", "package": "Microsoft.MicrosoftOfficeHub"},
            {"name": "Solitaire Collection", "pattern": "solitaire", "package": "Microsoft.MicrosoftSolitaireCollection"},
            {"name": "Sticky Notes", "pattern": "stickynotes", "package": "Microsoft.MicrosoftStickyNotes"},
            {"name": "Windows Camera", "pattern": "windowscamera", "package": "Microsoft.WindowsCamera"},
            {"name": "Windows Communications Apps", "pattern": "communicationsapps", "package": "Microsoft.WindowsCommunicationsApps"},
            {"name": "Windows Feedback Hub", "pattern": "feedbackhub", "package": "Microsoft.WindowsFeedbackHub"},
            {"name": "Windows Maps", "pattern": "windowsmaps", "package": "Microsoft.WindowsMaps"},
            {"name": "Windows Sound Recorder", "pattern": "soundrecorder", "package": "Microsoft.WindowsSoundRecorder"},
            {"name": "Your Phone", "pattern": "yourphone", "package": "Microsoft.YourPhone"},
            {"name": "Get Help", "pattern": "gethelp", "package": "Microsoft.GetHelp"},
            {"name": "Messaging", "pattern": "messaging", "package": "Microsoft.Messaging"},
            {"name": "Office OneNote", "pattern": "onenote", "package": "Microsoft.Office.OneNote"},
            {"name": "Outlook for Windows", "pattern": "outlook", "package": "Microsoft.OutlookForWindows"},
            {"name": "Paint 3D", "pattern": "paint3d", "package": "Microsoft.Paint3D"},
            {"name": "Print 3D", "pattern": "print3d", "package": "Microsoft.Print3D"},
            {"name": "Skype", "pattern": "skype", "package": "Microsoft.SkypeApp"},
            {"name": "Snip & Sketch", "pattern": "snip", "package": "Microsoft.ScreenSketch"},
            {"name": "Teams", "pattern": "teams", "package": "Microsoft.Teams"},
            {"name": "Todos", "pattern": "todos", "package": "Microsoft.Todos"},
            {"name": "Wallet", "pattern": "wallet", "package": "Microsoft.Wallet"},
            {"name": "Windows Alarms", "pattern": "alarms", "package": "Microsoft.WindowsAlarms"},
            {"name": "Windows Calculator", "pattern": "calculator", "package": "Microsoft.WindowsCalculator"},
            {"name": "Windows Clock", "pattern": "clock", "package": "Microsoft.WindowsClock"},
        ]

    def _get_ai_components(self) -> List[Dict[str, str]]:
        """Lista componentes de IA do Windows 11 e comandos para desabilitar."""
        return [
            {"name": "Copilot", "cmd": "reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f"},
            {"name": "Windows Recall (Snapshots)", "cmd": "reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI /v DisableAIDataAnalysis /t REG_DWORD /d 1 /f"},
            {"name": "Cortana", "cmd": "Get-AppxPackage *cortana* | Remove-AppxPackage"},
            {"name": "Web Search in Start", "cmd": "reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Search /v BingSearchEnabled /t REG_DWORD /d 0 /f"},
            {"name": "News & Interests", "cmd": "reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Feeds /v ShellFeedsTaskbarEnabled /t REG_DWORD /d 0 /f"},
            {"name": "Widgets", "cmd": "reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced /v TaskbarDa /t REG_DWORD /d 0 /f"},
        ]

    def _get_telemetry_commands(self) -> List[str]:
        """Comandos para desabilitar telemetria e coleta de dados."""
        return [
            "reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection /v AllowTelemetry /t REG_DWORD /d 0 /f",
            "reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy /v TailoredExperiencesWithDiagnosticDataEnabled /t REG_DWORD /d 0 /f",
            "reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy /v LetAppsRunInBackground /t REG_DWORD /d 2 /f",
            "schtasks /change /tn \"Microsoft\\Windows\\Application Experience\\Microsoft Compatibility Appraiser\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\Application Experience\\ProgramDataUpdater\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\Customer Experience Improvement Program\\Consolidator\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\Customer Experience Improvement Program\\UsbCeip\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\DiskDiagnostic\\Microsoft-Windows-DiskDiagnosticDataCollector\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\Feedback\\Siuf\\DmClient\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\Feedback\\Siuf\\DmClientOnScenarioDownload\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\Location\\Notifications\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\PI\\Sqm-Tasks\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\Power Efficiency Diagnostics\\AnalyzeSystem\" /disable",
            "schtasks /change /tn \"Microsoft\\Windows\\Windows Error Reporting\\QueueReporting\" /disable",
        ]

    def get_installed_bloatware(self) -> List[Dict[str, str]]:
        """
        Verifica quais bloatwares da lista estão instalados no sistema.
        Retorna uma lista de dicionários com 'name' e 'pattern' de cada app instalado.
        """
        installed = []
        try:
            # Executa PowerShell para listar todos os AppxPackages
            result = subprocess.run(
                ["powershell", "-Command", "Get-AppxPackage | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            if result.returncode != 0:
                logging.error(f"Erro ao executar PowerShell: {result.stderr}")
                return installed

            installed_packages = result.stdout.lower()
            for app in self.bloatware_list:
                # Verifica se o padrão (package name em minúsculas) está na lista
                if app["package"].lower() in installed_packages:
                    installed.append(app)
        except Exception as e:
            logging.error(f"Exceção ao verificar bloatware: {e}")
        return installed

    def remove_package_by_pattern(self, pattern: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Remove pacotes Appx que contenham o padrão informado.
        Retorna True se bem-sucedido, False caso contrário.
        """
        cmd = f'powershell -Command "Get-AppxPackage *{pattern}* | Remove-AppxPackage -ErrorAction SilentlyContinue"'
        return self._run_command(cmd, log_callback)

    def remove_package_by_name(self, package_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Remove um pacote Appx pelo nome exato (ou parte)."""
        return self.remove_package_by_pattern(package_name, log_callback)

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
        """Desabilita todos os componentes de IA listados."""
        success = True
        for comp in self.ai_components:
            if not self._run_command(comp["cmd"], log_callback):
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
            stdout, stderr = proc.communicate(timeout=60)
            if log_callback:
                if stdout:
                    log_callback(stdout)
                if stderr:
                    log_callback(f"ERRO: {stderr}")
            return proc.returncode == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            if log_callback:
                log_callback("Comando excedeu tempo limite e foi encerrado.")
            return False
        except Exception as e:
            if log_callback:
                log_callback(f"Exceção: {e}")
            return False
