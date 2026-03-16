#!/bin/bash
# Passo 1: Corrigir botão Detalhes (só aparece após senha)

set -e

cd ~/speedscan/speedscan

# Backup
cp core/main.py core/main.py.bak.passo1.$(date +%s)
echo "✅ Backup criado."

# 1. Remover todas as linhas de status inseridas antes de _run_subprocess
sed -i '/log.insert.*"Pinging google\.com\.\.\."/d' core/main.py
sed -i '/log.insert.*"Running ethtool\.\.\."/d' core/main.py
sed -i '/log.insert.*"Renewing IP via dhclient\.\.\."/d' core/main.py
sed -i '/log.insert.*"Running traceroute to google\.com\.\.\."/d' core/main.py
sed -i '/log.insert.*"Wi-Fi info\.\.\."/d' core/main.py
sed -i '/log.insert.*"Testing DNS (google\.com)\.\.\."/d' core/main.py
sed -i '/log.insert.*"Updating package list\.\.\."/d' core/main.py
sed -i '/log.insert.*"Scanning open ports\.\.\."/d' core/main.py
sed -i '/log.insert.*"Checking LANCache\.\.\."/d' core/main.py
sed -i '/log.insert.*"Obtaining public IP\.\.\."/d' core/main.py

# 2. Modificar os comandos para incluir um echo como primeira saída
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

# 3. Aumentar fallback para 10 segundos
sed -i 's/self\.after(2000, fallback)/self.after(10000, fallback)/' core/main.py

echo "✅ Passo 1 concluído."
echo "Execute o programa para testar o botão."
