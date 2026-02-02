#!/bin/bash
echo "🚀 Otimização Nativa Fedora 43..."

# 1. Ajusta a "agressividade" do sistema para usar a RAM (Swappiness)
# Isso faz os apps abrirem mais rápido em vez de travarem o disco
sudo sysctl -w vm.swappiness=10

# 2. Aumenta o limite de arquivos abertos (ajuda apps pesados como OnlyOffice)
echo "* soft nofile 1048576" | sudo tee -a /etc/security/limits.conf

# 3. Limpa a memória acumulada agora
sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# 4. Força o KDE a atualizar os atalhos
kbuildsycoca5 --noincremental

echo "✅ SISTEMA OTIMIZADO COM RECURSOS NATIVOS!"
