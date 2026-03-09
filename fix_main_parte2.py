#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_parte2')

# Backup
shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    content = f.read()

# 1. Encontrar a classe SpeedScan
class_pattern = r'(class SpeedScan\(ctk\.CTk\):\s*\n)(.*?)(?=\n\nclass|\n\Z|\nif __name__)'
class_match = re.search(class_pattern, content, re.DOTALL)
if not class_match:
    print("Classe SpeedScan não encontrada!")
    exit(1)

class_header = class_match.group(1)
class_body = class_match.group(2)
pre_class = content[:class_match.start()]
post_class = content[class_match.end():]

# 2. Extrair todas as definições de função que estão no post_class (fora da classe)
function_pattern = r'(\n\s*def \w+\(.*?\):.*?)(?=\n\s*def|\n\n|\Z)'
outside_functions = re.findall(function_pattern, post_class, re.DOTALL)

# 3. Extrair também funções que estão dentro da classe (já existentes)
inside_functions = re.findall(r'(\n    def \w+\(.*?\):.*?)(?=\n    def|\n\n|\Z)', class_body, re.DOTALL)

# 4. Combinar todas as funções, mantendo as de dentro e adicionando as de fora (com indentação)
all_functions = list(inside_functions) + outside_functions

# 5. Remover duplicatas baseado no nome da função
function_dict = {}
for func in all_functions:
    # Extrair nome da função
    name_match = re.match(r'\s*def (\w+)\(', func)
    if name_match:
        name = name_match.group(1)
        function_dict[name] = func

# 6. Garantir que métodos obrigatórios estejam presentes (apply_config e _restart_app)
if 'apply_config' not in function_dict:
    function_dict['apply_config'] = '''
    def apply_config(self):
        """Aplica as configurações de tema, escala e reinicia a interface."""
        self._save_config()
        self.update_theme_vars()
        self.apply_ui_scale()
        self.show_toast("Configurações aplicadas. Reinicie o aplicativo para ver todas as alterações.", 3000)
        self.after(1000, self._restart_app)
'''

if '_restart_app' not in function_dict:
    function_dict['_restart_app'] = '''
    def _restart_app(self):
        import sys
        import subprocess
        self.destroy()
        subprocess.Popen([sys.executable, "-m", "core.main"])
        sys.exit()
'''

# 7. Reconstruir o corpo da classe com todas as funções, ordenadas (opcional)
#    Vamos ordenar por nome para consistência
sorted_functions = [function_dict[name] for name in sorted(function_dict.keys())]

# Indentar corretamente as funções que vieram de fora (já devem estar com 4 espaços, mas garantimos)
indented_functions = []
for func in sorted_functions:
    lines = func.splitlines()
    # Se a primeira linha não começar com 4 espaços, adicionar
    if lines and not lines[0].startswith('    '):
        lines = ['    ' + line if line.strip() else '' for line in lines]
    indented_functions.append('\n'.join(lines))

new_class_body = '\n\n'.join(indented_functions)

# 8. Remover o bloco if __name__ do post_class (se houver) para recolocar no final
if_main_match = re.search(r'(\nif __name__ == ["\']__main__["\']:.*)', post_class, re.DOTALL)
if_main = if_main_match.group(1) if if_main_match else ''

# 9. Montar o novo conteúdo
new_content = pre_class + class_header + new_class_body + '\n\n' + if_main

# 10. Salvar
with open(file_path, 'w') as f:
    f.write(new_content)

print("✅ Parte 2 aplicada: classe reorganizada e métodos essenciais inseridos.")
print("Execute agora: python -m core.main")
