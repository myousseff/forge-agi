import json
import os
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from jsonschema import validate, ValidationError

from .schemas import SpecValidateRequest, SpecValidateResponse

app = FastAPI(title="Forge AGI API", version="1.0.0")

# Charger le schéma JSON
def load_schema() -> Dict[str, Any]:
    schema_path = Path(__file__).parent.parent.parent.parent / "specs" / "schema" / "mobile-app-0.1.0.json"
    try:
        with open(schema_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Schema file not found: {schema_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in schema file: {e}")

# Charger le schéma au démarrage
SCHEMA = load_schema()


@app.get("/v1/health")
async def health_check():
    """Endpoint de santé de l'API"""
    return {"ok": True}


@app.post("/v1/specs/validate", response_model=SpecValidateResponse)
async def validate_spec(request: SpecValidateRequest):
    """Valider une spécification d'application mobile"""
    
    # Vérifier la version du schéma
    if request.schema_version != "0.1.0":
        return SpecValidateResponse(
            valid=False,
            errors=[f"Unsupported schema version: {request.schema_version}. Expected: 0.1.0"]
        )
    
    try:
        # Valider le spec contre le schéma JSON
        validate(instance=request.spec, schema=SCHEMA)
        return SpecValidateResponse(valid=True)
        
    except ValidationError as e:
        # Extraire les erreurs de validation
        errors = []
        for error in e.context:
            errors.append(f"{error.path}: {error.message}")
        
        # Ajouter l'erreur principale si pas d'erreurs contextuelles
        if not errors:
            errors.append(f"{e.path}: {e.message}")
            
        return SpecValidateResponse(valid=False, errors=errors)
        
    except Exception as e:
        return SpecValidateResponse(
            valid=False,
            errors=[f"Validation error: {str(e)}"]
        )
