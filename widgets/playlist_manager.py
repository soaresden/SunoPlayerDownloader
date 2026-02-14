"""
Gestionnaire de playlist pour le player
"""

import tkinter as tk
from tkinter import Listbox, Menu
from typing import List, Dict, Callable
from config import COLOR_CARD_BG, COLOR_DARK_BG, COLOR_SUNO_PINK, COLOR_TEXT_LIGHT, COLOR_SUNO_YELLOW


class PlaylistManager(tk.Frame):
    """Gestion de la playlist"""
    
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
        self.playlist = []
        
        self._create_ui()
    
    def _create_ui(self):
        """Crée l'interface"""
        # Header
        header = tk.Frame(self, bg=COLOR_CARD_BG)
        header.pack(fill=tk.X)
        
        self.count_label = tk.Label(
            header,
            text=f"🎵 {self.lang.get('player.playlist')} (0)",
            font=("Arial", 9, "bold"),
            bg=COLOR_CARD_BG,
            fg=COLOR_SUNO_YELLOW
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
            selectbackground=COLOR_SUNO_PINK,
            selectforeground="white",
            activestyle='none',
            bd=0,
            highlightthickness=0
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Binds
        self.listbox.bind("<Double-Button-1>", self._on_double_click)
        self.listbox.bind("<Button-3>", self._on_right_click)
        
        # Bouton vider
        tk.Button(
            self,
            text=f"🗑️ {self.lang.get('player.buttons.clear')}",
            font=("Arial", 8, "bold"),
            bg=COLOR_SUNO_PINK,
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.clear
        ).pack(fill=tk.X, pady=(3, 0))
    
    def add(self, clip_data: dict) -> bool:
        """Ajoute un clip"""
        clip_id = clip_data.get('clip', {}).get('id', '')
        
        # Évite doublons
        if any(c.get('clip', {}).get('id') == clip_id for c in self.playlist):
            return False
        
        self.playlist.append(clip_data)
        self.update_display()
        return True
    
    def clear(self):
        """Vide la playlist"""
        if not self.playlist:
            return
        
        count = len(self.playlist)
        self.playlist.clear()
        self.update_display()
        
        if self.callbacks.get('on_clear'):
            self.callbacks['on_clear'](count)
    
    def remove(self, index: int):
        """Retire un élément"""
        if 0 <= index < len(self.playlist):
            self.playlist.pop(index)
            self.update_display()
    
    def get_current(self, index: int) -> dict:
        """Récupère un clip par index"""
        if 0 <= index < len(self.playlist):
            return self.playlist[index]
        return {}
    
    def update_display(self, current_index: int = -1):
        """Met à jour l'affichage"""
        self.listbox.delete(0, tk.END)
        
        for i, clip_data in enumerate(self.playlist):
            clip = clip_data.get('clip', {})
            title = clip.get('title', self.lang.get('common.untitled'))  # ⭐ TRADUIT
            clip_id = clip.get('id', '')[:8]
            
            prefix = "▶️ " if i == current_index else f"{i+1}. "
            display_title = f"{title[:35]} [{clip_id}]"
            
            self.listbox.insert(tk.END, f"{prefix}{display_title}")
        
        if current_index >= 0:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(current_index)
            self.listbox.see(current_index)
        
        # ⭐ TRADUIT
        self.count_label.config(
            text=f"🎵 {self.lang.get('player.playlist')} ({len(self.playlist)})"
        )
    
    def _on_double_click(self, event):
        """Double-clic → Joue"""
        selection = self.listbox.curselection()
        if selection and self.callbacks.get('on_play'):
            self.callbacks['on_play'](selection[0])
    
    def _on_right_click(self, event):
        """Clic droit → Menu"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        clip_data = self.playlist[index]
        
        menu = Menu(self, tearoff=0)
        menu.add_command(label=f"▶️ {self.lang.get('player.context_menu.play')}", command=lambda: self.callbacks.get('on_play')(index))
        menu.add_command(label=f"🖼️ {self.lang.get('player.context_menu.view_details')}", command=lambda: self.callbacks.get('on_details')(clip_data))
        menu.add_separator()
        menu.add_command(label=f"🗑️ {self.lang.get('player.context_menu.remove')}", command=lambda: self.remove(index))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()