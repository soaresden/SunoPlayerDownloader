"""
Afficheur de logs avec scrolling
"""

import tkinter as tk
from tkinter import scrolledtext
from config import *


class LogViewer(tk.Frame):
    """Widget d'affichage des logs"""
    
    def __init__(self, parent, lang_manager=None):
        """
        Args:
            parent: Widget parent
            lang_manager: Gestionnaire de langues (optionnel)
        """
        super().__init__(parent, bg=COLOR_PRIMARY)
        
        self.lang = lang_manager
        
        # Header
        self.header = tk.Label(
            self,
            text=self.lang.get('logs.title') if self.lang else "📝 Logs",
            font=("Arial", 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_TEXT_LIGHT,
            anchor=tk.W,
            padx=5
        )
        self.header.pack(fill=tk.X)
        
        # Zone de texte
        self.text = scrolledtext.ScrolledText(
            self,
            height=LOG_HEIGHT,
            font=("Consolas", 8),
            bg=COLOR_DARK_BG,
            fg=COLOR_TEXT_LIGHT,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.text.pack(fill=tk.BOTH, expand=True)
    
    def log(self, message: str):
        """
        Ajoute un message aux logs
        
        Args:
            message: Message à logger
        """
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)
    
    def clear(self):
        """Efface tous les logs"""
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)
    
    def update_texts(self):
        """Met à jour les textes après changement de langue"""
        if self.lang:
            self.header.config(text=self.lang.get('logs.title'))