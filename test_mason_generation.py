#!/usr/bin/env python3
"""
Test de la génération Flutter via Mason
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire services/worker au PYTHONPATH
worker_path = Path(__file__).parent / "services" / "worker"
sys.path.insert(0, str(worker_path))

def test_mason_generation():
    """Test de la génération Mason"""
    print("🔍 Test de la génération Flutter via Mason...")
    
    try:
        from worker.codegen import spec_to_vars, generate_app_from_spec
        from pathlib import Path
        
        print("✅ Imports réussis")
        
        # Test 1: Conversion spec vers vars
        print("\n1. Test conversion spec -> vars...")
        spec_path = Path("specs/examples/resa.yaml")
        
        if not spec_path.exists():
            print(f"❌ Spec non trouvée: {spec_path}")
            return False
        
        # Simuler la conversion (sans exécuter mason)
        import yaml
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)
        
        vars_obj = spec_to_vars(spec)
        print(f"   App name: {vars_obj['app_name']}")
        print(f"   Primary color: {vars_obj['primary_color']}")
        print(f"   Navigation: {vars_obj['navigation']}")
        print(f"   Entities: {len(vars_obj['entities'])}")
        
        # Test 2: Vérifier que la brick existe
        print("\n2. Test existence de la brick...")
        brick_dir = Path("bricks/mobile_app_base")
        if brick_dir.exists():
            print(f"✅ Brick trouvée: {brick_dir}")
            
            # Vérifier les fichiers de la brick
            brick_files = [
                "brick.yaml",
                "__brick__/pubspec.yaml",
                "__brick__/lib/main.dart",
                "__brick__/lib/app_router.dart"
            ]
            
            for file in brick_files:
                file_path = brick_dir / file
                if file_path.exists():
                    print(f"   ✅ {file}")
                else:
                    print(f"   ❌ {file} manquant")
                    return False
        else:
            print(f"❌ Brick non trouvée: {brick_dir}")
            return False
        
        print("\n🎉 Tests de structure Mason réussis!")
        print("\n📋 Pour tester la génération complète:")
        print("1. Builder l'image Flutter: docker compose -f infra/docker-compose.yml build runner_flutter")
        print("2. Lancer le pipeline: python scripts/dev_run_pipeline.py specs/examples/resa.yaml")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Test de la génération Mason Forge AGI\n")
    
    if test_mason_generation():
        print("\n✅ Tests réussis!")
    else:
        print("\n❌ Tests échoués!")
        sys.exit(1)
