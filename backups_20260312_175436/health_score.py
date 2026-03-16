#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Score calculation module (0-100) for system health.
Version 1.0.0
"""

import psutil
import time
import logging

from core import config


class HealthScore:
    """Calculates a health score for the system based on various metrics."""

    def __init__(self):
        """Initialize with a baseline CPU measurement."""
        self.last_cpu = psutil.cpu_percent(interval=0.1)

    def calculate_health_score(self):
        """Calculate the current health score (0-100).

        Returns:
            dict: Contains 'score' (float) and 'details' with individual component scores.
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = time.time() - psutil.boot_time()
        battery = psutil.sensors_battery()
        battery_score = 0
        if battery:
            battery_score = battery.percent

        # Weights for each component (sum to 1.0)
        cpu_weight = 0.3
        mem_weight = 0.3
        disk_weight = 0.2
        uptime_weight = 0.1
        battery_weight = 0.1 if battery else 0

        # Individual scores (higher is better)
        cpu_score = 100 - cpu_percent
        mem_score = 100 - mem.percent
        disk_score = 100 - disk.percent
        uptime_days = uptime / 86400
        uptime_score = min(100, uptime_days * 100 / 7) if uptime_days < 7 else 100

        total_weight = cpu_weight + mem_weight + disk_weight + uptime_weight + battery_weight
        weighted_score = (
            cpu_score * cpu_weight +
            mem_score * mem_weight +
            disk_score * disk_weight +
            uptime_score * uptime_weight +
            battery_score * battery_weight
        ) / total_weight

        score = round(weighted_score, 1)
        return {
            'score': score,
            'details': {
                'cpu': cpu_score,
                'memory': mem_score,
                'disk': disk_score,
                'uptime': uptime_score,
                'battery': battery_score if battery else None
            }
        }
