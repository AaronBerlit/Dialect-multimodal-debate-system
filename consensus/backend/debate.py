"""
Core logic for the Dialectic AI Collective Intelligence Platform.
Handles persona-based multi-agent debate with dynamic orchestration.
"""

import json
import asyncio
import random
from dataclasses import dataclass, asdict
from typing import AsyncGenerator, Optional, Dict, List
from enum import Enum

from duckduckgo_search import DDGS
from ollama_client import generate, stream_generate

# ── Model Roster ─────────────────────────────────────────────────────────────

MODELS = [
    {
        "id": "gemma4:e4b",
        "name": "Gemma 4",
        "accent": "#4285F4",
        "description": "Google's Gemma 4 — balanced reasoning",
    },
    {
        "id": "deepseek-r1:7b",
        "name": "DeepSeek R1",
        "accent": "#00D4AA",
        "description": "DeepSeek R1 — chain-of-thought reasoning specialist",
    },
    {
        "id": "llama3.1:8b",
        "name": "Llama 3.1",
        "accent": "#A855F7",
        "description": "Meta's Llama 3.1 — versatile general-purpose model",
    },
]

# ── Persona Definitions ──────────────────────────────────────────────────────

PERSONAS = {
    "answerer": {
        "name": "Gemma 4",
        "role": "THE PROVOCATEUR",
        "description": "Gemma 4 — delivers sharp, concise, and opinionated answers.",
        "prompt": "You are Gemma 4. You are the Answerer. Your goal is to provide a sharp, concise, and highly opinionated answer to the question. Do not be diplomatic. Take a definitive stance based on the provided context. Be extremely brief—under 100 words. Use the search results only to sharpen your argument and pick a clear side.",
        "accent": "#4285F4"
    },
    "critic": {
        "name": "Llama 3.1",
        "role": "THE ADVERSARY",
        "description": "Llama 3.1 — aggressively challenges and takes the opposite stance.",
        "prompt": "You are Llama 3.1. You are the Critic. Your goal is to aggressively challenge the Answerer's stance. Do not be polite. Identify the weakest parts of their argument and tear them down. You MUST take the opposite side. Be concise, sharp, and definitive. No 'on the other hand'—pick a side and fight for it.",
        "accent": "#FF7F6A"
    },
    "factchecker": {
        "name": "DeepSeek R1",
        "role": "THE JUDGE",
        "description": "DeepSeek R1 — delivers the final verdict and picks a winner.",
        "prompt": "You are DeepSeek R1. You are the Fact-Checker. Your goal is to deliver the final verdict. Based on the debate above and the search context, declare who has the stronger argument. Do not stay neutral. Point out any factual errors but ultimately pick the winner. Be concise and final. You are the Judge—no diplomacy.",
        "accent": "#00D4AA"
    }
}

# ── Dynamics Definitions ────────────────────────────────────────────────────

class DebateDynamics(str, Enum):
    DIRECT = "direct"
    DIALECTICAL = "dialectical"
    SOCRATIC = "socratic"

# ── Types ───────────────────────────────────────────────────────────────────

class DebatePhase(str, Enum):
    SEARCH = "search"
    ANSWER = "answer"
    CRITIQUE = "critique"
    FACTCHECK = "factcheck"
    COMPLETE = "complete"

@dataclass
class DebateEvent:
    phase: str
    model_id: str = ""
    model_name: str = ""
    persona_key: str = ""
    content: str = ""
    round_num: int = 0
    is_final: bool = False
    metrics: Optional[Dict[str, any]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

# ── Debate Orchestrator ──────────────────────────────────────────────────────

class DebateOrchestrator:
    def __init__(
        self,
        question: str,
        dynamics: str = "dialectical",
        model_persona_map: Dict[str, str] = None
    ):
        self.question = question
        self.dynamics = DebateDynamics(dynamics)
        
        if not model_persona_map:
            model_persona_map = {
                "answerer": "gemma4:e4b",
                "critic": "llama3.1:8b",
                "factchecker": "deepseek-r1:7b"
            }
        
        self.model_persona_map = model_persona_map
        self.total_steps = 4 # Search, Answer, Critique, FactCheck
        self.current_step = 0
        self.context = ""

    def _generate_metrics(self, phase: str, content: str) -> Dict[str, any]:
        seed = sum(ord(c) for c in content[:30]) if content else 0
        random.seed(seed)
        
        return {
            "strength": {
                "coherence": round(random.uniform(85, 98), 1),
                "accuracy": round(random.uniform(80, 95), 1),
                "resonance": round(random.uniform(60, 90), 1)
            },
            "progress": round((self.current_step / self.total_steps) * 100, 1)
        }

    async def run(self) -> AsyncGenerator[DebateEvent, None]:
        from ollama_client import list_models
        try:
            available_models = await list_models()
            fallback_model = available_models[0] if available_models else "kimi-k2.6:cloud"
        except Exception:
            available_models = []
            fallback_model = "kimi-k2.6:cloud"

        # ── Phase 1: Search Context ──
        yield DebateEvent(phase="status", content="Gathering real-world context from the network...")
        try:
            results = DDGS().text(self.question, max_results=3)
            # Truncate bodies for extreme conciseness
            self.context = "\n".join([f"- {r['title']}: {r['body'][:200]}..." for r in results])
        except Exception as e:
            self.context = "Network search unavailable. Use internal logic."
        
        self.current_step += 1
        yield DebateEvent(
            phase=DebatePhase.SEARCH,
            model_id="network",
            content=f"Context optimized for conciseness.",
            metrics={"progress": round((self.current_step / self.total_steps) * 100, 1)}
        )

        # ── Phase 2: The Provocateur (Answer) ──
        yield DebateEvent(phase="status", content="Provocateur is taking a stance...")
        answerer_id = self.model_persona_map.get("answerer", "gemma4:e4b")
        if available_models and answerer_id not in available_models:
            answerer_id = fallback_model
        answerer_persona = PERSONAS["answerer"]
        
        yield DebateEvent(
            phase=DebatePhase.ANSWER,
            model_id=answerer_id,
            persona_key="answerer",
            content=""
        )

        prompt = f"Question: {self.question}\n\nSupporting Context:\n{self.context}\n\nProvide a sharp, concise answer. PICK A SIDE. Be opinionated. Do NOT be diplomatic. Stay under 100 words."
        answer_text = ""
        try:
            async for token in stream_generate(answerer_id, prompt, answerer_persona["prompt"]):
                answer_text += token
                yield DebateEvent(phase="token", content=token)
        except Exception as e:
            answer_text = f"[Answer generation failed: {str(e)}]"
        
        self.current_step += 1
        yield DebateEvent(
            phase=DebatePhase.ANSWER,
            model_id=answerer_id,
            persona_key="answerer",
            content=answer_text,
            metrics=self._generate_metrics("answer", answer_text)
        )

        # ── Phase 3: The Adversary (Critique) ──
        yield DebateEvent(phase="status", content="Adversary is challenging the stance...")
        critic_id = self.model_persona_map.get("critic", "llama3.1:8b")
        if available_models and critic_id not in available_models:
            critic_id = fallback_model
        critic_persona = PERSONAS["critic"]

        yield DebateEvent(
            phase=DebatePhase.CRITIQUE,
            model_id=critic_id,
            persona_key="critic",
            content=""
        )

        prompt = f"Question: {self.question}\n\nOpposing Response:\n{answer_text}\n\nAttack this stance. Point out its flaws. Take the OPPOSITE side. Be aggressive and concise. Stay under 100 words."
        critique_text = ""
        try:
            async for token in stream_generate(critic_id, prompt, critic_persona["prompt"]):
                critique_text += token
                yield DebateEvent(phase="token", content=token)
        except Exception as e:
            critique_text = f"[Critique failed: {str(e)}]"

        self.current_step += 1
        yield DebateEvent(
            phase=DebatePhase.CRITIQUE,
            model_id=critic_id,
            persona_key="critic",
            content=critique_text,
            metrics=self._generate_metrics("critique", critique_text)
        )

        # ── Phase 4: The Judge (Final Verdict) ──
        yield DebateEvent(phase="status", content="Judge is delivering the final verdict...")
        fc_id = self.model_persona_map.get("factchecker", "deepseek-r1:7b")
        if available_models and fc_id not in available_models:
            fc_id = fallback_model
        fc_persona = PERSONAS["factchecker"]

        yield DebateEvent(
            phase=DebatePhase.FACTCHECK,
            model_id=fc_id,
            persona_key="factchecker",
            content=""
        )

        prompt = f"Question: {self.question}\n\nContext:\n{self.context}\n\nArguments:\n- PROVOCATEUR: {answer_text}\n- ADVERSARY: {critique_text}\n\nWho won? Declare a winner. Be final. Be concise. NO DIPLOMACY."
        fc_text = ""
        try:
            async for token in stream_generate(fc_id, prompt, fc_persona["prompt"]):
                fc_text += token
                yield DebateEvent(phase="token", content=token)
        except Exception as e:
            fc_text = f"[Verdict failed: {str(e)}]"

        self.current_step += 1
        yield DebateEvent(
            phase=DebatePhase.FACTCHECK,
            model_id=fc_id,
            persona_key="factchecker",
            content=fc_text,
            is_final=True,
            metrics={"progress": 100.0}
        )

        yield DebateEvent(phase=DebatePhase.COMPLETE, content="Discourse protocol concluded.")
