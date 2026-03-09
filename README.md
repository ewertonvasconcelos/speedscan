![GitHub release (latest by date)](https://img.shields.io/github/v/release/ewertonvasconcelos/speedscan)
![GitHub all releases](https://img.shields.io/github/downloads/ewertonvasconcelos/speedscan/total)
![GitHub](https://img.shields.io/github/license/ewertonvasconcelos/speedscan)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ewertonvasconcelos/speedscan/build.yml?branch=main)
![GitHub last commit](https://img.shields.io/github/last-commit/ewertonvasconcelos/speedscan)
![GitHub repo size](https://img.shields.io/github/repo-size/ewertonvasconcelos/speedscan)

# ⚡ SpeedScan

<div align="center">
  <img src="assets/banner.png" alt="SpeedScan Banner" width="600"/>
  <br>
  <strong>Ferramenta all-in-one de diagnóstico e otimização de sistema com IA integrada</strong>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/CustomTkinter-5.2.2-blue?style=for-the-badge" alt="CustomTkinter">
  <img src="https://img.shields.io/badge/Psutil-5.9.0-blue?style=for-the-badge" alt="Psutil">
  <img src="https://img.shields.io/badge/Matplotlib-3.5.0-blue?style=for-the-badge" alt="Matplotlib">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

## 📋 Índice
- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Capturas de Tela](#-capturas-de-tela)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Instalação e Uso](#-instalação-e-uso)
- [Como Contribuir](#-como-contribuir)
- [Roadmap](#-roadmap)
- [Licença](#-licença)

## 📖 Sobre o Projeto

O SpeedScan nasceu da necessidade de ter uma ferramenta centralizada para diagnosticar e otimizar sistemas. Ele oferece desde informações detalhadas de hardware até um dashboard interativo e sugestões de melhorias baseadas em IA. É o **canivete suíço** para quem quer manter o computador sempre no máximo desempenho.

## ⚙️ Funcionalidades

- **📊 Dashboard Rotativo:** Acompanhe CPU, RAM, Disco e mais em widgets personalizáveis.
- **🌡️ Monitoramento em Tempo Real:** Temperaturas, saúde dos discos (S.M.A.R.T.) e processos.
- **🚀 Otimização do Sistema:** Limpeza de cache, reset de swap e modo turbo.
- **🌐 Análise de Rede:** Teste de velocidade, scanner de LAN e configuração de DNS.
- **📋 Gerenciador de Processos:** Visualize e gerencie processos em execução.
- **🤖 IA Proativa:** Receba sugestões inteligentes para otimizar seu sistema.
- **🔒 Segurança:** Verificação de portas abertas, status do firewall e atualizações de segurança.
- **💾 LANCache:** Acelere seus downloads de jogos com um cache local.
- **🎨 Temas Customizáveis:** Escolha entre temas claro e escuro.

## 🖼️ Capturas de Tela

<p align="center">
  <img src="screenshots/dashboard.png" alt="Dashboard" width="23%"/>
  <img src="screenshots/otimizacao.png" alt="Otimização" width="23%"/>
  <img src="screenshots/agente-ia.png" alt="Agente IA" width="23%"/>
  <img src="screenshots/configuracoes.png" alt="Configurações" width="23%"/>
</p>
<p align="center">
  <em>Exemplo do Dashboard, aba de Otimização, Agente IA e Configurações.</em>
</p>

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.11+
- **Interface Gráfica:** CustomTkinter
- **Monitoramento:** Psutil
- **Gráficos:** Matplotlib
- **Teste de Velocidade:** Speedtest-cli
- **IA Local:** Integração com Ollama (opcional)

## 💻 Instalação e Uso

### 📦 Pacotes prontos (recomendado)
Baixe a versão mais recente para seu sistema na [página de releases](https://github.com/ewertonvasconcelos/speedscan/releases).

- **Linux (Debian/Ubuntu):** `sudo dpkg -i speedscan_*.deb`
- **Linux (Fedora/openSUSE):** `sudo rpm -ivh speedscan-*.rpm`
- **Windows:** Execute o instalador `.exe`
- **macOS:** Monte a imagem `.dmg` e arraste para Applications

### 🐍 Executar a partir do código fonte
```bash
# Clone o repositório
git clone https://github.com/ewertonvasconcelos/speedscan.git
cd speedscan

# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt

# Execute o programa
python -m core.main
