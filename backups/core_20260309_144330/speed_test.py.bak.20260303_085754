#!/usr/bin/env python3
# core/speed_test.py
# =============================================================================
#   ███████╗██████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ █████╗ ███╗   ██╗
#   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║
#   ███████╗██████╔╝█████╗  █████╗  ██║  ██║█████╗  ██║     ███████║██╔██╗ ██║
#   ╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║  ██║██╔══╝  ██║     ██╔══██║██║╚██╗██║
#   ███████║██║     ███████╗███████╗██████╔╝███████╗╚██████╗██║  ██║██║ ╚████║
#   ╚══════╝╚═╝     ╚══════╝╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
# =============================================================================
# Módulo de teste de velocidade de internet
# Versão 0.0.9-beta
# =============================================================================

import subprocess
import re
import time
import threading
import sys
import os

try:
    import speedtest
except ImportError:
    print("Instalando speedtest-cli...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "speedtest-cli"])
    import speedtest

class SpeedTester:
    def __init__(self, use_fallback=False):
        self.use_fallback = use_fallback
        self.result = {
            'ping': None,
            'download': None,
            'upload': None,
            'server': None,
            'timestamp': None,
            'error': None
        }

    def test_with_speedtest(self):
        try:
            st = speedtest.Speedtest(secure=True)
            st.get_best_server()
            self.result['ping'] = round(st.results.ping, 1)
            self.result['server'] = f"{st.results.server['name']} ({st.results.server['country']})"
            download_bps = st.download()
            self.result['download'] = round(download_bps / 1_000_000, 2)
            upload_bps = st.upload()
            self.result['upload'] = round(upload_bps / 1_000_000, 2)
            self.result['timestamp'] = time.time()
            return True
        except Exception as e:
            self.result['error'] = str(e)
            return False

    def test_fallback(self):
        import requests
        import tempfile
        try:
            start = time.time()
            requests.get("https://www.google.com", timeout=5)
            ping = (time.time() - start) * 1000
            self.result['ping'] = round(ping, 1)

            url_download = "http://speedtest.tele2.net/10MB.zip"
            with tempfile.NamedTemporaryFile() as tmp:
                start = time.time()
                r = requests.get(url_download, stream=True, timeout=30)
                size = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        size += len(chunk)
                        tmp.write(chunk)
                elapsed = time.time() - start
                download_mbps = (size * 8) / elapsed / 1_000_000
                self.result['download'] = round(download_mbps, 2)

            data = os.urandom(5 * 1024 * 1024)
            start = time.time()
            requests.post("https://httpbin.org/post", data=data, timeout=30)
            elapsed = time.time() - start
            upload_mbps = (len(data) * 8) / elapsed / 1_000_000
            self.result['upload'] = round(upload_mbps, 2)

            self.result['server'] = "Fallback (servidores públicos)"
            self.result['timestamp'] = time.time()
            return True
        except Exception as e:
            self.result['error'] = str(e)
            return False

    def run_test(self, callback=None):
        def _run():
            if self.use_fallback:
                success = self.test_fallback()
            else:
                success = self.test_with_speedtest()
                if not success:
                    self.use_fallback = True
                    success = self.test_fallback()
            if callback:
                callback(self.result)
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread

    def format_result(self, result=None):
        if result is None:
            result = self.result
        if result.get('error'):
            return f"❌ Erro: {result['error']}"
        lines = []
        if result.get('ping') is not None:
            lines.append(f"📡 Ping: {result['ping']} ms")
        if result.get('download') is not None:
            lines.append(f"⬇️ Download: {result['download']} Mbps")
        if result.get('upload') is not None:
            lines.append(f"⬆️ Upload: {result['upload']} Mbps")
        if result.get('server'):
            lines.append(f"🌍 Servidor: {result['server']}")
        if result.get('timestamp'):
            from datetime import datetime
            dt = datetime.fromtimestamp(result['timestamp'])
            lines.append(f"🕒 {dt.strftime('%d/%m/%Y %H:%M:%S')}")
        return "\n".join(lines)

if __name__ == "__main__":
    tester = SpeedTester()
    print("Iniciando teste de velocidade...")
    tester.run_test(callback=lambda res: print(tester.format_result(res)))
    time.sleep(60)
