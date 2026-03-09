from core import config
#!/usr/bin/env python3
import logging
# Módulo de integração com LANCache (servidor de cache para jogos)
# Versão 1.0.0

import subprocess
import os
from pathlib import Path

class LANCacheManager:
    def __init__(self, so):
        self.so = so
        self.compose_url = "https://github.com/lancachenet/docker-compose/raw/master/docker-compose.yml"
        self.env_url = "https://github.com/lancachenet/docker-compose/raw/master/lancache.env"

    def is_docker_installed(self):
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def install_docker(self):
        if self.so == "Linux":
            if os.path.exists("/etc/debian_version"):
                return [
                    "sudo apt update",
                    "sudo apt install -y docker.io",
                    "sudo systemctl enable --now docker",
                    "sudo usermod -aG docker $USER"
                ]
            elif os.path.exists("/etc/redhat-release"):
                return [
                    "sudo yum install -y yum-utils",
                    "sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo",
                    "sudo yum install -y docker-ce docker-ce-cli containerd.io",
                    "sudo systemctl enable --now docker",
                    "sudo usermod -aG docker $USER"
                ]
            else:
                return ["echo 'Distribuição não suportada para instalação automática do Docker'"]
        elif self.so == "Darwin":
            return [
                "echo 'No macOS, instale o Docker Desktop manualmente: https://docs.docker.com/desktop/install/mac-install/'"
            ]
        elif self.so == "Windows":
            return [
                "echo 'No Windows, instale o Docker Desktop manualmente: https://docs.docker.com/desktop/install/windows-install/'"
            ]
        return []

    def get_install_commands(self):
        home = Path.home()
        lancache_dir = home / "lancache"
        compose_file = lancache_dir / "docker-compose.yml"
        env_file = lancache_dir / "lancache.env"

        commands = []
        commands.append(f"mkdir -p {lancache_dir}")
        commands.append(f"wget -O {compose_file} {self.compose_url}")
        commands.append(f"wget -O {env_file} {self.env_url}")
        commands.append(f"cd {lancache_dir} && sudo docker-compose up -d")
        return commands

    def get_status(self):
        try:
            result = subprocess.run(["docker", "ps", "--filter", "name=lancache", "--format", "table"], capture_output=True, text=True)
            if "lancache" in result.stdout:
                return "✅ LANCache está em execução"
            else:
                return "❌ LANCache não está em execução"
        except:
            return "❌ Docker não está instalado ou não disponível"

    def stop(self):
        home = Path.home()
        lancache_dir = home / "lancache"
        return [f"cd {lancache_dir} && sudo docker-compose down"]

    def configure_dns(self, dns_ip=None):
        if dns_ip is None:
            try:
                result = subprocess.run(["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", "lancache-dns"], capture_output=True, text=True)
                dns_ip = result.stdout.strip()
            except:
                dns_ip = "127.0.0.1"
        if self.so == "Linux":
            return f"echo 'nameserver {dns_ip}' | sudo tee /etc/resolv.conf"
        elif self.so == "Windows":
            return f"netsh interface ip set dns name='Ethernet' static {dns_ip}"
        elif self.so == "Darwin":
            return f"networksetup -setdnsservers Wi-Fi {dns_ip}"
        return None
