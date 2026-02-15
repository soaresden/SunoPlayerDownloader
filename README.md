# 🎵 Suno Downloader v2.0
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/c68a5aa8-02b3-49be-af63-71c51e4f4c45" />

Application modulaire complète pour naviguer, écouter et télécharger vos projets Suno.

## 📁 Structure du projet

```
suno_app/
├── main.py                    # ▶️ Point d'entrée - Lance l'app
├── config.py                  # ⚙️ Configuration globale
├── requirements.txt           # 📦 Dépendances Python
├── suno_cookies.json          # 🍪 Vos cookies (à créer)
│
├── api/                       # 🔌 Couche API
│   ├── __init__.py
│   ├── client.py              # Client API Suno (get_all_projects, etc.)
│   └── auth.py                # Gestion authentification (AuthManager)
│
├── gui/                       # 🖼️ Interface graphique
│   ├── __init__.py
│   ├── main_window.py         # Fenêtre principale (orchestration)
│   ├── toolbar.py             # Barre d'outils (boutons principaux)
│   ├── projects_panel.py      # Panel gauche (liste projets)
│   └── clips_panel.py         # Panel droit (liste clips + checkboxes)
│
├── widgets/                   # 🧩 Composants réutilisables
│   ├── __init__.py
│   ├── player.py              # Player audio (overlay)
│   ├── lyrics_overlay.py      # Overlay paroles (double-clic)
│   └── log_viewer.py          # Zone de logs
│
└── utils/                     # 🛠️ Utilitaires
    ├── __init__.py
    ├── formatters.py          # Formatage (dates, durées, tailles)
    └── threading_helper.py    # Helpers threading GUI-safe
```

## 🚀 Installation

### 1. Installer Python
- Python 3.8+ requis
- Télécharger sur https://python.org

### 2. Installer les dépendances

```bash
cd suno_app
pip install -r requirements.txt
```

### 3. Créer suno_cookies.json

#### Option A : Bookmarklet (recommandé)

1. Va sur https://suno.com (connecté)
2. Crée un bookmarklet avec ce code :

```javascript
javascript:(function(){const cookies={};document.cookie.split(';').forEach(c=>{const[name,value]=c.trim().split('=');cookies[name]=value});const jwt=cookies['__session']||'';const deviceId=cookies['suno_device_id']||cookies['ajs_anonymous_id']||'8f955be9-40b8-496e-9a05-c12b86abd5f8';const data={jwt_token:jwt,device_id:deviceId,exported_at:new Date().toISOString()};const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='suno_cookies.json';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);alert('✅ Cookies exportés!')})();
```

3. Clique sur le bookmarklet → télécharge `suno_cookies.json`
4. Place-le dans le dossier `suno_app/`

#### Option B : Manuel

Crée `suno_cookies.json` :

```json
{
  "jwt_token": "TON_TOKEN_JWT_ICI",
  "device_id": "TON_DEVICE_ID_ICI",
  "exported_at": "2026-02-01T12:00:00Z"
}
```

### 4. Lancer l'application

```bash
python main.py
```

## 📖 Utilisation

### Interface

```
┌────────────────────────────────────────────────────────────┐
│ 🎵 SUNO    [🔄] [📁 COOKIES] [▶️ PLAYER]         🟢       │
├──────────────────────────┬─────────────────────────────────┤
│ 📁 PROJETS (137)         │ 🎵 CLIPS - Mon Projet          │
│ ┌──────────────────────┐ │ [⬇️ TOUT] [⬇️ COCHÉS] [▶️ PLAY]│
│ │Workspace  │#│Créé│MÀJ││ ┌───────────────────────────────┐│
│ │My Project │5│... │...││ │P│Créé│Titre│Style│⏱│🎵│⬇️│    ││
│ │Outlaws    │30│...│...││ │📌│...│...  │...  │3:│✓│  │    ││
│ │...        │  │   │   ││ │  │   │     │     │42│  │✓│    ││
│ └──────────────────────┘ │ └───────────────────────────────┘│
├──────────────────────────┴─────────────────────────────────┤
│ 📝 Logs                                                     │
│ ✅ 137 projets chargés                                     │
│ 📁 Projet sélectionné: My Project                          │
│ ✅ 5 clips (2 pinned)                                       │
└─────────────────────────────────────────────────────────────┘
```

### Actions principales

**Navigation :**
- Clic sur projet → Affiche ses clips
- Double-clic sur clip → Affiche les paroles
- Clic sur header → Tri la colonne

**Checkboxes :**
- **🎵** : Ajouter à la playlist
- **⬇️** : Marquer pour téléchargement

**Boutons :**
- **⬇️ TOUT** : Télécharge tout le projet
- **⬇️ COCHÉS** : Télécharge les clips cochés (⬇️)
- **▶️ PLAYLIST** : Joue les clips de la playlist (🎵)
- **▶️ PLAYER** : Ouvre le player audio

**Toolbar :**
- **🔄** : Recharge les cookies (si token expiré)
- **📁 COOKIES** : Charge un nouveau fichier
- **▶️ PLAYER** : Ouvre le player

### Raccourcis

- **Double-clic** sur clip → Overlay paroles
- **Clic** sur checkbox → Cocher/décocher

## 🔧 Architecture

### Séparation des responsabilités

**api/** → Communication avec Suno (aucune GUI)
- `client.py` : Appels API (get_all_projects, get_project_clips, download_clip)
- `auth.py` : Gestion cookies/tokens (AuthManager)

**gui/** → Interface graphique (aucune logique métier)
- `main_window.py` : Orchestration (charge projets, gère sélections)
- `toolbar.py` : Barre d'outils
- `projects_panel.py` : TreeView projets
- `clips_panel.py` : TreeView clips + checkboxes

**widgets/** → Composants réutilisables
- `player.py` : Player audio overlay
- `lyrics_overlay.py` : Popup paroles
- `log_viewer.py` : Zone de logs

**utils/** → Fonctions utilitaires
- `formatters.py` : format_date(), format_duration(), etc.
- `threading_helper.py` : run_in_thread() pour GUI-safe

### Avantages

✅ **Modulaire** : Chaque fichier < 250 lignes  
✅ **Maintenable** : Bugs faciles à localiser  
✅ **Testable** : Chaque module testable indépendamment  
✅ **Extensible** : Facile d'ajouter de nouvelles fonctionnalités  
✅ **Réutilisable** : Les widgets peuvent servir ailleurs  

## 🐛 Dépannage

### Erreur 401 Unauthorized
→ Token expiré (durée : 1h)  
→ Solution : Clique sur 🔄 ou exporte de nouveaux cookies

### Fichier cookies introuvable
→ Le fichier doit être dans le dossier `suno_app/`  
→ Le nom doit être exactement `suno_cookies.json`

### Module introuvable
→ Lance depuis le dossier `suno_app/` : `python main.py`  
→ Pas `python suno_app/main.py`

## 📝 TODO

- [ ] Implémenter lecture audio (player)
- [ ] Implémenter téléchargement batch
- [ ] Ajouter barre de progression téléchargement
- [ ] Export playlist M3U
- [ ] Recherche/filtre dans les clips
- [ ] Thèmes de couleur

## 📄 Licence

Projet personnel - Utilisez à vos risques et périls

## 👨‍💻 Auteur

Créé avec ❤️ pour Denis
