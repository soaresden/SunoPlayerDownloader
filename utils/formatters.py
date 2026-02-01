"""
Utilitaires de formatage (dates, durées, tailles)
"""

from datetime import datetime
from typing import Optional


def format_date(date_str: str, format: str = "%d/%m %H:%M") -> str:
    """
    Formate une date ISO en format lisible
    
    Args:
        date_str: Date ISO (ex: "2026-01-31T20:47:00Z")
        format: Format de sortie
        
    Returns:
        Date formatée (ex: "31/01 20:47")
    """
    if not date_str:
        return ""
    
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime(format)
    except:
        # Fallback: retourne juste les 10 premiers chars
        return date_str[:10]


def format_duration(seconds: float) -> str:
    """
    Formate une durée en secondes en min:sec
    
    Args:
        seconds: Durée en secondes
        
    Returns:
        Durée formatée (ex: "3:42")
    """
    if not seconds:
        return ""
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def format_file_size(bytes: int) -> str:
    """
    Formate une taille de fichier
    
    Args:
        bytes: Taille en bytes
        
    Returns:
        Taille formatée (ex: "3.5 MB")
    """
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 ** 2:
        return f"{bytes / 1024:.1f} KB"
    elif bytes < 1024 ** 3:
        return f"{bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes / (1024 ** 3):.1f} GB"


def truncate_text(text: str, max_length: int = 60, suffix: str = "...") -> str:
    """
    Tronque un texte
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximum
        suffix: Suffixe à ajouter
        
    Returns:
        Texte tronqué
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
