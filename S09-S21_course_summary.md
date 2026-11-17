# GenAI Agents Course — Sessions 9 to 27, summarised

One page per session: what it is about, the ideas to remember, one interview answer, and what my own lab
run showed. Built from each notebook's Part C summary. Model for my runs: `openai/gpt-oss-20b` on Groq.

## The one thread through all the sessions

```
 S09a-S09  call a model, count tokens          ─┐
 S10-S13   choose a model: where, cost, speed  │  "how do I talk to a model?"
           local vs hosted, images, JSON       ─┘
 S14-S18   prompts: anatomy, reasoning,        ─┐
           structure, evaluation, defence      ─┘  "how do I get a good, safe answer — and prove it?"
 S19-S21   conversation, tools, a framework    ─┐  "how do I build an assistant?"
                                                ─┘
```

Five ideas come back in almost every session:

1. **The model is stateless and never runs anything.** Your code sends everything, every time, and decides what
   to execute.
2. **Every call has a bill** in tokens, seconds and money. Output (including hidden reasoning) costs the most.
3. **A prompt is a request, a schema is a request.** Anything that matters is checked in code.
4. **Measure, don't assume.** Fixed test set, checks decided first, change one thing at a time.
5. **Keep evidence.** Prompts and reports live in a Git work repository, versioned, never overwritten.

---

## S09a · Environment and your first LLM call

**What it is about:** setting up one repo, one Python, one config file, and rebuilding `hello.py` step by step.

**Remember**
- `uv sync` + `uv.lock` give every laptop the same environment. Every command starts with `uv run`.
- Three settings, no secrets in code: `BASE_URL` (where), `API_KEY` (who), `MODEL` (which), read from `.env`,
  which `.gitignore` keeps off GitHub.
- A reply can be read all at once (`choices[0].message.content`) or streamed chunk by chunk.
- Errors are messages: 401 = key, 404 = model, 429 = wait, no connection = network or Ollama not running.

**Interview:** *Where do you keep API keys?* In a git-ignored `.env` locally and a secrets manager in production,
read as environment variables. If one leaks, revoke it at once — deleting the commit is not enough.

**My run:** Python 3.12.14 in the project `.venv`, `.env` found, key shown only masked. The same hello prompt cost
177 tokens not streamed and 175 streamed (72 chunks); the setup self-test passed 3/3.

## S09 · How LLMs work: tokens, cost, context window, embeddings

**Remember**
- A model sees **tokens**, not words. The tokenizer belongs to the model, so counts differ between models;
  Telugu, code and JSON cost more than English prose.
- Trust the provider's **`usage`** field for budgets: it includes the hidden chat-template wrapper.
- **Cost = tokens in × input price + tokens out × output price.** The answer usually dominates the bill.
- The **context window** is a budget. The model remembers nothing; your code resends history every turn.
- An **embedding** turns text into a vector so similar meanings sit close together. It never answers.

**Interview:** *Why can the provider's token count differ from yours?* Different tokenizer, plus a chat template
the provider adds and bills. Measure it; don't hard-code it.

**My run:** the same loan question was 16 tokens in English and 25 in Telugu (2.7 UTF-8 bytes per character).
`tiktoken` counted 16, but Groq's `usage` reported 87 — the chat wrapper. Output was 97% of the cost of a call,
and a 20-turn chat had grown to 1,550 tokens per call.

## S10 · The model landscape

**Remember**
- Three ways to get a model: **vendor API** (closed), **hosted open-weight**, **self-hosted**. They differ in who
  sees your data, who bills you and who is on call.
- **Price the task, not the token:** monthly cost = calls × tokens × price / 1,000,000 + fixed cost.
- Speed is three numbers: time to first token, tokens per second, total time.
- **Eliminate, then score, then verify:** hard constraints first, a weighted score second, your own examples last.
- A decision record names the choice, the runner-up, the assumptions and what would change your mind.

**Interview:** *How would you choose an LLM for a new use case?* Remove options with hard constraints (data
residency, latency, volume, context), rank survivors on cost, speed and quality with agreed weights, then test
the top two on my own examples.

**My run:** the FAQ job (20,000 calls a day) priced at Rs 8,460 a month on gpt-oss-20b (Groq), Rs 65,800
self-hosted and Rs 6,20,400 on a frontier flagship. Speed: Groq answered in 2.18 s at 385 tokens/s; llama3.2:3b on
my laptop took 34.5 s at 3.6 tokens/s. gpt-oss-20b ranked first for the FAQ job (score 90.0).

## S11 · Multi-provider calls

**Remember**
- A **provider** is where a model runs; a **model** is which brain answers. One `ask()` function serves Groq,
  Gemini and Ollama — only the client and model name change.
- The **system message** is the job description.
- `max_tokens` is a ceiling that cuts (hidden reasoning counts too); `stop` ends the reply at a string.
- **Temperature** controls randomness. Decisions such as routing belong at 0.

**Interview:** *How do you switch providers without rewriting code?* Keep provider settings in configuration and
route every call through one OpenAI-compatible function. Compatibility covers common features only, so test each.

**My run:** the same `ask()` worked on Groq (230 tokens) and Ollama (91 tokens); Gemini returned a 503 "high demand"
error that run — providers fail, and code must handle it. At temperature 0.3 one borderline ticket drifted
(`billing, technical, billing`), which is why classifiers run at 0.

## S12 · Local and open models

**Remember**
- Open-weight models come with a **model card** and a **licence**; **Ollama** runs them, it trains nothing.
- **Weight memory = parameters × bytes per parameter** (20B at int4 ≈ 10 GB), plus headroom for the KV cache.
- **Quantization** stores weights in fewer bits: about a quarter of the memory, small task-dependent accuracy cost.
- Hosted is typically 5–15× faster than a laptop. Local is right when data must stay in-house or offline.

**Interview:** *When would you self-host?* When data may not leave (customer PII), when offline, or when volume
makes owning hardware cheaper. Cost: you own the hardware, and small local models are slower and less accurate.

**My run:** `qwen2.5:1.5b` and `llama3.2:3b` both passed the tool-calling probe; `nomic-embed-text` (an embedding
model) did not. Ollama took 3.2 s to the first token at 13 tokens/s. Groq hit its 1,500-token ceiling after 13.5 s
of hidden reasoning — `max_tokens` cutting, as S11 warned. Earlier, loading `llama3.2:3b` failed with under 1 GB
of free RAM: the "keep headroom" rule in practice.

## S13 · Images in, structured data out

**Remember**
- An image is more content: the message `content` becomes a list (text + base64 image), billed in tokens.
- Three levels of structure: **asking** is a request, **JSON mode** guarantees valid JSON, **strict schema**
  guarantees your exact shape.
- **Shape is not truth.** Business rules (dates, misread letters) live in your code.
- Retry once with the exact error, then hand to a human.

**Interview:** *How do you get reliable JSON out of an LLM?* Use the strongest mode the model supports, then
validate in code. JSON mode promises syntax only; strict mode constrains the shape; neither checks the values.

**My run:** the vision model `qwen/qwen3.8-27b` read the sample ID card with every field matching. One image added
about 1,794 prompt tokens (40 → 1,834). All three structure levels passed 5/5; the validator rejected a future date
of birth and a bad ID pattern, and a misread ID number failed twice and was routed to a human.

---

## S14 · Prompt anatomy

**Remember**
- A prompt has **five parts**: role, task, context, constraints, output format (plus optional examples).
  A missing part shows up as a specific failing check.
- Standing rules go in the **system** message; the job goes in the **user** message.
- **"Better" needs a number:** write acceptance checks first, change one part at a time.
- A prompt is an asset: every version goes into `prompts/library.md`. Never edit an old entry.

**Interview:** *What makes a good prompt?* The five parts, paired with checks — structure makes the right answer
much more likely, not certain.

**My run:** all three tasks passed every check — credit summary 4/4, declined-loan SMS 6/6, complaint triage
JSON 4/4. Saved as v1 in `prompts/library.md`.

## S15 · Reasoning prompts

**Remember**
- **Thinking is billed**, hidden or visible.
- Match the method to the trap: **step by step** for chained steps, **step back** for choosing the rule, a
  **vote** for random slips (never a wrong rule).
- Thinking cannot supply a missing rule, and should not do arithmetic a calculator does exactly.
- The scratchpad stays behind a curtain: checks run on `<final>` only.

**Interview:** *When does chain-of-thought not help?* When the rule is missing from the prompt, or on a reasoning
model that already thinks — it adds cost for little gain. Decide per kind of question, from measurements.

**My run:** the scratchpad (v2) passed the same checks as v1 on both tasks. Credit summary: 4/4 either way,
977 vs 1,094 tokens (0.9×). SMS: 6/6 either way, 953 vs 727 tokens (1.3×) — so v1 is enough there.

## S16 · Structured prompting

**Remember**
- **Keep instructions and data apart:** customer text inside `<ticket>` tags, the system prompt says what the tags
  mean, and code escapes your own tag names inside customer text.
- **Tags are hygiene, not a shield** against deliberate attacks.
- A prompt for a million tickets is a **Jinja template**; `StrictUndefined` makes a missing value an error.
- The system prompt is a **versioned file** with front matter and a fingerprint.
- Examples come from the **training pool**; accuracy comes from the **held-out set**. Never leak test items.

**Interview:** *How do you stop user input being read as instructions?* Delimit it, say in the system prompt it is
data only, and escape your tag names. That removes accidental confusion — deliberate attacks need more layers.

**My run:** held-out accuracy **20/20** with the structured prompt vs **15/20** for the one-line baseline
(gate: 16/20).

## S17 · Prompt evaluation

**Remember**
- A label match is not a good reply. A **rubric** of pass/fail criteria, decided before reading answers,
  measures what accuracy cannot.
- The **golden set** is S16's held-out split, reused.
- An **LLM judge** returns strict JSON (fixed keys, PASS/FAIL), so code can total it.
- Judge biases: **position**, **verbosity**, **self-preference**. Shuffling order guards against the first.
- A **human spot-check** of five tickets is evidence you checked, not proof.

**Interview:** *How do you know a new prompt is better?* Same golden set, same rubric, same judge and same
order-guard for both versions; only the prompt changes.

## S18 · Defensive prompting

**Remember**
- Tags stop accidental confusion, not a deliberate attacker.
- Four attack families: **override**, **authority**, **exfiltrate**, **smuggle**.
- Two-part defence: an **instruction hierarchy** paragraph, and a **scratchpad/final split** your code enforces.
- Attack success is measured on the **visible answer only**.
- Re-check **clean accuracy** — a prompt that refuses everything is not a win.

**Interview:** *Does wrapping input in XML tags solve prompt injection?* No. It stops accidental confusion only.
You need an instruction hierarchy, a sealed scratchpad, output checks, and honest measurement. You can raise the
cost of attack, not reach 100% safety.

**My run:** attacks that succeeded fell from **4/16 (25%)** undefended to **1/16 (6%)** defended, with clean
accuracy still **20/20** for both.

---

## S19 · Chat state & memory windows

**Remember**
- An LLM call is **stateless**. "Remembering" is your code resending the growing `messages` list.
- Consequences: cost grows with length, the context window is a hard ceiling, and something has to give.
- **Sliding window:** flat cost, silently forgets anything outside it.
- **Summarization:** recovers most recall for one extra call per compression — and the summary can be wrong.
- **Retrieval-based memory** (vector database) is the scale answer — Module 4.

**Interview:** *Window vs summarization?* A window is cheap and flat but forgets with no warning; summarization
keeps more at an extra call and a new risk. Measure both with a planted-fact probe.

**My run (planted reference number, recalled at turn 17):** naive 1,747 tokens, recalled ✔ · window 918 tokens,
forgot ✘ · summarize 1,287 tokens, forgot ✘ (the summary dropped the number).

## S20 · Function calling

**Remember**
- **The model never runs anything.** It returns a function name and JSON arguments; your code decides.
- The round trip: tools in → `tool_calls` out → run → append the assistant message and a `tool` message with the
  same `tool_call_id` → call again.
- A tool's **description is a prompt**; its **schema is a request**.
- Small models **over-call** and **invent arguments**.
- Three fixes: **prompt guidance** (free, partial), **validate + feed back** (catches bad arguments, extra round
  trip), **router first** (stops over-calling, extra call, can mis-route).

**Interview:** *Why validate if the schema declares types?* The schema is a request to the model, not enforced by
it — models send strings where numbers belong.

**My run (10 golden questions):** no fix 10/10 answers, 17,270 tokens · Fix A 10/10 but one wrong tool · Fix B
10/10, 17,270 · Fix C 10/10, 18,829 · router+validate 10/10, 18,829. **Ship Fix B on this model:** best accuracy
at the lowest cost.

## S21 · LangChain — your first build

**Remember**
- A **framework** writes the repeated parts; it adds no powers.
- `ChatOpenAI` = the model as an object; `prompt | llm | parser` = a chain; `@tool` = a function as a tool.
- **The docstring is your prompt.** `parse_docstring=True` keeps per-argument descriptions.
- `bind_tools` + `tool_calls` + `tool.invoke(call)` remove S20's schema, `json.loads` and id-matching chores.
- **You still own the loop, its cap, and validation of meaning.** Type hints catch `"abc"`, not `0.085` vs `8.5`.
- Pin versions; give ChatGPT the version card.

**Interview:** *When would you not use LangChain?* A single simple call path, a need for full control and easy
debugging, or no capacity to track version changes.

**My run:** all checker tests pass; real answer ₹21,696 for 25 lakh at 8.5% over 20 years. Parity on S20's golden
set: the first LangChain version scored 7/10 right tool and 8/10 answers because my file had only 2 tools and a
short system prompt, not because of the framework. After adding `check_eligibility` and the fuller fact sheet it
scored **9/10 right tool and 10/10 answers**. The one miss: the model read the 8.5% rate from the system prompt
instead of calling `get_rate`.

---

## S22 · LiteLLM — one call format, many models

**Remember**
- **LiteLLM** gives one `completion()` call for many providers; the **model string** (`groq/openai/gpt-oss-20b`)
  picks the provider.
- A **Router** asks for a group name (`bankassist`) and falls back to another group when the primary fails.
- **Retry** = same model again; **fallback** = a different model; **timeout** = when to stop waiting.
- **Log cost per request** with the model that *really* answered. Local models cost $0 per token.
- LangChain (S21) gave the *parts*; LiteLLM is the *layer under them* — the LLM gateway.

**Honest limits:** another dependency that changes often (pinned `litellm==1.80.0`); a fallback to the same provider
does not survive that provider's outage; a fallback model can pass the call but fail your golden set.

**Interview:** *How do you make an LLM app resilient to provider outages?* Timeouts, one retry for blips, a fallback
to a *different* provider for outages, a polite error when everything fails, and a log of which model answered.

**My run:** with the primary deliberately broken, the router answered with `gpt-oss-120b` after 1 fallback. One call
cost $0.000045 (210 tokens, 0.2 s). The S22 checker passed 9/9.

## S23 · Serving BankAssist — an API with memory and streaming

**Remember**
- An **endpoint** is a function with a decorator. **FastAPI** describes the app; **uvicorn** runs it.
- **Pydantic** request models reject bad input with a **422** before it costs a token.
- The model API is stateless, so the **server** keeps one history per `session_id` and sends a **window** of it.
- **Streaming** shortens the *wait*, not the total time. **SSE** = `event:` + `data:` + a blank line.
- `TestClient` tests an API without running a server.

**Honest limits:** memory in RAM is lost on restart; a client-supplied `session_id` is not security; the window
forgets silently; the API key lives on the server and must never be logged or baked into an image.

**Interview:** *How do you serve an LLM app?* FastAPI behind uvicorn, Pydantic models for input and output, memory
per session, and streaming so users see the first words quickly.

**My run:** all 10 checks passed — `/health`, validation that rejects an empty message, the 4-turn window, memory
kept apart per session, SSE formatting, streaming of tool/token/done events, and the `DELETE /sessions` stretch.

## S24 · Embeddings — searching by meaning

**Remember**
- An **embedding** turns text into a vector so similar meanings sit close together.
- **Cosine similarity** measures how much two vectors point the same way (1 = same, 0 = unrelated).
- **Chunking** (one article → sections) decides what a search can return.
- **Keyword search** misses paraphrases ("parcel arrived smashed" vs "damaged items"); **meaning search** finds them
  but can return something even for off-topic questions.
- Measure with **hit@3** and **MRR** on a fixed question set.

**Interview:** *Why does keyword search miss paraphrases?* No shared words. Embeddings match by meaning.

**My run:** keyword search hit@3 **6/10** (MRR 0.50) against meaning search **10/10** (MRR 0.95). My own three
questions scored 3/3, and the checker passed.

## S25 · Vector databases — a fast index for meaning

**Remember**
- A vector DB stores the vector **plus metadata** (category, date), so you can filter *and* search by meaning.
- Filters use the DB's own language (`$and`, `$gte`); store dates as integers (`20260930`) to compare them.
- **Brute force** compares every vector — fine at 10,000, slow at millions.
- **HNSW** is an approximate index: much faster, at a small **recall** cost you can measure.

**Interview:** *What does an approximate index trade away?* A little recall (it may miss a true neighbour) for a lot
of speed. You measure it with recall@k against brute force.

**My run:** `fast` HNSW recall **0.78** at 0.16 ms; `default` **1.00** at 0.36 ms; `accurate` 1.00 at 1.54 ms.
All my filtered questions returned only rows matching the filter.

## S26 · Production vector stores

**Remember**
- A **library** (Chroma) lives inside your Python; a **server** (Qdrant, PostgreSQL + pgvector) runs on its own and
  many apps can share it.
- **Migration** = read rows, convert to the new store's format, write, then **prove** results match.
- **pgvector** lets you use normal SQL `WHERE` and keeps vectors beside your other data.
- **Multi-tenancy:** always filter by the customer id from the login token, never from user input.
- Choosing a store is a trade-off: ops effort, scale, filtering, cost, data residency.

**Interview:** *How would you pick a vector store?* By the deciding constraint: on-prem + existing PostgreSQL →
pgvector; no ops team → managed (Pinecone); huge scale with heavy filtering → Qdrant.

**My run:** the same top-3 as Chroma on all 5 questions (overlap **1.00**) on Chroma, Qdrant and pgvector. The tenant
filter returned only `CUST-1001` rows (SAFE). Qdrant and pgvector ran in Docker.

## S27 · Hybrid search and reranking

**Remember**
- No single search wins: **keyword (BM25)** is best for exact codes (`SKU-EL-004`), **vectors** for meaning.
- **Hybrid** merges both: **RRF** merges *rankings* (`1 / (k + rank)`); **weighted fusion** merges normalised
  *scores* (`alpha·dense + (1 − alpha)·keyword`).
- A **reranker** (cross-encoder) re-scores the top ~20 together with the question — more accurate but slower, so it
  is the *second stage*.
- A **relevance gate** (lowest score you trust) lets the assistant say "I don't know" for off-topic questions.

**Interview:** *Why do you need both keyword and vector search?* Exact terms vs meaning. Hybrid plus a reranker
beats either alone.

**My run (hit@3 on 25 questions):** keyword 23 · dense 23 · hybrid 24 · weighted 24 · **rerank 25**. Gate **−9.5**
kept 14/14 in-scope questions and blocked 3/3 off-topic ones (lowest in-scope −8.86, highest out-of-scope −10.20).

---

## Where my files are

| Session | File in this repo |
|---|---|
| S14, S15 | `prompts/library.md`, `experiments/s15_accuracy_table.md` |
| S16 | `prompts/support_classifier/system.md`, `user.j2`, `experiments/s16_heldout.md` |
| S17 | `experiments/s17_eval.md` |
| S18 | `experiments/s18_defense.md` |
| S19 | `experiments/s19_chat_memory.md` |
| S20 | `experiments/s20_tools.md`, `s20/stack_router_validate.py` |
| S21 | `s21/bankassist_lc.py`, `s21/parity.py` |
| S22 | `s22/bankassist_llm.py` |
| S23 | `s23/app.py` |
| S24 | `s24/search.py`, `s24/results.md` |
| S25 | `s25/store.py`, `s25/results.md` |
| S26 | `s26/migrate.py`, `s26/results.md` |
| S27 | `s27/hybrid.py`, `s27/results.md` |
