#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_remove_dup")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r') as f:
    linhas = f.readlines()

# Procurar a primeira ocorrência de 'def round_image'
primeira = -1
for i, linha in enumerate(linhas):
    if 'def round_image' in linha:
        primeira = i
        break

if primeira == -1:
    print("Função não encontrada.")
    exit(1)

# Agora procurar todas as outras ocorrências depois dessa e remover o bloco inteiro
# Vamos construir uma nova lista de linhas, pulando os blocos duplicados
# Para isso, precisamos identificar onde começa e termina cada bloco.
# Como é mais simples, vamos remover todas as ocorrências após a primeira,
# assumindo que o bloco termina antes da próxima definição de função (def)

nova_lista = []
i = 0
total = len(linhas)
encontrou_primeira = False

while i < total:
    linha = linhas[i]
    if 'def round_image' in linha and not encontrou_primeira:
        # É a primeira, mantém
        encontrou_primeira = True
        nova_lista.append(linha)
        i += 1
        # Incluir o corpo da função até a próxima definição de função no mesmo nível
        # Vamos incluir até encontrar uma linha que comece com 'def ' no mesmo nível de indentação
        # Mas é complicado. Vamos apenas incluir até a linha antes da próxima definição.
        while i < total and not (linhas[i].strip().startswith('def ') and linhas[i][0] != ' '):
            nova_lista.append(linhas[i])
            i += 1
    elif 'def round_image' in linha and encontrou_primeira:
        # É duplicata, pular todo o bloco
        print(f"Pulando bloco duplicado começando na linha {i+1}")
        i += 1
        while i < total and not (linhas[i].strip().startswith('def ') and linhas[i][0] != ' '):
            i += 1
    else:
        nova_lista.append(linha)
        i += 1

with open(arquivo, 'w') as f:
    f.writelines(nova_lista)

print("Duplicatas removidas.")
