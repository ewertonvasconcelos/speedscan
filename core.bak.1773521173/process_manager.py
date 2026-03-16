#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process management module (thread-safe with queue).
Version 1.0.0
"""
import logging
import queue
import threading
import time
from typing import List, Dict, Any, Optional
import psutil
from core import config

class ProcessManager:
    def __init__(self):
        self.sort_by = "cpu_percent"
        self.reverse = True
        self.filter_term = ""
        self.update_interval = 2
        self._stop_event = threading.Event()
        self._thread = None
        self.callback_queue = queue.Queue()
    def get_process_list(self) -> List[Dict[str, Any]]:
        process_list = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent",
                                         "status", "create_time", "username", "nice"]):
            try:
                pinfo = proc.info
                pinfo["cpu_percent"] = round(pinfo["cpu_percent"] or 0, 1)
                pinfo["memory_percent"] = round(pinfo["memory_percent"] or 0, 1)
                create_time = pinfo["create_time"]
                if create_time:
                    pinfo["create_time_str"] = time.strftime("%H:%M:%S", time.localtime(create_time))
                else:
                    pinfo["create_time_str"] = ""
                pinfo["nice"] = pinfo["nice"] if pinfo["nice"] is not None else 0
                process_list.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                pid = proc.pid if hasattr(proc, "pid") else "unknown"
                name = proc.name() if hasattr(proc, "name") else "unknown"
                logging.error(f"Failed to access process PID={pid} name={name}: {e}")
                continue
        if self.filter_term:
            term = self.filter_term.lower()
            process_list = [p for p in process_list if term in p["name"].lower()]
        process_list.sort(key=lambda x: x.get(self.sort_by, 0), reverse=self.reverse)
        return process_list
    def kill_process(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            gone, alive = psutil.wait_procs([proc], timeout=3)
            if alive:
                proc.kill()
            logging.info(f"Process PID={pid} terminated successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to terminate process PID={pid}: {e}")
            return False
    def set_nice(self, pid: int, nice_value: int) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.nice(nice_value)
            logging.info(f"Nice value of process PID={pid} set to {nice_value}.")
            return True
        except Exception as e:
            logging.error(f"Failed to set nice for process PID={pid}: {e}")
            return False
    def suspend_process(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.suspend()
            logging.info(f"Process PID={pid} suspended.")
            return True
        except Exception as e:
            logging.error(f"Failed to suspend process PID={pid}: {e}")
            return False
    def resume_process(self, pid: int) -> bool:
        try:
            proc = psutil.Process(pid)
            proc.resume()
            logging.info(f"Process PID={pid} resumed.")
            return True
        except Exception as e:
            logging.error(f"Failed to resume process PID={pid}: {e}")
            return False
    def start_monitoring(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            logging.debug("Process monitoring started.")
    def stop_monitoring(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
            logging.debug("Process monitoring stopped.")
    def _monitor_loop(self):
        while not self._stop_event.is_set():
            procs = self.get_process_list()
            self.callback_queue.put(procs)
            time.sleep(self.update_interval)
    def set_sort(self, key: str, reverse: bool = True):
        self.sort_by = key
        self.reverse = reverse
        logging.debug(f"Sort order changed: by={key}, reverse={reverse}")
    def set_filter(self, term: str):
        self.filter_term = term
        logging.debug(f"Filter set to: '{term}'")
    def set_update_interval(self, seconds: int):
        self.update_interval = max(1, seconds)
        logging.debug(f"Update interval set to {self.update_interval}s")
