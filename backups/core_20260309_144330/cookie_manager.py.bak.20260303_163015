#!/usr/bin/env python3
# core/cookie_manager.py
# =============================================================================
#   ███████╗██████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ █████╗ ███╗   ██╗
#   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║
#   ███████╗██████╔╝█████╗  █████╗  ██║  ██║█████╗  ██║     ███████║██╔██╗ ██║
#   ╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║  ██║██╔══╝  ██║     ██╔══██║██║╚██╗██║
#   ███████║██║     ███████╗███████╗██████╔╝███████╗╚██████╗██║  ██║██║ ╚████║
#   ╚══════╝╚═╝     ╚══════╝╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
# =============================================================================
# Gerenciador de cookies para navegadores
# Versão 0.3.0-beta
# =============================================================================

import sqlite3
import json
from pathlib import Path
import shutil

class CookieManager:
    def __init__(self):
        self.cookie_files = {
            'chrome': Path.home() / '.config/google-chrome/Default/Cookies',
            'chromium': Path.home() / '.config/chromium/Default/Cookies',
            'firefox': Path.home() / '.mozilla/firefox/*.default-release/cookies.sqlite',
            'brave': Path.home() / '.config/Brave-Browser/Default/Cookies',
            'edge': Path.home() / '.config/microsoft-edge/Default/Cookies',
            'opera': Path.home() / '.config/opera/Default/Cookies',
            'chromium-flatpak': Path.home() / '.var/app/org.chromium.Chromium/config/chromium/Default/Cookies',
            'firefox-flatpak': Path.home() / '.var/app/org.mozilla.firefox/.mozilla/firefox/*.default-release/cookies.sqlite',
        }

    def get_cookies_from_browser(self, browser_key):
        """Retorna lista de cookies (host, name, value) de um navegador."""
        path = self.cookie_files.get(browser_key)
        if not path:
            return []
        # Expande wildcards
        if '*' in str(path):
            paths = list(Path(str(path).replace('*', '')).parent.glob('*.default-release'))
            if not paths:
                return []
            path = paths[0] / 'cookies.sqlite'
        if not path.exists():
            return []
        cookies = []
        try:
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()
            # Tabela de cookies pode variar; para Chrome é 'cookies'
            cursor.execute("SELECT host_key, name, value FROM cookies")
            rows = cursor.fetchall()
            for row in rows:
                cookies.append({'host': row[0], 'name': row[1], 'value': row[2]})
            conn.close()
        except Exception as e:
            print(f"Erro ao ler cookies de {browser_key}: {e}")
        return cookies

    def get_cookie_summary(self):
        """Retorna um dicionário com contagem de cookies por domínio."""
        summary = {}
        for browser in self.cookie_files:
            cookies = self.get_cookies_from_browser(browser)
            for c in cookies:
                host = c['host']
                summary[host] = summary.get(host, 0) + 1
        return summary

    def backup_cookies(self, browser_key, backup_path):
        """Faz backup do arquivo de cookies."""
        src = self.cookie_files.get(browser_key)
        if not src or not src.exists():
            return False
        shutil.copy2(src, backup_path)
        return True

    def restore_cookies(self, backup_path, browser_key):
        """Restaura cookies a partir de um backup."""
        dest = self.cookie_files.get(browser_key)
        if not dest:
            return False
        shutil.copy2(backup_path, dest)
        return True

    def delete_cookies_except(self, browser_key, keep_domains):
        """Remove todos os cookies exceto os de domínios em keep_domains."""
        path = self.cookie_files.get(browser_key)
        if not path:
            return False
        if '*' in str(path):
            paths = list(Path(str(path).replace('*', '')).parent.glob('*.default-release'))
            if not paths:
                return False
            path = paths[0] / 'cookies.sqlite'
        if not path.exists():
            return False
        try:
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()
            # Obtém todos os cookies
            cursor.execute("SELECT host_key, name FROM cookies")
            all_cookies = cursor.fetchall()
            # Constrói lista de parâmetros para DELETE
            for host, name in all_cookies:
                if host not in keep_domains:
                    cursor.execute("DELETE FROM cookies WHERE host_key=? AND name=?", (host, name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao deletar cookies: {e}")
            return False
