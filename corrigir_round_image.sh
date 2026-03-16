#!/bin/bash
# Corrige a indentação da função round_image no main.py

set -e

ARQUIVO="core/main.py"
BACKUP="${ARQUIVO}.bak_roundimage_$(date +%Y%m%d_%H%M%S)"
cp "$ARQUIVO" "$BACKUP"
echo "✅ Backup criado: $BACKUP"

# Substitui a função round_image pela versão corrigida
sed -i '/def round_image/,/return None/c\
    def round_image(self, path, size=(96,96), radius=20):\
        print(f"DEBUG round_image: path={path}")\
        try:\
            img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)\
            mask = Image.new("L", size, 0)\
            ImageDraw.Draw(mask).rounded_rectangle((0,0)+size, radius=radius, fill=255)\
            result = Image.new("RGBA", size)\
            result.paste(img, (0,0), mask)\
            print("DEBUG round_image: sucesso")\
            return ctk.CTkImage(result, size=size)\
        except Exception as e:\
            print(f"DEBUG round_image: erro {e}")\
            return None' "$ARQUIVO"

echo "✅ Função round_image corrigida."
