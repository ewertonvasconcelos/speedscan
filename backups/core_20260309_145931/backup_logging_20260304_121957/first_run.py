#!/usr/bin/env python3
# Assistente de primeira execução (boas-vindas) com níveis de expertise
# Versão 0.3.1-beta

import customtkinter as ctk

class FirstRunWizard(ctk.CTkToplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.title("Bem-vindo ao SpeedScan!")
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

        welcome = ctk.CTkLabel(self.content_frame, text="Obrigado por instalar o SpeedScan! Vamos configurar suas preferências.",
                                font=("Inter", 12), justify="left", wraplength=500)
        welcome.pack(pady=10)

        name_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(name_frame, text="Seu nome:", font=("Inter", 12)).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="Digite seu nome")
        self.name_entry.pack(fill="x", pady=5)
        self.name_entry.insert(0, config.get("username", ""))

        theme_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(theme_frame, text="Tema preferido:", font=("Inter", 12)).pack(anchor="w")
        self.theme_var = ctk.StringVar(value="Padrão (Roxo)")
        theme_menu = ctk.CTkOptionMenu(theme_frame, values=["Padrão (Roxo)", "Cinza Profissional", "Escuro Total", "Claro Clean"],
                                       variable=self.theme_var, cursor="left_ptr")
        theme_menu.pack(anchor="w", pady=5)

        level_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        level_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(level_frame, text="Seu nível de conhecimento:", font=("Inter", 12)).pack(anchor="w")
        self.level_var = ctk.StringVar(value="iniciante")
        iniciante_radio = ctk.CTkRadioButton(level_frame, text="Iniciante (apenas funções básicas)", variable=self.level_var, value="iniciante", cursor="hand2")
        iniciante_radio.pack(anchor="w", pady=2)
        intermediario_radio = ctk.CTkRadioButton(level_frame, text="Intermediário (funções básicas + algumas avançadas)", variable=self.level_var, value="intermediario", cursor="hand2")
        intermediario_radio.pack(anchor="w", pady=2)
        avancado_radio = ctk.CTkRadioButton(level_frame, text="Avançado (todas as funções, sem restrições)", variable=self.level_var, value="avancado", cursor="hand2")
        avancado_radio.pack(anchor="w", pady=2)

        tip = ctk.CTkLabel(self.content_frame, text="💡 Você pode alterar essas configurações depois a qualquer momento na aba 'Configurações'.",
                            font=("Inter", 10, "italic"), text_color="#888888")
        tip.pack(pady=20)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=20)
        ctk.CTkButton(btn_frame, text="Concluir", command=self.save_and_close,
                      fg_color=self.parent.acc_color, width=150, cursor="hand2").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Pular", command=self.destroy,
                      fg_color="gray", width=100, cursor="hand2").pack(side="left", padx=10)

    def save_and_close(self):
        self.config["username"] = self.name_entry.get() or "usuário"
        theme_map = {
            "Padrão (Roxo)": "default",
            "Cinza Profissional": "grey",
            "Escuro Total": "dark",
            "Claro Clean": "light"
        }
        self.config["theme"] = theme_map.get(self.theme_var.get(), "default")
        level = self.level_var.get()
        if level == "iniciante":
            self.config["simple_mode"] = True
            self.config["expert_level"] = 1
        elif level == "intermediario":
            self.config["simple_mode"] = False
            self.config["expert_level"] = 2
        else:
            self.config["simple_mode"] = False
            self.config["expert_level"] = 3
        self.parent.config.update(self.config)
        self.parent._save_config()
        self.parent.show_toast("Configurações salvas! Algumas alterações podem exigir reinício.")
        self.destroy()

