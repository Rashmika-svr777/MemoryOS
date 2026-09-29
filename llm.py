"""Groq chat completion via its OpenAI-compatible REST API (stdlib only).
Returns None without a key so agents use the deterministic offline composer."""
import json, urllib.request
from . import config

def complete(system: str, user: str):
    if not config.GROQ_API_KEY:
        return None
    body = json.dumps({"model": config.GROQ_MODEL, "temperature": 0.2,
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", body,
        {"Content-Type": "application/json", "Authorization": f"Bearer {config.GROQ_API_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["choices"][0]["message"]["content"]
    except Exception:
        return None
