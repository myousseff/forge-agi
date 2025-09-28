from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from services.worker.agent_loop import agent_step

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/agent/step")
def agent_step_route(req: Request):
    data = req.json() if hasattr(req, 'json') else {}
    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return JSONResponse(status_code=400, content={"error": "conversation_id required"})
    messages = agent_step(conversation_id)
    return {"messages": messages}
