#!/usr/bin/env python3
import sys
from pathlib import Path

# Adiciona o diretório atual ao path para que 'core' seja encontrado
sys.path.insert(0, str(Path.cwd()))

modulos = [
    'core.config',
    'core.i18n',
    'core.hardware',
    'core.actions',
    'core.scheduler',
    'core.health_score',
    'core.temperature_monitor',
    'core.smart_monitor',
    'core.browser_cleaner',
    'core.speed_test',
    'core.process_manager',
    'core.historical_metrics',
    'core.lan_scanner',
    'core.ai_proactive',
    'core.security_scanner',
    'core.dashboard',
    'core.lan_cache',
    'core.chat',
    'core.first_run',
    'core.cookie_manager',
    'core.trash_manager',
    'core.ui',
    'core.windows_cleaner',
    'core.main'
]

print("Testando importações dos módulos core:")
print("-" * 40)
for modulo in modulos:
    try:
        __import__(modulo)
        print(f"✅ {modulo} importado com sucesso")
    except Exception as e:
        print(f"❌ {modulo} falhou: {e}")
        break  # Para no primeiro erro
print("-" * 40)
