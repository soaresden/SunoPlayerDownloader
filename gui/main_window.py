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
        
        # Setup UI
        self._create_ui()
        
        self.log('logs.app_started')
        
        # Auto-load cookies
        self._auto_load_cookies()
    
    def _create_ui(self):
        """Crée l'interface - LAYOUT 3 COLONNES"""
        
        # Toolbar
        self.toolbar = Toolbar(self.root, {
            'load_cookies': self.browse_cookies,
            'reload_cookies': self.reload_cookies,
            'change_language': self.change_language
        }, self.lang)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        
        # Log Viewer (bas)
        self.log_viewer = LogViewer(self.root, self.lang)
        self.log_viewer.pack(fill=tk.BOTH, side=tk.BOTTOM, padx=5, pady=5, ipady=2)
        
        # Content - 3 colonnes
        content = tk.Frame(self.root, bg=COLOR_PRIMARY)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # COLONNE 1: Projects Panel avec callback TOUT DL
        projects_container = tk.Frame(content, width=380, bg=COLOR_PRIMARY)
        projects_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 3))
        projects_container.pack_propagate(False)
        
        self.projects_panel = ProjectsPanel(
            projects_container,
            on_select=self.on_project_select,
            on_download_all=self.download_all_projects,  # ⭐ NOUVEAU
            lang_manager=self.lang
        )
        self.projects_panel.pack(fill=tk.BOTH, expand=True)
        
        # COLONNE 2: Clips Panel
        self.clips_panel = ClipsPanel(content, {
            'download_all': self.download_all_project,
            'download_checked': self.download_checked,
            'add_to_playlist': self.add_to_playlist,
            'add_to_download': self.add_to_download,
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
    
    def _auto_load_cookies(self):
        """Charge automatiquement les cookies si présents"""
        from pathlib import Path
        
        # Cherche tous les fichiers qui commencent par "suno_cookies"
        current_dir = Path.cwd()
        cookie_files = list(current_dir.glob("suno_cookies*.json"))
        
        if cookie_files:
            # Trie par date de modification (plus récent en premier)
            cookie_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Prend le plus récent
            latest_cookie = cookie_files[0]
            
            self.log('logs.file_detected', file=latest_cookie.name)
            
            # Affiche les autres fichiers trouvés
            if len(cookie_files) > 1:
                other_files = ', '.join([f.name for f in cookie_files[1:]])
                self.log(f"ℹ️  Autres fichiers cookies trouvés: {other_files}")
            
            self.root.after(500, lambda: self.load_cookies_file(str(latest_cookie)))
        else:
            self.log('logs.file_not_found', file="suno_cookies*.json")
            
    
    def download_all_projects(self):
        """Télécharge TOUS les projets"""
        if not self.projects:
            self.log("⚠️ Aucun projet chargé")
            return
        
        total_clips = sum(p.get('clip_count', 0) for p in self.projects)
        
        response = messagebox.askyesno(
            "Confirmation",
            f"Télécharger TOUS les projets ?\n\n📂 {len(self.projects)} projets\n🎵 ~{total_clips} clips au total\n\n⚠️ Cela peut prendre beaucoup de temps !\n\nContinuer ?"
        )
        
        if not response:
            self.log("❌ Téléchargement annulé")
            return
        
        self.log(f"📥 DÉBUT téléchargement de {len(self.projects)} projets")
        self.log(f"📊 Estimation: ~{total_clips} clips à télécharger")
        
        # Lance dans un thread pour ne pas bloquer l'UI
        def download_task():
            from utils.audio_cache import AudioCache
            
            cache = AudioCache(log_callback=self.log)
            
            total_success = 0
            total_errors = 0
            projects_done = 0
            
            for project in self.projects:
                project_id = project.get('id', '')
                project_name = project.get('name', 'Sans nom')
                clip_count = project.get('clip_count', 0)
                
                if clip_count == 0:
                    self.log(f"⏭️  [{projects_done+1}/{len(self.projects)}] {project_name} (vide)")
                    projects_done += 1
                    continue
                
                self.log("")
                self.log(f"📂 [{projects_done+1}/{len(self.projects)}] {project_name} ({clip_count} clips)")
                
                try:
                    # Récupère les clips du projet
                    project_data = self.client.get_project_clips(project_id)
                    
                    project_clips = project_data.get('project_clips', [])
                    pinned_clips = project_data.get('pinned_clips', [])
                    
                    # Marque les pinned
                    for pc in pinned_clips:
                        pc['is_pinned'] = True
                    
                    # Combine tous les clips
                    pinned_ids = {pc.get('clip', {}).get('id') for pc in pinned_clips}
                    all_clips = list(pinned_clips)
                    
                    for pc in project_clips:
                        if pc.get('clip', {}).get('id') not in pinned_ids:
                            all_clips.append(pc)
                    
                    if not all_clips:
                        self.log(f"  ⚠️ Aucun clip trouvé")
                        projects_done += 1
                        continue
                    
                    # Trie par date
                    sorted_clips = sorted(
                        all_clips,
                        key=lambda c: (
                            c.get('clip', {}).get('created_at', ''),
                            c.get('clip', {}).get('id', '')
                        )
                    )
                    
                    # Télécharge tous les clips
                    project_success = 0
                    project_errors = 0
                    
                    for i, clip_data in enumerate(sorted_clips, 1):
                        clip = clip_data.get('clip', {})
                        title = clip.get('title', 'Sans titre')
                        clip_id = clip.get('id', '')[:8]
                        
                        self.log(f"  [{i}/{len(sorted_clips)}] {title[:40]} ({clip_id})")
                        
                        filepath = cache.get_audio_path(
                            clip_data,
                            project_name,
                            permanent=True,
                            track_number=i
                        )
                        
                        if filepath:
                            project_success += 1
                            total_success += 1
                            
                            # Supprime du cache
                            cache.delete_temp_file(clip.get('id', ''), title)
                        else:
                            project_errors += 1
                            total_errors += 1
                    
                    self.log(f"  ✅ Projet terminé: {project_success} succès, {project_errors} échecs")
                    
                except Exception as e:
                    self.log(f"  ❌ ERREUR projet: {e}")
                    total_errors += clip_count
                
                projects_done += 1
            
            # Résumé final
            self.log("")
            self.log("=" * 60)
            self.log("🏁 TÉLÉCHARGEMENT TERMINÉ")
            self.log(f"📂 Projets traités: {projects_done}/{len(self.projects)}")
            self.log(f"✅ Clips téléchargés: {total_success}")
            self.log(f"❌ Échecs: {total_errors}")
            self.log("=" * 60)
            
            # Message final
            self.root.after(0, lambda: messagebox.showinfo(
                "Téléchargement terminé",
                f"✅ {total_success} clips téléchargés\n❌ {total_errors} échecs\n\n📂 {projects_done} projets traités"
            ))
        
        # Lance le thread
        import threading
        download_thread = threading.Thread(target=download_task, daemon=True)
        download_thread.start()
        
    def browse_cookies(self):
        """Ouvre le dialogue de sélection de cookies"""
        self.log('logs.opening_file_dialog')
        
        try:
            filename = filedialog.askopenfilename(
                title="Sélectionner suno_cookies.json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=Path.cwd()
            )
            
            if filename:
                self.log('logs.file_selected', file=Path(filename).name)
                self.load_cookies_file(filename)
            else:
                self.log('logs.selection_cancelled')
        except Exception as e:
            self.log('logs.error', msg=str(e))
            messagebox.showerror("Erreur", str(e))
    
    def reload_cookies(self):
        """Recharge les cookies"""
        self.log('logs.reload_attempt')
        
        if not self.auth.cookies_file or not Path(self.auth.cookies_file).exists():
            self.log('logs.no_cookies_loaded')
            messagebox.showinfo("Info", self.lang.get('messages.no_cookies'))
            return
        
        self.log('logs.reloading', file=Path(self.auth.cookies_file).name)
        self.load_cookies_file(self.auth.cookies_file)
    
    def load_cookies_file(self, filepath: str):
        """Charge un fichier cookies"""
        try:
            self.log('logs.reading_file', file=Path(filepath).name)
            
            self.auth.load_from_file(filepath)
            
            self.log('logs.auth_success')
            self.log('logs.jwt_token', token=self.auth.jwt_token[:20])
            self.log('logs.device_id', id=self.auth.device_id)
            self.toolbar.set_status("🟢")
            
            self.client = SunoClient(
                jwt_token=self.auth.jwt_token,
                device_id=self.auth.device_id
            )
            
            self.log('logs.client_init')
            self.root.after(100, self.load_projects)
            
        except Exception as e:
            self.log('logs.error', msg=str(e))
            self.log('logs.traceback', trace=traceback.format_exc())
            self.toolbar.set_status("🔴")
            messagebox.showerror("Erreur", f"Impossible de charger les cookies:\n{e}")
    
    def load_projects(self):
        """Charge tous les projets"""
        if not self.client:
            self.log('logs.client_not_init')
            return
        
        self.log('logs.loading_projects')
        
        def on_success(projects):
            self.projects = projects
            self.log('logs.projects_loaded', count=len(projects))
            self.log('logs.displaying_treeview')
            self.projects_panel.load_projects(projects)
            self.log('logs.projects_displayed')
        
        def on_error(error):
            self.log('logs.error', msg=str(error))
            self.log('logs.traceback', trace=traceback.format_exc())
            messagebox.showerror("Erreur", f"Erreur de chargement:\n{error}")
        
        run_in_thread(
            self.client.get_all_projects,
            on_success=lambda result: self.root.after(0, lambda: on_success(result)),
            on_error=lambda error: self.root.after(0, lambda: on_error(error))
        )
    
    def on_project_select(self, project_id: str):
        """Appelé quand un projet est sélectionné"""
        self.log('logs.selecting_project', id=project_id[:8])
        
        project = next((p for p in self.projects if p.get('id') == project_id), None)
        if not project:
            self.log('logs.project_not_found', id=project_id[:8])
            return
        
        self.current_project = project
        project_name = project.get('name', 'Sans nom')
        clip_count = project.get('clip_count', 0)
        
        self.log('logs.project_selected', name=project_name, count=clip_count)
        self.load_project_clips(project_id, project_name)
    
    def load_project_clips(self, project_id: str, project_name: str):
        """Charge les clips d'un projet"""
        self.log('logs.loading_clips', id=project_id[:8])
        
        def on_success(project_data):
            self.log('logs.clips_data_received')
            
            project_clips = project_data.get('project_clips', [])
            pinned_clips = project_data.get('pinned_clips', [])
            
            self.log('logs.pinned_clips', count=len(pinned_clips))
            self.log('logs.normal_clips', count=len(project_clips))
            
            for pc in pinned_clips:
                pc['is_pinned'] = True
            
            pinned_ids = {pc.get('clip', {}).get('id') for pc in pinned_clips}
            all_clips = list(pinned_clips)
            
            for pc in project_clips:
                if pc.get('clip', {}).get('id') not in pinned_ids:
                    all_clips.append(pc)
            
            self.current_clips = all_clips
            
            self.log('logs.total_clips', total=len(all_clips), pinned=len(pinned_clips))
            self.clips_panel.load_clips(project_name, all_clips)
            self.player_panel.set_workspace(project_name)
        
        def on_error(error):
            self.log('logs.error_loading_clips', msg=str(error))
            messagebox.showerror("Erreur", f"Erreur de chargement des clips:\n{error}")
        
        run_in_thread(
            lambda: self.client.get_project_clips(project_id),
            on_success=lambda result: self.root.after(0, lambda: on_success(result)),
            on_error=lambda error: self.root.after(0, lambda: on_error(error))
        )
    
    def add_to_playlist(self, clip_data: dict):
        """Ajoute un clip à la playlist"""
        self.player_panel.add_to_playlist(clip_data)
    
    def add_to_download(self, clip_data: dict):
        """Ajoute un clip à la liste de téléchargement"""
        clip = clip_data.get('clip', {})
        title = clip.get('title', 'Sans titre')
        self.log('logs.added_to_download', title=title[:50])
        """Ajoute un clip à la liste de téléchargement"""
        self.player_panel.add_to_downloads(clip_data)
    
    def download_all_project(self):
        """Télécharge tout le projet"""
        if not self.current_project:
            self.log('logs.no_project_selected')
            messagebox.showwarning("Attention", self.lang.get('messages.no_project'))
            return
        
        name = self.current_project.get('name')
        clip_count = len(self.current_clips)
        
        self.log('logs.confirm_download', name=name, count=clip_count)
        
        response = messagebox.askyesno(
            "Confirmation",
            self.lang.get('messages.confirm_download_all', name=name, count=clip_count)
        )
        
        if response:
            self.log('logs.download_start', name=name)
            self._download_clips(self.current_clips, name)
        else:
            self.log('logs.download_cancelled')
    
    def download_checked(self, clips_to_download: list):
        """Télécharge les clips cochés"""
        if not self.current_project:
            self.log('logs.no_project_active')
            return
        
        workspace_name = self.current_project.get('name', 'Unknown')
        self.log('logs.download_request', count=len(clips_to_download))
        
        self._download_clips(clips_to_download, workspace_name)
    
    def _download_clips(self, clips: list, workspace_name: str):
        """Télécharge une liste de clips"""
        from utils.audio_cache import AudioCache
        
        cache = AudioCache(log_callback=self.log)
        
        # ⭐ TRI par date de création (plus vieux en premier)
        # Si même date, trie par ID pour consistance
        sorted_clips = sorted(
            clips, 
            key=lambda c: (
                c.get('clip', {}).get('created_at', ''),
                c.get('clip', {}).get('id', '')
            )
        )
        
        success_count = 0
        error_count = 0
        
        folder_path = f"downloads/Suno-{workspace_name}/"
        self.log(f"📦 Téléchargement de {len(sorted_clips)} clip(s) vers {folder_path}")
        
        for i, clip_data in enumerate(sorted_clips, 1):
            clip = clip_data.get('clip', {})
            title = clip.get('title', 'Sans titre')
            clip_id = clip.get('id', '')[:8]
            
            self.log(f"[{i}/{len(sorted_clips)}] 📥 {title[:40]} ({clip_id})")
            
            # ⭐ Passe le track_number basé sur la position triée
            filepath = cache.get_audio_path(
                clip_data, 
                workspace_name, 
                permanent=True,
                track_number=i
            )
            
            if filepath:
                success_count += 1
            else:
                error_count += 1
        
        self.log("")
        self.log("✅ Téléchargement terminé:")
        self.log(f"  ✅ Succès: {success_count}")
        self.log(f"  ❌ Échecs: {error_count}")
        
        messagebox.showinfo(
            self.lang.get('logs.download_complete'),
            self.lang.get('messages.download_complete_msg', 
                         success=success_count, 
                         errors=error_count, 
                         folder=folder_path)
        )