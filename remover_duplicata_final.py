#!/usr/bin/env python3
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_final4")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r') as f:
    linhas = f.readlines()

# Encontrar a primeira ocorrência da função (linha ~175)
primeira = -1
for i, linha in enumerate(linhas):
    if 'def round_image' in linha:
        primeira = i
        break

if primeira == -1:
    print("Função não encontrada. Abortando.")
    exit(1)

# Agora, procurar a partir da linha 1000 em diante por outra ocorrência
segunda = -1
for i in range(1000, len(linhas)):
    if 'def round_image' in linhas[i]:
        segunda = i
        break

if segunda == -1:
    print("Nenhuma duplicata encontrada. Verifique manualmente.")
else:
    print(f"Duplicata encontrada na linha {segunda+1}. Removendo...")
    # Remover o bloco duplicado até a próxima definição de função
    fim = segunda + 1
    while fim < len(linhas) and not (linhas[fim].strip().startswith('def ') and linhas[fim][0] != ' '):
        fim += 1
    # Remover as linhas do intervalo
    del linhas[segunda:fim]
    print(f"Bloco removido (linhas {segunda+1} a {fim}).")

# Reescrever o arquivo
with open(arquivo, 'w') as f:
    f.writelines(linhas)

print("Arquivo limpo. Execute o programa novamente.")
