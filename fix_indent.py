#!/usr/bin/env python3
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_indent')

# Fazer backup
shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    lines = f.readlines()

# Encontrar a linha que contém "self.after(1000, self._restart_app)"
target = "self.after(1000, self._restart_app)"
found = False
for i, line in enumerate(lines):
    if target in line:
        # Verificar a indentação atual
        current_indent = len(line) - len(line.lstrip())
        # A indentação correta deve ser a mesma da linha anterior (self.show_toast)
        # Vamos pegar a indentação da linha anterior
        if i > 0:
            prev_line = lines[i-1]
            correct_indent = len(prev_line) - len(prev_line.lstrip())
        else:
            correct_indent = 8  # fallback
        # Se a indentação atual for diferente, ajustar
        if current_indent != correct_indent:
            lines[i] = ' ' * correct_indent + line.lstrip()
            print(f"Linha {i+1} corrigida: indentação de {current_indent} para {correct_indent} espaços.")
        else:
            print(f"Linha {i+1} já está com indentação correta ({current_indent} espaços).")
        found = True
        break

if not found:
    print("Linha não encontrada. Verifique se o código contém 'self.after(1000, self._restart_app)'.")
    exit(1)

# Salvar o arquivo corrigido
with open(file_path, 'w') as f:
    f.writelines(lines)

print("✅ Correção aplicada. Execute novamente: python -m core.main")
