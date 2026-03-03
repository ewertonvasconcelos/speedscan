#!/usr/bin/env python3
# core/historical_metrics.py
# =============================================================================
#   ███████╗██████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ █████╗ ███╗   ██╗
#   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║
#   ███████╗██████╔╝█████╗  █████╗  ██║  ██║█████╗  ██║     ███████║██╔██╗ ██║
#   ╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║  ██║██╔══╝  ██║     ██╔══██║██║╚██╗██║
#   ███████║██║     ███████╗███████╗██████╔╝███████╗╚██████╗██║  ██║██║ ╚████║
#   ╚══════╝╚═╝     ╚══════╝╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
# =============================================================================
# Módulo de coleta e armazenamento de métricas históricas (com inserção em lote)
# Versão 0.0.9-beta
# =============================================================================

import sqlite3
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import psutil

DB_PATH = Path.home() / "speedscan" / "metrics.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class MetricsDB:
    """Gerencia banco de dados SQLite para métricas."""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    cpu REAL,
                    memory REAL,
                    disk_usage REAL,
                    disk_io_read REAL,
                    disk_io_write REAL,
                    net_sent REAL,
                    net_recv REAL
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)')
    
    def insert_many(self, rows):
        """
        Insere múltiplas linhas de uma vez.
        rows: lista de tuplas no formato (timestamp, cpu, memory, disk_usage, disk_io_read, disk_io_write, net_sent, net_recv)
        """
        if not rows:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany('''
                INSERT INTO metrics 
                (timestamp, cpu, memory, disk_usage, disk_io_read, disk_io_write, net_sent, net_recv)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', rows)
    
    def get_last_hours(self, hours=1, metrics=None):
        if metrics is None:
            metrics = ['timestamp', 'cpu', 'memory', 'disk_usage']
        else:
            if 'timestamp' not in metrics:
                metrics = ['timestamp'] + metrics
        cols = ', '.join(metrics)
        cutoff = time.time() - hours * 3600
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f'SELECT {cols} FROM metrics WHERE timestamp >= ? ORDER BY timestamp', (cutoff,))
            rows = cursor.fetchall()
        return rows
    
    def prune_old(self, days=7):
        cutoff = time.time() - days * 24 * 3600
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff,))
    
    def get_stats(self, period_hours=1):
        cutoff = time.time() - period_hours * 3600
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT 
                    AVG(cpu), MIN(cpu), MAX(cpu),
                    AVG(memory), MIN(memory), MAX(memory),
                    AVG(disk_usage), MIN(disk_usage), MAX(disk_usage)
                FROM metrics WHERE timestamp >= ?
            ''', (cutoff,))
            row = cursor.fetchone()
        return {
            'cpu_avg': row[0], 'cpu_min': row[1], 'cpu_max': row[2],
            'mem_avg': row[3], 'mem_min': row[4], 'mem_max': row[5],
            'disk_avg': row[6], 'disk_min': row[7], 'disk_max': row[8]
        }

class MetricsCollector:
    """Coleta métricas em intervalos regulares e armazena em lote no banco."""
    
    def __init__(self, interval=5, batch_size=10):
        self.interval = interval
        self.batch_size = batch_size  # Número de amostras antes de inserir
        self.db = MetricsDB()
        self._stop_event = threading.Event()
        self._thread = None
        self._last_disk_io = psutil.disk_io_counters()
        self._last_net_io = psutil.net_io_counters()
        self._last_time = time.time()
        self._buffer = []  # Buffer para acumular amostras
    
    def start(self):
        self._stop_event.clear()
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._collect_loop, daemon=True)
            self._thread.start()
    
    def stop(self):
        self._stop_event.set()
        # Insere o que restou no buffer antes de parar
        if self._buffer:
            self.db.insert_many(self._buffer)
            self._buffer = []
        if self._thread:
            self._thread.join(timeout=1)
    
    def _collect_loop(self):
        while not self._stop_event.is_set():
            self._collect_once()
            time.sleep(self.interval)
    
    def _collect_once(self):
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            disk_io = psutil.disk_io_counters()
            now = time.time()
            dt = now - self._last_time
            if disk_io and self._last_disk_io and dt > 0:
                read_bps = (disk_io.read_bytes - self._last_disk_io.read_bytes) / dt
                write_bps = (disk_io.write_bytes - self._last_disk_io.write_bytes) / dt
            else:
                read_bps = write_bps = None
            self._last_disk_io = disk_io
            
            net_io = psutil.net_io_counters()
            if net_io and self._last_net_io and dt > 0:
                sent_bps = (net_io.bytes_sent - self._last_net_io.bytes_sent) / dt
                recv_bps = (net_io.bytes_recv - self._last_net_io.bytes_recv) / dt
            else:
                sent_bps = recv_bps = None
            self._last_net_io = net_io
            self._last_time = now
            
            # Adiciona ao buffer
            self._buffer.append((
                now, cpu, mem, disk,
                read_bps, write_bps,
                sent_bps, recv_bps
            ))
            
            # Se o buffer atingiu o tamanho do lote, insere e limpa
            if len(self._buffer) >= self.batch_size:
                self.db.insert_many(self._buffer)
                self._buffer = []
            
            # A cada hora, faz a limpeza de dados antigos
            if int(now) % 3600 < self.interval:
                self.db.prune_old(days=7)
        except Exception as e:
            print(f"Erro na coleta de métricas: {e}")
