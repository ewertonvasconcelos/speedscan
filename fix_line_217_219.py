#!/usr/bin/env python3
"""
Script para corrigir a indentação das linhas 217-219 (e arredores) manualmente.
Baseado no erro atual: expected an indented block after 'if' statement on line 217.
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
    backup_file = f"{main_py}.bak.line217.{timestamp}"
    shutil.copy2(main_py, backup_file)
    print(f"Backup criado: {backup_file}")

    # Mostrar as linhas 215-221 para contexto
    print("Linhas 215-221 atualmente:")
    for i in range(214, min(221, len(lines))):
        print(f"{i+1:4d}: {lines[i].rstrip()}")

    # Índices (base 0)
    line_215 = 214  # for d in devices:
    line_217 = 216  # if 'error' in d:
    line_219 = 218  # log.insert(...)

    if len(lines) > line_219:
        # Obter indentação da linha 215 (for)
        indent_215 = get_indent(lines[line_215])
        # A linha 217 deve estar indentada em relação à 215 (já deve estar, mas vamos verificar)
        # A linha 219 deve estar indentada em relação à 217
        target_indent_219 = get_indent(lines[line_217]) + 4
        current_indent_219 = get_indent(lines[line_219])
        if current_indent_219 != target_indent_219:
            lines[line_219] = ' ' * target_indent_219 + lines[line_219].lstrip()
            print(f"Indentação da linha 219 ajustada para {target_indent_219} espaços.")

    # Também verificar outras linhas dentro do mesmo bloco
    # Por exemplo, após a linha 219, pode haver mais linhas do if
    i = line_219 + 1
    base_indent = get_indent(lines[line_217])
    while i < len(lines):
        current_indent = get_indent(lines[i])
        if current_indent <= base_indent:
            break
        # Se já está indentado, mantém; caso contrário, ajusta para base+4
        target = base_indent + 4
        if current_indent != target:
            lines[i] = ' ' * target + lines[i].lstrip()
            print(f"Indentação da linha {i+1} ajustada para {target} espaços.")
        i += 1

    with open(main_py, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("Indentação específica corrigida. Verificando sintaxe...")
    ok2, err2 = check_syntax(main_py)
    if ok2:
        print("✅ Erro corrigido!")
    else:
        print(f"❌ Ainda há erro: {err2}")

    print("\nRevise com 'git diff' e depois teste.")

if __name__ == '__main__':
    main()
