#!/bin/bash
# Correção mínima: botão Detalhes e traduções

set -e

cd ~/speedscan/speedscan

# Backup do main.py atual (caso algo dê errado)
cp core/main.py core/main.py.bak.minimo.$(date +%s)
echo "✅ Backup do main.py criado."

# ============================================================
# 1. Adicionar método _show_detail_button (se não existir)
# ============================================================
if ! grep -q "def _show_detail_button" core/main.py; then
    sed -i '/def run_card_action/i \    def _show_detail_button(self, tag):\n        btn = self.detail_buttons.get(tag)\n        if btn and not btn.winfo_ismapped():\n            btn.pack(side="right", anchor="e", padx=10, pady=5)\n' core/main.py
    echo "   + _show_detail_button adicionado."
fi

# ============================================================
# 2. Modificar _run_subprocess para chamar _show_detail_button na primeira saída
# ============================================================
# Primeiro, garantir que a variável _btn_shown exista
if ! grep -q "self._btn_shown" core/main.py; then
    sed -i '/self.consoles_visible = {}/a \        self._btn_shown = False' core/main.py
fi

# Reseta _btn_shown em run_card_action
sed -i '/def run_card_action/,/threading.Thread/ {
    /log.delete/a \        self._btn_shown = False
}' core/main.py

# Adiciona chamada em _run_subprocess
sed -i '/for line in proc.stdout:/i \            if not self._btn_shown:\n                self._show_detail_button(tag)\n                self._btn_shown = True' core/main.py

# ============================================================
# 3. Ajustar toggle_console para que ao fechar, o botão suma
# ============================================================
sed -i '/def toggle_console/,/^    def/ {
    /def toggle_console/,/^    def/ c\
    def toggle_console(self, tag):\n\
        btn = self.detail_buttons.get(tag)\n\
        log = self.logs.get(tag)\n\
        if not btn or not log:\n\
            return\n\
        if self.consoles_visible.get(tag, False):\n\
            log.pack_forget()\n\
            btn.pack_forget()\n\
            btn.configure(text=self._("Details ▼"))\n\
            self.consoles_visible[tag] = False\n\
        else:\n\
            log.pack(fill="x", expand=True, padx=5, before=btn)\n\
            btn.configure(text=self._("Hide Details ▲"))\n\
            self.consoles_visible[tag] = True
}' core/main.py

echo "✅ Botão ajustado."

# ============================================================
# 4. Adaptar comandos para incluir echo (garantir saída)
# ============================================================
echo "   + Adaptando comandos..."
sed -i 's/self\._run_subprocess(\["ping", "-c", "4", "google\.com"\], log, tag="ping")/self._run_subprocess(["sh", "-c", "echo \x27Pinging google.com...\x27; ping -c 4 google.com"], log, tag="ping")/' core/main.py
sed -i 's/self\._run_subprocess(\["ethtool", "eth0"\], log, tag="ethtool")/self._run_subprocess(["sh", "-c", "echo \x27Running ethtool...\x27; ethtool eth0"], log, tag="ethtool")/' core/main.py
sed -i 's/self\._run_subprocess(\["sudo", "dhclient", "-v"\], log, use_sudo=True, tag="dhclient")/self._run_subprocess(["sh", "-c", "echo \x27Renewing IP via dhclient...\x27; sudo dhclient -v"], log, use_sudo=True, tag="dhclient")/' core/main.py
sed -i 's/self\._run_subprocess(\["traceroute", "google\.com"\], log, tag="traceroute")/self._run_subprocess(["sh", "-c", "echo \x27Running traceroute...\x27; traceroute google.com"], log, tag="traceroute")/' core/main.py
sed -i 's/self\._run_subprocess(\["iwconfig"\], log, tag="wifi")/self._run_subprocess(["sh", "-c", "echo \x27Wi-Fi info...\x27; iwconfig"], log, tag="wifi")/' core/main.py
sed -i 's/self\._run_subprocess(\["nslookup", "google\.com"\], log, tag="testdns")/self._run_subprocess(["sh", "-c", "echo \x27Testing DNS...\x27; nslookup google.com"], log, tag="testdns")/' core/main.py
sed -i 's/self\._run_subprocess(\["lspci"\], log, tag="pci")/self._run_subprocess(["sh", "-c", "echo \x27Listing PCI devices...\x27; lspci"], log, tag="pci")/' core/main.py
sed -i 's/self\._run_subprocess(\["sudo", "apt", "update"\], log, use_sudo=True, tag="update")/self._run_subprocess(["sh", "-c", "echo \x27Updating package list...\x27; sudo apt update"], log, use_sudo=True, tag="update")/' core/main.py
sed -i 's/self\._run_subprocess(\["lsusb"\], log, tag="usb")/self._run_subprocess(["sh", "-c", "echo \x27Listing USB devices...\x27; lsusb"], log, tag="usb")/' core/main.py
sed -i 's/self\._run_subprocess(\["lsmod"\], log, tag="modules")/self._run_subprocess(["sh", "-c", "echo \x27Listing kernel modules...\x27; lsmod"], log, tag="modules")/' core/main.py
sed -i 's/self\._run_subprocess(\["dmesg", "|", "grep", "-i", "firmware"\], log, shell=True, tag="firmware")/self._run_subprocess(["sh", "-c", "echo \x27Checking firmware messages...\x27; dmesg | grep -i firmware"], log, shell=True, tag="firmware")/' core/main.py
sed -i 's/self\._run_subprocess(\["lspci", "|", "grep", "-i", "vga"\], log, shell=True, tag="video_drv")/self._run_subprocess(["sh", "-c", "echo \x27Detecting video drivers...\x27; lspci | grep -i vga"], log, shell=True, tag="video_drv")/' core/main.py
sed -i 's/self\._run_subprocess(\["lspci", "|", "grep", "-i", "network"\], log, shell=True, tag="net_drv")/self._run_subprocess(["sh", "-c", "echo \x27Detecting network drivers...\x27; lspci | grep -i network"], log, shell=True, tag="net_drv")/' core/main.py

echo "✅ Comandos adaptados."

# ============================================================
# 5. Recompilar traduções (já devem estar prontas)
# ============================================================
echo "🌐 Recompilando traduções..."
msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo 2>/dev/null || true
msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo 2>/dev/null || true
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo 2>/dev/null || true
echo "✅ Traduções recompiladas."

echo ""
echo "🎉 Correções mínimas aplicadas!"
echo "Agora execute o programa:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
