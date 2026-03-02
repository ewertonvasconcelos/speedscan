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
# Dashboard com 3 slots fixos e todos os widgets do sistema (rotativo)
# Versão 0.0.9-beta
# =============================================================================

import customtkinter as ctk
import json
from pathlib import Path

DASHBOARD_CONFIG = Path.home() / ".speedscan_dashboard.json"

# Lista completa de widgets disponíveis
WIDGET_TYPES = [
    {"id": "hostname", "name": "Hostname", "callback": "widget_hostname"},
    {"id": "distro", "name": "Distribuição", "callback": "widget_distro"},
    {"id": "kernel", "name": "Kernel", "callback": "widget_kernel"},
    {"id": "uptime", "name": "Uptime", "callback": "widget_uptime"},
    {"id": "cpu", "name": "CPU", "callback": "widget_cpu"},
    {"id": "ram", "name": "Memória RAM", "callback": "widget_ram"},
    {"id": "gpu", "name": "GPU", "callback": "widget_gpu"},
    {"id": "disks", "name": "Discos", "callback": "widget_disks"},
    {"id": "battery", "name": "Bateria", "callback": "widget_battery"},
    {"id": "temps", "name": "Temperaturas", "callback": "widget_temps"},
    {"id": "health", "name": "Saúde", "callback": "widget_health"},
]

class SlotWidget(ctk.CTkFrame):
    """Representa um slot fixo que exibe um widget."""
    def __init__(self, parent, slot_index, widget_type, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.slot_index = slot_index
        self.widget_type = widget_type
        self.app = app_instance
        self.content_frame = None

        self.configure(fg_color=app_instance.bg_color, corner_radius=10,
                       border_width=1, border_color=app_instance.acc_color)
        self.pack_propagate(False)
        self.configure(height=200)

        # Título do slot (mostra o nome do widget)
        self.title_label = ctk.CTkLabel(self, text=widget_type["name"], font=("Inter", 14, "bold"),
                                         text_color=app_instance.acc_color)
        self.title_label.pack(pady=(5, 0))

        self.update_content()

    def update_content(self):
        """Recria o conteúdo do widget."""
        if self.content_frame:
            self.content_frame.destroy()
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Obtém o callback do app
        callback_name = self.widget_type["callback"]
        callback = getattr(self.app, callback_name)
        callback(self.content_frame, f"slot_{self.slot_index}")

    def set_widget_type(self, new_type):
        """Troca o tipo de widget exibido neste slot."""
        self.widget_type = new_type
        self.title_label.configure(text=new_type["name"])
        self.update_content()

class Dashboard(ctk.CTkFrame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.slots = []  # lista de objetos SlotWidget
        self.available_widgets = []  # widgets não utilizados nos slots

        self.configure(fg_color="transparent")

        self._build_ui()
        self.load_state()

    def _build_ui(self):
        """Cria os 3 slots e a barra de widgets disponíveis."""
        # Frame para os slots (dispostos horizontalmente)
        slots_frame = ctk.CTkFrame(self, fg_color="transparent")
        slots_frame.pack(fill="x", pady=10)

        # Cria os três slots vazios (apenas os frames)
        for i in range(3):
            slot_frame = ctk.CTkFrame(slots_frame, fg_color="transparent")
            slot_frame.pack(side="left", fill="both", expand=True, padx=5)
            self.slots.append(slot_frame)  # placeholder, será preenchido depois

        # Barra de widgets disponíveis
        available_label = ctk.CTkLabel(self, text="Widgets disponíveis:", font=("Inter", 14, "bold"),
                                        text_color=self.app.acc_color)
        available_label.pack(anchor="w", pady=(20, 5))

        self.available_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.available_frame.pack(fill="x", pady=5)

    def load_state(self):
        """Carrega a configuração salva ou define o estado padrão."""
        if DASHBOARD_CONFIG.exists():
            try:
                with open(DASHBOARD_CONFIG) as f:
                    data = json.load(f)
                    slot_ids = data.get("slots", [])
                    available_ids = data.get("available", [])
            except:
                slot_ids = []
                available_ids = []
        else:
            slot_ids = []
            available_ids = []

        # Se não houver configuração, define padrão: hostname, distro, uptime
        if not slot_ids:
            slot_ids = ["hostname", "distro", "uptime"]
            available_ids = [w["id"] for w in WIDGET_TYPES if w["id"] not in slot_ids]

        # Função para encontrar widget por id
        def find_widget(wid):
            for w in WIDGET_TYPES:
                if w["id"] == wid:
                    return w
            return WIDGET_TYPES[0]  # fallback

        # Constrói lista de widgets dos slots
        slot_widgets = [find_widget(wid) for wid in slot_ids]

        # Constrói lista de widgets disponíveis (garantindo que não estejam nos slots)
        available_widgets = []
        for wid in available_ids:
            w = find_widget(wid)
            if w not in slot_widgets:
                available_widgets.append(w)
        # Se algum widget da lista disponível já estiver nos slots, ignora
        # Adiciona quaisquer widgets que não estejam nem nos slots nem em available_ids
        for w in WIDGET_TYPES:
            if w not in slot_widgets and w not in available_widgets:
                available_widgets.append(w)

        self.available_widgets = available_widgets

        # Preenche os slots
        for i, slot_frame in enumerate(self.slots):
            if i < len(slot_widgets):
                widget_type = slot_widgets[i]
            else:
                widget_type = WIDGET_TYPES[0]  # fallback
            slot_widget = SlotWidget(slot_frame, i, widget_type, self.app,
                                      fg_color=self.app.bg_color)
            slot_widget.pack(fill="both", expand=True)
            self.slots[i] = slot_widget  # substitui o frame pelo widget

        self._update_available_buttons()
        self.save_state()

    def save_state(self):
        """Salva a configuração atual dos slots e disponíveis."""
        data = {
            "slots": [slot.widget_type["id"] for slot in self.slots],
            "available": [w["id"] for w in self.available_widgets]
        }
        with open(DASHBOARD_CONFIG, "w") as f:
            json.dump(data, f, indent=2)

    def _update_available_buttons(self):
        """Recria os botões de widgets disponíveis."""
        for child in self.available_frame.winfo_children():
            child.destroy()

        for widget in self.available_widgets:
            btn = ctk.CTkButton(self.available_frame, text=f"➕ {widget['name']}",
                                 fg_color=self.app.acc_color,
                                 command=lambda w=widget: self.add_to_slot(w))
            btn.pack(side="left", padx=5, pady=5)

    def add_to_slot(self, widget):
        """
        Adiciona o widget ao primeiro slot, rotacionando os demais.
        O widget que estava no último slot vai para a lista de disponíveis.
        """
        # Lista atual dos tipos nos slots
        current_slots = [slot.widget_type for slot in self.slots]

        # O novo widget vai para o slot 0
        new_slot0 = widget

        # O que estava no slot 0 vai para o slot 1
        new_slot1 = current_slots[0]

        # O que estava no slot 1 vai para o slot 2
        new_slot2 = current_slots[1]

        # O que estava no slot 2 vai para disponíveis
        removed = current_slots[2]

        # Atualiza os slots
        self.slots[0].set_widget_type(new_slot0)
        self.slots[1].set_widget_type(new_slot1)
        self.slots[2].set_widget_type(new_slot2)

        # Atualiza a lista de disponíveis
        # Remove o widget adicionado se ele estava na lista
        if widget in self.available_widgets:
            self.available_widgets.remove(widget)
        # Adiciona o removido, se ele não estiver já nos slots
        if removed not in [s.widget_type for s in self.slots]:
            self.available_widgets.append(removed)

        # Garante que não haja duplicatas
        # (opcional, mas por segurança)
        self.available_widgets = list({w["id"]: w for w in self.available_widgets}.values())

        self._update_available_buttons()
        self.save_state()
