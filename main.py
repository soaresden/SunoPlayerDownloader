#!/usr/bin/env python3
"""
🎵 Suno Downloader v2.0
Application modulaire pour naviguer et télécharger vos projets Suno

Usage:
    python main.py
"""

import sys
from pathlib import Path

# Ajoute le dossier courant au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))


def check_and_install_requirements():
    """Vérifie et installe les dépendances automatiquement"""
    import subprocess
    
    print("🔍 Vérification des dépendances...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("⚠️  requirements.txt introuvable")
        return
    
    # Lecture des requirements
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # ✨ MAPPING spécial pour certains packages
    package_import_map = {
        'Pillow': 'PIL',  # Pillow s'importe comme PIL
    }
    
    missing_packages = []
    
    # Vérifie chaque package
    for req in requirements:
        # Extrait le nom du package (avant >= ou ==)
        package_name = req.split('>=')[0].split('==')[0].strip()
        
        # Utilise le nom d'import correct
        import_name = package_import_map.get(package_name, package_name)
        
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} manquant")
            missing_packages.append(req)
    
    # Installe les packages manquants
    if missing_packages:
        print(f"\n📦 Installation de {len(missing_packages)} package(s) manquant(s)...")
        
        for package in missing_packages:
            print(f"  ⏳ Installation de {package}...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"  ✅ {package} installé")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Erreur installation {package}: {e}")
                print(f"\n⚠️  Installez manuellement : pip install {package}")
                return False
        
        print(f"\n✅ Toutes les dépendances sont installées !\n")
    else:
        print(f"\n✅ Toutes les dépendances sont déjà installées !\n")
    
    return True


def main():
    """Point d'entrée principal"""
    
    # Vérification des dépendances
    if not check_and_install_requirements():
        print("\n❌ Installation des dépendances échouée")
        print("💡 Essayez manuellement : pip install -r requirements.txt")
        input("\nAppuyez sur Entrée pour quitter...")
        sys.exit(1)
    
    # Import de l'application (APRÈS vérification des dépendances)
    try:
        import tkinter as tk
        from gui.main_window import SunoMainWindow
    except ImportError as e:
        print(f"\n❌ Erreur d'import : {e}")
        print("💡 Essayez : pip install -r requirements.txt")
        input("\nAppuyez sur Entrée pour quitter...")
        sys.exit(1)
    
    # Lance l'application
    root = tk.Tk()
    app = SunoMainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()