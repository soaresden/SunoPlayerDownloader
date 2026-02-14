"""
Parser de timestamps relatifs de Suno
"""

import re
from datetime import datetime, timedelta


def parse_relative_time(text: str) -> datetime:
    """
    Parse un timestamp relatif Suno et retourne la date exacte
    
    Exemples:
        "1d, 16h ago" → now - 1 day - 16 hours
        "2w, 5d ago" → now - 2 weeks - 5 days
        "3w ago" → now - 3 weeks
        "5 Songs · 1d, 16h ago" → extrait "1d, 16h ago"
    
    Args:
        text: Texte contenant le timestamp relatif
    
    Returns:
        datetime de la dernière mise à jour
    """
    
    # Nettoie le texte
    text = text.strip()
    
    # Extrait la partie temporelle (après "·")
    if '·' in text:
        text = text.split('·')[1].strip()
    
    # Retire " ago" à la fin
    text = text.replace(' ago', '').strip()
    
    # Parse les composants temporels
    # Format: "2w, 5d" ou "1d, 16h" ou "3w"
    
    total_delta = timedelta()
    
    # Regex pour extraire les valeurs (ex: "2w", "5d", "16h")
    pattern = r'(\d+)([wdhms])'
    matches = re.findall(pattern, text)
    
    for value, unit in matches:
        value = int(value)
        
        if unit == 'w':  # weeks
            total_delta += timedelta(weeks=value)
        elif unit == 'd':  # days
            total_delta += timedelta(days=value)
        elif unit == 'h':  # hours
            total_delta += timedelta(hours=value)
        elif unit == 'm':  # minutes
            total_delta += timedelta(minutes=value)
        elif unit == 's':  # seconds
            total_delta += timedelta(seconds=value)
    
    # Calcule la date
    now = datetime.now()
    updated_at = now - total_delta
    
    return updated_at


def format_relative_time(dt: datetime) -> str:
    """
    Convertit une date en format relatif Suno
    
    Args:
        dt: datetime à convertir
    
    Returns:
        Chaîne relative (ex: "1d, 16h ago")
    """
    now = datetime.now()
    delta = now - dt
    
    parts = []
    
    # Semaines
    weeks = delta.days // 7
    if weeks > 0:
        parts.append(f"{weeks}w")
        remaining_days = delta.days % 7
        if remaining_days > 0:
            parts.append(f"{remaining_days}d")
    else:
        # Jours
        if delta.days > 0:
            parts.append(f"{delta.days}d")
        
        # Heures
        hours = delta.seconds // 3600
        if hours > 0:
            parts.append(f"{hours}h")
    
    if not parts:
        return "now"
    
    return ", ".join(parts) + " ago"


# Tests
if __name__ == '__main__':
    test_cases = [
        "5 Songs · 1d, 16h ago",
        "82 Songs · 2w, 5d ago",
        "3 Songs · 3w ago",
        "6 Songs · 3w, 2d ago",
        "1d, 16h ago",
        "2w, 5d ago"
    ]
    
    for test in test_cases:
        result = parse_relative_time(test)
        print(f"{test:30} → {result.strftime('%Y-%m-%d %H:%M:%S')}")