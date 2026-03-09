#!/usr/bin/env python3
"""
Script interativo para reconstruir a definição de DEFAULT_CONFIG em core/main.py.
Exibe um trecho do arquivo (linhas 100-250) e permite que o usuário
especifique manualmente as linhas de início e fim do bloco que deve ser
envolvido em DEFAULT_CONFIG = { ... }. O script então substitui esse trecho
pela nova definição, preservando a indentação e ajustando vírgulas.
Cria backup antes de modificar.
"""

import os
import shutil
from datetime import datetime

def check_syntax(filepath):
    """Verifica sintaxe."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, filepath, 'exec')
        return True, None
    except SyntaxError as e:
        return False, e

def show_lines(lines, start, end):
    """Exibe linhas de start a end (1-based)."""
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1:4d}: {lines[i].rstrip()}")

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

    print("\nExibindo linhas 100 a 250 do arquivo atual:")
    show_lines(lines, 100, 250)

    print("\n" + "="*60)
    print("Identifique o bloco que deve se tornar DEFAULT_CONFIG.")
    print("Geralmente começa com linhas como '\"theme\": \"default\",'")
    print("e termina com as últimas definições (como escalas).")
    print("="*60)

    try:
        start = int(input("Digite o número da linha INICIAL (1-based): "))
        end = int(input("Digite o número da linha FINAL (1-based): "))
    except ValueError:
        print("Entrada inválida. Cancelando.")
        return

    if start < 1 or end > len(lines) or start > end:
        print("Intervalo inválido.")
        return

    # Confirmar
    print(f"\nBloco selecionado: linhas {start} a {end}")
    show_lines(lines, start, end)
    resp = input("Confirma? (s/N): ")
    if resp.lower() != 's':
        print("Cancelado.")
        return

    # Criar backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{main_py}.bak.rebuild.{timestamp}"
    shutil.copy2(main_py, backup_file)
    print(f"Backup criado: {backup_file}")

    # Extrair o bloco e ajustar vírgulas
    block_lines = lines[start-1:end]
    # Remover vírgula da última linha se existir
    last_line = block_lines[-1].rstrip()
    if last_line.endswith(','):
        block_lines[-1] = last_line[:-1] + '\n'
    # Garantir que a primeira linha não tenha indentação extra? Vamos manter a indentação original.

    # Construir nova definição
    new_block = []
    new_block.append("DEFAULT_CONFIG = {\n")
    # Adicionar as linhas do bloco com um nível de indentação a mais
    for line in block_lines:
        # Adiciona 4 espaços à esquerda (ajustável)
        new_block.append("    " + line)
    new_block.append("}\n")

    # Substituir o intervalo
    new_lines = lines[:start-1] + new_block + lines[end:]

    # Escrever
    with open(main_py, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print("Bloco reconstruído. Verificando sintaxe...")
    ok2, err2 = check_syntax(main_py)
    if ok2:
        print("✅ Erro corrigido!")
    else:
        print(f"❌ Ainda há erro: {err2}")
        print("Pode ser necessário ajustar manualmente o intervalo.")

    print("\nRevise com 'git diff' e depois teste.")

if __name__ == '__main__':
    main()
