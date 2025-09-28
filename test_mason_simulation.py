#!/usr/bin/env python3
"""
Test de simulation de la génération Mason (sans Docker)
"""

import sys
import os
import json
import yaml
from pathlib import Path

# Ajouter le répertoire services/worker au PYTHONPATH
worker_path = Path(__file__).parent / "services" / "worker"
sys.path.insert(0, str(worker_path))

def test_mason_simulation():
    """Test de simulation de la génération Mason"""
    print("🔍 Test de simulation de la génération Mason...")
    
    try:
        from worker.codegen import spec_to_vars, WORK_DIR
        from pathlib import Path
        
        print("✅ Imports réussis")
        
        # Test 1: Conversion spec vers vars
        print("\n1. Test conversion spec -> vars...")
        spec_path = Path("specs/examples/resa.yaml")
        
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec = yaml.safe_load(f)
        
        vars_obj = spec_to_vars(spec)
        print(f"   App name: {vars_obj['app_name']}")
        print(f"   Primary color: {vars_obj['primary_color']}")
        print(f"   Navigation: {vars_obj['navigation']}")
        print(f"   Entities: {len(vars_obj['entities'])}")
        
        # Test 2: Simulation de la création des fichiers
        print("\n2. Test simulation création fichiers...")
        run_id = "test-mason-simulation"
        run_root = WORK_DIR / run_id
        app_dir = run_root / "app"
        vars_path = run_root / "vars.json"
        
        # Créer les dossiers
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Écrire le fichier vars.json
        vars_path.write_text(json.dumps(vars_obj, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   ✅ Vars JSON créé: {vars_path}")
        
        # Simuler la création de l'app Flutter
        pubspec_content = f"""name: {vars_obj['app_name'].lower().replace(' ', '_')}
description: "Généré par Forge AGI (brick mobile_app_base)"
publish_to: "none"
environment:
  sdk: ">=3.0.0 <4.0.0"
dependencies:
  flutter: 
    sdk: flutter
  hooks_riverpod: ^2.5.1
  go_router: ^14.2.0
  freezed_annotation: ^2.4.4
  json_annotation: ^4.9.0
dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.9
  freezed: ^2.5.7
  json_serializable: ^6.8.0
flutter:
  uses-material-design: true
"""
        
        pubspec_path = app_dir / "pubspec.yaml"
        pubspec_path.write_text(pubspec_content, encoding="utf-8")
        print(f"   ✅ Pubspec créé: {pubspec_path}")
        
        # Créer la structure lib/
        lib_dir = app_dir / "lib"
        lib_dir.mkdir(exist_ok=True)
        
        main_content = f"""import 'package:flutter/material.dart';
import 'app_router.dart';

void main() {{
  runApp(ForgeApp());
}}

class ForgeApp extends StatelessWidget {{
  @override
  Widget build(BuildContext context) {{
    final theme = ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF{vars_obj['primary_color'].replace('#', '')})),
      useMaterial3: true,
    );
    return MaterialApp.router(
      title: '{vars_obj['app_name']}',
      theme: theme,
      routerConfig: buildRouter(),
    );
  }}
}}
"""
        
        main_path = lib_dir / "main.dart"
        main_path.write_text(main_content, encoding="utf-8")
        print(f"   ✅ Main.dart créé: {main_path}")
        
        # Test 3: Vérifier les fichiers créés
        print("\n3. Test vérification fichiers...")
        created_files = [
            vars_path,
            pubspec_path,
            main_path
        ]
        
        for file_path in created_files:
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"   ✅ {file_path.name} ({size} bytes)")
            else:
                print(f"   ❌ {file_path.name} manquant")
                return False
        
        print(f"\n🎉 Simulation réussie! App générée dans: {app_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Test de simulation Mason Forge AGI\n")
    
    if test_mason_simulation():
        print("\n✅ Simulation réussie!")
    else:
        print("\n❌ Simulation échouée!")
        sys.exit(1)
