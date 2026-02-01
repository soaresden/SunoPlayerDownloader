"""
Panel d'affichage des projets
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable
from config import *
from utils.formatters import format_date


class ProjectsPanel(tk.Frame):
    """Panel contenant la liste des projets"""
    
    def __init__(self, parent, on_select: Callable, on_download_all: Callable, lang_manager):
        """
        Args:
            parent: Widget parent
            on_select: Callback de sélection d'un projet
            on_download_all: Callback pour tout télécharger
            lang_manager: Gestionnaire de langues
        """
        super().__init__(parent, bg=COLOR_PRIMARY)
        
        self.on_select = on_select
        self.on_download_all = on_download_all
        self.lang = lang_manager
        
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
        
        # ⭐ BOUTON TOUT TÉLÉCHARGER
        btn_frame = tk.Frame(self, bg=COLOR_PRIMARY, height=35)
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        btn_frame.pack_propagate(False)
        
        tk.Button(
            btn_frame,
            text="📥 TOUT TÉLÉCHARGER",
            font=("Arial", 9, "bold"),
            bg=COLOR_SUNO_ORANGE,
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=6,
            command=self.on_download_all
        ).pack(fill=tk.BOTH, expand=True)
    
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
        
        self.tree.column("workspace", width=180)
        self.tree.column("count", width=40, anchor=tk.CENTER)
        self.tree.column("created", width=80)
        self.tree.column("updated", width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind de sélection
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
    
    def load_projects(self, projects: List[Dict]):
        """
        Charge les projets dans le TreeView
        
        Args:
            projects: Liste des projets
        """
        # Efface
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ajoute
        for project in projects:
            pid = project.get('id', '')
            name = project.get('name', 'Sans nom')
            count = project.get('clip_count', 0)
            created = format_date(project.get('created_at', ''))
            updated = format_date(project.get('updated_at', ''))
            
            self.tree.insert("", tk.END, iid=pid,
                           values=(name, count, created, updated))
        
        self.count_label.config(text=str(len(projects)))
    
    def _on_select(self, event):
        """Appelé quand un projet est sélectionné"""
        selection = self.tree.selection()
        if selection:
            project_id = selection[0]
            self.on_select(project_id)
    
    def update_texts(self):
        """Met à jour les textes après changement de langue"""
        self.title_label.config(text=self.lang.get('projects.title'))
        
        # Met à jour les headers
        self.tree.heading("workspace", text=self.lang.get('projects.columns.workspace'))
        self.tree.heading("count", text=self.lang.get('projects.columns.count'))
        self.tree.heading("created", text=self.lang.get('projects.columns.created'))
        self.tree.heading("updated", text=self.lang.get('projects.columns.updated'))