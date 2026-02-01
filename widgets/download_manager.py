"""
Gestionnaire de téléchargements pour le player
"""

import tkinter as tk
from tkinter import Listbox, Menu
from typing import List, Dict, Callable
from config import COLOR_CARD_BG, COLOR_DARK_BG, COLOR_SUNO_ORANGE, COLOR_TEXT_LIGHT, COLOR_DANGER


class DownloadManager(tk.Frame):
    """Gestion de la liste de téléchargements"""
    
    def __init__(self, parent, callbacks: dict, lang_manager):
        """
        Args:
            parent: Widget parent
            callbacks: Dict des callbacks
            lang_manager: Gestionnaire de langues
        """
        super().__init__(parent, bg=COLOR_CARD_BG)
        
        self.callbacks = callbacks
        self.lang = lang_manager
        self.download_list = []
        
        self._create_ui()
    
    def _create_ui(self):
        """Crée l'interface"""
        # Header
        header = tk.Frame(self, bg=COLOR_CARD_BG)
        header.pack(fill=tk.X)
        
        self.count_label = tk.Label(
            header,
            text="⬇️ DOWNLOADS (0)",
            font=("Arial", 9, "bold"),
            bg=COLOR_CARD_BG,
            fg=COLOR_SUNO_ORANGE
        )
        self.count_label.pack(side=tk.LEFT, pady=3)
        
        # Listbox
        list_frame = tk.Frame(self, bg=COLOR_DARK_BG, bd=1, relief=tk.SOLID)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=3)
        
        scrollbar = tk.Scrollbar(list_frame, bg=COLOR_CARD_BG)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = Listbox(
            list_frame,
            font=("Arial", 8),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            bg=COLOR_DARK_BG,
            fg=COLOR_TEXT_LIGHT,
            selectbackground=COLOR_SUNO_ORANGE,
            selectforeground="white",
            activestyle='none',
            bd=0,
            highlightthickness=0
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Bind
        self.listbox.bind("<Button-3>", self._on_right_click)
        
        # Boutons
        btns = tk.Frame(self, bg=COLOR_CARD_BG)
        btns.pack(fill=tk.X, pady=(3, 0))
        
        tk.Button(
            btns,
            text="📥 DL",
            font=("Arial", 8, "bold"),
            bg=COLOR_SUNO_ORANGE,
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.download_all
        ).pack(side=tk.LEFT, padx=(0, 2))
        
        tk.Button(
            btns,
            text="🗑️",
            font=("Arial", 8, "bold"),
            bg=COLOR_DANGER,
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.clear
        ).pack(side=tk.RIGHT)
    
    def add(self, clip_data: dict) -> bool:
        """Ajoute un clip"""
        clip_id = clip_data.get('clip', {}).get('id', '')
        
        # Évite doublons
        if any(c.get('clip', {}).get('id') == clip_id for c in self.download_list):
            return False
        
        self.download_list.append(clip_data)
        self.update_display()
        return True
    
    def clear(self):
        """Vide la liste"""
        if not self.download_list:
            return
        
        count = len(self.download_list)
        self.download_list.clear()
        self.update_display()
        
        if self.callbacks.get('on_clear'):
            self.callbacks['on_clear'](count)
    
    def remove(self, index: int):
        """Retire un élément"""
        if 0 <= index < len(self.download_list):
            self.download_list.pop(index)
            self.update_display()
    
    def download_all(self):
        """Télécharge tout"""
        if self.callbacks.get('on_download_all'):
            self.callbacks['on_download_all'](self.download_list)
    
    def update_display(self):
        """Met à jour l'affichage"""
        self.listbox.delete(0, tk.END)
        
        for i, clip_data in enumerate(self.download_list):
            clip = clip_data.get('clip', {})
            title = clip.get('title', 'Sans titre')
            clip_id = clip.get('id', '')[:8]
            
            display_title = f"{title[:35]} [{clip_id}]"
            self.listbox.insert(tk.END, f"{i+1}. {display_title}")
        
        self.count_label.config(text=f"⬇️ DOWNLOADS ({len(self.download_list)})")
    
    def _on_right_click(self, event):
        """Clic droit → Menu"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        clip_data = self.download_list[index]
        
        menu = Menu(self, tearoff=0)
        menu.add_command(label="📥 Télécharger", command=lambda: self.callbacks.get('on_download_one')(clip_data, index))
        menu.add_command(label="🖼️ Voir détails", command=lambda: self.callbacks.get('on_details')(clip_data))
        menu.add_separator()
        menu.add_command(label="🗑️ Retirer", command=lambda: self.remove(index))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()