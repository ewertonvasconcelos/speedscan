#!/usr/bin/env python3
"""Sistema de internacionalização simples"""
import json
from pathlib import Path

TRANSLATIONS = {}

def load_locale(locale='en'):
    global TRANSLATIONS
    locales_dir = Path(__file__).parent.parent.parent / 'i18n' / 'locales'
    file_path = locales_dir / f'{locale}.json'
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            TRANSLATIONS = json.load(f)
    else:
        fallback_file = locales_dir / 'en.json'
        if fallback_file.exists():
            with open(fallback_file, 'r', encoding='utf-8') as f:
                TRANSLATIONS = json.load(f)

def _(key, default=None):
    """Traduz uma chave"""
    global TRANSLATIONS
    if not TRANSLATIONS:
        load_locale('en')
    return TRANSLATIONS.get(key, default or key)

# Cargas padrão no carregamento inicial
load_locale('en')
