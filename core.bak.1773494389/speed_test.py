#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internet speed test module.
Version 1.0.0
"""
import logging
import subprocess
import sys
import time
import threading
import os

try:
    import speedtest
except ImportError:
    logging.error("Installing speedtest-cli...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "speedtest-cli"])
    import speedtest

from core import config


class SpeedTester:
    """
    Performs internet speed tests using speedtest-cli or a fallback method.
    """
    def __init__(self, use_fallback=False):
        """
        Initialize the speed tester.

        Args:
            use_fallback (bool): If True, always use the fallback method (using requests).
                                 Otherwise, try speedtest-cli first, and fall back on failure.
        """
        self.use_fallback = use_fallback
        self.result = {
            "ping": None,
            "download": None,
            "upload": None,
            "server": None,
            "timestamp": None,
            "error": None
        }

    def test_with_speedtest(self) -> bool:
        """
        Run the speed test using the speedtest-cli library.

        Returns:
            bool: True on success, False on error.
        """
        try:
            st = speedtest.Speedtest(secure=True)
            st.get_best_server()
            self.result["ping"] = round(st.results.ping, 1)
            self.result["server"] = f"{st.results.server['name']} ({st.results.server['country']})"
            download_bps = st.download()
            self.result["download"] = round(download_bps / 1_000_000, 2)
            upload_bps = st.upload()
            self.result["upload"] = round(upload_bps / 1_000_000, 2)
            self.result["timestamp"] = time.time()
            return True
        except Exception as e:
            logging.error(f"Error in test_with_speedtest: {e}")
            self.result["error"] = str(e)
            return False

    def test_fallback(self) -> bool:
        """
        Run a manual speed test using requests (download/upload to google/httpbin).

        Returns:
            bool: True on success, False on error.
        """
        import requests
        import tempfile
        try:
            start = time.time()
            requests.get("https://www.google.com", timeout=5)
            ping = (time.time() - start) * 1000
            self.result["ping"] = round(ping, 1)

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
                self.result["download"] = round(download_mbps, 2)

            data = os.urandom(5 * 1024 * 1024)  # 5 MB
            start = time.time()
            requests.post("https://httpbin.org/post", data=data, timeout=30)
            elapsed = time.time() - start
            upload_mbps = (len(data) * 8) / elapsed / 1_000_000
            self.result["upload"] = round(upload_mbps, 2)

            self.result["server"] = "Fallback (public servers)"
            self.result["timestamp"] = time.time()
            return True
        except Exception as e:
            logging.error(f"Error in test_fallback: {e}")
            self.result["error"] = str(e)
            return False

    def run_test(self, callback=None):
        """
        Run the speed test in a separate thread.

        Args:
            callback (callable): Optional function that will be called with the result dict after the test.

        Returns:
            threading.Thread: The thread object (daemon).
        """
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

    def format_result(self, result=None) -> str:
        """
        Format the speed test result as a readable string.

        Args:
            result (dict): The result dictionary (if None, uses self.result).

        Returns:
            str: A formatted string with the results.
        """
        if result is None:
            result = self.result
        if result.get("error"):
            return f"❌ Error: {result['error']}"
        lines = []
        if result.get("ping") is not None:
            lines.append(f"📶 Ping: {result['ping']} ms")
        if result.get("download") is not None:
            lines.append(f"⬇️ Download: {result['download']} Mbps")
        if result.get("upload") is not None:
            lines.append(f"⬆️ Upload: {result['upload']} Mbps")
        if result.get("server"):
            lines.append(f"🖥️ Server: {result['server']}")
        if result.get("timestamp"):
            from datetime import datetime
            dt = datetime.fromtimestamp(result["timestamp"])
            lines.append(f"🕒 {dt.strftime('%d/%m/%Y %H:%M:%S')}")
        return "\n".join(lines)
