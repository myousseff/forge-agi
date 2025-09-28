import requests
from services.contracts.models import Message

def agent_step(conversation_id: str) -> list[dict]:
    api_url = "http://api:8080/v1/conversations/" + conversation_id
    try:
        resp = requests.get(api_url, timeout=2)
        if resp.status_code != 200:
            return []
        messages = resp.json()
    except Exception:
        return []
    if not messages:
        return []
    last_msg = messages[-1]
    content = last_msg.get("content", "")
    if any(word in content.lower() for word in ["café", "restaurant"]):
        # Tool call
        tool_call = Message(role="tool", content="Recherche de restaurants", tool_name="restaurant_search")
        # Appel du tool (stub: GET tools, pas d'invoke direct)
        tools = requests.get("http://api:8080/v1/tools").json()
        if "restaurant_search" in tools:
            tool_result = requests.post("http://api:8080/v1/tools/restaurant_search/invoke", json={"query": content}).json()
            assistant_msg = Message(role="assistant", content=str(tool_result["result"]))
            return [tool_call.model_dump(), assistant_msg.model_dump()]
    # Sinon, réponse simple
    assistant_msg = Message(role="assistant", content="Je peux chercher des cafés si tu veux.")
    return [assistant_msg.model_dump()]
