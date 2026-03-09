#!/usr/bin/env python3
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_line211')

# Fazer backup
shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    lines = f.readlines()

# A linha 211 no erro corresponde ao índice 210 (pois a contagem começa em 1)
target_index = 210  # índice zero-based

if len(lines) > target_index:
    # Verificar se a linha contém apenas "3000)" ou algo similar
    current_line = lines[target_index].rstrip('\n')
    print(f"Linha 211 atual: {current_line}")

    # Substituir por uma linha correta (com indentação de 8 espaços, como esperado)
    correct_line = '        self.show_toast("Configurações aplicadas. Reinicie o aplicativo para ver todas as alterações.", 3000)\n'
    lines[target_index] = correct_line

    # Verificar se a linha seguinte (212) é um parêntese solto e removê-la
    if target_index + 1 < len(lines) and lines[target_index + 1].strip() == ')':
        print(f"Removendo linha {target_index+2} com parêntese solto.")
        del lines[target_index + 1]

    # Salvar
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print("✅ Linha 211 corrigida e linhas extras removidas.")
else:
    print("Arquivo tem menos de 211 linhas. Não foi possível corrigir.")
    exit(1)

print("Execute novamente: python -m core.main")

