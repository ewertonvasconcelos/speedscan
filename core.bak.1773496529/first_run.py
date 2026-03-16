#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
First run wizard for SpeedScan - displayed on first start to configure basic settings.
Version 1.0.0
"""
import customtkinter as ctk

from core import config


class FirstRunWizard(ctk.CTkToplevel):
    def __init__(self, parent, config_data):
        super().__init__(parent)
        self.parent = parent
        self.config = config_data

        self.title("Welcome to SpeedScan!")
        self.geometry("600x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(self, text="⚡ SpeedScan", font=("Inter", 24, "bold"),
                              text_color=parent.acc_color)
        title.grid(row=0, column=0, pady=(20,10))

        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        welcome = ctk.CTkLabel(self.content_frame,
                               text="Thank you for installing SpeedScan! Let's configure your preferences.",
                               font=("Inter", 12), justify="left", wraplength=500)
        welcome.pack(pady=10)

        name_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(name_frame, text="Your name:", font=("Inter", 12)).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="Enter your name")
        self.name_entry.pack(fill="x", pady=5)
        self.name_entry.insert(0, config_data.get("username", ""))

        theme_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(theme_frame, text="Preferred theme:", font=("Inter", 12)).pack(anchor="w")
        self.theme_var = ctk.StringVar(value="Still")
        theme_menu = ctk.CTkOptionMenu(theme_frame, values=["Still", "Tecno", "Snow"],
                                       variable=self.theme_var, cursor="left_ptr")
        theme_menu.pack(anchor="w", pady=5)

        level_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        level_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(level_frame, text="Your experience level:", font=("Inter", 12)).pack(anchor="w")
        self.level_var = ctk.StringVar(value="beginner")

        beginner_radio = ctk.CTkRadioButton(level_frame, text="Beginner (basic features only)",
                                            variable=self.level_var, value="beginner", cursor="hand2")
        beginner_radio.pack(anchor="w", pady=2)

        intermediate_radio = ctk.CTkRadioButton(level_frame, text="Intermediate (basic + some advanced)",
                                                variable=self.level_var, value="intermediate", cursor="hand2")
        intermediate_radio.pack(anchor="w", pady=2)

        advanced_radio = ctk.CTkRadioButton(level_frame, text="Advanced (all features, no restrictions)",
                                            variable=self.level_var, value="advanced", cursor="hand2")
        advanced_radio.pack(anchor="w", pady=2)

        tip = ctk.CTkLabel(self.content_frame,
                           text="💡 You can change these settings later at any time in the 'Settings' tab.",
                           font=("Inter", 10, "italic"), text_color="#888888")
        tip.pack(pady=20)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=20)

        ctk.CTkButton(btn_frame, text="Finish", command=self.save_and_close,
                      fg_color=self.parent.acc_color, width=150, cursor="hand2").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy,
                      fg_color="gray", width=100, cursor="hand2").pack(side="left", padx=10)

    def save_and_close(self):
        self.config["username"] = self.name_entry.get() or "User"

        theme_map = {
            "Still": "grey",
            "Tecno": "dark",
            "Snow": "light"
        }
        self.config["theme"] = theme_map.get(self.theme_var.get(), "default")

        level = self.level_var.get()
        if level == "beginner":
            self.config["simple_mode"] = True
            self.config["expert_level"] = 1
        elif level == "intermediate":
            self.config["simple_mode"] = False
            self.config["expert_level"] = 2
        else:
            self.config["simple_mode"] = False
            self.config["expert_level"] = 3

        self.parent.config_data.update(self.config)
        self.parent._save_config()
        self.parent.show_toast("Settings saved! Some changes may require restart.")
        self.destroy()
