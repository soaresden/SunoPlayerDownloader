# 🎵 Suno Player & Downloader

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Desktop app to manage, play and download your Suno AI creations**

</div>

---

## ✨ Features

- 🎧 **Audio Player** - Play your Suno clips directly
- 📥 **Smart Download** - Download with full ID3 tags (title, artist, album, cover, lyrics)
- 📁 **Auto-organize** - Format: `01-001 Title (ID)_UPLOADED.mp3`
- 🎨 **Modern UI** - Official Suno colors
- 🌍 **Multi-language** - English & Français

---

## 🚀 Quick Start

### 1. Clone & Run
```bash
git clone https://github.com/soaresden/SunoPlayerDownloader.git
cd SunoPlayerDownloader
python main.py
```

Dependencies install automatically!

### 2. Export Cookies

**Drag this button to your bookmarks bar:**

<a href="javascript:(function(){const e=['cookie','_cfuvid','__client','__client_uat','_clck','_clsk','cf_clearance','__stripe_mid','__stripe_sid','_ga','_ga_*','__cf_bm'],t=document.cookie.split('; ').reduce((t,o)=>{const[c,n]=o.split('=');return e.some(e=>e.endsWith('*')?c.startsWith(e.slice(0,-1)):c===e)&&(t[c]=n),t},{}),o=JSON.stringify(t,null,2),c=document.createElement('a');c.href='data:application/json;charset=utf-8,'+encodeURIComponent(o),c.download='suno_cookies.json',c.click()})();">📥 Export Suno Cookies</a>

**Then:**
1. Go to [suno.com](https://suno.com) and login
2. Click the bookmark
3. Save `suno_cookies.json` in project folder

**Alternative (manual):** Open browser console (F12) and paste:
```javascript
(function(){const e=['cookie','_cfuvid','__client','__client_uat','_clck','_clsk','cf_clearance','__stripe_mid','__stripe_sid','_ga','_ga_*','__cf_bm'],t=document.cookie.split('; ').reduce((t,o)=>{const[c,n]=o.split('=');return e.some(e=>e.endsWith('*')?c.startsWith(e.slice(0,-1)):c===e)&&(t[c]=n),t},{}),o=JSON.stringify(t,null,2),c=document.createElement('a');c.href='data:application/json;charset=utf-8,'+encodeURIComponent(o),c.download='suno_cookies.json',c.click()})();
```

### 3. Done!

The app auto-loads your projects. Double-click clips to play, right-click for options.

---

## 📦 File Format

**Naming:** `01-001 Title (ID)_UPLOADED.mp3`

**ID3 Tags:**
- Title, Artist, Album
- Track number (001, 002...)
- Disc number (01)
- Date (dd/mm/yyyy)
- Genre: "Suno AI"
- High-res cover art
- Lyrics (prompt)
- Comment: GitHub link + Style + Prompt

---

## 🎯 Usage

| Action | Result |
|--------|--------|
| Double-click clip | Add to playlist |
| Right-click clip | Show menu |
| Check ✓ download | Add to download queue |
| Click "📥 TOUT DL" | Download all projects |

---

## 📁 Structure
```
downloads/
├── !temp/                           # Temporary cache
├── Suno-Mirador/
│   ├── 01-001 Song (d73834dd)_UPLOADED.mp3
│   └── 01-002 Song (ae4cbf0d).mp3
└── Suno-Project/
    └── ...
```

---

## 🐛 Troubleshooting

**Cookies expired?** Re-export from suno.com

**File locked?** Stop player before downloading

---

## 📝 License

MIT License - See [LICENSE](LICENSE)

---

## 👤 Author

**Denis SOARES** - [@soaresden](https://github.com/soaresden)

---

<div align="center">

**⭐ Star if useful! ⭐**

Made with ❤️ and 🎵

</div>

---
---

# 🇫🇷 Version Française

## 🎵 Suno Player & Downloader

**Application desktop pour gérer, écouter et télécharger vos créations Suno AI**

---

## ✨ Fonctionnalités

- 🎧 **Lecteur Audio** - Écoutez vos clips Suno directement
- 📥 **Téléchargement Intelligent** - Avec tags ID3 complets (titre, artiste, album, pochette, paroles)
- 📁 **Organisation Auto** - Format : `01-001 Titre (ID)_UPLOADED.mp3`
- 🎨 **Interface Moderne** - Couleurs officielles Suno
- 🌍 **Multilingue** - Français & English

---

## 🚀 Démarrage Rapide

### 1. Cloner & Lancer
```bash
git clone https://github.com/soaresden/SunoPlayerDownloader.git
cd SunoPlayerDownloader
python main.py
```

Les dépendances s'installent automatiquement !

### 2. Exporter les Cookies

**Glissez ce bouton dans votre barre de favoris :**

<a href="javascript:(function(){const e=['cookie','_cfuvid','__client','__client_uat','_clck','_clsk','cf_clearance','__stripe_mid','__stripe_sid','_ga','_ga_*','__cf_bm'],t=document.cookie.split('; ').reduce((t,o)=>{const[c,n]=o.split('=');return e.some(e=>e.endsWith('*')?c.startsWith(e.slice(0,-1)):c===e)&&(t[c]=n),t},{}),o=JSON.stringify(t,null,2),c=document.createElement('a');c.href='data:application/json;charset=utf-8,'+encodeURIComponent(o),c.download='suno_cookies.json',c.click()})();">📥 Export Suno Cookies</a>

**Ensuite :**
1. Allez sur [suno.com](https://suno.com) et connectez-vous
2. Cliquez sur le favori
3. Enregistrez `suno_cookies.json` dans le dossier du projet

**Alternative (manuel) :** Ouvrez la console (F12) et collez :
```javascript
(function(){const e=['cookie','_cfuvid','__client','__client_uat','_clck','_clsk','cf_clearance','__stripe_mid','__stripe_sid','_ga','_ga_*','__cf_bm'],t=document.cookie.split('; ').reduce((t,o)=>{const[c,n]=o.split('=');return e.some(e=>e.endsWith('*')?c.startsWith(e.slice(0,-1)):c===e)&&(t[c]=n),t},{}),o=JSON.stringify(t,null,2),c=document.createElement('a');c.href='data:application/json;charset=utf-8,'+encodeURIComponent(o),c.download='suno_cookies.json',c.click()})();
```

### 3. Terminé !

L'app charge vos projets automatiquement. Double-clic pour jouer, clic droit pour options.

---

## 📦 Format des Fichiers

**Nommage :** `01-001 Titre (ID)_UPLOADED.mp3`

**Tags ID3 :**
- Titre, Artiste, Album
- N° piste (001, 002...)
- N° disque (01)
- Date (jj/mm/aaaa)
- Genre : "Suno AI"
- Pochette haute résolution
- Paroles (prompt)
- Commentaire : Lien GitHub + Style + Prompt

---

## 🎯 Utilisation

| Action | Résultat |
|--------|----------|
| Double-clic clip | Ajoute à la playlist |
| Clic droit clip | Affiche menu |
| Cocher ✓ download | Ajoute à la file de téléchargement |
| Clic "📥 TOUT DL" | Télécharge tous les projets |

---

## 📁 Structure
```
downloads/
├── !temp/                           # Cache temporaire
├── Suno-Mirador/
│   ├── 01-001 Song (d73834dd)_UPLOADED.mp3
│   └── 01-002 Song (ae4cbf0d).mp3
└── Suno-Projet/
    └── ...
```

---

## 🐛 Dépannage

**Cookies expirés ?** Ré-exportez depuis suno.com

**Fichier verrouillé ?** Arrêtez le player avant téléchargement

---

## 📝 Licence

Licence MIT - Voir [LICENSE](LICENSE)

---

## 👤 Auteur

**Denis SOARES** - [@soaresden](https://github.com/soaresden)

---

<div align="center">

**⭐ Star si utile ! ⭐**

Fait avec ❤️ et 🎵

</div>