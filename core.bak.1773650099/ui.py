#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI utility functions for the SpeedScan application.
Version 1.0.0
"""
import customtkinter as ctk

def add_tooltip(widget, text):
    tooltip = None
    def enter(event):
        nonlocal tooltip
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        tooltip = ctk.CTkToplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tooltip, text=text, justify="left",
                              fg_color="#2b2b2b", text_color="white",
                              corner_radius=5, padx=5, pady=5)
        label.pack()
    def leave(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

def create_card_grid(parent, items, tag_prefix, acc_color, bg_color, text_color, command_callback):
    grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
    grid_frame.pack(fill="x", pady=5)
    ping_labels = []
    for idx, (label, cmd, is_dns) in enumerate(items):
        row, col = divmod(idx, 3)
        card = ctk.CTkFrame(grid_frame, fg_color=bg_color, corner_radius=10,
                            border_width=1, border_color=acc_color)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        card.grid_propagate(False)
        card.configure(height=150)
        title = ctk.CTkLabel(card, text=label, font=("Inter", 14, "bold"), text_color=acc_color)
        title.pack(pady=(10,5))
        if cmd == "ping":
            ping_label = ctk.CTkLabel(card, text="-- ms", font=("Inter", 18, "bold"), text_color=text_color)
            ping_label.pack(expand=True)
            ping_labels.append(ping_label)
            btn = ctk.CTkButton(card, text="Start", fg_color=acc_color,
                                command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d),
                                cursor="hand2")
            btn.pack(pady=5)
        else:
            btn = ctk.CTkButton(card, text="Run", fg_color=acc_color,
                                command=lambda c=cmd, t=tag_prefix, d=is_dns: command_callback(c, t, d),
                                cursor="hand2")
            btn.pack(expand=True)
    for i in range(3):
        grid_frame.columnconfigure(i, weight=1)
    return ping_labels

def add_console(parent, tag_prefix, acc_color, toggle_callback):
    console = ctk.CTkTextbox(parent, height=150, fg_color="#1e1e1e", text_color="#ffffff",
                             font=("Consolas", 10), corner_radius=10)
    btn = ctk.CTkButton(parent, text="Details ▼", fg_color=acc_color,
                        command=lambda: toggle_callback(tag_prefix), cursor="hand2")
    return btn, console
