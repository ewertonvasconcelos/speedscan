#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

arquivo = Path("core/main.py")
backup = Path("core/main.py.bak_widgets")
shutil.copy2(arquivo, backup)
print(f"Backup criado: {backup}")

with open(arquivo, 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Verificar se os métodos de widget já existem
if 'def widget_hostname' not in conteudo:
    print("Métodos de widget não encontrados. Adicionando...")
    # Encontrar o final da classe (último método antes do __main__)
    # Vamos adicionar antes do if __name__ == "__main__"
    marker = 'if __name__ == "__main__":'
    pos = conteudo.find(marker)
    if pos == -1:
        print("Marcador não encontrado. Abortando.")
        exit(1)
    
    # Inserir os métodos antes do marcador
    metodos = '''
    # ============================================================================
    # Widgets do Dashboard
    # ============================================================================
    def widget_hostname(self, frame, tag):
        import socket
        hostname = socket.gethostname()
        label = ctk.CTkLabel(frame, text=hostname, font=("Inter", 16))
        label.pack(expand=True)

    def widget_distro(self, frame, tag):
        import platform
        text = f"{platform.system()} {platform.release()}"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_kernel(self, frame, tag):
        import platform
        text = platform.version()
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_uptime(self, frame, tag):
        import psutil
        from datetime import datetime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        delta = datetime.now() - boot_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        text = f"{days}d {hours}h {minutes}m"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_cpu(self, frame, tag):
        import psutil
        text = f"{psutil.cpu_percent(interval=0.1)}%"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_ram(self, frame, tag):
        import psutil
        mem = psutil.virtual_memory()
        text = f"{mem.percent}% ({mem.used // (1024**3)} GB / {mem.total // (1024**3)} GB)"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_gpu(self, frame, tag):
        try:
            import subprocess
            result = subprocess.run(['lspci', '|', 'grep', '-i', 'vga'], capture_output=True, text=True, shell=True)
            text = result.stdout.strip().split('\\n')[0][:50] if result.stdout else self._("N/A")
        except:
            text = self._("N/A")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_disks(self, frame, tag):
        import psutil
        disk = psutil.disk_usage('/')
        text = f"{disk.percent}% ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_battery(self, frame, tag):
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = self._("Carregando") if battery.power_plugged else self._("Descarregando")
            text = f"{percent}% ({plugged})"
        else:
            text = self._("Sem bateria")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_temps(self, frame, tag):
        import psutil
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    text = f"{entries[0].current}°C"
                    break
            else:
                text = self._("N/A")
        else:
            text = self._("N/A")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_health(self, frame, tag):
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem_percent = psutil.virtual_memory().percent
        if cpu_percent < 50 and mem_percent < 50:
            text = self._("Bom")
        elif cpu_percent < 80 and mem_percent < 80:
            text = self._("Ok")
        else:
            text = self._("Alto uso")
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 16))
        label.pack(expand=True)

    def widget_realtime_chart(self, frame, tag):
        from core.dashboard import RealTimeChartWidget
        chart = RealTimeChartWidget(frame, tag)
        if not hasattr(self, '_charts'):
            self._charts = []
        self._charts.append(chart)
'''
    novo_conteudo = conteudo[:pos] + metodos + '\n' + conteudo[pos:]
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(novo_conteudo)
    print("Métodos de widget adicionados.")
else:
    print("Métodos de widget já existem. Verifique manualmente se estão completos.")

print("Execute o programa novamente.")
