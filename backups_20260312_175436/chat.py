#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat interface for integration with AI providers (Ollama, OpenAI, DeepSeek, etc.)
Version 1.0.0
"""

import customtkinter as ctk
import threading
import requests
import json
import logging
from pathlib import Path

from core import config


class ChatFrame(ctk.CTkFrame):
    """A chat frame that allows the user to interact with AI assistants.

    Attributes:
        app (SpeedScan): Reference to the main application.
        history (list): List of message dicts with 'role' and 'content'.
        current_ai (str): Current ai provider (ollama, openai, deepseek).
        ai_model (str): AI model name.
        endpoint (str): API endpoint URL.
        api_key (str): API key for cloud services.
    """

    def __init__(self, parent, app_instance, **kwargs):
        """Initialize the chat frame.

        Args:
            parent: Widget parent.
            app_instance: The main SpeedScan application instance.
            **kwargs: Additional customtkinter frame keywords.
        """
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.configure(fg_color="transparent")

        self.history = []
        self.current_ai = app_instance.config.get("ai", {}).get("provider", "ollama")
        self.ai_model = app_instance.config.get("ai", {}).get("model", "llama3.2")
        self.endpoint = app_instance.config.get("ai", {}).get("endpoint", "http://localhost:11434")
        self.api_key = app_instance.config.get("ai", {}).get("api_key", "")

        self.chat_display = ctk.CTkTextbox(self, wrap="word", font=("Inter", 12),
                                            fg_color=self.app.light_bg,
                                            text_color=self.app.text_color)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_display.configure(state="disabled")

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0,10))

        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Digite sua mensagem...")
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(input_frame, text="Enviar", command=self.send_message,
                                       fg_color=self.app.acc_color, cursor="hand2")
        self.send_btn.pack(side="right")

        self._add_message("system", "🤖 Conectado ao assistente. Digite /help para comandos.")

    def _add_message(self, role, content):
        """Add a message to the chat display and history.

        Args:
            role (str): 'user', 'assistant' or 'system'.
            content (str): Message content.
        """
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

    def send_message(self):
        """Send the user's message and trigger an AI response."""
        msg = self.message_entry.get().strip()
        if not msg:
            return
        self.message_entry.delete(0, "end")
        self._add_message("user", msg)

        if msg.startswith("/"):
            self._handle_command(msg)
            return

        threading.Thread(target=self._get_ai_response, args=(msg,), daemon=True).start()

    def _handle_command(self, cmd):
        """Handle special commands prefixed with '/'."""
        if cmd == "/help":
            self._add_message("system", "Comandos disponíveis:\n/help - ajuda\n/clear - limpa chat\n/modelo - mostra modelo atual\n/trash - lista lixeira\n/emptytrash - esvazia lixeira")
        elif cmd == "/clear":
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
            self.history = []
            self._add_message("system", "🧹 Chat limpo.")
        elif cmd == "/modelo":
            self._add_message("system", f"Modelo atual: {self.current_ai} ({self.ai_model})")
        elif cmd == "/trash":
            items = self.app.trash_manager.list_trash()
            if items:
                msg = "Itens na lixeira:\n" + "\n".join([f"{i['name']} (original: {i['original']})" for i in items])
            else:
                msg = "Lixeira vazia."
            self._add_message("system", msg)
        elif cmd == "/emptytrash":
            self.app.trash_manager.empty_trash()
            self._add_message("system", "🗑️ Lixeira esvaziada.")
        else:
            self._add_message("system", f"Comando desconhecido: {cmd}")

    def _get_ai_response(self, user_message):
        """Query the configured AI provider in a background thread."""
        if self.current_ai == "ollama":
            self._query_ollama(user_message)
        elif self.current_ai == "openai":
            self._query_openai(user_message)
        elif self.current_ai == "deepseek":
            self._query_deepseek(user_message)
        else:
            self.app.after(0, lambda: self._add_message("system", "⚡ Provider não suportado."))

    def _query_ollama(self, message):
        """Query an Ollama instance and display the response."""
        try:
            messages = [{"role": m["role"], "content": m["content"]} for m in self.history if m["role"] != "system"]
            payload = {
                "model": self.ai_model,
                "messages": messages,
                "stream": False
            }
            response = requests.post(f"{self.endpoint}/api/chat", json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                reply = data.get("message", {}).get("content", "Sem resposta.")
                self.app.after(0, lambda: self._add_message("assistant", reply))
            else:
                self.app.after(0, lambda: self._add_message("system", f"Erro Ollama: {response.status_code}"))
        except Exception as e:
            logging.error(f"Error querying Ollama: {e}")
            self.app.after(0, lambda e=e: self._add_message("system", f"Erro conectando ao Ollama: {e}"))

    def _query_openai(self, message):
        """OpenAI is not implemented yet. Show a message."""
        self.app.after(0, lambda: self._add_message("system", "⚡ OpenAI not implemented. Configure your key."))

    def _query_deepseek(self, message):
        """DeepSeek is not implemented yet. Show a message."""
        self.app.after(0, lambda: self._add_message("system", "⚡ DeepSeek not implemented."))
