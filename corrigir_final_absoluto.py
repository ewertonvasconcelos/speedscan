#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_final_absoluto")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Expressão regular para encontrar o método _fill_sobre (do início ao fim)
# Vamos capturar desde "def _fill_sobre" até a próxima definição de função no mesmo nível
# O padrão busca: def _fill_sobre(...):, seguido de linhas indentadas, até uma linha que não é indentada e começa com 'def ' ou fim do arquivo
padrao = re.compile(
    r'(def _fill_sobre\(.*?\):.*?)(?=\n\s*def |\n\s*class |\Z)',
    re.DOTALL
)

# Verificar se encontrou
if not padrao.search(conteudo):
    print("Método _fill_sobre não encontrado. Verificando se existe com nome diferente...")
    # Tentar encontrar qualquer método que contenha 'sobre'
    padrao_alt = re.compile(r'(def .*sobre.*?\(.*?\):.*?)(?=\n\s*def |\n\s*class |\Z)', re.DOTALL | re.IGNORECASE)
    match = padrao_alt.search(conteudo)
    if match:
        print(f"Encontrado método alternativo: {match.group(0)[:50]}...")
        # Usar esse match
        metodo_antigo = match.group(1)
    else:
        print("Nenhum método relacionado a 'sobre' encontrado. Abortando.")
        exit(1)
else:
    metodo_antigo = padrao.search(conteudo).group(1)

# Novo método (versão corrigida, sem f-strings)
novo_metodo = '''    def _fill_sobre(self, parent):
        ctk.CTkLabel(parent, text=self._("Sobre o SpeedScan"), font=("Inter",28,"bold"),
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))
        card = ctk.CTkFrame(parent, fg_color=self.light_bg, corner_radius=15, border_width=2, border_color=self.acc_color)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        info = (
            self._("⚡ SpeedScan") + "\\n\\n"
            + self._("Versão") + " " + config.VERSION + "\\n\\n"
            + self._("Desenvolvedor: Ewerton Vasconcelos") + "\\n"
            + self._("Tecnologias: Python, CustomTkinter, psutil") + "\\n"
            + self._("Repositório: github.com/ewertonvasconcelos/speedscan") + "\\n\\n"
            + self._("Este software está em fase de desenvolvimento.") + "\\n\\n"
            + self._("Principais funcionalidades:") + "\\n"
            + self._("• Dashboard com widgets personalizáveis") + "\\n"
            + self._("• Monitoramento de CPU, RAM, disco, GPU e temperatura") + "\\n"
            + self._("• Otimização: cache, swap, turbo e limpeza de navegadores") + "\\n"
            + self._("• Rede: ping, DNS, teste de velocidade, scanner LAN, LANCache") + "\\n"
            + self._("• Diagnóstico de drivers e hardware") + "\\n"
            + self._("• Gerenciador de processos com ações") + "\\n"
            + self._("• Histórico de desempenho com gráficos") + "\\n"
            + self._("• Verificações de segurança (portas, firewall, atualizações)") + "\\n"
            + self._("• IA proativa com sugestões e chat local") + "\\n"
            + self._("• Gerenciador de cookies seletivo") + "\\n"
            + self._("• Lixeira interna para arquivos deletados") + "\\n"
            + self._("• Agendamento automático de tarefas") + "\\n"
            + self._("• Níveis de expertise (Iniciante, Intermediário, Avançado)") + "\\n"
            + self._("• Tooltips explicativos") + "\\n"
            + self._("• Temas personalizáveis") + "\\n\\n"
            + "© 2026 Ewerton Vasconcelos. " + self._("Todos os direitos reservados.")
        )
        label_info = ctk.CTkLabel(card, text=info, font=("Inter",12), justify="left", text_color=self.text_color)
        label_info.pack(pady=20, padx=30, fill="both", expand=True)'''

# Substituir no conteúdo
conteudo_novo = conteudo.replace(metodo_antigo, novo_metodo)

if conteudo_novo == conteudo:
    print("Nenhuma substituição foi feita. O método pode ser diferente.")
else:
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo_novo)
    print("Método _fill_sobre substituído com sucesso.")

print("Execute o programa novamente.")
