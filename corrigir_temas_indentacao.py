#!/usr/bin/env python3
"""
Corrige a indentação da seção de temas na aba Configurações e ajusta os temas.
Substitui o bloco de temas por uma versão com indentação correta.
"""

import shutil
import re
from pathlib import Path
from datetime import datetime

MAIN_FILE = Path("core/main.py")
BACKUP_DIR = Path("backups")

# Bloco corrigido da seção de temas (com indentação de 4 espaços)
BLOCO_TEMAS = '''        f_theme = ctk.CTkFrame(parent, fg_color="transparent")
        f_theme.pack(fill="x", pady=10)
        ctk.CTkLabel(f_theme, text="Tema da interface *", font=("Inter",14), text_color=self.text_color).pack(anchor="w")
        theme_names = ["Cinza Profissional (Default)", "Tecno", "Claro Clean"]
        current_theme = self.config.get("theme", "grey")
        if current_theme == "default":
            current_theme = "grey"
        theme_keys = ["grey", "dark", "light"]
        theme_index = theme_keys.index(current_theme) if current_theme in theme_keys else 0
        self.theme_name_var = ctk.StringVar(value=theme_names[theme_index])
        ctk.CTkOptionMenu(f_theme, values=theme_names, variable=self.theme_name_var, width=300, cursor="left_ptr").pack(anchor="w")'''

def fazer_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"main.py.{timestamp}.bak"
    shutil.copy(MAIN_FILE, backup_path)
    print(f"✅ Backup criado em: {backup_path}")

def main():
    print("🔧 Corrigindo indentação da seção de temas...")

    if not MAIN_FILE.exists():
        print("❌ core/main.py não encontrado!")
        return

    fazer_backup()

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Procurar a linha que contém 'f_theme = ctk.CTkFrame'
    start_idx = None
    for i, line in enumerate(lines):
        if 'f_theme = ctk.CTkFrame' in line:
            start_idx = i
            break

    if start_idx is None:
        print("❌ Não foi possível localizar a seção de temas.")
        return

    # Procurar o final do bloco (próxima linha que começa com '        f_' ou '        #' ou '        ctk.')
    # Vamos procurar a linha que define 'f_tab' (próximo frame)
    end_idx = None
    for j in range(start_idx + 1, len(lines)):
        if lines[j].strip().startswith('f_tab =') or lines[j].strip().startswith('f_level ='):
            end_idx = j
            break

    if end_idx is None:
        print("❌ Não foi possível determinar o final do bloco.")
        return

    # Substituir as linhas do bloco
    # O bloco tem 9 linhas (no código original), mas vamos substituir do start_idx até end_idx-1
    # Inserir o novo bloco
    novo_bloco = BLOCO_TEMAS.splitlines(True)
    # Garantir que cada linha termine com newline
    novo_bloco = [line + ('\n' if not line.endswith('\n') else '') for line in novo_bloco]

    # Construir novo arquivo
    new_lines = lines[:start_idx] + novo_bloco + lines[end_idx:]

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("✅ Indentação corrigida e temas atualizados.")
    print("▶️ Execute 'python -m core.main' para testar.")

if __name__ == "__main__":
    main()
