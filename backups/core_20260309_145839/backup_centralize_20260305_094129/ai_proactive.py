#!/usr/bin/env python3
import logging
# Módulo de IA Proativa - Sugere otimizações baseado em métricas
# Versão 1.0.0

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
        sugestoes = []
        
        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent > 90:
            sugestoes.append({
                'titulo': '⚠️ Pouco espaço em disco',
                'descricao': f'O disco está com {disk_usage.percent:.1f}% de uso. Libere espaço.',
                'acao': 'browsers',
                'prioridade': 'alta'
            })
        elif disk_usage.percent > 75:
            sugestoes.append({
                'titulo': 'ℹ️ Espaço em disco',
                'descricao': f'O disco está com {disk_usage.percent:.1f}% de uso. Considere limpar cache.',
                'acao': 'cache',
                'prioridade': 'media'
            })

        mem = psutil.virtual_memory()
        if mem.percent > 90:
            sugestoes.append({
                'titulo': '⚠️ Memória RAM alta',
                'descricao': f'Uso de RAM em {mem.percent:.1f}%. Feche aplicativos pesados.',
                'acao': None,
                'prioridade': 'alta'
            })
        elif mem.percent > 80:
            sugestoes.append({
                'titulo': 'ℹ️ Memória RAM',
                'descricao': f'Uso de RAM em {mem.percent:.1f}%. Considere reiniciar.',
                'acao': None,
                'prioridade': 'media'
            })

        try:
            temps = psutil.sensors_temperatures()
            for sensor, entries in temps.items():
                for entry in entries:
                    if entry.current > 80:
                        sugestoes.append({
                            'titulo': '🔥 Temperatura alta',
                            'descricao': f'{sensor}: {entry.current}°C. Verifique ventilação.',
                            'acao': None,
                            'prioridade': 'alta'
                        })
                        break
        except:
            pass

        battery = psutil.sensors_battery()
        if battery and battery.percent < 20 and not battery.power_plugged:
            sugestoes.append({
                'titulo': '🔋 Bateria fraca',
                'descricao': f'Bateria em {battery.percent:.1f}%. Conecte o carregador.',
                'acao': None,
                'prioridade': 'alta'
            })

        health = self.health_monitor.calculate_health_score()
        if health['score'] < 50:
            sugestoes.append({
                'titulo': '💔 Saúde do sistema crítica',
                'descricao': 'Score muito baixo. Execute otimizações.',
                'acao': 'check',
                'prioridade': 'alta'
            })
        elif health['score'] < 70:
            sugestoes.append({
                'titulo': '❤️‍🩹 Saúde do sistema',
                'descricao': 'Score médio. Considere limpeza.',
                'acao': 'cache',
                'prioridade': 'media'
            })

        stats = self.metrics_db.get_stats(period_hours=24)
        if stats['cpu_avg'] and stats['cpu_avg'] > 80:
            sugestoes.append({
                'titulo': '📈 CPU consistentemente alta',
                'descricao': f'Média de CPU nas últimas 24h: {stats["cpu_avg"]:.1f}%. Verifique processos.',
                'acao': None,
                'prioridade': 'media'
            })
        if stats['mem_avg'] and stats['mem_avg'] > 80:
            sugestoes.append({
                'titulo': '📈 Memória consistentemente alta',
                'descricao': f'Média de memória nas últimas 24h: {stats["mem_avg"]:.1f}%.',
                'acao': None,
                'prioridade': 'media'
            })

        cookie_sites = self.cookie_mgr.get_cookie_summary()
        if cookie_sites and len(cookie_sites) > 50:
            sugestoes.append({
                'titulo': '🍪 Muitos cookies armazenados',
                'descricao': f'Você tem cookies de {len(cookie_sites)} sites. Gerenciar cookies pode liberar espaço.',
                'acao': 'cookies',
                'prioridade': 'baixa'
            })

        trash_size = self.trash_mgr.get_trash_size()
        if trash_size > 100 * 1024 * 1024:  # > 100 MB
            sugestoes.append({
                'titulo': '🗑️ Lixeira do SpeedScan cheia',
                'descricao': f'A lixeira contém {trash_size / (1024*1024):.1f} MB. Deseja esvaziar?',
                'acao': 'empty_trash',
                'prioridade': 'media'
            })

        return sugestoes

    def get_summary(self):
        sugestoes = self.analyze()
        if not sugestoes:
            return "✅ Nenhuma sugestão no momento. Sistema OK!"
        
        linhas = []
        for s in sugestoes:
            prioridade_emoji = {
                'alta': '🔴',
                'media': '🟡',
                'baixa': '🟢'
            }.get(s['prioridade'], '⚪')
            linhas.append(f"{prioridade_emoji} {s['titulo']}: {s['descricao']}")
        return "\n".join(linhas)
