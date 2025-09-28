import json
from pathlib import Path
from typing import Dict, Any, List


def infer_entities_from_spec(spec: dict) -> List[Dict[str, Any]]:
    """
    Infère les entités et leurs champs à partir de la spécification.
    
    Args:
        spec: Dictionnaire de la spécification
        
    Returns:
        Liste des entités avec leurs champs et métadonnées
    """
    entities = []
    
    # Extraire les entités depuis spec.data.entities
    if 'data' in spec and 'entities' in spec['data']:
        for entity in spec['data']['entities']:
            entity_info = {
                'name': entity.get('name', 'Unknown'),
                'table_name': entity.get('name', 'Unknown').lower().replace(' ', '_'),
                'fields': []
            }
            
            # Traiter les champs de l'entité
            if 'fields' in entity:
                for field in entity['fields']:
                    field_info = {
                        'name': field.get('name', 'Unknown'),
                        'type': field.get('type', 'string'),
                        'required': field.get('required', True),
                        'primary_key': field.get('primary_key', False),
                        'foreign': field.get('foreign', None)  # "table.field -> ref_table.ref_field"
                    }
                    entity_info['fields'].append(field_info)
            
            entities.append(entity_info)
    
    return entities


def sqlite_type(py_type: str) -> str:
    """
    Mappe les types Python vers les types SQLite.
    
    Args:
        py_type: Type Python (string, int, float, bool, date)
        
    Returns:
        Type SQLite correspondant
    """
    type_mapping = {
        'string': 'TEXT',
        'str': 'TEXT',
        'text': 'TEXT',
        'int': 'INTEGER',
        'integer': 'INTEGER',
        'number': 'INTEGER',
        'float': 'REAL',
        'double': 'REAL',
        'decimal': 'REAL',
        'bool': 'INTEGER',
        'boolean': 'INTEGER',
        'date': 'TEXT',
        'datetime': 'TEXT',
        'timestamp': 'TEXT'
    }
    
    return type_mapping.get(py_type.lower(), 'TEXT')


def render_sql(entities: List[Dict[str, Any]]) -> str:
    """
    Génère le SQL CREATE TABLE pour toutes les entités.
    
    Args:
        entities: Liste des entités avec leurs champs
        
    Returns:
        Chaîne SQL avec les CREATE TABLE
    """
    if not entities:
        return "-- Aucune entité détectée dans la spécification\n"
    
    sql_lines = []
    sql_lines.append("-- Schéma SQLite généré automatiquement par Forge AGI")
    sql_lines.append("-- Basé sur la spécification de l'application")
    sql_lines.append("")
    
    for entity in entities:
        table_name = entity['table_name']
        fields = entity['fields']
        
        if not fields:
            continue
            
        sql_lines.append(f"CREATE TABLE {table_name} (")
        
        field_definitions = []
        for field in fields:
            field_name = field['name'].lower().replace(' ', '_')
            field_type = sqlite_type(field['type'])
            field_def = f"    {field_name} {field_type}"
            
            # Ajouter les contraintes
            if field.get('primary_key', False):
                field_def += " PRIMARY KEY"
            elif not field.get('required', True):
                field_def += " NULL"
            else:
                field_def += " NOT NULL"
                
            field_definitions.append(field_def)
        
        sql_lines.append(",\n".join(field_definitions))
        sql_lines.append(");")
        sql_lines.append("")
        
        # Ajouter les clés étrangères si spécifiées
        for field in fields:
            if field.get('foreign'):
                foreign_ref = field['foreign']
                if '->' in foreign_ref:
                    parts = foreign_ref.split('->')
                    if len(parts) == 2:
                        current_ref = parts[0].strip()
                        target_ref = parts[1].strip()
                        
                        if '.' in current_ref and '.' in target_ref:
                            current_table, current_field = current_ref.split('.')
                            target_table, target_field = target_ref.split('.')
                            
                            fk_sql = f"ALTER TABLE {table_name} ADD COLUMN {current_field}_id INTEGER;"
                            sql_lines.append(fk_sql)
                            
                            # Note: SQLite ne supporte pas ADD CONSTRAINT, on ajoute juste la colonne
                            sql_lines.append(f"-- Référence: {current_ref} -> {target_ref}")
                            sql_lines.append("")
    
    return "\n".join(sql_lines)


def write_artifacts(run_path: Path, sql: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Écrit les artefacts de base de données dans le dossier artifacts.
    
    Args:
        run_path: Chemin vers le dossier de run
        sql: Contenu SQL généré
        entities: Liste des entités
        
    Returns:
        Dictionnaire avec le résumé des artefacts créés
    """
    artifacts_dir = run_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Compter les tables et colonnes
    table_count = len(entities)
    column_count = sum(len(entity.get('fields', [])) for entity in entities)
    
    # 1. db_schema.sql
    schema_path = artifacts_dir / "db_schema.sql"
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(sql)
    
    # 2. db_migration_0001.sql (même contenu pour la v1)
    migration_path = artifacts_dir / "db_migration_0001.sql"
    with open(migration_path, 'w', encoding='utf-8') as f:
        f.write(f"-- Migration 0001: Schéma initial\n")
        f.write(f"-- Généré le: {run_path.name}\n\n")
        f.write(sql)
    
    # 3. db_report.json
    report = {
        "tables": table_count,
        "columns": column_count,
        "entities": [
            {
                "name": entity['name'],
                "table_name": entity['table_name'],
                "field_count": len(entity.get('fields', []))
            }
            for entity in entities
        ]
    }
    
    report_path = artifacts_dir / "db_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return {
        "success": True,
        "files_created": [
            "db_schema.sql",
            "db_migration_0001.sql", 
            "db_report.json"
        ],
        "table_count": table_count,
        "column_count": column_count
    }
