#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser cleaning module - cache, cookies, and history supporting Flatpak/Snap.
Version 1.0.0
"""

import os
import shutil
import logging
from pathlib import Path

from core import config


class BrowserCleaner:
    """Cleans browser caches, cookies and history for supported browsers."""

    def __init__(self):
        """Initialize the browser cleaner with predefined paths."""
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
            },
            'chromium-flatpak': {
                'name': 'Chromium (Flatpak)',
                'cache': Path.home() / '.var/app/org.chromium.Chromium/cache',
                'cookies': Path.home() / '.var/app/org.chromium.Chromium/config/chromium/Local State',
                'history': Path.home() / '.var/app/org.chromium.Chromium/config/chromium/Default/History'
            },
            'firefox-flatpak': {
                'name': 'Firefox (Flatpak)',
                'cache': Path.home() / '.var/app/org.mozilla.firefox/cache/mozilla/firefox',
                'cookies': Path.home() / '.var/app/org.mozilla.firefox/.mozilla/firefox/*.default-release/cookies.sqlite',
                'history': Path.home() / '.var/app/org.mozilla.firefox/.mozilla/firefox/*.default-release/places.sqlite'
            },
            'chromium-snap': {
                'name': 'Chromium (Snap)',
                'cache': Path.home() / 'snap/chromium/current/.cache/chromium',
                'cookies': Path.home() / 'snap/chromium/current/.config/chromium/Local State',
                'history': Path.home() / 'snap/chromium/current/.config/chromium/Default/History'
            }
        }

    def format_bytes(self, bytes):
        """Format a byte count into human-readable units (B/, KB,/MB,/GB, TB)."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"

    def get_size(self, path):
        """Calculate the total size of a file or directory (including subdirectories)."""
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
            return 0
        except Exception as e:
            logging.error(f"Error calculating size for {path}: {e}")
            return 0

    def clean_browser(self, browser_key, preserve_cookies=False, cookie_keep_list=None):
        """Clean a specific browser's cache, cookies and history.

        Args:
            browser_key (str): The key identifying the browser in self.browsers.
            preserve_cookies (bool): If True, cookies are not cleaned. (Not fully implemented).
            cookie_keep_list (list): List of cookie names to keep. (Not implemented).

        Returns:
            dict: A dictionary with 'name', 'cache_freed', 'cookies_freed', 'history_freed', 'errors'.
        """
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
        # TODO: implement cookies and history cleaning
        return result

    def clean_all_browsers(self, preserve_cookies=False, cookie_keep_list=None):
        """Clean all supported browsers and return a dictionary of results."""
        results = {}
        for key in self.browsers:
            results[key] = self.clean_browser(key, preserve_cookies, cookie_keep_list)
        return results
