import customtkinter as ctk
import os
import platform
import psutil
import subprocess

class SpeedScan(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SpeedScan - Central de Comando")
        self.geometry("950x600")
        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Barra Lateral
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="SPEEDSCAN", font=("Inter", 24, "bold"), text_color="#38bdf8").pack(pady=30)

        self.add_menu_button("Saúde do Sistema", self.show_status)
        self.add_menu_button("Instalar Apps Windows", lambda: self.install_package("wine winetricks"))
        self.add_menu_button("Suporte Android", lambda: self.install_package("waydroid"))
        self.add_menu_button("Jogos (Steam/Heroic)", lambda: self.install_package("steam heroic-games-launcher-bin"))
        
        ctk.CTkLabel(self.sidebar, text="---", text_color="gray").pack(pady=10)
        
        self.btn_clean = ctk.CTkButton(self.sidebar, text="OTIMIZAR AGORA", fg_color="#16a34a", hover_color="#15803d", font=("Inter", 14, "bold"), command=self.run_clean)
        self.btn_clean.pack(pady=20, padx=20)

        # Área de Conteúdo
        self.content = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=15)
        self.content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.label_info = ctk.CTkLabel(self.content, text="Aguardando comando...", font=("Inter", 16))
        self.label_info.pack(expand=True)

    def add_menu_button(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, font=("Inter", 13), fg_color="transparent", border_width=1, command=command)
        btn.pack(pady=8, padx=20, fill="x")

    def show_status(self):
        mem = psutil.virtual_memory()
        status = f"📊 Memória RAM: {mem.percent}% em uso\n💻 Sistema: {platform.system()} (Solus)\n\nHardware pronto para novas instalações."
        self.label_info.configure(text=status)

    def install_package(self, package):
        self.label_info.configure(text=f"Solicitando autorização para instalar: {package}...")
        # pkexec abre a janela de senha do sistema (GUI)
        comando = f"pkexec eopkg it {package} -y"
        threading_cmd = f"({comando}) &"
        os.system(threading_cmd)

    def run_clean(self):
        # Para a limpeza, mantemos o terminal para você ver o progresso dos arquivos sendo apagados
        subprocess.Popen(["konsole", "-e", "speedscan"])

if __name__ == "__main__":
    app = SpeedScan()
    app.mainloop()
