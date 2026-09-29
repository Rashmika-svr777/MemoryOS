import logging
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from . import config
from .agents import AGENTS, AgentRuntime
from .auth import create_token, verify_token
from .demo import run_learning_demo
from .memory_service import MemoryService
from .memory_store import KINDS

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="MemoryOS API", version="0.1.0",
              description="Enterprise AI OS: five agents sharing one persistent Hindsight-backed memory.")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
memory = MemoryService()
runtime = AgentRuntime(memory)

def current_user(authorization: str = Header(default="")) -> str:
    payload = verify_token(authorization.removeprefix("Bearer ").strip())
    if not payload:
        raise HTTPException(401, "Missing or invalid token. POST /api/auth/demo-login first.")
    return payload["sub"]

class ChatIn(BaseModel):
    agent: str
    message: str = Field(min_length=1)
    entity: str | None = None

class MemoryIn(BaseModel):
    agent: str = "strategy"
    kind: str = "semantic"
    text: str = Field(min_length=1)
    tags: list[str] = []
    entities: list[str] = []
    confidence: float = Field(0.5, ge=0, le=1)
    importance: float = Field(0.5, ge=0, le=1)

class OutcomeIn(BaseModel):
    agent: str
    action: str
    success: bool
    note: str = ""

def _agent(key: str):
    if key not in AGENTS:
        raise HTTPException(404, f"Unknown agent '{key}'. Valid: {list(AGENTS)}")

@app.get("/health")
def health():
    return {"status": "ok", "memory": memory.status()}

@app.post("/api/auth/demo-login")
def demo_login():
    return {"access_token": create_token("demo@memoryos.dev"), "token_type": "bearer"}

@app.get("/api/agents")
def agents(_: str = Depends(current_user)):
    return [{"key": a.key, "name": a.name, "focus": a.focus_tags} for a in AGENTS.values()]

@app.post("/api/chat")
def chat(body: ChatIn, _: str = Depends(current_user)):
    _agent(body.agent)
    return runtime.act(body.agent, body.message, body.entity)

@app.post("/api/outcomes")
def outcome(body: OutcomeIn, _: str = Depends(current_user)):
    _agent(body.agent)
    return runtime.learn(body.agent, body.action, body.success, body.note)

@app.post("/api/memories")
def add_memory(body: MemoryIn, _: str = Depends(current_user)):
    if body.kind not in KINDS:
        raise HTTPException(422, f"kind must be one of {sorted(KINDS)}")
    return memory.retain(body.agent, body.kind, body.text, body.tags, body.entities, body.confidence, body.importance)

@app.get("/api/memories")
def list_memories(agent: str | None = None, kind: str | None = None, limit: int = 100, _: str = Depends(current_user)):
    return memory.store.all(agent, kind, min(limit, 1000))

@app.delete("/api/memories/{mid}")
def delete_memory(mid: str, _: str = Depends(current_user)):
    if not memory.store.delete(mid):
        raise HTTPException(404, "memory not found")
    return {"deleted": mid}

@app.get("/api/search")
def search(q: str, agent: str | None = None, tag: str | None = None, entity: str | None = None,
           k: int = 10, _: str = Depends(current_user)):
    return memory.store.search(q, agent=agent, tag=tag, entity=entity, k=k)

@app.get("/api/graph")
def graph(_: str = Depends(current_user)):
    return memory.store.graph()

@app.get("/api/analytics/memory")
def analytics(_: str = Depends(current_user)):
    return memory.status()

@app.post("/api/demo/learning-loop")
def demo(_: str = Depends(current_user)):
    return run_learning_demo(runtime)
