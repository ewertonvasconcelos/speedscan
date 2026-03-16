#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/dashboard.py")
backup = Path("core/dashboard.py.bak_debug2")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r') as f:
    linhas = f.readlines()

# Adicionar print no __init__ do Dashboard
for i, linha in enumerate(linhas):
    if linha.strip().startswith('def __init__(self, parent, app_instance, **kwargs):'):
        linhas.insert(i+1, '        print(f"DEBUG Dashboard.__init__: type(app_instance) = {type(app_instance)}")\n')
        break

# Adicionar print no __init__ do SlotWidget
for i, linha in enumerate(linhas):
    if linha.strip().startswith('def __init__(self, parent, slot_index, widget_type, app_instance, **kwargs):'):
        linhas.insert(i+1, '        print(f"DEBUG SlotWidget.__init__: type(app_instance) = {type(app_instance)}")\n')
        break

# Adicionar print no update_content do SlotWidget
for i, linha in enumerate(linhas):
    if linha.strip().startswith('def update_content(self):'):
        # Encontrar a linha onde callback é obtido
        j = i
        while j < len(linhas) and not 'callback_name' in linhas[j]:
            j += 1
        if j < len(linhas):
            linhas.insert(j+1, '        print(f"DEBUG SlotWidget.update_content: self.app type = {type(self.app)}, callback_name={callback_name}")\n')
        break

with open(arquivo, 'w') as f:
    f.writelines(linhas)

print("Prints adicionados. Execute o programa.")
