"""
Gestionnaire de chargement et validation des cookies
"""
from pathlib import Path
from tkinter import messagebox
import traceback
from api.client import SunoClient
from utils.threading_helper import run_in_thread


class CookieManager:
    """Gestionnaire de cookies pour Suno"""
    
    def __init__(self, main_window):
        """
        Args:
            main_window: Instance de SunoMainWindow
        """
        self.window = main_window
    
    def auto_load_cookies(self):
        """Charge automatiquement les cookies si présents"""
        current_dir = Path.cwd()
        cookie_files = list(current_dir.glob("suno_cookies*.json"))
        
        if cookie_files:
            # Trie par date de modification (plus récent en premier)
            cookie_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Prend le plus récent
            latest_cookie = cookie_files[0]
            
            self.window.log('logs.file_detected', file=latest_cookie.name)
            
            # Affiche les autres fichiers trouvés
            if len(cookie_files) > 1:
                other_files = ', '.join([f.name for f in cookie_files[1:]])
                self.window.log(f"ℹ️  Autres fichiers cookies trouvés: {other_files}")
            
            self.window.root.after(500, lambda: self.load_cookies_file(str(latest_cookie)))
        else:
            self.window.log('logs.file_not_found', file="suno_cookies*.json")
    
    def load_cookies_file(self, filepath: str):
        """Charge un fichier cookies"""
        try:
            self.window.log('logs.reading_file', file=Path(filepath).name)
            
            self.window.auth.load_from_file(filepath)
            
            self.window.log('logs.auth_success')
            self.window.log('logs.jwt_token', token=self.window.auth.jwt_token[:20])
            self.window.log('logs.device_id', id=self.window.auth.device_id)
            self.window.toolbar.set_status("🟢")
            
            self.window.client = SunoClient(
                jwt_token=self.window.auth.jwt_token,
                device_id=self.window.auth.device_id
            )
            
            self.window.log('logs.client_init')
            self.window.root.after(100, self.load_projects)
            
        except Exception as e:
            self.window.log('logs.error', msg=str(e))
            self.window.log('logs.traceback', trace=traceback.format_exc())
            self.window.toolbar.set_status("🔴")
            messagebox.showerror("Erreur", f"Impossible de charger les cookies:\n{e}")
    
    def load_projects(self):
        """Charge tous les projets"""
        if not self.window.client:
            self.window.log('logs.client_not_init')
            return
        
        self.window.log('logs.loading_projects')
        
        def on_success(projects):
            self.window.projects = projects
            self.window.log('logs.projects_loaded', count=len(projects))
            self.window.log('logs.displaying_treeview')
            self.window.projects_panel.set_client(self.window.client)
            self.window.projects_panel.load_projects(projects)
            self.window.log('logs.projects_displayed')
        
        def on_error(error):
            self.window.log('logs.error', msg=str(error))
            self.window.log('logs.traceback', trace=traceback.format_exc())
            messagebox.showerror("Erreur", f"Erreur de chargement:\n{error}")
        
        run_in_thread(
            self.window.client.get_all_projects,
            on_success=lambda result: self.window.root.after(0, lambda: on_success(result)),
            on_error=lambda error: self.window.root.after(0, lambda: on_error(error))
        )