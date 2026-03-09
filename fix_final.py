#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_final2')

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

# 2. Coletar todas as definições de função (métodos) que estão dentro da classe atualmente
#    Vamos manter apenas as que estão corretamente indentadas (4 espaços)
existing_methods = re.findall(r'(\n    def \w+\(.*?\):.*?)(?=\n    def|\n\n|\Z)', class_body, re.DOTALL)
existing_methods = [m.strip('\n') for m in existing_methods]

# 3. Coletar definições de função que estão fora da classe (no post_class)
#    Inclui possíveis apply_config, _restart_app, widget_*, etc.
outside_methods = re.findall(r'(\ndef \w+\(.*?\):.*?)(?=\ndef|\n\n|\Z)', post_class, re.DOTALL)
outside_methods = [m.strip('\n') for m in outside_methods]

# 4. Coletar o bloco if __name__ do post_class (se existir)
if_main_match = re.search(r'(\nif __name__ == ["\']__main__["\']:.*)', post_class, re.DOTALL)
if_main = if_main_match.group(1) if if_main_match else ''

# 5. Combinar todos os métodos (os que já estão dentro + os de fora)
all_methods = existing_methods + outside_methods

# 6. Remover duplicatas (pelo nome da função)
method_dict = {}
for m in all_methods:
    # Extrai o nome da função
    name_match = re.match(r'    def (\w+)\(', m)
    if name_match:
        name = name_match.group(1)
        method_dict[name] = m  # última ocorrência vence

# 7. Métodos obrigatórios que devem existir (se não existirem, adicionar)
required_methods = {
    'apply_config': """
    def apply_config(self):
        \"\"\"Aplica as configurações de tema, escala e reinicia a interface.\"\"\"
        self._save_config()
        self.update_theme_vars()
        self.apply_ui_scale()
        self.show_toast("Configurações aplicadas. Reinicie o aplicativo para ver todas as alterações.", 3000)
        self.after(1000, self._restart_app)
""",
    '_restart_app': """
    def _restart_app(self):
        import sys
        import subprocess
        self.destroy()
        subprocess.Popen([sys.executable, "-m", "core.main"])
        sys.exit()
"""
}

for name, code in required_methods.items():
    if name not in method_dict:
        method_dict[name] = code.strip('\n')

# 8. Métodos widget_* também são necessários. Vamos garantir que todos os widget_* originais estejam presentes.
#    Eles já devem estar em method_dict, mas se faltar algum, adicionamos uma versão simples.

widget_names = ['hostname', 'distro', 'kernel', 'uptime', 'cpu', 'ram', 'gpu', 'disks', 'battery', 'temps', 'health']
for w in widget_names:
    name = f'widget_{w}'
    if name not in method_dict:
        # Cria um método simples que apenas coloca um label
        method_dict[name] = f"""
    def {name}(self, frame, tag):
        import socket
        label = ctk.CTkLabel(frame, text="N/A", font=("Inter", 16))
        label.pack(expand=True)
        print("DEBUG: {name} chamado")
"""

# 9. Reconstruir o corpo da classe com todos os métodos em ordem alfabética (opcional, mas organizado)
#    Vamos ordenar para consistência
sorted_methods = sorted(method_dict.values())
class_body_new = '\n\n'.join(sorted_methods)
# Garantir que cada método comece com 4 espaços (já deve estar, mas forçar)
class_body_new = re.sub(r'^', '    ', class_body_new, flags=re.MULTILINE)
class_body_new = class_body_new.lstrip()  # remove espaços extras no início

# 10. Montar o novo conteúdo
new_content = pre_class + class_header + class_body_new + '\n\n' + if_main

# 11. Salvar
with open(file_path, 'w') as f:
    f.write(new_content)

print("✅ Correções finais aplicadas!")
print("Execute: python -m core.main")
