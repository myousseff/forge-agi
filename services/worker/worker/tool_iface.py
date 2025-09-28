from typing import Any, Dict
from abc import ABC, abstractmethod

class Tool(ABC):
    name: str
    schema: dict

    @abstractmethod
    def run(self, args: dict) -> Any:
        raise NotImplementedError
