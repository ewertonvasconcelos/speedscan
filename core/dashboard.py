#!/usr/bin/env python3
# core/dashboard.py
# =============================================================================
#   ███████╗██████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ █████╗ ███╗   ██╗
#   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║
#   ███████╗██████╔╝█████╗  █████╗  ██║  ██║█████╗  ██║     ███████║██╔██╗ ██║
#   ╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║  ██║██╔══╝  ██║     ██╔══██║██║╚██╗██║
#   ███████║██║     ███████╗███████╗██████╔╝███████╗╚██████╗██║  ██║██║ ╚████║
#   ╚══════╝╚═╝     ╚══════╝╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
# =============================================================================
# Módulo de Dashboard Personalizável (com drag-and-drop) - CORRIGIDO
# =============================================================================

import customtkinter as ctk
import json
from pathlib import Path
import tkinter as tk

# Constante para o arquivo de configuração dos widgets
DASHBOARD_CONFIG = Path.home() / ".speedscan_dashboard.json"

class DraggableWidget(ctk.CTkFrame):
    """Widget que pode ser arrastado dentro do dashboard."""
    def __init__(self, parent, widget_id, title, content_callback, delete_callback, **kwargs):
        # Os kwargs já contêm fg_color e border_color passados pelo Dashboard
        super().__init__(parent, **kwargs)
        self.widget_id = widget_id
        self.title = title
        self.content_callback = content_callback
        self.delete_callback = delete_callback
        self.drag_start_x = 0
        self.drag_start_y = 0
        self._place_info = None  # Armazenará a posição durante o arrasto

        # Configuração visual adicional
        self.configure(corner_radius=10, border_width=1)
        self.pack_propagate(False)
        self.configure(height=200, width=300)

        # Barra de título (arrastável)
        title_bar = ctk.CTkFrame(self, fg_color=self.cget('border_color'), height=30, corner_radius=5)
        title_bar.pack(fill="x", padx=2, pady=2)
        title_bar.bind("<Button-1>", self.start_drag)
        title_bar.bind("<B1-Motion>", self.on_drag)

        lbl_title = ctk.CTkLabel(title_bar, text=title, font=("Inter", 12, "bold"),
                                  text_color="white")
        lbl_title.pack(side="left", padx=5)
        lbl_title.bind("<Button-1>", self.start_drag)
        lbl_title.bind("<B1-Motion>", self.on_drag)

        # Botão de fechar
        btn_close = ctk.CTkButton(title_bar, text="✕", width=20, height=20,
                                   fg_color="red", hover_color="darkred",
                                   command=self.delete_widget)
        btn_close.pack(side="right", padx=5)

        # Área de conteúdo (chama o callback para preencher)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.update_content()

    def start_drag(self, event):
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self._place_info = self.place_info()  # Salva a posição atual

    def on_drag(self, event):
        if self._place_info:
            dx = event.x_root - self.drag_start_x
            dy = event.y_root - self.drag_start_y
            new_x = self._place_info['x'] + dx
            new_y = self._place_info['y'] + dy
            self.place(x=new_x, y=new_y)

    def update_content(self):
        # Limpa o frame de conteúdo e chama o callback para preencher
        for child in self.content_frame.winfo_children():
            child.destroy()
        self.content_callback(self.content_frame, self.widget_id)

    def delete_widget(self):
        self.delete_callback(self.widget_id)
        self.destroy()

class Dashboard(ctk.CTkFrame):
    """
    Frame principal do dashboard. Gerencia os widgets e sua persistência.
    """
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.widgets = {}  # id -> widget
        self.next_id = 0
        self.configure(fg_color="transparent")
        self.load_widgets()

    def add_widget(self, widget_type, title, content_callback):
        """Adiciona um novo widget ao dashboard."""
        widget_id = str(self.next_id)
        self.next_id += 1
        widget = DraggableWidget(self, widget_id, title, content_callback,
                                  self.remove_widget, fg_color=self.app.bg_color,
                                  border_color=self.app.acc_color)
        # Posição inicial: canto superior esquerdo, com pequeno deslocamento
        x = (len(self.widgets) % 3) * 320
        y = (len(self.widgets) // 3) * 220
        widget.place(x=x, y=y)
        self.widgets[widget_id] = widget
        self.save_widgets()

    def remove_widget(self, widget_id):
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            self.save_widgets()

    def save_widgets(self):
        """Salva a posição e tipo de cada widget no arquivo de configuração."""
        data = []
        for wid, widget in self.widgets.items():
            info = widget.place_info()
            if info:  # Garante que place_info não seja None
                data.append({
                    'id': wid,
                    'title': widget.title,
                    'x': info['x'],
                    'y': info['y'],
                })
        with open(DASHBOARD_CONFIG, 'w') as f:
            json.dump(data, f, indent=2)

    def load_widgets(self):
        """Carrega os widgets salvos anteriormente."""
        if not DASHBOARD_CONFIG.exists():
            # Cria alguns widgets padrão na primeira execução
            self.add_default_widgets()
            return
        try:
            with open(DASHBOARD_CONFIG) as f:
                data = json.load(f)
            for item in data:
                widget_id = item['id']
                title = item['title']
                # Reconstrói o widget com o callback apropriado baseado no título
                content_callback = self.get_callback_for_title(title)
                widget = DraggableWidget(self, widget_id, title, content_callback,
                                          self.remove_widget, fg_color=self.app.bg_color,
                                          border_color=self.app.acc_color)
                widget.place(x=item['x'], y=item['y'])
                self.widgets[widget_id] = widget
                # Atualiza o next_id
                if int(widget_id) >= self.next_id:
                    self.next_id = int(widget_id) + 1
        except Exception as e:
            print(f"Erro ao carregar dashboard: {e}")
            self.add_default_widgets()

    def add_default_widgets(self):
        """Adiciona widgets iniciais."""
        self.add_widget("cpu", "CPU", self.app.widget_cpu)
        self.add_widget("ram", "Memória RAM", self.app.widget_ram)
        self.add_widget("disk", "Disco", self.app.widget_disk)

    def get_callback_for_title(self, title):
        """Retorna o callback apropriado baseado no título do widget."""
        mapping = {
            "CPU": self.app.widget_cpu,
            "Memória RAM": self.app.widget_ram,
            "Disco": self.app.widget_disk,
            "Rede": self.app.widget_network,
            "Temperaturas": self.app.widget_temps,
            "Processos": self.app.widget_processes,
        }
        return mapping.get(title, self.app.widget_cpu)  # fallback

    # Métodos para adicionar widgets específicos (chamados pelos botões)
    def add_cpu_widget(self):
        self.add_widget("cpu", "CPU", self.app.widget_cpu)

    def add_ram_widget(self):
        self.add_widget("ram", "Memória RAM", self.app.widget_ram)

    def add_disk_widget(self):
        self.add_widget("disk", "Disco", self.app.widget_disk)

    def add_network_widget(self):
        self.add_widget("network", "Rede", self.app.widget_network)

    def add_temps_widget(self):
        self.add_widget("temps", "Temperaturas", self.app.widget_temps)

    def add_processes_widget(self):
        self.add_widget("processes", "Processos", self.app.widget_processes)
