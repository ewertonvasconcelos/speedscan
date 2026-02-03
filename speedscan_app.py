import customtkinter as ctk
import os, platform, psutil, subprocess, threading, json, time
from PIL import Image

CONFIG_FILE = os.path.expanduser("~/.speedscan_conf")
ICON_PATH = os.path.expanduser("~/speedscan/icon.png")

def get_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"theme": "default", "geometry": "1200x950"}

conf = get_config()
themes = {
    "default": {"mode": "dark", "bg": "#1e293b", "side": "#0f172a", "acc": "#a855f7", "text": "#ffffff"},
    "grey":    {"mode": "light", "bg": "#f3f4f6", "side": "#374151", "acc": "#4b5563", "text": "#111827"},
    "dark":    {"mode": "dark", "bg": "#080808", "side": "#000000", "acc": "#10b981", "text": "#ffffff"},
    "light":   {"mode": "light", "bg": "#ffffff", "side": "#f8fafc", "acc": "#2563eb", "text": "#0f172a"}
}

class SpeedScan(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = conf
        self.update_theme_vars()
        self.title("SpeedScan")
        self.geometry(self.config.get("geometry", "1200x950"))
        self.configure(fg_color=self.bg_color)
        
        self.turbo_active = False
        self.consoles_visible = {"ot": False, "gm": False, "net": False, "drv": False, "ping": False}

        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=self.side_bg)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        try:
            logo_img = ctk.CTkImage(Image.open(ICON_PATH), size=(220, 220))
            ctk.CTkLabel(self.sidebar, image=logo_img, text="").pack(pady=(40, 10), padx=20)
        except:
            ctk.CTkLabel(self.sidebar, text="⚡", font=("Orbitron", 80)).pack(pady=40)
        
        self.title_label = ctk.CTkLabel(self.sidebar, text="SpeedScan", font=("Orbitron", 32, "bold"), text_color=self.accent)
        self.title_label.pack(pady=10)

        self.tab_view = ctk.CTkTabview(self, corner_radius=15, fg_color=self.bg_color, segmented_button_selected_color=self.accent)
        self.tab_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        for n in ["🏠 Início", "💻 Sistema", "🚀 Otimização", "🎮 Gamer", "🌐 Rede", "🛠 Drivers", "🎨 Temas"]:
            self.tab_view.add(n)
        
        self.setup_tabs()
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def update_theme_vars(self):
        t = themes.get(self.config.get("theme", "default"))
        ctk.set_appearance_mode(t["mode"])
        self.bg_color = t["bg"]; self.side_bg = t["side"]; self.accent = t["acc"]; self.text_color = t["text"]

    def _on_mousewheel(self, event):
        tab = self.tab_view.get()
        targets = {"💻 Sistema": self.scroll_sys, "🎮 Gamer": self.scroll_gm, "🛠 Drivers": self.scroll_drv}
        if tab in targets: targets[tab]._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_btn(self, m, t, c, color=None):
        return ctk.CTkButton(m, text=t, command=c, fg_color=color if color else self.accent, 
                             hover_color="#9333ea", text_color="#ffffff", width=420, height=45, font=("Inter", 14, "bold"))

    def toggle_console(self, target):
        lookup = {"ot": (self.log_ot, self.btn_ot), "gm": (self.log_gm, self.btn_gm), 
                  "net": (self.log_net, self.btn_net), "drv": (self.log_drv, self.btn_drv)}
        log, btn = lookup[target]
        if not self.consoles_visible[target]:
            log.pack(fill="x", padx=40, pady=10)
            btn.configure(text="Detalhes ⌃"); self.consoles_visible[target] = True
        else:
            log.pack_forget()
            btn.configure(text="Detalhes ⌄"); self.consoles_visible[target] = False

    def setup_tabs(self):
        self.scroll_sys = ctk.CTkScrollableFrame(self.tab_view.tab("💻 Sistema"), fg_color="transparent")
        self.scroll_sys.pack(fill="both", expand=True); self.update_sys_info()

        self.t_ot = self.tab_view.tab("🚀 Otimização")
        for n, c in [("Limpeza de Cache Profunda", "sudo eopkg dc"), ("Otimizar RAM/Swap", "sudo swapoff -a && sudo swapon -a"), ("Verificar Erros", "sudo eopkg check")]:
            self.create_btn(self.t_ot, n, lambda cmd=c: self.run_action(cmd, "ot")).pack(pady=10)
        self.btn_ot = ctk.CTkButton(self.t_ot, text="Detalhes ⌄", fg_color="transparent", text_color=self.accent, command=lambda: self.toggle_console("ot"))
        self.log_ot = ctk.CTkTextbox(self.t_ot, height=200, fg_color=self.side_bg, text_color="#10b981")

        self.t_gm = self.tab_view.tab("🎮 Gamer")
        self.btn_turbo = self.create_btn(self.t_gm, "🔥 ATIVAR MODO TURBO GAMER", self.toggle_turbo, color="#e11d48")
        self.btn_turbo.pack(pady=15)
        self.scroll_gm = ctk.CTkScrollableFrame(self.t_gm, fg_color="transparent", height=350)
        self.scroll_gm.pack(fill="both", expand=True)
        apps = [("Steam", "steam"), ("Lutris", "lutris"), ("Heroic Launcher", "heroic-games-launcher-bin"), ("Bottles", "bottles"), ("Wine", "wine"), ("MangoHud", "mangohud"), ("Goverlay", "goverlay")]
        for n, p in apps:
            self.create_btn(self.scroll_gm, f"Instalar {n}", lambda pkg=p: self.run_action(f"sudo eopkg it {pkg} -y", "gm")).pack(pady=5)
        self.btn_gm = ctk.CTkButton(self.t_gm, text="Detalhes ⌄", fg_color="transparent", text_color=self.accent, command=lambda: self.toggle_console("gm"))
        self.log_gm = ctk.CTkTextbox(self.t_gm, height=200, fg_color=self.side_bg, text_color="#10b981")

        self.t_net = self.tab_view.tab("🌐 Rede")
        self.create_btn(self.t_net, "Testar Latência (Ping)", self.toggle_ping_ui).pack(pady=10)
        self.ping_frame = ctk.CTkFrame(self.t_net, fg_color=self.side_bg, corner_radius=12)
        self.ping_label = ctk.CTkLabel(self.ping_frame, text="Ping: -- ms", font=("Consolas", 16, "bold"), text_color="#10b981")
        self.ping_label.pack(pady=10, padx=20)
        self.dns_box = ctk.CTkFrame(self.t_net, fg_color="transparent")
        self.dns_box.pack(fill="x")
        for n, c in [("Cloudflare DNS", "nmcli dev mod eth0 ipv4.dns '1.1.1.1'"), ("Google DNS", "nmcli dev mod eth0 ipv4.dns '8.8.8.8'"), ("DNS Automático", "nmcli dev mod eth0 ipv4.dns ''")]:
            self.create_btn(self.dns_box, n, lambda cmd=c: self.run_action(cmd, "net")).pack(pady=5)
        self.btn_net = ctk.CTkButton(self.t_net, text="Detalhes ⌄", fg_color="transparent", text_color=self.accent, command=lambda: self.toggle_console("net"))
        self.log_net = ctk.CTkTextbox(self.t_net, height=150, fg_color=self.side_bg, text_color="#10b981")

        self.t_drv = self.tab_view.tab("🛠 Drivers")
        self.scroll_drv = ctk.CTkScrollableFrame(self.t_drv, fg_color="transparent", height=450)
        self.scroll_drv.pack(fill="both", expand=True)
        for n, c in [("PCI (Vídeo/Rede)", "lspci -nnk"), ("USB Conectados", "lsusb"), ("Módulos Kernel", "lsmod"), ("CPU Detalhada", "lscpu"), ("Firmware Erros", "sudo dmesg | grep -i firmware")]:
            self.create_btn(self.scroll_drv, n, lambda cmd=c: self.run_action(cmd, "drv")).pack(pady=5)
        self.btn_drv = ctk.CTkButton(self.t_drv, text="Detalhes ⌄", fg_color="transparent", text_color=self.accent, command=lambda: self.toggle_console("drv"))
        self.log_drv = ctk.CTkTextbox(self.t_drv, height=200, fg_color=self.side_bg, text_color="#10b981")

        self.t_tm = self.tab_view.tab("🎨 Temas")
        for name, key in [("Padrão", "default"), ("Cinza", "grey"), ("Escuro", "dark"), ("Claro", "light")]:
            self.create_btn(self.t_tm, name, lambda k=key: self.set_theme(k)).pack(pady=10)

    def run_action(self, cmd, target):
        lookup = {"ot": (self.log_ot, self.btn_ot), "gm": (self.log_gm, self.btn_gm), 
                  "net": (self.log_net, self.btn_net), "drv": (self.log_drv, self.btn_drv)}
        log, btn = lookup[target]
        log.delete("0.0", "end")
        threading.Thread(target=self.execute, args=(cmd, log, btn, target), daemon=True).start()

    def execute(self, cmd, log, btn, target):
        p = subprocess.Popen(f"pkexec bash -c '{cmd}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        o, e = p.communicate()
        if p.returncode == 0:
            self.after(0, lambda: self.finish_action(btn, log, o + (e or "") + "\n-- OK --", target))

    def finish_action(self, btn, log, content, target):
        btn.pack(pady=5, anchor="e", padx=40)
        log.insert("end", content)
        if not self.consoles_visible[target]: self.toggle_console(target)

    def toggle_turbo(self):
        self.turbo_active = not self.turbo_active
        color = "#475569" if self.turbo_active else "#e11d48"
        self.btn_turbo.configure(text="🛡️ DESATIVAR TURBO" if self.turbo_active else "🔥 ATIVAR MODO TURBO", fg_color=color)
        cmd = "sudo cpupower frequency-set -g performance" if self.turbo_active else "sudo cpupower frequency-set -g powersave"
        self.run_action(cmd, "gm")

    def toggle_ping_ui(self):
        if not self.consoles_visible["ping"]:
            self.ping_frame.pack(pady=10, before=self.dns_box)
            self.consoles_visible["ping"] = True
            threading.Thread(target=self.ping_loop, daemon=True).start()
        else:
            self.ping_frame.pack_forget(); self.consoles_visible["ping"] = False

    def ping_loop(self):
        while self.consoles_visible["ping"]:
            try:
                p = subprocess.run(["ping", "-c", "1", "-W", "1", "8.8.8.8"], capture_output=True, text=True)
                res = p.stdout.split("time=")[1].split(" ")[0] if "time=" in p.stdout else "Erro"
                self.after(0, lambda r=res: self.ping_label.configure(text=f"Ping: {r} ms"))
            except: pass
            time.sleep(2)

    def update_sys_info(self):
        for w in self.scroll_sys.winfo_children(): w.destroy()
        gpu_raw = os.popen("lspci -k | grep -A 3 -i 'vga\\|3d'").read()
        gpu_brand = "Intel" if "Intel" in gpu_raw else ("Nvidia" if "Nvidia" in gpu_raw else "AMD")
        gpu_model = os.popen("lspci | grep -i 'vga\\|3d' | cut -d: -f3").read().strip()
        gpu_driver = os.popen("glxinfo | grep 'OpenGL core profile version string'").read().split(':')[-1].strip() or "Mesa Driver"
        disk_lines = os.popen("lsblk -d -o NAME,MODEL,SIZE,ROTA,TRAN").read().strip().split('\n')[1:]
        disk_summary = ""
        for line in disk_lines:
            p = line.split()
            if len(p) >= 4:
                name, size, rota = p[0], p[-2], p[-1]
                model = " ".join(p[1:-2])
                bus = p[-3] if len(p) > 4 else ("NVMe" if "nvme" in name else "SATA")
                tech = "HDD" if rota == "1" else "SSD"
                disk_summary += f"• {model} [{bus} {tech}] - {size}\n"
        
        info = [
            ("💻 DISPOSITIVO", platform.node()),
            ("💿 DISTRO", os.popen("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2").read().strip().replace('"', '')),
            ("🐧 KERNEL", platform.release()),
            ("🧠 CPU", os.popen("lscpu | grep 'Model name' | cut -d: -f2").read().strip()),
            ("🎮 GPU MARCA", f"{gpu_brand}"),
            ("🎥 GPU MODELO", gpu_model),
            ("🔧 GPU DRIVER", gpu_driver),
            ("📟 RAM", f"{psutil.virtual_memory().total/(1024**3):.2f} GB"),
            ("💽 DISCOS", disk_summary.strip()),
            ("🐍 PYTHON", platform.python_version()),
            ("🎨 CUSTOMTKINTER", ctk.__version__),
            ("🔋 BATERIA", f"{psutil.sensors_battery().percent}%" if psutil.sensors_battery() else "AC Power")
        ]
        for l, v in info:
            f = ctk.CTkFrame(self.scroll_sys, fg_color="transparent")
            f.pack(fill="x", padx=40, pady=10)
            ctk.CTkLabel(f, text=l, font=("Inter", 15, "bold"), text_color=self.accent, width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=v, font=("Consolas", 13), text_color=self.text_color, justify="left").pack(side="left")

    def set_theme(self, key):
        self.config["theme"] = key
        with open(CONFIG_FILE, "w") as f: json.dump(self.config, f)
        self.update_theme_vars(); self.configure(fg_color=self.bg_color)
        self.sidebar.configure(fg_color=self.side_bg); self.title_label.configure(text_color=self.accent)
        self.tab_view.configure(fg_color=self.bg_color, segmented_button_selected_color=self.accent)
        self.update_sys_info()

if __name__ == "__main__":
    app = SpeedScan(); app.mainloop()
