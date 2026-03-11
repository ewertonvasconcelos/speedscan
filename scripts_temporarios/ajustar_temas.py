#!/usr/bin/env python3
"""
Script para modificar os temas do SpeedScan:
- Remove o tema "Padrão (Roxo)"
- Renomeia os temas restantes para:
  - Cinza Profissional -> "Cinza Profissional (Default)"
  - Escuro Total -> "Tecno"
  - Claro Clean -> "Claro Clean" (mantém)
- Define o tema padrão como "Cinza Profissional (Default)" (chave "grey")
"""

import shutil
import re
import sys
from pathlib import Path
from datetime import datetime

MAIN_FILE = Path("core/main.py")
BACKUP_DIR = Path("backups")

def fazer_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"main.py.{timestamp}.bak"
    if MAIN_FILE.exists():
        shutil.copy(MAIN_FILE, backup_path)
        print(f"✅ Backup criado em: {backup_path}")
        return True
    else:
        print("❌ Arquivo core/main.py não encontrado!")
        return False

def main():
    print("🔧 Modificando temas do SpeedScan...")

    if not fazer_backup():
        sys.exit(1)

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Alterar o dicionário THEMES: remover a linha do "default"
    # Procuramos por THEMES = { ... } e removemos a entrada "default"
    # Vamos usar regex para encontrar o bloco e substituir.
    # Primeiro, encontrar o bloco THEMES.
    pattern_themes = r'(THEMES\s*=\s*\{)(.*?)(\})'
    match = re.search(pattern_themes, content, re.DOTALL)
    if not match:
        print("❌ Não foi possível encontrar THEMES no arquivo.")
        sys.exit(1)

    themes_block = match.group(2)
    # Remover a linha que contém "default": ...
    # Vamos quebrar em linhas e filtrar
    lines = themes_block.split('\n')
    new_lines = []
    for line in lines:
        if '"default"' not in line and "'default'" not in line:
            new_lines.append(line)
    new_themes_block = '\n'.join(new_lines)
    # Substituir no conteúdo
    new_content = content.replace(themes_block, new_themes_block)

    # 2. Alterar DEFAULT_CONFIG para theme "grey"
    new_content = re.sub(
        r'("theme"\s*:\s*)"default"',
        r'\1"grey"',
        new_content
    )

    # 3. Alterar a lista theme_names em _fill_config
    # Procuramos por: theme_names = ["Padrão (Roxo)", "Cinza Profissional", "Escuro Total", "Claro Clean"]
    new_theme_names = 'theme_names = ["Cinza Profissional (Default)", "Tecno", "Claro Clean"]'
    new_content = re.sub(
        r'theme_names = \[[^\]]+\]',
        new_theme_names,
        new_content
    )

    # 4. Alterar a lista de chaves theme_keys (a linha que define theme_index)
    # A linha original: theme_index = ["default", "grey", "dark", "light"].index(current_theme) ...
    # Vamos substituir por: theme_index = ["grey", "dark", "light"].index(current_theme) ...
    # Mas precisamos ajustar também o fallback para 0
    new_content = re.sub(
        r'theme_index = \[[^\]]+\]\.index\(current_theme\)',
        'theme_index = ["grey", "dark", "light"].index(current_theme)',
        new_content
    )

    # 5. Ajustar o fallback em update_theme_vars: THEMES.get(self.config["theme"], THEMES["default"])
    # Vamos mudar para THEMES.get(self.config["theme"], THEMES["grey"])
    new_content = re.sub(
        r'THEMES\.get\(self\.config\["theme"\],\s*THEMES\["default"\]\)',
        'THEMES.get(self.config["theme"], THEMES["grey"])',
        new_content
    )

    # 6. Salvar
    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ Temas modificados com sucesso!")
    print("   Agora os temas disponíveis são:")
    print("   - Cinza Profissional (Default)")
    print("   - Tecno")
    print("   - Claro Clean")
    print("▶️ Execute 'python -m core.main' para testar.")

if __name__ == "__main__":
    main()
