#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_final")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r') as f:
    linhas = f.readlines()

# Encontrar a classe SpeedScan
inicio_classe = -1
for i, linha in enumerate(linhas):
    if linha.strip().startswith('class SpeedScan'):
        inicio_classe = i
        break

if inicio_classe == -1:
    print("Classe SpeedScan não encontrada.")
    exit(1)

# Lista de métodos que precisam ser verificados/corrigidos
metodos = [
    '_fill_otimizacao',
    '_fill_rede',
    '_fill_drivers',
    '_fill_seguranca'
]

# Função para verificar se um método existe e retornar sua posição
def encontrar_metodo(nome):
    for i in range(inicio_classe, len(linhas)):
        if re.match(rf'    def {nome}\(', linhas[i]):
            return i
    return -1

# Garantir que os métodos existam e tenham o conteúdo correto
# Vamos primeiro remover os métodos existentes (se houver) e reinserir com a indentação correta
# Mas é mais seguro sobrescrever apenas se necessário.

# Método _fill_drivers corrigido (com botão oculto)
novo_drivers = [
    '    def _fill_drivers(self, parent):\n',
    '        ctk.CTkLabel(parent, text=self._("Drivers"), font=("Inter",28,"bold"),\n',
    '                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))\n',
    '        items = [\n',
    '            (self._("📮 PCI (Vídeo/Rede)"), "pci", False),\n',
    '            (self._("🔧 Atualizar Sistema"), "update", False),\n',
    '            (self._("🖥️ USB Conectados"), "usb", False),\n',
    '            (self._("📟 Módulos Kernel"), "modules", False),\n',
    '            (self._("⚙️ CPU Detalhada"), "cpu_info", False),\n',
    '            (self._("⚙️ Erros de Firmware"), "firmware", False),\n',
    '            (self._("📮 Drivers de Vídeo"), "video_drv", False),\n',
    '            (self._("🔍 Drivers de Rede"), "net_drv", False),\n',
    '            (self._("🔍 Atualizações Automáticas"), "auto_update", False),\n',
    '        ]\n',
    '        level = 3\n',
    '        if level == 1:\n',
    '            items = [item for item in items if item[1] not in ["modules","cpu_info","firmware","video_drv","net_drv","auto_update"]]\n',
    '        elif level == 2:\n',
    '            items = [item for item in items if item[1] not in ["video_drv","net_drv","auto_update"]]\n',
    '        ui.create_card_grid(parent, items, "drv", self.acc_color, self.bg_color, self.text_color, self.run_card_action)\n',
    '        btn, log = ui.add_console(parent, "drv", self.acc_color, self.toggle_console)\n',
    '        btn.pack_forget()\n',
    '        log.pack_forget()\n',
    '        self.detail_buttons["drv"] = btn\n',
    '        self.logs["drv"] = log\n',
]

# Método _fill_rede corrigido (com botão oculto)
novo_rede = [
    '    def _fill_rede(self, parent):\n',
    '        ctk.CTkLabel(parent, text=self._("Rede"), font=("Inter",28,"bold"),\n',
    '                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))\n',
    '        items = [\n',
    '            (self._("📟 Ping"), "ping", False),\n',
    '            (self._("📀 Cloudflare DNS"), "1.1.1.1", True),\n',
    '            (self._("📡 Google DNS"), "8.8.8.8", True),\n',
    '            (self._("📡 AdGuard DNS"), "94.140.14.14", True),\n',
    '            (self._("🔍 DNS Automático"), "auto", True),\n',
    '            (self._("📊 Testar Velocidade"), "speedtest", False),\n',
    '            (self._("🕸️ Diagnóstico Placa"), "ethtool", False),\n',
    '            (self._("🔍 Renovar IP"), "dhclient", False),\n',
    '            (self._("🔓 Portas Abertas"), "ports", False),\n',
    '            (self._("🌐 TraceRoute"), "traceroute", False),\n',
    '            (self._("📡 Informações Wi-Fi"), "wifi", False),\n',
    '            (self._("🔍 Testar DNS"), "testdns", False),\n',
    '            (self._("🔎 Scanner LAN"), "lanscan", False),\n',
    '            (self._("🗄️ LANCache"), "lancache", False),\n',
    '            (self._("📡 Verificar IP Público"), "public_ip", False),\n',
    '        ]\n',
    '        level = 3\n',
    '        if level == 1:\n',
    '            items = [item for item in items if item[1] not in ["ports","traceroute","ethtool","dhclient","lanscan","lancache"]]\n',
    '        elif level == 2:\n',
    '            items = [item for item in items if item[1] not in ["lanscan","lancache"]]\n',
    '        ping_labels, result_labels = ui.create_card_grid(parent, items, "net", self.acc_color, self.bg_color, self.text_color, self.run_card_action)\n',
    '        self.result_labels = {}\n',
    '        if result_labels:\n',
    '            self.result_labels.update(result_labels)\n',
    '        if ping_labels:\n',
    '            self.ping_label = ping_labels[0]\n',
    '        btn, log = ui.add_console(parent, "net", self.acc_color, self.toggle_console)\n',
    '        btn.pack_forget()\n',
    '        log.pack_forget()\n',
    '        self.detail_buttons["net"] = btn\n',
    '        self.logs["net"] = log\n',
]

# Método _fill_otimizacao corrigido (com botão oculto)
novo_otimizacao = [
    '    def _fill_otimizacao(self, parent):\n',
    '        ctk.CTkLabel(parent, text=self._("Otimização"), font=("Inter",28,"bold"),\n',
    '                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))\n',
    '        items = [\n',
    '            (self._("🗹 Limpeza de Cache"), "cache", False),\n',
    '            (self._("🗄 Reset de Swap"), "swap", False),\n',
    '            (self._("🔍 Verificar Erros"), "check", False),\n',
    '            (self._("🔧 Modo Turbo"), "turbo", False),\n',
    '            (self._("Steam"), "steam", False),\n',
    '            (self._("Lutris"), "lutris", False),\n',
    '            (self._("Heroic Launcher"), "heroic", False),\n',
    '            (self._("Bottles"), "bottles", False),\n',
    '            (self._("Wine"), "wine", False),\n',
    '            (self._("MangoHud"), "mangohud", False),\n',
    '            (self._("Governor"), "governer", False),\n',
    '            (self._("📮 Emulador Dolphin"), "dolphin", False),\n',
    '            (self._("🗑 Limpeza de Navegadores"), "browsers", False),\n',
    '            (self._("⚙️ Gerenciar Serviços"), "services", False),\n',
    '            (self._("📋 Análise de Logs"), "logs", False),\n',
    '            (self._("🗑️ Gerenciar Cookies"), "cookies", False),\n',
    '            (self._("🔧 Otimizar SSD (TRIM)"), "trim", False),\n',
    '            (self._("🗄 Reparar Pacotes Quebrados"), "fix_broken", False),\n',
    '        ]\n',
    '        level = 3\n',
    '        if level == 1:\n',
    '            items = [item for item in items if item[1] not in ["services","logs","cookies","trim","fix_broken"]]\n',
    '        elif level == 2:\n',
    '            items = [item for item in items if item[1] not in ["logs","cookies"]]\n',
    '        ui.create_card_grid(parent, items, "ot", self.acc_color, self.bg_color, self.text_color, self.run_card_action)\n',
    '        btn, log = ui.add_console(parent, "ot", self.acc_color, self.toggle_console)\n',
    '        btn.pack_forget()\n',
    '        log.pack_forget()\n',
    '        self.detail_buttons["ot"] = btn\n',
    '        self.logs["ot"] = log\n',
]

# Método _fill_seguranca corrigido (com botão oculto)
novo_seguranca = [
    '    def _fill_seguranca(self, parent):\n',
    '        ctk.CTkLabel(parent, text=self._("Segurança do Sistema"), font=("Inter",28,"bold"),\n',
    '                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))\n',
    '        items = [\n',
    '            (self._("🛡️ Portas Abertas"), "ports", False),\n',
    '            (self._("🛡️ Firewall"), "firewall", False),\n',
    '            (self._("🗄 Atualizações de Segurança"), "sec_updates", False),\n',
    '        ]\n',
    '        level = self.config.get("expert_level",1)\n',
    '        if level == 1:\n',
    '            items = [item for item in items if item[1] not in ["ports","sec_updates"]]\n',
    '        ui.create_card_grid(parent, items, "sec", self.acc_color, self.bg_color, self.text_color, self.run_card_action)\n',
    '        btn, log = ui.add_console(parent, "sec", self.acc_color, self.toggle_console)\n',
    '        btn.pack_forget()\n',
    '        log.pack_forget()\n',
    '        self.detail_buttons["sec"] = btn\n',
    '        self.logs["sec"] = log\n',
]

# Substituir os métodos existentes pelos novos
# Primeiro, remover os métodos antigos (encontrar e marcar para exclusão)
# Vamos construir uma nova lista de linhas, substituindo os blocos

nova_lista = []
i = 0
while i < len(linhas):
    linha = linhas[i]
    # Verifica se é um método que queremos substituir
    if re.match(r'    def _fill_(otimizacao|rede|drivers|seguranca)\(', linha):
        # Pular até o final do método (próxima definição no mesmo nível)
        metodo = linha.split('def ')[1].split('(')[0]
        print(f"Substituindo método {metodo}")
        i += 1
        while i < len(linhas) and not (linhas[i].strip() and not linhas[i].startswith(' ' * 4) and not linhas[i].startswith('\n')):
            i += 1
        # Inserir o novo método correspondente
        if metodo == '_fill_otimizacao':
            nova_lista.extend(novo_otimizacao)
        elif metodo == '_fill_rede':
            nova_lista.extend(novo_rede)
        elif metodo == '_fill_drivers':
            nova_lista.extend(novo_drivers)
        elif metodo == '_fill_seguranca':
            nova_lista.extend(novo_seguranca)
        continue
    else:
        nova_lista.append(linha)
        i += 1

# Agora, substituir o método toggle_console para usar setas
# Encontrar e substituir
for i, linha in enumerate(nova_lista):
    if linha.strip().startswith('def toggle_console'):
        inicio = i
        fim = i + 1
        while fim < len(nova_lista) and (nova_lista[fim].startswith(' ' * 4) or nova_lista[fim].strip() == ''):
            fim += 1
        novo_toggle = [
            '    def toggle_console(self, tag):\n',
            '        print(f"DEBUG toggle_console: tag={tag}")\n',
            '        btn = self.detail_buttons.get(tag)\n',
            '        log = self.logs.get(tag)\n',
            '        if not btn or not log:\n',
            '            return\n',
            '        if self.consoles_visible.get(tag, False):\n',
            '            log.pack_forget()\n',
            '            btn.configure(text="Detalhes ▼")\n',
            '            self.consoles_visible[tag] = False\n',
            '        else:\n',
            '            log.pack(fill="x", padx=5, before=btn)\n',
            '            btn.configure(text="Detalhes ▲")\n',
            '            self.consoles_visible[tag] = True\n',
        ]
        nova_lista[inicio:fim] = novo_toggle
        print("Método toggle_console substituído.")
        break

# Escrever o arquivo
with open(arquivo, 'w') as f:
    f.writelines(nova_lista)

print("Arquivo reescrito. Execute o programa.")
