#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_sobre")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Encontrar o método _fill_sobre
inicio = -1
for i, linha in enumerate(linhas):
    if linha.strip().startswith('def _fill_sobre'):
        inicio = i
        break

if inicio == -1:
    print("Método _fill_sobre não encontrado.")
    exit(1)

# Encontrar o final do método
fim = inicio + 1
while fim < len(linhas) and (linhas[fim].startswith(' ' * 4) or linhas[fim].strip() == ''):
    fim += 1

# Nova versão do método com chaves escapadas
novo_metodo = [
    '    def _fill_sobre(self, parent):\n',
    '        ctk.CTkLabel(parent, text=self._("Sobre o SpeedScan"), font=("Inter",28,"bold"),\n',
    '                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))\n',
    '        card = ctk.CTkFrame(parent, fg_color=self.light_bg, corner_radius=15, border_width=2, border_color=self.acc_color)\n',
    '        card.pack(fill="both", expand=True, padx=20, pady=10)\n',
    '        info = f"""\n',
    '{self._("⚡ SpeedScan")}\n',
    '\n',
    '{self._("Versão")} {config.VERSION}\n',
    '\n',
    '{self._("Desenvolvedor: Ewerton Vasconcelos")}\n',
    '{self._("Tecnologias: Python, CustomTkinter, psutil")}\n',
    '{self._("Repositório: github.com/ewertonvasconcelos/speedscan")}\n',
    '\n',
    '{self._("Este software está em fase de desenvolvimento.")}\n',
    '\n',
    '{self._("Principais funcionalidades:")}\n',
    '{self._("• Dashboard com widgets personalizáveis")}\n',
    '{self._("• Monitoramento de CPU, RAM, disco, GPU e temperatura")}\n',
    '{self._("• Otimização: cache, swap, turbo e limpeza de navegadores")}\n',
    '{self._("• Rede: ping, DNS, teste de velocidade, scanner LAN, LANCache")}\n',
    '{self._("• Diagnóstico de drivers e hardware")}\n',
    '{self._("• Gerenciador de processos com ações")}\n',
    '{self._("• Histórico de desempenho com gráficos")}\n',
    '{self._("• Verificações de segurança (portas, firewall, atualizações)")}\n',
    '{self._("• IA proativa com sugestões e chat local")}\n',
    '{self._("• Gerenciador de cookies seletivo")}\n',
    '{self._("• Lixeira interna para arquivos deletados")}\n',
    '{self._("• Agendamento automático de tarefas")}\n',
    '{self._("• Níveis de expertise (Iniciante, Intermediário, Avançado)")}\n',
    '{self._("• Tooltips explicativos")}\n',
    '{self._("• Temas personalizáveis")}\n',
    '\n',
    '\\u00a9 2026 Ewerton Vasconcelos. {self._("Todos os direitos reservados.")}"""\n',
    '        label_info = ctk.CTkLabel(card, text=info, font=("Inter",12), justify="left", text_color=self.text_color)\n',
    '        label_info.pack(pady=20, padx=30, fill="both", expand=True)\n',
]

# Substituir
linhas[inicio:fim] = novo_metodo

with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("Método _fill_sobre corrigido.")
