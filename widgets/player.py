"""
Widget Player audio pour Suno avec gestion de playlist
"""

import tkinter as tk
from typing import List, Dict
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER


class PlayerOverlay:
    """Overlay de player audio avec playlist"""
    
    def __init__(self, parent, log_callback=None):
        """
        Args:
            parent: Fenêtre parent
            log_callback: Fonction de log
        """
        self.parent = parent
        self.log = log_callback or (lambda x: print(x))
        self.window = None
        self.current_clip = None
        self.is_playing = False
        self.playlist = []
        self.current_index = 0
        
        self.info_label = None
        self.slider = None
        self.timer_label = None
        self.playlist_label = None
    
    def show(self):
        """Affiche le player"""
        self.log("🎵 Ouverture du player")
        
        if self.window:
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("🎵 Player")
        self.window.geometry("500x250")
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        
        # Header
        header = tk.Label(
            self.window,
            text="🎵 SUNO PLAYER",
            font=("Arial", 16, "bold"),
            bg=COLOR_PRIMARY,
            fg="white",
            padx=10,
            pady=15
        )
        header.pack(fill=tk.X)
        
        # Info playlist
        self.playlist_label = tk.Label(
            self.window,
            text="Aucune playlist chargée",
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        self.playlist_label.pack(pady=(5, 0))
        
        # Info piste
        self.info_label = tk.Label(
            self.window,
            text="Aucune piste",
            font=("Arial", 11)
        )
        self.info_label.pack(pady=10)
        
        # Slider
        self.slider = tk.Scale(
            self.window,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            length=400,
            showvalue=False
        )
        self.slider.pack(pady=10)
        
        # Timer
        self.timer_label = tk.Label(
            self.window,
            text="0:00 / 0:00",
            font=("Arial", 9)
        )
        self.timer_label.pack()
        
        # Boutons
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        tk.Button(
            btn_frame,
            text="⏮",
            font=("Arial", 14, "bold"),
            bg="#95a5a6",
            fg="white",
            padx=12,
            pady=5,
            command=self.previous
        ).pack(side=tk.LEFT, padx=3)
        
        tk.Button(
            btn_frame,
            text="▶️",
            font=("Arial", 14, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            padx=15,
            pady=5,
            command=self.play
        ).pack(side=tk.LEFT, padx=3)
        
        tk.Button(
            btn_frame,
            text="⏸",
            font=("Arial", 14, "bold"),
            bg=COLOR_WARNING,
            fg="white",
            padx=15,
            pady=5,
            command=self.pause
        ).pack(side=tk.LEFT, padx=3)
        
        tk.Button(
            btn_frame,
            text="⏹",
            font=("Arial", 14, "bold"),
            bg=COLOR_DANGER,
            fg="white",
            padx=15,
            pady=5,
            command=self.stop
        ).pack(side=tk.LEFT, padx=3)
        
        tk.Button(
            btn_frame,
            text="⏭",
            font=("Arial", 14, "bold"),
            bg="#95a5a6",
            fg="white",
            padx=12,
            pady=5,
            command=self.next
        ).pack(side=tk.LEFT, padx=3)
        
        # Center
        self.window.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 500) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 250) // 2
        self.window.geometry(f"+{x}+{y}")
        
        # Update display
        self._update_display()
    
    def load_playlist(self, clips: List[Dict]):
        """
        Charge une playlist
        
        Args:
            clips: Liste des clips à jouer
        """
        self.playlist = clips
        self.current_index = 0
        
        self.log(f"📋 Playlist chargée: {len(clips)} piste(s)")
        
        if clips:
            self.load_clip(clips[0])
        
        self._update_display()
    
    def load_clip(self, clip_data: dict):
        """
        Charge un clip dans le player
        
        Args:
            clip_data: Données du clip
        """
        self.current_clip = clip_data
        clip = clip_data.get('clip', {})
        title = clip.get('title', 'Sans titre')
        
        self.log(f"🎵 Clip chargé: {title}")
        
        self._update_display()
    
    def _update_display(self):
        """Met à jour l'affichage"""
        if not self.window:
            return
        
        # Info playlist
        if self.playlist:
            self.playlist_label.config(
                text=f"Playlist: {self.current_index + 1}/{len(self.playlist)}"
            )
        else:
            self.playlist_label.config(text="Aucune playlist chargée")
        
        # Info piste
        if self.current_clip:
            clip = self.current_clip.get('clip', {})
            title = clip.get('title', 'Sans titre')
            artist = clip.get('display_name', '')
            
            display_text = title
            if artist:
                display_text = f"{title} - {artist}"
            
            self.info_label.config(text=display_text[:60])
        else:
            self.info_label.config(text="Aucune piste")
    
    def play(self):
        """Démarre la lecture"""
        self.is_playing = True
        self.log("▶️ Play")
        # TODO: Implémenter lecture audio
    
    def pause(self):
        """Met en pause"""
        self.is_playing = False
        self.log("⏸ Pause")
        # TODO: Implémenter pause
    
    def stop(self):
        """Arrête la lecture"""
        self.is_playing = False
        if self.slider:
            self.slider.set(0)
        if self.timer_label:
            self.timer_label.config(text="0:00 / 0:00")
        self.log("⏹ Stop")
        # TODO: Implémenter stop
    
    def previous(self):
        """Piste précédente"""
        if not self.playlist:
            self.log("⚠️ Aucune playlist")
            return
        
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.load_clip(self.playlist[self.current_index])
        self.log(f"⏮ Piste précédente: {self.current_index + 1}/{len(self.playlist)}")
    
    def next(self):
        """Piste suivante"""
        if not self.playlist:
            self.log("⚠️ Aucune playlist")
            return
        
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.load_clip(self.playlist[self.current_index])
        self.log(f"⏭ Piste suivante: {self.current_index + 1}/{len(self.playlist)}")
    
    def close(self):
        """Ferme le player"""
        self.log("❌ Fermeture du player")
        self.stop()
        if self.window:
            self.window.destroy()
            self.window = None