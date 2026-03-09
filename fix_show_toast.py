#!/usr/bin/env python3
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_showtoast')
shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    lines = f.readlines()

# Procurar a linha que contém 'self.show_toast'
for i, line in enumerate(lines):
    if 'self.show_toast' in line:
        # Construir a linha correta
        correct_line = '        self.show_toast("Configurações aplicadas. Reinicie o aplicativo para ver todas as alterações.", 3000)\n'
        # Substituir a linha atual
        lines[i] = correct_line
        # Se houver linhas extras (como a linha 211 que só tem '3000)'), vamos removê-las
        # Verificar se a próxima linha contém apenas '3000)' ou algo similar
        if i+1 < len(lines) and '3000' in lines[i+1] and ')' in lines[i+1]:
            # Remover a próxima linha
            lines.pop(i+1)
        print(f"Linha {i+1} corrigida.")
        break

# Salvar o arquivo
with open(file_path, 'w') as f:
    f.writelines(lines)

print("✅ Correção aplicada. Execute novamente: python -m core.main")
