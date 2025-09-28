#!/usr/bin/env python3
"""
Test du pipeline hybride (génération de code + contrats, sans blocage Gradle)
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire services/worker au PYTHONPATH
worker_path = Path(__file__).parent / "services" / "worker"
sys.path.insert(0, str(worker_path))

from worker.pipeline import run_pipeline
import yaml

def test_pipeline_hybrid():
    """Test du pipeline hybride"""
    print("🧪 Test du pipeline hybride (sans blocage Gradle)")
    
    # Charger la spec
    spec_file = "specs/examples/resa.yaml"
    with open(spec_file, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    
    print(f"✅ Spec chargée: {spec['app']['name']}")
    
    # Générer un run_id unique
    import uuid
    run_id = str(uuid.uuid4())
    
    print(f"🚀 Lancement du pipeline hybride")
    print(f"Run ID: {run_id}")
    print(f"Mode: hybride (génération rapide + contrats, build APK simulé)")
    
    # Exécuter le pipeline
    result = run_pipeline(run_id, spec_file, dry_run=False)
    
    # Afficher le résultat
    if result.get("success"):
        print(f"\n✅ Pipeline hybride réussi!")
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
        
        return True
    else:
        print(f"\n❌ Pipeline hybride échoué!")
        print(f"Erreur: {result.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    try:
        success = test_pipeline_hybrid()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
