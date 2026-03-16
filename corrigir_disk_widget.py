#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_disk")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Procurar pela função widget_disks
padrao = r'(def widget_disks\(self, frame, tag\):.*?)(?=\n\s*def)'
match = re.search(padrao, conteudo, re.DOTALL)
if match:
    funcao_antiga = match.group(1)
    # Nova função que lista todos os discos
    nova_funcao = '''    def widget_disks(self, frame, tag):
        """Mostra informações de todos os discos montados."""
        import psutil
        disks = []
        for part in psutil.disk_partitions():
            if part.fstype and ('/dev' in part.device or part.fstype != 'squashfs'):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append(f"{part.mountpoint}: {usage.percent}% ({usage.used // (1024**3)} GB / {usage.total // (1024**3)} GB)")
                except PermissionError:
                    disks.append(f"{part.mountpoint}: Sem permissão")
        if not disks:
            disks = ["Nenhum disco encontrado"]
        text = "\\n".join(disks)
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 12), justify="left")
        label.pack(expand=True, fill="both", padx=5, pady=5)'''
    conteudo = conteudo.replace(funcao_antiga, nova_funcao)
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print("Função widget_disks atualizada.")
else:
    print("Função widget_disks não encontrada.")
