from typing import Dict, Any, List

def run_critic(spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """Contrôles logiques simples sur la spécification"""
    issues = []
    blocking = []
    
    # Vérifier la présence de meta/app/data/ui/ci
    if 'meta' not in spec_data:
        issues.append("Section 'meta' manquante")
        blocking.append("Section 'meta' manquante")
    
    if 'app' not in spec_data:
        issues.append("Section 'app' manquante")
        blocking.append("Section 'app' manquante")
    
    if 'data' not in spec_data:
        issues.append("Section 'data' manquante")
        blocking.append("Section 'data' manquante")
    
    if 'ui' not in spec_data:
        issues.append("Section 'ui' manquante")
        blocking.append("Section 'ui' manquante")
    
    if 'ci' not in spec_data:
        issues.append("Section 'ci' manquante")
        blocking.append("Section 'ci' manquante")
    
    # Vérifier les références d'entités dans les écrans
    if 'data' in spec_data and 'entities' in spec_data['data']:
        entity_names = {entity['name'] for entity in spec_data['data']['entities']}
        
        if 'ui' in spec_data and 'screens' in spec_data['ui']:
            for screen in spec_data['ui']['screens']:
                if 'widgets' in screen:
                    for widget in screen['widgets']:
                        # Vérifier les références 'source'
                        if 'source' in widget:
                            if widget['source'] not in entity_names:
                                issues.append(f"Écran '{screen.get('name', 'unknown')}': référence d'entité '{widget['source']}' inexistante")
                                blocking.append(f"Référence d'entité '{widget['source']}' inexistante")
                        
                        # Vérifier les références 'entity'
                        if 'entity' in widget:
                            if widget['entity'] not in entity_names:
                                issues.append(f"Écran '{screen.get('name', 'unknown')}': référence d'entité '{widget['entity']}' inexistante")
                                blocking.append(f"Référence d'entité '{widget['entity']}' inexistante")
    
    return {
        "issues": issues,
        "blocking": blocking,
        "critical_count": len(blocking),
        "warning_count": len(issues) - len(blocking)
    }
