"""
Utilitaire pour ajouter le tri automatique aux TreeView
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Any


class TreeViewSorter:
    """Gère le tri des colonnes dans un TreeView"""
    
    def __init__(self, tree: ttk.Treeview):
        """
        Args:
            tree: Le TreeView à rendre triable
        """
        self.tree = tree
        self.sort_columns = {}  # {col: (reverse, sort_key_func)}
    
    def make_sortable(self, columns: dict):
        """
        Rend les colonnes triables
        
        Args:
            columns: Dict {
                'col_id': {
                    'type': 'text' | 'number' | 'date',
                    'reverse': False  # Ordre initial
                }
            }
        
        Exemple:
            sorter.make_sortable({
                'name': {'type': 'text'},
                'count': {'type': 'number'},
                'created': {'type': 'date'}
            })
        """
        for col_id, config in columns.items():
            col_type = config.get('type', 'text')
            reverse = config.get('reverse', False)
            
            # Fonction de tri selon le type
            if col_type == 'number':
                sort_key = self._number_sort_key
            elif col_type == 'date':
                sort_key = self._date_sort_key
            else:
                sort_key = self._text_sort_key
            
            self.sort_columns[col_id] = [reverse, sort_key]
            
            # Bind le clic sur le header
            self.tree.heading(
                col_id,
                command=lambda c=col_id: self._sort_by_column(c)
            )
    
    def _sort_by_column(self, col: str):
        """Trie par une colonne"""
        if col not in self.sort_columns:
            return
        
        # Récupère l'état actuel
        reverse, sort_key_func = self.sort_columns[col]
        
        # Récupère toutes les lignes
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Trie
        items.sort(key=lambda x: sort_key_func(x[0]), reverse=reverse)
        
        # Réorganise
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
        
        # Inverse l'ordre pour le prochain clic
        self.sort_columns[col][0] = not reverse
        
        # Met à jour le symbole dans le header
        self._update_header_symbol(col, reverse)
    
    def _update_header_symbol(self, col: str, was_reverse: bool):
        """Met à jour le symbole de tri dans le header"""
        # Récupère le texte actuel
        current_text = self.tree.heading(col)['text']
        
        # Retire les anciens symboles
        clean_text = current_text.replace(' ▲', '').replace(' ▼', '')
        
        # Ajoute le nouveau symbole
        if was_reverse:
            new_text = f"{clean_text} ▲"  # Maintenant ascendant
        else:
            new_text = f"{clean_text} ▼"  # Maintenant descendant
        
        self.tree.heading(col, text=new_text)
    
    def _text_sort_key(self, value: str) -> str:
        """Clé de tri pour texte (insensible à la casse)"""
        return str(value).lower()
    
    def _number_sort_key(self, value: str) -> float:
        """Clé de tri pour nombre"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0
    
    def _date_sort_key(self, value: str) -> str:
        """Clé de tri pour date (format DD/MM HH:MM)"""
        # Pour le format "31/01 20:47", on retourne tel quel
        # car Python trie bien les strings de dates
        return str(value)


def make_treeview_sortable(tree: ttk.Treeview, columns_config: dict):
    """
    Helper rapide pour rendre un TreeView triable
    
    Args:
        tree: Le TreeView
        columns_config: Config des colonnes (voir TreeViewSorter.make_sortable)
    
    Exemple:
        make_treeview_sortable(self.tree, {
            'workspace': {'type': 'text'},
            'count': {'type': 'number'},
            'created': {'type': 'date'},
            'updated': {'type': 'date'}
        })
    """
    sorter = TreeViewSorter(tree)
    sorter.make_sortable(columns_config)
    return sorter