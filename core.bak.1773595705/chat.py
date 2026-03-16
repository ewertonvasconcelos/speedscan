#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat interface for integration with AI providers (Ollama, OpenAI, DeepSeek, etc.)
Version 1.0.0
"""
import customtkinter as ctk
import threading
import requests
import logging
from core import config

class ChatFrame(ctk.CTkFrame):
    def __init__(self, parent, app_instance, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app_instance
        self.configure(fg_color="transparent")

        self.history = []
        self.current_ai = app_instance.config_data.get("ai", {}).get("provider", "ollama")
        self.ai_model = app_instance.config_data.get("ai", {}).get("model", "llama3.2")
        self.endpoint = app_instance.config_data.get("ai", {}).get("endpoint", "http://localhost:11434")
        self.api_key = app_instance.config_data.get("ai", {}).get("api_key", "")

        self.chat_display = ctk.CTkTextbox(self, wrap="word", font=("Inter", 12),
                                            fg_color=self.app.light_bg,
                                            text_color=self.app.text_color)
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_display.configure(state="disabled")

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0,10))

        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Type your message...")
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(input_frame, text="Send", command=self.send_message,
                                      fg_color=self.app.acc_color, cursor="hand2")
        self.send_btn.pack(side="right")

        self._add_message("system", "🤖 Connected to assistant. Type /help for commands.")

    def _add_message(self, role, content):
        self.chat_display.configure(state="normal")
        if role == "user":
            self.chat_display.insert("end", f"You: {content}\n\n")
        elif role == "assistant":
            self.chat_display.insert("end", f"AI: {content}\n\n")
        elif role == "system":
            self.chat_display.insert("end", f"{content}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        self.history.append({"role": role, "content": content})

    def send_message(self):
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
        if cmd == "/help":
            self._add_message("system", "Available commands:\n/help - show this help\n/clear - clear chat\n/model - show current model\n/trash - list trash items\n/emptytrash - empty trash")
        elif cmd == "/clear":
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end")
            self.chat_display.configure(state="disabled")
            self.history = []
            self._add_message("system", "🗑️ Chat cleared.")
        elif cmd == "/model":
            self._add_message("system", f"Current model: {self.current_ai} ({self.ai_model})")
        elif cmd == "/trash":
            items = self.app.trash_manager.list_trash()
            if items:
                msg = "Items in trash:\n" + "\n".join([f"{i['name']} (original: {i['original']})" for i in items])
            else:
                msg = "Trash is empty."
            self._add_message("system", msg)
        elif cmd == "/emptytrash":
            self.app.trash_manager.empty_trash()
            self._add_message("system", "🗑️ Trash emptied.")
        else:
            self._add_message("system", f"Unknown command: {cmd}")

    def _get_ai_response(self, user_message):
        if self.current_ai == "ollama":
            self._query_ollama(user_message)
        elif self.current_ai == "openai":
            self._query_openai(user_message)
        elif self.current_ai == "deepseek":
            self._query_deepseek(user_message)
        else:
            self.app.after(0, lambda: self._add_message("system", "⚠️ Provider not supported."))

    def _query_ollama(self, message):
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
                reply = data.get("message", {}).get("content", "No response.")
                self.app.after(0, lambda: self._add_message("assistant", reply))
            else:
                self.app.after(0, lambda: self._add_message("system", f"Error Ollama: {response.status_code}"))
        except Exception as e:
            logging.error(f"Error querying Ollama: {e}")
            self.app.after(0, lambda e=e: self._add_message("system", f"Error connecting to Ollama: {e}"))

    def _query_openai(self, message):
        self.app.after(0, lambda: self._add_message("system", "⚠️ OpenAI not implemented. Configure your key."))

    def _query_deepseek(self, message):
        self.app.after(0, lambda: self._add_message("system", "⚠️ DeepSeek not implemented."))
