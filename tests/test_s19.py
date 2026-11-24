"""Session 19 checkpoint. Run with:  uv run pytest tests/test_s19.py -rs

Everything here is offline EXCEPT the checkpoint at the bottom. The offline tests use a scripted stand-in for
BankAssist, so they cost nothing, never touch the network, and give the same result every time: the fake model
reads whatever messages were actually sent on each call and bases its reply (and simulated token cost) on
exactly that - which is what lets these tests prove append_turn/slide_window/summarize_older are doing their
job, without ever calling a real model.

THE CHECKPOINT: test_checkpoint_your_chat_memory_report_is_complete loads YOUR report from YOUR work repository
(experiments/s19_chat_memory.md) and checks it is complete: all three strategies (naive, window, summarize)
scored, naive correctly recalling the planted fact (a sanity check on the setup itself), and both fixes costing
less than naive at the final turn. It needs a key in .env and WORK_REPO set (in .env, or in the shell before
you run pytest):

    WORK_REPO=C:\\Users\\you\\Documents\\genai-course-work

With no key it is skipped (read the reason: -rs). A skip is not a pass."""
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from dotenv import load_dotenv

load_dotenv(override=True)   # read .env BEFORE the skip checks below, so a key stored only in .env is seen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "module02"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "module03"))
from chat_tasks import BANKASSIST_SYSTEM, RECALL_PROBE, RECALL_TOKEN, SUMMARY_EVERY, WINDOW_SIZE  # noqa: E402
from chat_utils import (append_turn, chat_memory_markdown, check_s19_work, compare_strategies, format_turns,  # noqa: E402
                        parse_chat_report, recall_succeeded, run_strategy, save_chat_report, slide_window,
                        strategy_comparison_table, summarize_older, turn_cost_table)
from reasoning_utils import Lab  # noqa: E402


# ---------------------------------------------------------------- a scripted stand-in for BankAssist
def reply(text, prompt_tokens=None, completion_tokens=20):
    """prompt_tokens defaults to a number proportional to how much text was actually sent, so a scripted
    conversation's measured cost really does grow (or not) with what the strategy under test kept or dropped."""
    usage = SimpleNamespace(prompt_tokens=prompt_tokens if prompt_tokens is not None else 50,
                             completion_tokens=completion_tokens, completion_tokens_details=None)
    msg = SimpleNamespace(content=text, reasoning=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="stop")], usage=usage)


class FakeClient:
    def __init__(self, handler):
        self.handler, self.calls = handler, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self.handler(kwargs, len(self.calls))


def lab_for(client, **kw):
    return Lab(client, "openai/gpt-oss-20b", sleep=lambda s: None, **kw)


def honest_bankassist_lab():
    """A scripted BankAssist that genuinely only knows what is in the messages it was actually sent: it hunts
    for RECALL_TOKEN in the call's own messages (any role) before answering the recall question, and reports a
    prompt cost proportional to the total characters sent - so the fake models exactly what the real course
    goal is: a reply (and a cost) that depend only on what the strategy kept in the call, nothing else."""
    def handler(kw, n):
        messages = kw["messages"]
        total_chars = sum(len(m["content"]) for m in messages)
        last_user = messages[-1]["content"]
        if "remind me of the reference number" in last_user.lower():
            seen = any(RECALL_TOKEN in m["content"] for m in messages)
            text = f"Of course - your reference number is {RECALL_TOKEN}." if seen else \
                   "I'm sorry, I don't have a reference number on file for this chat - could you share it again?"
        elif "Summarize the key facts" in last_user:
            # the summarizing call: if the planted fact is in what it was asked to summarize, keep it verbatim
            text = (f"The customer is self-employed with an annual income of about Rs 8.5 lakh, looking at a "
                    f"home loan of around Rs 25 lakh over 20 years, reference number {RECALL_TOKEN}."
                    if RECALL_TOKEN in last_user else "The customer asked some general questions.")
        else:
            text = "Thanks for your question - here's what I can tell you about that."
        return reply(text, prompt_tokens=max(20, total_chars // 4))
    return lab_for(FakeClient(handler))


def write_work(tmp_path, report=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    if report is not None:
        (tmp_path / "experiments").mkdir(parents=True, exist_ok=True)
        (tmp_path / "experiments" / "s19_chat_memory.md").write_text(report, encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------- the data itself
def test_recall_probe_plants_the_token_at_turn_2_and_asks_for_it_back_at_the_last_turn():
    assert RECALL_TOKEN in RECALL_PROBE[1]
    assert "reference number" in RECALL_PROBE[-1].lower()
    assert len(RECALL_PROBE) == 17
    for turn in RECALL_PROBE[2:-1]:
        assert RECALL_TOKEN not in turn   # the filler turns are genuinely unrelated, not a second copy of the fact


def test_bankassist_system_prompt_instructs_remembering_but_states_no_reference_number_itself():
    low = BANKASSIST_SYSTEM.lower()
    assert "remember" in low
    assert RECALL_TOKEN not in BANKASSIST_SYSTEM   # the model could only get this from the conversation, never the prompt


# ---------------------------------------------------------------- the whole mechanism: a list that grows
def test_append_turn_returns_a_new_list_and_never_mutates_the_original():
    original = [{"role": "system", "content": "x"}]
    grown = append_turn(original, "user", "hello")
    assert len(original) == 1 and len(grown) == 2
    assert grown[-1] == {"role": "user", "content": "hello"}


def test_format_turns_labels_each_role_in_plain_text():
    turns = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"},
             {"role": "system", "content": "a note"}]
    text = format_turns(turns)
    assert "Customer: hi" in text and "BankAssist: hello" in text and "Note: a note" in text


# ---------------------------------------------------------------- fix 1: sliding window
def test_slide_window_keeps_the_system_message_and_only_the_last_n_after_it():
    system = {"role": "system", "content": "sys"}
    messages = [system] + [{"role": "user", "content": str(i)} for i in range(10)]
    trimmed = slide_window(messages, window_size=4)
    assert trimmed[0] == system
    assert len(trimmed) == 5
    assert [m["content"] for m in trimmed[1:]] == ["6", "7", "8", "9"]


def test_slide_window_is_a_no_op_while_the_conversation_is_still_shorter_than_the_window():
    system = {"role": "system", "content": "sys"}
    messages = [system, {"role": "user", "content": "1"}, {"role": "user", "content": "2"}]
    assert slide_window(messages, window_size=6) == messages


# ---------------------------------------------------------------- fix 2: summarization
def test_summarize_older_is_a_no_op_until_there_is_something_older_than_the_window():
    system = {"role": "system", "content": "sys"}
    lab = honest_bankassist_lab()
    messages = [system, {"role": "user", "content": "1"}, {"role": "user", "content": "2"}]
    assert summarize_older(lab, messages, system, window_size=6) == messages


def test_summarize_older_spends_exactly_one_extra_call_and_splices_in_a_system_note():
    system = {"role": "system", "content": "sys"}
    lab = honest_bankassist_lab()
    messages = [system] + [{"role": "user", "content": f"turn {i}, ref {RECALL_TOKEN}" if i == 1 else f"turn {i}"}
                            for i in range(1, 11)]
    before_calls = len(lab.client.calls)
    compressed = summarize_older(lab, messages, system, window_size=4)
    assert len(lab.client.calls) == before_calls + 1   # exactly one extra call, not one per older turn
    assert compressed[0] == system
    assert compressed[1]["role"] == "system" and "Earlier in this conversation" in compressed[1]["content"]
    assert len(compressed) == 1 + 1 + 4   # system + summary note + the kept window


def test_summarize_older_is_asked_to_preserve_reference_numbers_exactly():
    system = {"role": "system", "content": "sys"}
    captured = {}

    def handler(kw, n):
        captured["ask"] = kw["messages"][-1]["content"]
        return reply("a summary")
    lab = lab_for(FakeClient(handler))
    messages = [system] + [{"role": "user", "content": f"ref {RECALL_TOKEN}"}] + \
               [{"role": "user", "content": str(i)} for i in range(6)]
    summarize_older(lab, messages, system, window_size=4)
    assert "exactly" in captured["ask"].lower() and "reference number" in captured["ask"].lower()


# ---------------------------------------------------------------- did the final turn recall the planted fact?
def test_recall_succeeded_checks_only_the_exact_token():
    assert recall_succeeded(f"your reference number is {RECALL_TOKEN}") is True
    assert recall_succeeded("I don't have a reference number on file") is False
    assert recall_succeeded("") is False
    assert recall_succeeded(None) is False


# ---------------------------------------------------------------- running the whole scripted conversation
def test_run_strategy_rejects_an_unknown_strategy_name():
    with pytest.raises(ValueError):
        run_strategy(honest_bankassist_lab(), "something_else")


def test_naive_strategy_recalls_the_planted_fact_even_with_every_filler_turn_in_between():
    result = run_strategy(honest_bankassist_lab(), "naive")
    assert result["recall_ok"] is True
    assert result["n_turns"] == len(RECALL_PROBE)
    assert result["extra_calls"] == 0   # naive never spends an extra call - it just resends everything


def test_naive_strategys_per_turn_cost_never_goes_down():
    result = run_strategy(honest_bankassist_lab(), "naive")
    costs = result["turn_costs"]
    assert all(costs[i] <= costs[i + 1] for i in range(len(costs) - 1))
    assert costs[-1] > costs[0]   # the whole point: the list only ever grows


def test_window_strategy_drops_the_planted_fact_once_it_falls_outside_the_window():
    result = run_strategy(honest_bankassist_lab(), "window", window_size=WINDOW_SIZE)
    assert result["recall_ok"] is False   # by design: the reference number is 15 turns back by the final turn
    assert result["extra_calls"] == 0


def test_window_strategys_final_turn_cost_is_lower_than_naives():
    naive = run_strategy(honest_bankassist_lab(), "naive")
    window = run_strategy(honest_bankassist_lab(), "window", window_size=WINDOW_SIZE)
    assert window["final_turn_cost"] < naive["final_turn_cost"]


def test_summarize_strategy_spends_extra_calls_and_usually_recovers_recall():
    result = run_strategy(honest_bankassist_lab(), "summarize", window_size=WINDOW_SIZE, summary_every=SUMMARY_EVERY)
    assert result["extra_calls"] > 0
    assert result["recall_ok"] is True   # the scripted summarizer always keeps the reference number, by design here


def test_summarize_strategys_final_turn_cost_is_lower_than_naives():
    naive = run_strategy(honest_bankassist_lab(), "naive")
    summarize = run_strategy(honest_bankassist_lab(), "summarize", window_size=WINDOW_SIZE, summary_every=SUMMARY_EVERY)
    assert summarize["final_turn_cost"] < naive["final_turn_cost"]


def test_compare_strategies_runs_all_three_over_the_same_script():
    results = compare_strategies(honest_bankassist_lab())
    assert set(results) == {"naive", "window", "summarize"}
    assert all(r["n_turns"] == len(RECALL_PROBE) for r in results.values())


# ---------------------------------------------------------------- reading the results
def test_turn_cost_table_has_one_row_per_turn():
    result = run_strategy(honest_bankassist_lab(), "naive")
    table = turn_cost_table(result)
    lines = table.splitlines()
    assert len(lines) == 2 + len(RECALL_PROBE)   # header + separator rule + one row per turn
    assert lines[-1].strip().startswith(str(len(RECALL_PROBE)))   # the last row is turn 17


def test_strategy_comparison_table_has_one_row_per_strategy():
    results = compare_strategies(honest_bankassist_lab())
    table = strategy_comparison_table(results)
    for strategy in ("naive", "window", "summarize"):
        assert strategy in table
    assert "yes" in table and "no" in table   # naive recalls, window does not - both should show up


# ---------------------------------------------------------------- the report you commit
def fixed_results(naive_ok=True, naive_cost=4000, window_ok=False, window_cost=400, summarize_ok=True, summarize_cost=900, extra_calls=3):
    def row(ok, cost, extra=0):
        return {"strategy": "x", "n_turns": 17, "turn_costs": [cost], "final_turn_cost": cost,
                "final_reply": "...", "recall_ok": ok, "extra_calls": extra, "messages": []}
    return {"naive": row(naive_ok, naive_cost), "window": row(window_ok, window_cost),
            "summarize": row(summarize_ok, summarize_cost, extra_calls)}


def test_chat_memory_markdown_states_all_three_rows_and_the_recall_column():
    text = chat_memory_markdown(fixed_results(), "m", today="2026-10-27")
    assert "| naive | 4000 | yes |" in text
    assert "| window | 400 | no |" in text
    assert "| summarize | 900 | yes |" in text
    parsed = parse_chat_report(text)
    assert parsed == {"naive": {"cost": 4000, "recall_ok": True}, "window": {"cost": 400, "recall_ok": False},
                       "summarize": {"cost": 900, "recall_ok": True}}


def test_parse_chat_report_returns_empty_without_the_table():
    assert parse_chat_report("nothing useful here") == {}


def test_the_report_is_saved_where_the_checker_looks(tmp_path):
    text = chat_memory_markdown(fixed_results(), "m")
    path = save_chat_report(tmp_path, text)
    assert path == tmp_path / "experiments" / "s19_chat_memory.md" and path.exists()


# ---------------------------------------------------------------- is my work complete? (offline: no model call)
def test_check_s19_work_passes_a_complete_submission(tmp_path):
    text = chat_memory_markdown(fixed_results(), "m")
    repo = write_work(tmp_path, report=text)
    results = check_s19_work(repo)
    failed = [r for r in results if not r.passed]
    assert not failed, [(r.name, r.detail) for r in failed]
    assert len(results) >= 5


def test_check_s19_work_catches_a_missing_report(tmp_path):
    assert not check_s19_work(tmp_path / "nowhere")[0].passed
    no_report = write_work(tmp_path / "no_report")
    msgs = {r.name: r.passed for r in check_s19_work(no_report)}
    assert msgs["chat memory report exists"] is False


def test_check_s19_work_catches_a_missing_strategy(tmp_path):
    text = chat_memory_markdown(fixed_results(), "m")
    text = "\n".join(line for line in text.splitlines() if not line.startswith("| summarize"))   # simulate a hand-edited, incomplete report
    repo = write_work(tmp_path, report=text)
    failed = {r.name for r in check_s19_work(repo) if not r.passed}
    assert any("all three strategies" in n for n in failed)


def test_check_s19_work_catches_naive_failing_to_recall_its_own_planted_fact(tmp_path):
    text = chat_memory_markdown(fixed_results(naive_ok=False), "m")   # naive itself failing means the setup is broken
    repo = write_work(tmp_path, report=text)
    failed = {r.name for r in check_s19_work(repo) if not r.passed}
    assert any("naive strategy" in n for n in failed)


def test_check_s19_work_catches_a_fix_that_costs_more_than_naive(tmp_path):
    text = chat_memory_markdown(fixed_results(window_cost=9000), "m")   # window somehow costs MORE than naive
    repo = write_work(tmp_path, report=text)
    failed = {r.name for r in check_s19_work(repo) if not r.passed}
    assert any("sliding window costs less" in n for n in failed)


# ---------------------------------------------------------------- the notebook
def test_the_notebook_is_valid_and_compiles():
    nb = json.loads((Path(__file__).resolve().parents[1] / "module03" / "s19_chat_memory.ipynb").read_text(encoding="utf-8"))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(code) >= 8
    for i, cell in enumerate(code):
        compile("".join(cell["source"]), f"cell {i}", "exec")


# ---------------------------------------------------------------- the checkpoint (live: need a key)
LIVE = bool(os.getenv("API_KEY") and os.getenv("BASE_URL") and os.getenv("MODEL"))


@pytest.mark.skipif(not LIVE, reason="no API key in .env: the checkpoint cannot run yet")
def test_checkpoint_your_chat_memory_report_is_complete():
    repo = os.getenv("WORK_REPO")
    if not repo:
        pytest.fail("Set WORK_REPO to your work repository folder, in .env or in the shell, then run this again. "
                    "Example (PowerShell):  $env:WORK_REPO = \"$HOME\\Documents\\genai-course-work\"")
    results = check_s19_work(repo)
    for r in results:
        print(f"  {'PASS' if r.passed else 'FAIL'}  {r.name}" + (f"   ({r.detail})" if r.detail else ""))
    failed = [r for r in results if not r.passed]
    assert not failed, "fix the FAILs above, then run this again"
