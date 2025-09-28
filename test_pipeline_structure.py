#!/usr/bin/env python3
"""
Test simple pour vérifier la structure du pipeline
"""

import os
import sys
import json
import yaml
from pathlib import Path

def test_file_structure():
    """Test que tous les fichiers nécessaires existent"""
    print("🔍 Vérification de la structure des fichiers...")
    
    required_files = [
        "services/worker/requirements.txt",
        "services/worker/__init__.py",
        "services/worker/main.py",
        "services/worker/worker/__init__.py",
        "services/worker/worker/main.py",
        "services/worker/worker/pipeline.py",
        "services/worker/worker/critic.py",
        "services/worker/worker/judge.py",
        "services/worker/tests/test_pipeline.py",
        "scripts/dev_run_pipeline.py",
        "infra/docker/Dockerfile.worker",
        "infra/docker-compose.yml",
        "specs/examples/resa.yaml",
        "specs/schema/mobile-app-0.1.0.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Fichiers manquants:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print(f"\n✅ Tous les fichiers requis sont présents ({len(required_files)} fichiers)")
    return True

def test_spec_validation():
    """Test que la spec d'exemple peut être chargée"""
    print("\n🔍 Test de chargement de la spécification...")
    
    try:
        with open("specs/examples/resa.yaml", 'r', encoding='utf-8') as f:
            spec_data = yaml.safe_load(f)
        
        # Vérifier les sections requises
        required_sections = ['meta', 'app', 'data', 'ui', 'ci']
        missing_sections = []
        
        for section in required_sections:
            if section not in spec_data:
                missing_sections.append(section)
            else:
                print(f"✅ Section '{section}' présente")
        
        if missing_sections:
            print(f"❌ Sections manquantes: {missing_sections}")
            return False
        
        print(f"✅ Spécification valide - {len(spec_data)} sections principales")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la spec: {e}")
        return False

def test_schema_validation():
    """Test que le schéma JSON peut être chargé"""
    print("\n🔍 Test de chargement du schéma JSON...")
    
    try:
        # Essayer d'abord avec utf-8-sig pour gérer le BOM
        try:
            with open("specs/schema/mobile-app-0.1.0.json", 'r', encoding='utf-8-sig') as f:
                schema = json.load(f)
        except:
            # Si ça échoue, essayer avec utf-8 normal
            with open("specs/schema/mobile-app-0.1.0.json", 'r', encoding='utf-8') as f:
                schema = json.load(f)
        
        print(f"✅ Schéma JSON valide - version {schema.get('version', 'unknown')}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement du schéma: {e}")
        return False

def test_requirements():
    """Test que les dépendances sont correctement listées"""
    print("\n🔍 Test des dépendances...")
    
    try:
        with open("services/worker/requirements.txt", 'r') as f:
            requirements = f.read()
        
        required_packages = [
            "celery==5.3.6",
            "jsonschema==4.19.0",
            "rich==13.7.1",
            "click==8.1.7"
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
            else:
                print(f"✅ {package}")
        
        if missing_packages:
            print(f"❌ Packages manquants: {missing_packages}")
            return False
        
        print(f"✅ Toutes les dépendances requises sont présentes")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des dépendances: {e}")
        return False

def main():
    """Test principal"""
    print("🚀 Test de la structure du pipeline Forge AGI\n")
    
    tests = [
        test_file_structure,
        test_spec_validation,
        test_schema_validation,
        test_requirements
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés! Le pipeline est prêt.")
        print("\n📋 Prochaines étapes:")
        print("1. Installer Python 3.11+ et les dépendances")
        print("2. Lancer: python scripts/dev_run_pipeline.py specs/examples/resa.yaml")
        print("3. Ou avec Docker: docker compose -f infra/docker-compose.yml build worker")
        return True
    else:
        print("❌ Certains tests ont échoué. Vérifiez la structure.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
