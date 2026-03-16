import gettext
import os
from pathlib import Path
from core import config

LOCALE_DIR = Path(__file__).parent.parent / 'locale'

def get_translation(language=None):
    if language is None:
        language = config.load_config().get('language', 'pt_BR')
    try:
        translation = gettext.translation(
            'speedscan',
            localedir=str(LOCALE_DIR),
            languages=[language]
        )
        return translation.gettext
    except FileNotFoundError:
        return gettext.gettext

_ = get_translation('pt_BR')
