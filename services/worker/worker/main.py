from celery import Celery
import os
import uvicorn
from services.worker.http import app

# Configuration Celery
app = Celery('forge_worker')

# Configuration depuis les variables d'environnement
app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@app.task(name="run_pipeline")
def run_pipeline_task(run_id: str, spec_path: str, dry_run: bool = True):
    """Tâche Celery pour exécuter le pipeline de génération"""
    from .pipeline import run_pipeline
    return run_pipeline(run_id, spec_path, dry_run)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
