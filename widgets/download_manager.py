"""
Gestionnaire de liste de téléchargement
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Callable


class DownloadManager(tk.Frame):
    """Widget de gestion de la liste de téléchargement"""
    
    def __init__(self, parent, callbacks: dict, lang_manager):
        """
        Args:
            parent: Widget parent
            callbacks: Dict des callbacks :
                - on_clear: () -> None
                - on_download_all: (download_list: List[Dict]) -> None
            lang_manager: Gestionnaire de langues
        """
        super().__init__(parent, bg="#2c3e50")
        self.callbacks = callbacks or {}
        self.lang = lang_manager
        self.download_list: List[Dict] = []
        
        self._create_ui()
    
    # -------------------------------------------------------------------------
    # UI
    # -------------------------------------------------------------------------
    def _create_ui(self):
        """Crée l'interface"""
        # Header
        header = tk.Frame(self, bg="#2c3e50", height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        self.title_label = tk.Label(
            header,
            text="📥 À télécharger (0)",
            font=("Arial", 10, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        # Bouton Clear
        clear_btn = tk.Button(
            header,
            text="🗑️",
            font=("Arial", 8),
            bg="#e74c3c",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=5,
            pady=2,
            command=self._clear_all
        )
        clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # Liste
        list_frame = tk.Frame(self, bg="white", bd=1, relief=tk.SOLID)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            list_frame,
            font=("Arial", 9),
            bg="white",
            fg="#2c3e50",
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            activestyle='none'
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Bind double-click pour supprimer
        self.listbox.bind("<Double-Button-1>", self._on_double_click)
        
        # Boutons d'action
        actions = tk.Frame(self, bg="#2c3e50", height=35)
        actions.pack(fill=tk.X, padx=5, pady=(0, 5))
        actions.pack_propagate(False)
        
        tk.Button(
            actions,
            text="📥 Télécharger",
            font=("Arial", 9, "bold"),
            bg="#27ae60",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=5,
            command=self._download_all
        ).pack(fill=tk.BOTH, expand=True)
    
    # -------------------------------------------------------------------------
    # Gestion de la liste
    # -------------------------------------------------------------------------
    def add(self, clip_data: Dict) -> bool:
        """
        Ajoute un clip à la liste de téléchargement
        
        Args:
            clip_data: Données du clip (incluant éventuellement '_workspace_name')
        
        Returns:
            True si ajouté, False si déjà présent
        """
        clip = clip_data.get('clip', {})
        clip_id = clip.get('id', '')
        title = clip.get('title', 'Sans titre')
        
        if not clip_id:
            return False
        
        # Vérifie si déjà dans la liste (par ID de clip)
        for item in self.download_list:
            existing_id = item.get('clip', {}).get('id')
            if existing_id == clip_id:
                return False
        
        # Ajoute
        self.download_list.append(clip_data)
        
        # Affiche dans la listbox
        id_short = clip_id[:8]
        workspace = clip_data.get('_workspace_name', '')
        if workspace:
            display_text = f"{title} [{id_short}] — {workspace}"
        else:
            display_text = f"{title} [{id_short}]"
        
        self.listbox.insert(tk.END, display_text)
        
        # Met à jour le compteur
        self._update_count()
        
        return True
    
    def remove(self, index: int):
        """Supprime un clip de la liste"""
        if 0 <= index < len(self.download_list):
            self.download_list.pop(index)
            self.listbox.delete(index)
            self._update_count()
    
    def clear(self):
        """Vide la liste"""
        self.download_list.clear()
        self.listbox.delete(0, tk.END)
        self._update_count()
    
    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _update_count(self):
        """Met à jour le compteur"""
        count = len(self.download_list)
        # Si tu as des clés de langue, tu peux les utiliser ici
        # ex: self.lang.get('download_list.title', count=count)
        self.title_label.config(text=f"📥 À télécharger ({count})")
    
    def _clear_all(self):
        """Vide toute la liste (avec confirmation)"""
        if not self.download_list:
            return
        
        result = messagebox.askyesno(
            "Vider la liste",
            f"Supprimer {len(self.download_list)} clip(s) de la liste ?"
        )
        
        if result:
            self.clear()
            
            # Callback
            on_clear: Callable = self.callbacks.get('on_clear')
            if callable(on_clear):
                on_clear()
    
    def _download_all(self):
        """Lance le téléchargement de tous les clips"""
        if not self.download_list:
            messagebox.showinfo("Info", "Aucun clip dans la liste de téléchargement")
            return
        
        on_download_all: Callable = self.callbacks.get('on_download_all')
        if callable(on_download_all):
            on_download_all(self.download_list)
    
    def _on_double_click(self, event):
        """Supprime le clip double-cliqué"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.remove(index)
    
    # -------------------------------------------------------------------------
    # Internationalisation
    # -------------------------------------------------------------------------
    def update_texts(self):
        """Met à jour les textes (pour changement de langue)"""
        # Ici tu peux brancher ton lang_manager si tu as des clés
        # Exemple :
        # title = self.lang.get('download_list.title', count=len(self.download_list))
        # self.title_label.config(text=title)
        self._update_count()
