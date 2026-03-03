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
# Dashboard com 3 slots fixos e widgets disponíveis em duas linhas (4+4)
# Versão 0.1.0-beta
# =============================================================================

import customtkinter as ctk
import json
from pathlib import Path

DASHBOARD_CONFIG = Path.home() / ".speedscan_dashboard.json"

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

        self.title_label = ctk.CTkLabel(self, text=widget_type["name"], font=("Inter", 14, "bold"),
                                         text_color=app_instance.acc_color)
        self.title_label.pack(pady=(5, 0))

        self.update_content()

    def update_content(self):
        if self.content_frame:
            self.content_frame.destroy()
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        callback_name = self.widget_type["callback"]
        callback = getattr(self.app, callback_name)
        callback(self.content_frame, f"slot_{self.slot_index}")

    def set_widget_type(self, new_type):
        self.widget_type = new_type
        self.title_label.configure(text=new_type["name"])
        self.update_content()

class Dashboard(ctk.CTkFrame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.slots = []
        self.available_widgets = []

        self.configure(fg_color="transparent")

        self._build_ui()
        self.load_state()

    def _build_ui(self):
        slots_frame = ctk.CTkFrame(self, fg_color="transparent")
        slots_frame.pack(fill="x", pady=10)

        for i in range(3):
            slot_frame = ctk.CTkFrame(slots_frame, fg_color="transparent")
            slot_frame.pack(side="left", fill="both", expand=True, padx=5)
            self.slots.append(slot_frame)

        available_label = ctk.CTkLabel(self, text="Widgets disponíveis:", font=("Inter", 14, "bold"),
                                        text_color=self.app.acc_color)
        available_label.pack(anchor="center", pady=(20, 10))

        self.available_container = ctk.CTkFrame(self, fg_color="transparent")
        self.available_container.pack(anchor="center", pady=5)

        self.row1_frame = ctk.CTkFrame(self.available_container, fg_color="transparent")
        self.row1_frame.pack(pady=3)

        self.row2_frame = ctk.CTkFrame(self.available_container, fg_color="transparent")
        self.row2_frame.pack(pady=3)

    def load_state(self):
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

        if not slot_ids:
            slot_ids = ["hostname", "distro", "uptime"]
            available_ids = [w["id"] for w in WIDGET_TYPES if w["id"] not in slot_ids]

        def find_widget(wid):
            for w in WIDGET_TYPES:
                if w["id"] == wid:
                    return w
            return WIDGET_TYPES[0]

        slot_widgets = [find_widget(wid) for wid in slot_ids]
        available_widgets = []
        for wid in available_ids:
            w = find_widget(wid)
            if w not in slot_widgets:
                available_widgets.append(w)
        for w in WIDGET_TYPES:
            if w not in slot_widgets and w not in available_widgets:
                available_widgets.append(w)

        self.available_widgets = available_widgets

        for i, slot_frame in enumerate(self.slots):
            if i < len(slot_widgets):
                widget_type = slot_widgets[i]
            else:
                widget_type = WIDGET_TYPES[0]
            slot_widget = SlotWidget(slot_frame, i, widget_type, self.app,
                                      fg_color=self.app.bg_color)
            slot_widget.pack(fill="both", expand=True)
            self.slots[i] = slot_widget

        self._update_available_buttons()
        self.save_state()

    def save_state(self):
        data = {
            "slots": [slot.widget_type["id"] for slot in self.slots],
            "available": [w["id"] for w in self.available_widgets]
        }
        with open(DASHBOARD_CONFIG, "w") as f:
            json.dump(data, f, indent=2)

    def _update_available_buttons(self):
        for child in self.row1_frame.winfo_children():
            child.destroy()
        for child in self.row2_frame.winfo_children():
            child.destroy()

        total = len(self.available_widgets)
        if total >= 8:
            first_half = self.available_widgets[:4]
            second_half = self.available_widgets[4:8]
        else:
            half = (total + 1) // 2
            first_half = self.available_widgets[:half]
            second_half = self.available_widgets[half:]

        for widget in first_half:
            btn = ctk.CTkButton(self.row1_frame, text=f"➕ {widget['name']}",
                                 fg_color=self.app.acc_color,
                                 height=40, corner_radius=8,
                                 command=lambda w=widget: self.add_to_slot(w))
            btn.pack(side="left", padx=8, pady=5)

        for widget in second_half:
            btn = ctk.CTkButton(self.row2_frame, text=f"➕ {widget['name']}",
                                 fg_color=self.app.acc_color,
                                 height=40, corner_radius=8,
                                 command=lambda w=widget: self.add_to_slot(w))
            btn.pack(side="left", padx=8, pady=5)

        self.row1_frame.pack_configure(anchor="center")
        self.row2_frame.pack_configure(anchor="center")

    def add_to_slot(self, widget):
        current_slots = [slot.widget_type for slot in self.slots]

        new_slot0 = widget
        new_slot1 = current_slots[0]
        new_slot2 = current_slots[1]
        removed = current_slots[2]

        self.slots[0].set_widget_type(new_slot0)
        self.slots[1].set_widget_type(new_slot1)
        self.slots[2].set_widget_type(new_slot2)

        if widget in self.available_widgets:
            self.available_widgets.remove(widget)
        if removed not in [s.widget_type for s in self.slots]:
            self.available_widgets.append(removed)

        seen = set()
        unique = []
        for w in self.available_widgets:
            if w["id"] not in seen:
                seen.add(w["id"])
                unique.append(w)
        self.available_widgets = unique

        self._update_available_buttons()
        self.save_state()
