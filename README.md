# SpeedScan ⚡

O **SpeedScan** é uma central de otimização e diagnóstico de hardware de alta performance, desenvolvida especialmente para o ecossistema Linux (Solus/Eopkg). Com uma interface moderna e modular, ele une monitoramento em tempo real com ferramentas de automação gamer e rede.

---

## 🚀 Funcionalidades Principais

| Módulo | Descrição |
| :--- | :--- |
| **💻 Sistema** | Monitoramento detalhado de CPU, GPU, RAM e saúde de Discos (SSD/HDD). |
| **🎮 Gamer** | Modo Turbo (CPU Performance) e instaladores rápidos: Steam, Lutris, Wine e Bottles. |
| **🌐 Rede** | Teste de latência (Ping) e troca rápida de DNS (Cloudflare, Google, Auto). |
| **🛠 Drivers** | Diagnóstico via Kernel e listagem de dispositivos PCI/USB. |
| **🎨 Temas** | 4 estilos visuais (Dark, Grey, Light, Default) com troca instantânea. |
| **📦 Biblioteca** | Gerenciador local de instaladores .AppImage, .deb e .exe. |

---

## 🛠 Requisitos do Sistema

Para rodar o SpeedScan, você precisará de:
* **Linguagem:** Python 3.10+
* **Bibliotecas:** \`customtkinter\`, \`psutil\`, \`pillow\`
* **Privilégios:** Acesso root via \`pkexec\` (para comandos de sistema).

---

## 🔧 Como Instalar e Rodar

### 1. Clonar e Instalar Dependências
\`\`\`bash
git clone https://github.com/ewertonvasconcelos/speedscan.git
cd speedscan
pip install customtkinter psutil pillow
\`\`\`

### 2. Executar o Aplicativo
\`\`\`bash
python3 speedscan_app.py
\`\`\`

---
Desenvolvido por [Ewerton Vasconcelos](https://github.com/ewertonvasconcelos)
