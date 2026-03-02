#!/usr/bin/env python3
# core/browser_cleaner.py

import os
import shutil
import platform
from pathlib import Path
import glob
import time

class BrowserCleaner:
    """
    Limpa cache, cookies e histório dos principais navegadores.
    Suporta: Chrome, Chromium, Edge, Brave, Firefox, Opera.
    """

    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()

    def clean_all_browsers(self) -> dict:
        """Executa limpeza em todos os navegadores suportados e retorna relatório."""
        results = {}
        results['chrome'] = self._clean_chrome()
        results['chromium'] = self._clean_chromium()
        results['edge'] = self._clean_edge()
        results['brave'] = self._clean_brave()
        results['firefox'] = self._clean_firefox()
        results['opera'] = self._clean_opera()
        return results

    def _clean_chrome(self) -> dict:
        paths = self._get_chrome_paths()
        return self._clean_browser_paths(paths, "Google Chrome")

    def _clean_chromium(self) -> dict:
        paths = self._get_chromium_paths()
        return self._clean_browser_paths(paths, "Chromium")

    def _clean_edge(self) -> dict:
        paths = self._get_edge_paths()
        return self._clean_browser_paths(paths, "Microsoft Edge")

    def _clean_brave(self) -> dict:
        paths = self._get_brave_paths()
        return self._clean_browser_paths(paths, "Brave")

    def _clean_firefox(self) -> dict:
        paths = self._get_firefox_paths()
        return self._clean_browser_paths(paths, "Firefox")

    def _clean_opera(self) -> dict:
        paths = self._get_opera_paths()
        return self._clean_browser_paths(paths, "Opera")

    def _get_chrome_paths(self):
        if self.system == 'Windows':
            base = os.environ.get('LOCALAPPDATA', '') + r'\Google\Chrome\User Data\Default'
            return {
                'cache': [os.path.join(base, 'Cache'), os.path.join(base, 'Code Cache')],
                'cookies': [os.path.join(base, 'Cookies')],
                'history': [os.path.join(base, 'History')]
            }
        elif self.system == 'Linux':
            base = self.home / '.config/google-chrome/Default'
            return {
                'cache': [base / 'Cache', base / 'Code Cache'],
                'cookies': [base / 'Cookies'],
                'history': [base / 'History']
            }
        elif self.system == 'Darwin':
            base = self.home / 'Library/Application Support/Google/Chrome/Default'
            return {
                'cache': [base / 'Cache', base / 'Code Cache'],
                'cookies': [base / 'Cookies'],
                'history': [base / 'History']
            }
        return {}

    def _get_chromium_paths(self):
        if self.system == 'Linux':
            base = self.home / '.config/chromium/Default'
            return {
                'cache': [base / 'Cache', base / 'Code Cache'],
                'cookies': [base / 'Cookies'],
                'history': [base / 'History']
            }
        return {}

    def _get_edge_paths(self):
        if self.system == 'Linux':
            base = self.home / '.config/microsoft-edge/Default'
            return {
                'cache': [base / 'Cache', base / 'Code Cache'],
                'cookies': [base / 'Cookies'],
                'history': [base / 'History']
            }
        return {}

    def _get_brave_paths(self):
        if self.system == 'Linux':
            base = self.home / '.config/BraveSoftware/Brave-Browser/Default'
            return {
                'cache': [base / 'Cache', base / 'Code Cache'],
                'cookies': [base / 'Cookies'],
                'history': [base / 'History']
            }
        return {}

    def _get_firefox_paths(self):
        if self.system == 'Linux':
            profiles = self.home / '.mozilla/firefox'
            for path in profiles.glob('*.default*'):
                return {
                    'cache': [path / 'cache2'],
                    'cookies': [path / 'cookies.sqlite'],
                    'history': [path / 'places.sqlite']
                }
        return {}

    def _get_opera_paths(self):
        if self.system == 'Linux':
            base = self.home / '.config/opera'
            return {
                'cache': [base / 'Cache'],
                'cookies': [base / 'Cookies'],
                'history': [base / 'History']
            }
        return {}

    def _clean_browser_paths(self, paths, name):
        result = {
            'name': name,
            'cache_freed': 0,
            'cookies_freed': 0,
            'history_freed': 0,
            'errors': []
        }
        for category, path_list in paths.items():
            for path in path_list:
                if os.path.exists(path):
                    try:
                        if os.path.isfile(path):
                            size = os.path.getsize(path)
                            os.remove(path)
                            if category == 'cache':
                                result['cache_freed'] += size
                            elif category == 'cookies':
                                result['cookies_freed'] += size
                            elif category == 'history':
                                result['history_freed'] += size
                        elif os.path.isdir(path):
                            size = sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())
                            shutil.rmtree(path)
                            if category == 'cache':
                                result['cache_freed'] += size
                    except Exception as e:
                        result['errors'].append(str(e))
        return result

    def format_bytes(self, bytes):
        """Formata bytes para KB, MB, GB."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"
