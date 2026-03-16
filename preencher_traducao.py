#!/usr/bin/env python3
# Preenche automaticamente as traduções em arquivos .po usando Google Translate

import os
import sys
from googletrans import Translator

def traduzir_po(arquivo_po, idioma_destino):
    with open(arquivo_po, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    translator = Translator()
    novas_linhas = []
    msgid = None
    for linha in linhas:
        if linha.startswith('msgid "'):
            # Extrai o texto entre aspas
            inicio = linha.find('"') + 1
            fim = linha.rfind('"')
            if inicio < fim:
                msgid = linha[inicio:fim]
            novas_linhas.append(linha)
        elif linha.startswith('msgstr ""') and msgid and msgid.strip():
            # Traduz o msgid
            try:
                traducao = translator.translate(msgid, dest=idioma_destino).text
                novas_linhas.append(f'msgstr "{traducao}"\n')
                print(f'Traduzido: {msgid} -> {traducao}')
            except Exception as e:
                print(f'Erro ao traduzir "{msgid}": {e}')
                novas_linhas.append('msgstr ""\n')
            msgid = None
        else:
            novas_linhas.append(linha)

    with open(arquivo_po, 'w', encoding='utf-8') as f:
        f.writelines(novas_linhas)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python preencher_traducao.py <arquivo.po> <idioma_destino>")
        sys.exit(1)
    arquivo = sys.argv[1]
    idioma = sys.argv[2]  # ex: 'pt' para português, 'es' para espanhol
    traduzir_po(arquivo, idioma)

