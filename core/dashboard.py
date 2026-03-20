#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard module with 3 fixed slots and available widgets in two rows (4+4).
Version 1.0.0
"""

import customtkinter as ctk
import json
import logging
from pathlib import Path

# Color constants
COLOR_SUCCESS = "#4CAF50"   # Green
COLOR_WARNING = "#FF9800"   # Orange/Yellow
COLOR_DANGER = "#F44336"    # Red
COLOR_COLD = "#2196F3"      # Blue


def get_temp_icon(temp):
    """Get icon based on temperature."""
    if temp < 30:
        return "❄️"  # Cold
    elif temp < 50:
        return "🌡️"  # Normal
    elif temp < 70:
        return "⚠️"  # Warning
    else:
        return "🔥"  # Hot


def get_temp_color(temp):
    """Get color based on temperature."""
    if temp < 30:
        return COLOR_COLD   # blue
    elif temp < 50:
        return COLOR_SUCCESS  # green
    elif temp < 70:
        return COLOR_WARNING  # orange
    else:
        return COLOR_DANGER   # red


def get_usage_color(percent):
    """Get color based on usage percentage."""
    if percent <= 60:
        return "#4CAF50"  # green
    elif percent <= 85:
        return "#FF9800"  # orange
    else:
        return "#F44336"  # red


def get_battery_color(percent):
    """Get color based on battery percentage."""
    if percent <= 20:
        return "#F44336"  # red
    elif percent <= 50:
        return "#FF9800"  # orange
    else:
        return "#4CAF50"  # green


DASHBOARD_CONFIG = Path.home() / ".speedscan_dashboard.json"

# Widgets for big slots (top row)
BIG_WIDGETS = [
    {"id": "cpu", "name": "CPU", "callback": "widget_cpu"},
    {"id": "ram", "name": "Memória RAM", "callback": "widget_ram"},
    {"id": "disks", "name": "Discos", "callback": "widget_disks"},
]

# Widgets for small grid (bottom)
SMALL_WIDGETS = [
    {"id": "battery", "name": "Bateria", "callback": "widget_battery"},
    {"id": "gpu", "name": "GPU", "callback": "widget_gpu"},
    {"id": "temps", "name": "Temperaturas", "callback": "widget_temps"},
    {"id": "uptime", "name": "Uptime", "callback": "widget_uptime"},
    {"id": "kernel", "name": "Kernel", "callback": "widget_kernel"},
    {"id": "distro", "name": "Distribuição", "callback": "widget_distro"},
    {"id": "hostname", "name": "Hostname", "callback": "widget_hostname"},
    {"id": "health", "name": "Saúde", "callback": "widget_health"},
]

# All widget types combined
WIDGET_TYPES = BIG_WIDGETS + SMALL_WIDGETS


class SlotWidget(ctk.CTkFrame):
    def __init__(self, parent, slot_index, widget_type, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.slot_index = slot_index
        self.widget_type = widget_type
        self.app = app_instance
        self.content_frame = None

        self.configure(
            fg_color=app_instance.bg_color,
            corner_radius=10,
            border_width=1,
            border_color=app_instance.acc_color,
        )
        self.pack_propagate(False)
        self.configure(height=200)

        # Use widget_title method for proper title
        widget_name = app_instance.widget_title(widget_type)
        self.title_label = ctk.CTkLabel(
            self,
            text=widget_name,
            font=("Inter", 14, "bold"),
            text_color=app_instance.acc_color,
        )
        self.title_label.pack(pady=(5, 0))

        self.update_content()

    def update_content(self):
        if self.content_frame:
            self.content_frame.destroy()
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Center content
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        callback_name = self.widget_type["callback"]
        callback = getattr(self.app, callback_name)
        callback(self.content_frame, f"slot_{self.slot_index}")

    def set_widget_type(self, new_type):
        self.widget_type = new_type
        widget_name = self.app.widget_title(new_type)
        self.title_label.configure(text=widget_name)
        self.update_content()


class SmallWidget(ctk.CTkFrame):
    """Small widget for the grid (180x120)."""
    
    def __init__(self, parent, widget_type, app_instance, on_click=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.widget_type = widget_type
        self.app = app_instance
        self.on_click = on_click
        self.configure(
            fg_color=app_instance.bg_color,
            corner_radius=10,
            border_width=1,
            border_color=app_instance.acc_color,
            width=180,
            height=120,
            cursor="hand2",
        )
        self.grid_propagate(False)
        
        # Title - use widget_title method from app
        widget_name = app_instance.widget_title(widget_type)
        self.title_label = ctk.CTkLabel(
            self,
            text=widget_name,
            font=("Inter", 10, "bold"),
            text_color=app_instance.acc_color,
        )
        self.title_label.grid(row=0, column=0, pady=(5, 0), sticky="n")
        
        # Content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
        
        self.grid_rowconfigure(1, weight=1)
        
        # Bind click
        if on_click:
            self.bind("<Button-1>", lambda e: on_click(self.widget_type))
        
        self.update_content()
    
    def update_content(self):
        """Update widget content."""
        for child in self.content_frame.winfo_children():
            child.destroy()
        
        callback_name = self.widget_type["callback"]
        callback = getattr(self.app, callback_name)
        callback(self.content_frame, "small_" + self.widget_type["id"])


class Dashboard(ctk.CTkFrame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.slots = []
        self.small_widgets = []
        self._available_widgets = list(SMALL_WIDGETS)  # Track available small widgets

        self.configure(fg_color="transparent")

        self._build_ui()
        self._create_big_widgets()
        self._create_small_widgets()

    def _build_ui(self):
        # Big widgets frame (top row)
        slots_frame = ctk.CTkFrame(self, fg_color="transparent")
        slots_frame.pack(fill="x", padx=10, pady=10)
        
        slots_frame.grid_columnconfigure(0, weight=1)
        slots_frame.grid_columnconfigure(1, weight=1)
        slots_frame.grid_columnconfigure(2, weight=1)

        for i in range(3):
            slot_frame = ctk.CTkFrame(slots_frame, fg_color="transparent")
            slot_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            self.slots.append(slot_frame)

        # Small widgets label
        available_label = ctk.CTkLabel(
            self,
            text="Widgets",
            font=("Inter", 14, "bold"),
            text_color=self.app.acc_color,
        )
        available_label.pack(anchor="w", padx=15, pady=(10, 5))

        # Scrollable frame for small widgets (4 columns grid)
        self.small_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            label_text="",
            scrollbar_button_color=self.app.acc_color,
            scrollbar_button_hover_color=self.app.acc_color,
        )
        self.small_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Configure 4 columns
        for i in range(4):
            self.small_scroll.grid_columnconfigure(i, weight=1, uniform="col")

    def _create_big_widgets(self):
        """Create the 3 big widget slots."""
        for i in range(3):
            widget_type = BIG_WIDGETS[i]
            slot_widget = SlotWidget(
                self.slots[i], i, widget_type, self.app, fg_color=self.app.bg_color
            )
            slot_widget.pack(fill="both", expand=True)
            self.slots[i] = slot_widget

    def _create_small_widgets(self):
        """Create small widgets in a 4-column grid."""
        # Clear existing
        for child in self.small_scroll.winfo_children():
            child.destroy()
        
        # Initialize small widgets list if empty (first time)
        if not hasattr(self, '_available_widgets') or not self._available_widgets:
            self._available_widgets = list(SMALL_WIDGETS)
        
        # Use the available widgets list for creating the grid
        widget_list = self._available_widgets
        
        # Create widgets in 4-column grid
        for idx, wtype in enumerate(widget_list):
            row = idx // 4
            col = idx % 4
            
            widget = SmallWidget(
                self.small_scroll,
                wtype,
                self.app,
                on_click=self._on_small_click,
                fg_color=self.app.bg_color
            )
            widget.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.small_widgets.append(widget)

    def _on_small_click(self, widget_type):
        """Handle small widget click - rotate with big widgets."""
        # Initialize available widgets list if needed
        if not hasattr(self, '_available_widgets'):
            self._available_widgets = list(SMALL_WIDGETS)
        
        # Get current big widgets
        big_0 = self.slots[0].widget_type if hasattr(self.slots[0], 'widget_type') else None
        big_1 = self.slots[1].widget_type if hasattr(self.slots[1], 'widget_type') else None
        big_2 = self.slots[2].widget_type if hasattr(self.slots[2], 'widget_type') else None
        
        # Rotate: clicked goes to slot 0, slot 0->1, slot 1->2, slot 2->available
        self._create_big_widget(0, widget_type)
        if big_0:
            self._create_big_widget(1, big_0)
        if big_1:
            self._create_big_widget(2, big_1)
        
        # Remove the clicked widget from available list
        if widget_type in self._available_widgets:
            self._available_widgets.remove(widget_type)
        
        # If there was a widget in slot 2, add it to the end of available widgets
        if big_2:
            if big_2 not in self._available_widgets:
                self._available_widgets.append(big_2)
        
        # Recreate small widgets grid
        self._create_small_widgets()
    
    def _create_big_widget(self, index, widget_type):
        """Create/update a big widget at the given index."""
        # Clear the slot
        for child in self.slots[index].winfo_children():
            child.destroy()
        
        slot_widget = SlotWidget(
            self.slots[index], index, widget_type, self.app, fg_color=self.app.bg_color
        )
        slot_widget.pack(fill="both", expand=True)
        self.slots[index] = slot_widget

    # Legacy methods for compatibility
    def load_state(self):
        pass

    def save_state(self):
        pass

    def _update_available_buttons(self):
        pass

    def add_to_slot(self, widget):
        pass
