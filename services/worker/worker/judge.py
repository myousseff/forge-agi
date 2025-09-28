from typing import Dict, Any

def run_judge(critic_result: Dict[str, Any], static_checks_result: Dict[str, Any], tests_result: Dict[str, Any]) -> Dict[str, Any]:
    """Décide si le pipeline est accepté ou doit être révisé"""
    # Critères d'acceptation
    critic_ok = len(critic_result.get("blocking", [])) == 0
    static_ok = static_checks_result.get("analyze_ok", False)
    tests_ok = tests_result.get("tests_ok", False)
    
    decision = "accept" if (critic_ok and static_ok and tests_ok) else "revise"
    
    return {
        "decision": decision,
        "critic_ok": critic_ok,
        "static_ok": static_ok,
        "tests_ok": tests_ok,
        "reason": "Tous les critères sont satisfaits" if decision == "accept" else "Critères non satisfaits"
    }
