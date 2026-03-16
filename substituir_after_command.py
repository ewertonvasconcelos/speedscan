#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_after")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Encontrar o método _after_command
padrao = r'(def _after_command\(self, tag, log\):.*?)(?=\n\s*def)'
match = re.search(padrao, conteudo, re.DOTALL)
if match:
    metodo_antigo = match.group(1)
    novo_metodo = '''    def _after_command(self, tag, log):
        """Verifica o tamanho do log e decide se mostra o botão detalhes."""
        conteudo = log.get("1.0", "end-1c")
        print(f"DEBUG _after_command: tag={tag}, tamanho={len(conteudo)}")
        if len(conteudo) > 200:
            btn = self.detail_buttons.get(tag)
            if btn:
                btn.configure(text="Detalhes ▼")
                if not btn.winfo_ismapped():
                    btn.pack(anchor="e", padx=5, pady=5)'''
    conteudo = conteudo.replace(metodo_antigo, novo_metodo)
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print("Método _after_command substituído com sucesso.")
else:
    print("Método _after_command não encontrado.")
