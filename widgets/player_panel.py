"""
Panel player - VERSION ULTRA REFACTORISÉE
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable
from config import *
from utils.audio_cache import AudioCache
from widgets.audio_player import AudioPlayer
from widgets.player_controls import PlayerControls
from widgets.playlist_manager import PlaylistManager
from widgets.download_manager import DownloadManager


class PlayerPanel(tk.Frame):
    """Panel player orchestrateur"""
    
    def __init__(self, parent, log_callback: Callable, lang_manager):
        """
        Args:
            parent: Widget parent
            log_callback: Fonction de log
            lang_manager: Gestionnaire de langues
        """
        super().__init__(parent, bg=COLOR_CARD_BG)
        
        self.log = log_callback or (lambda x: print(x))
        self.lang = lang_manager
        self.current_index = -1
        self.current_workspace = ""
        self.current_duration = 0
        
        # Cache audio
        self.audio_cache = AudioCache(log_callback=self.log)
        
        # Audio player
        self.audio_player = AudioPlayer(log_callback=self.log)
        self.audio_player.on_track_end = self.next
        self.audio_player.on_progress_update = self._on_progress_update
        
        # Créer l'interface
        self._create_ui()
        
        self.log("🎵 Panel player initialisé")
    
    def _create_ui(self):
        """Crée l'interface"""
        
        # Header
        header = tk.Frame(self, bg=COLOR_SUNO_PINK, height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=self.lang.get('player.title'),
            font=("Arial", 13, "bold"),
            bg=COLOR_SUNO_PINK,
            fg="white"
        ).pack(pady=10)
        
        # Zone player avec contrôles
        player_zone = tk.Frame(self, bg=COLOR_CARD_BG)
        player_zone.pack(fill=tk.X, padx=8, pady=8)
        
        self.controls = PlayerControls(player_zone, {
            'on_toggle_play_pause': self.toggle_play_pause,
            'on_stop': self.stop,
            'on_previous': self.previous,
            'on_next': self.next
        }, self.lang)
        self.controls.pack(fill=tk.BOTH, expand=True)
        
        # Séparateur
        tk.Frame(self, bg=COLOR_BORDER, height=2).pack(fill=tk.X, padx=8, pady=8)
        
        # ZONE 2 COLONNES
        lists_container = tk.Frame(self, bg=COLOR_CARD_BG)
        lists_container.pack(fill=tk.BOTH, expand=True, padx=8)
        
        # Playlist
        playlist_col = tk.Frame(lists_container, bg=COLOR_CARD_BG)
        playlist_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        
        self.playlist_manager = PlaylistManager(playlist_col, {
            'on_play': self._play_from_index,
            'on_details': self._show_details,
            'on_clear': self._on_playlist_cleared
        }, self.lang)
        self.playlist_manager.pack(fill=tk.BOTH, expand=True)
        
        # Downloads
        download_col = tk.Frame(lists_container, bg=COLOR_CARD_BG)
        download_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))
        
        self.download_manager = DownloadManager(download_col, {
            'on_download_all': self._download_all,
            'on_download_one': self._download_one,
            'on_details': self._show_details,
            'on_clear': self._on_downloads_cleared
        }, self.lang)
        self.download_manager.pack(fill=tk.BOTH, expand=True)
        
        # Bouton cache
        tk.Button(
            self,
            text=f"🗂️ {self.lang.get('player.buttons.cache')}",
            font=("Arial", 8, "bold"),
            bg=COLOR_SECONDARY,
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.audio_cache.clear_temp_cache
        ).pack(fill=tk.X, padx=8, pady=(5, 8))
    
    def set_workspace(self, workspace_name: str):
        """Définit le workspace actuel"""
        self.current_workspace = workspace_name
        self.log(f"📁 Workspace actif: {workspace_name}")
    
    def add_to_playlist(self, clip_data: dict):
        """Ajoute un clip à la playlist"""
        if self.playlist_manager.add(clip_data):
            clip = clip_data.get('clip', {})
            self.log(f"➕ Ajouté à la playlist: {clip.get('title', '')[:50]}")
            
            if len(self.playlist_manager.playlist) == 1:
                self.current_index = 0
                self._load_current()
    
    def add_to_downloads(self, clip_data: dict):
        """Ajoute un clip aux téléchargements"""
        if self.download_manager.add(clip_data):
            clip = clip_data.get('clip', {})
            self.log(f"⬇️ Ajouté à downloads: {clip.get('title', '')[:50]}")
    
    def toggle_play_pause(self):
        """Bascule play/pause"""
        if self.audio_player.is_playing and not self.audio_player.is_paused:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """Démarre la lecture"""
        if not self.playlist_manager.playlist:
            messagebox.showinfo("Info", self.lang.get('messages.add_tracks_to_playlist'))
            return
        
        if self.audio_player.play():
            self.controls.set_play_pause_state(True)
    
    def pause(self):
        """Pause"""
        self.audio_player.pause()
        self.controls.set_play_pause_state(False)
    
    def stop(self):
        """Stop"""
        self.audio_player.stop()
        self.controls.set_play_pause_state(False)
        self.controls.set_duration(self.current_duration)
    
    def previous(self):
        """Piste précédente"""
        if not self.playlist_manager.playlist:
            return
        
        was_playing = self.audio_player.is_playing
        self.stop()
        
        self.current_index = (self.current_index - 1) % len(self.playlist_manager.playlist)
        self._load_current()
        self.log(f"⏮ Piste {self.current_index + 1}/{len(self.playlist_manager.playlist)}")
        
        if was_playing:
            self.play()
    
    def next(self):
        """Piste suivante"""
        if not self.playlist_manager.playlist:
            return
        
        was_playing = self.audio_player.is_playing
        self.stop()
        
        self.current_index = (self.current_index + 1) % len(self.playlist_manager.playlist)
        self._load_current()
        self.log(f"⏭ Piste {self.current_index + 1}/{len(self.playlist_manager.playlist)}")
        
        if was_playing:
            self.play()
    
    def _load_current(self):
        """Charge la piste actuelle"""
        if not self.playlist_manager.playlist or self.current_index < 0:
            self.controls.reset()
            return
        
        clip_data = self.playlist_manager.get_current(self.current_index)
        clip = clip_data.get('clip', {})
        meta = clip.get('metadata', {})
        
        title = clip.get('title', 'Sans titre')
        artist = clip.get('display_name', '')
        self.current_duration = meta.get('duration', 0) if meta else 0
        
        self.controls.set_track_info(title, artist)
        self.controls.set_duration(self.current_duration)
        self.playlist_manager.update_display(self.current_index)
        
        self.log(f"🎵 Chargé: {title[:50]}")
        
        # Charge l'audio
        audio_path = self.audio_cache.get_audio_path(
            clip_data, 
            self.current_workspace, 
            permanent=False,
            track_number=self.current_index + 1
        )
        
        if audio_path:
            self.audio_player.load(audio_path)
    
    def _on_progress_update(self, position: float):
        """Callback mise à jour progression"""
        self.controls.update_progress(position, self.current_duration)
    
    def _play_from_index(self, index: int):
        """Joue depuis un index"""
        self.stop()
        self.current_index = index
        self._load_current()
        self.play()
    
    def _on_playlist_cleared(self, count: int):
        """Playlist vidée"""
        self.stop()
        self.current_index = -1
        self.controls.reset()
        self.log(f"🗑️ Playlist vidée ({count} piste(s))")
    
    def _on_downloads_cleared(self, count: int):
        """Downloads vidée"""
        self.log(f"🗑️ Downloads vidée ({count} piste(s))")
    
    def _show_details(self, clip_data: dict):
        """Affiche les détails"""
        from widgets.lyrics_overlay import show_clip_details
        
        show_clip_details(self, clip_data, {
            'on_playlist_toggle': lambda cid, checked: None,
            'on_download_toggle': lambda cid, checked: None,
            'is_in_playlist': lambda cid: any(c.get('clip', {}).get('id') == cid for c in self.playlist_manager.playlist),
            'is_in_download': lambda cid: any(c.get('clip', {}).get('id') == cid for c in self.download_manager.download_list),
            'log': self.log
        })
    
    def _download_all(self, clips: list):
        """Télécharge tous"""
        if not clips:
            return
        
        self.stop()
        self.audio_player.unload()
        
        self.log(f"📥 Téléchargement de {len(clips)} clip(s)")
        
        sorted_clips = sorted(clips, key=lambda c: c.get('clip', {}).get('created_at', ''))
        
        success = 0
        for i, clip_data in enumerate(sorted_clips, 1):
            filepath = self.audio_cache.get_audio_path(clip_data, self.current_workspace, permanent=True, track_number=i)
            if filepath:
                success += 1
                clip = clip_data.get('clip', {})
                self.audio_cache.delete_temp_file(clip.get('id', ''), clip.get('title', ''))
        
        self.log(f"✅ {success}/{len(clips)} téléchargé(s)")
        messagebox.showinfo("Terminé", f"✅ {success} fichier(s) téléchargé(s)")
    
    def _download_one(self, clip_data: dict, index: int):
        """Télécharge un clip"""
        clip = clip_data.get('clip', {})
        self.log(f"📥 Téléchargement: {clip.get('title', '')[:50]}")
        
        sorted_clips = sorted(self.download_manager.download_list, key=lambda c: c.get('clip', {}).get('created_at', ''))
        track_num = sorted_clips.index(clip_data) + 1 if clip_data in sorted_clips else 1
        
        filepath = self.audio_cache.get_audio_path(clip_data, self.current_workspace, permanent=True, track_number=track_num)
        
        if filepath:
            self.log(f"✅ Téléchargé")
            self.audio_cache.delete_temp_file(clip.get('id', ''), clip.get('title', ''))
    
    def update_texts(self):
        """Met à jour les textes"""
        pass