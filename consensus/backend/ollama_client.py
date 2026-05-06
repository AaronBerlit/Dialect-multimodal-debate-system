"""
Async client wrapper for the Ollama REST API.
Handles generating responses from local LLM models.
"""

import httpx
import json
import asyncio
from typing import AsyncGenerator

OLLAMA_BASE_URL = "http://localhost:11434"


async def check_health() -> bool:
    """Check if Ollama is running and reachable."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            return resp.status_code == 200
    except Exception:
        return False


async def list_models() -> list[str]:
    """Return a list of locally available model names."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]


async def generate(model: str, prompt: str, system: str = "") -> str:
    """
    Generate a complete response from a model (non-streaming).
    Returns the full text response.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": 0,
        "options": {
            "temperature": 0.7,
            "num_predict": 1024,
        },
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=1200.0,
        )
        resp.raise_for_status()
        return resp.json()["response"]


async def stream_generate(
    model: str, prompt: str, system: str = ""
) -> AsyncGenerator[str, None]:
    """
    Stream tokens from a model as they are generated.
    Yields individual text chunks.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "keep_alive": 0,
        "options": {
            "temperature": 0.7,
            "num_predict": 1024,
        },
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=1200.0,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break
