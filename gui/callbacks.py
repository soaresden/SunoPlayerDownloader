"""
Callbacks et event handlers pour la fenêtre principale
"""
from tkinter import filedialog, messagebox
from pathlib import Path
import traceback
from utils.threading_helper import run_in_thread
from utils.local_files_scanner import LocalFilesScanner


class SunoCallbacks:
    """Gestionnaire de tous les callbacks de l'application"""
    
    def __init__(self, main_window):
        """
        Args:
            main_window: Instance de SunoMainWindow
        """
        self.window = main_window
    
    def browse_cookies(self):
        """Ouvre le dialogue de sélection de cookies"""
        self.window.log('logs.opening_file_dialog')
        
        try:
            filename = filedialog.askopenfilename(
                title=self.lang.get("dialogs.select_cookies"),
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=Path.cwd()
            )
            
            if filename:
                self.window.log('logs.file_selected', file=Path(filename).name)
                self.window.cookie_manager.load_cookies_file(filename)
            else:
                self.window.log('logs.selection_cancelled')
        except Exception as e:
            self.window.log('logs.error', msg=str(e))
            messagebox.showerror("Erreur", str(e))
    
    def reload_cookies(self):
        """Recharge les cookies"""
        self.window.log('logs.reload_attempt')
        
        if not self.window.auth.cookies_file or not Path(self.window.auth.cookies_file).exists():
            self.window.log('logs.no_cookies_loaded')
            messagebox.showinfo("Info", self.window.lang.get('messages.no_cookies'))
            return
        
        self.window.log('logs.reloading', file=Path(self.window.auth.cookies_file).name)
        self.window.cookie_manager.load_cookies_file(self.window.auth.cookies_file)
    
    def on_project_select(self, project_id: str):
        """Appelé quand un projet est sélectionné"""
        self.window.log('logs.selecting_project', id=project_id[:8])
        
        project = next((p for p in self.window.projects if p.get('id') == project_id), None)
        if not project:
            self.window.log('logs.project_not_found', id=project_id[:8])
            return
        
        self.window.current_project = project
        project_name = project.get('name', 'Sans nom')
        clip_count = project.get('clip_count', 0)
        
        self.window.log('logs.project_selected', name=project_name, count=clip_count)
        self._load_project_clips(project_id, project_name)
    
    def _load_project_clips(self, project_id: str, project_name: str):
        """Charge les clips d'un projet"""
        self.window.log('logs.loading_clips', id=project_id[:8])
        
        def on_success(project_data):
            self.window.log('logs.clips_data_received')
            
            project_clips = project_data.get('project_clips', [])
            pinned_clips = project_data.get('pinned_clips', [])
            
            self.window.log('logs.pinned_clips', count=len(pinned_clips))
            self.window.log('logs.normal_clips', count=len(project_clips))
            
            for pc in pinned_clips:
                pc['is_pinned'] = True
            
            pinned_ids = {pc.get('clip', {}).get('id') for pc in pinned_clips}
            all_clips = list(pinned_clips)
            
            for pc in project_clips:
                if pc.get('clip', {}).get('id') not in pinned_ids:
                    all_clips.append(pc)
            
            self.window.current_clips = all_clips
            
            self.window.log('logs.total_clips', total=len(all_clips), pinned=len(pinned_clips))
            
            # ⭐ APPEL CORRIGÉ : project_name en premier, all_clips en second
            self.window.clips_panel.load_clips(project_name, all_clips)
            self.window.player_panel.set_workspace(project_name)
        
        def on_error(error):
            self.window.log('logs.error_loading_clips', msg=str(error))
            messagebox.showerror("Erreur", f"Erreur de chargement des clips:\n{error}")
        
        run_in_thread(
            lambda: self.window.client.get_project_clips(project_id),
            on_success=lambda result: self.window.root.after(0, lambda: on_success(result)),
            on_error=lambda error: self.window.root.after(0, lambda: on_error(error))
        )
    
    def add_to_playlist(self, clip_data: dict):
        """Ajoute un clip à la playlist"""
        self.window.player_panel.add_to_playlist(clip_data)
    
    def add_to_download(self, clip_data: dict):
        """Ajoute un clip à la liste de téléchargement"""
        clip = clip_data.get('clip', {})
        title = clip.get('title', 'Sans titre')
        self.window.log('logs.added_to_download', title=title[:50])
        self.window.player_panel.add_to_downloads(clip_data)
    
    def download_all_project(self):
        """Télécharge tout le projet"""
        if not self.window.current_project:
            self.window.log('logs.no_project_selected')
            messagebox.showwarning("Attention", self.window.lang.get('messages.no_project'))
            return
        
        name = self.window.current_project.get('name')
        clip_count = len(self.window.current_clips)
        
        self.window.log('logs.confirm_download', name=name, count=clip_count)
        
        response = messagebox.askyesno(
            "Confirmation",
            self.window.lang.get('messages.confirm_download_all', name=name, count=clip_count)
        )
        
        if response:
            self.window.log('logs.download_start', name=name)
            self._download_clips(self.window.current_clips, name)
        else:
            self.window.log('logs.download_cancelled')
    
    def download_checked(self, clips_to_download: list):
        """Télécharge les clips cochés"""
        if not self.window.current_project:
            self.window.log('logs.no_project_active')
            return
        
        workspace_name = self.window.current_project.get('name', 'Unknown')
        self.window.log('logs.download_request', count=len(clips_to_download))
        
        self._download_clips(clips_to_download, workspace_name)
    
    def download_all_projects(self):
        """Télécharge TOUS les projets"""
        if not self.window.projects:
            self.window.log("⚠️ Aucun projet chargé")
            return
        
        total_clips = sum(p.get('clip_count', 0) for p in self.window.projects)
        
        response = messagebox.askyesno(
            "Confirmation",
            f"Télécharger TOUS les projets ?\n\n📂 {len(self.window.projects)} projets\n🎵 ~{total_clips} clips au total\n\n⚠️ Cela peut prendre beaucoup de temps !\n\nContinuer ?"
        )
        
        if not response:
            self.window.log("❌ Téléchargement annulé")
            return
        
        self.window.log(f"📥 DÉBUT téléchargement de {len(self.window.projects)} projets")
        self.window.log(f"📊 Estimation: ~{total_clips} clips à télécharger")
        
        # Lance dans un thread
        def download_task():
            from utils.audio_cache import AudioCache
            
            cache = AudioCache(log_callback=self.window.log)
            
            total_success = 0
            total_errors = 0
            projects_done = 0
            
            for project in self.window.projects:
                project_id = project.get('id', '')
                project_name = project.get('name', 'Sans nom')
                clip_count = project.get('clip_count', 0)
                
                if clip_count == 0:
                    self.window.log(f"⏭️  [{projects_done+1}/{len(self.window.projects)}] {project_name} (vide)")
                    projects_done += 1
                    continue
                
                self.window.log("")
                self.window.log(f"📂 [{projects_done+1}/{len(self.window.projects)}] {project_name} ({clip_count} clips)")
                
                try:
                    project_data = self.window.client.get_project_clips(project_id)
                    
                    project_clips = project_data.get('project_clips', [])
                    pinned_clips = project_data.get('pinned_clips', [])
                    
                    for pc in pinned_clips:
                        pc['is_pinned'] = True
                    
                    pinned_ids = {pc.get('clip', {}).get('id') for pc in pinned_clips}
                    all_clips = list(pinned_clips)
                    
                    for pc in project_clips:
                        if pc.get('clip', {}).get('id') not in pinned_ids:
                            all_clips.append(pc)
                    
                    if not all_clips:
                        self.window.log(f"  ⚠️ Aucun clip trouvé")
                        projects_done += 1
                        continue
                    
                    sorted_clips = sorted(
                        all_clips,
                        key=lambda c: (
                            c.get('clip', {}).get('created_at', ''),
                            c.get('clip', {}).get('id', '')
                        )
                    )
                    
                    project_success = 0
                    project_errors = 0
                    
                    for i, clip_data in enumerate(sorted_clips, 1):
                        clip = clip_data.get('clip', {})
                        title = clip.get('title', 'Sans titre')
                        clip_id = clip.get('id', '')[:8]
                        
                        self.window.log(f"  [{i}/{len(sorted_clips)}] {title[:40]} ({clip_id})")
                        
                        filepath = cache.get_audio_path(
                            clip_data,
                            project_name,
                            permanent=True,
                            track_number=i
                        )
                        
                        if filepath:
                            project_success += 1
                            total_success += 1
                            cache.delete_temp_file(clip.get('id', ''), title)
                        else:
                            project_errors += 1
                            total_errors += 1
                    
                    self.window.log(f"  ✅ Projet terminé: {project_success} succès, {project_errors} échecs")
                    
                except Exception as e:
                    self.window.log(f"  ❌ ERREUR projet: {e}")
                    total_errors += clip_count
                
                projects_done += 1
            
            self.window.log("")
            self.window.log("=" * 60)
            self.window.log("🏁 TÉLÉCHARGEMENT TERMINÉ")
            self.window.log(f"📂 Projets traités: {projects_done}/{len(self.window.projects)}")
            self.window.log(f"✅ Clips téléchargés: {total_success}")
            self.window.log(f"❌ Échecs: {total_errors}")
            self.window.log("=" * 60)
            
            self.window.root.after(0, lambda: messagebox.showinfo(
                "Téléchargement terminé",
                f"✅ {total_success} clips téléchargés\n❌ {total_errors} échecs\n\n📂 {projects_done} projets traités"
            ))
        
        import threading
        download_thread = threading.Thread(target=download_task, daemon=True)
        download_thread.start()
    
    def sync_project(self):
        """
        SYNC intelligent : Compare local vs API et télécharge uniquement les nouveaux clips
        """
        if not self.window.current_project:
            self.window.log("⚠️ Aucun projet sélectionné pour SYNC")
            messagebox.showwarning("Attention", self.window.lang.get('messages.no_project'))
            return
        
        project_name = self.window.current_project.get('name', 'Unknown')
        project_id = self.window.current_project.get('id', '')
        
        self.window.log("")
        self.window.log("=" * 60)
        self.window.log(f"🔄 SYNC : {project_name}")
        self.window.log("=" * 60)
        
        # Lance dans un thread
        def sync_task():
            from utils.audio_cache import AudioCache
            from utils.local_files_scanner import LocalFilesScanner
            
            cache = AudioCache(log_callback=self.window.log)
            scanner = LocalFilesScanner(log_callback=self.window.log)
            
            # 1. Récupère les clips de l'API
            self.window.log(f"📡 Récupération des clips depuis l'API...")
            
            try:
                project_data = self.window.client.get_project_clips(project_id)
                
                project_clips = project_data.get('project_clips', [])
                pinned_clips = project_data.get('pinned_clips', [])
                
                for pc in pinned_clips:
                    pc['is_pinned'] = True
                
                pinned_ids = {pc.get('clip', {}).get('id') for pc in pinned_clips}
                all_clips = list(pinned_clips)
                
                for pc in project_clips:
                    if pc.get('clip', {}).get('id') not in pinned_ids:
                        all_clips.append(pc)
                
                if not all_clips:
                    self.window.log("⚠️ Aucun clip trouvé sur l'API")
                    return
                
                self.window.log(f"✅ {len(all_clips)} clip(s) trouvé(s) sur l'API")
                
            except Exception as e:
                self.window.log(f"❌ Erreur API : {e}")
                return
            
            # 2. Scan des fichiers locaux
            self.window.log(f"📂 Scan des fichiers locaux...")
            
            local_files = scanner.scan_workspace(project_name)
            local_ids = set()
            
            for file_info in local_files:
                clip_id = file_info.get('suno_id')
                if clip_id:
                    local_ids.add(clip_id)
            
            self.window.log(f"✅ {len(local_ids)} clip(s) avec ID trouvé(s) en local")
            
            # 3. Compare et trouve les clips manquants
            missing_clips = []
            
            for clip_data in all_clips:
                clip = clip_data.get('clip', {})
                clip_id = clip.get('id', '')
                
                if clip_id not in local_ids:
                    missing_clips.append(clip_data)
            
            if not missing_clips:
                self.window.log("")
                self.window.log("✅ Tous les clips sont déjà téléchargés !")
                self.window.log(f"📊 Local: {len(local_ids)} / API: {len(all_clips)}")
                
                self.window.root.after(0, lambda: messagebox.showinfo(
                    "SYNC Terminé",
                    f"✅ Tous les clips sont déjà téléchargés !\n\n📊 {len(local_ids)} clip(s) à jour"
                ))
                return
            
            self.window.log("")
            self.window.log(f"🆕 {len(missing_clips)} nouveau(x) clip(s) à télécharger")
            self.window.log("")
            
            # 4. Télécharge les clips manquants
            sorted_clips = sorted(
                missing_clips,
                key=lambda c: (
                    c.get('clip', {}).get('created_at', ''),
                    c.get('clip', {}).get('id', '')
                )
            )
            
            success_count = 0
            error_count = 0
            
            for i, clip_data in enumerate(sorted_clips, 1):
                clip = clip_data.get('clip', {})
                title = clip.get('title', 'Sans titre')
                clip_id = clip.get('id', '')[:8]
                
                # Calcule le numéro de track (total local + nouveaux)
                track_number = len(local_ids) + i
                
                self.window.log(f"[{i}/{len(sorted_clips)}] 📥 {title[:40]} ({clip_id})")
                
                filepath = cache.get_audio_path(
                    clip_data,
                    project_name,
                    permanent=True,
                    track_number=track_number
                )
                
                if filepath:
                    success_count += 1
                    cache.delete_temp_file(clip.get('id', ''), title)
                else:
                    error_count += 1
            
            self.window.log("")
            self.window.log("=" * 60)
            self.window.log("✅ SYNC Terminé")
            self.window.log(f"📊 Local avant: {len(local_ids)} / API: {len(all_clips)}")
            self.window.log(f"🆕 Téléchargés: {success_count}")
            self.window.log(f"❌ Échecs: {error_count}")
            self.window.log(f"📊 Local après: {len(local_ids) + success_count} / API: {len(all_clips)}")
            self.window.log("=" * 60)
            
            self.window.root.after(0, lambda: messagebox.showinfo(
                "SYNC Terminé",
                f"✅ SYNC Terminé !\n\n🆕 Téléchargés: {success_count}\n❌ Échecs: {error_count}\n\n📊 {len(local_ids) + success_count}/{len(all_clips)} clip(s) à jour"
            ))
        
        import threading
        sync_thread = threading.Thread(target=sync_task, daemon=True)
        sync_thread.start()
    
    def _download_clips(self, clips: list, workspace_name: str):
        """Télécharge une liste de clips"""
        from utils.audio_cache import AudioCache
        
        cache = AudioCache(log_callback=self.window.log)
        
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
        self.window.log(f"📦 Téléchargement de {len(sorted_clips)} clip(s) vers {folder_path}")
        
        for i, clip_data in enumerate(sorted_clips, 1):
            clip = clip_data.get('clip', {})
            title = clip.get('title', 'Sans titre')
            clip_id = clip.get('id', '')[:8]
            
            self.window.log(f"[{i}/{len(sorted_clips)}] 📥 {title[:40]} ({clip_id})")
            
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
        
        self.window.log("")
        self.window.log("✅ Téléchargement terminé:")
        self.window.log(f"  ✅ Succès: {success_count}")
        self.window.log(f"  ❌ Échecs: {error_count}")
        
        messagebox.showinfo(
            self.window.lang.get('logs.download_complete'),
            self.window.lang.get('messages.download_complete_msg', 
                                success=success_count, 
                                errors=error_count, 
                                folder=folder_path)
        )