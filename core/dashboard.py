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
        """Update widget content."""
        if self.content_frame:
            self.content_frame.destroy()
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Center content
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        callback_name = self.widget_type["callback"]
        callback = getattr(self.app, callback_name)
        
        # Get data from widget method (no parameters)
        data = callback()
        
        # Build UI based on widget type and data
        self._build_widget_ui(data)

    def _build_widget_ui(self, data):
        """Build UI based on widget type and data."""
        widget_id = self.widget_type["id"]
        
        if widget_id == "disks":
            self._build_disks_ui(data)
        elif widget_id == "gpu":
            self._build_gpu_ui(data)
        elif widget_id == "battery":
            self._build_battery_ui(data)
        elif widget_id == "cpu":
            self._build_cpu_ui(data)
        elif widget_id == "ram":
            self._build_ram_ui(data)
        elif widget_id == "hostname":
            self._build_hostname_ui(data)
        elif widget_id == "distro":
            self._build_distro_ui(data)
        elif widget_id == "kernel":
            self._build_kernel_ui(data)
        elif widget_id == "temps":
            self._build_temps_ui(data)
        else:
            # Default: show data as text
            label = ctk.CTkLabel(self.content_frame, text=str(data), 
                                font=("Inter", 12), text_color=self.app.text_color)
            label.pack(anchor="center", expand=True)
    
    def _build_disks_ui(self, data):
        """Build disks UI from data."""
        if not data:
            label = ctk.CTkLabel(self.content_frame, text="N/A", 
                                font=("Inter", 16, "bold"), text_color=self.app.text_color)
            label.pack(anchor="center", expand=True)
            return
        
        # Show root and home usage
        for key, disk_data in data.items():
            percent = disk_data['percent']
            used_gb = disk_data['used'] // (1024**3)
            total_gb = disk_data['total'] // (1024**3)
            
            # Disk name
            name_label = ctk.CTkLabel(self.content_frame, text=f"💾 {disk_data['name']}", 
                                    font=("Inter", 11, "bold"), text_color=self.app.acc_color)
            name_label.pack(anchor="w", padx=10, pady=(8, 2))
            
            # Progress bar
            progress = ctk.CTkProgressBar(self.content_frame, orientation="horizontal")
            progress.set(percent / 100)
            progress.configure(
                progress_color=self._get_usage_color(percent),
                fg_color="#3B3B3B",
                height=12
            )
            progress.pack(fill="x", padx=10, pady=(0, 2))
            
            # Usage text
            usage_label = ctk.CTkLabel(self.content_frame, 
                                    text=f"{percent}% ({used_gb}GB / {total_gb}GB)",
                                    font=("Inter", 10), text_color=self._get_usage_color(percent))
            usage_label.pack(anchor="w", padx=10, pady=(0, 5))
    
    def _build_gpu_ui(self, data):
        """Build GPU UI from data."""
        label = ctk.CTkLabel(self.content_frame, text=f"🎮 {data}", 
                            font=("Inter", 16, "bold"), text_color=self.app.acc_color)
        label.pack(anchor="center", expand=True)
    
    def _build_battery_ui(self, data):
        """Build battery UI from data."""
        if isinstance(data, str):  # "No battery"
            label = ctk.CTkLabel(self.content_frame, text="🔋 N/A", 
                                font=("Inter", 16, "bold"), text_color=self.app.text_color)
            label.pack(anchor="center", expand=True)
            return
        
        percent = data['percent']
        plugged = data['plugged']
        status = data['status']
        icon = "🔌" if plugged else "🔋"
        
        # Icon and percentage
        icon_label = ctk.CTkLabel(self.content_frame, text=f"{icon} {percent}%", 
                                 font=("Inter", 20, "bold"), 
                                 text_color=self._get_battery_color(percent))
        icon_label.pack(anchor="center", expand=True)
        
        # Status
        status_label = ctk.CTkLabel(self.content_frame, text=status, 
                                   font=("Inter", 10), 
                                   text_color=self._get_battery_color(percent))
        status_label.pack(anchor="center", pady=(0, 5))
    
    def _get_usage_color(self, percent):
        """Get color based on usage percentage."""
        if percent >= 90:
            return "#ff4757"
        elif percent >= 75:
            return "#ffa502"
        elif percent >= 50:
            return "#ffd32c"
        else:
            return "#26de81"
    
    def _get_battery_color(self, percent):
        """Get color based on battery percentage."""
        if percent <= 20:
            return "#ff4757"
        elif percent <= 50:
            return "#ffa502"
        else:
            return "#26de81"
    
    def _get_temp_color(self, temp):
        """Get color based on temperature."""
        if temp >= 80:
            return "#ff4757"
        elif temp >= 70:
            return "#ffa502"
        elif temp >= 60:
            return "#ffd32c"
        else:
            return "#26de81"
    
    def _get_temp_icon(self, temp):
        """Get icon based on temperature."""
        if temp >= 80:
            return "🔥"
        elif temp >= 70:
            return "♨️"
        elif temp >= 60:
            return "🌡️"
        else:
            return "❄️"

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
        
        # Get data from widget method (no parameters)
        data = callback()
        
        # Build small UI based on widget type and data
        self._build_small_widget_ui(data)
    
    def _build_small_widget_ui(self, data):
        """Build small widget UI based on widget type and data."""
        widget_id = self.widget_type["id"]
        
        if widget_id == "disks":
            self._build_small_disks_ui(data)
        elif widget_id == "gpu":
            self._build_small_gpu_ui(data)
        elif widget_id == "battery":
            self._build_small_battery_ui(data)
        elif widget_id == "cpu":
            self._build_small_cpu_ui(data)
        elif widget_id == "ram":
            self._build_small_ram_ui(data)
        elif widget_id == "hostname":
            self._build_small_hostname_ui(data)
        elif widget_id == "distro":
            self._build_small_distro_ui(data)
        elif widget_id == "kernel":
            self._build_small_kernel_ui(data)
        elif widget_id == "temps":
            self._build_small_temps_ui(data)
        else:
            # Default: show data as text
            label = ctk.CTkLabel(self.content_frame, text=str(data), 
                                font=("Inter", 10), text_color=self.app.text_color)
            label.pack(anchor="center", expand=True)
    
    def _build_small_disks_ui(self, data):
        """Build small disks UI from data."""
        if not data:
            label = ctk.CTkLabel(self.content_frame, text="💾 N/A", 
                                font=("Inter", 14, "bold"), text_color=self.app.text_color)
            label.pack(anchor="center", expand=True)
            return
        
        # Show main disk percentage
        main_percent = data['root']['percent']
        color = self._get_usage_color(main_percent)
        
        label = ctk.CTkLabel(self.content_frame, text=f"💾 {main_percent}%", 
                            font=("Inter", 14, "bold"), text_color=color)
        label.pack(anchor="center", expand=True)
    
    def _build_small_gpu_ui(self, data):
        """Build small GPU UI from data."""
        label = ctk.CTkLabel(self.content_frame, text="🎮 GPU", 
                            font=("Inter", 14, "bold"), text_color=self.app.acc_color)
        label.pack(anchor="center", expand=True)
    
    def _build_small_battery_ui(self, data):
        """Build small battery UI from data."""
        if isinstance(data, str):  # "No battery"
            label = ctk.CTkLabel(self.content_frame, text="🔋 N/A", 
                                font=("Inter", 14, "bold"), text_color=self.app.text_color)
            label.pack(anchor="center", expand=True)
            return
        
        percent = data['percent']
        plugged = data['plugged']
        icon = "🔌" if plugged else "🔋"
        color = self._get_battery_color(percent)
        
        label = ctk.CTkLabel(self.content_frame, text=f"{icon} {percent}%", 
                            font=("Inter", 14, "bold"), text_color=color)
        label.pack(anchor="center", expand=True)
    
    def _build_small_hostname_ui(self, data):
        """Build small hostname UI from data."""
        label = ctk.CTkLabel(self.content_frame, text=f"🖥️ {data}", 
                            font=("Inter", 14, "bold"), text_color=self.app.acc_color)
        label.pack(anchor="center", expand=True)
    
    def _build_small_distro_ui(self, data):
        """Build small distro UI from data."""
        label = ctk.CTkLabel(self.content_frame, text=f"🐧 {data}", 
                            font=("Inter", 14, "bold"), text_color=self.app.acc_color)
        label.pack(anchor="center", expand=True)
    
    def _build_small_kernel_ui(self, data):
        """Build small kernel UI from data."""
        label = ctk.CTkLabel(self.content_frame, text=f"⚙️ {data}", 
                            font=("Inter", 14, "bold"), text_color=self.app.acc_color)
        label.pack(anchor="center", expand=True)
    
    def _build_small_cpu_ui(self, data):
        """Build small CPU UI from data."""
        if isinstance(data, dict):
            percent = data.get('percent', 0)
            color = self._get_usage_color(percent)
            label = ctk.CTkLabel(self.content_frame, text=f"🔥 {percent}%", 
                                font=("Inter", 14, "bold"), text_color=color)
        else:
            label = ctk.CTkLabel(self.content_frame, text=f"🔥 {data}", 
                                font=("Inter", 14, "bold"), text_color=self.app.acc_color)
        label.pack(anchor="center", expand=True)
    
    def _build_small_ram_ui(self, data):
        """Build small RAM UI from data."""
        if isinstance(data, dict):
            percent = data.get('percent', 0)
            color = self._get_usage_color(percent)
            label = ctk.CTkLabel(self.content_frame, text=f"💾 {percent}%", 
                                font=("Inter", 14, "bold"), text_color=color)
        else:
            label = ctk.CTkLabel(self.content_frame, text=f"💾 {data}", 
                                font=("Inter", 14, "bold"), text_color=self.app.acc_color)
        label.pack(anchor="center", expand=True)
    
    def _build_small_temps_ui(self, data):
        """Build small temperature UI from data."""
        if isinstance(data, dict):
            temp = data.get('temp', 0)
            color = self._get_temp_color(temp)
            icon = self._get_temp_icon(temp)
            label = ctk.CTkLabel(self.content_frame, text=f"{icon} {temp}°C", 
                                font=("Inter", 14, "bold"), text_color=color)
        else:
            label = ctk.CTkLabel(self.content_frame, text=f"🌡️ {data}", 
                                font=("Inter", 14, "bold"), text_color=self.app.acc_color)
        label.pack(anchor="center", expand=True)
    
    def _get_temp_color(self, temp):
        """Get color based on temperature."""
        if temp >= 80:
            return "#ff4757"
        elif temp >= 70:
            return "#ffa502"
        elif temp >= 60:
            return "#ffd32c"
        else:
            return "#26de81"
    
    def _get_temp_icon(self, temp):
        """Get icon based on temperature."""
        if temp >= 80:
            return "🔥"
        elif temp >= 70:
            return "♨️"
        elif temp >= 60:
            return "🌡️"
        else:
            return "❄️"


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
