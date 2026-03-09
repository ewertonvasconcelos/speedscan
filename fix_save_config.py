#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir o método _save_config em core/main.py.
A linha 443 contém um erro: open(config.CONFIG_FILE, 'default', 'utf-8')
deveria ser open(config.CONFIG_FILE, 'w', encoding='utf-8').
Cria backup antes de modificar.
"""

import os
import shutil
from datetime import datetime

def main():
    main_py = os.path.join(os.getcwd(), 'core', 'main.py')
    if not os.path.isfile(main_py):
        print("Erro: core/main.py não encontrado.")
        return

    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{main_py}.bak.saveconfig.{timestamp}"
    shutil.copy2(main_py, backup_file)
    print(f"Backup criado: {backup_file}")

    with open(main_py, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Procurar a linha que contém "open(config.CONFIG_FILE, 'default', 'utf-8')"
    # Vamos percorrer e substituir
    modified = False
    for i, line in enumerate(lines):
        if "open(config.CONFIG_FILE, 'default', 'utf-8')" in line:
            lines[i] = line.replace(
                "open(config.CONFIG_FILE, 'default', 'utf-8')",
                "open(config.CONFIG_FILE, 'w', encoding='utf-8')"
            )
            print(f"Linha {i+1} corrigida.")
            modified = True
            break

    if not modified:
        print("Não foi encontrada a linha com o erro. Verifique manualmente.")
        return

    # Escrever de volta
    with open(main_py, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("Arquivo corrigido. Teste novamente com 'python -m core.main'.")

if __name__ == '__main__':
    main()
