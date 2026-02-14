"""
Panel d'affichage des projets avec chargement progressif
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable
import threading
from config import *
from utils.formatters import format_date
from utils.treeview_sorter import make_treeview_sortable


class ProjectsPanel(tk.Frame):
    """Panel contenant la liste des projets"""
    
    def __init__(self, parent, on_select: Callable, on_download_all: Callable, on_sync: Callable, lang_manager):
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
            'on_sync': on_sync
        }
        self.lang = lang_manager
        
        # Map pour retrouver le project_id depuis l'item TreeView
        self.item_to_project = {}  # item_id -> project_id
        
        # Variable pour stocker le client
        self.client = None  # Sera défini par set_client()
        
        # Variable pour stocker tous les projets (pour menu contextuel)
        self.all_projects = []
        
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
        
        # SYNC
        tk.Button(
            btn_frame,
            text=self.lang.get("projects.buttons.sync"),
            font=("Arial", 9, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=6,
            command=self.callbacks.get('on_sync')
        ).pack(side=tk.LEFT, fill=tk.Y, expand=True, padx=(0, 2))
        
        # TOUT DL
        tk.Button(
            btn_frame,
            text=self.lang.get("projects.buttons.download_all"),
            font=("Arial", 9, "bold"),
            bg=COLOR_SUNO_ORANGE,
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=6,
            command=self.callbacks.get('on_download_all')
        ).pack(side=tk.RIGHT, fill=tk.Y, expand=True, padx=(2, 0))
    
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
        
        # ⭐ Largeurs ajustées
        self.tree.column("workspace", width=150)
        self.tree.column("count", width=30, anchor=tk.CENTER)
        self.tree.column("created", width=85)
        self.tree.column("updated", width=85)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Active le tri
        self._setup_sorting()
        
        # Bind de sélection
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # ⭐ NOUVEAU : Menu contextuel (clic droit)
        self.tree.bind('<Button-3>', self._on_right_click)  # Windows/Linux
        self.tree.bind('<Button-2>', self._on_right_click)  # Mac
    
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
    
    def load_projects(self, projects: List[Dict]):
        """
        Charge les projets dans le TreeView
        Affiche rapidement puis charge les clips en arrière-plan
        
        Args:
            projects: Liste des projets (sans clips au départ)
        """
        # Sauvegarde pour le menu contextuel
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
            created = '⏳'  # Indicateur de chargement
            
            # Insère dans le TreeView
            item_id = self.tree.insert('', 'end', values=(name, count, created, updated))
            
            # ⭐ Sauvegarde l'association item_id -> project_id
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
        
        # ⭐ Trouve l'item_id depuis le project_id
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
            
            # ⭐ CORRECTION : Récupère le vrai project_id
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
            return
        
        # Crée le menu contextuel
        menu = Menu(self, tearoff=0)
        
        menu.add_command(
            label=f"✏️  {self.lang.get('workspace_menu.rename', 'Renommer')}",
            command=lambda: self._rename_workspace(project)
        )
        
        menu.add_separator()
        
        menu.add_command(
            label=f"🗑️  {self.lang.get('workspace_menu.delete', 'Supprimer')}",
            command=lambda: self._delete_workspace(project)
        )
        
        # Affiche le menu
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _rename_workspace(self, project: dict):
        """Dialogue pour renommer un workspace"""
        from tkinter import simpledialog, messagebox
        
        project_id = project.get('id')
        old_name = project.get('name', 'Unknown')
        
        # Dialogue simple
        new_name = simpledialog.askstring(
            self.lang.get('workspace_menu.rename_title', 'Renommer le workspace'),
            f"{self.lang.get('workspace_menu.current_name', 'Nom actuel')} : {old_name}\n\n{self.lang.get('workspace_menu.new_name', 'Nouveau nom')} :",
            initialvalue=old_name
        )
        
        if not new_name or new_name == old_name:
            return
        
        # Renomme via API
        try:
            print(f"🔄 Renommage : '{old_name}' → '{new_name}'")
            
            if self.client:
                result = self.client.rename_project(project_id, new_name)
                
                print(f"✅ Workspace renommé : '{old_name}' → '{new_name}'")
                
                messagebox.showinfo(
                    self.lang.get('workspace_menu.success', 'Succès'),
                    f"{self.lang.get('workspace_menu.renamed', 'Workspace renommé')} :\n'{old_name}' → '{new_name}'"
                )
                
                # Recharge la liste des projets
                self.master.after(500, lambda: self._refresh_projects())
            else:
                messagebox.showerror(
                    "Erreur",
                    "Client API non disponible"
                )
        
        except Exception as e:
            print(f"❌ Erreur renommage : {e}")
            messagebox.showerror(
                "Erreur",
                f"{self.lang.get('workspace_menu.error_rename', 'Erreur lors du renommage')} :\n{e}"
            )
    
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
                messagebox.showerror(
                    "Erreur",
                    "Client API non disponible"
                )
        
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
            except Exception as e:
                print(f"❌ Erreur rechargement : {e}")