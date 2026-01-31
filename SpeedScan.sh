#!/bin/bash
# SpeedScan - Otimização e Diagnóstico de Sistema

echo "=========================================="
echo "      INICIANDO SPEEDSCAN BETA 0.1       "
echo "=========================================="

echo "[1/4] Verificando uso de disco..."
df -h | grep '^/dev/'

echo -e "\n[2/4] Limpando caches do sistema (DNF)..."
sudo dnf clean all

echo -e "\n[3/4] Otimizando caches de fontes (OnlyOffice fix)..."
fc-cache -f

echo -e "\n[4/4] Configurando Memória ZRAM (2GB)..."
# Tenta configurar, se já existir ele apenas avisa
sudo zramctl --find --size 2G || echo "ZRAM já configurada ou dispositivo ocupado."

echo -e "\n=========================================="
echo "       SISTEMA TUNADO COM SUCESSO!       "
echo "=========================================="
