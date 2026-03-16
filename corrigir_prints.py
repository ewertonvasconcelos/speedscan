#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_prints")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Função para inserir linha após um padrão, respeitando indentação
def inserir_linha_apos(linhas, padrao, nova_linha, indentacao_base=8):
    for i, linha in enumerate(linhas):
        if padrao in linha:
            # Determinar a indentação da linha alvo
            espacos = len(linha) - len(linha.lstrip())
            # A nova linha deve ter a mesma indentação + 4 (ou o padrão)
            # Vamos adicionar a indentação da linha + 4
            indent = ' ' * (espacos + 4)
            linhas.insert(i+1, indent + nova_linha + '\n')
            print(f"Inserido após linha {i+1}: {nova_linha}")
            return True
    return False

# 1. Print em run_card_action
inserir_linha_apos(linhas, 'def run_card_action(self, cmd, tag, is_dns):',
                   'print(f"DEBUG: run_card_action chamado com cmd={cmd}, tag={tag}, is_dns={is_dns}")')

# 2. Print em _execute_command
inserir_linha_apos(linhas, 'def _execute_command(self, cmd, log, tag, is_dns):',
                   'print(f"DEBUG: _execute_command: cmd={cmd}, tag={tag}, is_dns={is_dns}")')

# 3. Print em _run_ping (início)
inserir_linha_apos(linhas, 'def _run_ping(self, log, tag=None):',
                   'print("DEBUG: _run_ping iniciado")')

# 4. Print do tamanho da saída (dentro do try, após output = result.stdout)
# Vamos procurar a linha 'output = result.stdout' e inserir após
for i, linha in enumerate(linhas):
    if 'output = result.stdout' in linha:
        espacos = len(linha) - len(linha.lstrip())
        indent = ' ' * (espacos + 4)
        linhas.insert(i+1, indent + 'print(f"DEBUG: Tamanho da saída do ping: {len(output)} caracteres")\n')
        print("Inserido print de tamanho da saída.")
        break

# 5. Print quando mostra o botão (dentro de if len(output) > 200:)
# Vamos procurar a linha 'if len(output) > 200:' e inserir dentro do bloco
for i, linha in enumerate(linhas):
    if 'if len(output) > 200:' in linha:
        espacos = len(linha) - len(linha.lstrip())
        indent = ' ' * (espacos + 4)
        # Inserir após a linha, mas precisamos garantir que seja antes do bloco
        # Vamos inserir na próxima linha, que já deve estar indentada
        # Mas vamos inserir imediatamente após, com a indentação correta
        linhas.insert(i+1, indent + 'print("DEBUG: Saída longa, mostrando botão Detalhes")\n')
        print("Inserido print de botão.")
        break

# 6. Print em _after_command
inserir_linha_apos(linhas, 'def _after_command(self, tag, log):',
                   'print(f"DEBUG: _after_command: tag={tag}, tamanho do log = {len(log.get(\\"1.0\\", \\"end-1c\\"))}")')

# 7. Print em toggle_console
inserir_linha_apos(linhas, 'def toggle_console(self, tag):',
                   'print(f"DEBUG: toggle_console chamado com tag={tag}, visível={self.consoles_visible.get(tag)}")')

with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("Prints inseridos com segurança. Execute o programa agora.")
