"""
Gestionnaire de cache audio intelligent avec tagging ID3
Priorité : Musik > Downloads > !temp
"""

import os
import re
import requests
from pathlib import Path
from typing import Optional, Tuple
from config import MUSIK_LIBRARY_PATH, DOWNLOADS_PATH, TEMP_CACHE_PATH
from utils.mp3_tagger import MP3Tagger


class AudioCache:
    """Gestionnaire de cache audio avec priorités et tagging"""
    
    def __init__(self, log_callback=None):
        """
        Args:
            log_callback: Fonction de log
        """
        self.log = log_callback or (lambda x: print(x))
        self.tagger = MP3Tagger(log_callback=self.log)
        
        # Crée les dossiers si nécessaire
        Path(TEMP_CACHE_PATH).mkdir(parents=True, exist_ok=True)
        Path(DOWNLOADS_PATH).mkdir(exist_ok=True)
    
    def get_audio_path(self, clip_data: dict, workspace_name: str, permanent: bool = False, track_number: int = 1) -> Optional[str]:
        """
        Récupère le chemin du fichier audio (cherche ou télécharge)
        
        ORDRE DE PRIORITÉ :
        1. Musik (dossiers "Suno*")
        2. Downloads permanents
        3. Cache !temp (lecture seule)
        4. Téléchargement
        """
        clip = clip_data.get('clip', {})
        title = clip.get('title', 'Sans titre')
        clip_id = clip.get('id', '')
        audio_url = clip.get('audio_url', '')
        is_pinned = clip_data.get('is_pinned', False)
        
        if not audio_url:
            self.log(f"⚠️ Pas d'URL audio pour: {title}")
            return None
        
        # Génère le nom de fichier
        safe_title = self._sanitize_filename(title)
        disc_number = 1
        track_str = f"{track_number:03d}"
        id_short = clip_id[:8]
        upload_suffix = "_UPLOADED" if is_pinned else ""
        filename = f"{disc_number:02d}-{track_str} {safe_title} ({id_short}){upload_suffix}.mp3"
        
        # ✅ ÉTAPE 1 : Cherche dans Musik
        musik_path = self._search_in_musik(safe_title, clip_id)
        if musik_path:
            # ⭐ NOUVEAU : Vérifie si le fichier a l'ID Suno dans ISRC
            has_id = self._check_suno_id_in_file(musik_path, clip_id)
            
            if has_id:
                self.log(f"⏭️  IGNORÉ (déjà avec ID) : {Path(musik_path).name}")
                return musik_path
            else:
                if permanent:
                    self.log(f"⚠️  SANS ID - RE-TÉLÉCHARGEMENT : {Path(musik_path).name}")
                else:
                    # Pour la lecture, on utilise quand même le fichier
                    self.log(f"✅ Trouvé dans Musik (sans ID) : {Path(musik_path).name}")
                    return musik_path
        
        # ✅ ÉTAPE 2 : Cherche dans Downloads
        workspace_folder = Path(DOWNLOADS_PATH) / f"Suno-{self._sanitize_filename(workspace_name)}"
        downloads_path = workspace_folder / filename
        
        if downloads_path.exists():
            self.log(f"⏭️  IGNORÉ (déjà dans Downloads) : {filename}")
            return str(downloads_path)
        
        # ✅ ÉTAPE 3 : Si lecture, cherche dans !temp
        if not permanent:
            temp_path = Path(TEMP_CACHE_PATH) / filename
            
            if temp_path.exists():
                self.log(f"✅ Trouvé dans cache : {filename}")
                return str(temp_path)
        
        # ✅ ÉTAPE 4 : Télécharge
        if permanent:
            # Téléchargement permanent dans Downloads
            self.log(f"📥 TÉLÉCHARGEMENT : {title[:50]}")
            workspace_folder.mkdir(parents=True, exist_ok=True)
            downloaded_path = self._download_audio(audio_url, str(downloads_path))
            
            if downloaded_path:
                self.tagger.tag_file(downloaded_path, clip_data, workspace_name, track_number, disc_number=1)
                self.log(f"     ✅ Sauvegardé : {filename}")
                
                # Supprime du cache
                self.delete_temp_file(clip_id, title)
            else:
                self.log(f"     ❌ ÉCHEC téléchargement")
            
            return downloaded_path
        else:
            # Téléchargement cache temporaire
            temp_path = Path(TEMP_CACHE_PATH) / filename
            self.log(f"📥 Téléchargement cache : {filename}")
            downloaded_path = self._download_audio(audio_url, str(temp_path))
            
            if downloaded_path:
                self.tagger.tag_file(downloaded_path, clip_data, workspace_name, track_number, disc_number=1)
            
            return downloaded_path
    
    def _check_suno_id_in_file(self, filepath: str, clip_id: str) -> bool:
        """
        ⭐ NOUVELLE MÉTHODE : Vérifie si un fichier MP3 contient l'ID Suno dans le tag ISRC
        
        Args:
            filepath: Chemin du fichier
            clip_id: ID Suno à vérifier
        
        Returns:
            True si l'ID est trouvé dans l'ISRC
        """
        try:
            from mutagen.mp3 import MP3
            
            audio = MP3(filepath)
            
            # ⭐ PRIORITÉ : Lit depuis ISRC (tag TSRC) - NOUVEAU FORMAT
            if 'TSRC' in audio.tags:
                isrc = str(audio.tags['TSRC'])
                if clip_id in isrc:
                    return True
            
            # ⚠️ FALLBACK : Anciens fichiers avec COMM/TXXX
            # Pour compatibilité avec les MP3 déjà taggés avant le changement
            
            # Cherche dans COMM (ancien format)
            if 'COMM::eng' in audio.tags:
                comm_text = str(audio.tags['COMM::eng'])
                if clip_id in comm_text:
                    return True
            
            # Cherche dans TXXX (ancien format)
            if 'TXXX:SUNO_ID' in audio.tags:
                txxx_text = str(audio.tags['TXXX:SUNO_ID'])
                if clip_id in txxx_text:
                    return True
            
            return False
            
        except Exception as e:
            # En cas d'erreur de lecture, on suppose qu'il n'y a pas d'ID
            return False
    
    def delete_temp_file(self, clip_id: str, title: str):
        """
        Supprime un fichier du cache temporaire par ID avec retry
        
        Args:
            clip_id: ID du clip
            title: Titre pour générer le nom
        """
        import time
        
        safe_title = self._sanitize_filename(title)
        id_short = clip_id[:8]
        
        # Cherche le fichier dans !temp
        temp_path = Path(TEMP_CACHE_PATH)
        
        if not temp_path.exists():
            self.log(f"  ℹ️ Dossier !temp n'existe pas")
            return
        
        # Pattern: *{id_short}*.mp3
        files_found = list(temp_path.glob(f"*{id_short}*.mp3"))
        
        if not files_found:
            self.log(f"  ℹ️ Aucun fichier cache trouvé pour {id_short}")
            return
        
        for file in files_found:
            self.log(f"  🗑️ Tentative suppression: {file.name}")
            
            # Retry 3 fois avec délai
            for attempt in range(3):
                try:
                    file.unlink()
                    self.log(f"  ✅ Cache supprimé: {file.name}")
                    return
                except PermissionError as e:
                    if attempt < 2:
                        self.log(f"  ⏳ Fichier verrouillé, retry {attempt + 1}/3...")
                        time.sleep(0.5)
                    else:
                        self.log(f"  ⚠️ Impossible de supprimer (fichier utilisé): {file.name}")
                except Exception as e:
                    self.log(f"  ❌ Erreur suppression: {e}")
                    return
                
                
    def _search_in_musik(self, title: str, clip_id: str = '') -> Optional[str]:
        """
        Cherche un fichier audio dans la bibliothèque Musik
        UNIQUEMENT dans les dossiers commençant par "Suno" ou "SUNO"
        
        Args:
            title: Titre du morceau
            clip_id: ID du clip (optionnel)
            
        Returns:
            Chemin du fichier trouvé, ou None
        """
        musik_path = Path(MUSIK_LIBRARY_PATH)
        
        if not musik_path.exists():
            return None
        
        title_lower = title.lower()
        
        for folder in musik_path.iterdir():
            if not folder.is_dir():
                continue
            
            if not folder.name.lower().startswith('suno'):
                continue
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.flac', '.wav', '.m4a', '.ogg')):
                        # Cherche par titre
                        if title_lower in file.lower():
                            return os.path.join(root, file)
                        # Cherche par ID si fourni
                        if clip_id and clip_id[:8] in file:
                            return os.path.join(root, file)
        
        return None
    
    def _download_audio(self, url: str, output_path: str) -> Optional[str]:
        """
        Télécharge un fichier audio
        
        Args:
            url: URL du fichier
            output_path: Chemin de destination
            
        Returns:
            Chemin du fichier téléchargé, ou None si erreur
        """
        try:
            self.log(f"     ⏳ Téléchargement depuis: {url[:60]}...")
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            self.log(f"     ✅ Fichier téléchargé ({file_size:.2f} MB)")
            
            return output_path
            
        except Exception as e:
            self.log(f"     ❌ Erreur téléchargement: {e}")
            
            if os.path.exists(output_path):
                os.remove(output_path)
            
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Nettoie un nom de fichier
        
        Args:
            filename: Nom à nettoyer
            
        Returns:
            Nom nettoyé
        """
        filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
        
        if len(filename) > 80:
            filename = filename[:80]
        
        return filename.strip()
    
    def clear_temp_cache(self):
        """Vide le cache temporaire"""
        temp_path = Path(TEMP_CACHE_PATH)
        
        if not temp_path.exists():
            return
        
        count = 0
        for file in temp_path.glob('*.mp3'):
            try:
                file.unlink()
                count += 1
            except Exception as e:
                self.log(f"⚠️ Erreur suppression {file.name}: {e}")
        
        self.log(f"🗑️ Cache temporaire vidé ({count} fichier(s))")