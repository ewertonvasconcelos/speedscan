#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser cleaner module - cleans cache, cookies, and history from multiple browsers.
Version 1.0.0
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional

from core import config


class BrowserCleaner:
    """Cleans browser data (cache, cookies, history) for multiple browsers."""

    def __init__(self):
        self.browsers = {
            'chrome': {
                'name': 'Google Chrome',
                'cache': Path.home() / '.cache/google-chrome',
                'cookies': Path.home() / '.config/google-chrome/Default/Cookies',
                'history': Path.home() / '.config/google-chrome/Default/History',
            },
            'chromium': {
                'name': 'Chromium',
                'cache': Path.home() / '.cache/chromium',
                'cookies': Path.home() / '.config/chromium/Default/Cookies',
                'history': Path.home() / '.config/chromium/Default/History',
            },
            'firefox': {
                'name': 'Firefox',
                'profile_dir': Path.home() / '.mozilla/firefox',
            },
            'brave': {
                'name': 'Brave',
                'cache': Path.home() / '.cache/Brave-Browser',
                'cookies': Path.home() / '.config/Brave-Browser/Default/Cookies',
                'history': Path.home() / '.config/Brave-Browser/Default/History',
            },
            'edge': {
                'name': 'Microsoft Edge',
                'cache': Path.home() / '.cache/microsoft-edge',
                'cookies': Path.home() / '.config/microsoft-edge/Default/Cookies',
                'history': Path.home() / '.config/microsoft-edge/Default/History',
            },
            'opera': {
                'name': 'Opera',
                'cache': Path.home() / '.cache/opera',
                'cookies': Path.home() / '.config/opera/Default/Cookies',
                'history': Path.home() / '.config/opera/Default/History',
            },
            'vivaldi': {
                'name': 'Vivaldi',
                'cache': Path.home() / '.cache/vivaldi',
                'cookies': Path.home() / '.config/vivaldi/Default/Cookies',
                'history': Path.home() / '.config/vivaldi/Default/History',
            },
        }

    def format_bytes(self, size_bytes):
        """Convert bytes to human readable format."""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names)-1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"

    def get_firefox_profiles(self):
        """Find all Firefox profiles."""
        profiles = []
        profiles_ini = self.browsers['firefox']['profile_dir'] / 'profiles.ini'
        if not profiles_ini.exists():
            return profiles
        with open(profiles_ini) as f:
            lines = f.readlines()
        current_profile = None
        for line in lines:
            if line.startswith('['):
                current_profile = {}
            elif line.startswith('Path='):
                if current_profile is not None:
                    current_profile['path'] = line.split('=')[1].strip()
            elif line.startswith('Default=') and '1' in line:
                if current_profile is not None and 'path' in current_profile:
                    profiles.append(current_profile['path'])
        return profiles

    def clean_firefox(self, profile_path, preserve_cookies=False, cookie_keep_list=None):
        """Clean a single Firefox profile."""
        profile_dir = self.browsers['firefox']['profile_dir'] / profile_path
        freed = {'cache': 0, 'cookies': 0, 'history': 0}
        errors = []

        # Cache
        cache_dir = profile_dir / 'cache2'
        if cache_dir.exists():
            try:
                size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                shutil.rmtree(cache_dir)
                freed['cache'] = size
            except Exception as e:
                errors.append(f"Cache: {e}")

        # Cookies (places.sqlite)
        cookies_db = profile_dir / 'cookies.sqlite'
        if cookies_db.exists():
            try:
                size = cookies_db.stat().st_size
                if preserve_cookies and cookie_keep_list:
                    # Placeholder: implement selective deletion
                    pass
                else:
                    cookies_db.unlink()
                freed['cookies'] = size
            except Exception as e:
                errors.append(f"Cookies: {e}")

        # History (places.sqlite)
        places_db = profile_dir / 'places.sqlite'
        if places_db.exists():
            try:
                size = places_db.stat().st_size
                places_db.unlink()
                freed['history'] = size
            except Exception as e:
                errors.append(f"History: {e}")

        return freed, errors

    def clean_browser(self, browser_key, preserve_cookies=False, cookie_keep_list=None):
        """Clean a single browser by key."""
        browser = self.browsers.get(browser_key)
        if not browser:
            return None

        freed = {'cache': 0, 'cookies': 0, 'history': 0}
        errors = []

        if browser_key == 'firefox':
            profiles = self.get_firefox_profiles()
            for profile in profiles:
                f, e = self.clean_firefox(profile, preserve_cookies, cookie_keep_list)
                for k in freed:
                    freed[k] += f[k]
                errors.extend(e)
        else:
            # Chromium-based browsers
            if 'cache' in browser and browser['cache'].exists():
                try:
                    size = sum(f.stat().st_size for f in browser['cache'].rglob('*') if f.is_file())
                    shutil.rmtree(browser['cache'])
                    freed['cache'] = size
                except Exception as e:
                    errors.append(f"Cache: {e}")

            if 'cookies' in browser and browser['cookies'].exists():
                try:
                    size = browser['cookies'].stat().st_size
                    if preserve_cookies and cookie_keep_list:
                        # Placeholder
                        pass
                    else:
                        browser['cookies'].unlink()
                    freed['cookies'] = size
                except Exception as e:
                    errors.append(f"Cookies: {e}")

            if 'history' in browser and browser['history'].exists():
                try:
                    size = browser['history'].stat().st_size
                    browser['history'].unlink()
                    freed['history'] = size
                except Exception as e:
                    errors.append(f"History: {e}")

        return freed, errors

    def clean_all_browsers(self, preserve_cookies=False, cookie_keep_list=None):
        """Clean all known browsers."""
        results = {}
        for key in self.browsers:
            result = self.clean_browser(key, preserve_cookies, cookie_keep_list)
            if result:
                freed, errors = result
                results[key] = {
                    'name': self.browsers[key]['name'],
                    'cache_freed': freed['cache'],
                    'cookies_freed': freed['cookies'],
                    'history_freed': freed['history'],
                    'errors': errors
                }
        return results
