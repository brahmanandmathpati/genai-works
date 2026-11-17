# Session 17: prompt evaluation - v1 baseline vs v2 structured

Answering model: `openai/gpt-oss-20b` · Judge model: `openai/gpt-oss-20b` · Date: 2026-10-31

| Criterion | v1 (S14 baseline) | v2 (S16 structured) |
|---|---|---|
| Correct label | 15/20 = 75% | 20/20 = 100% |
| Cites the right house rule | 12/20 = 60% | 15/20 = 75% |
| Follows the reply format | 19/20 = 95% | 20/20 = 100% |
| Invents no policy | 20/20 = 100% | 20/20 = 100% |
| **All four criteria** | **12/20 = 60%** | **15/20 = 75%** |

Tickets graded: v1 20/20 · v2 20/20 (a ticket the judge could not parse is not counted, and is listed below).

Human spot-check: judge and human agreed on 19/20 = 95% of graded criteria (19/20).
