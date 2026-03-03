"""
SpeedScan - IA Proativa
========================
Analisa métricas do sistema automaticamente e gera recomendações
usando regras built-in + integração com Ollama (IA local).

Dependências:
    pip install requests psutil
    (Ollama local opcional: https://ollama.ai)
"""

import time
import threading
import json
import platform
import psutil
from dataclasses import dataclass, field
from typing import Optional, Callable
import urllib.request
import urllib.error
import hashlib


@dataclass
class AiRecommendation:
    """Uma recomendação gerada pela IA."""
    category: str       # performance | thermal | storage | memory | network | security
    priority: str       # critical | high | medium | low
    icon: str
    title: str
    description: str
    action: str         # Ação sugerida
    auto_fixable: bool  # Se o SpeedScan pode corrigir automaticamente

    @property
    def priority_color(self) -> str:
        colors = {
            "critical": "#ff0000",
            "high":     "#ff5500",
            "medium":   "#ffaa00",
            "low":      "#00aaff",
        }
        return colors.get(self.priority, "#ffffff")


@dataclass
class DiagnosticReport:
    """Relatório completo de diagnóstico."""
    timestamp: float
    system_context: dict
    recommendations: list[AiRecommendation]
    ai_summary: str         # Texto gerado pela IA (se disponível)
    ai_available: bool
    health_score: int

    @property
    def critical_count(self) -> int:
        return sum(1 for r in self.recommendations if r.priority == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for r in self.recommendations if r.priority == "high")

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "health_score": self.health_score,
            "recommendations": [
                {
                    "category": r.category,
                    "priority": r.priority,
                    "title": r.title,
                    "description": r.description,
                    "action": r.action,
                }
                for r in self.recommendations
            ],
            "ai_summary": self.ai_summary,
        }


class ProactiveAI:
    """
    IA Proativa do SpeedScan.

    Analisa métricas em tempo real e gera recomendações usando:
    1. Regras built-in (sempre disponível, sem internet)
    2. Ollama local (se disponível)
    3. APIs externas (DeepSeek, GPT, Gemini — se configurado)

    Exemplo de uso:
        ai = ProactiveAI()

        # Análise baseada em regras
        metrics = ai.collect_metrics()
        report = ai.analyze_system(metrics)
        for rec in report.recommendations:
            print(f"{rec.icon} [{rec.priority.upper()}] {rec.title}")

        # Diagnóstico por linguagem natural
        answer = ai.generate_natural_diagnostic("Por que meu PC está lento?")
        print(answer)
    """

    OLLAMA_URL = "http://localhost:11434"
    CACHE_TTL = 120  # Segundos entre análises repetidas
    OLLAMA_MODEL = "llama3.2"  # Modelo padrão do Ollama

    def __init__(self, api_key: Optional[str] = None,
                 api_provider: str = "ollama",
                 ollama_model: str = "llama3.2"):
        self.api_key = api_key
        self.api_provider = api_provider
        self.ollama_model = ollama_model
        self._last_analysis_hash = ""
        self._last_analysis_time = 0
        self._last_report: Optional[DiagnosticReport] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False

    # ------------------------------------------------------------------
    # Coleta de Métricas
    # ------------------------------------------------------------------
    def collect_metrics(self) -> dict:
        """Coleta todas as métricas relevantes do sistema."""
        cpu_percent = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        cpu_freq = psutil.cpu_freq()

        # Temperatura
        cpu_temp = None
        try:
            temps = psutil.sensors_temperatures()
            for key in ["coretemp", "k10temp", "cpu_thermal", "acpitz"]:
                if key in temps and temps[key]:
                    cpu_temp = max(t.current for t in temps[key])
                    break
        except Exception:
            pass

        # Disco
        disk_pct = 0
        disk_free_gb = 0
        try:
            root = "C:\\" if platform.system() == "Windows" else "/"
            disk = psutil.disk_usage(root)
            disk_pct = disk.percent
            disk_free_gb = round(disk.free / (1024 ** 3), 1)
        except Exception:
            pass

        # Rede
        net = psutil.net_io_counters()
        uptime_h = (time.time() - psutil.boot_time()) / 3600

        # Processos pesados
        top_procs = []
        try:
            procs = sorted(
                [p for p in psutil.process_iter(["name", "cpu_percent", "memory_info"])
                 if p.info.get("cpu_percent", 0) > 5],
                key=lambda p: p.info.get("cpu_percent", 0),
                reverse=True
            )[:5]
            top_procs = [
                {"name": p.info["name"], "cpu": p.info["cpu_percent"]}
                for p in procs
            ]
        except Exception:
            pass

        # Bateria
        battery = None
        try:
            batt = psutil.sensors_battery()
            if batt:
                battery = {
                    "percent": batt.percent,
                    "plugged": batt.power_plugged,
                    "secs_left": batt.secsleft,
                }
        except Exception:
            pass

        return {
            "cpu_percent": cpu_percent,
            "cpu_cores": psutil.cpu_count(logical=False),
            "cpu_threads": psutil.cpu_count(logical=True),
            "cpu_freq_mhz": round(cpu_freq.current, 0) if cpu_freq else None,
            "cpu_freq_max_mhz": round(cpu_freq.max, 0) if cpu_freq else None,
            "cpu_temp_c": cpu_temp,
            "ram_percent": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 1),
            "ram_total_gb": round(ram.total / (1024**3), 1),
            "ram_available_gb": round(ram.available / (1024**3), 1),
            "disk_percent": disk_pct,
            "disk_free_gb": disk_free_gb,
            "net_bytes_sent_mb": round(net.bytes_sent / (1024**2), 1),
            "net_bytes_recv_mb": round(net.bytes_recv / (1024**2), 1),
            "uptime_hours": round(uptime_h, 1),
            "top_processes": top_procs,
            "battery": battery,
            "platform": platform.system(),
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Análise com Regras Built-in
    # ------------------------------------------------------------------
    def _analyze_rules(self, metrics: dict) -> list[AiRecommendation]:
        """Gera recomendações baseadas em regras predefinidas."""
        recs = []
        cpu = metrics.get("cpu_percent", 0)
        ram = metrics.get("ram_percent", 0)
        cpu_temp = metrics.get("cpu_temp_c")
        disk_pct = metrics.get("disk_percent", 0)
        disk_free = metrics.get("disk_free_gb", 999)
        uptime = metrics.get("uptime_hours", 0)
        battery = metrics.get("battery")

        # --- CPU ---
        if cpu >= 95:
            recs.append(AiRecommendation(
                category="performance", priority="critical",
                icon="🔴", title="CPU em estado crítico",
                description=f"Uso de CPU está em {cpu:.0f}%, o que pode causar travamentos e lentidão extrema.",
                action="Abra o Gerenciador de Processos e encerre processos desnecessários",
                auto_fixable=False
            ))
        elif cpu >= 80:
            top = metrics.get("top_processes", [])
            culprits = ", ".join(p["name"] for p in top[:3]) if top else "desconhecido"
            recs.append(AiRecommendation(
                category="performance", priority="high",
                icon="🟠", title="Uso de CPU elevado",
                description=f"CPU em {cpu:.0f}%. Principais consumidores: {culprits}.",
                action="Verifique o Gerenciador de Processos e feche aplicativos pesados",
                auto_fixable=False
            ))

        # --- RAM ---
        if ram >= 95:
            recs.append(AiRecommendation(
                category="memory", priority="critical",
                icon="🔴", title="Memória RAM quase esgotada",
                description=f"RAM em {ram:.0f}%! O sistema pode usar swap excessivamente, causando lentidão severa.",
                action="Execute a limpeza de memória RAM no SpeedScan",
                auto_fixable=True
            ))
        elif ram >= 85:
            avail = metrics.get("ram_available_gb", 0)
            recs.append(AiRecommendation(
                category="memory", priority="high",
                icon="🟠", title="Memória RAM em uso alto",
                description=f"RAM em {ram:.0f}% — apenas {avail:.1f}GB disponível.",
                action="Feche abas desnecessárias do navegador e execute a otimização de memória",
                auto_fixable=True
            ))

        # --- Temperatura ---
        if cpu_temp:
            if cpu_temp >= 90:
                recs.append(AiRecommendation(
                    category="thermal", priority="critical",
                    icon="🌡️", title="Temperatura da CPU CRÍTICA",
                    description=f"CPU a {cpu_temp:.0f}°C! Risco de dano permanente ao hardware.",
                    action="Desligue o computador imediatamente. Limpe o cooler e troque a pasta térmica.",
                    auto_fixable=False
                ))
            elif cpu_temp >= 80:
                recs.append(AiRecommendation(
                    category="thermal", priority="high",
                    icon="🌡️", title="Temperatura da CPU alta",
                    description=f"CPU a {cpu_temp:.0f}°C. O processador pode estar em throttling, reduzindo desempenho.",
                    action="Ative o Modo Eco e verifique a ventilação do gabinete",
                    auto_fixable=True
                ))
            elif cpu_temp >= 70:
                recs.append(AiRecommendation(
                    category="thermal", priority="medium",
                    icon="🟡", title="Temperatura da CPU elevada",
                    description=f"CPU a {cpu_temp:.0f}°C. Considere melhorar a ventilação.",
                    action="Verifique se as ventoinhas estão funcionando corretamente",
                    auto_fixable=False
                ))

        # --- Disco ---
        if disk_pct >= 95:
            recs.append(AiRecommendation(
                category="storage", priority="critical",
                icon="💽", title="Disco praticamente cheio",
                description=f"Disco com {disk_pct:.0f}% de uso. Apenas {disk_free:.1f}GB livre. O sistema pode parar de funcionar.",
                action="Execute a limpeza de disco e remova arquivos desnecessários",
                auto_fixable=True
            ))
        elif disk_pct >= 85:
            recs.append(AiRecommendation(
                category="storage", priority="high",
                icon="💾", title="Pouco espaço em disco",
                description=f"Disco com {disk_pct:.0f}% de uso. Apenas {disk_free:.1f}GB livre.",
                action="Execute a limpeza de cache de navegadores e arquivos temporários",
                auto_fixable=True
            ))

        # --- Uptime ---
        if uptime > 720:  # 30 dias
            recs.append(AiRecommendation(
                category="performance", priority="medium",
                icon="🔄", title="Sistema sem reiniciar há muito tempo",
                description=f"O sistema está ligado há {uptime:.0f} horas ({uptime/24:.0f} dias). Reiniciar libera memória e aplica atualizações.",
                action="Reinicie o computador em um momento conveniente",
                auto_fixable=False
            ))

        # --- Bateria ---
        if battery:
            if not battery["plugged"] and battery["percent"] <= 15:
                recs.append(AiRecommendation(
                    category="performance", priority="critical" if battery["percent"] <= 5 else "high",
                    icon="🔋", title=f"Bateria crítica ({battery['percent']:.0f}%)",
                    description="Conecte o carregador imediatamente para evitar perda de dados.",
                    action="Conecte o carregador",
                    auto_fixable=False
                ))

        return recs

    # ------------------------------------------------------------------
    # Integração com Ollama (IA Local)
    # ------------------------------------------------------------------
    def is_ollama_available(self) -> bool:
        """Verifica se o Ollama está rodando localmente."""
        try:
            req = urllib.request.Request(f"{self.OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _ask_ollama(self, prompt: str, model: str = None) -> str:
        """Envia uma pergunta para o Ollama local."""
        model = model or self.ollama_model
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 300}
        }).encode()

        req = urllib.request.Request(
            f"{self.OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("response", "").strip()

    def generate_natural_diagnostic(
        self,
        question: str,
        metrics: Optional[dict] = None
    ) -> str:
        """
        Responde a uma pergunta em linguagem natural sobre o sistema.

        Args:
            question: Pergunta do usuário (ex: "Por que meu PC está lento?")
            metrics: Métricas coletadas (se None, coleta automaticamente)

        Returns:
            Resposta em linguagem natural
        """
        if metrics is None:
            metrics = self.collect_metrics()

        # Contexto do sistema para a IA
        context = f"""
Sistema: {metrics.get('platform', 'Linux')}
CPU: {metrics.get('cpu_percent', 0):.1f}% de uso
RAM: {metrics.get('ram_percent', 0):.1f}% ({metrics.get('ram_available_gb', 0):.1f}GB livre de {metrics.get('ram_total_gb', 0):.1f}GB total)
Temperatura CPU: {metrics.get('cpu_temp_c', 'N/A')}°C
Disco: {metrics.get('disk_percent', 0):.1f}% ({metrics.get('disk_free_gb', 0):.1f}GB livre)
Uptime: {metrics.get('uptime_hours', 0):.1f} horas
Processos mais pesados: {', '.join(p['name'] for p in metrics.get('top_processes', [])[:5])}
"""

        prompt = f"""Você é o assistente de diagnóstico do SpeedScan, um software de otimização de sistema.
Analise as métricas abaixo e responda à pergunta do usuário de forma clara e objetiva em português.
Seja direto e prático. Máximo de 3 parágrafos.

Métricas do sistema:
{context}

Pergunta do usuário: {question}

Resposta:"""

        # Tenta Ollama primeiro
        if self.is_ollama_available():
            try:
                return self._ask_ollama(prompt)
            except Exception:
                pass

        # Fallback: resposta baseada em regras
        return self._rule_based_answer(question, metrics)

    def _rule_based_answer(self, question: str, metrics: dict) -> str:
        """Resposta baseada em regras quando IA não está disponível."""
        cpu = metrics.get("cpu_percent", 0)
        ram = metrics.get("ram_percent", 0)
        temp = metrics.get("cpu_temp_c", 0) or 0
        disk = metrics.get("disk_percent", 0)

        question_lower = question.lower()
        if any(w in question_lower for w in ["lento", "devagar", "travando", "lentidão"]):
            causes = []
            if cpu > 80:
                causes.append(f"CPU em uso alto ({cpu:.0f}%)")
            if ram > 80:
                causes.append(f"RAM sobrecarregada ({ram:.0f}%)")
            if temp > 75:
                causes.append(f"CPU com temperatura elevada ({temp:.0f}°C)")
            if disk > 90:
                causes.append(f"Disco quase cheio ({disk:.0f}%)")

            if causes:
                return (f"Seu PC pode estar lento devido a: {', '.join(causes)}. "
                        f"Recomendo abrir o Gerenciador de Processos do SpeedScan para "
                        f"identificar o processo causador e usar o Modo de Otimização para liberar recursos.")
            return ("Não identifiquei problemas críticos nas métricas atuais. "
                    "Tente reiniciar o sistema para liberar memória e verifique se há atualizações pendentes.")

        recs = self._analyze_rules(metrics)
        if recs:
            top_rec = recs[0]
            return f"Diagnóstico atual: {top_rec.title}. {top_rec.description} Ação recomendada: {top_rec.action}"
        return "O sistema parece estar funcionando normalmente. Não foram detectadas anomalias críticas."

    # ------------------------------------------------------------------
    # Análise Principal
    # ------------------------------------------------------------------
    def analyze_system(
        self,
        metrics: Optional[dict] = None,
        use_ai: bool = True
    ) -> DiagnosticReport:
        """
        Analisa o sistema e retorna um relatório completo.

        Args:
            metrics: Métricas já coletadas (se None, coleta agora)
            use_ai: Se True, tenta usar Ollama para análise aprofundada

        Returns:
            DiagnosticReport com todas as recomendações
        """
        if metrics is None:
            metrics = self.collect_metrics()

        # Verificar cache
        metrics_hash = hashlib.md5(
            str(sorted(metrics.items())).encode()
        ).hexdigest()

        if (metrics_hash == self._last_analysis_hash and
                time.time() - self._last_analysis_time < self.CACHE_TTL and
                self._last_report):
            return self._last_report

        # Análise por regras
        recommendations = self._analyze_rules(metrics)

        # Calcular score básico
        health_score = 100
        for rec in recommendations:
            penalty = {"critical": 30, "high": 15, "medium": 7, "low": 3}.get(rec.priority, 0)
            health_score = max(0, health_score - penalty)

        # Resumo da IA (se disponível)
        ai_summary = ""
        ai_available = False
        if use_ai and self.is_ollama_available():
            ai_available = True
            try:
                context = (
                    f"CPU: {metrics.get('cpu_percent', 0):.0f}%, "
                    f"RAM: {metrics.get('ram_percent', 0):.0f}%, "
                    f"Disco: {metrics.get('disk_percent', 0):.0f}%, "
                    f"Temperatura: {metrics.get('cpu_temp_c', 'N/A')}°C"
                )
                prompt = (
                    f"Em uma frase, dê um resumo executivo da saúde deste sistema (score: {health_score}/100): "
                    f"{context}. Seja conciso e direto."
                )
                ai_summary = self._ask_ollama(prompt)
            except Exception:
                pass

        if not ai_summary:
            if health_score >= 90:
                ai_summary = "✅ Sistema funcionando de forma excelente. Nenhuma ação necessária."
            elif health_score >= 70:
                ai_summary = f"✅ Sistema em boas condições. {len(recommendations)} ponto(s) de atenção detectado(s)."
            elif health_score >= 50:
                ai_summary = f"⚠️ Sistema com {len(recommendations)} problema(s) detectado(s). Otimização recomendada."
            else:
                ai_summary = f"🔴 Sistema em estado crítico! {len(recommendations)} problema(s) grave(s) detectado(s). Ação imediata necessária."

        report = DiagnosticReport(
            timestamp=time.time(),
            system_context=metrics,
            recommendations=sorted(recommendations,
                                    key=lambda r: ["critical", "high", "medium", "low"].index(r.priority)),
            ai_summary=ai_summary,
            ai_available=ai_available,
            health_score=health_score,
        )

        self._last_analysis_hash = metrics_hash
        self._last_analysis_time = time.time()
        self._last_report = report
        return report

    def start_proactive_monitoring(
        self,
        callback: Callable[[DiagnosticReport], None],
        interval: float = 60.0
    ):
        """
        Inicia monitoramento proativo em background.
        Chama o callback quando novos problemas são detectados.

        Args:
            callback: Função chamada com DiagnosticReport quando há novos problemas
            interval: Intervalo de verificação em segundos
        """
        def _loop():
            last_critical_count = 0
            while self._running:
                try:
                    report = self.analyze_system()
                    # Notifica apenas se houve mudança significativa
                    if report.critical_count > last_critical_count or report.critical_count > 0:
                        callback(report)
                        last_critical_count = report.critical_count
                except Exception:
                    pass
                time.sleep(interval)

        self._running = True
        self._monitor_thread = threading.Thread(target=_loop, daemon=True)
        self._monitor_thread.start()

    def stop_proactive_monitoring(self):
        """Para o monitoramento proativo."""
        self._running = False


if __name__ == "__main__":
    print("=== SpeedScan — IA Proativa ===\n")
    ai = ProactiveAI()

    print("📊 Coletando métricas do sistema...")
    metrics = ai.collect_metrics()

    print(f"\n📈 Resumo:")
    print(f"  CPU:        {metrics['cpu_percent']:.1f}%")
    print(f"  RAM:        {metrics['ram_percent']:.1f}% ({metrics['ram_available_gb']:.1f}GB livre)")
    print(f"  Disco:      {metrics['disk_percent']:.1f}% ({metrics['disk_free_gb']:.1f}GB livre)")
    if metrics.get('cpu_temp_c'):
        print(f"  Temp. CPU:  {metrics['cpu_temp_c']:.1f}°C")

    print("\n🤖 Analisando sistema...")
    report = ai.analyze_system(metrics)

    print(f"\n{'='*50}")
    print(f"  SCORE: {report.health_score}/100")
    print(f"  STATUS: {report.ai_summary}")
    print(f"{'='*50}\n")

    if report.recommendations:
        print("📋 Recomendações:")
        for rec in report.recommendations:
            print(f"\n  {rec.icon} [{rec.priority.upper()}] {rec.title}")
            print(f"     {rec.description}")
            print(f"     ➡️  {rec.action}")
    else:
        print("✅ Nenhuma recomendação — sistema funcionando bem!")

    if ai.is_ollama_available():
        print("\n🤖 Ollama disponível! Testando diagnóstico natural...")
        answer = ai.generate_natural_diagnostic("Por que meu PC está lento?", metrics)
        print(f"\nResposta: {answer}")
    else:
        print("\n💡 Dica: Instale o Ollama (https://ollama.ai) para diagnósticos em linguagem natural!")
