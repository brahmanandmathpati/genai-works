"""Session 19 helpers - build a real conversation, measure what it costs, and fix the cost two ways.

Four ideas live here:
  1. A chat model has no memory between API calls. append_turn is the entire mechanism behind "the assistant
     remembers": it adds one message to a list that is resent, in full, on the NEXT call too.
  2. Cost is read off the real call, not guessed: every turn's token cost is whatever Lab.chat() reports for
     that call's prompt_tokens + completion_tokens, exactly like Session 15's metering habit, now over a whole
     conversation instead of one call.
  3. Two fixes for the resulting unbounded growth: slide_window (keep the last N messages, drop the rest) and
     summarize_older (compress older turns into one note, with one extra model call). Neither is free, and
     both are measured honestly against the same recall question.
  4. recall_succeeded checks ONLY the visible reply to the final turn - exactly the Session 17/18 habit of
     deciding what counts as success before looking at results.

Takes a Lab (module02/reasoning_utils.py), the same as Sessions 15-18."""
from __future__ import annotations

import datetime
import re
from pathlib import Path

from chat_tasks import BANKASSIST_SYSTEM, RECALL_PROBE, RECALL_TOKEN, SUMMARY_EVERY, WINDOW_SIZE
from prompt_utils import CheckResult

REPORT_PATH = Path("experiments") / "s19_chat_memory.md"
S19_CACHE = Path.home() / ".genai_course" / "s19_cache.json"

STRATEGIES = ("naive", "window", "summarize")


# ---------------------------------------------------------------- the whole mechanism: a list that grows
def append_turn(messages: list, role: str, content: str) -> list:
    """The entire fix for 'the model forgot' - a NEW message appended to a NEW list. messages itself is never
    mutated, so earlier snapshots (for a report, or a test) stay exactly as they were."""
    return messages + [{"role": role, "content": content}]


def format_turns(turns: list) -> str:
    """A scripted transcript, as readable text - used to ask the model to summarize older turns."""
    lines = []
    for m in turns:
        if m["role"] == "system":
            lines.append(f"Note: {m['content']}")
        else:
            speaker = "Customer" if m["role"] == "user" else "BankAssist"
            lines.append(f"{speaker}: {m['content']}")
    return "\n".join(lines)


# ---------------------------------------------------------------- fix 1: sliding window
def slide_window(messages: list, window_size: int = WINDOW_SIZE) -> list:
    """Keep the system message, plus only the last window_size messages after it. A no-op while the
    conversation is still shorter than the window - the trim only bites once it would matter."""
    system = messages[0]
    recent = messages[1:][-window_size:]
    return [system] + recent


# ---------------------------------------------------------------- fix 2: summarization
def summarize_older(lab, messages: list, system: dict, window_size: int = WINDOW_SIZE) -> list:
    """Compress everything older than the window into ONE extra model call, and splice the result in as a
    system-role note where the old messages used to be. One call per compression, not per turn."""
    recent = messages[1:][-window_size:]
    older = messages[1:-window_size] if len(messages) > window_size + 1 else []
    if not older:
        return messages
    ask = ("Summarize the key facts the customer has stated about THEMSELVES so far in this conversation, in "
           "one or two sentences. Keep any reference numbers, amounts or figures exactly as given, do not round "
           "or paraphrase them:\n\n" + format_turns(older))
    r = lab.chat([system, {"role": "user", "content": ask}], max_tokens=150)
    note = r["text"].strip()
    return [system, {"role": "system", "content": f"Earlier in this conversation: {note}"}] + recent


# ---------------------------------------------------------------- did the final turn recall the planted fact?
def recall_succeeded(reply_text: str, token: str = RECALL_TOKEN) -> bool:
    """Checks ONLY the visible reply to the recall question - not whether the model 'seems to understand',
    not partial credit. The planted reference number is either in the reply, or it is not."""
    return token in (reply_text or "")


# ---------------------------------------------------------------- run the whole scripted conversation, one strategy
def run_strategy(lab, strategy: str, *, script: list = None, system: str = None,
                 window_size: int = WINDOW_SIZE, summary_every: int = SUMMARY_EVERY, max_tokens: int = 300) -> dict:
    """Play the full RECALL_PROBE conversation through ONE memory strategy, turn by turn, exactly as a real
    application would: build the messages, apply the strategy's transform (if any), call the model, append the
    reply, move to the next turn. Returns the per-turn cost (so growth, or its absence, is visible), the final
    reply, and whether it recalled the planted fact."""
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy {strategy!r}; choose one of {STRATEGIES}")
    script = script if script is not None else RECALL_PROBE
    system_text = system if system is not None else BANKASSIST_SYSTEM
    messages = [{"role": "system", "content": system_text}]
    turn_costs, extra_calls, last_reply = [], 0, ""
    for i, user_text in enumerate(script, start=1):
        messages = append_turn(messages, "user", user_text)
        if strategy == "window":
            messages = slide_window(messages, window_size)
        elif strategy == "summarize" and i % summary_every == 0:
            messages = summarize_older(lab, messages, messages[0], window_size)
            extra_calls += 1
        r = lab.chat(messages, max_tokens=max_tokens)
        reply = r["text"].strip()
        turn_costs.append(r["prompt_tokens"] + r["completion_tokens"])
        messages = append_turn(messages, "assistant", reply)
        last_reply = reply
    return {"strategy": strategy, "n_turns": len(script), "turn_costs": turn_costs,
            "final_turn_cost": turn_costs[-1], "final_reply": last_reply,
            "recall_ok": recall_succeeded(last_reply), "extra_calls": extra_calls, "messages": messages}


def compare_strategies(lab, *, script: list = None, system: str = None,
                       window_size: int = WINDOW_SIZE, summary_every: int = SUMMARY_EVERY) -> dict:
    """The exact same 17-turn script, three ways - naive, window, summarize - so the only thing that changes
    between results is the memory strategy."""
    return {s: run_strategy(lab, s, script=script, system=system, window_size=window_size, summary_every=summary_every)
            for s in STRATEGIES}


# ---------------------------------------------------------------- reading the results
def turn_cost_table(result: dict) -> str:
    """Per-turn cost for ONE strategy's run - the shape of the growth (or its absence) is the point."""
    head = f"{'turn':>5}{'cost (tokens)':>16}"
    lines = [head, "-" * len(head)]
    for i, c in enumerate(result["turn_costs"], start=1):
        lines.append(f"{i:>5}{c:>16,}")
    return "\n".join(lines)


def strategy_comparison_table(results: dict) -> str:
    """One row per strategy: the cost of the FINAL (recall) turn, whether it recalled correctly, and how many
    extra model calls the strategy itself needed (summarization's own cost, beyond the 17 conversation turns)."""
    head = f"{'strategy':<12}{'final-turn cost':>18}{'recall':>10}{'extra calls':>13}"
    lines = [head, "-" * len(head)]
    for s in STRATEGIES:
        r = results[s]
        lines.append(f"{s:<12}{r['final_turn_cost']:>18,}{('yes' if r['recall_ok'] else 'no'):>10}{r['extra_calls']:>13}")
    return "\n".join(lines)


# ---------------------------------------------------------------- the report you commit
def chat_memory_markdown(results: dict, model: str, *, today: str = None) -> str:
    today = today or datetime.date.today().isoformat()
    n_turns = results["naive"]["n_turns"]
    lines = ["# Session 19: chat state & memory windows - naive vs sliding window vs summarization", "",
             f"Model: `{model}` · Date: {today} · Scripted conversation: {n_turns} turns, a reference "
             f"number planted at turn 2, asked for again at turn {n_turns}", "",
             f"| Strategy | Turn-{n_turns} cost (tokens) | Recall succeeded |", "|---|---|---|"]
    for s in STRATEGIES:
        r = results[s]
        lines.append(f"| {s} | {r['final_turn_cost']} | {'yes' if r['recall_ok'] else 'no'} |")
    lines += ["", "A strategy's cost is the input+output tokens of the FINAL (recall) turn only, not the whole "
              "conversation - this is the number that keeps climbing on a naive history and stays flat once a "
              f"fix is applied. 'Recall succeeded' means the reference number planted at turn 2 appeared in the "
              f"model's visible reply to turn {n_turns}, the only thing a recall check is allowed to look at."]
    return "\n".join(lines) + "\n"


def save_chat_report(repo_path, text: str) -> Path:
    target = Path(repo_path) / REPORT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


_ROW_RE = re.compile(r"\|\s*(naive|window|summarize)\s*\|\s*(\d+)\s*\|\s*(yes|no)\s*\|", re.IGNORECASE)


def parse_chat_report(text: str) -> dict:
    """{strategy: {"cost": int, "recall_ok": bool}} read back from a saved report, or {} if the table is missing."""
    rows = {}
    for m in _ROW_RE.finditer(text or ""):
        strat, cost, recall = m.group(1).lower(), int(m.group(2)), m.group(3).lower() == "yes"
        rows[strat] = {"cost": cost, "recall_ok": recall}
    return rows


# ---------------------------------------------------------------- is my work complete? (offline: no model call)
def check_s19_work(repo_path) -> list:
    """Plain-English checks on your work repository for Session 19. Each failure carries the fix."""
    repo = Path(repo_path)

    def ck(name, ok, fix="", info=""):
        return CheckResult(name, ok, info if ok else fix)
    if not repo.exists():
        return [ck("work repo folder exists", False, f"{repo} not found. Fix WORK_REPO.")]
    out = [ck("work repo folder exists", True)]

    report_file = repo / REPORT_PATH
    if not report_file.exists():
        out.append(ck("chat memory report exists", False, f"{REPORT_PATH} not found. Run notebook section 10 with SAVE_REPORT = True."))
        return out
    out.append(ck("chat memory report exists", True))

    text = report_file.read_text(encoding="utf-8")
    rows = parse_chat_report(text)
    have_all = set(rows) == set(STRATEGIES)
    out.append(ck("report covers all three strategies (naive, window, summarize)", have_all,
                  f"found {sorted(rows)}, need all three: {list(STRATEGIES)}. Re-save the report from section 10."))
    if not have_all:
        return out

    out.append(ck("naive strategy (full history) recalls the planted fact correctly", rows["naive"]["recall_ok"],
                  "naive history should always be able to recall it - check RECALL_TOKEN and RECALL_PROBE are unchanged in chat_tasks.py",
                  info="recalled correctly"))
    out.append(ck("sliding window costs less than naive at the final turn", rows["window"]["cost"] < rows["naive"]["cost"],
                  f"window cost {rows['window']['cost']} tokens, naive cost {rows['naive']['cost']} tokens - "
                  "a window should always be cheaper by the final turn",
                  info=f"{rows['window']['cost']} vs {rows['naive']['cost']} tokens"))
    out.append(ck("summarization costs less than naive at the final turn", rows["summarize"]["cost"] < rows["naive"]["cost"],
                  f"summarize cost {rows['summarize']['cost']} tokens, naive cost {rows['naive']['cost']} tokens - "
                  "summarizing older turns should still cost less than resending all of them",
                  info=f"{rows['summarize']['cost']} vs {rows['naive']['cost']} tokens"))
    return out
