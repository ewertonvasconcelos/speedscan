import customtkinter as ctk
import os, platform, psutil, subprocess, threading, json, time

CONFIG_FILE = os.path.expanduser("~/.speedscan_conf")
ICON_PATH = os.path.expanduser("~/speedscan/icon.png")

def get_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"theme": "default", "geometry": "1100x900"}

conf = get_config()
themes = {
    "default": ("dark", "#0f172a", "#1e293b", "#a855f7"),
    "grey": ("dark", "#2a2a2a", "#3d3d3d", "#ffffff"),
    "dark": ("dark", "#000000", "#1a1a1a", "#10b981"),
    "light": ("light", "#ffffff", "#f0f0f0", "#000000")
}
mode, bg, side_color, accent = themes.get(conf.get("theme", "default"))
ctk.set_appearance_mode(mode)

class SpeedScan(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = conf
        self.title("SpeedScan")
        self.geometry(self.config.get("geometry", "1100x900"))
        self.configure(fg_color=bg)
        
        if os.path.exists(ICON_PATH):
            try:
                from tkinter import PhotoImage
                self.icon_img = PhotoImage(file=ICON_PATH)
                self.tk.call('wm', 'iconphoto', self._w, self.icon_img)
            except: pass

        self.consoles = {"ot": False, "drv": False, "net": False, "ping": False}
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=side_color)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="⚡ SpeedScan", font=("Orbitron", 28, "bold"), text_color="#a855f7").pack(pady=40, padx=20)
        
        self.tab_view = ctk.CTkTabview(self, corner_radius=15, segmented_button_selected_color="#a855f7", fg_color=bg)
        self.tab_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        tabs = ["🏠 Início", "💻 Sistema", "🚀 Otimização", "🎮 Gamer", "🌐 Rede", "🛠️ Drivers", "🎨 Temas"]
        for n in tabs: self.tab_view.add(n)
        
        # CORREÇÃO DEFINITIVA DO ERRO DE EXPANSÃO
        def fix_layout():
            try:
                # Força o botão de abas a ocupar todo o espaço horizontal sem usar o argumento 'expand'
                self.tab_view._segmented_button.grid(sticky="ew")
                self.tab_view._segmented_button.master.grid_columnconfigure(0, weight=1)
            except: pass
        self.after(200, fix_layout)
        
        self.setup_tabs()
        self.set_theme(self.config.get("theme", "default"), save=False)
        self.bind_all("<Button-4>", self._on_mousewheel); self.bind_all("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        try:
            if event.num == 4: self.scroll_gm._parent_canvas.yview_scroll(-1, "units")
            elif event.num == 5: self.scroll_gm._parent_canvas.yview_scroll(1, "units")
        except: pass

    def create_btn(self, m, t, c):
        return ctk.CTkButton(m, text=t, command=c, fg_color="#a855f7", hover_color="#9333ea", text_color="#ffffff", width=400, height=40, font=("Inter", 14, "bold"))

    def setup_tabs(self):
        ctk.CTkLabel(self.tab_view.tab("🏠 Início"), text="⚡ SpeedScan", font=("Orbitron", 54, "bold"), text_color="#a855f7").pack(expand=True)
        self.systab = self.tab_view.tab("💻 Sistema"); self.update_sys_info()
        
        self.t_ot = self.tab_view.tab("🚀 Otimização")
        for n, c in [("Limpeza Profunda", "sudo eopkg dc"), ("Otimizar RAM/Swap", "sudo swapoff -a && sudo swapon -a"), ("Verificar Integridade", "sudo eopkg check")]: 
            self.create_btn(self.t_ot, n, lambda cmd=c: self.run_action(cmd, "ot")).pack(pady=10)
        self.btn_ot = ctk.CTkButton(self.t_ot, text="Detalhes ⌄", width=120, height=32, corner_radius=16, fg_color="transparent", text_color=accent, font=("Inter", 12, "bold"), hover_color=side_color, command=lambda: self.toggle_console("ot"))
        self.log_ot = ctk.CTkTextbox(self.t_ot, height=200, fg_color=side_color, text_color="#10b981", font=("Consolas", 13), corner_radius=12)

        t_gm = self.tab_view.tab("🎮 Gamer")
        self.scroll_gm = ctk.CTkScrollableFrame(t_gm, fg_color="transparent")
        self.scroll_gm.pack(fill="both", expand=True); self.scroll_gm.columnconfigure(0, weight=1)
        apps = [("Steam", "steam"), ("Heroic", "heroic-games-launcher-bin"), ("Lutris", "lutris"), ("Wine", "wine"), ("Bottles", "bottles"), ("MangoHud", "mangohud"), ("Goverlay", "goverlay"), ("Proton GE", "proton-ge-custom")]
        for i, (n, p) in enumerate(apps):
            self.create_btn(self.scroll_gm, f"Instalar {n}", lambda pkg=p: self.run_action(f"sudo eopkg it {pkg} -y", "ot")).grid(row=i, column=0, pady=5)
            
        self.t_net = self.tab_view.tab("🌐 Rede")
        self.create_btn(self.t_net, "Testar Latência (Ping)", self.toggle_ping).pack(pady=10)
        self.ping_frame = ctk.CTkFrame(self.t_net, fg_color=side_color, corner_radius=12)
        self.net_status = ctk.CTkLabel(self.ping_frame, text="Ping: -- ms | IP: --", font=("Consolas", 14, "bold"), text_color="#10b981")
        self.net_status.pack(pady=10, padx=20)

        self.dns_container = ctk.CTkFrame(self.t_net, fg_color="transparent")
        self.dns_container.pack(fill="x")
        for n, c in [("Cloudflare DNS", "nmcli dev mod eth0 ipv4.dns '1.1.1.1'"), ("Google DNS", "nmcli dev mod eth0 ipv4.dns '8.8.8.8'"), ("DNS Automático", "nmcli dev mod eth0 ipv4.dns ''")]:
            self.create_btn(self.dns_container, n, lambda cmd=c: self.run_action(cmd, "net")).pack(pady=10)
        
        self.btn_net = ctk.CTkButton(self.t_net, text="Detalhes ⌄", width=120, height=32, corner_radius=16, fg_color="transparent", text_color=accent, font=("Inter", 12, "bold"), hover_color=side_color, command=lambda: self.toggle_console("net"))
        self.log_net = ctk.CTkTextbox(self.t_net, height=150, fg_color=side_color, text_color="#10b981", font=("Consolas", 13), corner_radius=12)

        self.t_drv = self.tab_view.tab("🛠️ Drivers")
        for n, c in [
            ("Listar Hardware PCI (Vídeo/Rede)", "lspci -nnk"),
            ("Dispositivos USB Conectados", "lsusb"),
            ("Módulos do Kernel (Drivers Ativos)", "lsmod"),
            ("Informações de CPU Detalhadas", "lscpu"),
            ("Status de Som e Áudio", "aplay -l"),
            ("Verificar Firmware do Sistema", "sudo dmesg | grep -i firmware")
        ]:
            self.create_btn(self.t_drv, n, lambda cmd=c: self.run_action(cmd, "drv")).pack(pady=10)
        self.btn_drv = ctk.CTkButton(self.t_drv, text="Detalhes ⌄", width=120, height=32, corner_radius=16, fg_color="transparent", text_color=accent, font=("Inter", 12, "bold"), hover_color=side_color, command=lambda: self.toggle_console("drv"))
        self.log_drv = ctk.CTkTextbox(self.t_drv, height=200, fg_color=side_color, text_color="#10b981", font=("Consolas", 13), corner_radius=12)
            
        t_tm = self.tab_view.tab("🎨 Temas")
        for n, m in [("Default", "default"), ("Escuro", "dark"), ("Claro", "light"), ("Cinza", "grey")]: 
            self.create_btn(t_tm, n, lambda mode=m: self.set_theme(mode)).pack(pady=12)

    def toggle_ping(self):
        if not self.consoles["ping"]:
            self.ping_frame.pack(pady=10, before=self.dns_container)
            self.consoles["ping"] = True
            threading.Thread(target=self.ping_loop, daemon=True).start()
        else:
            self.ping_frame.pack_forget()
            self.consoles["ping"] = False

    def ping_loop(self):
        while self.consoles["ping"]:
            try:
                p = subprocess.run(["ping", "-c", "1", "-W", "1", "8.8.8.8"], capture_output=True, text=True)
                ping = p.stdout.split("time=")[1].split(" ")[0] if "time=" in p.stdout else "Erro"
                ip = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.split(" ")[0].strip()
                self.after(0, lambda: self.net_status.configure(text=f"Ping: {ping} ms | IP: {ip}"))
            except: pass
            time.sleep(2)

    def toggle_console(self, target):
        lookup = {"ot": (self.log_ot, self.btn_ot), "drv": (self.log_drv, self.btn_drv), "net": (self.log_net, self.btn_net)}
        log, btn = lookup[target]
        if not self.consoles[target]:
            log.pack(fill="x", padx=40, pady=10); btn.configure(text="Detalhes ⌃"); self.consoles[target] = True
        else:
            log.pack_forget(); btn.pack_forget(); self.consoles[target] = False

    def run_action(self, cmd, target):
        lookup = {"ot": (self.log_ot, self.btn_ot), "drv": (self.log_drv, self.btn_drv), "net": (self.log_net, self.btn_net)}
        log, btn = lookup[target]
        log.delete("0.0", "end"); btn.pack_forget(); self.consoles[target] = False
        threading.Thread(target=self.execute, args=(cmd, log, btn), daemon=True).start()

    def execute(self, cmd, log, btn):
        p = subprocess.Popen(f"pkexec bash -c '{cmd}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        o, e = p.communicate()
        self.after(0, lambda: btn.pack(side="top", anchor="e", padx=40, pady=5))
        self.after(0, lambda: log.insert("end", o + (e or "") + "\n-- CONCLUÍDO --"))

    def set_theme(self, mode_key, save=True):
        if save:
            self.config["theme"] = mode_key
            with open(CONFIG_FILE, "w") as f: json.dump(self.config, f)
        m_name, b_color, s_color, acc = themes.get(mode_key, themes["default"])
        ctk.set_appearance_mode(m_name); self.configure(fg_color=b_color); self.sidebar.configure(fg_color=s_color)
        self.tab_view.configure(fg_color=b_color)
        for l in [self.log_ot, self.log_drv, self.log_net]: l.configure(fg_color=s_color)
        for b in [self.btn_ot, self.btn_drv, self.btn_net]: b.configure(text_color=acc, hover_color=s_color)
        self.ping_frame.configure(fg_color=s_color)

    def update_sys_info(self):
        for w in self.systab.winfo_children(): w.destroy()
        cpu_p, mem = psutil.cpu_percent(), psutil.virtual_memory()
        cpu_m = os.popen("grep 'model name' /proc/cpuinfo | head -1").read().split(':')[-1].strip()
        gpu = os.popen("lspci | grep -E 'VGA|3D'").read().strip().split(':')[-1]
        for l, v in [("💻 MÁQUINA:", "Asus S46CA"), ("💿 S.O:", f"{platform.system()}"), ("🧠 CPU:", f"{cpu_m} ({cpu_p}%)"), ("📟 RAM:", f"{mem.used/(1024**3):.1f}/{mem.total/(1024**3):.1f} GB"), ("🎨 GPU:", gpu or "N/A")]:
            f = ctk.CTkFrame(self.systab, fg_color="transparent"); f.pack(fill="x", padx=40, pady=8)
            ctk.CTkLabel(f, text=l, font=("Inter", 16, "bold"), text_color="#a855f7", width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=v, font=("Consolas", 14)).pack(side="left")
        self.after(3000, self.update_sys_info)

if __name__ == "__main__":
    app = SpeedScan(); app.mainloop()
