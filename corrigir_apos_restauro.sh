#!/bin/bash
# Aplica correções após restaurar backup funcional

set -e

cd ~/speedscan/speedscan

echo "🔧 Aplicando correções leves..."

# Backup do main.py atual (caso queira reverter)
cp core/main.py core/main.py.bak.apos_restauro

# ============================================================
# 1. Modificar comandos para incluir echo (garante que o botão só apareça após saída real)
# ============================================================
echo "   + Adaptando comandos para usar echo..."

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

# ============================================================
# 2. Recriar traduções básicas (sem duplicatas)
# ============================================================
echo "   + Recriando arquivos .po com traduções básicas..."

rm -rf locale
mkdir -p locale/pt_BR/LC_MESSAGES locale/en_US/LC_MESSAGES locale/es_ES/LC_MESSAGES

# pt_BR
cat > locale/pt_BR/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: pt_BR\n"

msgid "Dashboard"
msgstr "Painel"

msgid "Network"
msgstr "Rede"

msgid "Optimization"
msgstr "Otimização"

msgid "Drivers"
msgstr "Drivers"

msgid "Process Manager"
msgstr "Gerenciador de Processos"

msgid "Historical Performance"
msgstr "Desempenho Histórico"

msgid "System Security"
msgstr "Segurança do Sistema"

msgid "AI Agent"
msgstr "Agente IA"

msgid "Settings"
msgstr "Configurações"

msgid "About"
msgstr "Sobre"

msgid "Windows Cleaner"
msgstr "Limpeza do Windows"
EOF

# en_US
cat > locale/en_US/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: en_US\n"

msgid "Dashboard"
msgstr "Dashboard"

msgid "Network"
msgstr "Network"

msgid "Optimization"
msgstr "Optimization"

msgid "Drivers"
msgstr "Drivers"

msgid "Process Manager"
msgstr "Process Manager"

msgid "Historical Performance"
msgstr "Historical Performance"

msgid "System Security"
msgstr "System Security"

msgid "AI Agent"
msgstr "AI Agent"

msgid "Settings"
msgstr "Settings"

msgid "About"
msgstr "About"

msgid "Windows Cleaner"
msgstr "Windows Cleaner"
EOF

# es_ES
cat > locale/es_ES/LC_MESSAGES/speedscan.po << 'EOF'
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: es_ES\n"

msgid "Dashboard"
msgstr "Panel"

msgid "Network"
msgstr "Red"

msgid "Optimization"
msgstr "Optimización"

msgid "Drivers"
msgstr "Controladores"

msgid "Process Manager"
msgstr "Administrador de Procesos"

msgid "Historical Performance"
msgstr "Rendimiento Histórico"

msgid "System Security"
msgstr "Seguridad del Sistema"

msgid "AI Agent"
msgstr "Agente IA"

msgid "Settings"
msgstr "Ajustes"

msgid "About"
msgstr "Acerca de"

msgid "Windows Cleaner"
msgstr "Limpiador de Windows"
EOF

# Compilar
msgfmt locale/pt_BR/LC_MESSAGES/speedscan.po -o locale/pt_BR/LC_MESSAGES/speedscan.mo
msgfmt locale/en_US/LC_MESSAGES/speedscan.po -o locale/en_US/LC_MESSAGES/speedscan.mo
msgfmt locale/es_ES/LC_MESSAGES/speedscan.po -o locale/es_ES/LC_MESSAGES/speedscan.mo

echo "✅ Traduções compiladas."

echo ""
echo "🎉 Correções concluídas!"
echo "Execute o programa: source venv/bin/activate && python3 -m core.main"
