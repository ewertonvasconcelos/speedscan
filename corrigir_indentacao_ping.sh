#!/bin/bash
# Corrige a indentação no método _fill_rede e garante que result_labels seja definido corretamente

set -e  # para o script em caso de erro

echo "Fazendo backup de core/main.py..."
cp core/main.py core/main.py.bak_indent

echo "Corrigindo indentação em _fill_rede..."

# Usar sed para substituir o bloco problemático
# Procuramos por "self.result_labels = {}" e as linhas seguintes
# Vamos reescrever o método _fill_rede com a indentação correta

sed -i '/def _fill_rede/,/^    def/ c\
    def _fill_rede(self, parent):\
        ctk.CTkLabel(parent, text=self._("Rede"), font=("Inter",28,"bold"),\
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))\
        items = [\
            (self._("📟 Ping"), "ping", False),\
            (self._("📀 Cloudflare DNS"), "1.1.1.1", True),\
            (self._("📡 Google DNS"), "8.8.8.8", True),\
            (self._("📡 AdGuard DNS"), "94.140.14.14", True),\
            (self._("🔍 DNS Automático"), "auto", True),\
            (self._("📊 Testar Velocidade"), "speedtest", False),\
            (self._("🕸️ Diagnóstico Placa"), "ethtool", False),\
            (self._("🔍 Renovar IP"), "dhclient", False),\
            (self._("🔓 Portas Abertas"), "ports", False),\
            (self._("🌐 TraceRoute"), "traceroute", False),\
            (self._("📡 Informações Wi-Fi"), "wifi", False),\
            (self._("🔍 Testar DNS"), "testdns", False),\
            (self._("🔎 Scanner LAN"), "lanscan", False),\
            (self._("🗄️ LANCache"), "lancache", False),\
            (self._("📡 Verificar IP Público"), "public_ip", False),\
        ]\
        level = 3\
        if level == 1:\
            items = [item for item in items if item[1] not in ["ports","traceroute","ethtool","dhclient","lanscan","lancache"]]\
        elif level == 2:\
            items = [item for item in items if item[1] not in ["lanscan","lancache"]]\
        ping_labels, result_labels = ui.create_card_grid(parent, items, "net", self.acc_color, self.bg_color, self.text_color, self.run_card_action)\
        self.result_labels = {}\
        if result_labels:\
            self.result_labels.update(result_labels)\
        if ping_labels:\
            self.ping_label = ping_labels[0]\
        btn, log = ui.add_console(parent, "net", self.acc_color, self.toggle_console)\
        btn.pack(anchor="e", padx=5, pady=5)\
        log.pack_forget()\
        self.detail_buttons["net"] = btn\
        self.logs["net"] = log' core/main.py

echo "Correção aplicada. Execute o programa novamente."
