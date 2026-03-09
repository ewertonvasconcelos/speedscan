#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_final')

# Fazer backup
shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    content = f.read()

# 1. Encontrar a classe SpeedScan
class_match = re.search(r'(class SpeedScan\(ctk\.CTk\):.*?)(?=\n\n\S|\Z)', content, re.DOTALL)
if not class_match:
    print("Classe SpeedScan não encontrada!")
    exit(1)

class_body = class_match.group(1)
pre_class = content[:class_match.start()]
post_class = content[class_match.end():]

# 2. Remover definições de função que estão fora da classe (no post_class)
#    Vamos simplesmente limpar o post_class, pois ele só contém os widgets (que já estão dentro da classe)
#    e possivelmente definições soltas. Vamos extrair apenas os widgets que já estão dentro da classe
#    e descartar o resto.

# Procurar por métodos widget_* no post_class (se houver)
widgets_pattern = r'(\n\s+def widget_\w+\(.*?\):.*?)(?=\n\s+def|\n\n|\Z)'
widgets = re.findall(widgets_pattern, post_class, re.DOTALL)

# Se encontrou widgets no post_class, significa que eles estão fora da classe. Precisamos movê-los para dentro.
if widgets:
    print("Métodos widget_* encontrados fora da classe. Movendo para dentro...")
    # Remover os widgets do post_class
    for w in widgets:
        post_class = post_class.replace(w, '')
    # Adicionar os widgets ao final da classe (antes do último método)
    # Vamos inserir antes do método _on_closing ou _maximize_window
    last_method_match = re.search(r'(\n\s+def _(?:on_closing|maximize_window)\(.*?\):.*?)(?=\n\s+def|\n\n|\Z)', class_body, re.DOTALL)
    if last_method_match:
        last_method = last_method_match.group(1)
        indented_widgets = '\n'.join('    ' + line for line in '\n'.join(widgets).splitlines())
        class_body = class_body.replace(last_method, indented_widgets + '\n' + last_method)
    else:
        # Se não encontrar, adiciona no final
        class_body += '\n' + '\n'.join('    ' + line for line in '\n'.join(widgets).splitlines())

# 3. Adicionar os métodos apply_config e _restart_app dentro da classe (se não existirem)
if 'def apply_config' not in class_body:
    # Inserir antes do _monitor_loop
    insert_before = 'def _monitor_loop'
    if insert_before in class_body:
        new_methods = """
    def apply_config(self):
        \"\"\"Aplica as configurações de tema, escala e reinicia a interface.\"\"\"
        self._save_config()
        self.update_theme_vars()
        self.apply_ui_scale()
        self.show_toast("Configurações aplicadas. Reinicie o aplicativo para ver todas as alterações.", 3000)
        self.after(1000, self._restart_app)

    def _restart_app(self):
        import sys
        import subprocess
        self.destroy()
        subprocess.Popen([sys.executable, "-m", "core.main"])
        sys.exit()
"""
        class_body = class_body.replace(insert_before, new_methods + '\n    ' + insert_before)
    else:
        class_body += new_methods

# 4. Remover quaisquer definições de função soltas no post_class (o que restar)
#    Agora post_class deve conter apenas o if __name__ == "__main__" e possivelmente lixo.
#    Vamos manter apenas a parte que começa com "if __name__"
if_match = re.search(r'(\nif __name__ == ["\']__main__["\']:.*)', post_class, re.DOTALL)
if if_match:
    post_class = if_match.group(1)
else:
    post_class = ''  # descarta o resto

# 5. Reconstruir o conteúdo
new_content = pre_class + class_body + post_class

# 6. Salvar
with open(file_path, 'w') as f:
    f.write(new_content)

print("✅ Correções aplicadas com sucesso!")
print("Execute: python -m core.main")
