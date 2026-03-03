"""
SpeedScan - Gerenciador de Processos
=====================================
Tabela de processos em tempo real com ordenação, filtro
e possibilidade de encerrar processos.

Dependências:
    pip install psutil
"""

import psutil
import time
import threading
import platform
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class ProcessInfo:
    """Informações de um processo do sistema."""
    pid: int
    name: str
    status: str
    cpu_percent: float
    ram_mb: float
    ram_percent: float
    user: str
    created_time: float
    num_threads: int
    exe: str
    cmdline: str

    @property
    def created_label(self) -> str:
        elapsed = time.time() - self.created_time
        if elapsed < 60:
            return f"{int(elapsed)}s"
        elif elapsed < 3600:
            return f"{int(elapsed/60)}m"
        elif elapsed < 86400:
            return f"{int(elapsed/3600)}h"
        return f"{int(elapsed/86400)}d"

    @property
    def status_icon(self) -> str:
        icons = {
            "running":  "🟢",
            "sleeping": "🔵",
            "idle":     "⚪",
            "stopped":  "🟡",
            "zombie":   "🔴",
            "dead":     "💀",
        }
        return icons.get(self.status, "⚪")

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "name": self.name,
            "status": self.status,
            "cpu_percent": self.cpu_percent,
            "ram_mb": self.ram_mb,
            "user": self.user,
        }


class ProcessManager:
    """
    Gerencia e monitora processos do sistema.

    Exemplo de uso:
        manager = ProcessManager()
        top = manager.get_top_processes(by="cpu", n=10)
        for proc in top:
            print(f"{proc.name}: {proc.cpu_percent:.1f}% CPU, {proc.ram_mb:.1f} MB RAM")
    """

    def __init__(self):
        self._system = platform.system()
        self._cache = []
        self._last_update = 0
        self._cache_ttl = 2.0
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False

    def get_processes(self, sort_by: str = "cpu", filter_name: str = "") -> list[ProcessInfo]:
        """
        Retorna lista de processos em execução.

        Args:
            sort_by: Coluna de ordenação: 'cpu', 'ram', 'name', 'pid'
            filter_name: Filtrar por nome (substring, case-insensitive)

        Returns:
            Lista de ProcessInfo ordenada
        """
        now = time.time()
        if now - self._last_update < self._cache_ttl and self._cache:
            processes = self._cache
        else:
            processes = self._collect_processes()
            self._cache = processes
            self._last_update = now

        # Filtrar
        if filter_name:
            processes = [p for p in processes if filter_name.lower() in p.name.lower()]

        # Ordenar
        sort_key = {
            "cpu":  lambda p: p.cpu_percent,
            "ram":  lambda p: p.ram_mb,
            "name": lambda p: p.name.lower(),
            "pid":  lambda p: p.pid,
        }.get(sort_by, lambda p: p.cpu_percent)

        reverse = sort_by in ("cpu", "ram")
        return sorted(processes, key=sort_key, reverse=reverse)

    def _collect_processes(self) -> list[ProcessInfo]:
        """Coleta informações de todos os processos."""
        processes = []
        for proc in psutil.process_iter([
            "pid", "name", "status", "cpu_percent",
            "memory_info", "memory_percent", "username",
            "create_time", "num_threads", "exe", "cmdline"
        ]):
            try:
                info = proc.info
                ram_bytes = info.get("memory_info")
                ram_mb = ram_bytes.rss / (1024 * 1024) if ram_bytes else 0

                cmdline = info.get("cmdline") or []
                if isinstance(cmdline, list):
                    cmdline = " ".join(cmdline)

                processes.append(ProcessInfo(
                    pid=info["pid"],
                    name=info.get("name", "?") or "?",
                    status=info.get("status", "unknown") or "unknown",
                    cpu_percent=round(info.get("cpu_percent", 0) or 0, 1),
                    ram_mb=round(ram_mb, 1),
                    ram_percent=round(info.get("memory_percent", 0) or 0, 1),
                    user=info.get("username", "") or "",
                    created_time=info.get("create_time", 0) or 0,
                    num_threads=info.get("num_threads", 0) or 0,
                    exe=info.get("exe", "") or "",
                    cmdline=cmdline[:200],
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes

    def get_top_processes(self, by: str = "cpu", n: int = 10) -> list[ProcessInfo]:
        """Retorna os N processos que mais consomem CPU ou RAM."""
        return self.get_processes(sort_by=by)[:n]

    def get_process_details(self, pid: int) -> Optional[dict]:
        """Retorna detalhes completos de um processo pelo PID."""
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                mem = proc.memory_info()
                connections = []
                try:
                    connections = proc.net_connections()
                except (psutil.AccessDenied, AttributeError):
                    pass

                open_files = []
                try:
                    open_files = [str(f.path) for f in proc.open_files()[:10]]
                except (psutil.AccessDenied, Exception):
                    pass

                return {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "exe": proc.exe() if hasattr(proc, 'exe') else "",
                    "cmdline": " ".join(proc.cmdline()),
                    "status": proc.status(),
                    "user": proc.username(),
                    "cpu_percent": proc.cpu_percent(interval=0.1),
                    "cpu_affinity": proc.cpu_affinity() if hasattr(proc, 'cpu_affinity') else [],
                    "num_threads": proc.num_threads(),
                    "memory_rss_mb": round(mem.rss / (1024**2), 1),
                    "memory_vms_mb": round(mem.vms / (1024**2), 1),
                    "memory_percent": round(proc.memory_percent(), 1),
                    "create_time": proc.create_time(),
                    "num_connections": len(connections),
                    "open_files": open_files,
                    "priority": proc.nice(),
                    "io_counters": str(proc.io_counters()) if hasattr(proc, 'io_counters') else "N/A",
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def kill_process(self, pid: int, force: bool = False) -> tuple[bool, str]:
        """
        Encerra um processo.

        Args:
            pid: PID do processo
            force: Se True, usa SIGKILL (Linux) ou TerminateProcess (Windows)

        Returns:
            (sucesso, mensagem)
        """
        try:
            proc = psutil.Process(pid)
            name = proc.name()

            # Proteção contra encerrar processos críticos do sistema
            protected = {"systemd", "init", "kernel", "kthreadd", "system"}
            if any(p in name.lower() for p in protected):
                return False, f"Processo {name} é um processo de sistema protegido."

            if force:
                proc.kill()
            else:
                proc.terminate()
                # Aguarda até 3 segundos para encerrar graciosamente
                try:
                    proc.wait(timeout=3)
                except psutil.TimeoutExpired:
                    proc.kill()

            return True, f"Processo '{name}' (PID {pid}) encerrado com sucesso."

        except psutil.NoSuchProcess:
            return False, f"Processo PID {pid} não encontrado."
        except psutil.AccessDenied:
            return False, f"Permissão negada. Execute como administrador."
        except Exception as e:
            return False, f"Erro ao encerrar processo: {e}"

    def get_system_summary(self) -> dict:
        """Retorna resumo do sistema (total de processos, uso total, etc.)."""
        processes = self.get_processes()
        return {
            "total_processes": len(processes),
            "running": sum(1 for p in processes if p.status == "running"),
            "sleeping": sum(1 for p in processes if p.status == "sleeping"),
            "zombie": sum(1 for p in processes if p.status == "zombie"),
            "total_cpu": psutil.cpu_percent(interval=0.5),
            "total_ram_percent": psutil.virtual_memory().percent,
        }

    def start_auto_refresh(self, callback: Callable[[list[ProcessInfo]], None],
                            interval: float = 2.0,
                            sort_by: str = "cpu"):
        """
        Inicia atualização automática em background.

        Args:
            callback: Função chamada com a lista atualizada
            interval: Intervalo em segundos
            sort_by: Critério de ordenação
        """
        def _loop():
            while self._running:
                processes = self.get_processes(sort_by=sort_by)
                callback(processes)
                time.sleep(interval)

        self._running = True
        self._monitor_thread = threading.Thread(target=_loop, daemon=True)
        self._monitor_thread.start()

    def stop_auto_refresh(self):
        """Para a atualização automática."""
        self._running = False


# -----------------------------------------------------------------------
# Widget CustomTkinter — Tabela de Processos
# -----------------------------------------------------------------------
PROCESS_WIDGET = '''
import customtkinter as ctk
import tkinter as tk
from process_manager import ProcessManager

class ProcessTab(ctk.CTkFrame):
    """Aba de gerenciamento de processos com tabela em tempo real."""

    COLUMNS = [
        ("PID",     50),
        ("Nome",   160),
        ("Status",  80),
        ("CPU %",   70),
        ("RAM MB",  75),
        ("Usuário", 110),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.manager = ProcessManager()
        self._sort_by = "cpu"
        self._selected_pid = None
        self._build_ui()
        self.manager.start_auto_refresh(self._on_update, interval=2, sort_by="cpu")

    def _build_ui(self):
        # Barra de controles
        bar = ctk.CTkFrame(self)
        bar.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(bar, text="🔍 Filtrar:").pack(side="left", padx=3)
        self.filter_entry = ctk.CTkEntry(bar, width=150, placeholder_text="Nome do processo...")
        self.filter_entry.pack(side="left", padx=3)
        self.filter_entry.bind("<KeyRelease>", self._on_filter_change)

        ctk.CTkLabel(bar, text="Ordenar por:").pack(side="left", padx=8)
        self.sort_var = ctk.StringVar(value="CPU")
        for label, key in [("CPU", "cpu"), ("RAM", "ram"), ("Nome", "name")]:
            ctk.CTkRadioButton(bar, text=label, variable=self.sort_var,
                                value=label,
                                command=lambda k=key: self._set_sort(k)).pack(side="left", padx=2)

        self.kill_btn = ctk.CTkButton(bar, text="⛔ Encerrar Processo",
                                       fg_color="#cc3333",
                                       command=self._kill_selected,
                                       state="disabled", width=160)
        self.kill_btn.pack(side="right", padx=5)

        # Cabeçalho da tabela
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=5)
        for col_name, col_width in self.COLUMNS:
            ctk.CTkLabel(header, text=col_name, width=col_width,
                          font=("Arial", 11, "bold"),
                          anchor="w").pack(side="left", padx=2)

        # Tabela com scroll
        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=5, pady=2)

        # Status bar
        self.status_var = tk.StringVar(value="Carregando...")
        ctk.CTkLabel(self, textvariable=self.status_var,
                      font=("Arial", 10), anchor="w").pack(fill="x", padx=5, pady=2)

    def _on_update(self, processes):
        self.after(0, self._refresh_table, processes)

    def _refresh_table(self, processes):
        # Limpar tabela
        for w in self.table_frame.winfo_children():
            w.destroy()

        # Aplicar filtro
        filter_text = self.filter_entry.get().lower()
        if filter_text:
            processes = [p for p in processes if filter_text in p.name.lower()]

        # Renderizar linhas
        for i, proc in enumerate(processes[:100]):  # Limitar a 100 processos
            row = ctk.CTkFrame(self.table_frame,
                                fg_color=("#2b2b3b" if i % 2 == 0 else "#1e1e2e"))
            row.pack(fill="x", pady=1)
            row.bind("<Button-1>", lambda e, p=proc: self._select_row(p, e.widget))

            cpu_color = "#ff4444" if proc.cpu_percent > 50 else "#ffaa00" if proc.cpu_percent > 20 else "#88ff00"
            ram_color = "#ff4444" if proc.ram_mb > 1000 else "#ffaa00" if proc.ram_mb > 500 else "white"

            values = [
                (str(proc.pid),        "white",    50),
                (proc.name[:20],       "white",    160),
                (f"{proc.status_icon} {proc.status}", "white", 80),
                (f"{proc.cpu_percent:.1f}%", cpu_color, 70),
                (f"{proc.ram_mb:.0f}",  ram_color, 75),
                (proc.user[:14],       "gray",     110),
            ]
            for text, color, width in values:
                ctk.CTkLabel(row, text=text, width=width,
                              text_color=color, anchor="w",
                              font=("Courier", 11)).pack(side="left", padx=2)

        summary = self.manager.get_system_summary()
        self.status_var.set(
            f"Total: {summary['total_processes']} processos | "
            f"CPU: {summary['total_cpu']:.1f}% | RAM: {summary['total_ram_percent']:.1f}%"
        )

    def _select_row(self, proc, widget):
        self._selected_pid = proc.pid
        self.kill_btn.configure(state="normal",
                                 text=f"⛔ Encerrar: {proc.name} ({proc.pid})")

    def _kill_selected(self):
        if not self._selected_pid:
            return
        success, msg = self.manager.kill_process(self._selected_pid)
        # Mostrar resultado como dialog ou label
        self.status_var.set(msg)
        self._selected_pid = None
        self.kill_btn.configure(state="disabled", text="⛔ Encerrar Processo")

    def _set_sort(self, key):
        self._sort_by = key
        self.manager._cache_ttl = 0  # Forçar refresh

    def _on_filter_change(self, event=None):
        if self.manager._cache:
            self._refresh_table(self.manager._cache)
'''

if __name__ == "__main__":
    print("=== SpeedScan — Gerenciador de Processos ===\n")
    manager = ProcessManager()

    print("📊 Top 10 processos por CPU:\n")
    top_cpu = manager.get_top_processes(by="cpu", n=10)
    print(f"{'PID':<8} {'Nome':<25} {'CPU%':<8} {'RAM MB':<10} {'Status'}")
    print("-" * 65)
    for p in top_cpu:
        print(f"{p.pid:<8} {p.name[:24]:<25} {p.cpu_percent:<8.1f} {p.ram_mb:<10.1f} {p.status}")

    summary = manager.get_system_summary()
    print(f"\n📈 Resumo:")
    print(f"  Total de processos: {summary['total_processes']}")
    print(f"  Em execução: {summary['running']}")
    print(f"  Dormindo: {summary['sleeping']}")
    print(f"  Zumbis: {summary['zombie']}")
