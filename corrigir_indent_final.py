#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_final")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

conteudo = arquivo.read_text()

# Padrão para encontrar a função round_image atual
padrao = re.compile(
    r'(def round_image\(self, path, size=\(96,96\), radius=20\):.*?)(?=\n\s*def|\Z)',
    re.DOTALL
)

# Versão correta com indentação adequada (8 espaços para o bloco interno)
substituicao = '''    def round_image(self, path, size=(96,96), radius=20):
        print(f"DEBUG round_image: path={path}")
        try:
            img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            mask = Image.new("L", size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0,0)+size, radius=radius, fill=255)
            result = Image.new("RGBA", size)
            result.paste(img, (0,0), mask)
            print("DEBUG round_image: sucesso")
            return ctk.CTkImage(result, size=size)
        except Exception as e:
            print(f"DEBUG round_image: erro {e}")
            return None'''

if padrao.search(conteudo):
    novo_conteudo = padrao.sub(substituicao, conteudo)
    arquivo.write_text(novo_conteudo)
    print("Função round_image substituída com sucesso.")
else:
    print("Padrão não encontrado. Verifique o arquivo.")

print("Pronto. Execute 'python -m core.main' agora.")
