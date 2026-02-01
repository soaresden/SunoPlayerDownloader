"""
Logique de lecture audio avec pygame
"""

import pygame
import threading
import time
from typing import Callable, Optional


class AudioPlayer:
    """Gestion de la lecture audio avec pygame"""
    
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
        
        # Init pygame
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.log("🎵 Pygame mixer initialisé")
        except Exception as e:
            self.log(f"⚠️ Erreur init pygame: {e}")
    
    def load(self, filepath: str) -> bool:
        """Charge un fichier audio"""
        try:
            pygame.mixer.music.load(filepath)
            self.log(f"✅ Audio chargé: {filepath}")
            return True
        except Exception as e:
            self.log(f"❌ Erreur chargement: {e}")
            return False
    
    def play(self) -> bool:
        """Démarre la lecture"""
        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.is_playing = True
                self.log("▶️ Reprise")
            else:
                pygame.mixer.music.play()
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
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            self.log("⏸ Pause")
    
    def stop(self):
        """Arrête la lecture"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.should_update = False
        self.log("⏹ Stop")
    
    def unload(self):
        """Décharge pygame (pour libérer les fichiers)"""
        try:
            pygame.mixer.music.unload()
            self.log("🔓 Pygame music déchargé")
        except:
            pass
    
    def get_position(self) -> float:
        """Récupère la position actuelle en secondes"""
        if self.is_playing and not self.is_paused:
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms > 0:
                return pos_ms / 1000
        return 0
    
    def is_busy(self) -> bool:
        """Vérifie si une piste est en cours de lecture"""
        return pygame.mixer.music.get_busy()
    
    def _update_progress(self):
        """Thread de mise à jour de la progression"""
        while self.should_update:
            try:
                if self.is_playing and not self.is_paused:
                    pos_sec = self.get_position()
                    
                    # Callback mise à jour
                    if self.on_progress_update and pos_sec > 0:
                        self.on_progress_update(pos_sec)
                    
                    # Vérifie si piste terminée
                    if not self.is_busy():
                        self.log("✅ Piste terminée")
                        if self.on_track_end:
                            self.on_track_end()
                
                time.sleep(0.1)
            except Exception as e:
                self.log(f"⚠️ Erreur update: {e}")
                time.sleep(0.5)