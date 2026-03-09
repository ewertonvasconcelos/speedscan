#!/usr/bin/env python3
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_class')

# Backup
shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    lines = f.readlines()

# Encontrar a linha onde começa a classe SpeedScan
class_start = None
for i, line in enumerate(lines):
    if 'class SpeedScan(ctk.CTk):' in line:
        class_start = i
        break

if class_start is None:
    print("Classe SpeedScan não encontrada!")
    exit(1)

# Encontrar o final da classe (próxima linha com indentação zero ou EOF)
class_end = class_start + 1
while class_end < len(lines) and (lines[class_end].startswith(' ') or lines[class_end].startswith('\t') or lines[class_end].strip() == ''):
    class_end += 1

print(f"Classe encontrada da linha {class_start+1} até {class_end}")

# Métodos que precisamos garantir que estejam dentro da classe
# Primeiro, verificar se apply_config já existe dentro da classe
apply_config_exists = any('def apply_config' in line and line.startswith('    ') for line in lines[class_start:class_end])

if not apply_config_exists:
    # Inserir apply_config e _restart_app antes do final da classe
    # Escolhemos um local: antes do método _monitor_loop (se existir) ou antes do último método
    # Vamos inserir antes da linha que contém 'def _monitor_loop'
    insert_pos = None
    for j in range(class_start, class_end):
        if 'def _monitor_loop' in lines[j]:
            insert_pos = j
            break
    if insert_pos is None:
        # Se não achar, insere no final, antes da última linha da classe
        insert_pos = class_end - 1

    # Código a ser inserido (com 4 espaços de indentação)
    new_code = [
        '    def apply_config(self):\n',
        '        """Aplica as configurações de tema, escala e reinicia a interface."""\n',
        '        self._save_config()\n',
        '        self.update_theme_vars()\n',
        '        self.apply_ui_scale()\n',
        '        self.show_toast("Configurações aplicadas. Reinicie o aplicativo para ver todas as alterações.", 3000)\n',
        '        self.after(1000, self._restart_app)\n',
        '\n',
        '    def _restart_app(self):\n',
        '        import sys\n',
        '        import subprocess\n',
        '        self.destroy()\n',
        '        subprocess.Popen([sys.executable, "-m", "core.main"])\n',
        '        sys.exit()\n',
        '\n'
    ]
    # Inserir em insert_pos
    lines[insert_pos:insert_pos] = new_code
    print("Métodos apply_config e _restart_app inseridos.")
else:
    print("apply_config já existe.")

# Agora, verificar se os métodos widget_* estão dentro da classe
# Se houver definições fora da classe (após class_end), movê-las para dentro
outside_widgets = []
j = class_end
while j < len(lines):
    if lines[j].startswith('def widget_') and not lines[j].startswith('    '):
        # Capturar o bloco do método
        start = j
        j += 1
        while j < len(lines) and (lines[j].startswith(' ') or lines[j].startswith('\t') or lines[j].strip() == ''):
            j += 1
        end = j
        outside_widgets.append((start, end))
    else:
        j += 1

if outside_widgets:
    # Remover os métodos de fora e inserir dentro da classe (antes do final)
    # Inserir antes da última linha da classe (antes de class_end)
    insert_pos = class_end - 1
    for start, end in reversed(outside_widgets):
        # Extrair o código
        widget_code = lines[start:end]
        # Garantir indentação de 4 espaços
        widget_code = ['    ' + line if line.strip() else '\n' for line in widget_code]
        # Remover do lugar original
        del lines[start:end]
        # Inserir na classe
        lines[insert_pos:insert_pos] = widget_code
        print(f"Método {widget_code[0].strip()} movido para dentro da classe.")
    # Atualizar class_end porque as linhas foram movidas
    # Como inserimos antes de class_end, class_end aumenta
    class_end += sum(len(w) for w in outside_widgets)

# Salvar
with open(file_path, 'w') as f:
    f.writelines(lines)

print("✅ Correções aplicadas. Execute: python -m core.main")
