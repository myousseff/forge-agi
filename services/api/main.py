from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import yaml
import json
import os
from services.api.agents import router as agents_router

app = FastAPI()

@app.get("/v1/health")
def health():
    return {"status": "ok"}

app.include_router(agents_router)

class SpecValidationRequest(BaseModel):
    spec_content: str

class SpecValidationResponse(BaseModel):
    valid: bool
    errors: list = []

@app.get("/")
async def root():
    return {"message": "Forge AGI API - Service de gÃ©nÃ©ration d'applications mobiles"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "forge-agi-api"}

@app.post("/validate-spec")
async def validate_spec(request: SpecValidationRequest):
    """Valide une spÃ©cification YAML"""
    try:
        # Charger le schÃ©ma JSON
        schema_path = "../../specs/schema/mobile-app-0.1.0.json"
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Parser le YAML
        spec_data = yaml.safe_load(request.spec_content)
        
        # Validation basique (Ã  amÃ©liorer avec jsonschema)
        required_fields = ["app", "screens", "models"]
        errors = []
        
        for field in required_fields:
            if field not in spec_data:
                errors.append(f"Champ requis manquant: {field}")
        
        return SpecValidationResponse(
            valid=len(errors) == 0,
            errors=errors
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-app")
async def generate_app(request: SpecValidationRequest):
    """DÃ©clenche la gÃ©nÃ©ration d'une application"""
    try:
        # Validation de la spec
        validation = await validate_spec(request)
        if not validation.valid:
            raise HTTPException(status_code=400, detail="SpÃ©cification invalide")
        
        # TODO: Envoyer la tÃ¢che au worker Celery
        # task = generate_app_task.delay(request.spec_content)
        
        return {
            "message": "GÃ©nÃ©ration d'application lancÃ©e",
            "task_id": "task_123"  # Ã€ remplacer par l'ID rÃ©el
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
