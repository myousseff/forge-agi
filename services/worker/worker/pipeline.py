import os
import json
import yaml
import uuid
import zipfile
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from jsonschema import validate, ValidationError
import click
from rich.console import Console
from rich.table import Table
from . import codegen, db_schema, api_contracts
from .codegen import generate_app_from_spec
console = Console()

def run_pipeline(run_id: str, spec_path: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    Pipeline principal de génération d'application
    
    Args:
        run_id: Identifiant unique de l'exécution
        spec_path: Chemin vers le fichier de spécification
        dry_run: Mode test sans génération de code Flutter
    
    Returns:
        Dict contenant les résultats de chaque étape
    """
    console.print(f"[bold blue]🚀 Démarrage du pipeline - Run ID: {run_id}[/bold blue]")
    
    # Étape 1: VALIDATE_SPEC
    console.print("\n[bold green]1. VALIDATE_SPEC[/bold green]")
    validation_result = validate_spec(spec_path)
    if not validation_result["valid"]:
        return {"error": "Validation de la spécification échouée", "details": validation_result}
    
    spec_data = validation_result["spec_data"]
    
    # Étape 2: CRITIC
    console.print("\n[bold green]2. CRITIC[/bold green]")
    from .critic import run_critic
    critic_result = run_critic(spec_data)
    
    # Étape 3: CODEGEN_stub (génération rapide sans build APK)
    console.print("\n[bold green]3. CODEGEN_stub[/bold green]")
    work_dir = os.getenv('WORK_DIR', './work')
    run_path = Path(work_dir) / run_id
    app_dir = generate_app_from_spec(Path(spec_path), run_id=run_id, build_apk=True)  # build_apk=True pour build effectif
    codegen_result = {
        "success": True,
        "app_dir": str(app_dir),
        "message": "Application Flutter générée via Mason (avec build APK)"
    }
    
    # Étape 4: DB_SCHEMA
    console.print("\n[bold green]4. DB_SCHEMA[/bold green]")
    db_schema_result = run_db_schema(run_id, spec_data)
    
    # Étape 5: API_CONTRACTS
    console.print("\n[bold green]5. API_CONTRACTS[/bold green]")
    api_contracts_result = run_api_contracts(run_id, spec_data, db_schema_result)

    # Étape 6: BUILD_APK
    print("\n6. BUILD_APK")
    res_apk = None
    if os.environ.get("FORGE_BUILD_APK", "0") != "1":
        print("[skip] BUILD_APK (dev fast mode)")
    else:
        try:
            res_apk = codegen.run_build_apk(run_id, app_dir)
            print(f"APK: {res_apk.get('apk_path')}")
        except Exception as e:
            res_apk = {"success": False, "error": str(e)}
            print(f"[WARN] BUILD_APK failed: {e}")
        # On continue malgré tout pour l’instant (Phase 1): ne bloque pas le pipeline.

    # Étape 7: STATIC_CHECKS_stub
    console.print("\n[bold green]7. STATIC_CHECKS_stub[/bold green]")
    static_checks_result = run_static_checks_stub(run_id)
    
    # Étape 8: TESTS_stub
    console.print("\n[bold green]8. TESTS_stub[/bold green]")
    tests_result = run_tests_stub(run_id)
    
    # Étape 9: PACKAGE
    console.print("\n[bold green]9. PACKAGE[/bold green]")
    package_result = run_package(run_id, critic_result, static_checks_result, tests_result)
    
    # Étape 10: JUDGE
    console.print("\n[bold green]10. JUDGE[/bold green]")
    from .judge import run_judge
    judge_result = run_judge(critic_result, static_checks_result, tests_result)
    
    # Mettre à jour le rapport judge dans les artifacts
    work_dir = os.getenv('WORK_DIR', './work')
    judge_report_path = os.path.join(work_dir, run_id, 'artifacts', 'judge_report.json')
    if os.path.exists(judge_report_path):
        with open(judge_report_path, 'w', encoding='utf-8') as f:
            json.dump(judge_result, f, indent=2, ensure_ascii=False)
    
    # Résultat final
    final_result = {
        "run_id": run_id,
        "dry_run": dry_run,
        "steps": {
            "validate_spec": validation_result,
            "critic": critic_result,
            "codegen_stub": codegen_result,
            "db_schema": db_schema_result,
            "api_contracts": api_contracts_result,
            "static_checks_stub": static_checks_result,
            "tests_stub": tests_result,
            "build_apk": res_apk, # Use res_apk from the new BUILD_APK step
            "package": package_result,
            "judge": judge_result
        },
        "success": judge_result["decision"] == "accept"
    }
    
    color = 'green' if final_result['success'] else 'red'
    console.print(f"\n[bold {color}]✅ Pipeline terminé - Décision: {judge_result['decision']}[/bold {color}]")
    
    return final_result

def validate_spec(spec_path: str) -> Dict[str, Any]:
    """Valide la spécification avec le schéma JSON"""
    try:
        # Charger le schéma
        schema_path = os.getenv('SCHEMA_PATH', 'specs/schema/mobile-app-0.1.0.json')
        if not os.path.exists(schema_path):
            # Essayer le chemin relatif depuis le workspace
            workspace_path = os.getenv('WORKSPACE_PATH', '/workspace')
            schema_path = os.path.join(workspace_path, 'specs/schema/mobile-app-0.1.0.json')
        
        # Essayer d'abord avec utf-8-sig pour gérer le BOM
        try:
            with open(schema_path, 'r', encoding='utf-8-sig') as f:
                schema = json.load(f)
        except:
            # Si ça échoue, essayer avec utf-8 normal
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        
        # Charger la spécification
        with open(spec_path, 'r', encoding='utf-8') as f:
            if spec_path.endswith('.yaml') or spec_path.endswith('.yml'):
                spec_data = yaml.safe_load(f)
            else:
                spec_data = json.load(f)
        
        # Valider
        validate(instance=spec_data, schema=schema)
        
        return {
            "valid": True,
            "spec_data": spec_data,
            "message": "Spécification valide"
        }
    
    except (ValidationError, FileNotFoundError, yaml.YAMLError, json.JSONDecodeError) as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Erreur de validation"
        }



def run_codegen_stub(run_id: str, spec_path: str, spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crée la structure de base pour la génération de code"""
    work_dir = os.getenv('WORK_DIR', './work')
    run_path = os.path.join(work_dir, run_id)
    
    try:
        # Créer la structure de répertoires
        app_dir = os.path.join(run_path, 'app')
        artifacts_dir = os.path.join(run_path, 'artifacts')
        reports_dir = os.path.join(run_path, 'reports')
        
        os.makedirs(app_dir, exist_ok=True)
        os.makedirs(artifacts_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        
        # Copier la spécification
        spec_dest = os.path.join(run_path, 'spec.yml')
        with open(spec_path, 'r', encoding='utf-8') as src:
            with open(spec_dest, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        # Créer un README placeholder
        readme_content = f"""# Application générée - Run ID: {run_id}

Cette application a été générée automatiquement à partir de la spécification.

## Structure
- `app/` - Code source de l'application (généré plus tard)
- `artifacts/` - Artifacts de build et rapports
- `reports/` - Rapports d'analyse et tests
- `spec.yml` - Spécification source

## Informations
- Nom de l'app: {spec_data.get('app', {}).get('name', 'Unknown')}
- Bundle ID: {spec_data.get('app', {}).get('bundle_id_android', 'Unknown')}
- Généré le: {run_id}

## Prochaines étapes
1. Génération du code Flutter (via Mason)
2. Build de l'application
3. Tests automatisés
"""
        
        with open(os.path.join(run_path, 'README_PLACEHOLDER.txt'), 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return {
            "success": True,
            "run_path": run_path,
            "app_dir": app_dir,
            "artifacts_dir": artifacts_dir,
            "reports_dir": reports_dir,
            "spec_copied": True
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def run_static_checks_stub(run_id: str) -> Dict[str, Any]:
    """Placeholder pour les vérifications statiques"""
    return {
        "format_ok": True,
        "analyze_ok": True,
        "lint_ok": True,
        "message": "Vérifications statiques simulées (placeholder)"
    }

def run_tests_stub(run_id: str) -> Dict[str, Any]:
    """Placeholder pour les tests"""
    return {
        "tests_ok": True,
        "test_count": 0,
        "passed": 0,
        "failed": 0,
        "message": "Tests simulés (placeholder)"
    }
def run_db_schema(run_id: str, spec: dict) -> Dict[str, Any]:
    """Génère le schéma de base de données SQLite à partir de la spécification"""
    try:
        from .db_schema import infer_entities_from_spec, render_sql, write_artifacts
        from pathlib import Path
        
        work_dir = os.getenv('WORK_DIR', './work')
        run_path = Path(work_dir) / run_id
        
        # Inférer les entités depuis la spécification
        entities = infer_entities_from_spec(spec)
        
        # Générer le SQL
        sql = render_sql(entities)
        
        # Écrire les artefacts
        result = write_artifacts(run_path, sql, entities)
        
        return {
            "success": True,
            "entities_detected": len(entities),
            "tables": result["table_count"],
            "columns": result["column_count"],
            "files_created": result["files_created"],
            "message": f"Schéma DB généré: {result['table_count']} tables, {result['column_count']} colonnes"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Erreur lors de la génération du schéma DB"
        }


# ... existing code ...
def run_build_apk(run_id: str, app_dir: Path) -> Dict[str, Any]:
    """Exécute le build APK de manière robuste avec logs détaillés"""
    try:
        console.print("�� Build APK en cours...")
        
        # Vérifier si l'app existe
        if not app_dir.exists():
            console.print(f"❌ Dossier app non trouvé: {app_dir}")
            return {
                "success": False,
                "error": "Dossier app non trouvé",
                "apk_path": None
            }
        
        console.print(f"✅ Dossier app trouvé: {app_dir}")
        
        # Créer le dossier artifacts
        artifacts_dir = Path(f"./work/{run_id}/artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"✅ Dossier artifacts créé: {artifacts_dir}")
        
        # Vérifier que l'app Flutter est valide
        pubspec_path = app_dir / "pubspec.yaml"
        if not pubspec_path.exists():
            console.print("❌ pubspec.yaml non trouvé - app Flutter invalide")
            return {
                "success": False,
                "error": "pubspec.yaml non trouvé",
                "apk_path": None
            }
        
        console.print("✅ pubspec.yaml trouvé")
        
        # Vérifier la structure Android
        android_dir = app_dir / "android"
        if not android_dir.exists():
            console.print("❌ Dossier android/ non trouvé - scaffolding Android manquant")
            return {
                "success": False,
                "error": "Dossier android/ manquant",
                "apk_path": None
            }
        
        console.print("✅ Dossier android/ trouvé")
        
        # Exécuter le build APK via Docker avec timeout et logs détaillés
        console.print("�� Lancement du build APK via Docker...")
        
        import subprocess
        
        # Construire la commande Docker pour le build APK uniquement
        compose_file = str((Path(__file__).parent.parent.parent.parent / "infra" / "docker-compose.yml").as_posix())
        
        # COMMANDE SIMPLIFIÉE - Test étape par étape
        cmd = [
            "docker", "compose", "-f", compose_file, "run", "--rm",
            "-w", "/work",
            "runner_flutter",
            "bash", "-c",
            f"cd /work/{run_id}/app && flutter build apk --debug"
        ]
        
        console.print("🔧 Commande Docker simplifiée, exécution...")
        console.print(f"Commande: {' '.join(cmd)}")
        
        # Exécuter avec timeout et capture des logs
        result = subprocess.run(
            cmd, 
            cwd=str(Path(__file__).parent.parent.parent),
            timeout=300,  # 5 minutes max
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print("✅ Build APK réussi!")
            console.print(f"📝 Logs stdout: {result.stdout[-200:]}")  # Derniers 200 caractères
            
            # Vérifier si l'APK a été créé
            apk_path = artifacts_dir / "app-debug.apk"
            if apk_path.exists():
                apk_size = apk_path.stat().st_size
                console.print(f"✅ APK généré: {apk_path} ({apk_size} bytes)")
                
                return {
                    "success": True,
                    "apk_path": str(apk_path),
                    "apk_size": apk_size,
                    "build_logs": result.stdout,
                    "message": f"APK généré avec succès ({apk_size} bytes)"
                }
            else:
                console.print("❌ APK non trouvé après build réussi")
                return {
                    "success": False,
                    "error": "APK non trouvé après build réussi",
                    "build_logs": result.stdout,
                    "apk_path": None
                }
        else:
            console.print(f"❌ Build APK échoué (code {result.returncode})")
            console.print(f"📝 Logs stdout: {result.stdout}")
            console.print(f"📝 Logs stderr: {result.stderr}")
            
            return {
                "success": False,
                "error": f"Build APK échoué (code {result.returncode})",
                "build_logs": result.stdout,
                "build_errors": result.stderr,
                "apk_path": None
            }
            
    except subprocess.TimeoutExpired:
        console.print("⏰ Timeout après 5 minutes - build APK trop long")
        return {
            "success": False,
            "error": "Timeout après 5 minutes",
            "apk_path": None
        }
    except Exception as e:
        console.print(f"❌ Erreur lors du build APK: {e}")
        return {
            "success": False,
            "error": str(e),
            "apk_path": None
        }
# ... existing code ...
        


        console.print("✅ Dossier android/ trouvé")
        
        # Exécuter le build APK via Docker avec timeout et logs détaillés
        console.print("🚀 Lancement du build APK via Docker...")
        
        import subprocess
        import tempfile
        
        # Créer un fichier temporaire pour les variables
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_vars = {
                "app_name": "temp_build", 
                "primary_color": "#000000", 
                "navigation": "tabs", 
                "entities": []
            }
            json.dump(temp_vars, f)
            temp_vars_path = f.name
        
        try:
            # Construire la commande Docker pour le build APK uniquement
            compose_file = str((Path(__file__).parent.parent.parent.parent / "infra" / "docker-compose.yml").as_posix())
            
            cmd = [
                "docker", "compose", "-f", compose_file, "run", "--rm",
                "-w", "/work",
                "runner_flutter",
                "bash", "-c",
                f"""
                set -e
                echo '[build] Vérification de l\'environnement Flutter'
                flutter --version
                echo '[build] Vérification de l\'environnement Android'
                flutter doctor -v
                echo '[build] Navigation vers le dossier app'
                cd /work/{run_id}/app
                echo '[build] Vérification des dépendances'
                flutter pub get
                echo '[build] Vérification de la structure Android'
                ls -la android/
                echo '[build] Lancement du build APK debug'
                flutter build apk --debug --verbose
                echo '[build] Vérification du résultat'
                ls -la build/app/outputs/flutter-apk/
                echo '[build] Copie de l\'APK vers artifacts'
                mkdir -p /work/{run_id}/artifacts
                if [ -f build/app/outputs/flutter-apk/app-debug.apk ]; then
                    cp build/app/outputs/flutter-apk/app-debug.apk /work/{run_id}/artifacts/app-debug.apk
                    echo '✅ APK copié: /work/{run_id}/artifacts/app-debug.apk'
                    ls -la /work/{run_id}/artifacts/app-debug.apk
                else
                    echo '❌ APK non trouvé après build'
                    find build/ -name "*.apk" -type f
                    exit 1
                fi
                echo '[build] Build APK terminé avec succès'
                """
            ]
            
            console.print("🔧 Commande Docker construite, exécution...")
            
            # Exécuter avec timeout et capture des logs
            result = subprocess.run(
                cmd, 
                cwd=str(Path(__file__).parent.parent.parent),
                timeout=600,  # 10 minutes max
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                console.print("✅ Build APK réussi!")
                console.print(f"📝 Logs stdout: {result.stdout[-500:]}")  # Derniers 500 caractères
                
                # Vérifier si l'APK a été créé
                apk_path = artifacts_dir / "app-debug.apk"
                if apk_path.exists():
                    apk_size = apk_path.stat().st_size
                    console.print(f"✅ APK généré: {apk_path} ({apk_size} bytes)")
                    
                    return {
                        "success": True,
                        "apk_path": str(apk_path),
                        "apk_size": apk_size,
                        "build_logs": result.stdout,
                        "message": f"APK généré avec succès ({apk_size} bytes)"
                    }
                else:
                    console.print("❌ APK non trouvé après build réussi")
                    return {
                        "success": False,
                        "error": "APK non trouvé après build réussi",
                        "build_logs": result.stdout,
                        "apk_path": None
                    }
            else:
                console.print(f"❌ Build APK échoué (code {result.returncode})")
                console.print(f"📝 Logs stdout: {result.stdout}")
                console.print(f"📝 Logs stderr: {result.stderr}")
                
                return {
                    "success": False,
                    "error": f"Build APK échoué (code {result.returncode})",
                    "build_logs": result.stdout,
                    "build_errors": result.stderr,
                    "apk_path": None
                }
                
        except subprocess.TimeoutExpired:
            console.print("⏰ Timeout après 10 minutes - build APK trop long")
            return {
                "success": False,
                "error": "Timeout après 10 minutes",
                "apk_path": None
            }
        except Exception as e:
            console.print(f"❌ Erreur lors du build APK: {e}")
            return {
                "success": False,
                "error": str(e),
                "apk_path": None
            }
        finally:
            # Nettoyer le fichier temporaire
            os.unlink(temp_vars_path)
            
    except Exception as e:
        console.print(f"❌ Erreur fatale dans run_build_apk: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "apk_path": None
        }


def run_api_contracts(run_id: str, spec: dict, db_schema_result: Dict[str, Any]) -> Dict[str, Any]:
    """Génère les contrats OpenAPI et le client Dart stub"""
    try:
        from .api_contracts import infer_endpoints_from_spec, render_openapi, write_artifacts, generate_dart_client_stub
        from pathlib import Path
        
        work_dir = os.getenv('WORK_DIR', './work')
        run_path = Path(work_dir) / run_id
        
        # Inférer les endpoints depuis la spécification
        endpoints = infer_endpoints_from_spec(spec)
        
        # Récupérer les entités depuis le résultat de DB_SCHEMA
        entities = []
        if db_schema_result.get("success"):
            # Re-extraire les entités depuis la spec (plus simple que de passer les entités)
            from .db_schema import infer_entities_from_spec
            entities = infer_entities_from_spec(spec)
        
        # Générer la spécification OpenAPI
        openapi = render_openapi(endpoints, entities)
        
        # Écrire les artefacts OpenAPI
        openapi_result = write_artifacts(run_path, openapi)
        
        # Générer le client Dart stub
        dart_result = generate_dart_client_stub(openapi, run_path / "artifacts")
        
        return {
            "success": True,
            "endpoints_detected": len(endpoints),
            "entities_supported": len(entities),
            "openapi_files": openapi_result["files_created"],
            "dart_client_files": dart_result["files_created"],
            "models_generated": dart_result.get("models_generated", 0),
            "message": f"Contrats API générés: {len(endpoints)} endpoints, {len(entities)} entités"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Erreur lors de la génération des contrats API"
        }

def run_package(run_id: str, critic_result: Dict[str, Any], static_checks_result: Dict[str, Any], tests_result: Dict[str, Any]) -> Dict[str, Any]:
    """Empaquette les résultats et calcule les checksums"""
    work_dir = os.getenv('WORK_DIR', './work')
    run_path = os.path.join(work_dir, run_id)
    artifacts_dir = os.path.join(run_path, 'artifacts')
    
    try:
        # Créer le répertoire artifacts s'il n'existe pas
        os.makedirs(artifacts_dir, exist_ok=True)
        
        # Créer le zip du dossier app (excluant android/, build/, etc.)
        app_dir = os.path.join(run_path, 'app')
        source_zip_path = os.path.join(artifacts_dir, 'source.zip')
        
        # Utiliser la fonction de zip filtré pour exclure les dossiers lourds
        from services.worker.worker.codegen import _zip_deterministic_filtered
        _zip_deterministic_filtered(Path(source_zip_path), Path(app_dir))
        print("✅ source.zip créé (android/ et build/ exclus)")
        
        # Copier spec.yml dans artifacts
        spec_src = os.path.join(run_path, 'spec.yml')
        spec_dest = os.path.join(artifacts_dir, 'spec.yml')
        if os.path.exists(spec_src):
            with open(spec_src, 'rb') as src:
                with open(spec_dest, 'wb') as dst:
                    dst.write(src.read())
        
        # Copier app-release.apk ou app-debug.apk si présent
        apk_src_release = os.path.join(run_path, 'app', 'build', 'app', 'outputs', 'flutter-apk', 'app-release.apk')
        apk_src_debug = os.path.join(run_path, 'app', 'build', 'app', 'outputs', 'flutter-apk', 'app-debug.apk')
        
        if os.path.exists(apk_src_release):
            apk_dest = os.path.join(artifacts_dir, 'app-release.apk')
            with open(apk_src_release, 'rb') as src:
                with open(apk_dest, 'wb') as dst:
                    dst.write(src.read())
            print(f"✅ APK Release copié: {apk_dest}")
        elif os.path.exists(apk_src_debug):
            apk_dest = os.path.join(artifacts_dir, 'app-debug.apk')
            with open(apk_src_debug, 'rb') as src:
                with open(apk_dest, 'wb') as dst:
                    dst.write(src.read())
            print(f"✅ APK Debug copié: {apk_dest}")
        else:
            print("⚠️ Aucun APK trouvé")
        
        # Copier README_PLACEHOLDER.txt si présent
        readme_src = os.path.join(run_path, 'README_PLACEHOLDER.txt')
        if os.path.exists(readme_src):
            readme_dest = os.path.join(artifacts_dir, 'README_PLACEHOLDER.txt')
            with open(readme_src, 'rb') as src:
                with open(readme_dest, 'wb') as dst:
                    dst.write(src.read())
        
        # Générer README.md dans artifacts/
        try:
            spec_data = {}
            spec_file = os.path.join(run_path, 'spec.yml')
            if os.path.exists(spec_file):
                import yaml
                with open(spec_file, 'r', encoding='utf-8') as f:
                    spec_data = yaml.safe_load(f)
            
            app_name = spec_data.get('app', {}).get('name', 'Application Mobile')
            bundle_id = spec_data.get('app', {}).get('bundle_id_android', 'com.example.app')
            
            readme_content = f"""# {app_name}

Application mobile générée par Forge AGI.

## Informations
- **Nom**: {app_name}
- **Bundle ID**: {bundle_id}
- **Généré le**: {run_id}
- **Type**: Application Flutter

## Installation

### APK
1. Télécharger `app-release.apk` depuis les artifacts
2. Installer sur un appareil Android (sources inconnues activées)

### Source
1. Extraire `source.zip`
2. Exécuter `flutter pub get`
3. Exécuter `flutter run`

## Build
```bash
flutter build apk --release
```

## Tests
```bash
flutter test
```

## Spécification
Voir `spec.yml` pour les détails de la configuration.
"""
            
            readme_path = os.path.join(artifacts_dir, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"✅ README.md généré: {readme_path}")
        except Exception as e:
            print(f"⚠️  Erreur génération README: {e}")
        
        # Écrire les rapports JSON
        reports = {
            'critic_report.json': critic_result,
            'verifier_report.json': static_checks_result,
            'judge_report.json': tests_result  # Temporaire, sera mis à jour après judge
        }
        
        for filename, report_data in reports.items():
            report_path = os.path.join(artifacts_dir, filename)
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Calculer les checksums
        checksums = {}
        for filename in os.listdir(artifacts_dir):
            file_path = os.path.join(artifacts_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                    checksums[filename] = hashlib.sha256(content).hexdigest()
        
        # Écrire le fichier checksums.txt
        checksums_path = os.path.join(artifacts_dir, 'checksums.txt')
        with open(checksums_path, 'w', encoding='utf-8') as f:
            for filename, checksum in checksums.items():
                f.write(f"{checksum}  {filename}\n")
        
        return {
            "success": True,
            "artifacts_dir": artifacts_dir,
            "files_created": list(checksums.keys()),
            "checksums": checksums
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



@click.command()
@click.option('--spec', required=True, help='Chemin vers le fichier de spécification')
@click.option('--run-id', default=None, help='ID de run (généré automatiquement si non fourni)')
@click.option('--dry-run', is_flag=True, default=True, help='Mode dry-run (par défaut)')
def cli(spec: str, run_id: str, dry_run: bool):
    """CLI pour exécuter le pipeline en local"""
    if run_id is None:
        run_id = str(uuid.uuid4())
    
    console.print(f"[bold blue]Pipeline CLI - Spec: {spec}, Run ID: {run_id}[/bold blue]")
    
    result = run_pipeline(run_id, spec, dry_run)
    
    # Afficher le résultat
    if result.get("success"):
        console.print(f"\n[bold green]✅ Pipeline réussi![/bold green]")
        console.print(f"Run ID: {run_id}")
        console.print(f"Artifacts: {os.path.join(os.getenv('WORK_DIR', '/work'), run_id, 'artifacts')}")
    else:
        console.print(f"\n[bold red]❌ Pipeline échoué![/bold red]")
        console.print(f"Erreur: {result.get('error', 'Unknown error')}")

if __name__ == '__main__':
    cli()
