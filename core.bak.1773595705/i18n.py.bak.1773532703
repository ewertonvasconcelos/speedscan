#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internationalization (i18n) module for SpeedScan.
Version 1.0.0
"""
import gettext
from pathlib import Path
from core import config

LOCALE_DIR = Path(__file__).parent.parent / "locale"

def get_translation(language=None):
    if language is None:
        try:
            cfg = config.load_config()
            language = cfg.get("language", "pt_BR")
        except Exception:
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
