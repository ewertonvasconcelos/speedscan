#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_widgets')

# Fazer backup
shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    content = f.read()

# Expressão para encontrar o bloco de métodos widget_*
# Procuramos por um comentário "Widgets do Dashboard" seguido de várias definições de função
widget_pattern = r'(# =+?\s*Widgets do Dashboard.*?)((?:def widget_\w+\(.*?\):.*?(?=\n\S|\Z))+)'
widget_match = re.search(widget_pattern, content, re.DOTALL)
if not widget_match:
    print("Não foi possível encontrar os métodos widget_* no arquivo.")
    exit(1)

widget_header = widget_match.group(1)  # o comentário
widget_code = widget_match.group(2)    # o código dos métodos

# Remover o bloco original
content = content.replace(widget_match.group(0), '')

# Encontrar o final da classe SpeedScan
# Vamos inserir os métodos antes do último método conhecido, por exemplo, antes de '_on_mousewheel'
# Ou antes do bloco 'if __name__ == "__main__"'
insert_before = 'def _on_mousewheel'
if insert_before not in content:
    print("Ponto de inserção não encontrado. Tentando inserir antes do final da classe...")
    # Alternativa: inserir antes do final da classe, antes do último 'def' ou antes do 'if __name__'
    # Vamos procurar o último 'def' dentro da classe e inserir depois dele
    # Mas isso é mais complicado. Vamos tentar inserir antes de 'if __name__'
    insert_before = 'if __name__ == "__main__":'
    if insert_before not in content:
        print("Não foi possível encontrar um local seguro para inserir. Abortando.")
        exit(1)

# Calcular a indentação da classe (4 espaços por padrão)
# Vamos pegar a indentação da linha onde está o insert_before
lines = content.splitlines()
insert_line_index = None
indent = '    '  # 4 espaços
for i, line in enumerate(lines):
    if insert_before in line:
        insert_line_index = i
        # Descobrir a indentação da linha (pode ser 4 ou 8 espaços)
        match = re.match(r'^(\s+)', line)
        if match:
            indent = match.group(1)
        break

if insert_line_index is None:
    print("Ponto de inserção não encontrado nas linhas.")
    exit(1)

# Preparar o código dos widgets com a indentação correta
widget_lines = widget_code.splitlines()
# Adicionar a indentação da classe + 4 espaços extras? Na verdade, os métodos devem estar no mesmo nível dos outros métodos, então usamos a indentação da classe (que é o que já temos)
# Mas a indentação atual do widget_code pode ser 0 ou 4. Vamos adicionar o 'indent' a cada linha não vazia.
indented_widget = '\n'.join(
    (indent + line) if line.strip() else ''
    for line in widget_lines
)

# Inserir antes da linha de insert_before
lines.insert(insert_line_index, indented_widget)
# Reconstruir o conteúdo
new_content = '\n'.join(lines)

with open(file_path, 'w') as f:
    f.write(new_content)

print("✅ Widgets movidos para dentro da classe SpeedScan com sucesso!")
print("Execute novamente: python -m core.main")
