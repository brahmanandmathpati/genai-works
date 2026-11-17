"""Session 20, C6 assignment: stack the fixes - a fifth way, "router+validate".

Route first (Fix C); on the TOOL path also validate arguments in code (Fix B). The course files are pull-only, so
this script imports the course toolbox and adds the new way here instead of editing tool_utils.py.

Run from the COURSE repository folder (so .env is found):
    uv run python $env:WORK_REPO\\s20\\stack_router_validate.py
"""
import os
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "module02"))
sys.path.insert(0, str(ROOT / "module03"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=True)

from openai import OpenAI
from reasoning_utils import DiskCache
from tool_tasks import GOLDEN, TOOLS, WAYS
from tool_utils import (MAX_STEPS, S20_CACHE, compare_fixes, fixes_table, question_grid, route, run_with_tools,
                        score_question, system_for)

STACK = "router+validate"


def answer_stacked(client, model, question, *, max_steps=MAX_STEPS, max_tokens=1500, cache=None):
    """Same as answer_question(way="router"), except run_with_tools gets validate=True (the one-word change)."""
    messages = [{"role": "system", "content": system_for("router")}, {"role": "user", "content": question}]
    routed, router_tokens = route(client, model, question, max_tokens=max_tokens, cache=cache)
    res = run_with_tools(client, model, messages, tools=TOOLS if routed else None, validate=True,
                         max_steps=max_steps, max_tokens=max_tokens, cache=cache)
    res.update({"way": STACK, "routed_to_tools": routed, "router_tokens": router_tokens,
                "total_tokens": res["prompt_tokens"] + res["completion_tokens"] + router_tokens})
    return res


def score_stacked(client, model, *, cache=None):
    rows = []
    for item in GOLDEN:
        res = answer_stacked(client, model, item["question"], cache=cache)
        rows.append({"id": item["id"], "question": item["question"], **score_question(item, res),
                     "tools_called": [c["name"] for c in res["calls"]], "final_text": res["final_text"],
                     "tokens": res["total_tokens"], "capped": res["capped"]})
    tool_qs = [r for r, it in zip(rows, GOLDEN) if it["expect_tools"]]
    return {"way": STACK, "rows": rows, "n": len(rows), "n_tool": len(tool_qs),
            "tool_right": sum(r["tool_ok"] for r in rows), "args_ok": sum(bool(r["args_ok"]) for r in tool_qs),
            "answer_ok": sum(r["answer_ok"] for r in rows), "tokens": sum(r["tokens"] for r in rows)}


def main():
    client = OpenAI(api_key=os.environ["API_KEY"], base_url=os.environ["BASE_URL"])
    model = os.environ["MODEL"]
    cache = DiskCache(S20_CACHE)
    results = compare_fixes(client, model, cache=cache)          # the four ways (cached - free if already run)
    results[STACK] = score_stacked(client, model, cache=cache)   # the fifth
    print(f"model: {model}\n")
    print(fixes_table(results))
    print()
    print(question_grid(results))
    return results


if __name__ == "__main__":
    main()
