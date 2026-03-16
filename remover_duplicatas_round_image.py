#!/usr/bin/env python3
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_remove_dup2")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r') as f:
    linhas = f.readlines()

indices = [i for i, linha in enumerate(linhas) if linha.strip().startswith('def round_image')]

if len(indices) > 1:
    print(f"Encontradas {len(indices)} definições. Mantendo a primeira (linha {indices[0]+1}) e removendo as demais.")
    nova_lista = []
    i = 0
    while i < len(linhas):
        if i in indices[1:]:
            # Pular este bloco
            i += 1
            while i < len(linhas) and not (linhas[i].strip().startswith('def ') and linhas[i][0] != ' '):
                i += 1
            continue
        nova_lista.append(linhas[i])
        i += 1
    with open(arquivo, 'w') as f:
        f.writelines(nova_lista)
    print("Definições extras removidas.")
else:
    print("Apenas uma definição encontrada. Verifique manualmente.")

# Verificar sintaxe
import subprocess
result = subprocess.run(["python", "-m", "py_compile", str(arquivo)], capture_output=True, text=True)
if result.returncode != 0:
    print("Ainda há erro de sintaxe:")
    print(result.stderr)
else:
    print("Sintaxe OK. Execute o programa.")
