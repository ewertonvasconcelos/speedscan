#!/usr/bin/env python3
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_widget_final")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Procurar a linha que contém 'def widget_disks'
inicio = -1
for i, linha in enumerate(linhas):
    if 'def widget_disks' in linha:
        inicio = i
        break

if inicio == -1:
    print("Função widget_disks não encontrada. Abortando.")
    exit(1)

# Encontrar o fim da função (próxima definição de função no mesmo nível)
fim = inicio + 1
while fim < len(linhas) and not (linhas[fim].strip().startswith('def ') and linhas[fim][0] != ' '):
    fim += 1

# Nova função com indentação correta
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

# Substituir o bloco
linhas[inicio:fim] = nova_funcao

with open(arquivo, 'w', encoding='utf-8') as f:
    f.writelines(linhas)

print("Função widget_disks corrigida com sucesso.")
