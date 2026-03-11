#!/usr/bin/env python3
"""
Ajuste experimental para compactar ao máximo a sidebar:
- center com expand=True e pady=(0,0)
- altura dos botões = 28
"""

import shutil
import re
from pathlib import Path

MAIN_FILE = Path("core/main.py")
BACKUP_FILE = Path("core/main.py.bak")

def main():
    print("🧪 Aplicando ajustes experimentais...")

    if not MAIN_FILE.exists():
        print("❌ core/main.py não encontrado!")
        return

    shutil.copy(MAIN_FILE, BACKUP_FILE)
    print(f"✅ Backup: {BACKUP_FILE}")

    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. center.pack com expand=True e pady=(0,0)
    content = re.sub(
        r'center\.pack\(expand=False, fill="x", pady=\(\d+, \d+\)\)',
        'center.pack(expand=True, fill="x", pady=(0, 0))',
        content
    )

    # 2. Altura dos botões para 28
    content = re.sub(
        r'(btn = ctk\.CTkButton\([^,]+,[^,]+,\s*height=)\d+',
        r'\g<1>28',
        content
    )

    # 3. (Opcional) reduzir pady dos botões para 1 (já está em 2, mas podemos forçar)
    content = re.sub(
        r'(frame\.pack\(pady=)\d+',
        r'\g<1>1',
        content
    )

    # 4. Garantir que o spacer continue height=0
    content = re.sub(
        r'spacer = ctk\.CTkLabel\(center, text="", height=\d+\)',
        'spacer = ctk.CTkLabel(center, text="", height=0)',
        content
    )

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Ajustes aplicados!")
    print("▶️ Execute 'python -m core.main' e veja o resultado.")
    print("🧹 Após testar, pode excluir este script.")

if __name__ == "__main__":
    main()
