#!/bin/bash
echo -e "\e[1;34m[ SPEEDSCAN - INICIANDO LIMPEZA PROFUNDA ]\e[0m"
sleep 1

# 1. Limpeza de Cache do Solus (eopkg)
echo -e "\n\e[1;32m>> Limpando cache do gerenciador de pacotes...\e[0m"
sudo eopkg dc -y

# 2. Remoção de Arquivos Temporários e Logs antigos
echo -e "\n\e[1;32m>> Removendo logs e temporários inúteis...\e[0m"
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*
sudo find /var/log -type f -name "*.log" -exec truncate -s 0 {} +

# 3. Limpeza de Miniaturas (Thumbnails) que pesam no SSD
echo -e "\n\e[1;32m>> Limpando cache de miniaturas de imagens...\e[0m"
rm -rf ~/.cache/thumbnails/*

# 4. Sincronizar Disco (Garantir escrita no SSD)
sync

echo -e "\n\e[1;34m[ OTIMIZAÇÃO CONCLUÍDA COM SUCESSO! ]\e[0m"
