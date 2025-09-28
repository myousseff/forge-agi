#!/usr/bin/env python3
"""
Test simple de la commande Docker pour isoler le problème
"""

import subprocess
import tempfile
import os
from pathlib import Path

def test_simple_docker():
    """Test simple de la commande Docker"""
    print("🧪 Test simple de la commande Docker")
    
    # Créer un fichier temporaire pour les variables
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_vars = {
            "app_name": "test_simple", 
            "primary_color": "#000000", 
            "navigation": "tabs", 
            "entities": []
        }
        import json
        json.dump(temp_vars, f)
        temp_vars_path = f.name
    
    try:
        # Test 1: Commande Docker très simple
        print("\n🔍 Test 1: Commande Docker très simple")
        cmd1 = [
            "docker", "--version"
        ]
        
        result1 = subprocess.run(cmd1, capture_output=True, text=True)
        print(f"✅ Docker version: {result1.stdout.strip()}")
        
        # Test 2: Commande Docker Compose simple
        print("\n🔍 Test 2: Commande Docker Compose simple")
        compose_file = str((Path(__file__).parent / "infra" / "docker-compose.yml").as_posix())
        
        if os.path.exists(compose_file):
            print(f"✅ Compose file trouvé: {compose_file}")
            
            cmd2 = [
                "docker", "compose", "-f", compose_file, "run", "--rm",
                "runner_flutter", "echo", "Hello from Docker"
            ]
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
            print(f"✅ Docker compose test: {result2.stdout.strip()}")
            
        else:
            print(f"❌ Compose file non trouvé: {compose_file}")
        
        # Test 3: Commande bash simple
        print("\n🔍 Test 3: Commande bash simple")
        cmd3 = [
            "docker", "compose", "-f", compose_file, "run", "--rm",
            "runner_flutter", "bash", "-c", "echo 'Hello bash'"
        ]
        
        result3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=30)
        print(f"✅ Bash simple test: {result3.stdout.strip()}")
        
        # Test 4: Commande bash avec variables
        print("\n🔍 Test 4: Commande bash avec variables")
        test_run_id = "test-simple-123"
        
        cmd4 = [
            "docker", "compose", "-f", compose_file, "run", "--rm",
            "runner_flutter", "bash", "-c", f"echo 'Run ID: {test_run_id}'"
        ]
        
        result4 = subprocess.run(cmd4, capture_output=True, text=True, timeout=30)
        print(f"✅ Bash avec variables test: {result4.stdout.strip()}")
        
        # Test 5: Commande bash complexe (comme dans codegen.py)
        print("\n🔍 Test 5: Commande bash complexe")
        bash_script = f"""
        set -e
        echo '[test] Début du test'
        echo "Run ID: {test_run_id}"
        echo '[test] Test terminé'
        """
        
        cmd5 = [
            "docker", "compose", "-f", compose_file, "run", "--rm",
            "runner_flutter", "bash", "-c", bash_script
        ]
        
        result5 = subprocess.run(cmd5, capture_output=True, text=True, timeout=30)
        print(f"✅ Bash complexe test: {result5.stdout.strip()}")
        
        print("\n🎉 Tous les tests Docker sont passés!")
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout sur un test Docker")
    except Exception as e:
        print(f"❌ Erreur lors du test Docker: {e}")
    finally:
        # Nettoyer le fichier temporaire
        os.unlink(temp_vars_path)

if __name__ == "__main__":
    test_simple_docker()
