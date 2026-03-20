#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Score calculation module (0-100) for system health.
Version 1.0.0
"""
import psutil
import time

class HealthScore:
    def __init__(self):
        self.last_cpu = psutil.cpu_percent(interval=0.1)

    def calculate_health_score(self):
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime = time.time() - psutil.boot_time()
        battery = psutil.sensors_battery()
        battery_score = 0
        if battery:
            battery_score = battery.percent
        
        # Get temperature
        temp_score = 100
        try:
            temps = psutil.sensors_temperatures()
            for name, entries in temps.items():
                if "cpu" in name.lower() or "k10" in name.lower() or "coretemp" in name.lower():
                    for entry in entries:
                        if hasattr(entry, 'current') and entry.current:
                            temp = entry.current
                            # Temperature scoring: 100 at <50°C, 50 at 80°C, 0 at 100°C+
                            if temp >= 100:
                                temp_score = 0
                            elif temp >= 80:
                                temp_score = 100 - ((temp - 80) * 5)  # 0 at 100, 50 at 80
                            elif temp >= 50:
                                temp_score = 100 - ((temp - 50) * 1)  # 50 at 50, 100 at 50
                            else:
                                temp_score = 100
                            break
                    if temp_score < 100:
                        break
        except:
            temp_score = 100

        cpu_weight = 0.25
        mem_weight = 0.25
        disk_weight = 0.20
        temp_weight = 0.15
        uptime_weight = 0.10
        battery_weight = 0.05 if battery else 0

        cpu_score = 100 - cpu_percent
        mem_score = 100 - mem.percent
        disk_score = 100 - disk.percent
        uptime_days = uptime / 86400
        uptime_score = min(100, uptime_days * 100 / 7) if uptime_days < 7 else 100

        total_weight = cpu_weight + mem_weight + disk_weight + temp_weight + uptime_weight + battery_weight
        weighted_score = (
            cpu_score * cpu_weight +
            mem_score * mem_weight +
            disk_score * disk_weight +
            temp_score * temp_weight +
            uptime_score * uptime_weight +
            battery_score * battery_weight
        ) / total_weight

        score = round(weighted_score, 1)

        return {
            "score": score,
            "details": {
                "cpu": cpu_score,
                "memory": mem_score,
                "disk": disk_score,
                "temperature": temp_score,
                "uptime": uptime_score,
                "battery": battery_score if battery else None
            }
        }
