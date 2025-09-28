from typing import Any, Dict, List
from abc import ABC, abstractmethod

class Tool(ABC):
    name: str
    schema: dict

    @abstractmethod
    def run(self, args: dict) -> Any:
        pass

class RestaurantSearchTool(Tool):
    name = "restaurant_search"
    schema = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}

    def run(self, args: dict) -> List[Dict[str, Any]]:
        query = args.get("query", "")
        # Stub: retourne des résultats factices
        return [
            {"name": "Café de Paris", "address": "1 rue de Paris", "rating": 4.5},
            {"name": "Bistro Central", "address": "2 avenue de la République", "rating": 4.2},
        ]

REGISTRY = {
    "restaurant_search": RestaurantSearchTool(),
}
