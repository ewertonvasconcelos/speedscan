#!/usr/bin/env python3
# core/health_score.py

import psutil
import platform
import time
from datetime import datetime

class HealthScore:
    """
    Calcula um score de saúde do sistema (0-100) baseado em:
    - CPU: uso, frequência, temperatura (se disponível)
    - Memória: uso, swap
    - Disco: uso, saúde S.M.A.R.T. (se disponível)
    - Rede: latência (ping)
    - Uptime (penaliza sistemas muito tempo ligados sem reboot)
    """

    def __init__(self):
        self.last_ping = None

    def calculate_health_score(self):
        """
        Retorna um objeto com score total e detalhes por componente.
        """
        scores = {}
        reasons = []

        # CPU Score (0-25)
        cpu_score, cpu_reason = self._cpu_score()
        scores['cpu'] = cpu_score
        if cpu_reason:
            reasons.append(cpu_reason)

        # Memory Score (0-25)
        mem_score, mem_reason = self._memory_score()
        scores['memory'] = mem_score
        if mem_reason:
            reasons.append(mem_reason)

        # Disk Score (0-25)
        disk_score, disk_reason = self._disk_score()
        scores['disk'] = disk_score
        if disk_reason:
            reasons.append(disk_reason)

        # Network Score (0-15)
        net_score, net_reason = self._network_score()
        scores['network'] = net_score
        if net_reason:
            reasons.append(net_reason)

        # Uptime Score (0-10)
        uptime_score, uptime_reason = self._uptime_score()
        scores['uptime'] = uptime_score
        if uptime_reason:
            reasons.append(uptime_reason)

        total = sum(scores.values())
        # Garantir que está entre 0 e 100
        total = max(0, min(100, total))

        # Gerar resumo
        if total >= 90:
            summary = "Excelente! Seu sistema está muito saudável."
        elif total >= 70:
            summary = "Bom. Alguns ajustes podem melhorar o desempenho."
        elif total >= 50:
            summary = "Regular. Considere otimizar seu sistema."
        else:
            summary = "Crítico. Ações urgentes são recomendadas."

        return {
            'score': total,
            'components': scores,
            'reasons': reasons,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }

    def _cpu_score(self):
        score = 25
        reasons = []

        # Uso da CPU
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            if cpu_percent > 90:
                score -= 10
                reasons.append("CPU com uso muito alto (>90%)")
            elif cpu_percent > 70:
                score -= 5
                reasons.append("CPU com uso alto (>70%)")
        except:
            pass

        # Frequência da CPU
        try:
            freq = psutil.cpu_freq()
            if freq and freq.current and freq.max:
                ratio = freq.current / freq.max
                if ratio < 0.5:
                    score -= 5
                    reasons.append("CPU operando em frequência muito baixa")
                elif ratio < 0.8:
                    score -= 2
        except:
            pass

        # Temperatura da CPU (se disponível)
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                max_temp = max(t.current for t in temps['coretemp'])
                if max_temp > 85:
                    score -= 10
                    reasons.append(f"Temperatura da CPU crítica ({max_temp}°C)")
                elif max_temp > 75:
                    score -= 5
                    reasons.append(f"Temperatura da CPU alta ({max_temp}°C)")
        except:
            pass

        return max(0, score), "; ".join(reasons) if reasons else None

    def _memory_score(self):
        score = 25
        reasons = []

        # Memória RAM
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            score -= 10
            reasons.append(f"Memória RAM muito alta ({mem.percent}%)")
        elif mem.percent > 80:
            score -= 5
            reasons.append(f"Memória RAM alta ({mem.percent}%)")

        # Swap
        swap = psutil.swap_memory()
        if swap.percent > 50:
            score -= 5
            reasons.append(f"Swap em uso elevado ({swap.percent}%)")

        return max(0, score), "; ".join(reasons) if reasons else None

    def _disk_score(self):
        score = 25
        reasons = []

        # Uso dos discos
        partitions = psutil.disk_partitions()
        for part in partitions:
            if part.fstype and 'loop' not in part.device:
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    if usage.percent > 95:
                        score -= 5
                        reasons.append(f"Disco {part.device} quase cheio ({usage.percent}%)")
                        break
                    elif usage.percent > 90:
                        score -= 3
                        reasons.append(f"Disco {part.device} muito cheio ({usage.percent}%)")
                        break
                except:
                    pass

        return max(0, score), "; ".join(reasons) if reasons else None

    def _network_score(self):
        score = 15
        reasons = []

        # Ping para 8.8.8.8 (latência)
        try:
            import subprocess
            param = '-n' if platform.system() == 'Windows' else '-c'
            result = subprocess.run(['ping', param, '1', '8.8.8.8'],
                                    capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                # Extrair tempo
                import re
                match = re.search(r'time[=<](\d+\.?\d*)', result.stdout, re.I)
                if match:
                    ping_ms = float(match.group(1))
                    if ping_ms > 200:
                        score -= 10
                        reasons.append(f"Ping muito alto ({ping_ms}ms)")
                    elif ping_ms > 100:
                        score -= 5
                        reasons.append(f"Ping alto ({ping_ms}ms)")
                else:
                    score -= 5
                    reasons.append("Não foi possível medir latência")
            else:
                score -= 15
                reasons.append("Sem conectividade com a internet")
        except:
            score -= 5
            reasons.append("Falha ao testar rede")

        return max(0, score), "; ".join(reasons) if reasons else None

    def _uptime_score(self):
        score = 10
        reasons = []

        # Uptime em horas
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = uptime_seconds / 3600

        if uptime_hours > 720:  # 30 dias
            score -= 10
            reasons.append("Sistema ligado há mais de 30 dias (recomenda-se reiniciar)")
        elif uptime_hours > 168:  # 7 dias
            score -= 5
            reasons.append("Sistema ligado há mais de 7 dias")
        elif uptime_hours > 72:  # 3 dias
            score -= 2

        return max(0, score), "; ".join(reasons) if reasons else None
