#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

def corrigir_funcao_round_image():
    main_path = Path("core/main.py")
    backup_path = main_path.with_suffix(".py.bak")
    shutil.copy2(main_path, backup_path)
    print(f"Backup criado: {backup_path}")

    with open(main_path, "r") as f:
        linhas = f.readlines()

    inicio = None
    fim = None
    for i, linha in enumerate(linhas):
        if "def round_image" in linha:
            inicio = i
        if inicio is not None and "return None" in linha:
            fim = i
            break

    if inicio is None or fim is None:
        print("Função round_image não encontrada.")
        return

    # Extrair a indentação base (espaços antes de 'def')
    indent_base = len(linhas[inicio]) - len(linhas[inicio].lstrip())
    indent_body = indent_base + 4
    indent_except = indent_body + 4

    # Substituir o bloco do except
    for i in range(inicio, fim+1):
        if "except Exception as e:" in linhas[i]:
            # A linha do except pode estar com indentação incorreta, vamos corrigi-la
            linhas[i] = " " * indent_body + "except Exception as e:\n"
        elif "print(f\"DEBUG round_image: erro {e}\")" in linhas[i]:
            linhas[i] = " " * indent_except + "print(f\"DEBUG round_image: erro {e}\")\n"
        elif "return None" in linhas[i] and i > inicio:
            linhas[i] = " " * indent_except + "return None\n"

    with open(main_path, "w") as f:
        f.writelines(linhas)

    print("Indentação corrigida. Execute o programa novamente.")

if __name__ == "__main__":
    corrigir_funcao_round_image()
