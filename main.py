import customtkinter as ctk
import os, platform, psutil, subprocess, threading, json, time

# Verificação de Sistema
IS_LINUX = platform.system() == "Linux"

class SpeedScan(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"SpeedScan Ultimate - [{platform.system()}]")
        self.geometry("1100x700")
        
        # Cores e Temas
        self.accent = "#a855f7" 
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0f172a")

        # Layout Principal (Grid)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Barra Lateral (Menu)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1e293b")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="⚡ SpeedScan", font=("Arial", 24, "bold"), text_color=self.accent).pack(pady=30)

        # Abas (Tabview)
        self.tab_view = ctk.CTkTabview(self, corner_radius=15, segmented_button_selected_color=self.accent, fg_color="#0f172a")
        self.tab_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.abas = ["🏠 Início", "💻 Sistema", "🚀 Otimização", "🎮 Gamer", "🌐 Rede", "🛠️ Drivers", "🎨 Temas"]
        for aba in self.abas:
            self.tab_view.add(aba)

        self.construir_abas()

    def construir_abas(self):
        # --- ABA INÍCIO ---
        ctk.CTkLabel(self.tab_view.tab("🏠 Início"), text="Bem-vindo ao SpeedScan", font=("Arial", 32, "bold")).pack(pady=100)
        ctk.CTkLabel(self.tab_view.tab("🏠 Início"), text="Seu sistema está sendo monitorado.", font=("Arial", 16)).pack()

        # --- ABA SISTEMA (Monitoramento Real) ---
        self.sys_frame = self.tab_view.tab("💻 Sistema")
        self.lbl_cpu = ctk.CTkLabel(self.sys_frame, text="CPU: --%", font=("Arial", 18))
        self.lbl_cpu.pack(pady=10)
        self.lbl_ram = ctk.CTkLabel(self.sys_frame, text="RAM: --%", font=("Arial", 18))
        self.lbl_ram.pack(pady=10)
        self.atualizar_monitor()

        # --- ABA OTIMIZAÇÃO (Detecção de Sistema Inteligente) ---
        t_ot = self.tab_view.tab("🚀 Otimização")
        if IS_LINUX:
            btn_txt = "Limpar Cache do Sistema (Solus)"
            cmd = "pkexec eopkg dc"
        else:
            btn_txt = "Limpar Arquivos Temporários (Windows)"
            cmd = "del /q/f/s %TEMP%\\*"

        ctk.CTkButton(t_ot, text=btn_txt, command=lambda: self.executar(cmd), fg_color=self.accent).pack(pady=20)
        ctk.CTkButton(t_ot, text="Otimizar Memória RAM", command=lambda: self.executar("gc"), fg_color="#10b981").pack(pady=10)

        # --- ABA GAMER ---
        t_gm = self.tab_view.tab("🎮 Gamer")
        ctk.CTkLabel(t_gm, text="Modo Gamer Ativo", font=("Arial", 20)).pack(pady=20)
        ctk.CTkSwitch(t_gm, text="Prioridade Máxima para Jogos", progress_color=self.accent).pack()

        # --- ABA REDE ---
        t_rd = self.tab_view.tab("🌐 Rede")
        ctk.CTkButton(t_rd, text="Resetar DNS / Flush", command=lambda: self.executar("dns"), fg_color=self.accent).pack(pady=20)

        # --- ABA DRIVERS ---
        t_dr = self.tab_view.tab("🛠️ Drivers")
        ctk.CTkLabel(t_dr, text="Verificando integridade de drivers...", font=("Arial", 14)).pack(pady=20)

        # --- ABA TEMAS ---
        t_tm = self.tab_view.tab("🎨 Temas")
        ctk.CTkSegmentedButton(t_tm, values=["Dark", "Light", "Solar"], selected_color=self.accent).pack(pady=20)

    def atualizar_monitor(self):
        self.lbl_cpu.configure(text=f"CPU: {psutil.cpu_percent()}%")
        self.lbl_ram.configure(text=f"RAM: {psutil.virtual_memory().percent}%")
        self.after(2000, self.atualizar_monitor)

    def executar(self, acao):
        # Aqui entra a lógica de comando que detecta o OS
        print(f"Executando: {acao} no {platform.system()}")
        threading.Thread(target=lambda: os.system(acao), daemon=True).start()

if __name__ == "__main__":
    app = SpeedScan()
    app.mainloop()
