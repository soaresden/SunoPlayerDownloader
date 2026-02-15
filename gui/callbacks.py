"""
Callbacks pour l'application Suno Player - VERSION CORRIGÉE
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import traceback
import shutil
import re
from datetime import datetime
from typing import List, Dict


class SunoCallbacks:
    """Gestionnaire centralisé des callbacks"""
    
    def __init__(self, window):
        """
        Args:
            window: Instance de SunoMainWindow
        """
        self.window = window
    
    def browse_cookies(self):
        """Ouvre un dialogue pour charger un fichier cookies.json"""
        filepath = filedialog.askopenfilename(
            title=self.window.lang.get('toolbar.load_cookies'),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            self.window.log('logs.loading_cookies', file=Path(filepath).name)
            self.window.cookie_manager.load_cookies(filepath)
    
    def reload_cookies(self):
        """Recharge le dernier fichier cookies"""
        self.window.cookie_manager.reload_last_cookies()
    
    def on_project_select(self, project_id: str):
        """Callback quand un projet est sélectionné"""
        self.window.log(f"🖱️ Sélection du projet ID: {project_id[:8]}...")
        
        # Trouve le projet complet
        project = None
        for p in self.window.projects:
            if p.get('id') == project_id:
                project = p
                break
        
        if not project:
            self.window.log('logs.project_not_found')
            return
        
        self.window.current_project = project
        project_name = project.get('name', 'Unknown')
        clip_count = project.get('clip_count', 0)
        
        self.window.log(f"📁 Projet: {project_name} ({clip_count} clip(s))")
        
        # Charge les clips du projet dans un thread
        def load_task():
            try:
                self.window.log(f"⏳ Récupération des clips du projet {project_id[:8]}...")
                project_data = self.window.client.get_project_clips(project_id)
                
                self.window.log(f"📦 Données projet reçues de l'API")
                
                # Structure des données
                pinned_clips = project_data.get('pinned_clips', [])
                project_clips = project_data.get('project_clips', [])
                
                self.window.log(f"📌 {len(pinned_clips)} clip(s) pinned détecté(s)")
                self.window.log(f"📄 {len(project_clips)} clip(s) normaux détecté(s)")
                
                # Marque les clips pinnés
                for pc in pinned_clips:
                    pc['is_pinned'] = True
                
                # Fusionne : pinnés en premier
                pinned_ids = {pc.get('clip', {}).get('id') for pc in pinned_clips}
                all_clips = list(pinned_clips)
                
                for pc in project_clips:
                    if pc.get('clip', {}).get('id') not in pinned_ids:
                        all_clips.append(pc)
                
                self.window.log(f"✅ Total: {len(all_clips)} clips ({len(pinned_clips)} pinned)")
                
                # Callback de succès dans le thread principal
                def on_success(result):
                    self.window.clips = all_clips  # Stocke pour download_all_project
                    self.window.clips_panel.load_clips(project_name, all_clips)
                
                # Exécute dans le thread principal
                self.window.root.after(0, lambda: on_success(all_clips))
                
            except Exception as e:
                self.window.log(f"❌ Erreur chargement projet: {e}")
                traceback.print_exc()
        
        # Lance dans un thread
        import threading
        thread = threading.Thread(target=load_task, daemon=True)
        thread.start()
    
    def download_all_projects(self):
        """Télécharge tous les clips de tous les projets"""
        if not self.window.projects:
            messagebox.showwarning(
                self.window.lang.get('common.warning'),
                self.window.lang.get('warnings.no_projects')
            )
            return
        
        total_count = sum(p.get('clip_count', 0) for p in self.window.projects)
        
        result = messagebox.askyesno(
            self.window.lang.get('dialogs.confirm_download_all_title'),
            self.window.lang.get('dialogs.confirm_download_all', 
                                project_count=len(self.window.projects),
                                clip_count=total_count)
        )
        
        if result:
            self.window.log(f"📥 Démarrage téléchargement global...")
            # TODO: Implémenter
    
    def download_all_project(self):
        """Ajoute tous les clips du projet actuel à la liste de téléchargement"""
        clips = getattr(self.window, 'clips', [])
        
        if not clips:
            messagebox.showinfo("Info", "Aucun clip chargé")
            return
        
        result = messagebox.askyesno(
            "Confirmer",
            f"Ajouter tous les {len(clips)} clips de ce projet à la liste de téléchargement ?"
        )
        
        if result:
            self.window.log(f"📥 Ajout de {len(clips)} clips à télécharger...")
            
            added_count = 0
            for clip_data in clips:
                if self.window.player_panel.download_manager.add(clip_data):
                    added_count += 1
            
            self.window.log(f"✅ {added_count} clip(s) ajouté(s) à la liste de téléchargement !")
            
            if added_count > 0:
                messagebox.showinfo(
                    "Clips ajoutés",
                    f"✅ {added_count} clip(s) ajouté(s) à la liste !\n\n"
                    f"💡 Clique sur 'Télécharger' pour lancer le téléchargement."
                )
    
    def download_checked(self, checked_clips):
        """Ajoute les clips cochés à la liste de téléchargement"""
        if not checked_clips:
            messagebox.showinfo("Info", "Aucun clip sélectionné")
            return
        
        # ⭐ IMPORTANT : Définit le workspace AVANT d'ajouter les clips
        if self.window.current_project:
            workspace_name = self.window.current_project.get('name', 'Unknown')
            self.window.player_panel.set_workspace(workspace_name)
        
        self.window.log(f"📥 Ajout de {len(checked_clips)} clip(s) à télécharger...")
        
        # Ajoute chaque clip au download_manager
        added_count = 0
        for clip_data in checked_clips:
            if self.window.player_panel.download_manager.add(clip_data):
                added_count += 1
        
        self.window.log(f"✅ {added_count} clip(s) ajouté(s) à la liste de téléchargement !")
        
        if added_count > 0:
            messagebox.showinfo(
                "Clips ajoutés",
                f"✅ {added_count} clip(s) ajouté(s) à la liste !\n\n"
                f"💡 Clique sur 'Télécharger' pour lancer le téléchargement."
            )
    
    def add_to_playlist(self, clip_data):
        """Ajoute un clip à la playlist"""
        self.window.player_panel.add_to_playlist(clip_data, self.window.current_project.get('name', 'Unknown'))
    
    def add_to_download(self, clip_data):
        """Ajoute un clip à la liste de téléchargement"""
        self.window.player_panel.download_manager.add(clip_data)
    
    def sync_project(self):
        """SYNC d'un seul workspace"""
        # Code similaire à sync_all_non_synced mais pour 1 seul projet
        pass
    
    def sync_all_non_synced(self):
        """
        SYNC automatique de tous les workspaces non-syncés (🔴 ROUGE et 🟡 JAUNE)
        
        Pour chaque workspace :
        1. Récupère clips API (triés par date)
        2. Scanne Downloads + Musik
        3. Renumérote les fichiers existants
        4. Copie les MP3 au bon endroit
        5. Ajoute les clips manquants à download queue
        6. Génère cleanup_XXX.bat
        """
        if not self.window.client:
            self.window.log("⚠️ Client non initialisé")
            return
        
        self.window.log("")
        self.window.log("=" * 60)
        self.window.log("🔄 SYNC ALL NON-SYNCED")
        self.window.log("=" * 60)
        
        # Récupère tous les projets
        all_projects = self.window.projects
        
        if not all_projects:
            self.window.log("⚠️ Aucun projet chargé")
            return
        
        # Trouve les workspaces non-syncés (ROUGE + JAUNE)
        non_synced = []
        
        for project in all_projects:
            project_name = project.get('name', 'Unknown')
            clip_count = project.get('clip_count', 0)
            
            # Utilise la même logique que projects_panel
            status = self.window.projects_panel._check_folder_status(project_name, clip_count)
            
            if status in ('no_folder', 'need_sync'):
                non_synced.append(project)
        
        if not non_synced:
            self.window.log("✅ Tous les workspaces sont déjà syncés !")
            messagebox.showinfo("SYNC", "✅ Tous les workspaces sont déjà syncés !")
            return
        
        self.window.log(f"📊 {len(non_synced)} workspace(s) à synchroniser")
        
        # Confirmation
        result = messagebox.askyesno(
            "SYNC All Non-Synced",
            f"⚠️  Synchroniser {len(non_synced)} workspace(s) non-syncé(s) ?\n\n"
            f"Cela va :\n"
            f"• Analyser chaque workspace\n"
            f"• Copier les fichiers existants au bon numéro\n"
            f"• Ajouter les clips manquants à télécharger\n"
            f"• Générer des scripts .bat de nettoyage\n\n"
            f"Continuer ?",
            icon='question'
        )
        
        if not result:
            self.window.log("❌ Synchronisation annulée")
            return
        
        # SYNC chaque workspace
        def sync_all_task():
            from mutagen.mp3 import MP3
            from config import DOWNLOADS_PATH, MUSIK_LIBRARY_PATH
            import time
            
            total = len(non_synced)
            total_copied = 0
            total_to_download = 0
            total_bat_files = 0
            
            for index, project in enumerate(non_synced, 1):
                project_id = project.get('id', '')
                project_name = project.get('name', 'Unknown')
                
                self.window.log("")
                self.window.log(f"[{index}/{total}] 🔄 SYNC : {project_name}")
                
                try:
                    # 1️⃣ Récupère TOUS les clips de l'API
                    self.window.log(f"  📡 Récupération...")
                    
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
                        self.window.log(f"  ⚠️ Aucun clip")
                        continue
                    
                    self.window.log(f"  ✅ {len(all_clips)} clip(s) API")
                    
                    # 2️⃣ TRI PAR DATE (plus vieux en premier)
                    all_clips.sort(key=lambda x: x.get('clip', {}).get('created_at', ''))
                    
                    # 3️⃣ Scanne les fichiers locaux
                    local_files = {}  # {clip_id: filepath}
                    local_files_data = []  # [(clip_id, filepath, date)]
                    
                    def scan_folder(folder_path):
                        if not folder_path.exists():
                            return
                        
                        for file in folder_path.rglob('*.mp3'):
                            try:
                                audio = MP3(file)
                                clip_id = None
                                date = None
                                
                                # Extrait l'ID
                                if 'TSRC' in audio.tags:
                                    clip_id = str(audio.tags['TSRC'])
                                elif 'COMM::eng' in audio.tags:
                                    clip_id = str(audio.tags['COMM::eng'])
                                elif 'TXXX:SUNO_ID' in audio.tags:
                                    clip_id = str(audio.tags['TXXX:SUNO_ID'])
                                
                                # Extrait la date
                                if 'TDRC' in audio.tags:
                                    date = str(audio.tags['TDRC'])
                                
                                if clip_id:
                                    local_files[clip_id] = str(file)
                                    local_files_data.append((clip_id, str(file), date or ''))
                            except:
                                pass
                    
                    def renumber_files(folder_path):
                        """Renumérote les fichiers du dossier par ordre chronologique"""
                        if not folder_path.exists():
                            return 0
                        
                        # Récupère tous les fichiers de CE dossier
                        folder_files = [(cid, fp, dt) for cid, fp, dt in local_files_data 
                                        if str(folder_path) in fp]
                        
                        if not folder_files:
                            return 0
                        
                        # Trie par date (plus vieux en premier)
                        folder_files.sort(key=lambda x: x[2])
                        
                        renamed_count = 0
                        
                        for expected_num, (clip_id, filepath, date) in enumerate(folder_files, 1):
                            file_path = Path(filepath)
                            
                            # Extrait le numéro actuel du nom de fichier
                            match = re.search(r'01-(\d{3})', file_path.name)
                            if not match:
                                continue
                            
                            current_num = int(match.group(1))
                            
                            # Si le numéro est incorrect
                            if current_num != expected_num:
                                # Génère le nouveau nom
                                new_name = re.sub(r'01-\d{3}', f'01-{expected_num:03d}', file_path.name)
                                new_path = file_path.parent / new_name
                                
                                # Renomme
                                try:
                                    file_path.rename(new_path)
                                    renamed_count += 1
                                    
                                    # Met à jour local_files
                                    local_files[clip_id] = str(new_path)
                                    
                                    self.window.log(f"    🔄 Renommé : {current_num:03d} → {expected_num:03d} - {file_path.name[:40]}")
                                except Exception as e:
                                    self.window.log(f"    ❌ Erreur renommage : {e}")
                        
                        return renamed_count
                    
                    # Sanitize le nom du workspace
                    safe_name = re.sub(r'[<>:"/\\|?*]', '-', project_name).strip()
                    if len(safe_name) > 80:
                        safe_name = safe_name[:80]
                    
                    # Scanne Downloads
                    downloads_folder = Path(DOWNLOADS_PATH) / f"Suno-{safe_name}"
                    scan_folder(downloads_folder)
                    
                    # Scanne Musik EXACT
                    musik_path = Path(MUSIK_LIBRARY_PATH)
                    if musik_path.exists():
                        exact_folder = musik_path / f"Suno-{safe_name}"
                        if exact_folder.exists() and exact_folder.is_dir():
                            scan_folder(exact_folder)
                    
                    # 4️⃣ Renumérote les fichiers existants
                    renamed = renumber_files(downloads_folder)
                    if renamed > 0:
                        self.window.log(f"  🔄 {renamed} fichier(s) renumeroté(s)")
                    
                    if musik_path.exists():
                        exact_folder = musik_path / f"Suno-{safe_name}"
                        if exact_folder.exists():
                            renamed = renumber_files(exact_folder)
                            if renamed > 0:
                                self.window.log(f"  🔄 Musik : {renamed} fichier(s) renumeroté(s)")
                    
                    self.window.log(f"  📂 {len(local_files)} local(aux)")
                    
                    # 5️⃣ Pour chaque clip (dans l'ordre chronologique)
                    to_copy = []
                    to_download = []
                    files_to_delete_ids = set()  # ⭐ Stocke les IDs, pas les paths !
                    
                    downloads_folder.mkdir(parents=True, exist_ok=True)
                    
                    for clip_index, clip_data in enumerate(all_clips, 1):
                        clip = clip_data.get('clip', {})
                        clip_id = clip.get('id', '')
                        title = clip.get('title', 'Sans titre')
                        is_pinned = clip_data.get('is_pinned', False)
                        
                        # Nom cible
                        safe_title = re.sub(r'[<>:"/\\|?*]', '-', title).strip()
                        if len(safe_title) > 80:
                            safe_title = safe_title[:80]
                        
                        track_str = f"{clip_index:03d}"
                        id_short = clip_id[:8]
                        upload_suffix = "_UPLOADED" if is_pinned else ""
                        target_filename = f"01-{track_str} {safe_title} ({id_short}){upload_suffix}.mp3"
                        target_path = downloads_folder / target_filename
                        
                        # Si le MP3 existe déjà
                        if clip_id in local_files:
                            source_path = local_files[clip_id]
                            
                            # Si déjà au bon endroit
                            if Path(source_path) == target_path:
                                pass  # OK
                            else:
                                # Copier
                                to_copy.append((source_path, target_filename, clip_id))
                                
                                # Si source dans Musik, noter pour suppression
                                if "Musik" in source_path or "musik" in source_path.lower():
                                    files_to_delete_ids.add(clip_id)  # ⭐ Stocke l'ID
                        else:
                            # À télécharger
                            to_download.append(clip_data)
                    
                    # 6️⃣ Effectue les copies
                    if to_copy:
                        self.window.log(f"  📋 Copie de {len(to_copy)} fichier(s)...")
                        
                        for source_path, target_filename, clip_id in to_copy:
                            target_path = downloads_folder / target_filename
                            
                            # Skip si déjà présent
                            if target_path.exists():
                                continue
                            
                            try:
                                shutil.copy2(source_path, target_path)
                                total_copied += 1
                            except Exception as e:
                                self.window.log(f"    ❌ Erreur copie : {e}")
                    
                    # 7️⃣ Génère le fichier .bat de nettoyage
                    if files_to_delete_ids:
                        # .bat dans le dossier principal Downloads/
                        bat_path = Path(DOWNLOADS_PATH) / f"cleanup_{safe_name}.bat"
                        
                        with open(bat_path, 'w', encoding='utf-8') as f:
                            f.write("@echo off\n")
                            f.write("chcp 65001 >nul\n")  # ⭐ Force UTF-8
                            f.write(f"echo Nettoyage des doublons pour : {project_name}\n")
                            f.write("echo.\n")
                            
                            # ⭐ Récupère les chemins ACTUELS (après renommage)
                            for clip_id in files_to_delete_ids:
                                if clip_id in local_files:
                                    file_path = local_files[clip_id]  # Chemin mis à jour !
                                    win_path = str(Path(file_path)).replace('/', '\\')
                                    f.write(f'del "{win_path}"\n')
                            
                            f.write("echo.\n")
                            f.write(f"echo {len(files_to_delete_ids)} fichier(s) supprime(s) !\n")
                            f.write("pause\n")
                        
                        total_bat_files += 1
                        self.window.log(f"  📄 .bat créé ({len(files_to_delete_ids)} doublons)")
                    
                    # 8️⃣ Ajoute les clips à télécharger
                    if to_download:
                        def add_to_queue():
                            for clip_data in to_download:
                                # Stocke le workspace dans le clip_data
                                clip_data['_workspace_name'] = safe_name
                                self.window.player_panel.download_manager.add(clip_data)
                        
                        self.window.root.after(0, add_to_queue)
                        total_to_download += len(to_download)
                        self.window.log(f"  📥 {len(to_download)} à DL")
                    
                    self.window.log(f"  ✅ Terminé ({len(to_copy)} copiés, {len(to_download)} à DL)")
                    
                    # Petit délai
                    time.sleep(0.3)
                
                except Exception as e:
                    self.window.log(f"  ❌ Erreur : {e}")
                    import traceback
                    traceback.print_exc()
            
            # 9️⃣ Message final
            def show_final():
                self.window.log("")
                self.window.log("=" * 60)
                self.window.log(f"✅ SYNC ALL TERMINÉ")
                self.window.log(f"📊 {total} workspace(s) traité(s)")
                self.window.log(f"📋 {total_copied} fichier(s) copié(s)")
                self.window.log(f"📥 {total_to_download} clip(s) à télécharger")
                if total_bat_files > 0:
                    self.window.log(f"📄 {total_bat_files} fichier(s) .bat créé(s)")
                self.window.log("=" * 60)
                
                msg = f"✅ SYNC ALL Terminé !\n\n"
                msg += f"📊 {total} workspace(s) traité(s)\n"
                msg += f"📋 {total_copied} fichier(s) copié(s)\n"
                msg += f"📥 {total_to_download} clip(s) ajouté(s) à télécharger\n"
                
                if total_bat_files > 0:
                    msg += f"\n📄 {total_bat_files} fichier(s) .bat créé(s)\n"
                    msg += f"💡 Exécute les .bat pour supprimer les doublons"
                
                messagebox.showinfo("SYNC ALL Terminé", msg)
                
                # Rafraîchit les couleurs
                if hasattr(self.window.projects_panel, 'refresh_colors'):
                    self.window.projects_panel.refresh_colors()
            
            self.window.root.after(0, show_final)
        
        # Lance dans un thread
        import threading
        sync_thread = threading.Thread(target=sync_all_task, daemon=True)
        sync_thread.start()