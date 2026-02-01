"""
Gestionnaire de langues avec support JSON
"""

import json
from pathlib import Path
from typing import Dict, Optional


class LanguageManager:
    """Gestionnaire de traductions"""
    
    LANGUAGES = {
        'Français': 'french',
        'English': 'english'
    }
    
    def __init__(self, default_language: str = 'Français'):
        """
        Args:
            default_language: Langue par défaut
        """
        self.current_language = default_language
        self.translations: Dict = {}
        self.languages_dir = Path(__file__).parent.parent / 'languages'
        
        # Charge la langue par défaut
        self.load_language(default_language)
    
    def load_language(self, language: str) -> bool:
        """
        Charge un fichier de langue
        
        Args:
            language: Nom de la langue (Français, English)
            
        Returns:
            True si chargé avec succès
        """
        if language not in self.LANGUAGES:
            return False
        
        lang_file = self.LANGUAGES[language]
        filepath = self.languages_dir / f"{lang_file}.json"
        
        if not filepath.exists():
            print(f"⚠️ Fichier de langue introuvable: {filepath}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            
            self.current_language = language
            return True
        except Exception as e:
            print(f"❌ Erreur chargement langue: {e}")
            return False
    
    def get(self, key_path: str, **kwargs) -> str:
        """
        Récupère une traduction
        
        Args:
            key_path: Chemin de la clé (ex: "logs.app_started")
            **kwargs: Variables à formater
            
        Returns:
            Texte traduit
        """
        keys = key_path.split('.')
        value = self.translations
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, key_path)
            else:
                return key_path
        
        # Formatage si variables
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except:
                return value
        
        return value if isinstance(value, str) else key_path
    
    def get_available_languages(self) -> list:
        """Retourne la liste des langues disponibles"""
        return list(self.LANGUAGES.keys())