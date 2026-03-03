#!/usr/bin/env python3
"""
SpeedScan - Exemplo de Integração dos Novos Módulos
=====================================================
Este arquivo mostra como integrar TODOS os novos módulos
ao projeto SpeedScan existente com CustomTkinter.

Execute: python main_integration.py
"""

import customtkinter as ctk
import tkinter as tk
import threading
import time
import psutil

# --- Importar os novos módulos ---
try:
    from temperature_monitor import TemperatureMonitor
    HAS_TEMP = True
except ImportError:
    HAS_TEMP = False

try:
    from health_score import SystemHealthScore
    HAS_HEALTH = True
except ImportError:
    HAS_HEALTH = False

try:
    from process_manager import ProcessManager
    HAS_PROC = True
except ImportError:
    HAS_PROC = False

try:
    from browser_cleaner import BrowserCleaner
    HAS_BROWSER = True
except ImportError:
    HAS_BROWSER = False

try:
    from speed_test import SpeedTestManager
    HAS_SPEED = True
except ImportError:
    HAS_SPEED = False

try:
    from historical_metrics import MetricsDatabase
    HAS_HISTORY = True
except ImportError:
    HAS_HISTORY = False

try:
    from ai_proactive import ProactiveAI
    HAS_AI = True
except ImportError:
    HAS_AI = False

try:
    from lan_scanner import LanScanner
    HAS_LAN = True
except ImportError:
    HAS_LAN = False

try:
    from smart_monitor import SmartMonitor
    HAS_SMART = True
except ImportError:
    HAS_SMART = False


# =====================================================================
# TAB: HEALTH SCORE
# =====================================================================
class HealthScoreTab(ctk.CTkFrame):
    """Aba com Score de Saúde do Sistema (0-100)."""

    def __init__(self, parent):
        super().__init__(parent)
        if not HAS_HEALTH:
            ctk.CTkLabel(self, text="⚠️ Módulo health_score.py não encontrado").pack(pady=20)
            return
        self.calculator = SystemHealthScore()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Título
        ctk.CTkLabel(self, text="🏥 Saúde do Sistema",
                     font=("Arial", 18, "bold")).pack(pady=(15, 5))

        # Frame do score
        score_frame = ctk.CTkFrame(self, corner_radius=15)
        score_frame.pack(padx=20, pady=10, fill="x")

        self.score_label = ctk.CTkLabel(
            score_frame, text="—",
            font=("Arial", 64, "bold"),
            text_color="#00ff88"
        )
        self.score_label.pack(pady=(20, 5))

        self.status_label = ctk.CTkLabel(
            score_frame, text="Calculando...",
            font=("Arial", 18)
        )
        self.status_label.pack(pady=(0, 10))

        self.summary_label = ctk.CTkLabel(
            score_frame, text="",
            font=("Arial", 12),
            wraplength=400,
            text_color="gray"
        )
        self.summary_label.pack(pady=(0, 15))

        # Barra de progresso do score
        self.progress = ctk.CTkProgressBar(score_frame, width=300, height=15)
        self.progress.set(0)
        self.progress.pack(pady=(0, 20))

        # Componentes individuais
        comp_frame = ctk.CTkFrame(self)
        comp_frame.pack(padx=20, pady=5, fill="x")
        ctk.CTkLabel(comp_frame, text="📊 Detalhes por Componente",
                     font=("Arial", 13, "bold")).pack(pady=8)
        self.comp_inner = ctk.CTkScrollableFrame(comp_frame, height=120)
        self.comp_inner.pack(fill="x", padx=10, pady=(0, 10))

        # Recomendações
        rec_frame = ctk.CTkFrame(self)
        rec_frame.pack(padx=20, pady=5, fill="x")
        ctk.CTkLabel(rec_frame, text="💡 Recomendações",
                     font=("Arial", 13, "bold")).pack(pady=8)
        self.rec_inner = ctk.CTkFrame(rec_frame)
        self.rec_inner.pack(fill="x", padx=10, pady=(0, 10))

        # Botão
        ctk.CTkButton(
            self, text="🔄 Atualizar Score",
            command=self.refresh,
            height=35, width=200
        ).pack(pady=10)

    def refresh(self):
        def _calc():
            result = self.calculator.calculate_score()
            self.after(0, self._update, result)
        threading.Thread(target=_calc, daemon=True).start()

    def _update(self, result):
        self.score_label.configure(
            text=str(result.score),
            text_color=result.color
        )
        self.status_label.configure(
            text=result.label,
            text_color=result.color
        )
        self.progress.configure(progress_color=result.color)
        self.progress.set(result.score / 100)

        # Componentes
        for w in self.comp_inner.winfo_children():
            w.destroy()
        for comp in result.components:
            row = ctk.CTkFrame(self.comp_inner)
            row.pack(fill="x", padx=3, pady=2)
            ctk.CTkLabel(row, text=f"{comp.status_icon} {comp.label}",
                          width=160, anchor="w").pack(side="left", padx=5)
            pb = ctk.CTkProgressBar(row, width=120, height=10,
                                     progress_color=result.color)
            pb.set(comp.score / 100)
            pb.pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"{comp.score}/100",
                          width=60).pack(side="left")
            ctk.CTkLabel(row, text=comp.message,
                          font=("Arial", 10), text_color="gray",
                          anchor="w").pack(side="left", padx=5)

        # Recomendações
        for w in self.rec_inner.winfo_children():
            w.destroy()
        if result.recommendations:
            for rec in result.recommendations[:4]:
                ctk.CTkLabel(
                    self.rec_inner, text=rec,
                    anchor="w", font=("Arial", 11),
                    wraplength=450
                ).pack(anchor="w", padx=10, pady=2)
        else:
            ctk.CTkLabel(self.rec_inner, text="✅ Nenhuma recomendação — sistema saudável!",
                          text_color="#00ff88").pack(pady=5)


# =====================================================================
# TAB: TEMPERATURA
# =====================================================================
class TemperatureTab(ctk.CTkFrame):
    """Aba de monitoramento de temperatura em tempo real."""

    def __init__(self, parent):
        super().__init__(parent)
        if not HAS_TEMP:
            ctk.CTkLabel(self, text="⚠️ Módulo temperature_monitor.py não encontrado").pack(pady=20)
            return
        self.monitor = TemperatureMonitor()
        self._build_ui()
        self.monitor.start_monitoring(self._on_update, interval=3)

    def _build_ui(self):
        ctk.CTkLabel(self, text="🌡️ Temperatura do Sistema",
                     font=("Arial", 18, "bold")).pack(pady=15)

        # Grid de cards de temperatura
        self.cards_frame = ctk.CTkScrollableFrame(self)
        self.cards_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.no_data_label = ctk.CTkLabel(
            self.cards_frame,
            text="⏳ Aguardando dados de temperatura...",
            text_color="gray"
        )
        self.no_data_label.pack(pady=20)

    def _on_update(self, sensors):
        self.after(0, self._refresh, sensors)

    def _refresh(self, sensors):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        if not sensors:
            ctk.CTkLabel(
                self.cards_frame,
                text="⚠️  Sensores de temperatura não disponíveis nesta plataforma.\n"
                     "(Linux com lm-sensors / Windows com WMI / macOS com osx-cpu-temp)",
                text_color="gray", wraplength=400
            ).pack(pady=20)
            return

        # Agrupar por tipo (CPU vs GPU)
        cpu_sensors = [s for s in sensors if "gpu" not in s.name.lower()]
        gpu_sensors = [s for s in sensors if "gpu" in s.name.lower()]

        def render_group(title, sensor_list):
            if not sensor_list:
                return
            ctk.CTkLabel(self.cards_frame, text=title,
                          font=("Arial", 13, "bold")).pack(anchor="w", padx=5, pady=(10, 3))

            for sensor in sensor_list:
                color_map = {
                    "normal":   "#00ff88",
                    "warning":  "#ffaa00",
                    "critical": "#ff4444",
                }
                color = color_map.get(sensor.status, "white")

                card = ctk.CTkFrame(self.cards_frame, corner_radius=8)
                card.pack(fill="x", padx=5, pady=3)

                left = ctk.CTkFrame(card, fg_color="transparent")
                left.pack(side="left", padx=10, pady=8, fill="y")

                ctk.CTkLabel(left, text=sensor.label,
                              font=("Arial", 12, "bold"), anchor="w").pack(anchor="w")

                if sensor.high or sensor.critical:
                    thresholds = ""
                    if sensor.high:
                        thresholds += f"Alto: {sensor.high}°C  "
                    if sensor.critical:
                        thresholds += f"Crítico: {sensor.critical}°C"
                    ctk.CTkLabel(left, text=thresholds,
                                  font=("Arial", 9), text_color="gray").pack(anchor="w")

                ctk.CTkLabel(
                    card,
                    text=f"{sensor.current:.1f}°C",
                    font=("Arial", 24, "bold"),
                    text_color=color
                ).pack(side="right", padx=15, pady=8)

                # Barra de temperatura
                max_temp = sensor.critical or 100
                pb = ctk.CTkProgressBar(card, height=6, progress_color=color)
                pb.set(min(sensor.current / max_temp, 1.0))
                pb.pack(fill="x", padx=10, pady=(0, 8))

        render_group("🖥️  CPU", cpu_sensors)
        render_group("🎮  GPU", gpu_sensors)


# =====================================================================
# TAB: PROCESSOS
# =====================================================================
class ProcessTab(ctk.CTkFrame):
    """Aba de gerenciamento de processos."""

    def __init__(self, parent):
        super().__init__(parent)
        if not HAS_PROC:
            ctk.CTkLabel(self, text="⚠️ Módulo process_manager.py não encontrado").pack(pady=20)
            return
        self.manager = ProcessManager()
        self._selected_pid = None
        self._build_ui()
        self.manager.start_auto_refresh(self._on_update, interval=2)

    def _build_ui(self):
        ctk.CTkLabel(self, text="⚙️ Gerenciador de Processos",
                     font=("Arial", 18, "bold")).pack(pady=(15, 5))

        # Barra de controles
        bar = ctk.CTkFrame(self)
        bar.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(bar, text="🔍").pack(side="left", padx=3)
        self.filter_entry = ctk.CTkEntry(bar, placeholder_text="Filtrar por nome...", width=180)
        self.filter_entry.pack(side="left", padx=3)
        self.filter_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        self.kill_btn = ctk.CTkButton(
            bar, text="⛔ Encerrar",
            fg_color="#cc2222", hover_color="#aa1111",
            state="disabled", width=130,
            command=self._kill_selected
        )
        self.kill_btn.pack(side="right", padx=5)

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color="#1a1a2e")
        header.pack(fill="x", padx=15, pady=(3, 0))
        for text, width in [("PID", 55), ("Nome", 160), ("CPU%", 65), ("RAM MB", 75), ("Status", 95), ("Usuário", 110)]:
            ctk.CTkLabel(header, text=text, width=width,
                          font=("Arial", 11, "bold"), anchor="w").pack(side="left", padx=2)

        # Tabela scrollável
        self.table = ctk.CTkScrollableFrame(self)
        self.table.pack(fill="both", expand=True, padx=15, pady=2)

        # Status bar
        self.status_var = tk.StringVar(value="Carregando...")
        ctk.CTkLabel(self, textvariable=self.status_var,
                      font=("Arial", 10), anchor="w",
                      text_color="gray").pack(anchor="w", padx=15, pady=3)

    def _on_update(self, processes):
        self.after(0, self._refresh_table, processes)

    def _refresh_table(self, processes):
        for w in self.table.winfo_children():
            w.destroy()

        filt = self.filter_entry.get().lower()
        if filt:
            processes = [p for p in processes if filt in p.name.lower()]

        for i, proc in enumerate(processes[:80]):
            bg = "#1e1e2e" if i % 2 == 0 else "#16162a"
            row = ctk.CTkFrame(self.table, fg_color=bg, corner_radius=3)
            row.pack(fill="x", pady=1)
            row.bind("<Button-1>", lambda e, p=proc: self._select(p))

            cpu_c = "#ff5555" if proc.cpu_percent > 50 else "#ffaa00" if proc.cpu_percent > 15 else "#aaaaaa"
            ram_c = "#ff5555" if proc.ram_mb > 1000 else "#ffaa00" if proc.ram_mb > 400 else "#aaaaaa"

            for text, color, width in [
                (str(proc.pid),               "#aaaaaa", 55),
                (proc.name[:20],              "white",   160),
                (f"{proc.cpu_percent:.1f}%",  cpu_c,     65),
                (f"{proc.ram_mb:.0f}",        ram_c,     75),
                (proc.status,                 "#888888", 95),
                (proc.user[:14],              "#666666", 110),
            ]:
                lbl = ctk.CTkLabel(row, text=text, width=width,
                                    text_color=color, anchor="w",
                                    font=("Courier", 11))
                lbl.pack(side="left", padx=2)
                lbl.bind("<Button-1>", lambda e, p=proc: self._select(p))

        summary = self.manager.get_system_summary()
        self.status_var.set(
            f"{summary['total_processes']} processos | {summary['running']} rodando | "
            f"CPU: {summary['total_cpu']:.1f}% | RAM: {summary['total_ram_percent']:.1f}%"
        )

    def _select(self, proc):
        self._selected_pid = proc.pid
        self.kill_btn.configure(state="normal", text=f"⛔ {proc.name[:15]} ({proc.pid})")

    def _kill_selected(self):
        if not self._selected_pid:
            return
        ok, msg = self.manager.kill_process(self._selected_pid)
        self.status_var.set(msg)
        self._selected_pid = None
        self.kill_btn.configure(state="disabled", text="⛔ Encerrar")

    def _apply_filter(self):
        if self.manager._cache:
            self._refresh_table(self.manager._cache)


# =====================================================================
# TAB: SPEED TEST
# =====================================================================
class SpeedTestTab(ctk.CTkFrame):
    """Aba de teste de velocidade de internet."""

    def __init__(self, parent):
        super().__init__(parent)
        if not HAS_SPEED:
            ctk.CTkLabel(self, text="⚠️ Módulo speed_test.py não encontrado").pack(pady=20)
            return
        self.manager = SpeedTestManager()
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="🌐 Teste de Velocidade",
                     font=("Arial", 18, "bold")).pack(pady=15)

        card = ctk.CTkFrame(self, corner_radius=15)
        card.pack(padx=30, pady=10, fill="x")

        # Métricas principais
        metrics_frame = ctk.CTkFrame(card, fg_color="transparent")
        metrics_frame.pack(pady=20, fill="x")

        for col, (label, attr, icon) in enumerate([
            ("Download", "dl_val", "📥"),
            ("Upload",   "ul_val", "📤"),
            ("Ping",     "ping_val", "📡"),
        ]):
            f = ctk.CTkFrame(metrics_frame, fg_color="transparent")
            f.grid(row=0, column=col, padx=20, sticky="nsew")
            metrics_frame.columnconfigure(col, weight=1)
            ctk.CTkLabel(f, text=icon + " " + label,
                          font=("Arial", 12), text_color="gray").pack()
            lbl = ctk.CTkLabel(f, text="—",
                                font=("Arial", 26, "bold"))
            lbl.pack()
            setattr(self, attr, lbl)

        # Status e botão
        self.status_lbl = ctk.CTkLabel(card, text="Pronto para testar",
                                        text_color="gray", font=("Arial", 11))
        self.status_lbl.pack(pady=5)

        ctk.CTkProgressBar(card, mode="indeterminate",
                            height=4).pack(fill="x", padx=20, pady=5)

        self.test_btn = ctk.CTkButton(
            self, text="▶ Iniciar Teste",
            height=40, width=200, font=("Arial", 14),
            command=self._start
        )
        self.test_btn.pack(pady=15)

        # Histórico de testes
        ctk.CTkLabel(self, text="📊 Último Resultado",
                     font=("Arial", 12, "bold")).pack(anchor="w", padx=30)
        self.history_frame = ctk.CTkFrame(self)
        self.history_frame.pack(fill="x", padx=20, pady=5)

    def _start(self):
        self.test_btn.configure(state="disabled", text="⏳ Testando...")
        self.manager.run_test(
            on_progress=lambda m: self.after(0, self.status_lbl.configure, {"text": m}),
            on_complete=self._on_complete,
            on_error=self._on_error,
        )

    def _on_complete(self, result):
        quality, color = result.get_quality()
        self.after(0, lambda: [
            self.dl_val.configure(text=result.download_label, text_color=color),
            self.ul_val.configure(text=result.upload_label),
            self.ping_val.configure(text=result.ping_label),
            self.status_lbl.configure(text=f"✅ Qualidade: {quality} | {result.isp} | {result.ip}"),
            self.test_btn.configure(state="normal", text="▶ Testar Novamente"),
        ])

    def _on_error(self, error):
        self.after(0, lambda: [
            self.status_lbl.configure(text=f"❌ {error}", text_color="red"),
            self.test_btn.configure(state="normal", text="▶ Tentar Novamente"),
        ])


# =====================================================================
# TAB: IA PROATIVA
# =====================================================================
class AIProactiveTab(ctk.CTkFrame):
    """Aba do Agente IA Proativo."""

    def __init__(self, parent):
        super().__init__(parent)
        if not HAS_AI:
            ctk.CTkLabel(self, text="⚠️ Módulo ai_proactive.py não encontrado").pack(pady=20)
            return
        self.ai = ProactiveAI()
        self._build_ui()
        self.analyze()

    def _build_ui(self):
        ctk.CTkLabel(self, text="🤖 IA Proativa",
                     font=("Arial", 18, "bold")).pack(pady=15)

        # Summary
        self.summary_lbl = ctk.CTkLabel(
            self, text="🔍 Analisando sistema...",
            font=("Arial", 13), wraplength=500
        )
        self.summary_lbl.pack(pady=5, padx=20)

        # Chat
        ctk.CTkLabel(self, text="💬 Pergunte ao Assistente",
                     font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(15, 3))

        chat_frame = ctk.CTkFrame(self)
        chat_frame.pack(fill="x", padx=20, pady=5)

        self.question_entry = ctk.CTkEntry(
            chat_frame,
            placeholder_text="Ex: Por que meu PC está lento?",
            height=36, font=("Arial", 12)
        )
        self.question_entry.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        self.question_entry.bind("<Return>", lambda e: self._ask())

        ctk.CTkButton(chat_frame, text="Perguntar",
                       width=100, command=self._ask).pack(side="right", padx=5)

        self.answer_box = ctk.CTkTextbox(self, height=100, font=("Arial", 11))
        self.answer_box.pack(fill="x", padx=20, pady=5)
        self.answer_box.insert("0.0", "Resposta aparecerá aqui...")
        self.answer_box.configure(state="disabled")

        # Recomendações
        ctk.CTkLabel(self, text="📋 Recomendações Atuais",
                     font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(10, 3))
        self.rec_frame = ctk.CTkScrollableFrame(self, height=150)
        self.rec_frame.pack(fill="both", expand=True, padx=20, pady=5)

        ctk.CTkButton(self, text="🔄 Reanalisar",
                       command=self.analyze).pack(pady=8)

    def analyze(self):
        def _run():
            report = self.ai.analyze_system()
            self.after(0, self._update_report, report)
        threading.Thread(target=_run, daemon=True).start()

    def _update_report(self, report):
        self.summary_lbl.configure(
            text=f"Score: {report.health_score}/100 | {report.ai_summary}"
        )
        for w in self.rec_frame.winfo_children():
            w.destroy()
        if not report.recommendations:
            ctk.CTkLabel(self.rec_frame, text="✅ Sistema funcionando bem!",
                          text_color="#00ff88").pack(pady=10)
        for rec in report.recommendations:
            card = ctk.CTkFrame(self.rec_frame, corner_radius=6)
            card.pack(fill="x", padx=3, pady=3)
            ctk.CTkLabel(card, text=f"{rec.icon} {rec.title}",
                          font=("Arial", 11, "bold"),
                          text_color=rec.priority_color,
                          anchor="w").pack(anchor="w", padx=8, pady=(6, 0))
            ctk.CTkLabel(card, text=rec.action,
                          font=("Arial", 10), text_color="gray",
                          anchor="w", wraplength=440).pack(anchor="w", padx=8, pady=(0, 6))

    def _ask(self):
        question = self.question_entry.get().strip()
        if not question:
            return
        self.answer_box.configure(state="normal")
        self.answer_box.delete("0.0", "end")
        self.answer_box.insert("0.0", "⏳ Processando pergunta...")
        self.answer_box.configure(state="disabled")

        def _run():
            answer = self.ai.generate_natural_diagnostic(question)
            self.after(0, lambda: [
                self.answer_box.configure(state="normal"),
                self.answer_box.delete("0.0", "end"),
                self.answer_box.insert("0.0", answer),
                self.answer_box.configure(state="disabled"),
            ])
        threading.Thread(target=_run, daemon=True).start()


# =====================================================================
# JANELA PRINCIPAL DE DEMONSTRAÇÃO
# =====================================================================
class SpeedScanNewFeatures(ctk.CTk):
    """
    Janela de demonstração com as novas funcionalidades do SpeedScan.
    Para integrar ao projeto original, adicione cada Tab ao seu sistema de abas.
    """

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("SpeedScan — Novas Funcionalidades (Demonstração)")
        self.geometry("800x700")
        self.minsize(700, 500)

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#0f3460", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="⚡ SpeedScan v1.0 — Novas Funcionalidades",
            font=("Arial", 16, "bold"),
            text_color="#00d4ff"
        ).pack(pady=12, padx=20)

        # TabView
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)

        tab_configs = [
            ("🏥 Saúde",      HealthScoreTab),
            ("🌡️ Temperatura", TemperatureTab),
            ("⚙️ Processos",   ProcessTab),
            ("🌐 Speed Test",  SpeedTestTab),
            ("🤖 IA Proativa", AIProactiveTab),
        ]

        for tab_name, TabClass in tab_configs:
            tab = tabs.add(tab_name)
            widget = TabClass(tab)
            widget.pack(fill="both", expand=True)

        # Footer
        footer = ctk.CTkFrame(self, fg_color="#0a0a1a", height=25, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        ctk.CTkLabel(
            footer,
            text="github.com/ewertonvasconcelos/speedscan — Pressione Ctrl+Q para sair",
            font=("Arial", 9), text_color="#444466"
        ).pack(pady=4)

        self.bind("<Control-q>", lambda e: self.destroy())


if __name__ == "__main__":
    print("🚀 Iniciando SpeedScan — Demonstração de Novas Funcionalidades...")
    print("   Módulos disponíveis:")
    print(f"   {'✅' if HAS_HEALTH  else '❌'} health_score")
    print(f"   {'✅' if HAS_TEMP    else '❌'} temperature_monitor")
    print(f"   {'✅' if HAS_PROC    else '❌'} process_manager")
    print(f"   {'✅' if HAS_SPEED   else '❌'} speed_test")
    print(f"   {'✅' if HAS_AI      else '❌'} ai_proactive")
    print(f"   {'✅' if HAS_HISTORY else '❌'} historical_metrics")
    print(f"   {'✅' if HAS_LAN     else '❌'} lan_scanner")
    print(f"   {'✅' if HAS_SMART   else '❌'} smart_monitor")
    print()

    app = SpeedScanNewFeatures()
    app.mainloop()
