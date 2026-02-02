#!/bin/bash
echo "🚀 Iniciando otimização de abertura de apps..."

# 1. Limpa o cache de ícones do KDE (faz o menu carregar mais rápido)
rm -rf ~/.cache/icon-cache.kcache
rm -rf ~/.cache/ksycoca5_*

# 2. Reconstrói o índice de aplicativos
kbuildsycoca5 --noincremental

# 3. Limpa caches temporários que podem estar pesando no SSD/HD
find ~/.cache -type f -atime +3 -delete

echo "✅ Otimização concluída! Os ícones devem responder mais rápido agora."
