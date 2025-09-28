import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test de l'endpoint /v1/health"""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_validate_spec_valid():
    """Test de validation avec un spec valide (basé sur resa.yaml)"""
    valid_spec = {
        "app": {
            "name": "Resa App",
            "package": "com.example.resa",
            "version": "1.0.0"
        },
        "screens": [
            {
                "name": "login",
                "type": "login",
                "widgets": [
                    {
                        "type": "TextField",
                        "label": "Email",
                        "field": "email"
                    }
                ]
            },
            {
                "name": "reservations",
                "type": "list",
                "widgets": []
            }
        ],
        "models": [
            {
                "name": "User",
                "fields": [
                    {
                        "name": "id",
                        "type": "int",
                        "required": True
                    },
                    {
                        "name": "email",
                        "type": "string",
                        "required": True
                    }
                ]
            }
        ]
    }
    
    request_data = {
        "schema_version": "0.1.0",
        "spec": valid_spec
    }
    
    response = client.post("/v1/specs/validate", json=request_data)
    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is True
    assert "errors" not in result or result["errors"] is None


def test_validate_spec_invalid_missing_app():
    """Test de validation avec un spec invalide (app manquant)"""
    invalid_spec = {
        "screens": [],
        "models": []
    }
    
    request_data = {
        "schema_version": "0.1.0",
        "spec": invalid_spec
    }
    
    response = client.post("/v1/specs/validate", json=request_data)
    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is False
    assert "errors" in result
    assert len(result["errors"]) > 0
    assert any("app" in error.lower() for error in result["errors"])


def test_validate_spec_invalid_schema_version():
    """Test de validation avec une version de schéma invalide"""
    valid_spec = {
        "app": {
            "name": "Test App",
            "package": "com.test.app",
            "version": "1.0.0"
        },
        "screens": [],
        "models": []
    }
    
    request_data = {
        "schema_version": "0.2.0",  # Version non supportée
        "spec": valid_spec
    }
    
    response = client.post("/v1/specs/validate", json=request_data)
    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is False
    assert "errors" in result
    assert len(result["errors"]) == 1
    assert "0.2.0" in result["errors"][0]
    assert "0.1.0" in result["errors"][0]


def test_validate_spec_invalid_app_missing_fields():
    """Test de validation avec des champs manquants dans app"""
    invalid_spec = {
        "app": {
            "name": "Test App"
            # package et version manquants
        },
        "screens": [],
        "models": []
    }
    
    request_data = {
        "schema_version": "0.1.0",
        "spec": invalid_spec
    }
    
    response = client.post("/v1/specs/validate", json=request_data)
    assert response.status_code == 200
    result = response.json()
    assert result["valid"] is False
    assert "errors" in result
    assert len(result["errors"]) > 0
    assert any("package" in error.lower() or "version" in error.lower() for error in result["errors"])
