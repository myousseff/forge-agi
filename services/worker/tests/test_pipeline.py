import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, MagicMock

# Ajouter le répertoire parent au PYTHONPATH
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from worker.pipeline import validate_spec
from worker.critic import run_critic as critic_module_run_critic
from worker.judge import run_judge as judge_module_run_judge

@pytest.fixture
def valid_spec_data():
    """Données de spécification valides pour les tests"""
    return {
        "meta": {
            "schema_version": "0.1.0",
            "vertical": "mobile_app"
        },
        "app": {
            "name": "Test App",
            "bundle_id_android": "com.test.app"
        },
        "data": {
            "entities": [
                {
                    "name": "User",
                    "fields": [
                        {"name": "email", "type": "string", "required": True}
                    ]
                },
                {
                    "name": "Restaurant",
                    "fields": [
                        {"name": "title", "type": "string", "required": True}
                    ]
                }
            ]
        },
        "ui": {
            "screens": [
                {
                    "name": "Home",
                    "widgets": [
                        {"type": "List", "source": "Restaurant"}
                    ]
                }
            ]
        },
        "ci": {
            "android": {
                "build_variant": "release"
            }
        }
    }

@pytest.fixture
def invalid_spec_data():
    """Données de spécification invalides pour les tests"""
    return {
        "app": {
            "name": "Test App"
        }
        # Manque meta, data, ui, ci
    }

def test_validate_spec_valid(valid_spec_data):
    """Test de validation avec une spécification valide"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_spec_data, f)
        spec_path = f.name
    
    try:
        with patch('worker.pipeline.os.path.exists', return_value=True):
            with patch('builtins.open') as mock_open:
                # Mock pour le schéma
                mock_open.return_value.__enter__.return_value.read.return_value = '''
                {
                    "type": "object",
                    "properties": {
                        "meta": {"type": "object"},
                        "app": {"type": "object"},
                        "data": {"type": "object"},
                        "ui": {"type": "object"},
                        "ci": {"type": "object"}
                    },
                    "required": ["meta", "app", "data", "ui", "ci"]
                }
                '''
                
                result = validate_spec(spec_path)
                assert result["valid"] is True
                assert "spec_data" in result
    finally:
        os.unlink(spec_path)

def test_validate_spec_invalid(invalid_spec_data):
    """Test de validation avec une spécification invalide"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(invalid_spec_data, f)
        spec_path = f.name
    
    try:
        with patch('worker.pipeline.os.path.exists', return_value=True):
            with patch('builtins.open') as mock_open:
                # Mock pour le schéma
                mock_open.return_value.__enter__.return_value.read.return_value = '''
                {
                    "type": "object",
                    "properties": {
                        "meta": {"type": "object"},
                        "app": {"type": "object"},
                        "data": {"type": "object"},
                        "ui": {"type": "object"},
                        "ci": {"type": "object"}
                    },
                    "required": ["meta", "app", "data", "ui", "ci"]
                }
                '''
                
                result = validate_spec(spec_path)
                assert result["valid"] is False
                assert "error" in result
    finally:
        os.unlink(spec_path)

def test_critic_valid(valid_spec_data):
    """Test du module critic avec des données valides"""
    result = critic_module_run_critic(valid_spec_data)
    
    assert "issues" in result
    assert "blocking" in result
    assert "critical_count" in result
    assert "warning_count" in result
    assert result["critical_count"] == 0
    assert result["warning_count"] == 0

def test_critic_invalid(invalid_spec_data):
    """Test du module critic avec des données invalides"""
    result = critic_module_run_critic(invalid_spec_data)
    
    assert "issues" in result
    assert "blocking" in result
    assert "critical_count" in result
    assert "warning_count" in result
    assert result["critical_count"] > 0  # Doit y avoir des erreurs critiques

def test_judge_accept():
    """Test du module judge avec des résultats acceptables"""
    critic_result = {"blocking": []}
    static_checks_result = {"analyze_ok": True}
    tests_result = {"tests_ok": True}
    
    result = judge_module_run_judge(critic_result, static_checks_result, tests_result)
    
    assert result["decision"] == "accept"
    assert result["critic_ok"] is True
    assert result["static_ok"] is True
    assert result["tests_ok"] is True

def test_judge_revise():
    """Test du module judge avec des résultats inacceptables"""
    critic_result = {"blocking": ["Erreur critique"]}
    static_checks_result = {"analyze_ok": False}
    tests_result = {"tests_ok": False}
    
    result = judge_module_run_judge(critic_result, static_checks_result, tests_result)
    
    assert result["decision"] == "revise"
    assert result["critic_ok"] is False
    assert result["static_ok"] is False
    assert result["tests_ok"] is False

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
