#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_debug')

shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    content = f.read()

# Adicionar prints no __init__ da classe SpeedScan
content = content.replace(
    'def __init__(self):',
    'def __init__(self):\n        print("DEBUG: SpeedScan __init__ iniciado")'
)

# Adicionar print no _fill_dashboard
content = content.replace(
    'def _fill_dashboard(self, parent):',
    'def _fill_dashboard(self, parent):\n        print("DEBUG: _fill_dashboard chamado")'
)

# Adicionar print na criação do Dashboard
content = content.replace(
    'self.dashboard = Dashboard(parent, self, fg_color="transparent")',
    'self.dashboard = Dashboard(parent, self, fg_color="transparent")\n        print("DEBUG: Dashboard instanciado")'
)

# Garantir que o dashboard seja empacotado
if 'self.dashboard.pack' not in content:
    # Procurar onde inserir
    content = content.replace(
        'self.dashboard = Dashboard(parent, self, fg_color="transparent")',
        'self.dashboard = Dashboard(parent, self, fg_color="transparent")\n        self.dashboard.pack(fill="both", expand=True)'
    )

# Adicionar um after para forçar atualização
content = content.replace(
    'self.dashboard.pack(fill="both", expand=True)',
    'self.dashboard.pack(fill="both", expand=True)\n        self.after(100, self.dashboard.load_state)'
)

# Adicionar prints nos métodos widget_* para ver se são chamados
widget_methods = ['hostname', 'distro', 'kernel', 'uptime', 'cpu', 'ram', 'gpu', 'disks', 'battery', 'temps', 'health']
for w in widget_methods:
    pattern = f'def widget_{w}\\(self, frame, tag\\):'
    replacement = f'def widget_{w}(self, frame, tag):\n        print(f"DEBUG: widget_{w} chamado")'
    content = content.replace(pattern, replacement)

with open(file_path, 'w') as f:
    f.write(content)

print("✅ Debug adicionado. Execute: python -m core.main")
