#!/usr/bin/env python3
"""
Test simple de l'étape API_CONTRACTS sans le build Gradle complet
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire services/worker au PYTHONPATH
worker_path = Path(__file__).parent / "services" / "worker"
sys.path.insert(0, str(worker_path))

from worker.api_contracts import infer_endpoints_from_spec, render_openapi, write_artifacts, generate_dart_client_stub
from worker.db_schema import infer_entities_from_spec
import yaml

def test_api_contracts():
    """Test de l'étape API_CONTRACTS"""
    print("🧪 Test de l'étape API_CONTRACTS")
    
    # Charger la spec
    spec_file = "specs/examples/resa.yaml"
    with open(spec_file, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    
    print(f"✅ Spec chargée: {spec['app']['name']}")
    
    # Test 1: Inférer les endpoints
    endpoints = infer_endpoints_from_spec(spec)
    print(f"✅ Endpoints détectés: {len(endpoints)}")
    for endpoint in endpoints:
        print(f"  - {endpoint['method']} {endpoint['path']}")
    
    # Test 2: Inférer les entités
    entities = infer_entities_from_spec(spec)
    print(f"✅ Entités détectées: {len(entities)}")
    for entity in entities:
        print(f"  - {entity['name']} ({len(entity['fields'])} champs)")
    
    # Test 3: Générer OpenAPI
    openapi = render_openapi(endpoints, entities)
    print(f"✅ OpenAPI généré: {openapi['openapi']}")
    print(f"  - Paths: {len(openapi['paths'])}")
    print(f"  - Schemas: {len(openapi['components']['schemas'])}")
    
    # Test 4: Écrire les artefacts
    test_run_path = Path("test_api_contracts")
    if test_run_path.exists():
        import shutil
        shutil.rmtree(test_run_path)
    
    openapi_result = write_artifacts(test_run_path, openapi)
    print(f"✅ Artefacts OpenAPI créés: {openapi_result['files_created']}")
    
    # Test 5: Générer le client Dart
    dart_result = generate_dart_client_stub(openapi, test_run_path)
    print(f"✅ Client Dart généré: {dart_result['files_created']}")
    print(f"  - Modèles: {dart_result['models_generated']}")
    print(f"  - Entités supportées: {dart_result['entities_supported']}")
    
    # Vérifier les fichiers créés
    artifacts_dir = test_run_path / "artifacts"
    if artifacts_dir.exists():
        print(f"\n📁 Fichiers créés dans {artifacts_dir}:")
        for file in artifacts_dir.rglob("*"):
            if file.is_file():
                size = file.stat().st_size
                print(f"  - {file.relative_to(test_run_path)} ({size} bytes)")
    
    print("\n🎉 Test API_CONTRACTS réussi !")
    return True

if __name__ == "__main__":
    try:
        test_api_contracts()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
