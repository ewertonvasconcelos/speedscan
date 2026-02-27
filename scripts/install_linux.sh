#!/bin/bash
echo "⚙️ Instalando dependências..."
sudo eopkg it python3 python3-pillow -y 2>/dev/null
pip3 install customtkinter psutil pillow --user
chmod +x ~/speedscan/speedscan_app.py
echo "✅ Pronto! Use ./speedscan_app.py para iniciar."
