"""
Barre d'outils supérieure de l'application
"""

import tkinter as tk
from tkinter import ttk
from config import *


class Toolbar(tk.Frame):
    """Barre d'outils avec boutons principaux"""
    
    def __init__(self, parent, callbacks: dict, lang_manager):
        """
        Args:
            parent: Widget parent
            callbacks: Dict avec les callbacks
            lang_manager: Gestionnaire de langues
        """
        super().__init__(parent, bg=COLOR_DARK_BG, height=TOOLBAR_HEIGHT)
        self.pack_propagate(False)
        
        self.callbacks = callbacks
        self.lang = lang_manager
        
        # Logo + Titre
        logo_frame = tk.Frame(self, bg=COLOR_DARK_BG)
        logo_frame.pack(side=tk.LEFT, padx=15, pady=8)
        
        tk.Label(
            logo_frame,
            text="🎵",
            font=("Arial", 20),
            bg=COLOR_DARK_BG,
            fg=COLOR_SUNO_YELLOW
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Label(
            logo_frame,
            text="SUNO",
            font=("Arial", 16, "bold"),
            bg=COLOR_DARK_BG,
            fg=COLOR_SUNO_YELLOW
        ).pack(side=tk.LEFT, padx=(0, 3))
        
        tk.Label(
            logo_frame,
            text="Downloader",
            font=("Arial", 14),
            bg=COLOR_DARK_BG,
            fg=COLOR_TEXT_MUTED
        ).pack(side=tk.LEFT)
        
        # Status (droite)
        self.status_label = tk.Label(
            self,
            text="⚪",
            font=("Arial", 16),
            bg=COLOR_DARK_BG
        )
        self.status_label.pack(side=tk.RIGHT, padx=15)
        
        # Boutons (droite)
        self.btn_cookies = tk.Button(
            self,
            text=self.lang.get('toolbar.cookies'),
            font=("Arial", 10, "bold"),
            bg=COLOR_SUNO_YELLOW,
            fg=COLOR_DARK_BG,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=callbacks.get('load_cookies')
        )
        self.btn_cookies.pack(side=tk.RIGHT, padx=5, pady=8)
        
        tk.Button(
            self,
            text="🔄",
            font=("Arial", 12, "bold"),
            bg=COLOR_CARD_BG,
            fg=COLOR_SUNO_PINK,
            relief=tk.FLAT,
            padx=12,
            pady=8,
            cursor="hand2",
            command=callbacks.get('reload_cookies')
        ).pack(side=tk.RIGHT, padx=5, pady=8)
        
        # 🌍 Combobox langue
        lang_frame = tk.Frame(self, bg=COLOR_DARK_BG)
        lang_frame.pack(side=tk.RIGHT, padx=10, pady=8)
        
        tk.Label(
            lang_frame,
            text="🌍",
            font=("Arial", 12),
            bg=COLOR_DARK_BG,
            fg=COLOR_TEXT_LIGHT
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        style = ttk.Style()
        style.configure('Lang.TCombobox', background=COLOR_CARD_BG)
        
        self.lang_combo = ttk.Combobox(
            lang_frame,
            values=self.lang.get_available_languages(),
            state='readonly',
            width=10,
            font=("Arial", 9),
            style='Lang.TCombobox'
        )
        self.lang_combo.set(self.lang.current_language)
        self.lang_combo.pack(side=tk.LEFT)
        self.lang_combo.bind('<<ComboboxSelected>>', self._on_language_change)
    
    def _on_language_change(self, event):
        """Changement de langue"""
        new_lang = self.lang_combo.get()
        
        if self.callbacks.get('change_language'):
            self.callbacks['change_language'](new_lang)
    
    def update_texts(self):
        """Met à jour les textes après changement de langue"""
        self.btn_cookies.config(text=self.lang.get('toolbar.cookies'))
    
    def set_status(self, status: str):
        """Met à jour le status"""
        self.status_label.config(text=status)