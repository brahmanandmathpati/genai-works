# Session 27 - my hybrid search results

25 questions (12 exact incl. my 3, 13 meaning), top 3

| method | hit@3 | MRR | exact | meaning |
|---|---|---|---|---|
| keyword | 23/25 | 0.83 | 12/12 | 11/13 |
| dense | 23/25 | 0.85 | 10/12 | 13/13 |
| hybrid | 24/25 | 0.89 | 11/12 | 13/13 |
| weighted | 24/25 | 0.91 | 12/12 | 12/13 |
| rerank | 25/25 | 0.96 | 12/12 | 13/13 |

## My relevance gate

Gate -9.5: kept 14/14 in-scope questions, said 'I don't know' to 3/3 out-of-scope ones. Why this number: The lowest in-scope question scored -8.86 and the highest out-of-scope one -10.20, so -9.5 sits in the gap and keeps every real question while blocking the off-topic ones.

## My exact-term questions

- `SKU-CL-002` (products) -> SKU-CL-002
- `Office Classic loafers` (products) -> SKU-FW-005
- `DryFit` (products) -> SKU-CL-003
