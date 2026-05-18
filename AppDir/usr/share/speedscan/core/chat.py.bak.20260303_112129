#!/usr/bin/env python3
# core/chat.py
# =============================================================================
#   ███████╗██████╗ ███████╗███████╗██████╗ ███████╗ ██████╗ █████╗ ███╗   ██╗
#   ██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║
#   ███████╗██████╔╝█████╗  █████╗  ██║  ██║█████╗  ██║     ███████║██╔██╗ ██║
#   ╚════██║██╔═══╝ ██╔══╝  ██╔══╝  ██║  ██║██╔══╝  ██║     ██╔══██║██║╚██╗██║
#   ███████║██║     ███████╗███████╗██████╔╝███████╗╚██████╗██║  ██║██║ ╚████║
#   ╚══════╝╚═╝     ╚══════╝╚══════╝╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
# =============================================================================
# Interface de chat para integração com IAs (Ollama, OpenAI, etc.)
# Versão 0.2.0-beta
# =============================================================================

import customtkinter as ctk
import threading
import requests
import json
from pathlib import Path

class ChatFrame(ctk.CTkFrame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.configure(fg_color="transparent")

        self.history = []  # Lista de mensagens {role, content}
        self.current_ai = "Ollama (local)"  # padrão

        # Área de chat
        self.chat_display = ctk.CTkTextbox(self, wrap="word", font=("Inter", 12),
                                            fg_color=self.app.light_bg,
                                            text_color=self.app.text_color)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_display.configure(state="disabled")

        # Frame de entrada
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0,10))

        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Digite sua mensagem...")
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(input_frame, text="Enviar", command=self.send_message,
                                       fg_color=self.app.acc_color)
        self.send_btn.pack(side="right")

        # Seletor de IA (pode ser movido para configurações)
        ai_frame = ctk.CTkFrame(self, fg_color="transparent")
        ai_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(ai_frame, text="Modelo:", font=("Inter",12)).pack(side="left", padx=5)
        self.ai_var = ctk.StringVar(value="Ollama (local)")
        ai_menu = ctk.CTkOptionMenu(ai_frame, values=["Ollama (local)", "OpenAI GPT", "DeepSeek"],
                                     variable=self.ai_var, command=self.change_ai)
        ai_menu.pack(side="left", padx=5)

        self._add_message("system", "🤖 Conectado ao Ollama local. Digite /help para comandos.")

    def change_ai(self, choice):
        self.current_ai = choice
        self._add_message("system", f"🔄 Modelo alterado para {choice}. Configure a API nas configurações se necessário.")

    def send_message(self):
        msg = self.message_entry.get().strip()
        if not msg:
            return
        self.message_entry.delete(0, "end")
        self._add_message("user", msg)

        # Processa comandos especiais
        if msg.startswith("/"):
            self._handle_command(msg)
            return

        # Envia para a IA em thread separada
        threading.Thread(target=self._get_ai_response, args=(msg,), daemon=True).start()

    def _add_message(self, role, content):
        self.chat_display.configure(state="normal")
        if role == "user":
            self.chat_display.insert("end", f"Você: {content}\n\n")
        elif role == "assistant":
            self.chat_display.insert("end", f"IA: {content}\n\n")
        elif role == "system":
            self.chat_display.insert("end", f"{content}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        self.history.append({"role": role, "content": content})

    def _handle_command(self, cmd):
        if cmd == "/help":
            self._add_message("system", "Comandos disponíveis:\n/help - mostra esta ajuda\n/clear - limpa o chat\n/modelo - mostra modelo atual")
        elif cmd == "/clear":
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
            self.history = []
            self._add_message("system", "🧹 Chat limpo.")
        elif cmd == "/modelo":
            self._add_message("system", f"Modelo atual: {self.current_ai}")
        else:
            self._add_message("system", f"Comando desconhecido: {cmd}")

    def _get_ai_response(self, user_message):
        if self.current_ai == "Ollama (local)":
            self._query_ollama(user_message)
        elif self.current_ai == "OpenAI GPT":
            self._query_openai(user_message)
        elif self.current_ai == "DeepSeek":
            self._query_deepseek(user_message)
        else:
            self._add_message("system", "⚠️ Modelo não configurado. Use /modelo para ver opções.")

    def _query_ollama(self, message):
        try:
            # Monta o histórico para contexto
            messages = [{"role": m["role"], "content": m["content"]} for m in self.history if m["role"] != "system"]
            # Chama a API do Ollama (padrão: http://localhost:11434/api/chat)
            payload = {
                "model": "llama3.2",  # ou qualquer modelo instalado
                "messages": messages,
                "stream": False
            }
            response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                reply = data.get("message", {}).get("content", "Sem resposta.")
                self.app.after(0, lambda: self._add_message("assistant", reply))
            else:
                self.app.after(0, lambda: self._add_message("system", f"Erro Ollama: {response.status_code}"))
        except Exception as e:
            self.app.after(0, lambda: self._add_message("system", f"Erro ao conectar ao Ollama: {e}"))

    def _query_openai(self, message):
        # Implementação simplificada - requer chave de API configurada
        self.app.after(0, lambda: self._add_message("system", "⚠️ OpenAI ainda não implementado. Configure sua chave nas configurações."))

    def _query_deepseek(self, message):
        self.app.after(0, lambda: self._add_message("system", "⚠️ DeepSeek ainda não implementado."))
