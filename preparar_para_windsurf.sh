#!/bin/bash
# Script para empacotar todo o código do SpeedScan + problemas
# Executar no diretório ~/speedscan/speedscan

set -e

OUTPUT_FILE="speedscan_completo.txt"

echo "📦 Gerando $OUTPUT_FILE ..."

# Limpa arquivo anterior
> "$OUTPUT_FILE"

# 1. Lista de arquivos
echo "=========================================" >> "$OUTPUT_FILE"
echo "ESTRUTURA DO PROJETO" >> "$OUTPUT_FILE"
echo "=========================================" >> "$OUTPUT_FILE"
ls -la core/ >> "$OUTPUT_FILE"
echo -e "\n\n" >> "$OUTPUT_FILE"

# 2. Código de cada módulo
for file in core/*.py; do
  echo "===== $file =====" >> "$OUTPUT_FILE"
  cat "$file" >> "$OUTPUT_FILE"
  echo -e "\n\n" >> "$OUTPUT_FILE"
done

# 3. Arquivos de tradução (se existirem)
for lang in pt_BR en_US es_ES; do
  po_file="locale/$lang/LC_MESSAGES/speedscan.po"
  if [ -f "$po_file" ]; then
    echo "===== $po_file =====" >> "$OUTPUT_FILE"
    cat "$po_file" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"
  fi
done

# 4. Descrição dos problemas
cat >> "$OUTPUT_FILE" << 'EOF'
=========================================
========== PROBLEMAS CONHECIDOS ==========
=========================================

1. BOTÃO "DETALHES"
   - Atualmente aparece antes da senha ser digitada (em cards que exigem sudo)
   - DEVERIA aparecer SOMENTE após a primeira saída real do comando
   - Ao clicar para fechar o console, o botão deve sumir completamente
   - Ao executar um novo card, o processo deve recomeçar (botão anterior some)

2. CARDS NÃO EXECUTAM
   - Ex: clicar em "Ping" (aba Rede) não mostra saída no console
   - O método run_card_action é chamado (já temos prints), mas a execução não chega ao comando
   - Possível problema no _run_subprocess ou na captura de saída

3. TRADUÇÃO
   - Apenas os títulos das abas estão traduzidos (Dashboard, Network, etc.)
   - Todo o resto do software (mensagens dos cards, etc.) continua em inglês
   - Os arquivos .po existem mas estão incompletos

4. COMPORTAMENTO DESEJADO (resumo)
   - Botão "Detalhes": aparece só depois da execução real (após senha)
   - Ao clicar: console abre, botão vira "Hide Details ▲"
   - Ao clicar novamente: console fecha, botão desaparece
   - Novo card: processo recomeça
   - Cards mostram saída no console
   - Tradução completa em pt_BR, es_ES, en_US

5. OBSERVAÇÕES TÉCNICAS
   - O software roda dentro de um container Distrobox (KDE Linux)
   - Dependências: customtkinter, psutil, matplotlib, requests, speedtest-cli, pillow
   - O Python usado é 3.14 (dentro do container)
   - O ambiente virtual atual é venv_distrobox

EOF

echo "✅ Arquivo $OUTPUT_FILE criado com sucesso!"
echo "👉 Agora copie TODO o conteúdo deste arquivo e cole no chat do Windsurf."
echo "👉 Tamanho: $(wc -l < "$OUTPUT_FILE") linhas."
