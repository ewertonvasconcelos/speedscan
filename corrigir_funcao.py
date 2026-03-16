#!/usr/bin/env python3
import sys
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_final3")
with open(arquivo, 'r') as f:
    linhas = f.readlines()

# Backup
with open(backup, 'w') as f:
    f.writelines(linhas)
print(f"Backup criado: {backup}")

# Encontrar a função round_image
inicio = -1
fim = -1
for i, linha in enumerate(linhas):
    if 'def round_image' in linha:
        inicio = i
        # Procurar o fim: próximo def no mesmo nível ou EOF
        j = i + 1
        while j < len(linhas):
            if linhas[j].strip().startswith('def ') and linhas[j][0].isspace() and len(linhas[j].lstrip()) == len(linhas[j]) - 4:  # provavelmente mesmo nível
                fim = j
                break
            j += 1
        if fim == -1:
            fim = len(linhas)
        break

if inicio == -1:
    print("Função não encontrada.")
    sys.exit(1)

print(f"Função encontrada nas linhas {inicio+1}-{fim}")

# Nova função com indentação de 4 espaços
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
    '            return None\n'
]

# Substituir as linhas
linhas[inicio:fim] = nova_funcao

# Escrever de volta
with open(arquivo, 'w') as f:
    f.writelines(linhas)

print("Função substituída com sucesso.")
