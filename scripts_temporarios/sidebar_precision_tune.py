#!/usr/bin/env python3
"""
Ajuste preciso da sidebar com valores calculados.
"""

import shutil
import re
from pathlib import Path

MAIN_FILE = Path("core/main.py")
BACKUP_FILE = Path("core/main.py.bak")

def main():
    print("🔧 Aplicando ajuste preciso da sidebar...")

    if not MAIN_FILE.exists():
        print("❌ core/main.py não encontrado!")
        return

    shutil.copy(MAIN_FILE, BACKUP_FILE)
    print(f"✅ Backup: {BACKUP_FILE}")

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Ajustar padding da logo para (15, 5)
    content = re.sub(
        r'(top\.pack\(pady=)\$\{?[^)]*\)?',
        r'top.pack(pady=(15, 5))',
        content
    )

    # 2. Ajustar center para expand=False e pady=(5,5)
    content = re.sub(
        r'center\.pack\(expand=(?:True|False), fill="x", pady=\(\d+, \d+\)\)',
        'center.pack(expand=False, fill="x", pady=(5, 5))',
        content
    )

    # 3. Garantir altura dos botões em 30
    content = re.sub(
        r'(btn = ctk\.CTkButton\([^,]+,[^,]+,\s*height=)\d+',
        r'\g<1>30',
        content
    )

    # 4. Garantir pady dos botões em 2
    content = re.sub(
        r'(frame\.pack\(pady=)\d+',
        r'\g<1>2',
        content
    )

    # 5. Garantir spacers com height=0
    content = re.sub(
        r'spacer = ctk\.CTkLabel\(center, text="", height=\d+\)',
        'spacer = ctk.CTkLabel(center, text="", height=0)',
        content
    )

    # 6. Ajustar bottom para pady=(0,5)
    content = re.sub(
        r'(bottom\.pack\(side="bottom", fill="x", pady=)\$\{?[^)]*\)?',
        r'bottom.pack(side="bottom", fill="x", pady=(0, 5))',
        content
    )

    # 7. Ajustar minsize para 900x480
    content = re.sub(
        r'self\.minsize\(900,\s*\d+\)',
        'self.minsize(900, 480)',
        content
    )

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Ajustes aplicados!")
    print("▶️ Execute 'python -m core.main' e veja o resultado.")
    print("🧹 Após testar, pode excluir este script.")

if __name__ == "__main__":
    main()
