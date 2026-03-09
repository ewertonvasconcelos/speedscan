#!/usr/bin/env python3
"""
Script para corrigir erros de chaves desbalanceadas em core/main.py.
Analisa linha a linha, conta profundidade de {} e remove chaves extras.
Cria backup antes de modificar.
"""

import os
import re
import shutil
from datetime import datetime

def count_braces(line):
    """Retorna (abre, fecha) número de { e } na linha."""
    return line.count('{'), line.count('}')

def fix_braces(filepath):
    """Tenta corrigir chaves desbalanceadas."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    depth = 0
    changes = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Ignora linhas vazias ou comentários (mas cuidado com comentários que tenham chaves)
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue

        open_b, close_b = count_braces(line)
        # Se a linha tem mais fechamentos do que aberturas, e a profundidade atual é zero,
        # pode ser uma linha de fechamento extra. Vamos tentar ignorar se parecer isolada.
        if close_b > open_b and depth - (close_b - open_b) < 0:
            # Temos fechamentos demais. Vamos ver se a linha é apenas "}" ou algo assim.
            if stripped == '}':
                print(f"Removendo linha {i+1}: fechamento extra.")
                changes = True
                continue  # pula a linha
            else:
                # Tentar remover apenas os fechamentos extras? Muito complexo, manteremos.
                pass

        # Atualiza profundidade com base nos caracteres
        depth += open_b - close_b
        new_lines.append(line)

    # Se ainda sobrar profundidade positiva no final, precisamos adicionar fechamentos?
    # Mas isso pode ser perigoso. Vamos apenas avisar.
    if depth > 0:
        print(f"Aviso: profundidade final {depth} (faltam {depth} fechamentos).")
        # Adicionar linhas de fechamento?
        # for _ in range(depth):
        #     new_lines.append('}\n')
        # changes = True
    elif depth < 0:
        print(f"Aviso: profundidade final negativa {depth} (excesso de fechamentos).")

    if changes:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    else:
        return False

def check_syntax(filepath):
    """Verifica sintaxe."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, filepath, 'exec')
        return True, None
    except SyntaxError as e:
        return False, e

def main():
    main_py = os.path.join(os.getcwd(), 'core', 'main.py')
    if not os.path.isfile(main_py):
        print("Erro: core/main.py não encontrado.")
        return

    print("Verificando sintaxe atual...")
    ok, err = check_syntax(main_py)
    if ok:
        print("✅ Sintaxe OK.")
        return

    print(f"❌ Erro: {err}")
    resposta = input("Criar backup e tentar corrigir chaves automaticamente? (s/N): ")
    if resposta.lower() != 's':
        print("Cancelado.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{main_py}.bak.braces.{timestamp}"
    shutil.copy2(main_py, backup_file)
    print(f"Backup criado: {backup_file}")

    fixed = fix_braces(main_py)
    if fixed:
        print("Alterações realizadas. Verificando novamente...")
        ok2, err2 = check_syntax(main_py)
        if ok2:
            print("✅ Erro corrigido!")
        else:
            print(f"❌ Ainda há erro: {err2}")
            print("Pode ser necessário ajuste manual.")
    else:
        print("Nenhuma alteração necessária (ou não foi possível corrigir).")

    print("\nRevise com 'git diff' e depois teste.")

if __name__ == '__main__':
    main()
