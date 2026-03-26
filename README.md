# SpeedScan 🚀

SpeedScan é uma ferramenta completa de monitoramento de sistema com interface moderna e responsiva.

## 📸 Screenshots

![SpeedScan Interface](assets/screenshot.png)

## ✨ Características

- 🖥️ **Monitoramento em tempo real** de CPU, RAM, disco, bateria e mais
- 🎨 **Interface moderna** com CustomTkinter
- 📊 **Widgets centralizados** e responsivos
- 🌡️ **Monitoramento de temperatura**
- ⚡ **Teste de velocidade** da internet
- 💚 **Indicador de saúde** do sistema

## 🚀 Instalação

### Linux

#### AppImage (Recomendado)
```bash
wget https://github.com/ewertonvasconcelos/speedscan/releases/latest/download/SpeedScan.AppImage
chmod +x SpeedScan.AppImage
./SpeedScan.AppImage
```

#### Flatpak
```bash
flatpak install flathub org.speedscan.SpeedScan
flatpak run org.speedscan.SpeedScan
```

#### Debian/Ubuntu (.deb)
```bash
wget https://github.com/ewertonvasconcelos/speedscan/releases/latest/download/speedscan_amd64.deb
sudo dpkg -i speedscan_amd64.deb
```

#### Fedora/RPM (.rpm)
```bash
wget https://github.com/ewertonvasconcelos/speedscan/releases/latest/download/speedscan_x86_64.rpm
sudo rpm -i speedscan_x86_64.rpm
```

#### Snap
```bash
sudo snap install speedscan
```

### Windows

#### Executável (.exe)
1. Baixe `SpeedScan-Windows.exe` da [página de releases](https://github.com/ewertonvasconcelos/speedscan/releases)
2. Execute o instalador
3. Siga as instruções

### macOS

#### DMG
1. Baixe `SpeedScan-macOS.dmg` da [página de releases](https://github.com/ewertonvasconcelos/speedscan/releases)
2. Abra o DMG
3. Arraste o SpeedScan para Applications

### Android

#### APK (Versão Demo)
```bash
wget https://github.com/ewertonvasconcelos/speedscan/releases/latest/download/SpeedScan-debug.apk
# Instale no dispositivo Android
```

**Nota**: A versão Android é limitada devido à incompatibilidade do tkinter. Para funcionalidade completa, use as versões desktop.

## 🛠️ Desenvolvimento

### Pré-requisitos
- Python 3.10+
- tkinter
- pip

### Instalação do ambiente de desenvolvimento
```bash
git clone https://github.com/ewertonvasconcelos/speedscan.git
cd speedscan
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Executar em desenvolvimento
```bash
python -m core.main
```

### Empacotamento
Veja a pasta `packaging/` para scripts de build para diferentes plataformas.

## 📋 Dependências

- **customtkinter**: Interface gráfica moderna
- **psutil**: Informações do sistema
- **matplotlib**: Gráficos e visualizações
- **requests**: Requisições HTTP
- **speedtest-cli**: Teste de velocidade
- **pillow**: Processamento de imagens

## 🔧 Configuração

O SpeedScan detecta automaticamente seu sistema e configura os widgets correspondentes.

### Widgets Disponíveis
- 🖥️ CPU - Uso do processador
- 💾 RAM - Memória utilizada
- 🎮 GPU - Placa de vídeo
- 🔋 Bateria - Status e percentual
- 💿 Discos - Uso do armazenamento
- 🌡️ Temperatura - Monitoramento térmico
- ⏳ Uptime - Tempo de atividade
- ⚙️ Kernel - Versão do kernel
- 🐧 Distribuição - Sistema operacional
- 🖥️ Hostname - Nome do computador
- 💚 Saúde - Saúde geral do sistema

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🐛 Problemas

Encontrou um problema? [Abra uma issue](https://github.com/ewertonvasconcelos/speedscan/issues)!

## 🙏 Agradecimentos

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) pela interface moderna
- [psutil](https://github.com/giampaolo/psutil) pelas informações do sistema
- Comunidade Python pelas ferramentas incríveis

---

**SpeedScan** - Monitoramento do sistema, simplificado. 🚀
