class MemoryStore:
    """Stub de mémoire vectorielle."""
    def upsert(self, items: list[dict]) -> int:
        # Stub: ne fait rien
        return len(items)

    def query(self, query: str, top_k: int = 5) -> list[dict]:
        # Stub: retourne une liste vide
        return []
