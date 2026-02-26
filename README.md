# ⚡ SpeedScan

![Versão](https://img.shields.io/badge/version-0.9.0--beta-blue)
![Licença](https://img.shields.io/badge/license-MIT-green)
![Plataformas](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS%20%7C%20Android-lightgrey)

SpeedScan é uma ferramenta de diagnóstico e otimização de sistemas desenvolvida em Python com CustomTkinter. Oferece monitoramento em tempo real, otimização de desempenho, configuração de rede e diagnóstico de drivers, tudo em uma interface moderna e intuitiva.

## ✨ Funcionalidades

- **Monitoramento do Sistema**: CPU, RAM, GPU, discos, uptime e bateria
- **Otimização**: Limpeza de cache, reset de swap, verificação de erros
- **Modo Turbo**: Ajusta o governador de CPU para máxima performance (Linux) ou plano de energia (Windows)
- **Rede**: Teste de ping, configuração de DNS (Cloudflare, Google, AdGuard), traceroute, informações Wi-Fi
- **Drivers**: Diagnóstico de hardware, atualização de drivers de vídeo/rede
- **Agente IA**: Conexão com modelos de IA (DeepSeek, GPT, Gemini, etc.) e configuração local (Ollama)
- **Temas**: Personalização com temas dark/light e reinicialização instantânea

## 📸 Capturas de Tela

| Sistema | Otimização | Rede |
|--------|------------|------|
| ![Sistema](screenshots/sistema.png) | ![Otimização](screenshots/otimizacao.png) | ![Rede](screenshots/rede.png) |

*Nota: As imagens acima são apenas ilustrativas. Substitua pelos prints reais do software.*

## 🖥️ Plataformas Suportadas

| Sistema | Status | Observações |
|---------|--------|-------------|
| 🐧 Linux | ✅ Funcional | Testado em Fedora, Solus, openSUSE, KDE Linux. Pacotes `.deb` e `.rpm` disponíveis. |
| 🪟 Windows | ✅ Funcional | Requer winget para instalação de apps |
| 🍏 macOS | ✅ Funcional | Requer Homebrew para instalação de apps |
| 📱 Android | 🚧 Em desenvolvimento | Versão separada com Kivy/BeeWare |

## 🚀 Instalação

### Linux – Pacotes `.deb` e `.rpm`
Baixe os pacotes da página de [releases](https://github.com/ewertonvasconcelos/speedscan/releases) ou diretamente do repositório:

- **Debian/Ubuntu**: `sudo dpkg -i speedscan_0.9.0_amd64.deb`
- **Fedora/openSUSE**: `sudo rpm -ivh speedscan-0.9.0-1.x86_64.rpm`

### Via código fonte (Linux, Windows, macOS)
```bash
git clone https://github.com/ewertonvasconcelos/speedscan.git
cd speedscan
pip install -r requirements.txt
python3 core/speedscan_app.py
