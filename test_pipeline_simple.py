#!/usr/bin/env python3
"""
Test simple du pipeline étape par étape
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire services/worker au PYTHONPATH
worker_path = Path(__file__).parent / "services" / "worker"
sys.path.insert(0, str(worker_path))

def test_pipeline_steps():
    """Test chaque étape du pipeline individuellement"""
    print("🔍 Test du pipeline étape par étape...")
    
    try:
        from worker.pipeline import validate_spec, run_codegen_stub, run_static_checks_stub, run_tests_stub, run_package
        from worker.critic import run_critic as critic_module
        from worker.judge import run_judge as judge_module
        
        print("✅ Imports réussis")
        
        # Test 1: Validation de la spec
        print("\n1. Test VALIDATE_SPEC...")
        result = validate_spec("specs/examples/resa.yaml")
        print(f"   Résultat: {result.get('valid', False)}")
        if result.get('valid'):
            print("   ✅ Validation réussie")
        else:
            print(f"   ❌ Erreur: {result.get('error', 'Unknown')}")
            return False
        
        # Test 2: CRITIC
        print("\n2. Test CRITIC...")
        spec_data = result['spec_data']
        critic_result = critic_module(spec_data)
        print(f"   Problèmes critiques: {critic_result.get('critical_count', 0)}")
        print(f"   Problèmes warnings: {critic_result.get('warning_count', 0)}")
        
        # Test 3: CODEGEN_stub
        print("\n3. Test CODEGEN_stub...")
        run_id = "test-run-123"
        codegen_result = run_codegen_stub(run_id, "specs/examples/resa.yaml", spec_data)
        print(f"   Succès: {codegen_result.get('success', False)}")
        if codegen_result.get('success'):
            print(f"   Dossier créé: {codegen_result.get('run_path', 'Unknown')}")
        else:
            print(f"   ❌ Erreur: {codegen_result.get('error', 'Unknown')}")
            return False
        
        # Test 4: STATIC_CHECKS_stub
        print("\n4. Test STATIC_CHECKS_stub...")
        static_result = run_static_checks_stub(run_id)
        print(f"   Format OK: {static_result.get('format_ok', False)}")
        print(f"   Analyze OK: {static_result.get('analyze_ok', False)}")
        
        # Test 5: TESTS_stub
        print("\n5. Test TESTS_stub...")
        tests_result = run_tests_stub(run_id)
        print(f"   Tests OK: {tests_result.get('tests_ok', False)}")
        
        # Test 6: PACKAGE
        print("\n6. Test PACKAGE...")
        package_result = run_package(run_id, critic_result, static_result, tests_result)
        print(f"   Succès: {package_result.get('success', False)}")
        if package_result.get('success'):
            print(f"   Fichiers créés: {len(package_result.get('files_created', []))}")
        else:
            print(f"   ❌ Erreur: {package_result.get('error', 'Unknown')}")
            return False
        
        # Test 7: JUDGE
        print("\n7. Test JUDGE...")
        judge_result = judge_module(critic_result, static_result, tests_result)
        print(f"   Décision: {judge_result.get('decision', 'unknown')}")
        print(f"   Raison: {judge_result.get('reason', 'unknown')}")
        
        print("\n🎉 Tous les tests du pipeline sont passés!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_artifacts():
    """Vérifier que les artifacts ont été créés"""
    print("\n🔍 Vérification des artifacts...")
    
    work_dir = os.getenv('WORK_DIR', './work')
    test_run_id = "test-run-123"
    artifacts_path = os.path.join(work_dir, test_run_id, 'artifacts')
    
    if os.path.exists(artifacts_path):
        print(f"✅ Dossier artifacts trouvé: {artifacts_path}")
        files = os.listdir(artifacts_path)
        print(f"   Fichiers créés ({len(files)}):")
        for file in files:
            file_path = os.path.join(artifacts_path, file)
            size = os.path.getsize(file_path)
            print(f"   - {file} ({size} bytes)")
        return True
    else:
        print(f"❌ Dossier artifacts non trouvé: {artifacts_path}")
        return False

if __name__ == '__main__':
    print("🚀 Test simple du pipeline Forge AGI\n")
    
    # Test du pipeline
    if test_pipeline_steps():
        # Test des artifacts
        test_artifacts()
    else:
        print("❌ Test du pipeline échoué")
        sys.exit(1)
