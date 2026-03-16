#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_prints2")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Corrigir o print problemático na linha 840 (aproximadamente)
# Substituir: print(f"DEBUG: _after_command: tag={tag}, tamanho do log = {len(log.get(\"1.0\", \"end-1c\"))}")
# Por: print(f"DEBUG: _after_command: tag={tag}, tamanho do log = {len(log.get('1.0', 'end-1c'))}")

padrao = r'print\(f"DEBUG: _after_command: tag={tag}, tamanho do log = {len\(log\.get\(\\"1.0\\", \\"end-1c\\"\)\)}"\)'
substituicao = 'print(f"DEBUG: _after_command: tag={tag}, tamanho do log = {len(log.get(\\'1.0\\', \\'end-1c\\'))}")'

# Como é complexo, vamos fazer uma substituição manual mais simples:
# Procurar pela linha específica e substituir
linhas = conteudo.split('\n')
for i, linha in enumerate(linhas):
    if 'tamanho do log = {len(log.get(\"1.0\", \"end-1c\"))}' in linha:
        linhas[i] = linha.replace('\"1.0\", \"end-1c\"', "'1.0', 'end-1c'")
        print(f"Linha {i+1} corrigida.")
        break

with open(arquivo, 'w', encoding='utf-8') as f:
    f.write('\n'.join(linhas))

print("Correção aplicada. Execute o programa novamente.")
