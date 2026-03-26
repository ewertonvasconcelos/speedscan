#!/bin/bash
# Build Android APK for SpeedScan (Demo Version)

echo "🤖 Construindo APK Android..."

# NOTA: SpeedScan usa customtkinter/tkinter que não funciona no Android
# Este script cria uma versão demo com Kivy

# Instalar buildozer
pip install buildozer

# Criar versão Android demo
mkdir -p android_demo
cd android_demo

# Criar main.py para Android (versão simplificada)
cat > main.py << 'PYTHON_EOF'
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
import platform

class SpeedScanAndroidApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Título
        title = Label(
            text='SpeedScan Android',
            font_size='24sp',
            size_hint_y=None,
            height=50
        )
        layout.add_widget(title)
        
        # Informações do sistema
        info = Label(
            text=f'Sistema: {platform.system()}\n' +
                 f'Arquitetura: {platform.machine()}\n' +
                 f'Python: {platform.python_version()}\n\n' +
                 'NOTA: Versão demo.\n' +
                 'Versão completa disponível\n' +
                 'para Linux/Windows/macOS',
            font_size='16sp',
            text_size=(400, None),
            halign='center'
        )
        layout.add_widget(info)
        
        return layout

if __name__ == '__main__':
    SpeedScanAndroidApp().run()
PYTHON_EOF

# Copiar buildozer.spec
cp ../packaging/buildozer.spec .

# Construir APK
buildozer android debug

# Mover APK para dist
mv bin/*.apk ../../dist/
cd ..

echo "✅ APK Android demo criado em dist/"
echo "⚠️  NOTA: Versão limitada devido à incompatibilidade do tkinter no Android"
