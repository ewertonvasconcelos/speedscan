#!/usr/bin/env python3
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_840")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

for i, linha in enumerate(linhas):
    if 'tamanho do log = {len(log.get(\"1.0\", \"end-1c\"))}' in linha:
        linhas[i] = '        print(f"DEBUG: _after_command: tag={tag}, tamanho do log = {len(log.get(\'1.0\', \'end-1c\'))}")\n'
        print(f"Linha {i+1} corrigida.")
        break

with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("Correção aplicada. Execute o programa.")
