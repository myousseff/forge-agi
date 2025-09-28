#!/usr/bin/env python3
"""
Script de développement pour lancer le pipeline en local
Usage: python scripts/dev_run_pipeline.py specs/examples/resa.yaml
"""

import sys
import os
import uuid
from pathlib import Path

# Ajouter le répertoire services/worker au PYTHONPATH
worker_path = Path(__file__).parent.parent / "services" / "worker"
sys.path.insert(0, str(worker_path))

from worker.pipeline import run_pipeline
from rich.console import Console

console = Console()

def main():
    if len(sys.argv) != 2:
        console.print("[bold red]Usage: python scripts/dev_run_pipeline.py <spec_file>[/bold red]")
        console.print("Example: python scripts/dev_run_pipeline.py specs/examples/resa.yaml")
        sys.exit(1)
    
    spec_file = sys.argv[1]
    
    if not os.path.exists(spec_file):
        console.print(f"[bold red]Erreur: Le fichier {spec_file} n'existe pas[/bold red]")
        sys.exit(1)
    
    # Générer un run_id unique
    run_id = str(uuid.uuid4())
    
    console.print(f"[bold blue]🚀 Lancement du pipeline en mode développement[/bold blue]")
    console.print(f"Spec: {spec_file}")
    console.print(f"Run ID: {run_id}")
    console.print(f"Mode: normal (génération Flutter complète)")
    
    # Exécuter le pipeline
    result = run_pipeline(run_id, spec_file, dry_run=False)
    
    # Afficher le résultat
    if result.get("success"):
        console.print(f"\n[bold green]✅ Pipeline réussi![/bold green]")
        work_dir = os.getenv('WORK_DIR', './work')
        artifacts_path = os.path.join(work_dir, run_id, 'artifacts')
        console.print(f"Run ID: {run_id}")
        console.print(f"Artifacts: {artifacts_path}")
        
        # Lister les fichiers créés
        if os.path.exists(artifacts_path):
            console.print("\n[bold]Fichiers créés:[/bold]")
            for file in os.listdir(artifacts_path):
                file_path = os.path.join(artifacts_path, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    console.print(f"  - {file} ({size} bytes)")
    else:
        console.print(f"\n[bold red]❌ Pipeline échoué![/bold red]")
        console.print(f"Erreur: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == '__main__':
    main()
