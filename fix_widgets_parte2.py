#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_parte2')

# Fazer backup
shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    content = f.read()

# Encontrar a classe SpeedScan
class_match = re.search(r'class SpeedScan\(ctk\.CTk\):(.*?)(?=\n\n\S|\Z)', content, re.DOTALL)
if not class_match:
    print("Classe SpeedScan não encontrada!")
    exit(1)

class_body = class_match.group(1)

# Encontrar os métodos widget_* que estão fora da classe (provavelmente no final do arquivo)
widgets_pattern = r'(\n# =+?\s*Widgets do Dashboard.*?\n)((?:def widget_\w+\(.*?\):.*?(?=\n\S|\Z))+)'
widgets_match = re.search(widgets_pattern, content, re.DOTALL)
if not widgets_match:
    print("Métodos widget_* não encontrados no final do arquivo.")
    exit(1)

widgets_code = widgets_match.group(2)

# Remover os widgets do lugar original
content = content.replace(widgets_match.group(0), '')

# Encontrar o último método dentro da classe para inserir antes dele
# Vamos inserir antes do método _maximize_window ou _on_closing (últimos métodos)
last_method_match = re.search(r'(\n\s+def _on_closing\(.*?\):.*?)(?=\n\s+def|\Z)', class_body, re.DOTALL)
if not last_method_match:
    last_method_match = re.search(r'(\n\s+def _maximize_window\(.*?\):.*?)(?=\n\s+def|\Z)', class_body, re.DOTALL)

if not last_method_match:
    print("Não foi possível encontrar o final da classe.")
    exit(1)

last_method = last_method_match.group(1)
# Descobrir a indentação da classe (geralmente 4 espaços)
indent = re.match(r'(\s+)', last_method).group(1)

# Indentar os métodos widget_* com a mesma indentação da classe (ou um nível a mais?)
# Os métodos da classe têm indentação de 4 espaços, então vamos adicionar 4 espaços a cada linha não vazia
indented_widgets = '\n'.join(
    indent + line if line.strip() else ''
    for line in widgets_code.splitlines()
)

# Inserir antes do último método
new_class_body = class_body.replace(last_method, indented_widgets + '\n' + last_method)
new_content = content.replace(class_body, new_class_body)

with open(file_path, 'w') as f:
    f.write(new_content)

print("✅ Métodos widget_* movidos para dentro da classe SpeedScan!")
print("Execute agora: python -m core.main")
