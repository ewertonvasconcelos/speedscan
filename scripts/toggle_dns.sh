#!/bin/bash

# Identifica a conexão Wi-Fi ativa
CON_NAME=$(nmcli -t -f NAME,TYPE connection show --active | grep wireless | cut -d: -f1)

if [ -z "$CON_NAME" ]; then
    echo "Erro: Nenhuma conexão Wi-Fi ativa encontrada."
    exit 1
fi

echo "Conexão detectada: $CON_NAME"
echo "Escolha o perfil:"
echo "1) AdGuard (Anúncios OFF) + Abrir Apps (Stremio/WhatsApp)"
echo "2) Google (Padrão/Diagnóstico)"
read -p "Opção: " OPT

case $OPT in
    1)
        nmcli connection modify "$CON_NAME" ipv4.dns "94.140.14.14 94.140.15.15"
        nmcli connection modify "$CON_NAME" ipv4.ignore-auto-dns yes
        nmcli connection up "$CON_NAME"
        echo "Rede configurada! Abrindo seus apps..."
        
        # Abre o WhatsApp (modo App do Chrome) e o Stremio (Flatpak) em background
        google-chrome --app=https://web.whatsapp.com &
        flatpak run com.stremio.Stremio &
        ;;
    2)
        nmcli connection modify "$CON_NAME" ipv4.dns "8.8.8.8 8.8.4.4"
        nmcli connection modify "$CON_NAME" ipv4.ignore-auto-dns no
        nmcli connection up "$CON_NAME"
        echo "DNS Google aplicado (Padrão)."
        ;;
    *)
        echo "Opção inválida."
        exit 1
        ;;
esac
