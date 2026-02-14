#!/usr/bin/env python3
"""
Test les clips d'un projet pour voir les champs de date
"""

import json
import requests
import time
import base64


def load_credentials():
    """Charge jwt_token et device_id"""
    with open('suno_cookies.json', 'r') as f:
        credentials = json.load(f)
    
    jwt_token = credentials.get('jwt_token', '') or \
                credentials.get('__session', '') or \
                credentials.get('__client', '')
    
    device_id = credentials.get('device_id') or \
                credentials.get('suno_device_id') or \
                credentials.get('ajs_anonymous_id') or \
                '8f955be9-40b8-496e-9a05-c12b86abd5f8'
    
    return jwt_token, device_id


def get_browser_token():
    """Génère un browser token"""
    timestamp_ms = int(time.time() * 1000)
    token_data = json.dumps({"timestamp": timestamp_ms})
    return base64.b64encode(token_data.encode()).decode()


def test_project_clips():
    """Teste les clips d'un projet"""
    
    print("🎵 TEST CLIPS D'UN PROJET")
    print("=" * 80)
    
    # Charge credentials
    jwt_token, device_id = load_credentials()
    
    # Headers
    headers = {
        "accept": "*/*",
        "authorization": f"Bearer {jwt_token}",
        "device-id": device_id,
        "browser-token": get_browser_token(),
        "origin": "https://suno.com",
        "referer": "https://suno.com/",
        "user-agent": "Mozilla/5.0"
    }
    
    # 1. Récupère un projet
    print("\n🔍 Récupération du premier projet...")
    
    response = requests.get(
        "https://studio-api.prod.suno.com/api/project/me",
        headers=headers,
        params={'page': 1, 'sort': 'max_created_at_last_updated_clip'}
    )
    
    projects = response.json().get('projects', [])
    
    if not projects:
        print("❌ Aucun projet trouvé")
        return
    
    first_project = projects[0]
    project_id = first_project['id']
    project_name = first_project['name']
    
    print(f"✅ Projet: {project_name} (ID: {project_id})")
    
    # 2. Récupère les clips du projet
    print(f"\n🔍 Récupération des clips du projet...")
    
    response = requests.get(
        f"https://studio-api.prod.suno.com/api/project/{project_id}",
        headers=headers
    )
    
    clips_data = response.json()
    clips = clips_data.get('project_clips', [])
    
    print(f"✅ {len(clips)} clip(s) trouvé(s)")
    
    if not clips:
        print("⚠️ Aucun clip dans ce projet")
        return
    
    # 3. Affiche le premier clip
    first_clip = clips[0]
    
    print("\n" + "=" * 80)
    print("📋 PREMIER CLIP - TOUTES LES CLÉS:")
    print("=" * 80)
    
    for key in sorted(first_clip.keys()):
        value = first_clip[key]
        if isinstance(value, str) and len(value) > 50:
            print(f"  {key}: {value[:50]}...")
        else:
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("🔍 CLÉS AVEC 'DATE' OU 'TIME' OU 'CREATED':")
    print("=" * 80)
    
    date_keys = [k for k in first_clip.keys() if any(x in k.lower() for x in ['date', 'time', 'created', 'at'])]
    
    for key in date_keys:
        print(f"  ⭐ {key}: {first_clip[key]}")
    
    if not date_keys:
        print("  ⚠️ Aucune clé de date trouvée !")
    
    # Sauvegarde
    with open('clip_example.json', 'w', encoding='utf-8') as f:
        json.dump(first_clip, f, indent=2, ensure_ascii=False)
    
    print("\n💾 Clip complet sauvegardé dans: clip_example.json")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)


if __name__ == '__main__':
    test_project_clips()