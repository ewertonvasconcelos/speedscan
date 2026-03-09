#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process management module (thread-safe with queue).
Version 1.0.0
"""

import psutil
import time
import threading
import queue
import logging
from typing import List, Dict, Any, Optional

from core import config


class ProcessManager:
    """Manages system processes: listing, killing, changing priority, suspending/resuming."""

    def __init__(self):
        """Initialize the process manager with default sorting, filtering, and monitoring settings."""
        self.sort_by = 'cpu_percent'          # Key to sort the process list
        self.reverse = True                    # Descending order by default
        self.filter_term = ""                   # Filter by process name
        self.update_interval = 2                  # Seconds between updates in monitoring mode
        self._stop_event = threading.Event()     # Signal to stop monitoring thread
        self._thread = None                      # Background thread for monitoring
        self.callback_queue = queue.Queue()      # Queue to deliver process lists to UI

    def get_process_list(self) -> List[Dict[str, Any]]:
        """Retrieve and return a list of running processes with selected attributes.

        Returns:
            List[Dict[str, Any]]: Each dict contains pid, name, cpu_percent,
            memory_percent, status, create_time_str, username, and nice.
        """
        process_list = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent',
                                         'status', 'create_time', 'username', 'nice']):
            try:
                pinfo = proc.info
                pinfo['cpu_percent'] = round(pinfo['cpu_percent'] or 0, 1)
                pinfo['memory_percent'] = round(pinfo['memory_percent'] or 0, 1)
                create_time = pinfo['create_time']
                if create_time:
                    pinfo['create_time_str'] = time.strftime('%H:%M:%S', time.localtime(create_time))
                else:
                    pinfo['create_time_str'] = ''
                pinfo['nice'] = pinfo['nice'] if pinfo['nice'] is not None else 0
                process_list.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                # Log error with process identifier if possible
                pid = proc.pid if hasattr(proc, 'pid') else 'unknown'
                name = proc.name() if hasattr(proc, 'name') else 'unknown'
                logging.error(f"Failed to access process PID={pid} name={name}: {e}")
                continue

        # Apply name filter
        if self.filter_term:
            term = self.filter_term.lower()
            process_list = [p for p in process_list if term in p['name'].lower()]

        # Sort list
        process_list.sort(key=lambda x: x.get(self.sort_by, 0), reverse=self.reverse)
        return process_list

    def kill_process(self, pid: int) -> bool:
        """
        Terminate (and if necessary, kill) a process by PID.

        Args:
            pid (int): Process ID.

        Returns:
            bool: True if the process was successfully terminated, False otherwise.
        """
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
        """
        Change the nice value (priority) of a process.

        Args:
            pid (int): Process ID.
            nice_value (int): New nice value (range depends on OS).

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            proc = psutil.Process(pid)
            proc.nice(nice_value)
            logging.info(f"Nice value of process PID={pid} set to {nice_value}.")
            return True
        except Exception as e:
            logging.error(f"Failed to set nice for process PID={pid}: {e}")
            return False

    def suspend_process(self, pid: int) -> bool:
        """
        Suspend a process (pause execution).

        Args:
            pid (int): Process ID.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            proc = psutil.Process(pid)
            proc.suspend()
            logging.info(f"Process PID?{pid} suspended.")
            return True
        except Exception as e:
            logging.error(f"Failed to suspend process PID?{pid}: {e}")
            return False

    def resume_process(self, pid: int) -> bool:
        """
        Resume a previously suspended process.

        Args:
            pid (int): Process ID.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            proc = psutil.Process(pid)
            proc.resume()
            logging.info(f"Process PID={pid} resumed.")
            return True
        except Exception as e:
            logging.error(f"Failed to resume process PID={pid}: {e}")
            return False

    def start_monitoring(self):
        """Start the background thread that periodically updates the process list."""
        self._stop_event.clear()
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            logging.debug("Process monitoring started.")

    def stop_monitoring(self):
        """Stop the background monitoring thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
            logging.debug("Process monitoring stopped.")

    def _monitor_loop(self):
        """Background loop: fetch process list and put it into the callback queue."""
        while not self._stop_event.is_set():
            procs = self.get_process_list()
            self.callback_queue.put(procs)
            time.sleep(self.update_interval)

    def set_sort(self, key: str, reverse: bool = True):
        """
        Set sorting criteria for the process list.

        Args:
            key (str): Attribute to sort by (e.g., 'cpu_percent', 'memory_percent', 'name').
            reverse (bool): If True, sort in descending order.
        """
        self.sort_by = key
        self.reverse = reverse
        logging.debug(f"Sort order changed: by={key}, reverse={reverse}")

    def set_filter(self, term: str):
        """
        Set a filter string to show only processes whose names contain the term.

        Args:
            term (str): Filter term (case-insensitive).
        """
        self.filter_term = term
        logging.debug(f"Filter set to: '{term}'")

    def set_update_interval(self, seconds: int):
        """
        Set the interval between automatic process list updates.

        Args:
            seconds (int): Interval in seconds (minimum 1).
        """
        self.update_interval = max(1, seconds)
        logging.debug(f"Update interval set to {self.update_interval}s")
