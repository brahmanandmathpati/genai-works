# Session 19: chat state & memory windows - naive vs sliding window vs summarization

Model: `openai/gpt-oss-20b` · Date: 2026-11-03 · Scripted conversation: 17 turns, a reference number planted at turn 2, asked for again at turn 17

| Strategy | Turn-17 cost (tokens) | Recall succeeded |
|---|---|---|
| naive | 1747 | yes |
| window | 918 | no |
| summarize | 1287 | no |

A strategy's cost is the input+output tokens of the FINAL (recall) turn only, not the whole conversation - this is the number that keeps climbing on a naive history and stays flat once a fix is applied. 'Recall succeeded' means the reference number planted at turn 2 appeared in the model's visible reply to turn 17, the only thing a recall check is allowed to look at.
