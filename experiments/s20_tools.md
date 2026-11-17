# Session 20: function calling - golden set, four ways

Model: `openai/gpt-oss-20b` · Date: 2026-11-03 · Golden set: 10 questions (6 need a tool, 4 need none)

| Way | Right tool (or none) | Args valid | Answer correct | Tokens |
|---|---|---|---|---|
| none | 10/10 | 6/6 | 10/10 | 17270 |
| prompt | 9/10 | 5/6 | 10/10 | 17908 |
| validate | 10/10 | 6/6 | 10/10 | 17270 |
| router | 10/10 | 6/6 | 10/10 | 18829 |

Per question (tool / args / answer, '-' = no tool needed):

| Question | none | prompt | validate | router |
|---|---|---|---|---|
| g1 | y/y/y | y/y/y | y/y/y | y/y/y |
| g2 | y/y/y | y/y/y | y/y/y | y/y/y |
| g3 | y/y/y | n/n/y | y/y/y | y/y/y |
| g4 | y/y/y | y/y/y | y/y/y | y/y/y |
| g5 | y/y/y | y/y/y | y/y/y | y/y/y |
| g6 | y/y/y | y/y/y | y/y/y | y/y/y |
| g7 | y/-/y | y/-/y | y/-/y | y/-/y |
| g8 | y/-/y | y/-/y | y/-/y | y/-/y |
| g9 | y/-/y | y/-/y | y/-/y | y/-/y |
| g10 | y/-/y | y/-/y | y/-/y | y/-/y |

Scores were decided before running: right tool means exactly the expected tools (none for a no-tool question); args valid counts tool questions only; answer correct checks the final text for the expected number or fact. A 10-question golden set is a smoke test - quote it with the model name.
