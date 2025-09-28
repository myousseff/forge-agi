import json
import yaml
from pathlib import Path
from typing import Dict, Any, List


def infer_endpoints_from_spec(spec: dict) -> List[Dict[str, Any]]:
    """
    Infère les endpoints API à partir de la spécification.
    
    Args:
        spec: Dictionnaire de la spécification
        
    Returns:
        Liste des endpoints avec leurs méthodes et chemins
    """
    endpoints = []
    
    # Endpoint de santé par défaut
    endpoints.append({
        "method": "GET",
        "path": "/health",
        "summary": "Health check endpoint",
        "description": "Vérifie que l'API est opérationnelle",
        "tags": ["system"]
    })
    
    # Analyser la spécification pour détecter les entités et générer des endpoints CRUD
    if 'data' in spec and 'entities' in spec['data']:
        for entity in spec['data']['entities']:
            entity_name = entity.get('name', 'Unknown').lower()
            entity_plural = f"{entity_name}s"  # Simple pluralisation
            
            # Endpoints CRUD basiques
            endpoints.extend([
                {
                    "method": "GET",
                    "path": f"/{entity_plural}",
                    "summary": f"Liste tous les {entity_name}s",
                    "description": f"Récupère la liste de tous les {entity_name}s",
                    "tags": [entity_name],
                    "entity": entity_name
                },
                {
                    "method": "POST",
                    "path": f"/{entity_plural}",
                    "summary": f"Crée un nouveau {entity_name}",
                    "description": f"Crée un nouveau {entity_name}",
                    "tags": [entity_name],
                    "entity": entity_name
                },
                {
                    "method": "GET",
                    "path": f"/{entity_plural}/{{id}}",
                    "summary": f"Récupère un {entity_name} par ID",
                    "description": f"Récupère les détails d'un {entity_name} spécifique",
                    "tags": [entity_name],
                    "entity": entity_name
                },
                {
                    "method": "PUT",
                    "path": f"/{entity_plural}/{{id}}",
                    "summary": f"Met à jour un {entity_name}",
                    "description": f"Met à jour un {entity_name} existant",
                    "tags": [entity_name],
                    "entity": entity_name
                },
                {
                    "method": "DELETE",
                    "path": f"/{entity_plural}/{{id}}",
                    "summary": f"Supprime un {entity_name}",
                    "description": f"Supprime un {entity_name} existant",
                    "tags": [entity_name],
                    "entity": entity_name
                }
            ])
    
    return endpoints


def render_openapi(endpoints: List[Dict[str, Any]], entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Génère la spécification OpenAPI 3.1.
    
    Args:
        endpoints: Liste des endpoints détectés
        entities: Liste des entités (optionnel, pour les schémas)
        
    Returns:
        Dictionnaire OpenAPI 3.1
    """
    # Schémas de base
    schemas = {
        "Error": {
            "type": "object",
            "properties": {
                "error": {"type": "string"},
                "message": {"type": "string"},
                "status": {"type": "integer"}
            },
            "required": ["error", "message", "status"]
        },
        "HealthResponse": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "example": "ok"},
                "timestamp": {"type": "string", "format": "date-time"}
            },
            "required": ["status", "timestamp"]
        }
    }
    
    # Ajouter les schémas des entités
    for entity in entities:
        entity_name = entity.get('name', 'Unknown')
        entity_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for field in entity.get('fields', []):
            field_name = field.get('name', 'Unknown')
            field_type = field.get('type', 'string')
            
            # Mapping des types vers OpenAPI
            if field_type in ['int', 'integer', 'number']:
                openapi_type = "integer"
            elif field_type in ['float', 'double', 'decimal']:
                openapi_type = "number"
            elif field_type in ['bool', 'boolean']:
                openapi_type = "boolean"
            elif field_type in ['date', 'datetime', 'timestamp']:
                openapi_type = "string"
                field_format = "date-time"
            else:
                openapi_type = "string"
                field_format = None
            
            field_prop = {"type": openapi_type}
            if field_format:
                field_prop["format"] = field_format
            
            entity_schema["properties"][field_name] = field_prop
            
            if field.get('required', True):
                entity_schema["required"].append(field_name)
        
        # Ajouter le schéma de l'entité
        schemas[entity_name] = entity_schema
        
        # Schéma pour la liste
        schemas[f"{entity_name}List"] = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {"$ref": f"#/components/schemas/{entity_name}"}
                },
                "total": {"type": "integer"},
                "page": {"type": "integer"},
                "limit": {"type": "integer"}
            },
            "required": ["data", "total"]
        }
    
    # Construire les paths
    paths = {}
    for endpoint in endpoints:
        path = endpoint["path"]
        method = endpoint["method"].lower()
        
        if path not in paths:
            paths[path] = {}
        
        # Paramètres de chemin
        path_params = []
        if "{id}" in path:
            path_params.append({
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "Identifiant unique"
            })
        
        # Réponses par défaut
        responses = {
            "200": {
                "description": "Succès",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/HealthResponse"}
                    }
                }
            },
            "400": {
                "description": "Requête invalide",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"}
                    }
                }
            },
            "404": {
                "description": "Ressource non trouvée",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"}
                    }
                }
            },
            "500": {
                "description": "Erreur serveur",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"}
                    }
                }
            }
        }
        
        # Créer d'abord l'entrée dans paths
        paths[path][method] = {
            "summary": endpoint["summary"],
            "description": endpoint["description"],
            "tags": endpoint["tags"],
            "parameters": path_params,
            "responses": responses
        }
        
        # Personnaliser les réponses selon l'endpoint
        if endpoint.get("entity"):
            entity_name = endpoint["entity"]
            if method == "get" and "{id}" not in path:
                # Liste
                paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"] = {
                    "$ref": f"#/components/schemas/{entity_name.capitalize()}List"
                }
            elif method == "get" and "{id}" in path:
                # Détail
                paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"] = {
                    "$ref": f"#/components/schemas/{entity_name.capitalize()}"
                }
            elif method in ["post", "put"]:
                # Création/Modification
                paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"] = {
                    "$ref": f"#/components/schemas/{entity_name.capitalize()}"
                }
                # Ajouter le body de la requête
                if method == "post":
                    paths[path][method]["requestBody"] = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{entity_name.capitalize()}"}
                            }
                        }
                    }
    
    # Construire la spécification OpenAPI complète
    openapi_spec = {
        "openapi": "3.1.0",
        "info": {
            "title": "Forge AGI API",
            "description": "API générée automatiquement par Forge AGI",
            "version": "1.0.0",
            "contact": {
                "name": "Forge AGI",
                "url": "https://github.com/forge-agi"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "Serveur de développement"
            }
        ],
        "paths": paths,
        "components": {
            "schemas": schemas
        },
        "tags": [
            {"name": "system", "description": "Endpoints système"},
        ]
    }
    
    # Ajouter les tags des entités
    for entity in entities:
        entity_name = entity.get('name', 'Unknown').lower()
        openapi_spec["tags"].append({
            "name": entity_name,
            "description": f"Opérations sur les {entity_name}s"
        })
    
    return openapi_spec


def write_artifacts(run_path: Path, openapi: dict) -> Dict[str, Any]:
    """
    Écrit les artefacts OpenAPI dans le dossier artifacts.
    
    Args:
        run_path: Chemin vers le dossier de run
        openapi: Spécification OpenAPI
        
    Returns:
        Dictionnaire avec le résumé des artefacts créés
    """
    artifacts_dir = run_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. openapi.yaml
    openapi_path = artifacts_dir / "openapi.yaml"
    with open(openapi_path, 'w', encoding='utf-8') as f:
        yaml.dump(openapi, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    return {
        "success": True,
        "files_created": ["openapi.yaml"],
        "openapi_path": str(openapi_path)
    }


def generate_dart_client_stub(openapi: dict, out_dir: Path) -> Dict[str, Any]:
    """
    Génère le client Dart stub à partir de la spécification OpenAPI.
    
    Args:
        openapi: Spécification OpenAPI
        out_dir: Dossier de sortie (artifacts/dart_client)
        
    Returns:
        Dictionnaire avec le résumé des fichiers créés
    """
    dart_client_dir = out_dir / "dart_client"
    dart_client_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. pubspec.yaml
    pubspec_content = """name: forge_client
description: Client Dart généré automatiquement par Forge AGI
version: 1.0.0
publish_to: none

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  http: ^1.1.0
  json_annotation: ^4.9.0

dev_dependencies:
  build_runner: ^2.4.9
  json_serializable: ^6.8.0
  test: ^1.24.0
"""
    
    pubspec_path = dart_client_dir / "pubspec.yaml"
    with open(pubspec_path, 'w', encoding='utf-8') as f:
        f.write(pubspec_content)
    
    # 2. lib/forge_client.dart
    lib_dir = dart_client_dir / "lib"
    lib_dir.mkdir(exist_ok=True)
    
    # Générer les modèles Dart
    models = []
    for schema_name, schema in openapi.get("components", {}).get("schemas", {}).items():
        if schema_name in ["Error", "HealthResponse"]:
            continue  # Modèles système
            
        if "properties" in schema:
            model_class = f"""class {schema_name} {{
  {schema_name}({{
"""
            
            # Propriétés
            for prop_name, prop_schema in schema.get("properties", {}).items():
                dart_type = "String"
                if prop_schema.get("type") == "integer":
                    dart_type = "int"
                elif prop_schema.get("type") == "number":
                    dart_type = "double"
                elif prop_schema.get("type") == "boolean":
                    dart_type = "bool"
                
                model_class += f"    required this.{prop_name},\n"
            
            model_class += "  });\n\n"
            
            # Déclaration des propriétés
            for prop_name, prop_schema in schema.get("properties", {}).items():
                dart_type = "String"
                if prop_schema.get("type") == "integer":
                    dart_type = "int"
                elif prop_schema.get("type") == "number":
                    dart_type = "double"
                elif prop_schema.get("type") == "boolean":
                    dart_type = "bool"
                
                model_class += f"  final {dart_type} {prop_name};\n"
            
            # Factory fromJson
            model_class += f"""
  factory {schema_name}.fromJson(Map<String, dynamic> json) {{
    return {schema_name}(
"""
            
            for prop_name, prop_schema in schema.get("properties", {}).items():
                dart_type = "String"
                if prop_schema.get("type") == "integer":
                    dart_type = "int"
                elif prop_schema.get("type") == "number":
                    dart_type = "double"
                elif prop_schema.get("type") == "boolean":
                    dart_type = "bool"
                
                if dart_type == "int":
                    model_class += f"      {prop_name}: json['{prop_name}'] as int,\n"
                elif dart_type == "double":
                    model_class += f"      {prop_name}: (json['{prop_name}'] as num).toDouble(),\n"
                elif dart_type == "bool":
                    model_class += f"      {prop_name}: json['{prop_name}'] as bool,\n"
                else:
                    model_class += f"      {prop_name}: json['{prop_name}'] as String,\n"
            
            model_class += "    );\n  }\n\n"
            
            # toJson
            model_class += """  Map<String, dynamic> toJson() {
    return {
"""
            
            for prop_name in schema.get("properties", {}).keys():
                model_class += f"      '{prop_name}': {prop_name},\n"
            
            model_class += """    };
  }
}"""
            
            models.append(model_class)
    
    # Générer le client HTTP
    client_content = """import 'dart:convert';
import 'package:http/http.dart' as http;

// Modèles de données
"""
    
    # Ajouter les modèles
    for model in models:
        client_content += model + "\n\n"
    
    # Client HTTP
    client_content += """class ForgeClient {
  final String baseUrl;
  final http.Client _httpClient;

  ForgeClient({
    this.baseUrl = 'http://localhost:8000',
    http.Client? httpClient,
  }) : _httpClient = httpClient ?? http.Client();

  // Endpoints système
  Future<HealthResponse> health() async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/health'),
    );

    if (response.statusCode == 200) {
      return HealthResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Erreur de santé: ${response.statusCode}');
    }
  }

"""
    
    # Ajouter les endpoints des entités
    entities = []
    for schema_name in openapi.get("components", {}).get("schemas", {}).keys():
        if schema_name not in ["Error", "HealthResponse"] and not schema_name.endswith("List"):
            entities.append(schema_name)
    
    for entity in entities:
        entity_lower = entity.lower()
        entity_plural = f"{entity_lower}s"
        
        client_content += f"""  // Endpoints {entity}
  Future<List<{entity}>> get{entity_plural}() async {{
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/{entity_plural}'),
    );

    if (response.statusCode == 200) {{
      final data = jsonDecode(response.body);
      return (data['data'] as List)
          .map((json) => {entity}.fromJson(json))
          .toList();
    }} else {{
      throw Exception('Erreur récupération {entity_plural}: ${{response.statusCode}}');
    }}
  }}

  Future<{entity}> get{entity}(String id) async {{
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/{entity_plural}/$id'),
    );

    if (response.statusCode == 200) {{
      return {entity}.fromJson(jsonDecode(response.body));
    }} else {{
      throw Exception('Erreur récupération {entity}: ${{response.statusCode}}');
    }}
  }}

  Future<{entity}> create{entity}({entity} {entity_lower}) async {{
    final response = await _httpClient.post(
      Uri.parse('$baseUrl/{entity_plural}'),
      headers: {{'Content-Type': 'application/json'}},
      body: jsonEncode({entity_lower}.toJson()),
    );

    if (response.statusCode == 200) {{
      return {entity}.fromJson(jsonDecode(response.body));
    }} else {{
      throw Exception('Erreur création {entity}: ${{response.statusCode}}');
    }}
  }}

  Future<{entity}> update{entity}(String id, {entity} {entity_lower}) async {{
    final response = await _httpClient.put(
      Uri.parse('$baseUrl/{entity_plural}/$id'),
      headers: {{'Content-Type': 'application/json'}},
      body: jsonEncode({entity_lower}.toJson()),
    );

    if (response.statusCode == 200) {{
      return {entity}.fromJson(jsonDecode(response.body));
    }} else {{
      throw Exception('Erreur mise à jour {entity}: ${{response.statusCode}}');
    }}
  }}

  Future<void> delete{entity}(String id) async {{
    final response = await _httpClient.delete(
      Uri.parse('$baseUrl/{entity_plural}/$id'),
    );

    if (response.statusCode != 200) {{
      throw Exception('Erreur suppression {entity}: ${{response.statusCode}}');
    }}
  }}

"""
    
    client_content += """  void dispose() {
    _httpClient.close();
  }
}"""
    
    client_path = lib_dir / "forge_client.dart"
    with open(client_path, 'w', encoding='utf-8') as f:
        f.write(client_content)
    
    # 3. README.md
    readme_content = f"""# Forge Client

Client Dart généré automatiquement par Forge AGI pour consommer l'API.

## Installation

```bash
cd dart_client
dart pub get
```

## Utilisation

```dart
import 'package:forge_client/forge_client.dart';

void main() async {{
  final client = ForgeClient(baseUrl: 'http://localhost:8000');
  
  try {{
    // Vérifier la santé de l'API
    final health = await client.health();
    print('API Status: ${{health.status}}');
    
    // Utiliser les endpoints des entités
    // ... (voir les méthodes disponibles dans forge_client.dart)
    
  }} catch (e) {{
    print('Erreur: $e');
  }} finally {{
    client.dispose();
  }}
}}
```

## Endpoints disponibles

- `GET /health` - Vérification de santé
"""
    
    # Ajouter les endpoints des entités
    for entity in entities:
        entity_lower = entity.lower()
        entity_plural = f"{entity_lower}s"
        readme_content += f"""
- `GET /{entity_plural}` - Liste des {entity_lower}s
- `POST /{entity_plural}` - Créer un {entity_lower}
- `GET /{entity_plural}/{{id}}` - Récupérer un {entity_lower}
- `PUT /{entity_plural}/{{id}}` - Mettre à jour un {entity_lower}
- `DELETE /{entity_plural}/{{id}}` - Supprimer un {entity_lower}
"""
    
    readme_content += """
## Modèles de données

Les modèles sont générés automatiquement avec support JSON.
Utilisez `fromJson()` pour désérialiser et `toJson()` pour sérialiser.

## Gestion des erreurs

Le client lève des exceptions en cas d'erreur HTTP.
Gérez-les avec try/catch dans votre code.
"""
    
    readme_path = dart_client_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    return {
        "success": True,
        "files_created": [
            "pubspec.yaml",
            "lib/forge_client.dart",
            "README.md"
        ],
        "models_generated": len(models),
        "entities_supported": entities
    }
