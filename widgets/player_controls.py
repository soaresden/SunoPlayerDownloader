"""
Contrôles UI du player (boutons, slider, timer)
"""

import tkinter as tk
from typing import Callable
from config import *
from utils.formatters import format_duration


class PlayerControls(tk.Frame):
    """Contrôles visuels du player"""
    
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
        
        self._create_ui()
    
    def _create_ui(self):
        """Crée l'interface"""
        
        # Info piste
        self.current_label = tk.Label(
            self,
            text=self.lang.get('player.no_track'),
            font=("Arial", 10, "bold"),
            bg=COLOR_CARD_BG,
            fg=COLOR_TEXT_LIGHT,
            wraplength=300,
            justify=tk.CENTER
        )
        self.current_label.pack(pady=(5, 2))
        
        self.artist_label = tk.Label(
            self,
            text="",
            font=("Arial", 9),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG
        )
        self.artist_label.pack(pady=(0, 8))
        
        # Slider
        slider_frame = tk.Frame(self, bg=COLOR_CARD_BG)
        slider_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.slider = tk.Scale(
            slider_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            showvalue=False,
            bg=COLOR_CARD_BG,
            fg=COLOR_SUNO_YELLOW,
            troughcolor=COLOR_DARK_BG,
            highlightthickness=0,
            sliderrelief=tk.FLAT,
            command=lambda v: None
        )
        self.slider.pack(fill=tk.X)
        
        # Timer
        self.timer_label = tk.Label(
            self,
            text="0:00 / 0:00",
            font=("Arial", 9),
            bg=COLOR_CARD_BG,
            fg=COLOR_TEXT_MUTED
        )
        self.timer_label.pack(pady=(2, 8))
        
        # Boutons de contrôle
        controls = tk.Frame(self, bg=COLOR_CARD_BG)
        controls.pack(pady=10)
        
        btn_config = {
            "font": ("Arial", 14, "bold"),
            "fg": "white",
            "relief": tk.FLAT,
            "cursor": "hand2",
            "bd": 0,
            "padx": 12,
            "pady": 8
        }
        
        tk.Button(
            controls, 
            text="⏮", 
            bg=COLOR_SECONDARY, 
            command=self.callbacks.get('on_previous'), 
            **btn_config
        ).pack(side=tk.LEFT, padx=3)
        
        self.btn_play_pause = tk.Button(
            controls, 
            text="▶️", 
            bg=COLOR_SUCCESS, 
            command=self.callbacks.get('on_toggle_play_pause'), 
            **btn_config
        )
        self.btn_play_pause.pack(side=tk.LEFT, padx=3)
        
        tk.Button(
            controls, 
            text="⏹", 
            bg=COLOR_SUNO_PINK, 
            command=self.callbacks.get('on_stop'), 
            **btn_config
        ).pack(side=tk.LEFT, padx=3)
        
        tk.Button(
            controls, 
            text="⏭", 
            bg=COLOR_SECONDARY, 
            command=self.callbacks.get('on_next'), 
            **btn_config
        ).pack(side=tk.LEFT, padx=3)
    
    def set_track_info(self, title: str, artist: str):
        """Définit les infos de la piste"""
        self.current_label.config(text=title)
        self.artist_label.config(text=artist)
    
    def set_duration(self, duration: float):
        """Définit la durée totale"""
        duration_str = format_duration(duration)
        self.timer_label.config(text=f"0:00 / {duration_str}")
    
    def update_progress(self, current: float, total: float):
        """Met à jour la progression"""
        if total > 0:
            progress = (current / total) * 100
            self.slider.set(min(progress, 100))
            
            current_str = format_duration(current)
            total_str = format_duration(total)
            self.timer_label.config(text=f"{current_str} / {total_str}")
    
    def set_play_pause_state(self, is_playing: bool):
        """Change l'état du bouton play/pause"""
        if is_playing:
            self.btn_play_pause.config(text="⏸", bg=COLOR_SUNO_ORANGE)
        else:
            self.btn_play_pause.config(text="▶️", bg=COLOR_SUCCESS)
    
    def reset(self):
        """Réinitialise l'affichage"""
        self.current_label.config(text=self.lang.get('player.no_track'))
        self.artist_label.config(text="")
        self.timer_label.config(text="0:00 / 0:00")
        self.slider.set(0)
        self.set_play_pause_state(False)