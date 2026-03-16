#!/usr/bin/env python3
import shutil
from pathlib import Path

arquivo = Path("core/dashboard.py")
backup = Path("core/dashboard.py.bak_try")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r') as f:
    linhas = f.readlines()

# Encontrar a linha com getattr
for i, linha in enumerate(linhas):
    if 'callback = getattr(self.app, callback_name)' in linha:
        # Substituir por um bloco try-except
        indent = linha[:len(linha) - len(linha.lstrip())]
        novo_bloco = [
            f'{indent}try:\n',
            f'{indent}    callback = getattr(self.app, callback_name)\n',
            f'{indent}except AttributeError as e:\n',
            f'{indent}    print(f"DEBUG: AttributeError: {e}, self.app type = {type(self.app)}, callback_name={callback_name}")\n',
            f'{indent}    print(f"DEBUG: self.app dir = {dir(self.app)[:10]}...")\n',
            f'{indent}    # Tentar obter do tipo\n',
            f'{indent}    callback = getattr(type(self.app), callback_name, None)\n',
            f'{indent}    if callback:\n',
            f'{indent}        # Se for método, precisamos do self\n',
            f'{indent}        callback = callback.__get__(self.app, type(self.app))\n',
            f'{indent}    else:\n',
            f'{indent}        raise\n',
        ]
        linhas[i:i+1] = novo_bloco
        print("Bloco try-except inserido.")
        break

with open(arquivo, 'w') as f:
    f.writelines(linhas)

print("Modificação concluída. Execute o programa.")
