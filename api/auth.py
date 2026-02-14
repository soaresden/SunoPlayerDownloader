"""
Gestion de l'authentification et des cookies Suno
"""
import json
from pathlib import Path
from typing import Dict, Optional
from config import COOKIES_FILE, DEFAULT_DEVICE_ID


class AuthManager:
    """Gestionnaire d'authentification"""
    
    def __init__(self, cookies_file: str = COOKIES_FILE):
        """
        Args:
            cookies_file: Chemin vers suno_cookies.json
        """
        self.cookies_file = cookies_file
        self.jwt_token: Optional[str] = None
        self.device_id: str = DEFAULT_DEVICE_ID
    
    def load_from_file(self, filepath: str = None) -> bool:
        """
        Charge les credentials depuis un fichier JSON
        
        Args:
            filepath: Chemin vers le fichier (optionnel)
            
        Returns:
            True si chargement réussi
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si le token est vide
        """
        path = Path(filepath or self.cookies_file)
        
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            credentials = json.load(f)
        
        # ⭐ SUPPORTE PLUSIEURS FORMATS
        # Format 1: jwt_token direct (ancien)
        self.jwt_token = credentials.get('jwt_token', '')
        
        # Format 2: __session (nouveau bookmarklet)
        if not self.jwt_token:
            self.jwt_token = credentials.get('__session', '')
        
        # Format 3: __client (très ancien)
        if not self.jwt_token:
            self.jwt_token = credentials.get('__client', '')
        
        # Device ID
        self.device_id = credentials.get('device_id') or \
                        credentials.get('suno_device_id') or \
                        credentials.get('ajs_anonymous_id') or \
                        DEFAULT_DEVICE_ID
        
        if not self.jwt_token:
            raise ValueError("Token JWT vide dans le fichier")
        
        # Sauvegarde le chemin du fichier
        self.cookies_file = str(path)
        
        return True
    
    def reload(self) -> bool:
        """
        Recharge les credentials depuis le dernier fichier utilisé
        
        Returns:
            True si rechargement réussi
        """
        return self.load_from_file(self.cookies_file)
    
    def is_authenticated(self) -> bool:
        """Vérifie si on est authentifié"""
        return bool(self.jwt_token)
    
    def get_headers(self) -> Dict[str, str]:
        """
        Retourne les headers HTTP pour les requêtes API
        
        Returns:
            Dict avec Authorization et device-id
        """
        if not self.is_authenticated():
            raise ValueError("Non authentifié - chargez d'abord les cookies")
        
        return {
            'Authorization': f'Bearer {self.jwt_token}',
            'device-id': self.device_id
        }
    
    def clear(self):
        """Efface les credentials"""
        self.jwt_token = None
        self.device_id = DEFAULT_DEVICE_ID