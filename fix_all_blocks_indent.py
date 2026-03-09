#!/usr/bin/env python3
"""
Script para corrigir a indentação de blocos após qualquer linha que termine com ':'
(if, for, while, else, elif, try, except, etc.), exceto definições de função/classe.
Garante que a primeira linha não vazia após o bloco tenha indentação aumentada em 4 espaços.
Cria backup antes de modificar.
"""

import os
import shutil
from datetime import datetime

def check_syntax(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, filepath, 'exec')
        return True, None
    except SyntaxError as e:
        return False, e

def get_indent(line):
    return len(line) - len(line.lstrip())

def main():
    main_py = os.path.join(os.getcwd(), 'core', 'main.py')
    if not os.path.isfile(main_py):
        print("Erro: core/main.py não encontrado.")
        return

    print("Verificando sintaxe atual...")
    ok, err = check_syntax(main_py)
    if ok:
        print("✅ Sintaxe OK. Nada a fazer.")
        return
    print(f"❌ Erro atual: {err}")

    with open(main_py, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{main_py}.bak.allblocks.{timestamp}"
    shutil.copy2(main_py, backup_file)
    print(f"Backup criado: {backup_file}")

    # Percorrer todas as linhas
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        # Se a linha termina com ':' e não é definição de função/classe
        if stripped and stripped[-1] == ':' and not stripped.startswith(('def ', 'class ')):
            block_indent = get_indent(line)
            # Procurar a próxima linha não vazia
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines):
                next_indent = get_indent(lines[j])
                # Se a próxima linha não vazia tem indentação <= à do bloco, ajustar
                if next_indent <= block_indent:
                    lines[j] = ' ' * (block_indent + 4) + lines[j].lstrip()
                    print(f"Indentada linha {j+1} (após bloco na linha {i+1})")
        i += 1

    with open(main_py, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("Indentação de blocos ajustada. Verificando sintaxe...")
    ok2, err2 = check_syntax(main_py)
    if ok2:
        print("✅ Erro corrigido!")
    else:
        print(f"❌ Ainda há erro: {err2}")

    print("\nRevise com 'git diff' e depois teste.")

if __name__ == '__main__':
    main()
