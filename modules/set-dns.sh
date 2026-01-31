#!/bin/bash
# Automação de Configuração de Rede - DNS Google
# Foco em Performance e Conectividade de Dados

echo "Configurando DNS para Google (8.8.8.8 e 8.8.4.4)..."

# Comando nmcli para modificar a conexão padrão do Fedora KDE
nmcli connection modify "Wired connection 1" ipv4.dns "8.8.8.8 8.8.4.4"
nmcli connection modify "Wired connection 1" ipv4.ignore-auto-dns yes
nmcli connection up "Wired connection 1"

echo "Rede atualizada e DNS configurado com sucesso!"
