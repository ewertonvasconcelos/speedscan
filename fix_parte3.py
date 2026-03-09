#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

file_path = Path('core/main.py')
backup_path = file_path.with_suffix('.py.bak_parte3')

# Backup
shutil.copy(file_path, backup_path)
print(f"Backup criado: {backup_path}")

with open(file_path, 'r') as f:
    content = f.read()

# 1. Encontrar a classe SpeedScan
class_pattern = r'(class SpeedScan\(ctk\.CTk\):\s*\n)(.*?)(?=\n\nclass|\n\Z|\nif __name__)'
class_match = re.search(class_pattern, content, re.DOTALL)
if not class_match:
    print("Classe SpeedScan não encontrada!")
    exit(1)

class_header = class_match.group(1)
class_body = class_match.group(2)
pre_class = content[:class_match.start()]
post_class = content[class_match.end():]

# 2. Substituir ou adicionar os métodos widget_* com versões funcionais
widget_methods = '''
    def widget_hostname(self, frame, tag):
        """Exibe o hostname no frame do dashboard."""
        import socket
        hostname = socket.gethostname()
        label = ctk.CTkLabel(frame, text=hostname, font=("Inter", 14, "bold"))
        label.pack(expand=True, pady=10)
        print(f"DEBUG: widget_hostname executado: {hostname}")

    def widget_distro(self, frame, tag):
        """Exibe a distribuição Linux."""
        import platform
        distro = platform.system() + " " + platform.release()
        label = ctk.CTkLabel(frame, text=distro, font=("Inter", 14))
        label.pack(expand=True, pady=10)

    def widget_kernel(self, frame, tag):
        """Exibe a versão do kernel."""
        import platform
        kernel = platform.version()
        label = ctk.CTkLabel(frame, text=kernel, font=("Inter", 12), wraplength=180)
        label.pack(expand=True, pady=10)

    def widget_uptime(self, frame, tag):
        """Exibe o tempo de atividade."""
        import psutil
        from datetime import datetime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        text = f"{days}d {hours}h {minutes}m"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 14))
        label.pack(expand=True, pady=10)

    def widget_cpu(self, frame, tag):
        """Exibe o uso da CPU."""
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.5)
        text = f"CPU: {cpu_percent}%"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 14, "bold"))
        label.pack(expand=True, pady=10)

    def widget_ram(self, frame, tag):
        """Exibe o uso da RAM."""
        import psutil
        mem = psutil.virtual_memory()
        text = f"RAM: {mem.percent}%\\n{mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 12))
        label.pack(expand=True, pady=10)

    def widget_gpu(self, frame, tag):
        """Exibe informações da GPU (simplificado)."""
        try:
            import subprocess
            result = subprocess.run(['lspci'], capture_output=True, text=True)
            for line in result.stdout.split('\\n'):
                if 'VGA' in line or '3D' in line:
                    gpu = line.split(':')[2].strip()[:40]
                    break
            else:
                gpu = "N/A"
        except:
            gpu = "N/A"
        label = ctk.CTkLabel(frame, text=gpu, font=("Inter", 12), wraplength=180)
        label.pack(expand=True, pady=10)

    def widget_disks(self, frame, tag):
        """Exibe o uso do disco."""
        import psutil
        disk = psutil.disk_usage('/')
        text = f"Disco: {disk.percent}%\\n{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 12))
        label.pack(expand=True, pady=10)

    def widget_battery(self, frame, tag):
        """Exibe o status da bateria."""
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = "Carregando" if battery.power_plugged else "Descarregando"
            text = f"Bateria: {percent}%\\n{plugged}"
        else:
            text = "Sem bateria"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 12))
        label.pack(expand=True, pady=10)

    def widget_temps(self, frame, tag):
        """Exibe a temperatura (se disponível)."""
        import psutil
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    temp = entries[0].current
                    text = f"Temp: {temp}°C"
                    break
            else:
                text = "Temp: N/A"
        else:
            text = "Temp: N/A"
        label = ctk.CTkLabel(frame, text=text, font=("Inter", 14))
        label.pack(expand=True, pady=10)

    def widget_health(self, frame, tag):
        """Exibe a saúde do sistema (score)."""
        # Simula um score baseado em CPU e RAM
        import psutil
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory().percent
        if cpu < 30 and mem < 50:
            health = "Excelente"
        elif cpu < 60 and mem < 80:
            health = "Bom"
        elif cpu < 85 and mem < 90:
            health = "Regular"
        else:
            health = "Ruim"
        label = ctk.CTkLabel(frame, text=f"Saúde: {health}", font=("Inter", 14, "bold"))
        label.pack(expand=True, pady=10)
'''

# 3. Remover métodos widget_* antigos do corpo da classe (se existirem) e inserir os novos
#    Vamos substituir qualquer bloco que comece com 'def widget_' dentro da classe
widget_pattern = r'(\n    def widget_\w+\(.*?\):.*?)(?=\n    def|\n\n|\Z)'
class_body = re.sub(widget_pattern, '', class_body, flags=re.DOTALL)

# Inserir os novos métodos no final da classe (antes do último método, se houver)
# Vamos inserir antes do método _on_closing ou _maximize_window, se existirem
insert_before = '_on_closing'
if insert_before not in class_body:
    insert_before = '_maximize_window'
    if insert_before not in class_body:
        insert_before = None

if insert_before:
    # Encontrar a posição para inserir
    pattern = fr'(\n    def {insert_before}\(.*?\):.*?)(?=\n    def|\n\n|\Z)'
    match = re.search(pattern, class_body, re.DOTALL)
    if match:
        target = match.group(1)
        class_body = class_body.replace(target, widget_methods + '\n' + target)
    else:
        class_body += '\n' + widget_methods
else:
    class_body += '\n' + widget_methods

# 4. Ajustar o método __init__ para aumentar o tamanho da janela
#    Procurar por self.minsize(900, 600) e substituir por self.geometry("1200x700")
class_body = class_body.replace('self.minsize(900, 600)', 'self.geometry("1200x700")')

# 5. Garantir que o Dashboard seja criado com um pequeno atraso para evitar problemas de carregamento
#    No método _fill_dashboard, após criar o dashboard, adicionar self.after(100, self.dashboard.load_state)
#    Isso já deve estar ok, mas vamos garantir
if 'self.dashboard = Dashboard(parent, self, fg_color="transparent")' in class_body:
    # Verificar se já tem um after
    if 'self.after(100, self.dashboard.load_state)' not in class_body:
        # Inserir após a linha do dashboard
        class_body = class_body.replace(
            'self.dashboard.pack(fill="both", expand=True)',
            'self.dashboard.pack(fill="both", expand=True)\n        self.after(100, self.dashboard.load_state)'
        )

# 6. Reconstruir o conteúdo final
new_content = pre_class + class_header + class_body + '\n\n' + post_class

# 7. Salvar
with open(file_path, 'w') as f:
    f.write(new_content)

print("✅ Parte 3 aplicada: widgets do Dashboard corrigidos e janela redimensionada.")
print("Execute agora: python -m core.main")
