"""
Panel d'affichage des clips avec checkboxes, clic droit et actions
"""

import tkinter as tk
from tkinter import ttk, messagebox, Menu
from typing import List, Dict, Callable, Set
from config import *
from utils.formatters import format_date, format_duration
from widgets.lyrics_overlay import show_clip_details
from utils.treeview_sorter import make_treeview_sortable


class ClipsPanel(tk.Frame):
    """Panel contenant la liste des clips"""
    
    def __init__(self, parent, callbacks: dict, lang_manager):
        """
        Args:
            parent: Widget parent
            callbacks: Dict des callbacks
            lang_manager: Gestionnaire de langues
        """
        super().__init__(parent, bg=COLOR_PRIMARY)
        self.callbacks = callbacks
        self.clips = []
        self.download_checked: Set[str] = set()
        self.lang = lang_manager
        
        # Header
        self._create_header()
        
        # Boutons
        self._create_buttons()
        
        # TreeView
        self._create_treeview()
    
    def log(self, message: str):
        """Log helper"""
        if self.callbacks.get('log'):
            self.callbacks['log'](message)
    
    def _create_header(self):
        """Crée le header"""
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        self.title_label = tk.Label(
            header,
            text=self.lang.get('clips.title'),
            font=("Arial", 10, "bold"),
            bg=COLOR_PRIMARY,
            fg="white"
        )
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        self.count_label = tk.Label(
            header,
            text="",
            font=("Arial", 8),
            bg=COLOR_PRIMARY,
            fg="#bdc3c7"
        )
        self.count_label.pack(side=tk.RIGHT, padx=5)
    
    def _create_buttons(self):
        """Crée les boutons d'action"""
        btns = tk.Frame(self, bg=COLOR_PRIMARY, height=30)
        btns.pack(fill=tk.X)
        btns.pack_propagate(False)
        
        self.btn_download_all = tk.Button(
            btns,
            text=f"⬇️ {self.lang.get('clips.buttons.download_all')}",
            font=("Arial", 8, "bold"),
            bg=COLOR_DANGER,
            fg="white",
            relief=tk.FLAT,
            padx=8,
            pady=4,
            command=self.callbacks.get('download_all')
        )
        self.btn_download_all.pack(side=tk.LEFT, padx=3, pady=3)
        
        self.btn_download_checked = tk.Button(
            btns,
            text=f"⬇️ {self.lang.get('clips.buttons.download_checked')}",
            font=("Arial", 8, "bold"),
            bg=COLOR_WARNING,
            fg="white",
            relief=tk.FLAT,
            padx=8,
            pady=4,
            command=self._download_checked
        )
        self.btn_download_checked.pack(side=tk.LEFT, padx=3, pady=3)
    
    def _create_treeview(self):
        """Crée le TreeView"""
        clips_cont = tk.Frame(self, bg="white", bd=1, relief=tk.SOLID)
        clips_cont.pack(fill=tk.BOTH, expand=True, padx=3, pady=(0, 3))
        
        clips_vsb = ttk.Scrollbar(clips_cont)
        clips_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(
            clips_cont,
            columns=("pin", "created", "title", "style", "dur", "dl"),
            show="headings",
            yscrollcommand=clips_vsb.set,
            selectmode="extended",
            height=18
        )
        clips_vsb.config(command=self.tree.yview)
        
        # Colonnes
        self.tree.heading("pin", text=self.lang.get('clips.columns.pin'))
        self.tree.heading("created", text=self.lang.get('clips.columns.created'))
        self.tree.heading("title", text=self.lang.get('clips.columns.title'))
        self.tree.heading("style", text=self.lang.get('clips.columns.style'))
        self.tree.heading("dur", text=self.lang.get('clips.columns.duration'))
        self.tree.heading("dl", text=self.lang.get('clips.columns.download'))
        
        self.tree.column("pin", width=30, anchor=tk.CENTER)
        self.tree.column("created", width=90)
        self.tree.column("title", width=320)
        self.tree.column("style", width=220)
        self.tree.column("dur", width=60, anchor=tk.CENTER)
        self.tree.column("dl", width=35, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self._setup_sorting()

        
         # ⭐ NOUVEAUX BINDS
        self.tree.bind("<Double-Button-1>", self._on_double_click_add_playlist)  # Double-clic → Playlist
        self.tree.bind("<Button-1>", self._on_click)  # Clic simple → Checkboxes
        self.tree.bind("<Button-3>", self._on_right_click_show_details)  # Clic droit → Détails

    def _setup_sorting(self):
        """Active le tri"""
        self.sorter = make_treeview_sortable(self.tree, {
            'pin': {'type': 'text', 'reverse': True},
            'created': {'type': 'date', 'reverse': True},
            'title': {'type': 'text', 'reverse': False},
            'style': {'type': 'text', 'reverse': False},
            'dur': {'type': 'text', 'reverse': True}
        })
        
    def load_clips(self, project_name: str, clips: List[Dict]):
        """Charge les clips"""
        self.log(f"📥 Chargement de {len(clips)} clips pour projet: {project_name}")
        
        self.clips = clips
        self.title_label.config(text=f"🎵 {project_name[:40]}")
        
        # Reset checkboxes
        self.download_checked.clear()
        
        # Efface
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajoute
        for clip_wrapper in clips:
            clip = clip_wrapper.get('clip', {})
            
            cid = clip.get('id', '')
            title = clip.get('title', 'Sans titre')
            created = format_date(clip.get('created_at', ''))
            
            # ⭐ Ajoute l'ID court pour différencier les clips avec le même titre
            title_with_id = f"{title} [{cid[:8]}]"
            
            meta = clip.get('metadata', {})
            tags = meta.get('tags', '') if meta else ''
            dur = meta.get('duration', 0) if meta else 0
            
            pin = "📌" if clip_wrapper.get('is_pinned', False) else ""
            dur_str = format_duration(dur)
            
            self.tree.insert("", tk.END, iid=cid,
                           values=(pin, created, title_with_id, tags, dur_str, ""))
        
        self.count_label.config(text=str(len(clips)))
        self.log(f"✅ {len(clips)} clips affichés dans le TreeView")
        
    
    
    def _on_click(self, event):
        """Gère les clics sur checkboxes"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        if not item:
            return
        
        # Colonne 6 = Download checkbox
        if column == "#6":
            # Trouve le clip complet
            clip_data = self._find_clip(item)
            if not clip_data:
                return
            
            if item in self.download_checked:
                # ❌ DÉCOCHE
                self.download_checked.remove(item)
                self.log(f"❌ Retiré de DL: {item[:8]}")
            else:
                # ✅ COCHE
                self.download_checked.add(item)
                self.log(f"✅ Ajouté à DL: {item[:8]}")
                
                # ⭐ AJOUTE À LA LISTBOX DOWNLOADS
                callback = self.callbacks.get('add_to_download')
                if callback:
                    callback(clip_data)
            
            self._update_checkboxes()
        
    def _update_checkboxes(self):
        """Met à jour l'affichage des checkboxes"""
        for item in self.tree.get_children():
            values = list(self.tree.item(item)['values'])
            values[5] = "✓" if item in self.download_checked else ""
            self.tree.item(item, values=values)
    
    def _on_double_click(self, event):
        """Affiche les détails au double-clic"""
        item = self.tree.selection()
        if not item:
            return
        
        clip_id = item[0]
        clip_data = self._find_clip(clip_id)
        if not clip_data:
            return
        
        self.log(f"🖼️ Double-clic sur clip: {clip_data.get('clip', {}).get('title', 'Sans titre')[:50]}")
        
        show_clip_details(self, clip_data, {
            'on_playlist_toggle': self._on_overlay_playlist_toggle,
            'on_download_toggle': self._on_overlay_download_toggle,
            'is_in_playlist': lambda cid: False,
            'is_in_download': lambda cid: cid in self.download_checked,
            'log': self.log
        }, self.lang)
    
    def _on_right_click(self, event):
        """Menu contextuel clic droit"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        clip_data = self._find_clip(item)
        if not clip_data:
            return
        
        clip = clip_data.get('clip', {})
        title = clip.get('title', 'Sans titre')[:40]
        
        self.log(f"🖱️ Clic droit sur: {title}")
        
        menu = Menu(self, tearoff=0)
        menu.add_command(
            label=f"🎵 {self.lang.get('clips.context_menu.add_to_playlist')}",
            command=lambda: self._add_to_playlist_from_menu(clip_data)
        )
        menu.add_command(
            label=f"⬇️ {self.lang.get('clips.context_menu.add_to_download')}",
            command=lambda: self._add_to_download_from_menu(clip_data)
        )
        menu.add_separator()
        menu.add_command(
            label=f"🖼️ {self.lang.get('clips.context_menu.view_details')}",
            command=lambda: self._on_double_click(event)
        )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_double_click_add_playlist(self, event):
        """Double-clic → Ajoute à la playlist"""
        item = self.tree.selection()
        if not item:
            return
        
        clip_id = item[0]
        clip_data = self._find_clip(clip_id)
        if not clip_data:
            return
        
        clip = clip_data.get('clip', {})
        title = clip.get('title', 'Sans titre')
        
        self.log(f"🖱️ Double-clic → Ajout playlist: {title[:50]}")
        
        callback = self.callbacks.get('add_to_playlist')
        if callback:
            callback(clip_data)

    def _on_right_click_show_details(self, event):
        """Clic droit → Affiche détails + menu"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self.tree.selection_set(item)
        clip_data = self._find_clip(item)
        if not clip_data:
            return
        
        clip = clip_data.get('clip', {})
        title = clip.get('title', 'Sans titre')[:40]
        
        self.log(f"🖱️ Clic droit sur: {title}")
        
        # Menu contextuel
        menu = Menu(self, tearoff=0)
        menu.add_command(
            label=f"🖼️ {self.lang.get('clips.context_menu.view_details')}",
            command=lambda: self._show_details(clip_data)
        )
        menu.add_separator()
        menu.add_command(
            label=f"🎵 {self.lang.get('clips.context_menu.add_to_playlist')}",
            command=lambda: self._add_to_playlist_from_menu(clip_data)
        )
        menu.add_command(
            label=f"⬇️ {self.lang.get('clips.context_menu.add_to_download')}",
            command=lambda: self._add_to_download_from_menu(clip_data)
        )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _show_details(self, clip_data: dict):
        """Affiche l'overlay de détails"""
        show_clip_details(self, clip_data, {
            'on_playlist_toggle': self._on_overlay_playlist_toggle,
            'on_download_toggle': self._on_overlay_download_toggle,
            'is_in_playlist': lambda cid: False,
            'is_in_download': lambda cid: cid in self.download_checked,
            'log': self.log
        }, self.lang)
        
        
    def _add_to_playlist_from_menu(self, clip_data: dict):
        """Ajoute à la playlist via menu contextuel"""
        clip = clip_data.get('clip', {})
        title = clip.get('title', 'Sans titre')
        
        self.log(f"➕ Menu: Ajout à playlist → {title[:50]}")
        
        callback = self.callbacks.get('add_to_playlist')
        if callback:
            callback(clip_data)
    
    def _add_to_download_from_menu(self, clip_data: dict):
        """Ajoute aux DL via menu contextuel"""
        clip = clip_data.get('clip', {})
        clip_id = clip.get('id', '')
        title = clip.get('title', 'Sans titre')
        
        self.log(f"➕ Menu: Ajout à DL → {title[:50]}")
        
        if clip_id not in self.download_checked:
            self.download_checked.add(clip_id)
            self._update_checkboxes()
            
            callback = self.callbacks.get('add_to_download')
            if callback:
                callback(clip_data)
    
    def _on_overlay_playlist_toggle(self, clip_id: str, checked: bool):
        """Callback overlay pour playlist"""
        clip_data = self._find_clip(clip_id)
        if not clip_data:
            return
        
        if checked:
            callback = self.callbacks.get('add_to_playlist')
            if callback:
                callback(clip_data)
    
    def _on_overlay_download_toggle(self, clip_id: str, checked: bool):
        """Callback overlay pour download"""
        if checked:
            self.download_checked.add(clip_id)
        else:
            self.download_checked.discard(clip_id)
        self._update_checkboxes()
    
    def _find_clip(self, clip_id: str) -> dict:
        """Trouve un clip par ID"""
        for cd in self.clips:
            if cd.get('clip', {}).get('id') == clip_id:
                return cd
        return None
    
    def _download_checked(self):
        """Télécharge les clips cochés"""
        if not self.download_checked:
            self.log("⚠️ Aucune piste cochée pour DL")
            messagebox.showinfo("Info", self.lang.get('messages.no_tracks_download'))
            return
        
        self.log(f"📥 Demande DL de {len(self.download_checked)} clip(s)")
        
        clips_to_download = []
        for clip_id in self.download_checked:
            for cd in self.clips:
                if cd.get('clip', {}).get('id') == clip_id:
                    clips_to_download.append(cd)
                    break
        
        if self.callbacks.get('download_checked'):
            self.callbacks['download_checked'](clips_to_download)
    
    def update_texts(self):
        """Met à jour les textes après changement de langue"""
        self.title_label.config(text=self.lang.get('clips.title'))
        
        # Boutons
        self.btn_download_all.config(text=f"⬇️ {self.lang.get('clips.buttons.download_all')}")
        self.btn_download_checked.config(text=f"⬇️ {self.lang.get('clips.buttons.download_checked')}")
        
        # Headers TreeView
        self.tree.heading("pin", text=self.lang.get('clips.columns.pin'))
        self.tree.heading("created", text=self.lang.get('clips.columns.created'))
        self.tree.heading("title", text=self.lang.get('clips.columns.title'))
        self.tree.heading("style", text=self.lang.get('clips.columns.style'))
        self.tree.heading("dur", text=self.lang.get('clips.columns.duration'))
        self.tree.heading("dl", text=self.lang.get('clips.columns.download'))