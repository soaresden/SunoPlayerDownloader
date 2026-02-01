"""
Overlay complet pour afficher les détails d'un clip
"""

import tkinter as tk
from tkinter import scrolledtext
from typing import Callable
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING
from utils.formatters import format_date


class ClipDetailsOverlay:
    """Overlay complet avec pochette, infos, paroles et checkboxes"""
    
    def __init__(self, parent, clip_data: dict, callbacks: dict):
        """
        Args:
            parent: Fenêtre parent
            clip_data: Données du clip
            callbacks: {
                'on_playlist_toggle': function(clip_id, checked),
                'on_download_toggle': function(clip_id, checked),
                'is_in_playlist': function(clip_id) -> bool,
                'is_in_download': function(clip_id) -> bool,
                'log': function(message)
            }
        """
        self.parent = parent
        self.clip_data = clip_data
        self.callbacks = callbacks
        self.window = None
        
        clip = clip_data.get('clip', {})
        self.clip_id = clip.get('id', '')
        
        self.callbacks.get('log', lambda x: None)(f"🖼️ Ouverture détails clip: {clip.get('title', 'Sans titre')[:50]}")
        
        self._create_overlay()
    
    def _create_overlay(self):
        """Crée l'overlay"""
        clip = self.clip_data.get('clip', {})
        
        # Données
        title = clip.get('title', 'Sans titre')
        artist = clip.get('display_name', 'Artiste inconnu')
        created = format_date(clip.get('created_at', ''))
        
        meta = clip.get('metadata', {})
        lyrics = meta.get('prompt', 'Aucunes paroles disponibles') if meta else 'Aucunes paroles disponibles'
        
        image_url = clip.get('image_large_url') or clip.get('image_url', '')
        
        # Fenêtre
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"🎵 {title}")
        self.window.geometry("700x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Header avec titre
        header = tk.Frame(self.window, bg=COLOR_PRIMARY, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=title,
            font=("Arial", 14, "bold"),
            bg=COLOR_PRIMARY,
            fg="white",
            wraplength=650
        ).pack(pady=10, padx=10)
        
        # Content frame
        content = tk.Frame(self.window)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Section infos (gauche)
        info_frame = tk.Frame(content)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # Pochette (placeholder si pas d'image)
        cover_frame = tk.Frame(info_frame, bg="#ecf0f1", width=200, height=200, relief=tk.SOLID, bd=1)
        cover_frame.pack()
        cover_frame.pack_propagate(False)
        
        if image_url:
            # Tenter de charger l'image
            try:
                import requests
                from PIL import Image, ImageTk
                from io import BytesIO
                
                response = requests.get(image_url, timeout=5)
                img_data = Image.open(BytesIO(response.content))
                img_data = img_data.resize((200, 200), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img_data)
                
                img_label = tk.Label(cover_frame, image=photo, bg="#ecf0f1")
                img_label.image = photo  # Garde référence
                img_label.pack(fill=tk.BOTH, expand=True)
                
                self.callbacks.get('log', lambda x: None)(f"✅ Pochette chargée")
            except Exception as e:
                self.callbacks.get('log', lambda x: None)(f"⚠️ Erreur chargement pochette: {e}")
                tk.Label(
                    cover_frame,
                    text="🎵\n\nPas de\npochette",
                    font=("Arial", 12),
                    bg="#ecf0f1",
                    fg="#7f8c8d"
                ).pack(expand=True)
        else:
            tk.Label(
                cover_frame,
                text="🎵\n\nPas de\npochette",
                font=("Arial", 12),
                bg="#ecf0f1",
                fg="#7f8c8d"
            ).pack(expand=True)
        
        # Infos textuelles
        tk.Label(
            info_frame,
            text=f"👤 {artist}",
            font=("Arial", 10),
            anchor=tk.W,
            justify=tk.LEFT
        ).pack(fill=tk.X, pady=(10, 2))
        
        tk.Label(
            info_frame,
            text=f"📅 {created}",
            font=("Arial", 9),
            fg="#7f8c8d",
            anchor=tk.W
        ).pack(fill=tk.X, pady=2)
        
        # Checkboxes
        checkbox_frame = tk.Frame(info_frame)
        checkbox_frame.pack(fill=tk.X, pady=(15, 0))
        
        # État initial
        is_playlist = self.callbacks.get('is_in_playlist', lambda x: False)(self.clip_id)
        is_download = self.callbacks.get('is_in_download', lambda x: False)(self.clip_id)
        
        self.playlist_var = tk.BooleanVar(value=is_playlist)
        self.download_var = tk.BooleanVar(value=is_download)
        
        tk.Checkbutton(
            checkbox_frame,
            text="🎵 Ajouter à la playlist",
            variable=self.playlist_var,
            font=("Arial", 9),
            command=self._on_playlist_toggle
        ).pack(anchor=tk.W, pady=2)
        
        tk.Checkbutton(
            checkbox_frame,
            text="⬇️ Marquer pour DL",
            variable=self.download_var,
            font=("Arial", 9),
            command=self._on_download_toggle
        ).pack(anchor=tk.W, pady=2)
        
        # Section paroles (droite)
        lyrics_frame = tk.Frame(content)
        lyrics_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            lyrics_frame,
            text="📝 PAROLES",
            font=("Arial", 10, "bold"),
            anchor=tk.W
        ).pack(fill=tk.X, pady=(0, 5))
        
        lyrics_text = scrolledtext.ScrolledText(
            lyrics_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            padx=10,
            pady=10
        )
        lyrics_text.pack(fill=tk.BOTH, expand=True)
        lyrics_text.insert("1.0", lyrics)
        lyrics_text.config(state=tk.DISABLED)
        
        # Bouton fermer
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Button(
            btn_frame,
            text="FERMER",
            font=("Arial", 10, "bold"),
            bg=COLOR_PRIMARY,
            fg="white",
            command=self.close,
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)
        
        # Center
        self.window.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 700) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 600) // 2
        self.window.geometry(f"+{x}+{y}")
    
    def _on_playlist_toggle(self):
        """Toggle playlist"""
        checked = self.playlist_var.get()
        self.callbacks.get('log', lambda x: None)(f"{'✅' if checked else '❌'} Playlist toggle: {self.clip_id[:8]}")
        
        callback = self.callbacks.get('on_playlist_toggle')
        if callback:
            callback(self.clip_id, checked)
    
    def _on_download_toggle(self):
        """Toggle download"""
        checked = self.download_var.get()
        self.callbacks.get('log', lambda x: None)(f"{'✅' if checked else '❌'} Download toggle: {self.clip_id[:8]}")
        
        callback = self.callbacks.get('on_download_toggle')
        if callback:
            callback(self.clip_id, checked)
    
    def close(self):
        """Ferme l'overlay"""
        self.callbacks.get('log', lambda x: None)(f"❌ Fermeture détails clip")
        if self.window:
            self.window.destroy()
            self.window = None


def show_clip_details(parent, clip_data: dict, callbacks: dict):
    """
    Affiche l'overlay de détails d'un clip
    
    Args:
        parent: Fenêtre parent
        clip_data: Données du clip
        callbacks: Callbacks pour interactions
    """
    ClipDetailsOverlay(parent, clip_data, callbacks)