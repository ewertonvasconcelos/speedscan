#!/usr/bin/env python3
"""
Ajusta os temas do SpeedScan:
- Remove o tema "default" (Padrão)
- Mantém apenas: grey (Cinza Profissional), dark (Escuro Total), light (Claro Clean)
- Renomeia: "Cinza Profissional (Default)", "Tecno", "Claro Clean"
- Corrige a indentação e a lógica na aba Configurações
- Faz backup automático do arquivo main.py
"""

import shutil
import re
from pathlib import Path
from datetime import datetime

MAIN_FILE = Path("core/main.py")
BACKUP_DIR = Path("backups")

# Novo dicionário THEMES (com indentação de 4 espaços)
NOVO_THEMES = '''THEMES = {
    "grey":    {"mode": "light", "bg": "#d1d5db", "side": "#374151", "acc": "#4b5563", "text": "#111827"},
    "dark":    {"mode": "dark",  "bg": "#080808", "side": "#000000", "acc": "#10b981", "text": "#ffffff"},
    "light":   {"mode": "light", "bg": "#ffffff", "side": "#f8fafc", "acc": "#2563eb", "text": "#0f172a"}
}'''

# Novo trecho para a parte de temas em _fill_config
NOVO_FILL_CONFIG_THEMES = '''        f_theme = ctk.CTkFrame(parent, fg_color="transparent")
        f_theme.pack(fill="x", pady=10)
        ctk.CTkLabel(f_theme, text="Tema da interface *", font=("Inter",14), text_color=self.text_color).pack(anchor="w")
        theme_names = ["Cinza Profissional (Default)", "Tecno", "Claro Clean"]
        current_theme = self.config.get("theme", "grey")
        # Se ainda houver "default" no config, converte para "grey"
        if current_theme == "default":
            current_theme = "grey"
        theme_keys = ["grey", "dark", "light"]
        theme_index = theme_keys.index(current_theme) if current_theme in theme_keys else 0
        self.theme_name_var = ctk.StringVar(value=theme_names[theme_index])
        ctk.CTkOptionMenu(f_theme, values=theme_names, variable=self.theme_name_var, width=300, cursor="left_ptr").pack(anchor="w")'''

def fazer_backup():
    """Cria um backup do arquivo main.py com timestamp"""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"main.py.{timestamp}.bak"
    shutil.copy(MAIN_FILE, backup_path)
    print(f"✅ Backup criado em: {backup_path}")

def main():
    print("🔧 Aplicando correção dos temas...")

    if not MAIN_FILE.exists():
        print("❌ Arquivo core/main.py não encontrado!")
        return

    # Backup
    fazer_backup()

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Substituir o dicionário THEMES (do início até o fechamento)
    # Padrão: THEMES = { ... } (pode ter quebras de linha)
    pattern_themes = r'THEMES\s*=\s*\{.*?\n\}'
    # Usamos re.DOTALL para que . capture quebras de linha
    novo_conteudo = re.sub(pattern_themes, NOVO_THEMES, content, flags=re.DOTALL)

    # 2. Substituir o trecho da interface de temas em _fill_config
    # Precisamos encontrar o bloco que começa com "f_theme = ctk.CTkFrame" e termina antes do próximo elemento
    # Vamos usar um padrão que capture desde a linha "f_theme = ..." até a linha do pack do OptionMenu
    pattern_fill_config = r'(f_theme = ctk\.CTkFrame\(parent, fg_color="transparent"\).*?ctk\.CTkOptionMenu\(f_theme, values=theme_names, variable=self\.theme_name_var, width=300, cursor="left_ptr"\)\.pack\(anchor="w"\))'
    novo_conteudo = re.sub(pattern_fill_config, NOVO_FILL_CONFIG_THEMES, novo_conteudo, flags=re.DOTALL)

    # 3. Ajustar a definição da lista de temas e o mapeamento de índices
    # (já feito no passo 2)

    # 4. Garantir que não haja menções a "default" nos temas (caso existam em outros lugares)
    # Opcional: substituir ocorrências de "default" no config inicial? Não necessário.

    # Escrever o arquivo
    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)

    print("✅ Temas corrigidos e atualizados com sucesso!")
    print("   Novos temas: Cinza Profissional (Default), Tecno, Claro Clean")
    print("▶️ Execute 'python -m core.main' para testar.")

if __name__ == "__main__":
    main()
