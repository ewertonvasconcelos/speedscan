import customtkinter as ctk
import os
import platform
import psutil
import subprocess
from PIL import Image, ImageTk

class SpeedScan(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("SpeedScan - Otimizador Universal")
        self.geometry("1000x800")
        self.wm_class = "speedscan"

        icon_path = os.path.expanduser("~/.local/share/icons/speedscan_icon.png")
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
            self.icon_photo = ImageTk.PhotoImage(img)
            self.wm_iconphoto(True, self.icon_photo)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="⚡ SPEEDSCAN", font=("Orbitron", 22, "bold"), text_color="#38bdf8").pack(pady=30)

        # Tabs
        self.tab_view = ctk.CTkTabview(self, corner_radius=15, segmented_button_selected_color="#38bdf8")
        self.tab_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        for name in ["🏠 Início", "💻 Sistema", "🚀 Otimização", "🎮 Gamer", "🌐 DNS", "🎨 Temas"]:
            self.tab_view.add(name)

        self.setup_inicio_tab()
        self.setup_sistema_tab()
        self.setup_otimizacao_tab()
        self.setup_gamer_tab()
        self.setup_dns_tab()
        self.setup_temas_tab()

        self.change_theme("Escuro")

    def change_theme(self, theme):
        if theme == "Default":
            ctk.set_appearance_mode("system")
            self.sidebar.configure(fg_color=None)
        elif theme == "Escuro":
            ctk.set_appearance_mode("dark")
            self.sidebar.configure(fg_color="#0a0a0a")
            self.tab_view.configure(fg_color="#121212")
        elif theme == "Claro":
            ctk.set_appearance_mode("light")
            self.sidebar.configure(fg_color="#f2f2f2")
            self.tab_view.configure(fg_color="#ffffff")
        elif theme == "Cinza":
            ctk.set_appearance_mode("dark")
            self.sidebar.configure(fg_color="#3d3d3d")
            self.tab_view.configure(fg_color="#575757")

    def create_standard_button(self, master, text, command):
        return ctk.CTkButton(master, text=text, command=command, 
                             fg_color="#38bdf8", hover_color="#0ea5e9", text_color="#000000",
                             width=400, height=45, font=("Inter", 14, "bold"))

    def setup_inicio_tab(self):
        tab = self.tab_view.tab("🏠 Início")
        ctk.CTkLabel(tab, text="SPEEDSCAN", font=("Orbitron", 38, "bold"), text_color="#38bdf8").pack(pady=(150, 10))
        ctk.CTkLabel(tab, text="Otimizador Universal para seu Sistema", font=("Inter", 18)).pack()

    def setup_sistema_tab(self):
        tab = self.tab_view.tab("💻 Sistema")
        laptop = os.popen("cat /sys/class/dmi/id/product_name").read().strip() or "Sistema Linux"
        cpu = os.popen("grep 'model name' /proc/cpuinfo | head -n1 | cut -d: -f2").read().strip()
        mem = psutil.virtual_memory()
        info = [("💻 MÁQUINA:", laptop), ("💿 S.O:", platform.platform()), ("🧠 CPU:", cpu), 
                ("📟 RAM:", f"{mem.used/(1024**3):.2f} GB / {mem.total/(1024**3):.2f} GB")]
        for label, val in info:
            f = ctk.CTkFrame(tab, fg_color="transparent")
            f.pack(fill="x", padx=40, pady=8)
            ctk.CTkLabel(f, text=label, font=("Inter", 14, "bold"), text_color="#38bdf8", width=160, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=val, font=("Consolas", 14)).pack(side="left", padx=10)

    def setup_otimizacao_tab(self):
        tab = self.tab_view.tab("🚀 Otimização")
        ctk.CTkLabel(tab, text="Manutenção do Sistema", font=("Inter", 18, "bold")).pack(pady=20)
        opcoes = [
            ("Limpar Cache do Sistema", "sudo eopkg dc && sudo rm -rf /var/cache/*"),
            ("Corrigir Erros de Pacotes", "sudo eopkg check && sudo eopkg rdb"),
            ("Encontrar Atualizações de Software", "sudo eopkg up"),
            ("Otimizar Memória Virtual (Swap)", "sudo swapoff -a && sudo swapon -a")
        ]
        for nome, comando in opcoes:
            self.create_standard_button(tab, nome, lambda c=comando: self.run_cmd(c)).pack(pady=10)

    def setup_gamer_tab(self):
        tab = self.tab_view.tab("🎮 Gamer")
        ctk.CTkLabel(tab, text="Instalação de Plataformas", font=("Inter", 18, "bold")).pack(pady=20)
        for name, pkg in [("Steam", "steam"), ("Heroic Games", "heroic-games-launcher-bin"), ("Lutris", "lutris")]:
            self.create_standard_button(tab, f"Instalar {name}", lambda p=pkg: self.run_cmd(f"eopkg it {p} -y")).pack(pady=10)

    def setup_dns_tab(self):
        tab = self.tab_view.tab("🌐 DNS")
        ctk.CTkLabel(tab, text="Otimização de Rede", font=("Inter", 18, "bold")).pack(pady=20)
        self.create_standard_button(tab, "Google DNS", lambda: self.set_dns("8.8.8.8,8.8.4.4")).pack(pady=10)
        self.create_standard_button(tab, "Cloudflare DNS", lambda: self.set_dns("1.1.1.1,1.0.0.1")).pack(pady=10)

    def setup_temas_tab(self):
        tab = self.tab_view.tab("🎨 Temas")
        ctk.CTkLabel(tab, text="Personalização Visual", font=("Inter", 18, "bold")).pack(pady=20)
        for t in ["Default", "Escuro", "Claro", "Cinza"]:
            self.create_standard_button(tab, t, lambda m=t: self.change_theme(m)).pack(pady=10)

    def run_cmd(self, cmd):
        subprocess.Popen(["konsole", "--hold", "-e", "bash", "-c", f"pkexec {cmd}"])

    def set_dns(self, servers):
        cmd = f'nmcli device modify $(nmcli -t -f DEVICE,TYPE device | grep ethernet | cut -d: -f1 | head -n1) ipv4.dns "{servers}" && nmcli device reapply $(nmcli -t -f DEVICE,TYPE device | grep ethernet | cut -d: -f1 | head -n1)'
        self.run_cmd(cmd)

if __name__ == "__main__":
    app = SpeedScan()
    app.after(200, lambda: app.wm_instanceclass("speedscan"))
    app.mainloop()
