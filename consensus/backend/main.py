import os
import asyncio
from typing import Optional, Dict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ollama_client import check_health, list_models
from debate import DebateOrchestrator, MODELS, PERSONAS

app = FastAPI(title="Dialectic — AI Collective Intelligence")

# API Endpoints FIRST to avoid shadow by StaticFiles
@app.get("/api/health")
async def health():
    return {"status": "ok", "ollama": await check_health()}

@app.get("/api/models")
async def get_models():
    """Return the roster of models and personas."""
    available = await list_models()
    
    model_roster = []
    for m in MODELS:
        m_copy = m.copy()
        m_copy["installed"] = any(m["id"] in a for a in available)
        model_roster.append(m_copy)
        
    return {
        "models": model_roster,
        "personas": PERSONAS
    }

class DebateRequest(BaseModel):
    question: str
    dynamics: str = "dialectical"
    personas: Optional[Dict[str, str]] = None

@app.post("/api/debate")
async def start_debate(request: DebateRequest):
    valid_dynamics = ["direct", "dialectical", "socratic"]
    if request.dynamics not in valid_dynamics:
        request.dynamics = "dialectical"

    orchestrator = DebateOrchestrator(
        question=request.question,
        dynamics=request.dynamics,
        model_persona_map=request.personas
    )

    async def event_generator():
        async for event in orchestrator.run():
            yield f"data: {event.to_json()}\n\n"
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Mount frontend as the ROOT
# This will serve index.html automatically for /
import starlette.staticfiles

class NoCacheStaticFiles(starlette.staticfiles.StaticFiles):
    def is_not_modified(self, response_headers, request_headers):
        return False
    
    async def get_response(self, path: str, scope):
        resp = await super().get_response(path, scope)
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resp

app.mount("/", NoCacheStaticFiles(directory="../frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    import asyncio
    from ollama_client import list_models
    
    async def startup_check():
        print("\n[+] Checking model availability...")
        try:
            available = await list_models()
            required = [m["id"] for m in MODELS]
            missing = [m for m in required if not any(m in a for a in available)]
            
            if missing:
                print(f"    [!] Warning: Missing models: {', '.join(missing)}")
                print("    [!] Please run 'setup_models.ps1' to configure the D drive path.\n")
            else:
                print("    [+] All required models are available.\n")
        except Exception as e:
            print(f"    [!] Could not connect to Ollama: {e}\n")

    print("\n[+] Dialectic starting...")
    print("    Open http://localhost:8000 in your browser\n")
    
    # Run startup check in the background loop if possible, or just before run
    loop = asyncio.new_event_loop()
    loop.run_until_complete(startup_check())
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
