#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_after_indent")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Procurar pelo início do método _after_command
inicio = -1
for i, linha in enumerate(linhas):
    if linha.strip().startswith('def _after_command'):
        inicio = i
        break

if inicio == -1:
    print("Método _after_command não encontrado.")
    exit(1)

# Encontrar o fim do método (próxima definição de função)
fim = inicio + 1
while fim < len(linhas) and not (linhas[fim].strip().startswith('def ') and linhas[fim][0] != ' '):
    fim += 1

# Novo método com indentação correta
novo_metodo = [
    '    def _after_command(self, tag, log):\n',
    '        """Verifica o tamanho do log e decide se mostra o botão detalhes."""\n',
    '        conteudo = log.get("1.0", "end-1c")\n',
    '        print(f"DEBUG _after_command: tag={tag}, tamanho={len(conteudo)}")\n',
    '        if len(conteudo) > 200:\n',
    '            btn = self.detail_buttons.get(tag)\n',
    '            if btn:\n',
    '                btn.configure(text="Detalhes ▼")\n',
    '                if not btn.winfo_ismapped():\n',
    '                    btn.pack(anchor="e", padx=5, pady=5)\n',
]

# Substituir
linhas[inicio:fim] = novo_metodo

with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("Método _after_command corrigido com indentação adequada.")
