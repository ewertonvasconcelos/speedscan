#!/bin/bash
# Corrige: Aba Drivers e comportamento do botão Detalhes (oculto inicialmente, setas)

echo "Aplicando correções..."

# Backup
cp core/main.py core/main.py.bak_drivers

# 1. Garantir que o método _fill_drivers existe e está correto
# Se não existir, adiciona. Se existir, substitui pela versão correta.

if grep -q "def _fill_drivers" core/main.py; then
    echo "Método _fill_drivers encontrado. Substituindo..."
    sed -i '/def _fill_drivers/,/^    def/ c\
    def _fill_drivers(self, parent):\
        ctk.CTkLabel(parent, text=self._("Drivers"), font=("Inter",28,"bold"),\
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))\
        items = [\
            (self._("📮 PCI (Vídeo/Rede)"), "pci", False),\
            (self._("🔧 Atualizar Sistema"), "update", False),\
            (self._("🖥️ USB Conectados"), "usb", False),\
            (self._("📟 Módulos Kernel"), "modules", False),\
            (self._("⚙️ CPU Detalhada"), "cpu_info", False),\
            (self._("⚙️ Erros de Firmware"), "firmware", False),\
            (self._("📮 Drivers de Vídeo"), "video_drv", False),\
            (self._("🔍 Drivers de Rede"), "net_drv", False),\
            (self._("🔍 Atualizações Automáticas"), "auto_update", False),\
        ]\
        level = 3\
        if level == 1:\
            items = [item for item in items if item[1] not in ["modules","cpu_info","firmware","video_drv","net_drv","auto_update"]]\
        elif level == 2:\
            items = [item for item in items if item[1] not in ["video_drv","net_drv","auto_update"]]\
        ui.create_card_grid(parent, items, "drv", self.acc_color, self.bg_color, self.text_color, self.run_card_action)\
        btn, log = ui.add_console(parent, "drv", self.acc_color, self.toggle_console)\
        btn.pack_forget()  # Inicia oculto\
        log.pack_forget()\
        self.detail_buttons["drv"] = btn\
        self.logs["drv"] = log' core/main.py
else
    echo "Método _fill_drivers não encontrado. Inserindo..."
    # Inserir após _fill_rede (linha aproximada)
    sed -i '/def _fill_rede/,/^    def/ a\
    def _fill_drivers(self, parent):\
        ctk.CTkLabel(parent, text=self._("Drivers"), font=("Inter",28,"bold"),\
                     text_color=self.acc_color).pack(anchor="center", pady=(0,20))\
        items = [\
            (self._("📮 PCI (Vídeo/Rede)"), "pci", False),\
            (self._("🔧 Atualizar Sistema"), "update", False),\
            (self._("🖥️ USB Conectados"), "usb", False),\
            (self._("📟 Módulos Kernel"), "modules", False),\
            (self._("⚙️ CPU Detalhada"), "cpu_info", False),\
            (self._("⚙️ Erros de Firmware"), "firmware", False),\
            (self._("📮 Drivers de Vídeo"), "video_drv", False),\
            (self._("🔍 Drivers de Rede"), "net_drv", False),\
            (self._("🔍 Atualizações Automáticas"), "auto_update", False),\
        ]\
        level = 3\
        if level == 1:\
            items = [item for item in items if item[1] not in ["modules","cpu_info","firmware","video_drv","net_drv","auto_update"]]\
        elif level == 2:\
            items = [item for item in items if item[1] not in ["video_drv","net_drv","auto_update"]]\
        ui.create_card_grid(parent, items, "drv", self.acc_color, self.bg_color, self.text_color, self.run_card_action)\
        btn, log = ui.add_console(parent, "drv", self.acc_color, self.toggle_console)\
        btn.pack_forget()\
        log.pack_forget()\
        self.detail_buttons["drv"] = btn\
        self.logs["drv"] = log' core/main.py
fi

# 2. Modificar os métodos _fill_* para que os botões detalhes iniciem ocultos (pack_forget)
# Já fizemos para drv, agora para ot, net, sec
sed -i 's/btn.pack(anchor="e", padx=5, pady=5)/btn.pack_forget()/g' core/main.py

# 3. Modificar o método _execute_command para que após a execução, se a saída for longa, mostre o botão
# Já temos a modificação no _run_ping, mas precisamos aplicá-la a todos os métodos que produzem saída.
# Vamos adicionar no _execute_command uma lógica que, após chamar o método, verifica o tamanho do log.
# Como é complexo, faremos por enquanto apenas para ping. Depois estendemos.

# 4. Modificar toggle_console para usar setas
sed -i '/def toggle_console/,/^    def/ c\
    def toggle_console(self, tag):\
        print(f"DEBUG toggle_console: tag={tag}")\
        btn = self.detail_buttons.get(tag)\
        log = self.logs.get(tag)\
        if not btn or not log:\
            return\
        if self.consoles_visible.get(tag, False):\
            log.pack_forget()\
            btn.configure(text="Detalhes ▼")\
            self.consoles_visible[tag] = False\
        else:\
            log.pack(fill="x", padx=5, before=btn)\
            btn.configure(text="Detalhes ▲")\
            self.consoles_visible[tag] = True' core/main.py

echo "Correções aplicadas. Execute o programa."
