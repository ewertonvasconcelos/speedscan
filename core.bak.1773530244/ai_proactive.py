#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proactive AI module - Suggests optimizations based on metrics.
Version 1.0.0
"""
import logging
import psutil
import time
from core.cookie_manager import CookieManager
from core.trash_manager import TrashManager
from core import config

class AIProactive:
    def __init__(self, metrics_db, health_monitor):
        self.metrics_db = metrics_db
        self.health_monitor = health_monitor
        self.cookie_mgr = CookieManager()
        self.trash_mgr = TrashManager()

    def analyze(self):
        suggestions = []

        disk_usage = psutil.disk_usage("/")
        if disk_usage.percent > 90:
            suggestions.append({
                "title": "⚠️ Low disk space",
                "description": f"Disk is at {disk_usage.percent:.1f}% usage. Free up space.",
                "action": "browsers",
                "priority": "high"
            })
        elif disk_usage.percent > 75:
            suggestions.append({
                "title": "💿 Disk space",
                "description": f"Disk is at {disk_usage.percent:.1f}% usage. Consider cache clean.",
                "action": "cache",
                "priority": "medium"
            })

        mem = psutil.virtual_memory()
        if mem.percent > 90:
            suggestions.append({
                "title": "⚠️ High RAM memory",
                "description": f"RAM usage is {mem.percent:.1f}%. Close heavy applications.",
                "action": None,
                "priority": "high"
            })
        elif mem.percent > 80:
            suggestions.append({
                "title": "📈 RAM memory",
                "description": f"RAM usage is {mem.percent:.1f}%. Consider restarting.",
                "action": None,
                "priority": "medium"
            })

        try:
            temps = psutil.sensors_temperatures()
            for sensor, entries in temps.items():
                for entry in entries:
                    if entry.current > 80:
                        suggestions.append({
                            "title": "🔥 High temperature",
                            "description": f"{sensor}: {entry.current}°C. Check cooling.",
                            "action": None,
                            "priority": "high"
                        })
                        break
        except Exception as e:
            logging.error(f"Error accessing temperatures: {e}")
            pass

        battery = psutil.sensors_battery()
        if battery and battery.percent < 20 and not battery.power_plugged:
            suggestions.append({
                "title": "🔋 Low battery",
                "description": f"Battery at {battery.percent:.1f}%. Plug in charger.",
                "action": None,
                "priority": "high"
            })

        health = self.health_monitor.calculate_health_score()
        if health["score"] < 50:
            suggestions.append({
                "title": "🩺 System health critical",
                "description": "Health score is low. Run optimizations.",
                "action": "check",
                "priority": "high"
            })
        elif health["score"] < 70:
            suggestions.append({
                "title": "🩺 System health",
                "description": "Health score is medium. Consider cleaning.",
                "action": "cache",
                "priority": "medium"
            })

        stats = self.metrics_db.get_stats(period_hours=24)
        if stats.get("cpu_avg") and stats["cpu_avg"] > 80:
            suggestions.append({
                "title": "📊 CPU consistently high",
                "description": f"Average CPU over last 24h: {stats['cpu_avg']:.1f}%. Check processes.",
                "action": None,
                "priority": "medium"
            })
        if stats.get("mem_avg") and stats["mem_avg"] > 80:
            suggestions.append({
                "title": "📊 Memory consistently high",
                "description": f"Average memory over last 24h: {stats['mem_avg']:.1f}%.",
                "action": None,
                "priority": "medium"
            })

        cookie_sites = self.cookie_mgr.get_cookie_summary()
        if cookie_sites and len(cookie_sites) > 50:
            suggestions.append({
                "title": "🍪 Many cookies stored",
                "description": f"You have cookies from {len(cookie_sites)} sites. Cleaning cookies may free space.",
                "action": "cookies",
                "priority": "low"
            })

        trash_size = self.trash_mgr.get_trash_size()
        if trash_size > 100 * 1024 * 1024:
            suggestions.append({
                "title": "🗑️ Trash is full",
                "description": f"Trash contains {trash_size / (1024*1024):.1f} MB. Empty it?",
                "action": "empty_trash",
                "priority": "medium"
            })

        return suggestions

    def get_summary(self):
        suggestions = self.analyze()
        if not suggestions:
            return "✅ No suggestions at the moment. System is OK!"
        lines = []
        for s in suggestions:
            priority_emojis = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(s["priority"], "⚪")
            lines.append(f"{priority_emojis} {s['title']}: {s['description']}")
        return "\n".join(lines)
