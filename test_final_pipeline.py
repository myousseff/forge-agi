#!/usr/bin/env python3
"""
Test final du pipeline complet avec toutes les étapes
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire services/worker au PYTHONPATH
worker_path = Path(__file__).parent / "services" / "worker"
sys.path.insert(0, str(worker_path))

from worker.pipeline import run_pipeline
import yaml

def test_final_pipeline():
    """Test du pipeline final complet"""
    print("🧪 Test final du pipeline complet")
    
    # Charger la spec
    spec_file = "specs/examples/resa.yaml"
    with open(spec_file, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    
    print(f"✅ Spec chargée: {spec['app']['name']}")
    
    # Générer un run_id unique
    import uuid
    run_id = str(uuid.uuid4())
    
    print(f"🚀 Lancement du pipeline final")
    print(f"Run ID: {run_id}")
    
    # Exécuter le pipeline
    result = run_pipeline(run_id, spec_file, dry_run=False)
    
    # Afficher le résultat
    if result.get("success"):
        print(f"\n🎉 Pipeline final réussi!")
        print(f"Run ID: {run_id}")
        
        # Lister les étapes exécutées
        steps = result.get("steps", {})
        print(f"\n📋 Étapes exécutées:")
        for step_name, step_result in steps.items():
            status = "✅" if step_result.get("success", False) else "❌"
            print(f"  {status} {step_name}: {step_result.get('message', 'N/A')}")
        
        # Vérifier les artefacts
        work_dir = os.getenv('WORK_DIR', './work')
        artifacts_path = os.path.join(work_dir, run_id, 'artifacts')
        if os.path.exists(artifacts_path):
            print(f"\n📁 Artefacts créés dans {artifacts_path}:")
            for file in os.listdir(artifacts_path):
                file_path = os.path.join(artifacts_path, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"  - {file} ({size} bytes)")
                elif os.path.isdir(file_path):
                    print(f"  - {file}/ (dossier)")
        
        # Vérifier les fichiers critiques
        critical_files = [
            "openapi.yaml",
            "dart_client/lib/forge_client.dart",
            "db_schema.sql",
            "source.zip"
        ]
        
        print(f"\n🔍 Vérification des fichiers critiques:")
        for critical_file in critical_files:
            file_path = os.path.join(artifacts_path, critical_file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"  ✅ {critical_file} ({size} bytes)")
            else:
                print(f"  ❌ {critical_file} - MANQUANT")
        
        return True
    else:
        print(f"\n❌ Pipeline final échoué!")
        print(f"Erreur: {result.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    try:
        success = test_final_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
