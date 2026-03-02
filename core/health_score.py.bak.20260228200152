"""
SpeedScan - Score de Saúde do Sistema (0-100)
=============================================
Calcula um score ponderado baseado em múltiplos indicadores
do sistema. Exibe na tela principal do SpeedScan.

Dependências:
    pip install psutil
    (Opcional) temperature_monitor.py e smart_monitor.py do SpeedScan
"""

import psutil
import time
import platform
from dataclasses import dataclass, field
from typing import Optional
import subprocess


@dataclass
class ScoreComponent:
    """Representa a pontuação de um componente individual."""
    name: str
    label: str
    value: float         # Valor bruto (%, °C, etc.)
    score: int           # Score parcial (0-100)
    weight: float        # Peso no score final (0.0 a 1.0)
    status: str          # excellent | good | regular | bad | critical
    message: str         # Mensagem explicativa

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight

    @property
    def status_icon(self) -> str:
        icons = {
            "excellent": "🟢",
            "good": "🟢",
            "regular": "🟡",
            "bad": "🟠",
            "critical": "🔴",
        }
        return icons.get(self.status, "⚪")


@dataclass
class HealthScoreResult:
    """Resultado completo do cálculo de saúde do sistema."""
    score: int                              # Score final 0-100
    label: str                              # Excelente, Bom, Regular, Ruim, Crítico
    color: str                              # Cor hex para UI
    components: list[ScoreComponent] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def get_worst_components(self, n: int = 3) -> list[ScoreComponent]:
        """Retorna os N piores componentes."""
        return sorted(self.components, key=lambda c: c.score)[:n]

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "label": self.label,
            "color": self.color,
            "components": [
                {
                    "name": c.name,
                    "label": c.label,
                    "score": c.score,
                    "status": c.status,
                    "message": c.message,
                }
                for c in self.components
            ],
            "recommendations": self.recommendations,
        }


class SystemHealthScore:
    """
    Calcula o score de saúde do sistema (0-100).

    Pesos dos componentes:
        - CPU Load:         20%
        - RAM Usage:        20%
        - CPU Temperature:  25%
        - Disk Health:      25%
        - Boot Time:        10%

    Exemplo de uso:
        calculator = SystemHealthScore()
        result = calculator.calculate_score()
        print(f"Score: {result.score}/100 — {result.label}")
        for comp in result.components:
            print(f"  {comp.status_icon} {comp.label}: {comp.score}/100 — {comp.message}")
    """

    WEIGHTS = {
        "cpu":         0.20,
        "ram":         0.20,
        "cpu_temp":    0.25,
        "disk_health": 0.25,
        "boot_time":   0.10,
    }

    SCORE_THRESHOLDS = [
        (90, "Excelente", "#00ff88"),
        (75, "Bom",       "#88ff00"),
        (55, "Regular",   "#ffee00"),
        (35, "Ruim",      "#ff5500"),
        (0,  "Crítico",   "#ff0000"),
    ]

    def __init__(self):
        self._cpu_history = []
        self._history_size = 10  # Média dos últimos N readings de CPU

    def _get_status(self, score: int) -> str:
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "regular"
        elif score >= 30:
            return "bad"
        return "critical"

    def _classify_score(self, score: int) -> tuple[str, str]:
        """Retorna (label, color) para o score final."""
        for threshold, label, color in self.SCORE_THRESHOLDS:
            if score >= threshold:
                return label, color
        return "Crítico", "#ff0000"

    # ------------------------------------------------------------------
    # Componentes individuais
    # ------------------------------------------------------------------
    def _score_cpu(self) -> ScoreComponent:
        """Avalia uso de CPU."""
        # Usa média de múltiplas leituras para estabilidade
        cpu_pct = psutil.cpu_percent(interval=1.0)
        self._cpu_history.append(cpu_pct)
        if len(self._cpu_history) > self._history_size:
            self._cpu_history.pop(0)
        avg_cpu = sum(self._cpu_history) / len(self._cpu_history)

        # Score diminui exponencialmente acima de 70%
        if avg_cpu <= 50:
            score = 100
            msg = f"CPU estável ({avg_cpu:.0f}% de uso)"
        elif avg_cpu <= 70:
            score = int(100 - (avg_cpu - 50) * 1.5)
            msg = f"CPU em uso moderado ({avg_cpu:.0f}%)"
        elif avg_cpu <= 85:
            score = int(70 - (avg_cpu - 70) * 3)
            msg = f"CPU com uso elevado ({avg_cpu:.0f}%) — verifique processos"
        elif avg_cpu <= 95:
            score = int(25 - (avg_cpu - 85) * 1.5)
            msg = f"CPU sobrecarregada ({avg_cpu:.0f}%)!"
        else:
            score = 5
            msg = f"CPU em uso crítico ({avg_cpu:.0f}%)!"

        return ScoreComponent(
            name="cpu", label="Uso de CPU",
            value=avg_cpu, score=max(0, score),
            weight=self.WEIGHTS["cpu"],
            status=self._get_status(max(0, score)),
            message=msg
        )

    def _score_ram(self) -> ScoreComponent:
        """Avalia uso de RAM."""
        ram = psutil.virtual_memory()
        used_pct = ram.percent
        available_gb = ram.available / (1024 ** 3)

        if used_pct <= 60:
            score = 100
            msg = f"RAM com folga ({used_pct:.0f}% usado, {available_gb:.1f}GB livre)"
        elif used_pct <= 75:
            score = int(100 - (used_pct - 60) * 2)
            msg = f"RAM em uso moderado ({used_pct:.0f}%)"
        elif used_pct <= 85:
            score = int(70 - (used_pct - 75) * 4)
            msg = f"RAM em uso alto ({used_pct:.0f}%) — {available_gb:.1f}GB livre"
        elif used_pct <= 95:
            score = int(30 - (used_pct - 85) * 2)
            msg = f"RAM quase cheia ({used_pct:.0f}%)! Feche aplicativos."
        else:
            score = 5
            msg = f"RAM crítica ({used_pct:.0f}%)! Sistema pode travar."

        return ScoreComponent(
            name="ram", label="Uso de RAM",
            value=used_pct, score=max(0, score),
            weight=self.WEIGHTS["ram"],
            status=self._get_status(max(0, score)),
            message=msg
        )

    def _score_cpu_temp(self) -> ScoreComponent:
        """Avalia temperatura da CPU."""
        temp = self._get_cpu_temp()

        if temp is None:
            return ScoreComponent(
                name="cpu_temp", label="Temp. CPU",
                value=0, score=75,
                weight=self.WEIGHTS["cpu_temp"],
                status="regular",
                message="Temperatura não disponível nesta plataforma"
            )

        if temp <= 55:
            score = 100
            msg = f"Temperatura ideal ({temp:.0f}°C)"
        elif temp <= 65:
            score = int(100 - (temp - 55) * 4)
            msg = f"Temperatura normal ({temp:.0f}°C)"
        elif temp <= 75:
            score = int(60 - (temp - 65) * 4)
            msg = f"Temperatura elevada ({temp:.0f}°C) — verifique o cooler"
        elif temp <= 85:
            score = int(20 - (temp - 75) * 1.5)
            msg = f"Temperatura alta ({temp:.0f}°C)! Risco de throttling."
        else:
            score = 0
            msg = f"Temperatura crítica ({temp:.0f}°C)! Desligue o PC imediatamente."

        return ScoreComponent(
            name="cpu_temp", label="Temp. CPU",
            value=temp, score=max(0, score),
            weight=self.WEIGHTS["cpu_temp"],
            status=self._get_status(max(0, score)),
            message=msg
        )

    def _get_cpu_temp(self) -> Optional[float]:
        """Obtém temperatura da CPU via psutil."""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return None

            # Prioridade de sensores
            priority = ["coretemp", "k10temp", "cpu_thermal", "acpitz", "zenpower"]
            for key in priority:
                if key in temps and temps[key]:
                    readings = [t.current for t in temps[key] if t.current > 0]
                    if readings:
                        return max(readings)  # Usa o núcleo mais quente

            # Fallback: primeiro sensor disponível
            for key, entries in temps.items():
                if entries:
                    return entries[0].current
        except Exception:
            pass
        return None

    def _score_disk_health(self) -> ScoreComponent:
        """Avalia saúde dos discos (via S.M.A.R.T. se disponível, senão uso)."""
        # Tenta importar SmartMonitor
        try:
            from smart_monitor import SmartMonitor
            monitor = SmartMonitor()
            disks = monitor.get_all_disks_health()
            if disks:
                # Usa o pior disco como referência
                worst = min(disks, key=lambda d: d.health_score)
                score = worst.health_score
                msg = f"Disco {worst.device}: {worst.health_label} ({score}/100)"
                if worst.warnings:
                    msg = worst.warnings[0]
                return ScoreComponent(
                    name="disk_health", label="Saúde do Disco",
                    value=score, score=score,
                    weight=self.WEIGHTS["disk_health"],
                    status=self._get_status(score),
                    message=msg
                )
        except ImportError:
            pass

        # Fallback: avalia apenas espaço livre
        return self._score_disk_space()

    def _score_disk_space(self) -> ScoreComponent:
        """Avalia espaço em disco."""
        try:
            # Disco raiz
            if platform.system() == "Windows":
                usage = psutil.disk_usage("C:\\")
            else:
                usage = psutil.disk_usage("/")

            free_pct = 100 - usage.percent
            free_gb = usage.free / (1024 ** 3)

            if free_pct >= 30:
                score = 100
                msg = f"Espaço adequado ({free_pct:.0f}% livre, {free_gb:.1f}GB)"
            elif free_pct >= 20:
                score = int(80 - (30 - free_pct) * 3)
                msg = f"Espaço razoável ({free_pct:.0f}% livre)"
            elif free_pct >= 10:
                score = int(50 - (20 - free_pct) * 3)
                msg = f"Pouco espaço ({free_pct:.0f}% livre, {free_gb:.1f}GB) — limpe arquivos"
            else:
                score = int(free_pct * 2)
                msg = f"Disco quase cheio ({free_pct:.0f}% livre)! Libere espaço urgente."

            return ScoreComponent(
                name="disk_health", label="Espaço em Disco",
                value=usage.percent, score=max(0, score),
                weight=self.WEIGHTS["disk_health"],
                status=self._get_status(max(0, score)),
                message=msg
            )
        except Exception:
            return ScoreComponent(
                name="disk_health", label="Espaço em Disco",
                value=0, score=70,
                weight=self.WEIGHTS["disk_health"],
                status="regular",
                message="Não foi possível verificar o disco"
            )

    def _score_boot_time(self) -> ScoreComponent:
        """Avalia tempo desde o último boot (proxy para instabilidade)."""
        try:
            boot_timestamp = psutil.boot_time()
            uptime_seconds = time.time() - boot_timestamp
            uptime_hours = uptime_seconds / 3600

            # Boot recente
            if uptime_hours < 0.1:
                # Acabou de ligar — pode indicar reboot por crash
                score = 70
                msg = "Sistema recém-iniciado"
            elif uptime_hours <= 24:
                score = 100
                msg = f"Uptime saudável ({uptime_hours:.1f}h)"
            elif uptime_hours <= 168:  # 1 semana
                score = 90
                msg = f"Uptime de {uptime_hours:.0f}h ({uptime_hours/24:.0f} dias)"
            elif uptime_hours <= 720:  # 1 mês
                score = 75
                msg = f"Uptime longo ({uptime_hours/24:.0f} dias) — considere reiniciar"
            else:
                score = 50
                msg = f"Uptime muito longo ({uptime_hours/24:.0f} dias) — recomendado reiniciar"

        except Exception:
            score = 75
            msg = "Não foi possível verificar o uptime"

        return ScoreComponent(
            name="boot_time", label="Uptime do Sistema",
            value=0, score=score,
            weight=self.WEIGHTS["boot_time"],
            status=self._get_status(score),
            message=msg
        )

    # ------------------------------------------------------------------
    # Recomendações
    # ------------------------------------------------------------------
    def _generate_recommendations(self, components: list[ScoreComponent]) -> list[str]:
        """Gera recomendações baseadas nos componentes com baixo score."""
        recs = []
        for comp in sorted(components, key=lambda c: c.score):
            if comp.score >= 75:
                continue
            if comp.name == "cpu":
                recs.append("🖥️  Feche aplicativos desnecessários para reduzir uso de CPU")
                recs.append("🔍 Verifique o Gerenciador de Processos para processos pesados")
            elif comp.name == "ram":
                recs.append("💾 Feche abas do navegador e apps em segundo plano")
                recs.append("⚡ Considere executar a limpeza de memória")
            elif comp.name == "cpu_temp":
                recs.append("🌡️  Limpe o cooler e verifique a pasta térmica da CPU")
                recs.append("🌀 Aumente a velocidade das ventoinhas")
                recs.append("⚡ Ative o Modo Eco para reduzir temperatura")
            elif comp.name == "disk_health":
                recs.append("💿 Execute uma limpeza de disco imediatamente")
                recs.append("📁 Mova arquivos grandes para HD externo ou nuvem")
                recs.append("🔍 Faça backup dos seus dados — disco pode estar falhando")
            elif comp.name == "boot_time":
                recs.append("🔄 Reinicie o sistema para limpar a memória e aplicar atualizações")
        return recs[:5]  # Máximo 5 recomendações

    # ------------------------------------------------------------------
    # Cálculo principal
    # ------------------------------------------------------------------
    def calculate_score(self) -> HealthScoreResult:
        """
        Calcula o score de saúde do sistema.

        Returns:
            HealthScoreResult com score, label, cor e detalhes
        """
        components = [
            self._score_cpu(),
            self._score_ram(),
            self._score_cpu_temp(),
            self._score_disk_health(),
            self._score_boot_time(),
        ]

        # Score ponderado
        final_score = sum(c.weighted_score for c in components)
        final_score = max(0, min(100, int(round(final_score))))

        label, color = self._classify_score(final_score)
        recommendations = self._generate_recommendations(components)

        return HealthScoreResult(
            score=final_score,
            label=label,
            color=color,
            components=components,
            recommendations=recommendations,
        )


# -----------------------------------------------------------------------
# Widget CustomTkinter — Círculo de Score
# -----------------------------------------------------------------------
HEALTH_SCORE_WIDGET = '''
import customtkinter as ctk
import math
import tkinter as tk
from health_score import SystemHealthScore

class HealthScoreWidget(ctk.CTkFrame):
    """Widget que exibe o score de saúde com um círculo animado."""

    def __init__(self, parent):
        super().__init__(parent)
        self.calculator = SystemHealthScore()
        self._score = 0
        self._target_score = 0
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.canvas = tk.Canvas(self, width=180, height=180,
                                 bg=self._apply_appearance_mode(
                                     ctk.ThemeManager.theme["CTkFrame"]["fg_color"]),
                                 highlightthickness=0)
        self.canvas.pack(pady=10)

        self.score_label = ctk.CTkLabel(self, text="—",
                                         font=("Arial", 42, "bold"))
        self.score_label.pack()

        self.label_text = ctk.CTkLabel(self, text="Calculando...",
                                        font=("Arial", 14))
        self.label_text.pack()

        self.detail_frame = ctk.CTkScrollableFrame(self, height=120)
        self.detail_frame.pack(fill="x", padx=10, pady=5)

        self.rec_frame = ctk.CTkFrame(self)
        self.rec_frame.pack(fill="x", padx=10, pady=5)

        self.refresh_btn = ctk.CTkButton(self, text="🔄 Atualizar",
                                          command=self.refresh)
        self.refresh_btn.pack(pady=5)

    def refresh(self):
        """Recalcula o score e atualiza a UI."""
        self.refresh_btn.configure(state="disabled")
        import threading
        def _calc():
            result = self.calculator.calculate_score()
            self.after(0, self._update_ui, result)
        threading.Thread(target=_calc, daemon=True).start()

    def _update_ui(self, result):
        self._target_score = result.score
        self._animate_score()
        self.score_label.configure(text=str(result.score),
                                    text_color=result.color)
        self.label_text.configure(text=result.label, text_color=result.color)

        # Detalhes dos componentes
        for w in self.detail_frame.winfo_children():
            w.destroy()
        for comp in result.components:
            row = ctk.CTkFrame(self.detail_frame)
            row.pack(fill="x", padx=3, pady=1)
            ctk.CTkLabel(row, text=f"{comp.status_icon} {comp.label}",
                          width=140, anchor="w").pack(side="left")
            ctk.CTkProgressBar(row, progress_color=result.color,
                                 width=100).pack(side="left", padx=3)
            ctk.CTkLabel(row, text=str(comp.score)).pack(side="left")

        # Recomendações
        for w in self.rec_frame.winfo_children():
            w.destroy()
        for rec in result.recommendations[:3]:
            ctk.CTkLabel(self.rec_frame, text=rec,
                          font=("Arial", 11), anchor="w",
                          wraplength=280).pack(anchor="w", padx=5)

        self.refresh_btn.configure(state="normal")

    def _animate_score(self):
        """Animação suave do número do score."""
        if self._score < self._target_score:
            self._score = min(self._score + 2, self._target_score)
            self.score_label.configure(text=str(self._score))
            self.after(20, self._animate_score)
'''


if __name__ == "__main__":
    print("=== SpeedScan — Score de Saúde do Sistema ===\n")
    print("⏳ Calculando... (aguarde)")

    calculator = SystemHealthScore()
    result = calculator.calculate_score()

    print(f"\n{'='*50}")
    print(f"  SCORE FINAL: {result.score}/100 — {result.label}")
    print(f"{'='*50}\n")

    print("📊 Componentes:")
    for comp in result.components:
        bar = "█" * (comp.score // 10) + "░" * (10 - comp.score // 10)
        print(f"  {comp.status_icon} {comp.label:<20} [{bar}] {comp.score:3d}/100")
        print(f"     → {comp.message}")

    if result.recommendations:
        print(f"\n💡 Recomendações:")
        for rec in result.recommendations:
            print(f"  {rec}")
