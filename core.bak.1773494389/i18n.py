#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internationalization (i18n) module for SpeedScan.
Handles loading of translations using gettext.
Version 1.0.0
"""
import gettext
from pathlib import Path

from core import config

# Directory where locale files are stored (parent of core/ is the project root)
LOCALE_DIR = Path(__file__).parent.parent / "locale"


def get_translation(language=None):
    """
    Return a gettext translation function for the specified language.

    Args:
        language (str): Language code (e.g., "pt_BR", "en_US", "es_ES").
                        If None, loads from configuration.

    Returns:
        function: A gettext function that translates strings.
    """
    if language is None:
        # Attempt to load language from config
        try:
            # config.load_config() should return the configuration dictionary
            cfg = config.load_config()
            language = cfg.get("language", "pt_BR")
        except Exception:
            language = "pt_BR"  # fallback to Portuguese

    try:
        translation = gettext.translation(
            "speedscan",
            localedir=str(LOCALE_DIR),
            languages=[language]
        )
        return translation.gettext
    except FileNotFoundError:
        # Fallback to the identity function (no translation)
        return gettext.gettext


# Global translation function (default to Portuguese)
_ = get_translation("pt_BR")
