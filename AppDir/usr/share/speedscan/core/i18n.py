import gettext
import os
from pathlib import Path
from core import config

# Diretório onde ficarão as traduções
LOCALE_DIR = Path(__file__).parent.parent / 'locale'

def get_translation(language=None):
    """Retorna a função de tradução para o idioma especificado."""
    if language is None:
        language = config.load_config().get('language', 'pt_BR')
    try:
        # Tenta carregar a tradução para o idioma
        translation = gettext.translation(
            'speedscan',
            localedir=str(LOCALE_DIR),
            languages=[language]
        )
        return translation.gettext
    except FileNotFoundError:
        # Fallback para inglês se o idioma não for encontrado
        return gettext.gettext

# Função global de tradução (será sobrescrita no início da aplicação)
_ = get_translation('pt_BR')
