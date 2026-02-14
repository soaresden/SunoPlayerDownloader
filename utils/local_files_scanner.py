"""
Scanner de fichiers locaux pour détecter les clips déjà téléchargés
"""

import os
from pathlib import Path
from typing import Set, Dict, List
from mutagen.mp3 import MP3
from mutagen.id3 import ID3


class LocalFilesScanner:
    """Scanne les MP3 locaux et extrait les IDs Suno"""
    
    def __init__(self, download_folder: str):
        """
        Args:
            download_folder: Dossier où sont stockés les MP3
        """
        self.download_folder = Path(download_folder)
        self.local_ids: Set[str] = set()
        self.local_files: Dict[str, str] = {}  # {clip_id: filepath}
    
    def scan(self) -> int:
        """
        Scanne tous les MP3 et extrait les IDs Suno
        
        Returns:
            Nombre de fichiers trouvés
        """
        self.local_ids.clear()
        self.local_files.clear()
        
        if not self.download_folder.exists():
            return 0
        
        count = 0
        
        # Parcourt tous les MP3
        for mp3_file in self.download_folder.rglob("*.mp3"):
            clip_id = self._extract_suno_id(mp3_file)
            
            if clip_id:
                self.local_ids.add(clip_id)
                self.local_files[clip_id] = str(mp3_file)
                count += 1
        
        return count
    
    def _extract_suno_id(self, mp3_file: Path) -> str:
        """
        Extrait l'ID Suno d'un fichier MP3
        
        Args:
            mp3_file: Chemin du fichier MP3
        
        Returns:
            ID Suno ou chaîne vide
        """
        try:
            audio = MP3(mp3_file, ID3=ID3)
            
            # Méthode 1 : Cherche dans COMM (commentaire)
            if 'COMM::eng' in audio.tags:
                comment = str(audio.tags['COMM::eng'])
                if comment.startswith('suno:'):
                    return comment.replace('suno:', '')
            
            # Méthode 2 : Cherche dans TXXX (user-defined text)
            for key in audio.tags.keys():
                if key.startswith('TXXX:SUNO_ID'):
                    return str(audio.tags[key])
            
            # Méthode 3 : Cherche dans le nom de fichier (fallback)
            # Format: "titre [clip_id].mp3"
            filename = mp3_file.stem
            if '[' in filename and ']' in filename:
                clip_id = filename.split('[')[-1].split(']')[0]
                # Vérifie que c'est bien un ID Suno (format UUID partiel)
                if len(clip_id) >= 8 and '-' in clip_id:
                    return clip_id
            
        except Exception:
            pass
        
        return ""
    
    def has_clip(self, clip_id: str) -> bool:
        """Vérifie si un clip est déjà téléchargé"""
        return clip_id in self.local_ids
    
    def get_missing_clips(self, all_clips: List[dict]) -> List[dict]:
        """
        Retourne les clips manquants
        
        Args:
            all_clips: Liste de tous les clips Suno
        
        Returns:
            Liste des clips non téléchargés
        """
        missing = []
        
        for clip_data in all_clips:
            clip = clip_data.get('clip', {})
            clip_id = clip.get('id', '')
            
            if clip_id and not self.has_clip(clip_id):
                missing.append(clip_data)
        
        return missing
    
    def get_stats(self) -> dict:
        """Retourne les statistiques"""
        return {
            'total_local': len(self.local_ids),
            'download_folder': str(self.download_folder)
        }