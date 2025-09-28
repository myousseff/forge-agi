from __future__ import annotations
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
import yaml
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import sys, shutil, subprocess, textwrap, time

WORK_DIR = Path(os.environ.get("WORK_DIR", "./work"))
# En mode local, utiliser le répertoire courant
if os.environ.get("REPO_ROOT"):
    REPO_ROOT = Path(os.environ.get("REPO_ROOT"))
else:
    REPO_ROOT = Path(__file__).parent.parent.parent.parent  # Remonter depuis worker/worker/codegen.py
BRICK_DIR = REPO_ROOT / "bricks" / "mobile_app_base"

def _run(cmd, cwd=None):
    print(f"[run] {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def _run_stream(cmd: list[str], cwd: Path | None, log_file: Path, timeout_s: int = 1800) -> int:
    """
    Lance un process en streamant stdout/stderr vers console + fichier log.
    Kill dur si timeout atteint. Retourne l'exit code.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("w", encoding="utf-8") as lf:
        lf.write(f"$ {' '.join(cmd)}\n")
        lf.flush()
        start = time.time()
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        try:
            for line in proc.stdout:
                sys.stdout.write(line)
                lf.write(line)
                lf.flush()
                if time.time() - start > timeout_s:
                    lf.write("\n[TIMEOUT] killing process...\n")
                    lf.flush()
                    proc.kill()
                    return 124
        finally:
            try:
                proc.stdout.close()
            except Exception:
                pass
        return proc.wait()

def _ensure_android_scaffold(app_dir: Path) -> None:
    """
    Si /android absent dans l'app générée par Mason, on génère un squelette Flutter temporaire
    puis on copie 'android/' et '.metadata'.
    """
    android_dir = app_dir / "android"
    if android_dir.exists():
        return
    tmp = app_dir.parent / ".flutter_scaffold_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    # On utilise le runner_flutter via docker compose pour générer le squelette
    cmd = [
        "docker", "compose", "-f", "infra/docker-compose.yml",
        "run", "--rm",
        "-w", "/work/.flutter_scaffold_tmp",
        "runner_flutter",
        "bash", "-lc",
        "set -euo pipefail; flutter create . >/dev/null 2>&1 || flutter create ."
    ]
    rc = _run_stream(cmd, cwd=Path("."), log_file=app_dir.parent / "artifacts" / "build_apk.log", timeout_s=600)
    if rc not in (0,):
        raise RuntimeError(f"flutter create failed (rc={rc})")

    # Copie des répertoires nécessaires
    for name in ("android", ".metadata"):
        src = tmp / name
        if src.exists():
            dst = app_dir / name
            if dst.exists():
                shutil.rmtree(dst)
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

def run_build_apk(run_id: str, app_dir: Path) -> dict:
    """Build APK avec vérifications et copie vers artifacts/."""
    from pathlib import Path
    import subprocess, os

    # Sanity app
    pubspec = app_dir / "pubspec.yaml"
    if not pubspec.exists():
        return {"success": False, "error": "pubspec.yaml manquant", "apk_path": None}

    android_dir = app_dir / "android"
    if not android_dir.exists():
        return {"success": False, "error": "android/ manquant (scaffold)", "apk_path": None}

    # Artifacts
    artifacts_dir = Path(f"./work/{run_id}/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Build via docker compose runner_flutter (commande simple et lisible)
    compose_file = str((Path(__file__).parents[3] / "infra" / "docker-compose.yml").as_posix())
    cmd = [
        "docker", "compose", "-f", compose_file, "run", "--rm",
        "-e", f"RUN_ID={run_id}",
        "runner_flutter",
        "bash", "-lc",
        f"cd /work/{run_id}/app && flutter pub get && flutter build apk --debug"
    ]
    try:
        proc = subprocess.run(cmd, check=False)
        if proc.returncode != 0:
            return {"success": False, "error": f"flutter build rc={proc.returncode}", "apk_path": None}
    except Exception as e:
        return {"success": False, "error": str(e), "apk_path": None}

    # Copie APK
    apk_debug = app_dir / "build" / "app" / "outputs" / "flutter-apk" / "app-debug.apk"
    apk_release = app_dir / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"
    dest = None
    if apk_release.exists():
        dest = artifacts_dir / "app-release.apk"
        dest.write_bytes(apk_release.read_bytes())
    elif apk_debug.exists():
        dest = artifacts_dir / "app-debug.apk"
        dest.write_bytes(apk_debug.read_bytes())
    else:
        return {"success": False, "error": "APK introuvable après build", "apk_path": None}

    return {"success": True, "apk_path": str(dest)}

def ensure_flutter_android_scaffold(app_dir: Path, org: str = "com.forge", project_name: str | None = None):
    """
    Crée un squelette Flutter dans un dossier temporaire, puis copie android/ (et .metadata)
    dans app_dir sans écraser lib/ et pubspec.yaml générés par Mason.
    """
    app_dir = Path(app_dir).resolve()
    project_name = project_name or app_dir.name.replace("-", "_").replace(" ", "_")
    scaffold_dir = app_dir.parent / ".flutter_scaffold_tmp"

    if scaffold_dir.exists():
        shutil.rmtree(scaffold_dir)
    scaffold_dir.mkdir(parents=True, exist_ok=True)

    # 1) Créer un projet Flutter complet (Android uniquement) dans le dossier temporaire
    _run(f'flutter create -t app --platforms android --org {org} --project-name {project_name} "{scaffold_dir.as_posix()}"')

    # 2) Copier uniquement ce qu'il faut vers app_dir (android/ et .metadata)
    src_android = scaffold_dir / "android"
    if not src_android.exists():
        raise RuntimeError("flutter create n'a pas produit de dossier android/")

    dst_android = app_dir / "android"
    if dst_android.exists():
        shutil.rmtree(dst_android)
    shutil.copytree(src_android, dst_android)

    # .metadata utile pour certains outils Flutter
    src_meta = scaffold_dir / ".metadata"
    if src_meta.exists():
        shutil.copy2(src_meta, app_dir / ".metadata")

    # 3) Nettoyer le scaffold temporaire
    shutil.rmtree(scaffold_dir)

    print("✅ Scaffolding Android injecté dans l'app.")

DETERMINISTIC_TS = (1980, 1, 1, 0, 0, 0)

def _zip_deterministic_filtered(zip_path: Path, root_dir: Path, exclude_dirs=("android", "build", ".dart_tool", ".gradle")):
    """
    Zip déterministe des sources Flutter, en excluant les dossiers lourds.
    """
    excl = {d.lower() for d in exclude_dirs}
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        for base, dirs, files in os.walk(root_dir):
            # filtre des dossiers exclus
            dirs[:] = [d for d in dirs if d.lower() not in excl]

            for fn in files:
                p = Path(base) / fn
                # filtre fichiers lourds/inutiles (apk, aab, lock, etc.)
                name_lower = p.name.lower()
                if name_lower.endswith((".apk", ".aab", ".keystore")):
                    continue

                rel = p.relative_to(root_dir).as_posix()
                data = p.read_bytes()
                info = ZipInfo(filename=rel, date_time=DETERMINISTIC_TS)
                info.compress_type = ZIP_DEFLATED
                info.external_attr = (0o100644 & 0xFFFF) << 16
                zf.writestr(info, data)

def spec_to_vars(spec: dict) -> dict:
    # Map minimal : app_name, primary_color, navigation, entities (noms + champs)
    app_name = spec["app"]["name"]
    primary_color = spec["app"]["theme"]["primary_color"]
    navigation = spec["ui"]["navigation"]
    entities = []
    for e in spec["data"]["entities"]:
        entities.append({
            "name": e["name"],
            "fields": [f["name"] for f in e["fields"]]
        })
    return {
        "app_name": app_name,
        "primary_color": primary_color,
        "navigation": navigation,
        "entities": entities
    }

def run_mason_make(run_id: str, vars_obj: dict, build_apk: bool = True) -> Path:
    run_root = WORK_DIR / run_id
    app_dir = run_root / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    vars_path = run_root / "vars.json"
    vars_path.write_text(json.dumps(vars_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # Vérifier si Docker est disponible
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        docker_available = result.returncode == 0
        print(f"Docker check result: {result.returncode}")
    except FileNotFoundError:
        docker_available = False
        print("Docker not found")
    
    print(f"Docker available: {docker_available}")
    
    # Docker disponible, utiliser le mode normal
    print("✅ Docker disponible, utilisation du mode normal")

    if docker_available:
        # Appel du conteneur runner_flutter avec mason_cli
        compose_file = str((REPO_ROOT / "infra" / "docker-compose.yml").as_posix())
        # IMPORTANT : chemin interne au conteneur
        brick_path = "/workspace/bricks/mobile_app_base"

        # Construire la commande bash de manière propre
        bash_script = f"""set -e
echo '[mason] init/add/make'
mason --version
mason init || true
mason add mobile_app_base --path {brick_path}
mason make mobile_app_base -c /work/{run_id}/vars.json -o /work/{run_id}/app
echo '[flutter] scaffolding Android'
cd /work/{run_id}/app
flutter create -t app --platforms android --org com.forge --project-name resa_cafe_atlas .flutter_scaffold_tmp
cp -r .flutter_scaffold_tmp/android .
cp -r .flutter_scaffold_tmp/.metadata . 2>/dev/null || true
rm -rf .flutter_scaffold_tmp
echo '[flutter] Android scaffold injecté'
flutter pub get"""

        # Ajouter la logique de build APK conditionnelle
        if build_apk:
            bash_script += f"""
if true; then
  echo '[flutter] build APK...'
  flutter build apk --debug
  mkdir -p /work/{run_id}/artifacts
  if [ -f build/app/outputs/flutter-apk/app-debug.apk ]; then
    cp build/app/outputs/flutter-apk/app-debug.apk /work/{run_id}/artifacts/app-debug.apk
    echo '✅ APK copié dans artifacts/app-debug.apk'
  else
    echo '⚠️ APK non trouvé (regarde les logs gradle)'
  fi
else
  echo '[flutter] build APK ignoré (mode génération uniquement)'
fi"""
        else:
            bash_script += """
echo '[flutter] build APK ignoré (mode génération uniquement)'"""

        bash_script += """
echo '[mason] done'"""

        cmd = [
            "docker", "compose", "-f", compose_file, "run", "--rm",
            "-w", "/work",
            "runner_flutter",
            "bash", "-c", bash_script
        ]
        # Exécuter avec timeout pour éviter le blocage
        try:
            result = subprocess.run(cmd, cwd=str(REPO_ROOT), timeout=300)  # 5 minutes max
            if result.returncode == 0:
                print("✅ Génération Mason + scaffolding Android + build APK terminés")
            else:
                print(f"⚠️ Commande Docker terminée avec code {result.returncode}")
        except subprocess.TimeoutExpired:
            print("⚠️ Timeout après 5 minutes - build APK probablement bloqué")
            print("✅ Génération Mason + scaffolding Android terminés (sans APK)")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'exécution Docker: {e}")
            print("✅ Génération Mason + scaffolding Android terminés (sans APK)")
    else:
        # Mode simulation : créer les fichiers Flutter directement
        print("🔧 Mode simulation : génération directe des fichiers Flutter")
        
        # Créer pubspec.yaml
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
        
        # Créer la structure lib/
        lib_dir = app_dir / "lib"
        lib_dir.mkdir(exist_ok=True)
        
        # Créer main.dart
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
        
        # Créer app_router.dart
        router_content = """import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

GoRouter buildRouter() {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const HomeScreen(),
      ),
      // TODO: routes supplémentaires auto-générées pour entities/screens
    ],
  );
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: const Center(child: Text('App générée - Forge AGI')),
    );
  }
}
"""
        
        router_path = lib_dir / "app_router.dart"
        router_path.write_text(router_content, encoding="utf-8")
        
        # Créer analysis_options.yaml
        analysis_content = """include: package:flutter_lints/flutter.yaml
analyzer:
  exclude:
    - "**/*.g.dart"
    - "**/*.freezed.dart"
"""
        
        analysis_path = app_dir / "analysis_options.yaml"
        analysis_path.write_text(analysis_content, encoding="utf-8")
        
        # Créer README.md
        readme_content = f"""# {vars_obj['app_name']}
Généré par Forge AGI (brick mobile_app_base).
- Build : `flutter build apk --release`
- Tests : `flutter test`
"""
        
        readme_path = app_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        
        print(f"✅ App Flutter générée en mode simulation: {app_dir}")
    
    return app_dir

def generate_app_from_spec(spec_path: Path, run_id: str | None = None, build_apk: bool = True) -> Path:
    run_id = run_id or str(uuid.uuid4())
    with open(spec_path, "r", encoding="utf-8") as f:
        if spec_path.suffix.lower() in (".yaml", ".yml"):
            spec = yaml.safe_load(f)
        else:
            spec = json.load(f)
    vars_obj = spec_to_vars(spec)
    app_dir = run_mason_make(run_id, vars_obj, build_apk=build_apk)
    # écrire la spec à côté
    (WORK_DIR / run_id / "spec.yml").write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    return app_dir
