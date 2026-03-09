#!/usr/bin/env python3
# core/config.py
# Arquivo centralizado de configurações do SpeedScan
# Gerado automaticamente – não edite manualmente (altere os scripts correspondentes)

import os
from pathlib import Path

# =============================================================================
# Versão do aplicativo
# =============================================================================
VERSION = "1.0.0"

# =============================================================================
# Caminhos de diretórios e arquivos
# =============================================================================
CONFIG_FILE = Path.home() / ".speedscan_conf"
ICON_PATH = Path.home() / "speedscan" / "assets" / "icon.png"
LOG_DIR = Path.home() / "speedscan" / "logs"
AGENT_SCRIPT = Path.home() / "speedscan" / "speedscan-agent.py"

# =============================================================================
# Configuração padrão
# =============================================================================
DEFAULT_CONFIG = {
    "theme": "default",
    "username": "ewerton",
    "language": "pt_BR",
    "ui_scale": "auto",
    "open_file_in_tab": False,
    "simple_mode": True,
    "expert_level": 1,
    "window_state": {
        "maximized": False,
        "width": 1000,
        "height": 700,
        "x": None,
        "y": None
    },
    "schedule": {
        "enabled": False,
        "frequency": "weekly",
        "hour": "03:00",
        "day_of_week": "monday",
        "day_of_month": 1,
        "interval_days": 7,
        "tasks": ["cache", "swap", "check"],
        "elevated": False
    },
    "ai": {
        "provider": "ollama",
        "model": "llama3.2",
        "api_key": "",
        "endpoint": "http://localhost:11434"
    }
}

# =============================================================================
# Temas
# =============================================================================
THEMES = {
    "default": {"mode": "dark", "bg": "#1e293b", "side": "#0f172a", "acc": "#a855f7", "text": "#ffffff"},
    "grey":    {"mode": "light", "bg": "#d1d5db", "side": "#374151", "acc": "#4b5563", "text": "#111827"},
    "dark":    {"mode": "dark", "bg": "#080808", "side": "#000000", "acc": "#10b981", "text": "#ffffff"},
    "light":   {"mode": "light", "bg": "#ffffff", "side": "#f8fafc", "acc": "#2563eb", "text": "#0f172a"}
}

# =============================================================================
# Idiomas suportados
# =============================================================================
LANGUAGES = {
    "pt_BR": "Português Brasileiro",
    "en_US": "English (US)",
    "es_ES": "Español"
}

# =============================================================================
# Escalas de interface
# =============================================================================
SCALES = {
    "auto": "Automático",
    "100": "100%",
    "125": "125%",
    "150": "150%"
}

# =============================================================================
# Lista de sugestões de IA
# =============================================================================
AI_SUGGESTIONS = [
    "Ollama (local)", "OpenAI GPT", "Google Gemini", "Claude (Anthropic)",
    "Llama 3 (Meta)", "Mistral AI", "Cohere", "DeepSeek", "Configurar IA Local"
]
