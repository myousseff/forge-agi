#!/usr/bin/env python3
"""
Test uniquement de l'étape BUILD_APK
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire services/worker au PYTHONPATH
worker_path = Path(__file__).parent / "services" / "worker"
sys.path.insert(0, str(worker_path))

from worker.pipeline import run_build_apk

def test_build_apk_only():
    """Test uniquement de l'étape BUILD_APK"""
    print("🧪 Test uniquement de l'étape BUILD_APK")
    
    # Utiliser le dernier run_id créé
    work_dir = Path("./work")
    if not work_dir.exists():
        print("❌ Dossier work/ non trouvé")
        return False
    
    # Trouver le dernier run_id
    run_dirs = [d for d in work_dir.iterdir() if d.is_dir()]
    if not run_dirs:
        print("❌ Aucun run trouvé dans work/")
        return False
    
    # Prendre le plus récent
    latest_run = max(run_dirs, key=lambda d: d.stat().st_mtime)
    run_id = latest_run.name
    app_dir = latest_run / "app"
    
    print(f"✅ Utilisation du run: {run_id}")
    print(f"✅ Dossier app: {app_dir}")
    
    # Tester BUILD_APK
    result = run_build_apk(run_id, app_dir)
    
    print(f"\n📋 Résultat BUILD_APK:")
    print(f"  Success: {result.get('success')}")
    print(f"  Message: {result.get('message')}")
    print(f"  APK Path: {result.get('apk_path')}")
    
    if result.get('success'):
        print("✅ BUILD_APK réussi!")
        return True
    else:
        print(f"❌ BUILD_APK échoué: {result.get('error')}")
        return False

if __name__ == "__main__":
    try:
        success = test_build_apk_only()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
