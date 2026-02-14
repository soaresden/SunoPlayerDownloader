"""
Fenêtre principale de l'application
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import traceback

from config import *
from api.auth import AuthManager
from api.client import SunoClient
from gui.toolbar import Toolbar
from gui.projects_panel import ProjectsPanel
from gui.clips_panel import ClipsPanel
from widgets.log_viewer import LogViewer
from widgets.player_panel import PlayerPanel
from utils.threading_helper import run_in_thread
from utils.language_manager import LanguageManager
from gui.callbacks import SunoCallbacks
from gui.cookie_manager import CookieManager


class SunoMainWindow:
    """Fenêtre principale de l'application"""
    
    def __init__(self, root):
        """
        Args:
            root: Fenêtre Tkinter root
        """
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self.root.configure(bg=COLOR_PRIMARY)
        
        # Gestionnaire de langues
        self.lang = LanguageManager(DEFAULT_LANGUAGE)
        
        # Managers
        self.auth = AuthManager()
        self.client = None
        
        # Data
        self.projects = []
        self.current_project = None
        self.current_clips = []
        
        # ⭐ Gestionnaires modulaires
        self.callbacks = SunoCallbacks(self)
        self.cookie_manager = CookieManager(self)
        
        # Setup UI
        self._create_ui()
        
        self.log('logs.app_started')
        
        # Auto-load cookies via le manager
        self.cookie_manager.auto_load_cookies()
    
    def _create_ui(self):
        """Crée l'interface - LAYOUT 3 COLONNES"""
        
        # Toolbar
        self.toolbar = Toolbar(self.root, {
            'load_cookies': self.callbacks.browse_cookies,
            'reload_cookies': self.callbacks.reload_cookies,
            'change_language': self.change_language
        }, self.lang)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        
        # Log Viewer (bas)
        self.log_viewer = LogViewer(self.root, self.lang)
        self.log_viewer.pack(fill=tk.BOTH, side=tk.BOTTOM, padx=5, pady=5, ipady=2)
        
        # Content - 3 colonnes
        content = tk.Frame(self.root, bg=COLOR_PRIMARY)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # COLONNE 1: Projects Panel
        projects_container = tk.Frame(content, width=380, bg=COLOR_PRIMARY)
        projects_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 3))
        projects_container.pack_propagate(False)
        
        self.projects_panel = ProjectsPanel(
            projects_container,
            on_select=self.callbacks.on_project_select,
            on_download_all=self.callbacks.download_all_projects,
            on_sync=self.callbacks.sync_project,
            lang_manager=self.lang
        )
        self.projects_panel.pack(fill=tk.BOTH, expand=True)
        
        # COLONNE 2: Clips Panel
        self.clips_panel = ClipsPanel(content, {
            'download_all': self.callbacks.download_all_project,
            'download_checked': self.callbacks.download_checked,
            'add_to_playlist': self.callbacks.add_to_playlist,
            'add_to_download': self.callbacks.add_to_download,
            'log': self.log
        }, self.lang)
        self.clips_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
        
        # COLONNE 3: Player Panel
        player_container = tk.Frame(content, width=350, bg=COLOR_PRIMARY)
        player_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(3, 0))
        player_container.pack_propagate(False)
        
        self.player_panel = PlayerPanel(player_container, log_callback=self.log, lang_manager=self.lang)
        self.player_panel.pack(fill=tk.BOTH, expand=True)
    
    def log(self, key: str, **kwargs):
        """Log un message traduit"""
        message = self.lang.get(key, **kwargs)
        self.log_viewer.log(message)
    
    def change_language(self, new_language: str):
        """Change la langue de l'interface"""
        self.log('logs.loading_language', lang=new_language)
        
        if self.lang.load_language(new_language):
            # Met à jour tous les composants
            self.toolbar.update_texts()
            self.projects_panel.update_texts()
            self.clips_panel.update_texts()
            self.player_panel.update_texts()
            self.log_viewer.update_texts()
            
            self.log('logs.language_changed', lang=new_language)
        else:
            messagebox.showerror("Error", f"Failed to load language: {new_language}")