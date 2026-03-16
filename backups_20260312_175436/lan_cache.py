#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LANCache integration module (game caching server).
Version 1.0.0
"""

import logging
import subprocess
import os
from pathlib import Path

from core import config


class LANCacheManager:
    """Manages LANCache (docker-based local game caching server)."""

    def __init__(self, so):
        """Initialize with the operating system.

        Args:
            so (str): Operating system (Linux, Windows, Darwin).
        """
        self.so = so
        self.compose_url = "https://github.com/lancachenet/docker-compose/raw/master/docker-compose.yml"
        self.env_url = "https://github.com/lancachenet/docker-compose/raw/master/lancache.env"

    def is_docker_installed(self):
        """Check if Docker is installed on the system.

        Returns:
            bool: True if Docker is available.
        """
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception as e:
            logging.error(f"Error checking Docker installation: {e}")
            return False

    def install_docker(self):
        """Return a list of commands to install Docker on the current system.

        Returns:
            list of str: Commands to be executed sequentially.
        """
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
                return ["echo 'Distribution not supported for automatic Docker installation'"]
        elif self.so == "Darwin":
            return [
                "echo \"For macOS, install Docker Desktop manually: https://docs.docker.com/desktop/install/mac-install/\""
            ]
        elif self.so == "Windows":
            return [
                "echo \"For Windows, install Docker Desktop manually: https://docs.docker.com/desktop/install/windows-install/\""
            ]
        return []

    def get_install_commands(self):
        """Return a list of commands to set up LANCache containers.

        Returns:
            list of str: Commands to be executed in order.
        """
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
        """Get the current status of the LANCache service.

        Returns:
            str: A message describing whether LANCache is running.
        """
        try:
            result = subprocess.run(["docker", "ps", "--filter", "name=lancache", "--format", "table"], capture_output=True, text=True)
            if "lancache" in result.stdout:
                return "✅ LANCache is running"
            else:
                return "❌ LANCache is not running"
        except FileNotFoundError:
            return "❌ Docker is not installed"
        except Exception as e:
            logging.error(f"Error checking LANCache status: {e}")
            return "❌ Error checking status"

    def stop(self):
        """Return a command to stop the LANCache containers.

        Returns:
            list of str: A command list to stop the service.
        """
        home = Path.home()
        lancache_dir = home / "lancache"
        return [f"cd {lancache_dir} && sudo docker-compose down"]

    def configure_dns(self, dns_ip=None):
        """Generate a command to configure the system to use the LANCache DNS server.

        Args:
            dns_ip (str): IP address of the DNS container (if known).

        Returns:
            str or None: A command to run or None if unsupported.
        """
        if dns_ip is None:
            try:
                result = subprocess.run(["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", "lancache-dns"], capture_output=True, text=True)
                dns_ip = result.stdout.strip()
            except Exception as e:
                logging.error(f"Error obtaining DNS container IP: {e}")
                dns_ip = "127.0.0.1"
        if self.so == "Linux":
            return f"echo 'nameserver {dns_ip}' | sudo tee /etc/resolv.conf"
        elif self.so == "Windows":
            return f"netsh interface ip set dns name='Ethernet' static {dns_ip}"
        elif self.so == "Darwin":
            return f"networksetup -setdnsservers Wi-Fi {dns_ip}"
        return None
