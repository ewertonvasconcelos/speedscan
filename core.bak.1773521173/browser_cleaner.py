#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser cleaner module - cleans cache, cookies, and history from major browsers.
Version 1.0.0
"""
import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional

class BrowserCleaner:
    def __init__(self):
        self.browsers = {
            "chrome": {
                "name": "Google Chrome",
                "cache_paths": [
                    Path.home() / ".cache/google-chrome",
                    Path.home() / ".config/google-chrome/Default/Cache"
                ],
                "cookies_path": Path.home() / ".config/google-chrome/Default/Cookies",
                "history_path": Path.home() / ".config/google-chrome/Default/History"
            },
            "chromium": {
                "name": "Chromium",
                "cache_paths": [
                    Path.home() / ".cache/chromium",
                    Path.home() / ".config/chromium/Default/Cache"
                ],
                "cookies_path": Path.home() / ".config/chromium/Default/Cookies",
                "history_path": Path.home() / ".config/chromium/Default/History"
            },
            "firefox": {
                "name": "Firefox",
                "profile_pattern": Path.home() / ".mozilla/firefox/*.default-release",
                "cache_subdir": "cache2",
                "cookies_file": "cookies.sqlite",
                "places_file": "places.sqlite"
            },
            "brave": {
                "name": "Brave",
                "cache_paths": [
                    Path.home() / ".cache/Brave-Browser",
                    Path.home() / ".config/Brave-Browser/Default/Cache"
                ],
                "cookies_path": Path.home() / ".config/Brave-Browser/Default/Cookies",
                "history_path": Path.home() / ".config/Brave-Browser/Default/History"
            }
        }
    def clean_browser(self, browser_key: str, preserve_cookies: bool = False,
                      cookie_keep_list: Optional[List[str]] = None) -> Dict:
        result = {"cache_freed": 0, "cookies_freed": 0, "history_freed": 0, "errors": []}
        browser = self.browsers.get(browser_key)
        if not browser:
            return result
        if "cache_paths" in browser:
            for path in browser["cache_paths"]:
                if path.exists():
                    try:
                        size = self._get_size(path)
                        shutil.rmtree(path)
                        result["cache_freed"] += size
                    except Exception as e:
                        result["errors"].append(f"Cache: {e}")
        elif browser_key == "firefox":
            profiles = list(Path.home().glob(".mozilla/firefox/*.default-release"))
            if profiles:
                profile = profiles[0]
                cache_dir = profile / browser["cache_subdir"]
                if cache_dir.exists():
                    try:
                        size = self._get_size(cache_dir)
                        shutil.rmtree(cache_dir)
                        result["cache_freed"] += size
                    except Exception as e:
                        result["errors"].append(f"Cache: {e}")
        if not preserve_cookies:
            if "cookies_path" in browser:
                path = browser["cookies_path"]
                if path.exists():
                    try:
                        size = path.stat().st_size
                        path.unlink()
                        result["cookies_freed"] += size
                    except Exception as e:
                        result["errors"].append(f"Cookies: {e}")
            elif browser_key == "firefox":
                profiles = list(Path.home().glob(".mozilla/firefox/*.default-release"))
                if profiles:
                    profile = profiles[0]
                    cookies_file = profile / browser["cookies_file"]
                    if cookies_file.exists():
                        try:
                            size = cookies_file.stat().st_size
                            cookies_file.unlink()
                            result["cookies_freed"] += size
                        except Exception as e:
                            result["errors"].append(f"Cookies: {e}")
        if "history_path" in browser:
            path = browser["history_path"]
            if path.exists():
                try:
                    size = path.stat().st_size
                    path.unlink()
                    result["history_freed"] += size
                except Exception as e:
                    result["errors"].append(f"History: {e}")
        elif browser_key == "firefox":
            profiles = list(Path.home().glob(".mozilla/firefox/*.default-release"))
            if profiles:
                profile = profiles[0]
                places_file = profile / browser["places_file"]
                if places_file.exists():
                    try:
                        size = places_file.stat().st_size
                        places_file.unlink()
                        result["history_freed"] += size
                    except Exception as e:
                        result["errors"].append(f"History: {e}")
        return result
    def clean_all_browsers(self, preserve_cookies: bool = False,
                           cookie_keep_list: Optional[List[str]] = None) -> Dict:
        results = {}
        for key in self.browsers:
            results[key] = self.clean_browser(key, preserve_cookies, cookie_keep_list)
            results[key]["name"] = self.browsers[key]["name"]
        return results
    def _get_size(self, path: Path) -> int:
        total = 0
        try:
            for entry in path.iterdir():
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self._get_size(entry)
        except:
            pass
        return total
    @staticmethod
    def format_bytes(num_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if num_bytes < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} TB"
