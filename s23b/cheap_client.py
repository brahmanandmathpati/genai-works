"""Session 23b homework 2 - call the gateway's third model group, `shopassist-cheap`.

The gateway's config.yaml got one more group (a small model). The app only changes the NAME it asks for:
    model="shopassist-cheap"   instead of   model="shopassist"
Run from the COURSE repository folder, with the gateway up on port 4000:
    uv run python "<work repo>\\s23b\\cheap_client.py"
"""
import os

import httpx
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))
URL = os.getenv("GATEWAY_URL", "http://localhost:4000")
KEY = os.getenv("LITELLM_MASTER_KEY", "sk-class-1234")          # the classroom master key, laptop only
QUESTION = "Can I return shoes after 5 days? Answer in one sentence."


def ask(group: str) -> dict:
    r = httpx.post(f"{URL}/v1/chat/completions", timeout=60, headers={"Authorization": f"Bearer {KEY}"},
                   json={"model": group, "messages": [{"role": "user", "content": QUESTION}], "max_tokens": 400})
    r.raise_for_status()
    body = r.json()
    return {"group": group, "answer": body["choices"][0]["message"]["content"], "tokens": body["usage"]["total_tokens"],
            "real_model": body.get("model"), "cost": r.headers.get("x-litellm-response-cost")}


if __name__ == "__main__":
    for group in ("shopassist", "shopassist-cheap"):
        out = ask(group)
        print(f"{out['group']:<18} real model: {out['real_model']:<26} tokens: {out['tokens']:<5} cost: {out['cost']}")
        print(f"   {out['answer'].strip()[:160]}")
