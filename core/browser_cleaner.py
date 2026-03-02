#!/usr/bin/env python3
# core/browser_cleaner.py
# =============================================================================
#   ███████╗██████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ █████╗ ███╗   ██╗
#   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║
#   ███████╗██████╔╝█████╗  █████╗  ██║  ██║█████╗  ██║     ███████║██╔██╗ ██║
#   ╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║  ██║██╔══╝  ██║     ██╔══██║██║╚██╗██║
#   ███████║██║     ███████╗███████╗██████╔╝███████╗╚██████╗██║  ██║██║ ╚████║
#   ╚══════╝╚═╝     ╚══════╝╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
# =============================================================================
# Módulo de limpeza de navegadores (cache, cookies, histórico)
# Versão 0.0.9-beta
# =============================================================================

import os
import shutil
from pathlib import Path

class BrowserCleaner:
    def __init__(self):
        self.browsers = {
            'chrome': {
                'name': 'Google Chrome',
                'cache': Path.home() / '.cache/google-chrome',
                'cookies': Path.home() / '.config/google-chrome/Local State',
                'history': Path.home() / '.config/google-chrome/Default/History'
            },
            'firefox': {
                'name': 'Firefox',
                'cache': Path.home() / '.cache/mozilla/firefox',
                'cookies': Path.home() / '.mozilla/firefox/*.default-release/cookies.sqlite',
                'history': Path.home() / '.mozilla/firefox/*.default-release/places.sqlite'
            },
            'edge': {
                'name': 'Microsoft Edge',
                'cache': Path.home() / '.cache/microsoft-edge',
                'cookies': Path.home() / '.config/microsoft-edge/Local State',
                'history': Path.home() / '.config/microsoft-edge/Default/History'
            },
            'brave': {
                'name': 'Brave',
                'cache': Path.home() / '.cache/Brave-Browser',
                'cookies': Path.home() / '.config/Brave-Browser/Local State',
                'history': Path.home() / '.config/Brave-Browser/Default/History'
            },
            'opera': {
                'name': 'Opera',
                'cache': Path.home() / '.cache/opera',
                'cookies': Path.home() / '.config/opera/Local State',
                'history': Path.home() / '.config/opera/Default/History'
            }
        }

    def format_bytes(self, bytes):
        """Formata bytes para unidade legível."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"

    def get_size(self, path):
        """Calcula o tamanho de um arquivo ou diretório."""
        try:
            if path.is_file():
                return path.stat().st_size
            elif path.is_dir():
                total = 0
                for root, dirs, files in os.walk(path):
                    for f in files:
                        fp = Path(root) / f
                        total += fp.stat().st_size
                return total
        except:
            return 0
        return 0

    def clean_browser(self, browser_key):
        """Limpa cache, cookies e histórico de um navegador específico."""
        browser = self.browsers.get(browser_key)
        if not browser:
            return None
        result = {
            'name': browser['name'],
            'cache_freed': 0,
            'cookies_freed': 0,
            'history_freed': 0,
            'errors': []
        }
        # Cache
        cache_path = browser['cache']
        if cache_path.exists():
            size = self.get_size(cache_path)
            try:
                if cache_path.is_dir():
                    shutil.rmtree(cache_path)
                else:
                    cache_path.unlink()
                result['cache_freed'] = size
            except Exception as e:
                result['errors'].append(f"cache: {e}")
        # Cookies (simplificado - pode ser mais complexo)
        # Para Chrome/Edge/Brave, o arquivo de cookies é um banco SQLite, remover pode causar problemas.
        # Por simplicidade, não removemos cookies, apenas cache.
        # Histórico (também SQLite, não removemos)
        return result

    def clean_all_browsers(self):
        """Limpa todos os navegadores suportados."""
        results = {}
        for key in self.browsers:
            results[key] = self.clean_browser(key)
        return results
