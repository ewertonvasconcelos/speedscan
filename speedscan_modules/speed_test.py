"""
SpeedScan - Módulo de Teste de Velocidade de Internet
======================================================
Realiza testes de download, upload, ping e jitter.
Executa em thread separada para não travar a UI.

Dependências:
    pip install speedtest-cli
"""

import threading
import time
import socket
import urllib.request
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class SpeedTestResult:
    """Resultado de um teste de velocidade."""
    download_mbps: float
    upload_mbps: float
    ping_ms: float
    jitter_ms: float
    server_name: str
    server_country: str
    isp: str
    ip: str
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "download_mbps": self.download_mbps,
            "upload_mbps": self.upload_mbps,
            "ping_ms": self.ping_ms,
            "jitter_ms": self.jitter_ms,
            "server_name": self.server_name,
            "isp": self.isp,
            "ip": self.ip,
            "timestamp": self.timestamp,
        }

    @property
    def download_label(self) -> str:
        return f"{self.download_mbps:.1f} Mbps"

    @property
    def upload_label(self) -> str:
        return f"{self.upload_mbps:.1f} Mbps"

    @property
    def ping_label(self) -> str:
        return f"{self.ping_ms:.1f} ms"

    def get_quality(self) -> tuple[str, str]:
        """Retorna (classificação, cor) baseado no download."""
        dl = self.download_mbps
        if dl >= 100:
            return ("Excelente", "#00ff88")
        elif dl >= 50:
            return ("Ótima", "#88ff00")
        elif dl >= 25:
            return ("Boa", "#ffee00")
        elif dl >= 10:
            return ("Regular", "#ffaa00")
        elif dl >= 5:
            return ("Ruim", "#ff5500")
        return ("Muito Ruim", "#ff0000")


class SpeedTestManager:
    """
    Gerencia testes de velocidade de internet.

    Exemplo de uso:
        manager = SpeedTestManager()
        manager.run_test(
            on_progress=lambda msg: print(f"Progresso: {msg}"),
            on_complete=lambda result: print(f"Download: {result.download_label}")
        )
    """

    def __init__(self):
        self._running = False
        self._last_result: Optional[SpeedTestResult] = None

    def is_online(self) -> bool:
        """Verifica conexão com a internet."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def run_test(
        self,
        on_progress: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[SpeedTestResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        Inicia teste de velocidade em thread separada.

        Args:
            on_progress: Callback com mensagem de progresso
            on_complete: Callback com SpeedTestResult ao finalizar
            on_error: Callback com mensagem de erro
        """
        if self._running:
            if on_error:
                on_error("Teste já em andamento.")
            return

        def _run():
            self._running = True
            try:
                result = self._run_speedtest(on_progress)
                self._last_result = result
                if on_complete:
                    on_complete(result)
            except Exception as e:
                if on_error:
                    on_error(str(e))
            finally:
                self._running = False

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _run_speedtest(
        self,
        on_progress: Optional[Callable] = None
    ) -> SpeedTestResult:
        """Executa o teste usando speedtest-cli."""

        def progress(msg: str):
            if on_progress:
                on_progress(msg)

        # Tenta usar speedtest-cli
        try:
            import speedtest as st_lib
            progress("🔍 Detectando servidores disponíveis...")
            s = st_lib.Speedtest()
            s.get_best_server()

            server = s.results.server
            server_name = f"{server.get('sponsor', 'N/A')} ({server.get('name', 'N/A')})"
            server_country = server.get("country", "N/A")
            isp = s.results.client.get("isp", "N/A")
            ip = s.results.client.get("ip", "N/A")

            progress("📥 Testando download...")
            download_bps = s.download(threads=4)

            progress("📤 Testando upload...")
            upload_bps = s.upload(threads=4, pre_allocate=False)

            progress("📡 Medindo latência...")
            ping = s.results.ping
            jitter = self._measure_jitter()

            progress("✅ Teste concluído!")

            return SpeedTestResult(
                download_mbps=round(download_bps / 1_000_000, 2),
                upload_mbps=round(upload_bps / 1_000_000, 2),
                ping_ms=round(ping, 1),
                jitter_ms=round(jitter, 1),
                server_name=server_name,
                server_country=server_country,
                isp=isp,
                ip=ip,
                timestamp=time.time(),
            )

        except ImportError:
            progress("⚠️  speedtest-cli não instalado. Usando método alternativo...")
            return self._fallback_test(on_progress)

    def _fallback_test(
        self,
        on_progress: Optional[Callable] = None
    ) -> SpeedTestResult:
        """Fallback: teste básico usando urllib (apenas download)."""

        def progress(msg: str):
            if on_progress:
                on_progress(msg)

        progress("📡 Medindo ping...")
        ping = self._measure_ping("8.8.8.8")
        jitter = self._measure_jitter()

        progress("📥 Testando download (método alternativo)...")
        # URL de arquivo de teste público (10MB)
        test_url = "https://speed.cloudflare.com/__down?bytes=10000000"
        download_mbps = self._measure_download_speed(test_url)

        progress("✅ Teste concluído (apenas download disponível no modo alternativo)!")

        return SpeedTestResult(
            download_mbps=download_mbps,
            upload_mbps=0.0,
            ping_ms=ping,
            jitter_ms=jitter,
            server_name="Cloudflare (fallback)",
            server_country="Global",
            isp="N/A",
            ip=self._get_public_ip(),
            timestamp=time.time(),
        )

    def _measure_download_speed(self, url: str) -> float:
        """Mede velocidade de download via urllib."""
        try:
            start = time.time()
            total_bytes = 0
            req = urllib.request.Request(url, headers={"User-Agent": "SpeedScan/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                while True:
                    chunk = response.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    total_bytes += len(chunk)
            elapsed = time.time() - start
            if elapsed > 0:
                return round((total_bytes * 8) / elapsed / 1_000_000, 2)  # Mbps
        except Exception:
            pass
        return 0.0

    def _measure_ping(self, host: str = "8.8.8.8") -> float:
        """Mede latência média para um host."""
        times = []
        for _ in range(4):
            try:
                start = time.time()
                socket.create_connection((host, 53), timeout=3)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
            except Exception:
                pass
            time.sleep(0.2)
        return round(sum(times) / len(times), 1) if times else 999.0

    def _measure_jitter(self, host: str = "8.8.8.8", samples: int = 10) -> float:
        """Calcula jitter (variação de latência)."""
        pings = []
        for _ in range(samples):
            try:
                start = time.time()
                socket.create_connection((host, 53), timeout=2)
                elapsed = (time.time() - start) * 1000
                pings.append(elapsed)
            except Exception:
                pass
            time.sleep(0.1)

        if len(pings) < 2:
            return 0.0

        diffs = [abs(pings[i] - pings[i-1]) for i in range(1, len(pings))]
        return round(sum(diffs) / len(diffs), 1)

    def _get_public_ip(self) -> str:
        """Obtém IP público."""
        try:
            with urllib.request.urlopen("https://api.ipify.org", timeout=5) as resp:
                return resp.read().decode().strip()
        except Exception:
            return "N/A"

    @property
    def last_result(self) -> Optional[SpeedTestResult]:
        """Retorna o resultado do último teste."""
        return self._last_result

    @property
    def is_running(self) -> bool:
        return self._running


# -----------------------------------------------------------------------
# Widget CustomTkinter para Speed Test
# -----------------------------------------------------------------------
SPEED_TEST_WIDGET = '''
import customtkinter as ctk
from speed_test import SpeedTestManager

class SpeedTestTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.manager = SpeedTestManager()
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="🌐 Teste de Velocidade",
                     font=("Arial", 16, "bold")).pack(pady=10)

        # Labels de resultado
        self.dl_label = ctk.CTkLabel(self, text="📥 Download: —", font=("Arial", 14))
        self.dl_label.pack(pady=3)

        self.ul_label = ctk.CTkLabel(self, text="📤 Upload: —", font=("Arial", 14))
        self.ul_label.pack(pady=3)

        self.ping_label = ctk.CTkLabel(self, text="📡 Ping: —", font=("Arial", 14))
        self.ping_label.pack(pady=3)

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=5)

        self.btn = ctk.CTkButton(self, text="▶ Iniciar Teste",
                                  command=self._start_test)
        self.btn.pack(pady=10)

    def _start_test(self):
        self.btn.configure(state="disabled", text="⏳ Testando...")
        self.manager.run_test(
            on_progress=lambda msg: self.after(0, self.status_label.configure, {"text": msg}),
            on_complete=self._on_complete,
            on_error=self._on_error,
        )

    def _on_complete(self, result):
        quality, color = result.get_quality()
        self.after(0, lambda: self.dl_label.configure(
            text=f"📥 Download: {result.download_label}",
            text_color=color
        ))
        self.after(0, lambda: self.ul_label.configure(
            text=f"📤 Upload: {result.upload_label}"
        ))
        self.after(0, lambda: self.ping_label.configure(
            text=f"📡 Ping: {result.ping_label} | Jitter: {result.jitter_ms:.1f}ms"
        ))
        self.after(0, lambda: self.btn.configure(
            state="normal", text="▶ Testar Novamente"
        ))

    def _on_error(self, error):
        self.after(0, lambda: self.status_label.configure(
            text=f"❌ Erro: {error}", text_color="red"
        ))
        self.after(0, lambda: self.btn.configure(
            state="normal", text="▶ Tentar Novamente"
        ))
'''

if __name__ == "__main__":
    import sys

    manager = SpeedTestManager()

    if not manager.is_online():
        print("❌ Sem conexão com a internet.")
        sys.exit(1)

    print("=== SpeedScan — Teste de Velocidade ===\n")

    done = threading.Event()
    result_holder = []

    def on_progress(msg):
        print(f"  {msg}")

    def on_complete(result: SpeedTestResult):
        result_holder.append(result)
        done.set()

    def on_error(err):
        print(f"❌ Erro: {err}")
        done.set()

    manager.run_test(on_progress=on_progress, on_complete=on_complete, on_error=on_error)
    done.wait()

    if result_holder:
        r = result_holder[0]
        quality, color = r.get_quality()
        print(f"\n📊 Resultados:")
        print(f"  📥 Download:  {r.download_label}")
        print(f"  📤 Upload:    {r.upload_label}")
        print(f"  📡 Ping:      {r.ping_label}")
        print(f"  〰️  Jitter:    {r.jitter_ms:.1f} ms")
        print(f"  🌍 Servidor:  {r.server_name}")
        print(f"  🏢 Provedor:  {r.isp}")
        print(f"  🌐 IP:        {r.ip}")
        print(f"  ⭐ Qualidade: {quality}")
