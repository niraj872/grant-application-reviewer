import json, os, re
import httpx
from pydantic import BaseModel, ValidationError
from ..core import ai_provider
class AIError(Exception): pass
def llm(system: str, user: str) -> str:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key: raise AIError("ANTHROPIC_API_KEY is not set")
    r = httpx.post("https://api.anthropic.com/v1/messages", timeout=180,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
        json={"model": os.getenv("AI_MODEL", "claude-sonnet-4-5"), "max_tokens": 8000, "system": system,
              "messages": [{"role": "user", "content": user}]})
    if r.status_code != 200: raise AIError(f"LLM request failed ({r.status_code})")
    return "".join(b.get("text", "") for b in r.json()["content"])
def recover_json(raw: str):
    """Safe recovery: strip code fences, then try the outermost {...}."""
    s = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    for cand in (s, s[s.find("{"): s.rfind("}") + 1] if "{" in s else ""):
        try: return json.loads(cand)
        except (json.JSONDecodeError, ValueError): continue
    raise AIError("LLM returned invalid JSON")
def parse_validated(model: type[BaseModel], raw: str):
    try: return model.model_validate(recover_json(raw))
    except ValidationError as e: raise AIError(f"LLM output failed validation: {e.error_count()} error(s)")
def call(model, prompt: str):
    from .prompts import SYSTEM
    return parse_validated(model, llm(SYSTEM, prompt))
def is_demo(): return ai_provider() == "demo"
