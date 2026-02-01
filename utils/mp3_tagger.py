"""
Gestionnaire de tags ID3 pour fichiers MP3
"""

from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, APIC, COMM, TRCK, TPOS, TPUB, TLEN, USLT
from mutagen.mp3 import MP3
import requests
from io import BytesIO
from datetime import datetime
from typing import Optional


class MP3Tagger:
    """Gestionnaire de tags ID3"""
    
    def __init__(self, log_callback=None):
        """
        Args:
            log_callback: Fonction de log
        """
        self.log = log_callback or (lambda x: print(x))
    
    def tag_file(self, filepath: str, clip_data: dict, workspace_name: str, track_number: int = 1, disc_number: int = 1) -> bool:
        """
        Ajoute les tags ID3 à un fichier MP3
        
        Args:
            filepath: Chemin du fichier MP3
            clip_data: Données du clip
            workspace_name: Nom du workspace (utilisé comme album)
            track_number: Numéro de piste
            disc_number: Numéro de disque
            
        Returns:
            True si succès
        """
        try:
            clip = clip_data.get('clip', {})
            meta = clip.get('metadata', {})
            
            # Données
            title = clip.get('title', 'Sans titre')
            artist = clip.get('display_name', 'Artiste inconnu')
            album = f"Suno - {workspace_name}"
            
            # Date complète (dd/mm/yyyy)
            date_str = clip.get('created_at', '')
            date_formatted = self._format_date(date_str)
            
            # Style/tags comme genre de base
            style_tags = meta.get('tags', '') if meta else ''
            prompt = meta.get('prompt', '') if meta else ''
            
            image_url = clip.get('image_large_url') or clip.get('image_url', '')
            
            # Durée en millisecondes
            duration = meta.get('duration', 0) if meta else 0
            duration_ms = int(duration * 1000)
            
            self.log(f"🏷️ Ajout tags ID3: {title[:40]}")
            
            # Charge le fichier MP3
            try:
                audio = MP3(filepath, ID3=ID3)
            except:
                audio = MP3(filepath)
                audio.add_tags()
            
            # Efface les tags existants
            audio.delete()
            audio = MP3(filepath)
            audio.add_tags()
            
            # ✅ TITRE
            audio.tags.add(TIT2(encoding=3, text=title))
            
            # ✅ ARTISTE
            audio.tags.add(TPE1(encoding=3, text=artist))
            
            # ✅ ALBUM
            audio.tags.add(TALB(encoding=3, text=album))
            
            # ✅ NUMÉRO DE PISTE (format "001")
            audio.tags.add(TRCK(encoding=3, text=f"{track_number:03d}"))
            
            # ✅ NUMÉRO DE DISQUE (format "01")
            audio.tags.add(TPOS(encoding=3, text=f"{disc_number:02d}"))
            
            # ✅ DATE (dd/mm/yyyy) - Dans TDRC comme texte
            if date_formatted:
                audio.tags.add(TDRC(encoding=3, text=date_formatted))
            
            # ✅ GENRE - "Suno AI"
            audio.tags.add(TCON(encoding=3, text="Suno AI"))
            
            # ✅ ÉDITEUR
            audio.tags.add(TPUB(encoding=3, text="Suno AI"))
            
            # ✅ DURÉE (millisecondes)
            if duration_ms > 0:
                audio.tags.add(TLEN(encoding=3, text=str(duration_ms)))
            
            # ✅ COMMENTAIRE - GitHub + Prompt/Style
            comment_lines = ["Downloaded with https://github.com/soaresden/SunoPlayerDownloader"]
            
            if style_tags:
                comment_lines.append(f"\nStyle: {style_tags}")
            
            comment_text = "".join(comment_lines)
            audio.tags.add(COMM(encoding=3, lang='eng', desc='', text=comment_text))
            
            # ✅ PAROLES (dans USLT uniquement si prompt existe)
            if prompt:
                audio.tags.add(USLT(encoding=3, lang='eng', desc='Prompt', text=prompt))
            
            # ✅ POCHETTE (Front Cover)
            if image_url:
                cover_data = self._download_cover(image_url)
                if cover_data:
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,  # 3 = Front cover
                            desc='Cover',
                            data=cover_data
                        )
                    )
                    self.log(f"  ✅ Pochette ajoutée")
            
            # Sauvegarde
            audio.save(v2_version=3)  # Force ID3v2.3 pour compatibilité Windows
            
            self.log(f"  ✅ Tags sauvegardés")
            return True
            
        except Exception as e:
            self.log(f"  ❌ Erreur tagging: {e}")
            return False
    
    def _format_date(self, iso_date: str) -> str:
        """
        Formate une date ISO en dd/mm/yyyy
        
        Args:
            iso_date: Date ISO (2026-01-31T20:47:00Z)
            
        Returns:
            Date formatée (31/01/2026)
        """
        if not iso_date:
            return ""
        
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y")
        except:
            return ""
    
    def _download_cover(self, url: str) -> Optional[bytes]:
        """
        Télécharge une image de pochette
        
        Args:
            url: URL de l'image
            
        Returns:
            Données de l'image en bytes, ou None
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            self.log(f"  ⚠️ Erreur téléchargement pochette: {e}")
            return None
    
    def read_tags(self, filepath: str) -> dict:
        """
        Lit les tags d'un fichier MP3
        
        Args:
            filepath: Chemin du fichier
            
        Returns:
            Dict avec les tags
        """
        try:
            audio = MP3(filepath, ID3=ID3)
            
            return {
                'title': str(audio.tags.get('TIT2', 'Sans titre')),
                'artist': str(audio.tags.get('TPE1', 'Artiste inconnu')),
                'album': str(audio.tags.get('TALB', '')),
                'track': str(audio.tags.get('TRCK', '')),
                'disc': str(audio.tags.get('TPOS', '')),
                'date': str(audio.tags.get('TDRC', '')),
                'genre': str(audio.tags.get('TCON', '')),
                'publisher': str(audio.tags.get('TPUB', '')),
                'has_cover': 'APIC:Cover' in audio.tags
            }
        except Exception as e:
            self.log(f"❌ Erreur lecture tags: {e}")
            return {}