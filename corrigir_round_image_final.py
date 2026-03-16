#!/usr/bin/env python3
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_round_final")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Encontrar a primeira definição de round_image
inicio = -1
for i, linha in enumerate(linhas):
    if linha.strip().startswith('def round_image'):
        inicio = i
        break

if inicio == -1:
    print("Função round_image não encontrada.")
    exit(1)

# Encontrar o fim da função (próxima definição de função no mesmo nível)
fim = inicio + 1
while fim < len(linhas) and not (linhas[fim].strip().startswith('def ') and linhas[fim][0] != ' '):
    fim += 1

# Versão correta da função (indentação: 4 espaços para a linha def, 8 para dentro)
nova_funcao = [
    '    def round_image(self, path, size=(96,96), radius=20):\n',
    '        print(f"DEBUG round_image: path={path}")\n',
    '        try:\n',
    '            img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)\n',
    '            mask = Image.new("L", size, 0)\n',
    '            ImageDraw.Draw(mask).rounded_rectangle((0,0)+size, radius=radius, fill=255)\n',
    '            result = Image.new("RGBA", size)\n',
    '            result.paste(img, (0,0), mask)\n',
    '            print("DEBUG round_image: sucesso")\n',
    '            return ctk.CTkImage(result, size=size)\n',
    '        except Exception as e:\n',
    '            print(f"DEBUG round_image: erro {e}")\n',
    '            return None\n',
]

# Substituir
linhas[inicio:fim] = nova_funcao

with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("Função round_image corrigida. Verificando sintaxe...")

import subprocess
result = subprocess.run(["python", "-m", "py_compile", str(arquivo)], capture_output=True, text=True)
if result.returncode != 0:
    print("Ainda há erro de sintaxe:")
    print(result.stderr)
else:
    print("Sintaxe OK. Execute o programa.")
