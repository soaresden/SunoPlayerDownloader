"""
Panel d'affichage des projets avec chargement progressif et codes couleur
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable
import threading
import os
from pathlib import Path
from config import *
from utils.formatters import format_date
from utils.treeview_sorter import make_treeview_sortable


class ProjectsPanel(tk.Frame):
    """Panel contenant la liste des projets"""
    
    def __init__(self, parent, on_select, on_download_all, on_sync, on_sync_all_non_synced, lang_manager):
        """
        Args:
            parent: Widget parent
            on_select: Callback de sélection d'un projet
            on_download_all: Callback pour tout télécharger
            on_sync: Callback pour sync (delta)
            lang_manager: Gestionnaire de langues
        """
        super().__init__(parent, bg=COLOR_PRIMARY)
        
        self.on_select = on_select
        self.callbacks = {
            'on_download_all': on_download_all,
            'on_sync': on_sync,
            'on_sync_all_non_synced': on_sync_all_non_synced  # ⭐ NOUVEAU
        }

        self.lang = lang_manager
        
        # Variables
        self.client = None  # Sera défini par set_client()
        self.all_projects = []  # Pour le menu contextuel - IMPORTANT !
        self.item_to_project = {}  # item_id -> project_id
        
        # Header
        self._create_header()
        
        # TreeView
        self._create_treeview()
    
    def _create_header(self):
        """Crée le header"""
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        self.title_label = tk.Label(
            header,
            text=self.lang.get('projects.title'),
            font=("Arial", 10, "bold"),
            bg=COLOR_PRIMARY,
            fg="white"
        )
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        self.count_label = tk.Label(
            header,
            text="",
            font=("Arial", 8),
            bg=COLOR_PRIMARY,
            fg="#bdc3c7"
        )
        self.count_label.pack(side=tk.RIGHT, padx=5)
        
        # Indicateur de chargement
        self.loading_label = tk.Label(
            header,
            text="",
            font=("Arial", 8),
            bg=COLOR_PRIMARY,
            fg=COLOR_INFO
        )
        self.loading_label.pack(side=tk.RIGHT, padx=5)
        
        # Boutons
        btn_frame = tk.Frame(self, bg=COLOR_PRIMARY, height=35)
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        btn_frame.pack_propagate(False)
        
        # Boutons - 3 boutons verticaux
        btn_frame = tk.Frame(self, bg=COLOR_PRIMARY)
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        # SYNC SELECTED
        tk.Button(
            btn_frame,
            text=self.lang.get("projects.buttons.sync"),
            font=("Arial", 8, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=5,
            command=self.callbacks.get('on_sync')
        ).pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        # ⭐ NOUVEAU : SYNC ALL NON-SYNCED
        tk.Button(
            btn_frame,
            text=self.lang.get("projects.buttons.sync_all_non_synced"),
            font=("Arial", 8, "bold"),
            bg="#ff8800",  # Orange
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=5,
            command=self.callbacks.get('on_sync_all_non_synced')
        ).pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        # DOWNLOAD ALL
        tk.Button(
            btn_frame,
            text=self.lang.get("projects.buttons.download_all"),
            font=("Arial", 8, "bold"),
            bg=COLOR_SUNO_ORANGE,
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=5,
            command=self.callbacks.get('on_download_all')
        ).pack(side=tk.TOP, fill=tk.X)

    
    def _create_treeview(self):
        """Crée le TreeView"""
        proj_cont = tk.Frame(self, bg="white", bd=1, relief=tk.SOLID)
        proj_cont.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        proj_vsb = ttk.Scrollbar(proj_cont)
        proj_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(
            proj_cont,
            columns=("workspace", "count", "created", "updated"),
            show="headings",
            yscrollcommand=proj_vsb.set,
            selectmode="browse",
            height=25
        )
        proj_vsb.config(command=self.tree.yview)
        
        # Colonnes
        self.tree.heading("workspace", text=self.lang.get('projects.columns.workspace'))
        self.tree.heading("count", text=self.lang.get('projects.columns.count'))
        self.tree.heading("created", text=self.lang.get('projects.columns.created'))
        self.tree.heading("updated", text=self.lang.get('projects.columns.updated'))
        
        # Largeurs ajustées
        self.tree.column("workspace", width=150)
        self.tree.column("count", width=30, anchor=tk.CENTER)
        self.tree.column("created", width=85)
        self.tree.column("updated", width=85)
        
        # ⭐ TAGS COLORÉS
        # 🔴 ROUGE : Dossier n'existe pas → À télécharger
        self.tree.tag_configure('no_folder', background='#ffcccc', foreground='#cc0000')
        
        # 🟡 JAUNE : Dossier existe mais nombre différent → À SYNC
        self.tree.tag_configure('need_sync', background='#ffffcc', foreground='#cc9900')
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Active le tri
        self._setup_sorting()
        
        # Bind de sélection
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
    
    def _setup_sorting(self):
        """Active le tri"""
        self.sorter = make_treeview_sortable(self.tree, {
            'workspace': {'type': 'text', 'reverse': False},
            'count': {'type': 'number', 'reverse': True},
            'created': {'type': 'date', 'reverse': True},
            'updated': {'type': 'date', 'reverse': True}
        })
    
    def _format_datetime(self, iso_date: str) -> str:
        """
        Formate une date ISO en dd/mm/yy hh:mm
        
        Args:
            iso_date: Date au format ISO (ex: "2026-01-22T00:37:05.593Z")
        
        Returns:
            Date formatée (ex: "22/01/26 00:37")
        """
        if not iso_date:
            return '-'
        
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%y %H:%M')
        except:
            return '-'
    
    def _get_oldest_clip_date(self, clips: List[Dict]) -> str:
        """
        Trouve la date du clip le plus ancien
        
        Args:
            clips: Liste des clips du projet (structure imbriquée)
        
        Returns:
            Date ISO du clip le plus ancien
        """
        if not clips:
            return ''
        
        oldest_date = None
        
        for clip_item in clips:
            # Structure imbriquée : {"clip": {...}, "pinned": False, ...}
            clip = clip_item.get('clip', {})
            created = clip.get('created_at', '')
            
            if created:
                if oldest_date is None or created < oldest_date:
                    oldest_date = created
        
        return oldest_date or ''
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Nettoie un nom de fichier (même algo que audio_cache)
        """
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
        if len(filename) > 80:
            filename = filename[:80]
        return filename.strip()
    
    def _count_mp3_in_folder(self, folder_path: Path) -> int:
        """
        Compte le nombre de MP3 dans un dossier
        
        Args:
            folder_path: Chemin du dossier
        
        Returns:
            Nombre de fichiers MP3
        """
        if not folder_path.exists():
            return 0
        
        count = 0
        try:
            for file in folder_path.iterdir():
                if file.is_file() and file.suffix.lower() == '.mp3':
                    count += 1
        except:
            pass
        
        return count
    
    def _check_folder_status(self, workspace_name: str, clip_count: int) -> str:
        """
        Vérifie le statut d'un workspace
        
        Args:
            workspace_name: Nom du workspace
            clip_count: Nombre de clips sur Suno
        
        Returns:
            'ok' = Tout bon (même nombre)
            'need_sync' = Dossier existe mais nombre différent → JAUNE
            'no_folder' = Dossier n'existe pas → ROUGE
        """
        safe_name = self._sanitize_filename(workspace_name)
        
        # Cherche dans DOWNLOADS
        downloads_folder = Path(DOWNLOADS_PATH) / f"Suno-{safe_name}"
        
        # Cherche dans MUSIK (dossiers Suno*)
        musik_folders = []
        if Path(MUSIK_LIBRARY_PATH).exists():
            for folder in Path(MUSIK_LIBRARY_PATH).iterdir():
                if folder.is_dir() and folder.name.lower().startswith('suno'):
                    # Vérifie si le nom du workspace est dans le nom du dossier
                    if safe_name.lower() in folder.name.lower():
                        musik_folders.append(folder)
        
        # Compte les MP3 dans tous les dossiers trouvés
        total_mp3 = 0
        
        if downloads_folder.exists():
            total_mp3 += self._count_mp3_in_folder(downloads_folder)
        
        for musik_folder in musik_folders:
            total_mp3 += self._count_mp3_in_folder(musik_folder)
        
        # Décision
        if total_mp3 == 0:
            # Aucun MP3 trouvé → ROUGE
            return 'no_folder'
        elif total_mp3 != clip_count:
            # Nombre différent → JAUNE (à sync)
            return 'need_sync'
        else:
            # Même nombre → OK
            return 'ok'
    
    def load_projects(self, projects: List[Dict]):
        """
        Charge les projets dans le TreeView
        Affiche rapidement puis charge les clips en arrière-plan
        
        Args:
            projects: Liste des projets (sans clips au départ)
        """
        # ⭐ IMPORTANT : Sauvegarde pour le menu contextuel
        self.all_projects = projects
        
        # Efface
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_to_project.clear()
        
        # Affiche rapidement avec "⏳" pour created
        for project in projects:
            project_id = project.get('id', '')
            name = project.get('name', 'Sans nom')
            count = project.get('clip_count', 0)
            
            # Updated disponible immédiatement
            updated_raw = project.get('last_updated_clip', '')
            updated = self._format_datetime(updated_raw)
            
            # Created = "⏳" au départ (sera chargé en arrière-plan)
            created = '⏳'
            
            # ⭐ NOUVEAU : Vérifie le statut (rouge/jaune/ok)
            status = self._check_folder_status(name, count)
            
            # Insère dans le TreeView avec le bon tag
            if status == 'no_folder':
                # 🔴 ROUGE : Dossier n'existe pas
                item_id = self.tree.insert('', 'end', values=(name, count, created, updated), tags=('no_folder',))
            elif status == 'need_sync':
                # 🟡 JAUNE : Nombre différent
                item_id = self.tree.insert('', 'end', values=(name, count, created, updated), tags=('need_sync',))
            else:
                # ⚫ NORMAL : Tout OK
                item_id = self.tree.insert('', 'end', values=(name, count, created, updated))
            
            # Sauvegarde l'association item_id -> project_id
            self.item_to_project[item_id] = project_id
        
        self.count_label.config(text=str(len(projects)))
        
        # Lance le chargement en arrière-plan
        if self.client:
            self._load_clips_background(projects)
    
    def _load_clips_background(self, projects: List[Dict]):
        """
        Charge les clips de chaque projet en arrière-plan
        
        Args:
            projects: Liste des projets
        """
        def worker():
            total = len(projects)
            
            for index, project in enumerate(projects, 1):
                project_id = project.get('id', '')
                
                if not project_id:
                    continue
                
                try:
                    # Appelle l'API pour récupérer les clips
                    clips_data = self.client.get_project_clips(project_id)
                    clips = clips_data.get('project_clips', [])
                    
                    # Trouve le clip le plus ancien
                    oldest_date = self._get_oldest_clip_date(clips)
                    created = self._format_datetime(oldest_date)
                    
                    # Met à jour le TreeView (dans le thread principal)
                    self.after(0, lambda pid=project_id, c=created, i=index, t=total: 
                              self._update_project_created(pid, c, i, t))
                
                except Exception as e:
                    # En cas d'erreur, met "-"
                    self.after(0, lambda pid=project_id, i=index, t=total: 
                              self._update_project_created(pid, '-', i, t))
            
            # Termine
            self.after(0, lambda: self.loading_label.config(text="✅ Terminé"))
            self.after(2000, lambda: self.loading_label.config(text=""))
        
        # Lance le thread
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _update_project_created(self, project_id: str, created: str, current: int, total: int):
        """
        Met à jour la colonne Created d'un projet
        
        Args:
            project_id: ID du projet
            created: Date formatée
            current: Index actuel
            total: Nombre total
        """
        # Met à jour le label de chargement
        self.loading_label.config(text=f"⏳ {current}/{total}")
        
        # Trouve l'item_id depuis le project_id
        item_id = None
        for iid, pid in self.item_to_project.items():
            if pid == project_id:
                item_id = iid
                break
        
        if not item_id:
            return
        
        # Récupère les valeurs actuelles
        values = list(self.tree.item(item_id, 'values'))
        
        # Met à jour la colonne created (index 2)
        values[2] = created
        
        # Applique
        self.tree.item(item_id, values=values)
    
    def _on_select(self, event):
        """Appelé quand un projet est sélectionné"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            
            # Récupère le vrai project_id
            project_id = self.item_to_project.get(item_id)
            
            if project_id:
                self.on_select(project_id)
    
    def update_texts(self):
        """Met à jour les textes après changement de langue"""
        self.title_label.config(text=self.lang.get('projects.title'))
        
        # Met à jour les headers
        self.tree.heading("workspace", text=self.lang.get('projects.columns.workspace'))
        self.tree.heading("count", text=self.lang.get('projects.columns.count'))
        self.tree.heading("created", text=self.lang.get('projects.columns.created'))
        self.tree.heading("updated", text=self.lang.get('projects.columns.updated'))
    
    def set_client(self, client):
        """Définit le client API (appelé depuis main_window)"""
        self.client = client
    
    def _on_right_click(self, event):
        """
        Gère le clic droit sur un workspace
        Affiche le menu contextuel
        """
        from tkinter import Menu
        
        # Identifie l'item cliqué
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        
        # Sélectionne l'item
        self.tree.selection_set(item_id)
        
        # Récupère les infos du projet
        project_id = self.item_to_project.get(item_id)
        if not project_id:
            return
        
        # Trouve le projet complet
        project = None
        for p in self.all_projects:
            if p.get('id') == project_id:
                project = p
                break
        
        if not project:
            print(f"⚠️ Projet non trouvé dans all_projects : {project_id}")
            return
        
        # Crée le menu contextuel
        menu = Menu(self, tearoff=0)
        
        menu.add_command(
            label=f"✏️  {self.lang.get('workspace_menu.rename')}",
            command=lambda: self._rename_workspace(project)
        )
        
        menu.add_separator()
        
        menu.add_command(
            label=f"🗑️  {self.lang.get('workspace_menu.delete')}",
            command=lambda: self._delete_workspace(project)
        )
        
        # Affiche le menu
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _rename_workspace(self, project_id: str):
        """Renomme un workspace"""
        from tkinter import simpledialog
        
        # Trouve le projet
        project = None
        for p in self.all_projects:
            if p.get('id') == project_id:
                project = p
                break
        
        if not project:
            return
        
        current_name = project.get('name', 'Unknown')
        
        # ⭐ Popup avec nom pré-rempli
        new_name = simpledialog.askstring(
            "Renommer le workspace",
            f"Nom actuel: {current_name}\n\nNouveau nom:",
            initialvalue=current_name  # ⭐ IMPORTANT
        )
        
        if not new_name or new_name == current_name:
            return
        
        # Met à jour localement
        project['name'] = new_name
        self.load_projects(self.all_projects)
        
        self.log(f"✅ Renommé : {current_name} → {new_name}")
        messagebox.showinfo("Succès", f"✅ Workspace renommé\n\n{current_name} → {new_name}")
    
    def _delete_workspace(self, project: dict):
        """Dialogue pour supprimer un workspace"""
        from tkinter import messagebox
        
        project_id = project.get('id')
        project_name = project.get('name', 'Unknown')
        clip_count = project.get('clip_count', 0)
        
        # Confirmation
        result = messagebox.askyesno(
            self.lang.get('workspace_menu.delete_title', 'Supprimer le workspace ?'),
            f"{self.lang.get('workspace_menu.workspace', 'Workspace')} : {project_name}\n"
            f"{self.lang.get('workspace_menu.clips', 'Clips')} : {clip_count}\n\n"
            f"⚠️  {self.lang.get('workspace_menu.warning_irreversible', 'Cette action est IRRÉVERSIBLE !')}\n\n"
            f"{self.lang.get('workspace_menu.confirm_delete', 'Confirmer la suppression ?')}",
            icon='warning'
        )
        
        if not result:
            return
        
        # Supprime via API
        try:
            print(f"🗑️  Suppression du workspace : '{project_name}'")
            
            if self.client:
                success = self.client.delete_project(project_id)
                
                if success:
                    print(f"✅ Workspace supprimé : '{project_name}'")
                    
                    messagebox.showinfo(
                        self.lang.get('workspace_menu.success', 'Succès'),
                        f"{self.lang.get('workspace_menu.deleted', 'Workspace supprimé')} :\n'{project_name}'"
                    )
                    
                    # Recharge la liste des projets
                    self.master.after(500, lambda: self._refresh_projects())
                else:
                    raise Exception("Aucune méthode de suppression n'a fonctionné")
            else:
                messagebox.showerror("Erreur", "Client API non disponible")
        
        except Exception as e:
            print(f"❌ Erreur suppression : {e}")
            messagebox.showerror(
                "Erreur",
                f"{self.lang.get('workspace_menu.error_delete', 'Erreur lors de la suppression')} :\n{e}"
            )
    
    def _refresh_projects(self):
        """Recharge la liste des projets après renommage/suppression"""
        if self.client:
            try:
                print("🔄 Rechargement de la liste des projets...")
                
                # Récupère les projets
                projects = self.client.get_all_projects()
                
                # Réaffiche
                self.load_projects(projects)
                
                print("✅ Liste rechargée")
            except Exception as e   :
                print(f"❌ Erreur rechargement : {e}")
    
    def refresh_colors(self):
        """Rafraîchit les couleurs de tous les workspaces"""
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if len(values) >= 2:
                workspace_name = values[0]
                clip_count_str = str(values[1])
                clip_count = int(clip_count_str) if clip_count_str.isdigit() else 0
                
                status = self._check_folder_status(workspace_name, clip_count)
                
                if status == 'ok':
                    self.tree.item(item, tags=('ok',))
                elif status == 'need_sync':
                    self.tree.item(item, tags=('need_sync',))
                else:
                    self.tree.item(item, tags=('no_folder',))
        
        # ✅ Pas de self.log (n'existe pas dans ProjectsPanel)