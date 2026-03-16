#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_detalhes")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# 1. Modificar o método toggle_console para que, ao fechar, o botão também suma
inicio_toggle = -1
for i, linha in enumerate(linhas):
    if linha.strip().startswith('def toggle_console'):
        inicio_toggle = i
        break

if inicio_toggle != -1:
    # Encontrar o fim do método
    fim_toggle = inicio_toggle + 1
    while fim_toggle < len(linhas) and (linhas[fim_toggle].startswith(' ' * 4) or linhas[fim_toggle].strip() == ''):
        fim_toggle += 1
    # Substituir pelo novo método
    novo_toggle = [
        '    def toggle_console(self, tag):\n',
        '        print(f"DEBUG toggle_console: tag={tag}")\n',
        '        btn = self.detail_buttons.get(tag)\n',
        '        log = self.logs.get(tag)\n',
        '        if not btn or not log:\n',
        '            return\n',
        '        if self.consoles_visible.get(tag, False):\n',
        '            log.pack_forget()\n',
        '            btn.pack_forget()  # esconde o botão também\n',
        '            self.consoles_visible[tag] = False\n',
        '        else:\n',
        '            log.pack(fill="x", padx=5, before=btn)\n',
        '            btn.configure(text="Detalhes ▲")\n',
        '            self.consoles_visible[tag] = True\n',
    ]
    linhas[inicio_toggle:fim_toggle] = novo_toggle
    print("Método toggle_console atualizado.")
else:
    print("Método toggle_console não encontrado.")

# 2. Modificar _after_command para que, ao mostrar o botão, ele tenha a seta para baixo
# e também garantir que o botão esteja oculto inicialmente (já está com pack_forget)
# Vamos adicionar a configuração do texto antes de mostrar
for i, linha in enumerate(linhas):
    if linha.strip().startswith('def _after_command'):
        inicio = i
        # Encontrar o fim
        fim = inicio + 1
        while fim < len(linhas) and (linhas[fim].startswith(' ' * 4) or linhas[fim].strip() == ''):
            fim += 1
        # Substituir pelo novo método
        novo_after = [
            '    def _after_command(self, tag, log):\n',
            '        """Verifica o tamanho do log e decide se mostra o botão detalhes."""\n',
            '        # Obter o conteúdo do log\n',
            '        conteudo = log.get("1.0", "end-1c")\n',
            '        if len(conteudo) > 200:\n',
            '            # Mostrar botão com seta para baixo\n',
            '            btn = self.detail_buttons.get(tag)\n',
            '            if btn:\n',
            '                btn.configure(text="Detalhes ▼")\n',
            '                if not btn.winfo_ismapped():\n',
            '                    btn.pack(anchor="e", padx=5, pady=5)\n',
            '        # Se for curto, não faz nada (botão permanece oculto)\n',
        ]
        linhas[inicio:fim] = novo_after
        print("Método _after_command atualizado.")
        break
else:
    print("Método _after_command não encontrado. Verifique se ele existe.")

# 3. Garantir que os botões sejam criados com o texto inicial "Detalhes ▼"
# e que já iniciem ocultos (pack_forget). Isso já está nos _fill_*, mas vamos
# assegurar que o texto esteja correto. Não precisamos modificar, pois os _fill_*
# já fazem pack_forget, e o texto é definido em ui.add_console. Se quisermos
# que o texto inicial seja "Detalhes ▼", podemos alterar ui.add_console,
# mas isso já foi feito em scripts anteriores? Vamos manter como está.

# 4. Salvar o arquivo
with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("Correções aplicadas. Execute o programa novamente.")
