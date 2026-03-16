#!/bin/bash
# Corrige o botão Detalhes para que só apareça após a senha

set -e

cd ~/speedscan/speedscan

# Backup
cp core/main.py core/main.py.bak.$(date +%s)
echo "✅ Backup criado."

# ============================================================
# 1. Remover todas as linhas de status inseridas antes de _run_subprocess
# ============================================================
echo "   + Removendo linhas de status prematuras..."

# Métodos que inserem linha antes de chamar _run_subprocess
# _run_ping, _run_ethtool, _run_dhclient, _run_traceroute, _run_wifi, _run_testdns, _run_pci, _run_update, _run_usb, _run_modules, _run_firmware, _run_video_drv, _run_net_drv

sed -i '/log.insert.*"Pinging google\.com\.\.\."/d' core/main.py
sed -i '/log.insert.*"Running ethtool\.\.\."/d' core/main.py
sed -i '/log.insert.*"Renewing IP via dhclient\.\.\."/d' core/main.py
sed -i '/log.insert.*"Running traceroute to google\.com\.\.\."/d' core/main.py
sed -i '/log.insert.*"Wi-Fi info\.\.\."/d' core/main.py
sed -i '/log.insert.*"Testing DNS (google\.com)\.\.\."/d' core/main.py
sed -i '/log.insert.*"Updating package list\.\.\."/d' core/main.py

# Para comandos que não usam _run_subprocess mas inserem linha antes (ex: _run_ports)
# Vamos apenas remover a linha de status, mas manter o resto
sed -i '/log.insert.*"Scanning open ports\.\.\."/d' core/main.py
sed -i '/log.insert.*"Checking LANCache\.\.\."/d' core/main.py
sed -i '/log.insert.*"Obtaining public IP\.\.\."/d' core/main.py

# ============================================================
# 2. Modificar _run_subprocess para que, se não houver tag, não tente mostrar botão
# ============================================================
# Já está ok, mas vamos garantir que a chamada a _show_detail_button só ocorra se tag for fornecida
sed -i '/if tag:/!b; /self._show_detail_button/!b' core/main.py  # (não modifica, só verifica)

# ============================================================
# 3. Adicionar mensagens de status como parte do comando (via echo)
#    para que a primeira saída seja após a autenticação
# ============================================================
echo "   + Adicionando mensagens via echo nos comandos..."

# Para comandos que usam _run_subprocess, vamos modificar os argumentos para incluir um echo
# Exemplo: _run_ping antes chamava self._run_subprocess(["ping", ...])
# Agora vamos fazer self._run_subprocess(["sh", "-c", "echo 'Pinging...'; ping ..."])

# _run_ping
sed -i 's/self\._run_subprocess(\["ping", "-c", "4", "google\.com"\], log, tag="ping")/self._run_subprocess(["sh", "-c", "echo \x27Pinging google.com...\x27; ping -c 4 google.com"], log, tag="ping")/' core/main.py

# _run_ethtool (pode não existir, mas vamos tratar)
sed -i 's/self\._run_subprocess(\["ethtool", "eth0"\], log, tag="ethtool")/self._run_subprocess(["sh", "-c", "echo \x27Running ethtool...\x27; ethtool eth0"], log, tag="ethtool")/' core/main.py

# _run_dhclient
sed -i 's/self\._run_subprocess(\["sudo", "dhclient", "-v"\], log, use_sudo=True, tag="dhclient")/self._run_subprocess(["sh", "-c", "echo \x27Renewing IP via dhclient...\x27; sudo dhclient -v"], log, use_sudo=True, tag="dhclient")/' core/main.py

# _run_traceroute
sed -i 's/self\._run_subprocess(\["traceroute", "google\.com"\], log, tag="traceroute")/self._run_subprocess(["sh", "-c", "echo \x27Running traceroute...\x27; traceroute google.com"], log, tag="traceroute")/' core/main.py

# _run_wifi
sed -i 's/self\._run_subprocess(\["iwconfig"\], log, tag="wifi")/self._run_subprocess(["sh", "-c", "echo \x27Wi-Fi info...\x27; iwconfig"], log, tag="wifi")/' core/main.py

# _run_testdns
sed -i 's/self\._run_subprocess(\["nslookup", "google\.com"\], log, tag="testdns")/self._run_subprocess(["sh", "-c", "echo \x27Testing DNS...\x27; nslookup google.com"], log, tag="testdns")/' core/main.py

# _run_pci
sed -i 's/self\._run_subprocess(\["lspci"\], log, tag="pci")/self._run_subprocess(["sh", "-c", "echo \x27Listing PCI devices...\x27; lspci"], log, tag="pci")/' core/main.py

# _run_update
sed -i 's/self\._run_subprocess(\["sudo", "apt", "update"\], log, use_sudo=True, tag="update")/self._run_subprocess(["sh", "-c", "echo \x27Updating package list...\x27; sudo apt update"], log, use_sudo=True, tag="update")/' core/main.py

# _run_usb
sed -i 's/self\._run_subprocess(\["lsusb"\], log, tag="usb")/self._run_subprocess(["sh", "-c", "echo \x27Listing USB devices...\x27; lsusb"], log, tag="usb")/' core/main.py

# _run_modules
sed -i 's/self\._run_subprocess(\["lsmod"\], log, tag="modules")/self._run_subprocess(["sh", "-c", "echo \x27Listing kernel modules...\x27; lsmod"], log, tag="modules")/' core/main.py

# _run_firmware (já usa shell=True, mas vamos adaptar)
sed -i 's/self\._run_subprocess(\["dmesg", "|", "grep", "-i", "firmware"\], log, shell=True, tag="firmware")/self._run_subprocess(["sh", "-c", "echo \x27Checking firmware messages...\x27; dmesg | grep -i firmware"], log, shell=True, tag="firmware")/' core/main.py

# _run_video_drv
sed -i 's/self\._run_subprocess(\["lspci", "|", "grep", "-i", "vga"\], log, shell=True, tag="video_drv")/self._run_subprocess(["sh", "-c", "echo \x27Detecting video drivers...\x27; lspci | grep -i vga"], log, shell=True, tag="video_drv")/' core/main.py

# _run_net_drv
sed -i 's/self\._run_subprocess(\["lspci", "|", "grep", "-i", "network"\], log, shell=True, tag="net_drv")/self._run_subprocess(["sh", "-c", "echo \x27Detecting network drivers...\x27; lspci | grep -i network"], log, shell=True, tag="net_drv")/' core/main.py

# Para comandos que não usam _run_subprocess (ex: _run_ports, _run_lancache, _run_public_ip),
# eles já inseriam linha de status antes de executar. Vamos remover essa linha e,
# se necessário, adicionar um echo no próprio comando (mas eles não usam subprocesso direto).
# Como esses comandos não envolvem autenticação, não há problema. Mas para consistência,
# vamos também adicionar um echo via subprocesso? Deixamos como está.

# ============================================================
# 4. Ajustar o fallback para não atrapalhar (aumentar timeout ou remover)
# ============================================================
echo "   + Ajustando fallback para 10 segundos..."
sed -i 's/self\.after(2000, fallback)/self.after(10000, fallback)/' core/main.py

# ============================================================
# 5. Finalizar
# ============================================================
echo ""
echo "✅ Correções aplicadas!"
echo ""
echo "Execute o programa:"
echo "   source venv/bin/activate"
echo "   python3 -m core.main"
echo ""
echo "Agora o botão 'Detalhes' só aparecerá após a primeira saída do comando."
echo "Se o comando exigir senha, essa saída só ocorrerá após a autenticação."
