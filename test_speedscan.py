#!/usr/bin/env python3
import sys
import os

# Adicionar caminho do SpeedScan
sys.path.insert(0, '/home/ewerton/speedscan/speedscan')

try:
    import tkinter
    print("✅ Tkinter disponível")
    
    import customtkinter
    print("✅ CustomTkinter disponível")
    
    import psutil
    print("✅ PSUtil disponível")
    
    from core.main import SpeedScan
    print("✅ SpeedScan importado com sucesso")
    
    # Criar janela de teste
    app = customtkinter.CTk()
    app.title("SpeedScan - Teste")
    app.geometry("400x300")
    
    label = customtkinter.CTkLabel(app, text="SpeedScan funcionando!", font=("Arial", 20))
    label.pack(pady=50)
    
    button = customtkinter.CTkButton(app, text="Fechar", command=app.quit)
    button.pack(pady=20)
    
    print("🚀 Interface de teste criada")
    print("   Feche a janela para continuar...")
    
    app.mainloop()
    
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)
