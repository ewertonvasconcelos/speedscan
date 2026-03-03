"""
SpeedScan - Métricas Históricas (SQLite)
=========================================
Armazena e recupera histórico de métricas do sistema
para gerar gráficos de desempenho ao longo do tempo.

Dependências:
    pip install psutil matplotlib
    (sqlite3 já vem na biblioteca padrão)
"""

import sqlite3
import time
import threading
import psutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import platform


@dataclass
class MetricSnapshot:
    """Um ponto no tempo com todas as métricas do sistema."""
    timestamp: float
    cpu_percent: float
    ram_percent: float
    ram_used_mb: float
    cpu_temp: Optional[float]
    gpu_temp: Optional[float]
    disk_used_percent: float
    net_sent_mb: float
    net_recv_mb: float
    net_sent_speed_kbps: float = 0
    net_recv_speed_kbps: float = 0

    @property
    def timestamp_label(self) -> str:
        import datetime
        return datetime.datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")


class MetricsDatabase:
    """
    Banco de dados SQLite para histórico de métricas do sistema.

    Exemplo de uso:
        db = MetricsDatabase()
        db.start_collection(interval=30)

        # Depois de um tempo...
        history = db.get_history("cpu_percent", minutes=60)
        for point in history:
            print(f"{point.timestamp_label}: {point.cpu_percent:.1f}%")
    """

    DEFAULT_DB_PATH = Path.home() / ".speedscan" / "metrics.db"
    MAX_RETENTION_DAYS = 30  # Manter apenas últimos 30 dias

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
        self._lock = threading.Lock()
        self._collect_thread: Optional[threading.Thread] = None
        self._running = False
        self._prev_net = None
        self._prev_net_time = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Retorna conexão com o banco (thread-safe)."""
        if not self._conn:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        """Cria tabelas se não existirem."""
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp       REAL NOT NULL,
                    cpu_percent     REAL DEFAULT 0,
                    ram_percent     REAL DEFAULT 0,
                    ram_used_mb     REAL DEFAULT 0,
                    cpu_temp        REAL,
                    gpu_temp        REAL,
                    disk_used_pct   REAL DEFAULT 0,
                    net_sent_mb     REAL DEFAULT 0,
                    net_recv_mb     REAL DEFAULT 0,
                    net_sent_kbps   REAL DEFAULT 0,
                    net_recv_kbps   REAL DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)
            """)
            conn.commit()

    def _collect_snapshot(self) -> MetricSnapshot:
        """Coleta uma snapshot das métricas atuais."""
        now = time.time()

        cpu_pct = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk_pct = 0
        try:
            if platform.system() == "Windows":
                disk_pct = psutil.disk_usage("C:\\").percent
            else:
                disk_pct = psutil.disk_usage("/").percent
        except Exception:
            pass

        # Rede
        net = psutil.net_io_counters()
        net_sent_mb = net.bytes_sent / (1024 * 1024)
        net_recv_mb = net.bytes_recv / (1024 * 1024)
        net_sent_kbps = 0
        net_recv_kbps = 0

        if self._prev_net and self._prev_net_time:
            elapsed = now - self._prev_net_time
            if elapsed > 0:
                net_sent_kbps = ((net.bytes_sent - self._prev_net.bytes_sent) / elapsed) / 1024
                net_recv_kbps = ((net.bytes_recv - self._prev_net.bytes_recv) / elapsed) / 1024

        self._prev_net = net
        self._prev_net_time = now

        # Temperatura (opcional)
        cpu_temp = None
        gpu_temp = None
        try:
            from temperature_monitor import TemperatureMonitor
            monitor = TemperatureMonitor()
            cpu_temp = monitor.get_max_cpu_temp()
            gpu_temp = monitor.get_max_gpu_temp()
        except Exception:
            try:
                temps = psutil.sensors_temperatures()
                for key, entries in temps.items():
                    if entries:
                        cpu_temp = max(e.current for e in entries)
                        break
            except Exception:
                pass

        return MetricSnapshot(
            timestamp=now,
            cpu_percent=cpu_pct,
            ram_percent=ram.percent,
            ram_used_mb=round(ram.used / (1024**2), 1),
            cpu_temp=cpu_temp,
            gpu_temp=gpu_temp,
            disk_used_percent=disk_pct,
            net_sent_mb=round(net_sent_mb, 2),
            net_recv_mb=round(net_recv_mb, 2),
            net_sent_speed_kbps=round(max(0, net_sent_kbps), 1),
            net_recv_speed_kbps=round(max(0, net_recv_kbps), 1),
        )

    def save_snapshot(self, snapshot: Optional[MetricSnapshot] = None) -> MetricSnapshot:
        """
        Salva uma snapshot no banco de dados.

        Args:
            snapshot: Snapshot a salvar (se None, coleta automaticamente)

        Returns:
            A snapshot salva
        """
        if snapshot is None:
            snapshot = self._collect_snapshot()

        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                INSERT INTO metrics
                    (timestamp, cpu_percent, ram_percent, ram_used_mb,
                     cpu_temp, gpu_temp, disk_used_pct,
                     net_sent_mb, net_recv_mb, net_sent_kbps, net_recv_kbps)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp,
                snapshot.cpu_percent,
                snapshot.ram_percent,
                snapshot.ram_used_mb,
                snapshot.cpu_temp,
                snapshot.gpu_temp,
                snapshot.disk_used_percent,
                snapshot.net_sent_mb,
                snapshot.net_recv_mb,
                snapshot.net_sent_speed_kbps,
                snapshot.net_recv_speed_kbps,
            ))
            conn.commit()
        return snapshot

    def get_history(self, metric: str = "cpu_percent", minutes: int = 60) -> list[MetricSnapshot]:
        """
        Retorna histórico de uma métrica.

        Args:
            metric: Nome da coluna ('cpu_percent', 'ram_percent', 'cpu_temp', etc.)
            minutes: Quantos minutos de histórico retornar

        Returns:
            Lista de MetricSnapshot ordenada por timestamp
        """
        since = time.time() - (minutes * 60)
        valid_metrics = {
            "cpu_percent", "ram_percent", "cpu_temp", "gpu_temp",
            "disk_used_pct", "net_sent_kbps", "net_recv_kbps"
        }
        if metric not in valid_metrics:
            metric = "cpu_percent"

        with self._lock:
            conn = self._get_conn()
            rows = conn.execute("""
                SELECT * FROM metrics
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (since,)).fetchall()

        return [
            MetricSnapshot(
                timestamp=row["timestamp"],
                cpu_percent=row["cpu_percent"],
                ram_percent=row["ram_percent"],
                ram_used_mb=row["ram_used_mb"],
                cpu_temp=row["cpu_temp"],
                gpu_temp=row["gpu_temp"],
                disk_used_percent=row["disk_used_pct"],
                net_sent_mb=row["net_sent_mb"],
                net_recv_mb=row["net_recv_mb"],
                net_sent_speed_kbps=row["net_sent_kbps"],
                net_recv_speed_kbps=row["net_recv_kbps"],
            )
            for row in rows
        ]

    def get_chart_data(self, metric: str = "cpu_percent", minutes: int = 60) -> tuple[list, list]:
        """
        Retorna dados prontos para matplotlib.

        Args:
            metric: Métrica desejada
            minutes: Período em minutos

        Returns:
            Tupla (timestamps_relativos_segundos, valores)
        """
        history = self.get_history(metric, minutes)
        if not history:
            return [], []

        now = time.time()
        metric_map = {
            "cpu_percent":     lambda s: s.cpu_percent,
            "ram_percent":     lambda s: s.ram_percent,
            "cpu_temp":        lambda s: s.cpu_temp or 0,
            "gpu_temp":        lambda s: s.gpu_temp or 0,
            "disk_used_pct":   lambda s: s.disk_used_percent,
            "net_sent_kbps":   lambda s: s.net_sent_speed_kbps,
            "net_recv_kbps":   lambda s: s.net_recv_speed_kbps,
        }

        getter = metric_map.get(metric, lambda s: s.cpu_percent)
        x = [-(now - s.timestamp) / 60 for s in history]  # Minutos atrás (negativo)
        y = [getter(s) for s in history]
        return x, y

    def get_statistics(self, metric: str = "cpu_percent", minutes: int = 60) -> dict:
        """Retorna estatísticas (min, max, média) de uma métrica."""
        _, values = self.get_chart_data(metric, minutes)
        if not values:
            return {"min": 0, "max": 0, "avg": 0, "current": 0, "count": 0}
        non_zero = [v for v in values if v > 0]
        return {
            "min":     round(min(non_zero or [0]), 1),
            "max":     round(max(values), 1),
            "avg":     round(sum(values) / len(values), 1),
            "current": round(values[-1], 1),
            "count":   len(values),
        }

    def cleanup_old_data(self):
        """Remove registros mais antigos que MAX_RETENTION_DAYS dias."""
        cutoff = time.time() - (self.MAX_RETENTION_DAYS * 86400)
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
            conn.execute("VACUUM")
            conn.commit()

    def get_db_size_mb(self) -> float:
        """Retorna tamanho do banco em MB."""
        try:
            return round(self.db_path.stat().st_size / (1024**2), 2)
        except Exception:
            return 0.0

    def start_collection(self, interval: float = 30.0):
        """
        Inicia coleta automática de métricas em background.

        Args:
            interval: Intervalo em segundos entre snapshots
        """
        if self._running:
            return

        def _loop():
            while self._running:
                try:
                    self.save_snapshot()
                    # Limpeza periódica (a cada 1000 snapshots)
                    with self._lock:
                        conn = self._get_conn()
                        count = conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]
                        if count > 100000:
                            self.cleanup_old_data()
                except Exception:
                    pass
                time.sleep(interval)

        self._running = True
        self._collect_thread = threading.Thread(target=_loop, daemon=True)
        self._collect_thread.start()

    def stop_collection(self):
        """Para a coleta automática."""
        self._running = False

    def plot_metric(self, metric: str = "cpu_percent", minutes: int = 60, save_path: Optional[str] = None):
        """
        Gera um gráfico matplotlib da métrica.

        Args:
            metric: Métrica a plotar
            minutes: Período em minutos
            save_path: Se fornecido, salva o gráfico neste caminho
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.ticker as ticker

            x, y = self.get_chart_data(metric, minutes)
            if not x:
                print("Sem dados para plotar.")
                return

            stats = self.get_statistics(metric, minutes)

            labels = {
                "cpu_percent":    ("Uso de CPU (%)", "#00aaff"),
                "ram_percent":    ("Uso de RAM (%)", "#ff6600"),
                "cpu_temp":       ("Temp. CPU (°C)", "#ff4444"),
                "gpu_temp":       ("Temp. GPU (°C)", "#aa44ff"),
                "disk_used_pct":  ("Uso de Disco (%)", "#ffaa00"),
                "net_sent_kbps":  ("Upload (KB/s)", "#00ff88"),
                "net_recv_kbps":  ("Download (KB/s)", "#ff8888"),
            }

            title, color = labels.get(metric, ("Métrica", "#00aaff"))

            fig, ax = plt.subplots(figsize=(10, 4), facecolor="#1a1a2e")
            ax.set_facecolor("#16213e")
            ax.plot(x, y, color=color, linewidth=2, alpha=0.9)
            ax.fill_between(x, y, alpha=0.2, color=color)
            ax.set_title(f"SpeedScan — {title} (últimos {minutes} min)",
                          color="white", fontsize=12)
            ax.set_xlabel("Minutos atrás", color="#aaaaaa")
            ax.set_ylabel(title, color="#aaaaaa")
            ax.tick_params(colors="#aaaaaa")
            ax.spines[:].set_color("#333355")

            # Linha de média
            ax.axhline(stats["avg"], color="#ffff88", linestyle="--", alpha=0.5,
                        label=f"Média: {stats['avg']}")
            ax.legend(facecolor="#1a1a2e", labelcolor="white")

            fig.tight_layout()
            if save_path:
                plt.savefig(save_path, facecolor="#1a1a2e", dpi=100)
            else:
                plt.show()
            plt.close()

        except ImportError:
            print("⚠️  matplotlib não instalado. Execute: pip install matplotlib")

    def close(self):
        """Fecha a conexão com o banco."""
        self.stop_collection()
        if self._conn:
            self._conn.close()
            self._conn = None


if __name__ == "__main__":
    print("=== SpeedScan — Métricas Históricas ===\n")
    db = MetricsDatabase()

    print("📊 Coletando 5 snapshots (aguarde 10s)...\n")
    for i in range(5):
        snap = db.save_snapshot()
        print(f"  [{i+1}/5] CPU: {snap.cpu_percent:.1f}% | RAM: {snap.ram_percent:.1f}% | "
              f"Disco: {snap.disk_used_percent:.1f}% | "
              f"Download: {snap.net_recv_speed_kbps:.1f} KB/s")
        time.sleep(2)

    stats = db.get_statistics("cpu_percent", minutes=5)
    print(f"\n📈 Estatísticas de CPU (últimos 5 min):")
    print(f"  Mín: {stats['min']}% | Máx: {stats['max']}% | Média: {stats['avg']}%")
    print(f"  Total de amostras: {stats['count']}")
    print(f"\n💾 Tamanho do banco: {db.get_db_size_mb()} MB")
    print(f"📁 Local: {db.db_path}")
    db.close()
