#!/usr/bin/env python3
import logging
# SpeedScan - Versão com rolagem corrigida (sobe e desce)
# Uso: python3 core/speedscan_app.py

import customtkinter as ctk
import os
import platform
import psutil
import subprocess
import threading
import json
import time
import sys
import re
from PIL import Image, ImageDraw
from datetime import datetime

# CONFIGURAÇÕES
from core import config
os.makedirs(config.LOG_DIR, exist_ok=True)

def get_config():
    if os.path.exists(config.CONFIG_FILE):
        try:
            with open(config.CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "theme": "default",
        "username": "ewerton",
        "language": "pt_BR",
        "ui_scale": "auto",
        "open_file_in_tab": False,
        "schedule": {
            "enabled": False,
            "frequency": "weekly",
            "hour": "03:00",
            "day_of_week": "monday",
            "day_of_month": 1,
            "interval_days": 7,
            "tasks": ["cache", "swap", "check"],
            "elevated": False
        }
    }

conf = get_config()

themes = {
    "default": {"mode": "dark", "bg": "#1e293b", "side": "#0f172a", "acc": "#a855f7", "text": "#ffffff"},
    "grey":    {"mode": "light", "bg": "#d1d5db", "side": "#374151", "acc": "#4b5563", "text": "#111827"},
    "dark":    {"mode": "dark", "bg": "#080808", "side": "#000000", "acc": "#10b981", "text": "#ffffff"},
    "light":   {"mode": "light", "bg": "#ffffff", "side": "#f8fafc", "acc": "#2563eb", "text": "#0f172a"}
}

languages = {
    "pt_BR": "Português Brasileiro",
    "en_US": "English (US)",
    "es_ES": "Español"
}

scales = {
    "auto": "Automático",
    "100": "100%",
    "125": "125%",
    "150": "150%"
}

    "DeepSeek",
    "OpenAI GPT-4",
    "Google Gemini",
    "Claude (Anthropic)",
    "Llama 3 (Meta)",
    "Mistral AI",
    "Cohere",
    "Local (Ollama)",
    "Configurar IA Local"
]

# CLASSE PRINCIPAL
class SpeedScan(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.SO = platform.system()
        self.config = conf
        self.update_theme_vars()
        self.title("SpeedScan")
        self.geometry("1200x950")
        self.minsize(1000, 700)
        self.configure(fg_color=self.bg_color)

        self.apply_ui_scale()

        self.turbo_active = False
        self.consoles_visible = {}
        self.ping_active = False
        self.current_module = "sistema"
        self.sidebar_buttons = {}
        self.detail_buttons = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.side_bg)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.create_sidebar()
        self.create_frames()
        self.show_frame("sistema")
        
        # Binding corrigido para suportar Linux (Button-4/Button-5) e outros sistemas (MouseWheel)
        if self.SO == "Linux":
            self.bind_all("<Button-4>", self._on_mousewheel)
            self.bind_all("<Button-5>", self._on_mousewheel)
        else:
            self.bind_all("<MouseWheel>", self._on_mousewheel)
            
        threading.Thread(target=self.hardware_monitor, daemon=True).start()

    # ---------- Funções de tema e imagem ----------
    def round_image(self, path, size=(96, 96), radius=20):
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize(size, Image.Resampling.LANCZOS)
            mask = Image.new("L", size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0) + size, radius=radius, fill=255)
            result = Image.new("RGBA", size)
            result.paste(img, (0, 0), mask)
            return ctk.CTkImage(result, size=size)
        except Exception as e:
            logging.error(f"Erro ao arredondar imagem: {e}")
            return None

    def update_theme_vars(self):
        t = themes.get(self.config["theme"], themes["default"])
        ctk.set_appearance_mode(t["mode"])
        self.bg_color = t["bg"]
        self.side_bg = t["side"]
        self.acc_color = t["acc"]
        self.text_color = t["text"]
        self.light_bg = self._lighten_color(self.bg_color, 0.2)

    def _lighten_color(self, hex_color, factor=0.2):
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def apply_ui_scale(self):
        scale = self.config.get("ui_scale", "auto")
        if scale == "auto":
            ctk.set_widget_scaling(1.0)
        else:
            ctk.set_widget_scaling(float(scale) / 100)

    # ---------- Sidebar ----------
    def create_sidebar(self):
        top_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        top_frame.pack(side="top", fill="x", pady=(30, 10))

        icon_image = None
        if os.path.exists(config.ICON_PATH):
            icon_image = self.round_image(config.ICON_PATH, size=(96, 96), radius=20)

        if icon_image:
            btn_speed = ctk.CTkButton(
                top_frame,
                image=icon_image,
                text="",
                width=96,
                height=96,
                corner_radius=20,
                fg_color="transparent",
                hover_color=self.acc_color,
                command=lambda: self.show_frame("sistema"),
                cursor="hand2"
            )
            btn_speed.pack()
        else:
            btn_speed = ctk.CTkButton(
                top_frame,
                text="⚡",
                width=96,
                height=96,
                corner_radius=20,
                fg_color="transparent",
                hover_color=self.acc_color,
                font=("Inter", 48),
                command=lambda: self.show_frame("sistema"),
                cursor="hand2"
            )
            btn_speed.pack()

        center_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        center_frame.pack(side="top", fill="both", expand=True, pady=20)

        ctk.CTkLabel(center_frame, text="").pack(expand=True)

        self.sidebar_buttons["otimizacao"] = self.add_sidebar_btn(center_frame, "🚀", "Otimização", "otimizacao")
        self.sidebar_buttons["rede"] = self.add_sidebar_btn(center_frame, "🌐", "Rede", "rede")
        self.sidebar_buttons["drivers"] = self.add_sidebar_btn(center_frame, "🛠️", "Drivers", "drivers")
        self.sidebar_buttons["agente"] = self.add_sidebar_btn(center_frame, "🤖", "Agente IA", "agente")

        ctk.CTkLabel(center_frame, text="").pack(expand=True)

        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=20)

        self.sidebar_buttons["config"] = self.add_sidebar_btn(bottom_frame, "⚙️", "Configurações", "config")
        self.sidebar_buttons["sobre"] = self.add_sidebar_btn(bottom_frame, "ℹ️", "Sobre", "sobre")

    def add_sidebar_btn(self, parent, icon, text, target):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=5, fill="x", padx=10)
        btn = ctk.CTkButton(
            frame,
            text=f"{icon}  {text}",
            anchor="w",
            height=40,
            fg_color="transparent",
            hover_color=self.acc_color,
            font=("Inter", 13),
            corner_radius=10,
            command=lambda: self.show_frame(target),
            cursor="hand2"
        )
        btn.pack(fill="x")
        return btn

    def show_frame(self, target):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[target].pack(fill="both", expand=True)
        self.current_module = target

        for key, btn in self.sidebar_buttons.items():
            if key == target:
                btn.configure(fg_color=self.acc_color)
            else:
                btn.configure(fg_color="transparent")

        if target == "sistema":
            self.update_sys_info()

    # ---------- Criação dos frames ----------
    def create_frames(self):
        self.frames["sistema"] = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.create_sistema_frame(self.frames["sistema"])

        self.frames["otimizacao"] = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.create_otimizacao_frame(self.frames["otimizacao"])

        self.frames["rede"] = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.create_rede_frame(self.frames["rede"])

        self.frames["drivers"] = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.create_drivers_frame(self.frames["drivers"])

        self.frames["agente"] = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.create_agente_frame(self.frames["agente"])

        self.frames["config"] = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        self.create_config_frame(self.frames["config"])

        self.frames["sobre"] = ctk.CTkFrame(self.container, fg_color="transparent")
        self.create_sobre_frame(self.frames["sobre"])

    # ---------- Sistema (cards de informações) ----------
    def create_sistema_frame(self, parent):
        ctk.CTkLabel(parent, text="Informações do Sistema", font=("Inter", 28, "bold"), text_color=self.acc_color).pack(anchor="w", pady=(0, 30))

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        info_fields = [
            ("💻 Hostname", "hostname", self._get_hostname),
            ("💿 Distribuição", "distro", self._get_distro),
            ("🐧 Kernel", "kernel", self._get_kernel),
            ("🖥️ CPU", "cpu", self._get_cpu),
            ("📟 RAM", "ram", self._get_ram),
            ("🎮 GPU", "gpu", self._get_gpu),
            ("💽 Discos", "disks", self._get_disks_detailed),
            ("⏱️ Uptime", "uptime", self._get_uptime),
            ("🔋 Bateria", "battery", self._get_battery)
        ]

        self.sys_labels = {}

        for i, (label, key, func) in enumerate(info_fields):
            row, col = divmod(i, 3)
            card = ctk.CTkFrame(grid, fg_color=self.bg_color, corner_radius=10, border_width=1, border_color=self.acc_color)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)
            card.configure(height=150)

            ctk.CTkLabel(card, text=label, font=("Inter", 14, "bold"), text_color=self.acc_color).pack(pady=(10, 5))

            value_label = ctk.CTkLabel(
                card,
                text="...",
                font=("Consolas", 11),
                text_color=self.text_color,
                wraplength=180,
                justify="left"
            )
            value_label.pack(expand=True, fill="both", padx=5, pady=(0, 10))
            self.sys_labels[key] = value_label

        self.update_sys_info()

    def update_sys_info(self):
        try:
            self.sys_labels["hostname"].configure(text=self._get_hostname())
            self.sys_labels["distro"].configure(text=self._get_distro())
            self.sys_labels["kernel"].configure(text=self._get_kernel())
            self.sys_labels["cpu"].configure(text=self._get_cpu())
            self.sys_labels["ram"].configure(text=self._get_ram())
            self.sys_labels["gpu"].configure(text=self._get_gpu())
            self.sys_labels["disks"].configure(text=self._get_disks_detailed())
            self.sys_labels["uptime"].configure(text=self._get_uptime())
            self.sys_labels["battery"].configure(text=self._get_battery())
        except Exception as e:
            logging.error(f"Erro ao atualizar informações: {e}")

    def _get_hostname(self):
        return platform.node()

    def _get_distro(self):
        if self.SO == "Linux":
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            return line.split("=")[1].strip().strip('"')
            except:
                pass
        return platform.system() + " " + platform.release()

    def _get_kernel(self):
        return platform.release()

    def _get_cpu(self):
        try:
            if self.SO == "Linux":
                out = subprocess.check_output("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2", shell=True, text=True).strip()
                if out:
                    return out
            elif self.SO == "Windows":
                out = subprocess.check_output("wmic cpu get name", shell=True, text=True).strip().split('\n')[1]
                if out:
                    return out
            elif self.SO == "Darwin":
                out = subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True, text=True).strip()
                if out:
                    return out
        except:
            pass
        return f"{psutil.cpu_count()} núcleos ({psutil.cpu_percent()}%)"

    def _get_ram(self):
        mem = psutil.virtual_memory()
        return f"{mem.used // 1048576} MB / {mem.total // 1048576} MB ({mem.percent}%)"

    def _get_gpu(self):
        try:
            if self.SO == "Linux":
                out = subprocess.check_output("lspci | grep -i 'vga\\|3d' | cut -d: -f3-", shell=True, text=True).strip()
                if out:
                    return out
            elif self.SO == "Windows":
                out = subprocess.check_output("wmic path win32_VideoController get name", shell=True, text=True).strip().split('\n')[1]
                if out:
                    return out
            elif self.SO == "Darwin":
                out = subprocess.check_output("system_profiler SPDisplaysDataType | grep Chipset", shell=True, text=True).strip()
                if out:
                    return out
        except:
            pass
        return "Não detectado"

    def _get_disks_detailed(self):
        try:
            disks_info = []
            for part in psutil.disk_partitions():
                if part.fstype and not part.mountpoint.startswith("/snap/"):
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        total_gb = usage.total / (1024**3)
                        used_gb = usage.used / (1024**3)
                        free_gb = usage.free / (1024**3)
                        disks_info.append(f"{part.device} ({total_gb:.1f}G, usado {used_gb:.1f}G, livre {free_gb:.1f}G)")
                    except:
                        continue
            if disks_info:
                return "\n".join(disks_info[:3])
            else:
                return "Nenhum disco detectado"
        except:
            return "N/A"

    def _get_uptime(self):
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            return str(datetime.timedelta(seconds=int(uptime_seconds)))
        except:
            return "N/A"

    def _get_battery(self):
        try:
            battery = psutil.sensors_battery()
            if battery:
                return f"{battery.percent:.1f}%"
            else:
                return "AC Power"
        except:
            return "AC Power"

    # ---------- Otimização ----------
    def create_otimizacao_frame(self, parent):
        ctk.CTkLabel(parent, text="Otimização", font=("Inter", 28, "bold"), text_color=self.acc_color).pack(anchor="w", pady=(0, 20))

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="both", expand=True, pady=10)
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        cards = [
            ("🧹 Limpeza de Cache", "cache", "ot", False),
            ("🔄 Reset de Swap", "swap", "ot", False),
            ("✅ Verificar Erros", "check", "ot", False),
            ("🔥 Modo Turbo", "turbo", "ot", False),
            ("Steam", "steam", "gm", True),
            ("Lutris", "lutris", "gm", True),
            ("Heroic Launcher", "heroic", "gm", True),
            ("Bottles", "bottles", "gm", True),
            ("Wine", "wine", "gm", True),
            ("MangoHud", "mangohud", "gm", True),
            ("Goverlay", "goverlay", "gm", True),
            ("🎮 Emulador Dolphin", "dolphin", "ot", True),
        ]

        for idx, (title, cmd, tag, is_install) in enumerate(cards):
            row, col = divmod(idx, 3)
            card = ctk.CTkFrame(grid, fg_color=self.bg_color, corner_radius=10, border_width=1, border_color=self.acc_color)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)
            card.configure(height=150)

            ctk.CTkLabel(card, text=title, font=("Inter", 14, "bold"), text_color=self.acc_color).pack(pady=(10, 5))
            btn_text = "Instalar" if is_install else "Executar"
            btn = ctk.CTkButton(
                card,
                text=btn_text,
                fg_color=self.acc_color,
                command=lambda c=cmd, t=tag, ti=title: self.run_optimization_action(c, t, ti),
                cursor="hand2"
            )
            btn.pack(pady=5)

        self._add_console(parent, "ot")

    def run_optimization_action(self, cmd, tag, title):
        if cmd == "turbo":
            self.toggle_turbo()
        elif cmd == "dolphin":
            self.install_dolphin()
        elif cmd in ["steam", "lutris", "heroic", "bottles", "wine", "mangohud", "goverlay"]:
            self.install_package(cmd, tag)
        else:
            self.run_system_action(cmd, tag)

    def install_package(self, pkg, tag):
        if self.SO == "Linux":
            if os.path.exists("/etc/eopkg/repositories"):  # Solus
                self.run_action(f"sudo eopkg it {pkg} -y", tag)
            elif os.path.exists("/etc/debian_version"):  # Debian/Ubuntu
                self.run_action(f"sudo apt install -y {pkg}", tag)
            elif os.path.exists("/etc/redhat-release"):  # Fedora/RHEL
                self.run_action(f"sudo dnf install -y {pkg}", tag)
            else:
                self.run_action(f"echo 'Instalação automática não suportada para {pkg}'", tag)
        elif self.SO == "Windows":
            self.run_action(f"winget install {pkg}", tag)
        elif self.SO == "Darwin":
            self.run_action(f"brew install {pkg}", tag)
        else:
            self.run_action(f"echo 'Sistema não suportado'", tag)

    def run_system_action(self, cmd, tag):
        if self.SO == "Linux":
            if cmd == "cache":
                self.run_action("sudo eopkg dc && sudo eopkg clean", tag)
            elif cmd == "swap":
                self.run_action("sudo swapoff -a && sudo swapon -a", tag)
            elif cmd == "check":
                self.run_action("sudo eopkg check", tag)
            else:
                self.run_action(f"echo 'Comando {cmd} não implementado'", tag)
        else:
            self.run_action(f"echo 'Ação {cmd} não disponível neste SO'", tag)

    def install_dolphin(self):
        distro = self._get_distro().lower()
        if self.SO == "Linux":
            if "ubuntu" in distro or "debian" in distro:
                install_cmd = "sudo apt install dolphin-emu -y"
            elif "fedora" in distro:
                install_cmd = "sudo dnf install dolphin-emu -y"
            elif "arch" in distro:
                install_cmd = "sudo pacman -S dolphin-emu --noconfirm"
            elif "opensuse" in distro:
                install_cmd = "sudo zypper install dolphin-emu -y"
            else:
                install_cmd = "echo 'Distro não suportada para instalação automática'"
        elif self.SO == "Windows":
            install_cmd = "winget install dolphin-emu"
        elif self.SO == "Darwin":
            install_cmd = "brew install dolphin-emu"
        else:
            install_cmd = "echo 'Sistema não suportado'"
        self.run_action(install_cmd, "ot")
        log = getattr(self, "log_ot")
        log.insert("end", "\n\nDOLPHIN INSTALADO COM SUCESSO!\n")
        log.insert("end", "Para configurar, execute 'dolphin-emu' no terminal.\n")

    # ---------- Rede ----------
    def create_rede_frame(self, parent):
        ctk.CTkLabel(parent, text="Rede", font=("Inter", 28, "bold"), text_color=self.acc_color).pack(anchor="w", pady=(0, 20))

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="both", expand=True, pady=10)
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        cards = [
            ("📡 Ping", "ping", "net", False),
            ("☁️ Cloudflare DNS", "1.1.1.1", "net", True),
            ("🔵 Google DNS", "8.8.8.8", "net", True),
            ("🛡️ AdGuard DNS", "94.140.14.14", "net", True),
            ("🔄 DNS Automático", "auto", "net", True),
            ("🌐 Testar Velocidade", "speedtest", "net", False),
            ("🔌 Diagnóstico Placa", "ethtool", "net", False),
            ("🔄 Renovar IP", "dhclient", "net", False),
            ("🧭 Portas Abertas", "ports", "net", False),
            ("📶 Traceroute", "traceroute", "net", False),
            ("📶 Informações Wi-Fi", "wifi", "net", False),
            ("🌍 Testar DNS", "testdns", "net", False),
        ]

        for idx, (title, cmd, tag, is_dns) in enumerate(cards):
            row, col = divmod(idx, 3)
            card = ctk.CTkFrame(grid, fg_color=self.bg_color, corner_radius=10, border_width=1, border_color=self.acc_color)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)
            card.configure(height=150)

            ctk.CTkLabel(card, text=title, font=("Inter", 14, "bold"), text_color=self.acc_color).pack(pady=(10, 5))
            if cmd == "ping":
                btn = ctk.CTkButton(
                    card,
                    text="Iniciar",
                    fg_color=self.acc_color,
                    command=self.toggle_ping,
                    cursor="hand2"
                )
                btn.pack(pady=5)
                self.ping_label = ctk.CTkLabel(card, text="-- ms", font=("Consolas", 14), text_color="#10b981")
                self.ping_label.pack()
            else:
                btn_text = "Aplicar" if is_dns else "Executar"
                btn = ctk.CTkButton(
                    card,
                    text=btn_text,
                    fg_color=self.acc_color,
                    command=lambda c=cmd, t=tag, d=is_dns: self.run_network_action(c, t, d),
                    cursor="hand2"
                )
                btn.pack(pady=5)

        self._add_console(parent, "net")

    def run_network_action(self, cmd, tag, is_dns):
        if cmd == "ping":
            self.toggle_ping()
        elif cmd == "traceroute":
            self.run_traceroute(tag)
        elif cmd == "speedtest":
            self.run_speedtest(tag)
        elif cmd == "wifi":
            self.run_wifi_info(tag)
        elif cmd == "testdns":
            self.run_testdns(tag)
        elif cmd == "ethtool":
            if self.SO == "Linux":
                iface = subprocess.getoutput("ip route | grep default | awk '{print $5}' | head -1")
                if iface:
                    self.run_action(f"ethtool {iface}", tag)
                else:
                    self.run_action("echo 'Interface não encontrada'", tag)
            else:
                self.run_action("echo 'Comando ethtool disponível apenas no Linux'", tag)
        elif cmd == "dhclient":
            if self.SO == "Linux":
                self.run_action("sudo dhclient -v -r && sudo dhclient -v", tag)
            else:
                self.run_action("echo 'Renovação de IP via DHCPClient não suportada neste SO'", tag)
        elif cmd == "ports":
            self.scan_ports_interactive()
        elif is_dns:
            self.apply_dns(cmd, tag)
        else:
            self.run_action(cmd, tag)

    def run_traceroute(self, tag):
        if self.SO == "Windows":
            cmd = "tracert 8.8.8.8"
        else:
            cmd = "traceroute 8.8.8.8"
        self.run_action(cmd, tag)

    def run_wifi_info(self, tag):
        log = getattr(self, f"log_{tag}")
        log.delete("1.0", "end")
        log.insert("end", "Obtendo informações da rede Wi-Fi...\n")
        if self.SO == "Linux":
            cmd = "nmcli -t -f GENERAL.STATE,IP4.ADDRESS,IP4.GATEWAY,WIFI.SSID,WIFI.SIGNAL,WIFI.CHANNEL dev show"
        elif self.SO == "Windows":
            cmd = "netsh wlan show interfaces"
        elif self.SO == "Darwin":
            cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I"
        else:
            cmd = "echo 'Comando não disponível'"
        self.run_action(cmd, tag)

    def run_testdns(self, tag):
        log = getattr(self, f"log_{tag}")
        log.delete("1.0", "end")
        log.insert("end", "Testando resolução DNS para google.com...\n")
        if self.SO == "Windows":
            cmd = "nslookup google.com"
        else:
            cmd = "dig google.com +short"
        self.run_action(cmd, tag)

    def run_speedtest(self, tag):
        log = getattr(self, f"log_{tag}")
        log.delete("1.0", "end")
        log.insert("end", "Iniciando teste de velocidade...\n")
        try:
            subprocess.run(["speedtest-cli", "--version"], capture_output=True, check=True)
            cmd = "speedtest-cli"
        except:
            cmd = "curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3 -"
        self.run_action(cmd, tag)

    def apply_dns(self, dns, tag):
        if self.SO == "Linux":
            iface = subprocess.getoutput("nmcli -t -f DEVICE,STATE dev | grep connected | cut -d: -f1 | head -n1")
            if iface:
                if dns == "auto":
                    cmd = f"nmcli dev mod {iface} ipv4.dns ''"
                else:
                    cmd = f"nmcli dev mod {iface} ipv4.dns '{dns}'"
                self.run_action(cmd, tag)
            else:
                self.run_action("echo 'Interface de rede não encontrada'", tag)
        elif self.SO == "Windows":
            iface = subprocess.getoutput("wmic nic where netenabled=true get NetConnectionID | findstr /v NetConnectionID").strip()
            if iface:
                if dns == "auto":
                    cmd = f'netsh interface ip set dns "{iface}" dhcp'
                else:
                    cmd = f'netsh interface ip set dns "{iface}" static {dns}'
                self.run_action(cmd, tag)
            else:
                self.run_action("echo 'Interface não encontrada'", tag)
        elif self.SO == "Darwin":
            service = subprocess.getoutput("networksetup -listallnetworkservices | grep -v 'An asterisk' | head -1")
            if service:
                if dns == "auto":
                    cmd = f"networksetup -setdnsservers '{service}' empty"
                else:
                    cmd = f"networksetup -setdnsservers '{service}' {dns}"
                self.run_action(cmd, tag)
            else:
                self.run_action("echo 'Serviço de rede não encontrado'", tag)
        else:
            self.run_action("echo 'Configuração de DNS não suportada neste SO'", tag)

    def scan_ports_interactive(self):
        log = getattr(self, "log_net")
        log.delete("1.0", "end")
        log.insert("end", "Escaneando portas abertas...\n")
        try:
            if self.SO == "Linux":
                output = subprocess.check_output("ss -tuln | tail -n +2", shell=True, text=True)
                lines = output.strip().split('\n')
                ports = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        proto = parts[0]
                        addr_port = parts[4]
                        if ':' in addr_port:
                            port = addr_port.split(':')[-1]
                            ports.append((proto, port))
            elif self.SO == "Windows":
                output = subprocess.check_output("netstat -an | findstr LISTENING", shell=True, text=True)
                lines = output.strip().split('\n')
                ports = []
                for line in lines:
                    parts = line.split()
                    if len(parts) > 1:
                        addr = parts[1]
                        if ':' in addr:
                            port = addr.split(':')[-1]
                            ports.append(("TCP", port))
            elif self.SO == "Darwin":
                output = subprocess.check_output("lsof -i -P -n | grep LISTEN", shell=True, text=True)
                lines = output.strip().split('\n')
                ports = []
                for line in lines:
                    parts = line.split()
                    if len(parts) > 8:
                        proto = parts[7].split('/')[0]
                        port = parts[8].split(':')[-1]
                        ports.append((proto, port))
            else:
                ports = []
            if not ports:
                log.insert("end", "Nenhuma porta aberta encontrada.\n")
                return
            log.insert("end", "Portas abertas:\n")
            for i, (proto, port) in enumerate(ports):
                log.insert("end", f"[{i+1}] {proto} {port}\n")
            log.insert("end", "\nPara fechar, use o firewall apropriado.\n")
        except Exception as e:
            log.insert("end", f"Erro ao escanear: {e}\n")

    # ---------- Drivers ----------
    def create_drivers_frame(self, parent):
        ctk.CTkLabel(parent, text="Drivers", font=("Inter", 28, "bold"), text_color=self.acc_color).pack(anchor="w", pady=(0, 20))

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="both", expand=True, pady=10)
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        cards = [
            ("🖥️ PCI (Vídeo/Rede)", "pci", "drv", False),
            ("📦 Atualizar Sistema", "update", "drv", False),
            ("🔌 USB Conectados", "usb", "drv", False),
            ("🧩 Módulos Kernel", "modules", "drv", False),
            ("⚙️ CPU Detalhada", "cpu_info", "drv", False),
            ("⚠️ Firmware Erros", "firmware", "drv", False),
            ("🎮 Drivers de Vídeo", "video_drv", "drv", False),
            ("🌐 Drivers de Rede", "net_drv", "drv", False),
            ("🔄 Atualizações Automáticas", "auto_update", "drv", False),
        ]

        for idx, (title, cmd, tag, _) in enumerate(cards):
            row, col = divmod(idx, 3)
            card = ctk.CTkFrame(grid, fg_color=self.bg_color, corner_radius=10, border_width=1, border_color=self.acc_color)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)
            card.configure(height=150)

            ctk.CTkLabel(card, text=title, font=("Inter", 14, "bold"), text_color=self.acc_color).pack(pady=(10, 5))
            btn = ctk.CTkButton(
                card,
                text="Executar",
                fg_color=self.acc_color,
                command=lambda c=cmd, t=tag: self.run_driver_action(c, t),
                cursor="hand2"
            )
            btn.pack(pady=5)

        self._add_console(parent, "drv")

    def run_driver_action(self, cmd, tag):
        if cmd == "pci":
            if self.SO == "Linux":
                self.run_action("lspci -nnk", tag)
            elif self.SO == "Darwin":
                self.run_action("system_profiler SPHardwareDataType", tag)
            elif self.SO == "Windows":
                self.run_action("wmic path win32_VideoController get name", tag)
        elif cmd == "update":
            if self.SO == "Linux":
                self.run_action("sudo dnf upgrade -y || sudo apt upgrade -y", tag)
            elif self.SO == "Windows":
                self.run_action("winget upgrade --all", tag)
            elif self.SO == "Darwin":
                self.run_action("brew upgrade", tag)
        elif cmd == "usb":
            if self.SO == "Linux":
                self.run_action("lsusb", tag)
            elif self.SO == "Darwin":
                self.run_action("system_profiler SPUSBDataType", tag)
            elif self.SO == "Windows":
                self.run_action("wmic path Win32_USBControllerDevice get *", tag)
        elif cmd == "modules":
            if self.SO == "Linux":
                self.run_action("lsmod", tag)
            elif self.SO == "Darwin":
                self.run_action("kextstat", tag)
            elif self.SO == "Windows":
                self.run_action("driverquery", tag)
        elif cmd == "cpu_info":
            if self.SO == "Linux":
                self.run_action("lscpu", tag)
            elif self.SO == "Darwin":
                self.run_action("sysctl -a | grep machdep.cpu", tag)
            elif self.SO == "Windows":
                self.run_action("wmic cpu get name", tag)
        elif cmd == "firmware":
            if self.SO == "Linux":
                self.run_action("sudo dmesg | grep -i firmware", tag)
            elif self.SO == "Darwin":
                self.run_action("ioreg -l | grep -i firmware", tag)
            else:
                self.run_action("echo 'Firmware info not available'", tag)
        elif cmd == "video_drv":
            self.install_video_drivers()
        elif cmd == "net_drv":
            self.install_network_drivers()
        elif cmd == "auto_update":
            self.setup_auto_updates()
        else:
            self.run_action(f"echo 'Comando {cmd} não reconhecido'", tag)

    def install_video_drivers(self):
        log = getattr(self, "log_drv")
        log.delete("1.0", "end")
        log.insert("end", "Detectando GPU...\n")
        try:
            if self.SO == "Linux":
                lspci = subprocess.check_output("lspci | grep -i 'vga\\|3d'", shell=True, text=True)
                if "NVIDIA" in lspci:
                    log.insert("end", "GPU NVIDIA detectada. Instalando driver proprietário...\n")
                    if "fedora" in self._get_distro().lower():
                        cmd = "sudo dnf install nvidia-driver -y"
                    else:
                        cmd = "sudo apt install nvidia-driver -y"
                elif "AMD" in lspci:
                    log.insert("end", "GPU AMD detectada. Instalando driver amdgpu...\n")
                    if "fedora" in self._get_distro().lower():
                        cmd = "sudo dnf install xorg-x11-drv-amdgpu -y"
                    else:
                        cmd = "sudo apt install xserver-xorg-video-amdgpu -y"
                elif "Intel" in lspci:
                    log.insert("end", "GPU Intel detectada. Driver já incluso no kernel.\n")
                    cmd = "echo 'Driver Intel já presente'"
                else:
                    log.insert("end", "GPU não identificada.\n")
                    return
                self.run_action(cmd, "drv")
            elif self.SO == "Windows":
                log.insert("end", "No Windows, os drivers de vídeo são gerenciados pelo Windows Update.\n")
                self.run_action("echo 'Use o Gerenciador de Dispositivos para atualizar'", "drv")
            elif self.SO == "Darwin":
                log.insert("end", "No macOS, os drivers são atualizados via atualização do sistema.\n")
                self.run_action("softwareupdate --list", "drv")
        except Exception as e:
            log.insert("end", f"Erro: {e}\n")

    def install_network_drivers(self):
        log = getattr(self, "log_drv")
        log.delete("1.0", "end")
        log.insert("end", "Verificando placa de rede...\n")
        try:
            if self.SO == "Linux":
                lspci = subprocess.check_output("lspci | grep -i ethernet", shell=True, text=True)
                if "Realtek" in lspci:
                    log.insert("end", "Placa Realtek detectada. Instalando driver r8168...\n")
                    if "fedora" in self._get_distro().lower():
                        cmd = "sudo dnf install r8168 -y"
                    else:
                        cmd = "sudo apt install r8168-dkms -y"
                else:
                    log.insert("end", "Placa não Realtek. Driver padrão já deve funcionar.\n")
                    cmd = "echo 'Nenhuma ação necessária'"
                self.run_action(cmd, "drv")
            else:
                log.insert("end", "Detecção de drivers de rede disponível apenas no Linux.\n")
        except Exception as e:
            log.insert("end", f"Erro: {e}\n")

    def setup_auto_updates(self):
        log = getattr(self, "log_drv")
        log.delete("1.0", "end")
        if self.SO == "Linux":
            if "fedora" in self._get_distro().lower():
                log.insert("end", "Instalando e configurando dnf-automatic...\n")
                self.run_action("sudo dnf install dnf-automatic -y && sudo systemctl enable --now dnf-automatic.timer", "drv")
            elif "ubuntu" in self._get_distro().lower() or "debian" in self._get_distro().lower():
                log.insert("end", "Configurando unattended-upgrades...\n")
                self.run_action("sudo apt install unattended-upgrades -y && sudo dpkg-reconfigure -plow unattended-upgrades", "drv")
            else:
                log.insert("end", "Sistema não suportado para atualizações automáticas.\n")
        elif self.SO == "Windows":
            log.insert("end", "Configurando Windows Update para automático...\n")
            self.run_action("wuauclt /detectnow /updatenow", "drv")
        elif self.SO == "Darwin":
            log.insert("end", "Configurando atualizações automáticas do macOS...\n")
            self.run_action("sudo softwareupdate --schedule on", "drv")
        else:
            log.insert("end", "Sistema não suportado.\n")

    # ---------- Agente IA ----------
    def create_agente_frame(self, parent):
        ctk.CTkLabel(parent, text="Agente de IA", font=("Inter", 28, "bold"), text_color=self.acc_color).pack(pady=(0, 30))
        ctk.CTkLabel(parent, text="Conecte um modelo de IA:", font=("Inter", 16), text_color=self.text_color).pack(pady=10)

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="both", expand=True, pady=10)
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        for idx, ia in enumerate(config.AI_SUGGESTIONS):
            row, col = divmod(idx, 3)
            card = ctk.CTkFrame(grid, fg_color=self.bg_color, corner_radius=10, border_width=1, border_color=self.acc_color)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)
            card.configure(height=150)

            ctk.CTkLabel(card, text=ia, font=("Inter", 14, "bold"), text_color=self.acc_color).pack(pady=(10, 5))
            if ia == "Configurar IA Local":
                btn = ctk.CTkButton(
                    card,
                    text="Configurar",
                    fg_color=self.acc_color,
                    command=self.configure_local_ai,
                    cursor="hand2"
                )
            else:
                btn = ctk.CTkButton(
                    card,
                    text="Conectar",
                    fg_color=self.acc_color,
                    command=lambda i=ia: self.connect_ai(i),
                    cursor="hand2"
                )
            btn.pack(pady=5)

        self.ai_status = ctk.CTkLabel(parent, text="", font=("Inter", 12), text_color=self.acc_color)
        self.ai_status.pack(pady=20)

    def connect_ai(self, ia_name):
        self.ai_status.configure(text=f"Conectado a {ia_name} (simulação)")

    def configure_local_ai(self):
        if not hasattr(self, "log_agente"):
            self._add_console(self.frames["agente"], "agente")
        log = getattr(self, "log_agente")
        log.delete("1.0", "end")
        log.insert("end", "Configurando IA local...\n")
        log.insert("end", "Instalando Ollama...\n")
        self.run_action("curl -fsSL https://ollama.com/install.sh | sh", "agente")
        log.insert("end", "Após instalação, execute 'ollama run llama2' para testar.\n")

    # ---------- Configurações (com agendamento automático e toast centralizado) ----------
    def create_config_frame(self, parent):
        ctk.CTkLabel(parent, text="Configurações", font=("Inter", 28, "bold"), text_color=self.acc_color).pack(anchor="w", pady=(0, 30))

        # === Seção: Configurações existentes ===
        frame_user = ctk.CTkFrame(parent, fg_color="transparent")
        frame_user.pack(fill="x", pady=10)
        ctk.CTkLabel(frame_user, text="Nome de usuário", font=("Inter", 14), text_color=self.text_color).pack(anchor="w")
        self.entry_user = ctk.CTkEntry(frame_user, placeholder_text="Seu nome", width=300)
        self.entry_user.insert(0, self.config.get("username", "ewerton"))
        self.entry_user.pack(anchor="w", pady=5)
        btn_reset_user = ctk.CTkButton(frame_user, text="Voltar para o padrão", fg_color="transparent", text_color=self.acc_color, command=lambda: self.entry_user.delete(0, "end") or self.entry_user.insert(0, "ewerton"), cursor="hand2")
        btn_reset_user.pack(anchor="w")

        frame_lang = ctk.CTkFrame(parent, fg_color="transparent")
        frame_lang.pack(fill="x", pady=10)
        ctk.CTkLabel(frame_lang, text="Idioma de Interface", font=("Inter", 14), text_color=self.text_color).pack(anchor="w")
        self.lang_var = ctk.StringVar(value=languages.get(self.config.get("language", "pt_BR"), "Português Brasileiro"))
        lang_menu = ctk.CTkOptionMenu(frame_lang, values=list(languages.values()), variable=self.lang_var, width=300)
        lang_menu.pack(anchor="w", pady=5)

        frame_scale = ctk.CTkFrame(parent, fg_color="transparent")
        frame_scale.pack(fill="x", pady=10)
        ctk.CTkLabel(frame_scale, text="Escala da interface *", font=("Inter", 14), text_color=self.text_color).pack(anchor="w")
        self.scale_var = ctk.StringVar(value=scales.get(self.config.get("ui_scale", "auto"), "Automático"))
        scale_menu = ctk.CTkOptionMenu(frame_scale, values=list(scales.values()), variable=self.scale_var, width=300)
        scale_menu.pack(anchor="w", pady=5)

        frame_theme = ctk.CTkFrame(parent, fg_color="transparent")
        frame_theme.pack(fill="x", pady=10)
        ctk.CTkLabel(frame_theme, text="Tema da interface", font=("Inter", 14), text_color=self.text_color).pack(anchor="w")

        theme_names = ["Padrão (Roxo)", "Cinza Profissional", "Escuro Total", "Claro Clean"]
        theme_keys = ["default", "grey", "dark", "light"]

        current_theme_key = self.config.get("theme", "default")
        if current_theme_key in theme_keys:
            default_idx = theme_keys.index(current_theme_key)
        else:
            default_idx = 0

        self.theme_name_var = ctk.StringVar(value=theme_names[default_idx])
        theme_menu = ctk.CTkOptionMenu(frame_theme, values=theme_names, variable=self.theme_name_var, width=300)
        theme_menu.pack(anchor="w", pady=5)

        frame_tab = ctk.CTkFrame(parent, fg_color="transparent")
        frame_tab.pack(fill="x", pady=10)
        ctk.CTkLabel(frame_tab, text="Abrir arquivo", font=("Inter", 14), text_color=self.text_color).pack(anchor="w")
        self.tab_var = ctk.StringVar(value="Na guia" if self.config.get("open_file_in_tab", False) else "Nova janela")
        tab_menu = ctk.CTkOptionMenu(frame_tab, values=["Na guia", "Nova janela"], variable=self.tab_var, width=300)
        tab_menu.pack(anchor="w", pady=5)

        # === NOVA SEÇÃO: AGENDAMENTO AUTOMÁTICO ===
        separator = ctk.CTkFrame(parent, height=2, fg_color=self.acc_color)
        separator.pack(fill="x", pady=20)

        ctk.CTkLabel(parent, text="Agendamento Automático", font=("Inter", 20, "bold"), text_color=self.acc_color).pack(anchor="w", pady=(0, 10))

        self.schedule_enabled_var = ctk.BooleanVar(value=self.config.get("schedule", {}).get("enabled", False))
        schedule_check = ctk.CTkCheckBox(parent, text="Executar tarefas de otimização automaticamente",
                                         variable=self.schedule_enabled_var, onvalue=True, offvalue=False,
                                         command=self.toggle_schedule_options)
        schedule_check.pack(anchor="w", pady=5)

        self.schedule_options_frame = ctk.CTkFrame(parent, fg_color="transparent")

        freq_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        freq_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(freq_frame, text="Frequência:", font=("Inter", 13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_freq_var = ctk.StringVar(value=self.config.get("schedule", {}).get("frequency", "weekly"))
        freq_menu = ctk.CTkOptionMenu(freq_frame, values=["daily", "weekly", "monthly", "custom"], variable=self.schedule_freq_var,
                                      command=self.update_schedule_visibility, width=150)
        freq_menu.pack(side="left", padx=5)

        time_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        time_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(time_frame, text="Horário (HH:MM):", font=("Inter", 13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_hour_var = ctk.StringVar(value=self.config.get("schedule", {}).get("hour", "03:00"))
        hour_entry = ctk.CTkEntry(time_frame, textvariable=self.schedule_hour_var, placeholder_text="03:00", width=100)
        hour_entry.pack(side="left", padx=5)

        self.weekday_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        self.weekday_frame.pack_forget()
        ctk.CTkLabel(self.weekday_frame, text="Dia da semana:", font=("Inter", 13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_weekday_var = ctk.StringVar(value=self.config.get("schedule", {}).get("day_of_week", "monday"))
        weekday_menu = ctk.CTkOptionMenu(self.weekday_frame,
                                         values=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                                         variable=self.schedule_weekday_var, width=150)
        weekday_menu.pack(side="left", padx=5)

        self.monthday_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        self.monthday_frame.pack_forget()
        ctk.CTkLabel(self.monthday_frame, text="Dia do mês:", font=("Inter", 13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_monthday_var = ctk.IntVar(value=self.config.get("schedule", {}).get("day_of_month", 1))
        monthday_entry = ctk.CTkEntry(self.monthday_frame, textvariable=self.schedule_monthday_var, placeholder_text="1", width=50)
        monthday_entry.pack(side="left", padx=5)

        self.custom_interval_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        self.custom_interval_frame.pack_forget()
        ctk.CTkLabel(self.custom_interval_frame, text="Intervalo (dias):", font=("Inter", 13), text_color=self.text_color).pack(side="left", padx=5)
        self.schedule_interval_var = ctk.IntVar(value=self.config.get("schedule", {}).get("interval_days", 7))
        interval_entry = ctk.CTkEntry(self.custom_interval_frame, textvariable=self.schedule_interval_var, placeholder_text="7", width=50)
        interval_entry.pack(side="left", padx=5)

        tasks_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        tasks_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(tasks_frame, text="Tarefas a executar:", font=("Inter", 13, "bold"), text_color=self.acc_color).pack(anchor="w", pady=5)

        self.schedule_tasks = {}
        task_list = [
            ("cache", "🧹 Limpeza de Cache"),
            ("swap", "🔄 Reset de Swap"),
            ("check", "✅ Verificar Erros"),
            ("update", "📦 Atualizar Sistema (requer privilégios)"),
            ("turbo", "🔥 Modo Turbo (temporário)")
        ]
        saved_tasks = self.config.get("schedule", {}).get("tasks", ["cache", "swap", "check"])
        for task_key, task_label in task_list:
            var = ctk.BooleanVar(value=task_key in saved_tasks)
            cb = ctk.CTkCheckBox(tasks_frame, text=task_label, variable=var, onvalue=True, offvalue=False)
            cb.pack(anchor="w", padx=20, pady=2)
            self.schedule_tasks[task_key] = var

        self.schedule_elevated_var = ctk.BooleanVar(value=self.config.get("schedule", {}).get("elevated", False))
        elevated_check = ctk.CTkCheckBox(self.schedule_options_frame, text="Executar com privilégios de administrador (quando necessário)",
                                          variable=self.schedule_elevated_var, onvalue=True, offvalue=False)
        elevated_check.pack(anchor="w", pady=5)

        log_frame = ctk.CTkFrame(self.schedule_options_frame, fg_color="transparent")
        log_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(log_frame, text=f"Logs salvos em: {config.LOG_DIR}", font=("Inter", 11), text_color=self.text_color).pack(side="left", padx=5)
        btn_open_logs = ctk.CTkButton(log_frame, text="Abrir pasta", command=self.open_logs_folder, width=100, height=25)
        btn_open_logs.pack(side="left", padx=5)

        btn_save_schedule = ctk.CTkButton(self.schedule_options_frame, text="Salvar configurações de agendamento",
                                          fg_color=self.acc_color, command=self.save_schedule_config, width=300, height=40)
        btn_save_schedule.pack(pady=15)

        self.toggle_schedule_options()
        self.update_schedule_visibility(self.schedule_freq_var.get())

        self.schedule_options_frame.pack(fill="x", pady=10)

        separator2 = ctk.CTkFrame(parent, height=2, fg_color=self.acc_color)
        separator2.pack(fill="x", pady=20)

        ctk.CTkLabel(parent, text="* - As alterações serão aplicadas após reiniciar o aplicativo", font=("Inter", 10), text_color="#888888").pack(anchor="w", pady=20)

        btn_apply = ctk.CTkButton(parent, text="Aplicar", fg_color=self.acc_color, command=self.apply_config, width=200, height=40, cursor="hand2")
        btn_apply.pack(pady=20)

    def toggle_schedule_options(self):
        if self.schedule_enabled_var.get():
            for child in self.schedule_options_frame.winfo_children():
                self._enable_widget(child)
        else:
            for child in self.schedule_options_frame.winfo_children():
                self._disable_widget(child)

    def _enable_widget(self, widget):
        if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
            for child in widget.winfo_children():
                self._enable_widget(child)
        else:
            try:
                widget.configure(state="normal")
            except:
                pass

    def _disable_widget(self, widget):
        if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
            for child in widget.winfo_children():
                self._disable_widget(child)
        else:
            try:
                widget.configure(state="disabled")
            except:
                pass

    def update_schedule_visibility(self, choice):
        self.weekday_frame.pack_forget()
        self.monthday_frame.pack_forget()
        self.custom_interval_frame.pack_forget()
        if choice == "weekly":
            self.weekday_frame.pack(fill="x", pady=5)
        elif choice == "monthly":
            self.monthday_frame.pack(fill="x", pady=5)
        elif choice == "custom":
            self.custom_interval_frame.pack(fill="x", pady=5)

    def open_logs_folder(self):
        try:
            if self.SO == "Windows":
                os.startfile(config.LOG_DIR)
            elif self.SO == "Darwin":
                subprocess.run(["open", config.LOG_DIR])
            else:
                subprocess.run(["xdg-open", config.LOG_DIR])
        except Exception as e:
            logging.error(f"Erro ao abrir pasta de logs: {e}")

    def save_schedule_config(self):
        # Mapeamento de valores em português para inglês
        freq_map = {
            "Diário": "daily",
            "Semanal": "weekly",
            "Mensal": "monthly",
            "Personalizado": "custom"
        }
        day_map = {
            "segunda": "monday",
            "terça": "tuesday",
            "quarta": "wednesday",
            "quinta": "thursday",
            "sexta": "friday",
            "sábado": "saturday",
            "domingo": "sunday"
        }

        schedule = {
            "enabled": self.schedule_enabled_var.get(),
            "frequency": freq_map[self.schedule_freq_var.get()],
            "hour": self.schedule_hour_var.get(),
            "day_of_week": day_map[self.schedule_weekday_var.get()],
            "day_of_month": self.schedule_monthday_var.get(),
            "interval_days": self.schedule_interval_var.get(),
            "tasks": [key for key, var in self.schedule_tasks.items() if var.get()],
            "elevated": self.schedule_elevated_var.get()
        }
        self.config["schedule"] = schedule
        with open(config.CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

        self.create_system_schedule(schedule)
        self.show_toast("Configurações salvas!")

    def show_toast(self, message, duration=3000):
        """Exibe uma pequena mensagem flutuante no centro da janela."""
        toast = ctk.CTkLabel(self, text=message,
                             fg_color=self.acc_color,
                             text_color="white",
                             corner_radius=10,
                             font=("Inter", 12),
                             padx=20, pady=10)
        toast.place(relx=0.5, rely=0.5, anchor="center")
        self.after(duration, toast.destroy)

    def create_system_schedule(self, schedule):
        if not schedule["enabled"]:
            self.remove_system_schedule()
            return

        agent_cmd = f"python3 {config.AGENT_SCRIPT}"

        if self.SO == "Linux":
            self._schedule_linux(schedule, agent_cmd)
        elif self.SO == "Windows":
            self._schedule_windows(schedule, agent_cmd)
        elif self.SO == "Darwin":
            self._schedule_macos(schedule, agent_cmd)

    def _schedule_linux(self, schedule, cmd):
        try:
            current = subprocess.check_output("crontab -l 2>/dev/null", shell=True, text=True)
        except:
            current = ""

        hour, minute = schedule["hour"].split(":")
        if schedule["frequency"] == "daily":
            cron_time = f"{minute} {hour} * * *"
        elif schedule["frequency"] == "weekly":
            day_map = {"monday":1, "tuesday":2, "wednesday":3, "thursday":4, "friday":5, "saturday":6, "sunday":0}
            dow = day_map.get(schedule["day_of_week"], 1)
            cron_time = f"{minute} {hour} * * {dow}"
        elif schedule["frequency"] == "monthly":
            day = schedule["day_of_month"]
            cron_time = f"{minute} {hour} {day} * *"
        else:
            cron_time = f"{minute} {hour} * * *"

        full_cmd = f"{cmd} >> {config.LOG_DIR}/schedule.log 2>&1"

        new_crontab = []
        for line in current.splitlines():
            if "speedscan-agent.py" not in line:
                new_crontab.append(line)
        new_crontab.append(f"{cron_time} {full_cmd}")

        tmp_file = "/tmp/speedscan_cron"
        with open(tmp_file, "w") as f:
            f.write("\n".join(new_crontab) + "\n")
        subprocess.run(f"crontab {tmp_file}", shell=True)
        os.unlink(tmp_file)

    def _schedule_windows(self, schedule, cmd):
        task_name = "SpeedScanAgent"
        hour, minute = schedule["hour"].split(":")
        if schedule["frequency"] == "daily":
            schtask_cmd = f'schtasks /create /tn "{task_name}" /tr "{cmd}" /sc daily /st {hour}:{minute} /f'
        elif schedule["frequency"] == "weekly":
            day_map = {"monday":"MON", "tuesday":"TUE", "wednesday":"WED", "thursday":"THU", "friday":"FRI", "saturday":"SAT", "sunday":"SUN"}
            dow = day_map.get(schedule["day_of_week"], "MON")
            schtask_cmd = f'schtasks /create /tn "{task_name}" /tr "{cmd}" /sc weekly /d {dow} /st {hour}:{minute} /f'
        elif schedule["frequency"] == "monthly":
            day = schedule["day_of_month"]
            schtask_cmd = f'schtasks /create /tn "{task_name}" /tr "{cmd}" /sc monthly /d {day} /st {hour}:{minute} /f'
        else:
            return
        if schedule["elevated"]:
            schtask_cmd += " /ru SYSTEM"
        subprocess.run(schtask_cmd, shell=True)

    def _schedule_macos(self, schedule, cmd):
        plist_path = os.path.expanduser("~/Library/LaunchAgents/org.speedscan.agent.plist")
        hour, minute = schedule["hour"].split(":")
        import plistlib
        plist = {"Label": "org.speedscan.agent", "ProgramArguments": ["/bin/bash", "-c", cmd], "StartCalendarInterval": []}
        if schedule["frequency"] == "daily":
            plist["StartCalendarInterval"] = {"Hour": int(hour), "Minute": int(minute)}
        elif schedule["frequency"] == "weekly":
            day_map = {"monday":1, "tuesday":2, "wednesday":3, "thursday":4, "friday":5, "saturday":6, "sunday":0}
            dow = day_map.get(schedule["day_of_week"], 1)
            plist["StartCalendarInterval"] = {"Weekday": dow, "Hour": int(hour), "Minute": int(minute)}
        elif schedule["frequency"] == "monthly":
            plist["StartCalendarInterval"] = {"Day": schedule["day_of_month"], "Hour": int(hour), "Minute": int(minute)}
        else:
            return
        with open(plist_path, "wb") as f:
            plistlib.dump(plist, f)
        subprocess.run(f"launchctl load {plist_path}", shell=True)

    def remove_system_schedule(self):
        if self.SO == "Linux":
            try:
                current = subprocess.check_output("crontab -l 2>/dev/null", shell=True, text=True)
                new_crontab = [line for line in current.splitlines() if "speedscan-agent.py" not in line]
                tmp_file = "/tmp/speedscan_cron"
                with open(tmp_file, "w") as f:
                    f.write("\n".join(new_crontab) + "\n")
                subprocess.run(f"crontab {tmp_file}", shell=True)
                os.unlink(tmp_file)
            except:
                pass
        elif self.SO == "Windows":
            subprocess.run('schtasks /delete /tn "SpeedScanAgent" /f', shell=True)
        elif self.SO == "Darwin":
            plist_path = os.path.expanduser("~/Library/LaunchAgents/org.speedscan.agent.plist")
            subprocess.run(f"launchctl unload {plist_path}", shell=True)
            if os.path.exists(plist_path):
                os.unlink(plist_path)

    def apply_config(self):
        self.config["username"] = self.entry_user.get()
        selected_lang = self.lang_var.get()
        for k, v in languages.items():
            if v == selected_lang:
                self.config["language"] = k
                break
        selected_scale = self.scale_var.get()
        for k, v in scales.items():
            if v == selected_scale:
                self.config["ui_scale"] = k
                break

        theme_names = ["Padrão (Roxo)", "Cinza Profissional", "Escuro Total", "Claro Clean"]
        theme_keys = ["default", "grey", "dark", "light"]
        selected_theme_name = self.theme_name_var.get()
        if selected_theme_name in theme_names:
            idx = theme_names.index(selected_theme_name)
            self.config["theme"] = theme_keys[idx]
        else:
            self.config["theme"] = "default"

        self.config["open_file_in_tab"] = (self.tab_var.get() == "Na guia")

        with open(config.CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

        python = sys.executable
        os.execl(python, python, *sys.argv)

    # ---------- Sobre ----------
    def create_sobre_frame(self, parent):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(parent, fg_color=self.light_bg, corner_radius=15, border_width=2, border_color=self.acc_color)
        card.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")
        card.grid_propagate(False)
        card.configure(width=600, height=500)

        ctk.CTkLabel(card, text="⚡ SpeedScan", font=("Inter", 36, "bold"), text_color=self.acc_color).pack(pady=(40, 10))
        ctk.CTkLabel(card, text="Versão Beta 0.9.0", font=("Inter", 14), text_color="#888888").pack()

        info_text = (
            "Desenvolvedor: Ewerton Vasconcelos\n"
            "Tecnologias: Python, CustomTkinter, psutil\n"
            "Repositório: github.com/ewertonvasconcelos/speedscan\n\n"
            "Este software está em fase de desenvolvimento.\n"
            "Não foi lançado oficialmente.\n\n"
            "Funcionalidades:\n"
            "• Monitoramento de hardware em tempo real\n"
            "• Otimização de sistema (cache, swap, turbo)\n"
            "• Instalação de apps gamers (Steam, Lutris, Dolphin)\n"
            "• Configuração de DNS e rede\n"
            "• Diagnóstico e atualização de drivers\n"
            "• Conexão com modelos de IA\n"
            "• Temas personalizáveis\n"
            "• Agendamento automático de tarefas\n\n"
            "© 2026 Ewerton Vasconcelos. Todos os direitos reservados."
        )
        ctk.CTkLabel(card, text=info_text, font=("Inter", 12), justify="left", text_color=self.text_color).pack(pady=20, padx=30)

    # ---------- Utilitários (consoles) ----------
    def _add_console(self, parent, tag):
        btn = ctk.CTkButton(
            parent,
            text="Detalhes ⌄",
            fg_color="transparent",
            text_color=self.acc_color,
            hover_color=self.acc_color,
            corner_radius=20,
            command=lambda: self.toggle_console(tag),
            cursor="hand2"
        )
        setattr(self, f"detail_btn_{tag}", btn)

        log = ctk.CTkTextbox(parent, height=150, fg_color="#000000", text_color="#10b981", font=("Consolas", 11))
        setattr(self, f"log_{tag}", log)
        self.consoles_visible[tag] = False

    def show_details_button(self, tag):
        btn = getattr(self, f"detail_btn_{tag}")
        if not btn.winfo_ismapped():
            btn.pack(anchor="e", pady=5)
        btn.configure(text="Detalhes ⌄")

    def hide_details_button(self, tag):
        btn = getattr(self, f"detail_btn_{tag}")
        if btn.winfo_ismapped():
            btn.pack_forget()

    def toggle_console(self, tag):
        log = getattr(self, f"log_{tag}")
        btn = getattr(self, f"detail_btn_{tag}")
        if self.consoles_visible.get(tag, False):
            log.pack_forget()
            btn.pack_forget()
            self.consoles_visible[tag] = False
        else:
            log.pack(fill="x", pady=5, before=btn)
            btn.configure(text="Detalhes ⌃")
            self.consoles_visible[tag] = True

    def run_action(self, cmd, tag):
        log = getattr(self, f"log_{tag}")
        log.delete("1.0", "end")
        self.hide_details_button(tag)
        self.consoles_visible[tag] = False
        threading.Thread(target=self._execute, args=(cmd, log, tag), daemon=True).start()

    def _execute(self, cmd, log, tag):
        if self.SO == "Linux" and "sudo" in cmd:
            full_cmd = f"pkexec bash -c '{cmd}'"
        else:
            full_cmd = cmd
        proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            self.after(0, lambda l=line: self._update_log(log, l))
        proc.wait()
        self.after(0, lambda: self._update_log(log, "\n-- COMANDO FINALIZADO --\n"))
        self.after(0, lambda: self.show_details_button(tag))

    def _update_log(self, log, text):
        log.insert("end", text)
        log.see("end")

    # ---------- Funções específicas ----------
    def toggle_turbo(self):
        self.turbo_active = not self.turbo_active
        if self.SO == "Linux":
            cmd = "sudo cpupower frequency-set -g performance" if self.turbo_active else "sudo cpupower frequency-set -g powersave"
        elif self.SO == "Windows":
            guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" if self.turbo_active else "381b4222-f694-41f0-9685-ff5bb260df2e"
            cmd = f"powercfg /setactive {guid}"
        elif self.SO == "Darwin":
            cmd = "echo 'Modo Turbo não disponível no macOS'"
        else:
            cmd = "echo 'Sistema não suportado'"
        self.run_action(cmd, "ot")

    def toggle_ping(self):
        if not self.ping_active:
            self.ping_active = True
            threading.Thread(target=self._ping_loop, daemon=True).start()
        else:
            self.ping_active = False

    def _ping_loop(self):
        while self.ping_active:
            try:
                param = "-n" if self.SO == "Windows" else "-c"
                p = subprocess.run(
                    ["ping", param, "1", "-W", "1", "8.8.8.8"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                match = re.search(r'time[=<](\d+\.?\d*)', p.stdout, re.IGNORECASE) or \
                        re.search(r'tempo[=<](\d+\.?\d*)', p.stdout, re.IGNORECASE) or \
                        re.search(r'(\d+\.?\d*) ?ms', p.stdout)
                res = match.group(1) if match else "Erro"
                self.after(0, lambda r=res: self.ping_label.configure(text=f"{r} ms"))
            except:
                self.after(0, lambda: self.ping_label.configure(text="-- ms"))
            time.sleep(2)

    # ---------- Hardware monitor ----------
    def hardware_monitor(self):
        while True:
            if self.current_module == "sistema":
                self.after(0, self.update_sys_info)
            time.sleep(2)

    def _on_mousewheel(self, event):
        """Rola o frame scrollable sob o mouse, independentemente do foco."""
        widget = event.widget
        # Determina a direção e intensidade do scroll
        if self.SO == "Linux":
            # No Linux, os eventos são Button-4 (cima) e Button-5 (baixo)
            delta = -1 if event.num == 4 else 1
        else:
            # No Windows/macOS, event.delta positivo para cima
            delta = -1 * (event.delta / 120)
        # Procura um CTkScrollableFrame ancestral
        while widget is not None:
            if isinstance(widget, ctk.CTkScrollableFrame):
                if self.SO == "Linux":
                    widget._parent_canvas.yview_scroll(delta, "units")
                else:
                    widget._parent_canvas.yview_scroll(int(delta), "units")
                return
            widget = widget.master

if __name__ == "__main__":
    app = SpeedScan()
    app.mainloop()

