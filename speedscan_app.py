import customtkinter as ctk
import os, platform, psutil, subprocess, threading, json

CONFIG_FILE = os.path.expanduser("~/.speedscan_conf")
ICON_PATH = os.path.expanduser("~/speedscan/icon.png")

def get_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"theme": "default", "geometry": "1100x900"}

conf = get_config()
# Temas configurados: (Modo, Fundo Principal, Cor Barra/Detalhes, Cor Texto Accent)
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

        self.console_visible = False
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        
        # Barra Esquerda na cor clara do tema
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=side_color)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="⚡ SpeedScan", font=("Orbitron", 28, "bold"), text_color="#a855f7").pack(pady=40, padx=20)
        
        self.tab_view = ctk.CTkTabview(self, corner_radius=15, segmented_button_selected_color="#a855f7", fg_color=bg)
        self.tab_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        for n in ["🏠 Início", "💻 Sistema", "🚀 Otimização", "🎮 Gamer", "🌐 DNS", "🎨 Temas"]: self.tab_view.add(n)
        
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
        ctk.CTkLabel(self.tab_view.tab("🏠 Início"), text="⚡ SpeedScan", font=("Orbitron", 54, "bold"), text_color="#a855f7").pack(pady=200)
        self.systab = self.tab_view.tab("💻 Sistema"); self.update_sys_info()
        
        self.t_ot = self.tab_view.tab("🚀 Otimização")
        for n, c in [("Limpeza Profunda", "sudo eopkg dc"), ("Otimizar RAM/Swap", "sudo swapoff -a && sudo swapon -a"), ("Fstrim (SSD)", "sudo fstrim -av")]: 
            self.create_btn(self.t_ot, n, lambda cmd=c: self.run_action(cmd)).pack(pady=10)
        
        # Botão Detalhes Cápsula
        self.toggle_btn = ctk.CTkButton(self.t_ot, text="Detalhes ⌄", width=120, height=32, corner_radius=16, fg_color="transparent", text_color=accent, font=("Inter", 12, "bold"), hover_color=side_color, command=self.toggle_console)
        
        # Janela de Detalhes na cor da Barra Esquerda (side_color)
        self.log_box = ctk.CTkTextbox(self.t_ot, height=250, fg_color=side_color, text_color="#10b981" if mode == "dark" else "#000000", font=("Consolas", 13), corner_radius=12)

        t_gm = self.tab_view.tab("🎮 Gamer")
        self.scroll_gm = ctk.CTkScrollableFrame(t_gm, fg_color="transparent", scrollbar_button_color="#a855f7")
        self.scroll_gm.pack(fill="both", expand=True); self.scroll_gm.columnconfigure(0, weight=1)
        apps = [("Steam", "steam"), ("Proton GE", "proton-ge-custom"), ("Heroic", "heroic-games-launcher-bin"), ("Lutris", "lutris"), ("Wine", "wine"), ("Bottles", "bottles"), ("RetroArch", "retroarch"), ("Dolphin", "dolphin-emu"), ("RPCS3", "rpcs3"), ("PCSX2", "pcsx2"), ("Snes9x", "snes9x")]
        for i, (n, p) in enumerate(apps):
            self.create_btn(self.scroll_gm, f"Instalar {n}", lambda pkg=p: self.run_action(f"sudo eopkg it {pkg} -y")).grid(row=i, column=0, pady=5)
            
        t_dns = self.tab_view.tab("🌐 DNS")
        for n, c in [("Cloudflare (1.1.1.1)", "nmcli dev mod eth0 ipv4.dns '1.1.1.1'"), ("Google (8.8.8.8)", "nmcli dev mod eth0 ipv4.dns '8.8.8.8'"), ("DNS Automático", "nmcli dev mod eth0 ipv4.dns ''")]: 
            self.create_btn(t_dns, n, lambda cmd=c: self.run_action(cmd)).pack(pady=10)
            
        t_tm = self.tab_view.tab("🎨 Temas")
        for n, m in [("Default", "default"), ("Escuro", "dark"), ("Claro", "light"), ("Cinza", "grey")]: 
            self.create_btn(t_tm, n, lambda mode=m: self.set_theme(mode)).pack(pady=12)

    def set_theme(self, mode_key, save=True):
        if save:
            self.config["theme"] = mode_key
            with open(CONFIG_FILE, "w") as f: json.dump(self.config, f)
        
        m_name, b_color, s_color, acc = themes.get(mode_key, themes["default"])
        ctk.set_appearance_mode(m_name)
        self.configure(fg_color=b_color)
        self.sidebar.configure(fg_color=s_color)
        self.tab_view.configure(fg_color=b_color)
        self.log_box.configure(fg_color=s_color, text_color="#10b981" if m_name == "dark" else "#000000")
        self.toggle_btn.configure(text_color=acc, hover_color=s_color)
        for tab in ["🏠 Início", "💻 Sistema", "🚀 Otimização", "🎮 Gamer", "🌐 DNS", "🎨 Temas"]: 
            self.tab_view.tab(tab).configure(fg_color=b_color)

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

    def toggle_console(self):
        if not self.console_visible:
            self.log_box.pack(fill="x", padx=40, pady=10)
            self.toggle_btn.configure(text="Detalhes ⌃")
            self.console_visible = True
        else:
            self.log_box.pack_forget()
            self.toggle_btn.pack_forget()
            self.console_visible = False

    def run_action(self, cmd):
        self.log_box.delete("0.0", "end"); self.toggle_btn.pack_forget(); self.console_visible = False
        threading.Thread(target=self.execute, args=(cmd,), daemon=True).start()

    def execute(self, cmd):
        p = subprocess.Popen(f"pkexec bash -c '{cmd}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        o, e = p.communicate()
        self.after(0, lambda: self.toggle_btn.pack(side="top", anchor="e", padx=40, pady=5))
        self.after(0, lambda: self.log_box.insert("end", o + (e or "") + "\n-- FIM --"))

if __name__ == "__main__":
    app = SpeedScan(); app.mainloop()
