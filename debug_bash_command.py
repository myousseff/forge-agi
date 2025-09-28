#!/usr/bin/env python3
"""
Débogage de la commande bash qui pose problème
"""

def debug_bash_command():
    """Débogue la construction de la commande bash"""
    
    # Paramètres de test
    run_id = "test-123"
    build_apk = False
    brick_path = "/workspace/bricks/mobile_app_base"
    
    # Construire la commande bash comme dans codegen.py
    bash_commands = (
        "set -e;"
        "echo '[mason] init/add/make';"
        "mason --version;"
        "mason init || true;"
        "mason remove mobile_app_base || true;"
        f"mason add mobile_app_base --path {brick_path};"
        f"mason make mobile_app_base -c /work/{run_id}/vars.json -o /work/{run_id}/app;"
        # Scaffolding Android après Mason
        "echo '[flutter] scaffolding Android';"
        f"cd /work/{run_id}/app;"
        "flutter create -t app --platforms android --org com.forge --project-name resa_cafe_atlas .flutter_scaffold_tmp;"
        "cp -r .flutter_scaffold_tmp/android .;"
        "cp -r .flutter_scaffold_tmp/.metadata . 2>/dev/null || true;"
        "rm -rf .flutter_scaffold_tmp;"
        "echo '[flutter] Android scaffold injecté';"
        # rafraîchir les dépendances après injection d'android/
        "flutter pub get;"
        # Build APK conditionnel selon le paramètre build_apk
        f"if {str(build_apk).lower()}; then"
        "  echo '[flutter] build APK...';"
        "  flutter build apk --debug;"
        "  # copie l'APK dans artifacts/"
        "  mkdir -p /work/{run_id}/artifacts;"
        "  if [ -f build/app/outputs/flutter-apk/app-debug.apk ]; then"
        "    cp build/app/outputs/flutter-apk/app-debug.apk /work/{run_id}/artifacts/app-debug.apk;"
        "    echo '✅ APK copié dans artifacts/app-debug.apk';"
        "  else"
        "    echo '⚠️ APK non trouvé (regarde les logs gradle)';"
        "  fi;"
        "else"
        "  echo '[flutter] build APK ignoré (mode génération uniquement)';"
        "fi;"
        "echo '[mason] done';"
    )
    
    print("🔍 Commande bash construite:")
    print("=" * 80)
    print(bash_commands)
    print("=" * 80)
    
    # Analyser ligne par ligne
    lines = bash_commands.split(';')
    print(f"\n📋 Analyse ligne par ligne ({len(lines)} lignes):")
    for i, line in enumerate(lines, 1):
        print(f"{i:2d}: {line.strip()}")
    
    # Vérifier les problèmes potentiels
    print(f"\n🔍 Problèmes potentiels détectés:")
    
    # Vérifier les guillemets non fermés
    quote_count = bash_commands.count('"')
    if quote_count % 2 != 0:
        print(f"❌ Guillemets non équilibrés: {quote_count} guillemets")
    
    # Vérifier les accolades non fermées
    brace_count = bash_commands.count('{')
    close_brace_count = bash_commands.count('}')
    if brace_count != close_brace_count:
        print(f"❌ Accolades non équilibrées: {{ {brace_count}, }} {close_brace_count}")
    
    # Vérifier les parenthèses non fermées
    paren_count = bash_commands.count('(')
    close_paren_count = bash_commands.count(')')
    if paren_count != close_paren_count:
        print(f"❌ Parenthèses non équilibrées: ( {paren_count}, ) {close_paren_count}")
    
    # Vérifier les f-strings
    if "f'" in bash_commands or 'f"' in bash_commands:
        print("❌ F-strings détectées dans la commande bash")
    
    print(f"\n✅ Analyse terminée")

if __name__ == "__main__":
    debug_bash_command()
