"""
Logique de lecture audio avec VLC - VERSION OPTIMALE POUR LA MUSIQUE
"""

import vlc
import threading
import time
from typing import Callable, Optional
from pathlib import Path


class AudioPlayer:
    """Gestion de la lecture audio avec VLC"""
    
    def __init__(self, log_callback: Callable):
        """
        Args:
            log_callback: Fonction de log
        """
        self.log = log_callback
        self.is_playing = False
        self.is_paused = False
        self.should_update = False
        self.update_thread = None
        self.on_track_end = None  # Callback quand piste terminée
        self.on_progress_update = None  # Callback mise à jour progression
        self.current_file = None
        
        # Init VLC
        try:
            self.instance = vlc.Instance('--no-xlib')  # Pour éviter les warnings
            self.player = self.instance.media_player_new()
            
            # Event pour détecter fin de piste
            self.event_manager = self.player.event_manager()
            self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)
            
            self.log("🎵 VLC player initialisé")
        except Exception as e:
            self.log(f"⚠️ Erreur init VLC: {e}")
    
    def load(self, filepath: str) -> bool:
        """Charge un fichier audio"""
        try:
            self.log(f"📂 Chargement: {Path(filepath).name}")
            
            # Stop l'ancien fichier
            if self.is_playing:
                self.stop()
            
            # Crée le media
            media = self.instance.media_new(filepath)
            self.player.set_media(media)
            self.current_file = filepath
            
            self.log(f"✅ Audio chargé: {Path(filepath).name}")
            return True
        except Exception as e:
            self.log(f"❌ Erreur chargement: {e}")
            return False
    
    def play(self) -> bool:
        """Démarre la lecture"""
        try:
            if self.is_paused:
                self.player.pause()  # VLC: pause() toggle pause/unpause
                self.is_paused = False
                self.is_playing = True
                self.log("▶️ Reprise")
            else:
                self.player.play()
                self.is_playing = True
                self.log("▶️ Lecture démarrée")
                
                # Démarre le thread de mise à jour
                if not self.should_update:
                    self.should_update = True
                    self.update_thread = threading.Thread(target=self._update_progress, daemon=True)
                    self.update_thread.start()
            
            return True
        except Exception as e:
            self.log(f"❌ Erreur lecture: {e}")
            return False
    
    def pause(self):
        """Met en pause"""
        if self.is_playing and not self.is_paused:
            self.player.pause()
            self.is_paused = True
            self.is_playing = False
            self.log("⏸ Pause")
    
    def stop(self):
        """Arrête la lecture"""
        self.player.stop()
        self.is_playing = False
        self.is_paused = False
        self.should_update = False
        self.log("⏹ Stop")
    
    def unload(self):
        """Décharge VLC (pour libérer les fichiers)"""
        try:
            self.player.stop()
            self.current_file = None
            self.log("🔓 VLC player déchargé")
        except:
            pass
    
    def get_position(self) -> float:
        """Récupère la position actuelle en secondes"""
        if self.is_playing and not self.is_paused:
            time_ms = self.player.get_time()  # ms
            if time_ms > 0:
                return time_ms / 1000
        return 0
    
    def is_busy(self) -> bool:
        """Vérifie si une piste est en cours de lecture"""
        return self.player.is_playing() == 1
    
    def set_volume(self, volume: int):
        """
        Définit le volume (0-100)
        
        Args:
            volume: Volume (0 = muet, 100 = max)
        """
        self.player.audio_set_volume(volume)
    
    def _on_end_reached(self, event):
        """Callback VLC : piste terminée"""
        self.log("✅ Piste terminée")
        self.is_playing = False
        if self.on_track_end:
            self.on_track_end()
    
    def _update_progress(self):
        """Thread de mise à jour de la progression"""
        while self.should_update:
            try:
                if self.is_playing and not self.is_paused:
                    pos_sec = self.get_position()
                    
                    # Callback mise à jour
                    if self.on_progress_update and pos_sec > 0:
                        self.on_progress_update(pos_sec)
                
                time.sleep(0.1)
            except Exception as e:
                self.log(f"⚠️ Erreur update: {e}")
                time.sleep(0.5)