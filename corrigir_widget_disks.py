#!/usr/bin/env python3
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_disk2")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backo}")

with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Encontrar o início da função widget_disks
inicio = -1
for i, linha in enumerate(linhas):
    if linha.strip().startswith('def widget_disks'):
        inicio = i
        break

if inicio == -1:
    print("Função widget_disks não encontrada.")
    exit(1)

# Encontrar o fim da função (próxima definição no mesmo nível)
fim = inicio + 1
while fim < len(linhas) and (linhas[fim].startswith(' ' * 4) or linhas[fim].strip() == ''):
    fim += 1

# Nova função com indentação correta (4 espaços)
nova_funcao = [
    '    def widget_disks(self, frame, tag):\n',
    '        """Mostra informações de todos os discos montados."""\n',
    '        import psutil\n',
    '        disks = []\n',
    '        for part in psutil.disk_partitions():\n',
    '            if part.fstype and (\'/dev\' in part.device or part.fstype != \'squashfs\'):\n',
    '                try:\n',
    '                    usage = psutil.disk_usage(part.mountpoint)\n',
    '                    disks.append(f"{part.mountpoint}: {usage.percent}% ({usage.used // (1024**3)} GB / {usage.total // (1024**3)} GB)")\n',
    '                except PermissionError:\n',
    '                    disks.append(f"{part.mountpoint}: Sem permissão")\n',
    '        if not disks:\n',
    '            disks = ["Nenhum disco encontrado"]\n',
    '        text = "\\n".join(disks)\n',
    '        label = ctk.CTkLabel(frame, text=text, font=("Inter", 12), justify="left")\n',
    '        label.pack(expand=True, fill="both", padx=5, pady=5)\n',
]

linhas[inicio:fim] = nova_funcao

with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("Função widget_disks corrigida.")
