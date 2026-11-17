"""Session 21 homework 4 - parity: does the LangChain version behave like the raw Session 20 code?

Runs YOUR ask() from bankassist_lc.py on Session 20's ten golden questions (tools attached, no fix = S20's "none"
way) and scores it with the same rules as Session 20 (_norm keyword match, expected tool names).

Run from the COURSE repository folder:
    uv run python $env:WORK_REPO\\s21\\parity.py
"""
import contextlib
import io
import os
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "module02"))
sys.path.insert(0, str(ROOT / "module03"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=True)

from tool_tasks import GOLDEN
from tool_utils import _norm
from s21_check import load_student

mod = load_student(os.environ["WORK_REPO"])
llm_with_tools = mod.make_llm().bind_tools(list(mod.TOOLS.values()))

rows = []
for item in GOLDEN:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):                 # ask() prints "step n: name(args)" for every tool call
        final = mod.ask(llm_with_tools, item["question"])
    called = re.findall(r"step \d+: (\w+)\(", buf.getvalue())
    text = _norm(final)
    answer_ok = bool(text) and (not item["answer_any"] or any(_norm(a) in text for a in item["answer_any"])) \
        and not any(_norm(b) in text for b in item["answer_not"])
    tool_ok = set(called) == set(item["expect_tools"])
    rows.append((item["id"], tool_ok, answer_ok, called, final))

n = len(rows)
print(f"LangChain ask() on the S20 golden set  (model: {os.environ['MODEL']})")
print(f"  right tool (or none): {sum(r[1] for r in rows)}/{n}")
print(f"  answer correct:       {sum(r[2] for r in rows)}/{n}")
print()
for gid, tool_ok, answer_ok, called, final in rows:
    print(f"{gid:<4} tool={'y' if tool_ok else 'n'} answer={'y' if answer_ok else 'n'}  called={called}")
    if not (tool_ok and answer_ok):
        print(f"      final: {final[:160]!r}")
