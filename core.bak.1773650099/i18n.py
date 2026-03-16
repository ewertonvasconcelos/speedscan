#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internationalization (i18n) module for SpeedScan.
Version 1.0.0
"""
import gettext
import json
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"
CONFIG_FILE = Path.home() / ".speedscan_config"

def get_translation(language=None):
    if language is None:
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                language = cfg.get("language", "pt_BR")
        except:
            language = "pt_BR"
    try:
        translation = gettext.translation(
            "speedscan",
            localedir=str(LOCALE_DIR),
            languages=[language]
        )
        return translation.gettext
    except FileNotFoundError:
        return gettext.gettext

_ = get_translation("pt_BR")
