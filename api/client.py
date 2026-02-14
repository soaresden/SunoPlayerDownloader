"""
Client API Suno - Version simplifiée pour la GUI
"""

import requests
import json
import time
import base64
from typing import List, Dict
from config import SUNO_BASE_URL
from utils.timestamp_parser import parse_relative_time


class SunoClient:
    """Client pour communiquer avec l'API Suno"""
    
    def __init__(self, jwt_token: str, device_id: str):
        """
        Args:
            jwt_token: JWT token d'authentification
            device_id: Device ID (UUID)
        """
        self.jwt_token = jwt_token
        self.device_id = device_id
        self.session = requests.Session()
        
        # Headers par défaut
        self.session.headers.update({
            "accept": "*/*",
            "authorization": f"Bearer {jwt_token}",
            "device-id": device_id,
            "origin": "https://suno.com",
            "referer": "https://suno.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def _get_browser_token(self) -> str:
        """Génère un browser token"""
        timestamp_ms = int(time.time() * 1000)
        token_data = json.dumps({"timestamp": timestamp_ms})
        return base64.b64encode(token_data.encode()).decode()
    
    def _add_browser_token(self):
        """Ajoute le browser token aux headers"""
        self.session.headers["browser-token"] = self._get_browser_token()
    
    def get_projects(self, page: int = 1) -> Dict:
        """
        Récupère une page de projets
        
        Args:
            page: Numéro de page
            
        Returns:
            Dict avec 'projects' et 'num_total_results'
        """
        self._add_browser_token()
        
        params = {
            'page': page,
            'sort': 'max_created_at_last_updated_clip',
            'show_trashed': 'false',
            'exclude_shared': 'false'
        }
        
        response = self.session.get(
            f"{SUNO_BASE_URL}/api/project/me",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_all_projects(self) -> List[Dict]:
        """
        Récupère tous les projets (toutes les pages)
        
        Returns:
            Liste de tous les projets
        """
        all_projects = []
        page = 1
        
        while True:
            data = self.get_projects(page=page)
            projects = data.get("projects", [])
            
            if not projects:
                break
            
            all_projects.extend(projects)
            total = data.get("num_total_results", 0)
            
            if len(all_projects) >= total:
                break
            
            page += 1
            time.sleep(0.3)  # Rate limiting
        
        return all_projects
    
    def get_project_clips(self, project_id: str) -> Dict:
        """
        Récupère les détails d'un projet avec tous ses clips
        
        Args:
            project_id: ID du projet
            
        Returns:
            Dict avec 'project_clips' et 'pinned_clips'
        """
        self._add_browser_token()
        
        response = self.session.get(f"{SUNO_BASE_URL}/api/project/{project_id}")
        response.raise_for_status()
        return response.json()
    
    def download_clip(self, clip_url: str, output_path: str) -> bool:
        """
        Télécharge un clip MP3
        
        Args:
            clip_url: URL du fichier MP3
            output_path: Chemin de destination
            
        Returns:
            True si réussi
        """
        try:
            response = requests.get(clip_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"Erreur téléchargement: {e}")
            return False
    
    def rename_project(self, project_id: str, new_name: str, description: str = "") -> dict:
        """
        Renomme un workspace/projet
        
        Args:
            project_id: ID du projet
            new_name: Nouveau nom
            description: Description (optionnel)
        
        Returns:
            Données du projet mis à jour
        """
        url = f"{SUNO_BASE_URL}/api/project/{project_id}/metadata"
        
        payload = {
            "name": new_name,
            "description": description or new_name
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def delete_project(self, project_id: str) -> bool:
        """
        Supprime un workspace/projet (met à la corbeille)
        
        Args:
            project_id: ID du projet
        
        Returns:
            True si succès
        """
        # Méthode 1 : Mettre à la corbeille (soft delete)
        url = f"{SUNO_BASE_URL}/api/project/{project_id}/trash"
        
        try:
            response = self.session.post(url, json={})
            response.raise_for_status()
            return True
        except:
            pass
        
        # Méthode 2 : DELETE direct
        url = f"{SUNO_BASE_URL}/api/project/{project_id}"
        
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return True
        except:
            pass
        
        # Méthode 3 : POST /metadata avec is_trashed
        url = f"{SUNO_BASE_URL}/api/project/{project_id}/metadata"
        
        try:
            response = self.session.post(url, json={"is_trashed": True})
            response.raise_for_status()
            return True
        except:
            pass
        
        return False