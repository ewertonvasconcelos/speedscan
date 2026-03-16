#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_copyright")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Substituir o caractere © por \u00a9 (escape Unicode) na f-string
# Encontrar a linha problemática: "© 2026 Ewerton Vasconcelos."
# Padrão: © 2026 Ewerton Vasconcelos.
padrao = r'© 2026 Ewerton Vasconcelos\.'
substituicao = r'\\u00a9 2026 Ewerton Vasconcelos.'

# Aplicar a substituição
novo_conteudo = re.sub(padrao, substituicao, conteudo, flags=re.UNICODE)

# Verificar se houve mudança
if novo_conteudo != conteudo:
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(novo_conteudo)
    print("Caractere © substituído por \\u00a9.")
else:
    print("Caractere não encontrado. Verificando manualmente...")

print("Pronto. Execute o programa novamente.")
