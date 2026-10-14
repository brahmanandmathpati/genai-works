# GenAI & AI Agents — Hands-On Engineering Portfolio

I built this repository myself, from the ground up, to learn how to engineer real applications on top of large language models. It is not a collection of copy-pasted snippets. Every folder contains working code, measured experiments, automated tests and written findings.

## What this repo shows about me

- **I measure before I trust.** Token counts are checked against provider billing, models are compared on cost, latency and quality, and classifiers are scored on held-out data.
- **I write testable LLM code.** The logic around the model is plain Python with offline tests, so it can be checked without an API key.
- **I know where a model should and should not be in control.** The model reads messy text. Code owns decisions, safety rules and sequencing.
- **I work across providers.** Groq, Gemini and local Ollama models all run behind one codebase.
- **I think about cost and failure.** Rate limits, daily token budgets, retries, caching and cost per 1,000 requests are built in, not bolted on.

---

## At a glance

| Area | What I built | Where |
|---|---|---|
| LLM fundamentals | Token counting, billing reconciliation, cost in INR, embeddings plotted with PCA | [module01/s09_tokens.ipynb](module01/s09_tokens.ipynb) |
| Model selection | Eliminate, score, verify framework over a model catalog | [module01/s10_model_matrix.ipynb](module01/s10_model_matrix.ipynb) |
| Multi-provider code | One `ask()` function across Groq, Gemini and Ollama, plus a temperature study | [module01/s11_providers.ipynb](module01/s11_providers.ipynb) |
| Local models | Memory-fit calculator, tool-calling probe, speed comparison | [module01/s12_local_models.ipynb](module01/s12_local_models.ipynb) |
| Vision + structured output | Scanned documents to validated KYC records, with retry and human fallback | [module01/s13_vision_structured.ipynb](module01/s13_vision_structured.ipynb) |
| Prompt engineering | Five-part prompt spec, acceptance checks, versioned prompt library | [module02/s14_prompt_anatomy.ipynb](module02/s14_prompt_anatomy.ipynb) |
| Reasoning | Four reasoning strategies benchmarked on accuracy, tokens, time and cost | [module02/s15_reasoning.ipynb](module02/s15_reasoning.ipynb) |
| Production prompting | Delimiters, tag escaping, Jinja templates, prompt files, held-out evaluation | [module02/s16_structured.ipynb](module02/s16_structured.ipynb) |
| End-to-end projects | Insurance claims pipeline and healthcare booking assistant | [showcase/](showcase/) |

---

## Projects

### 1. Insurance claims pipeline — [showcase/a2_insurance/](showcase/a2_insurance/)

A customer types a claim in plain, messy English. The system turns it into a structured form and routes it.

```text
free-text claim -> model extracts JSON form -> code routes by severity -> templated reply
```

- The model has exactly one job: read the text and fill a fixed JSON schema.
- Routing is a plain Python function that receives only the parsed form, never the model client. It cannot call the model even by accident.
- Eight mock claims cover minor, major, injury and no-injury cases, plus one ambiguous and one suspicious claim.
- Tests: offline tests for the schema and router, plus live tests that skip automatically when no API key is set.

### 2. Healthcare appointment assistant — [showcase/a3_healthcare/](showcase/a3_healthcare/)

A patient messages a clinic to book an appointment.

```text
safety rule -> intent router -> slot filling -> booking -> confirmation
   (code)       (model reads)   (model reads,     (code)     (template)
                                 code decides
                                 what to ask next)
```

- An emergency rule runs before any model call. For an emergency message, no model call happens at all.
- The model only classifies intent and extracts details. The question order, availability lookup and confirmation text are all code.
- The assistant cannot invent an appointment slot, because availability is a data table, not generated language.
- Seven scripted patient conversations, 15 offline tests using a keyword stand-in for the model, and one live test.
- Mock data only. This demonstrates a code-owned safety check; it is not a medical tool.

---

# Module 1 — LLM foundations

Before writing any prompt, I wanted to understand the machine: what a model actually receives, what it costs, which one to pick, where it can run, and how to get reliable data out of it.

## Session 9b — Tokens, cost, context and embeddings

**Question I set out to answer:** what does a model actually see, and what does it cost?

**What I built** ([tokens_utils.py](module01/tokens_utils.py))
- `count_tokens` and `show_tokens` using `tiktoken` with the `o200k_harmony` encoding, so I can see exactly how text is split.
- `usage_for` to send a real request and read the token usage the provider reports back.
- `cost_inr` to turn token counts into rupees using price cards (at an exchange rate of Rs 84 per USD), scaled by number of calls.
- `embed_via_ollama` using the `nomic-embed-text` model, and `pca_2d` to squash embeddings into a 2-D plot.
- Ten words (loan, EMI, interest, credit score, bank, hospital, doctor, prescription, cricket, monsoon) embedded and plotted. Banking words cluster apart from healthcare and weather/sport words, which shows what "meaning as geometry" looks like. The embeddings are cached in a JSON file so the notebook still works when Ollama is not running.

**Findings**

`tiktoken` counts only the text I write, but the provider's `usage` figure is higher because chat-template wrapper tokens are added behind the scenes. For Groq `openai/gpt-oss-20b` that wrapper is a fixed **71 tokens per request**. Subtract it and the counts match `tiktoken` exactly. Token counts also differ across tokenizers: the same Telugu sentence cost about 4x more tokens on an Ollama model than under `o200k_harmony`.

| Text | tiktoken | Groq usage | Groq minus wrapper | Ollama usage |
|---|---|---|---|---|
| English | 16 | 87 | 16 | 41 |
| Telugu | 25 | 96 | 25 | 132 |
| Python | 35 | 106 | 35 | 61 |
| JSON | 25 | 96 | 25 | 49 |

**Why it matters:** if you estimate cost from word counts or from one tokenizer, you will be wrong, especially for non-English text. Budgets have to be built on measured usage.

## Session 10 — Choosing a model without guessing

**Question:** how do you pick a model for a business case without relying on hype?

**The method I implemented** ([landscape_utils.py](module01/landscape_utils.py))
1. **Eliminate.** `eligible()` removes any model that fails a hard constraint for the scenario: data residency, latency, context window or call volume. It also returns the reasons, so a rejection can be explained.
2. **Score.** `rank()` normalises cost, latency and quality to a common scale and applies the weights that suit each business scenario.
3. **Verify.** The winner is tested on real prompts before anyone trusts it.

**Supporting pieces**
- `monthly_cost_usd` / `monthly_cost_inr` project a monthly bill from calls per day and tokens per call (30-day month).
- `time_stream` measures real response timing on the same prompt across models.
- [models_catalog.json](module01/models_catalog.json) holds the catalog. Prices are indicative (Sep 2026). Quality and latency start as estimates which I overwrite with my own measurements.

**The test case:** salary Rs 60,000/month, existing EMIs Rs 8,000/month, loan Rs 8,00,000 at 11.5% over 60 months. The code computes the right answer independently: EMI **Rs 17,594.09** and ratio **42.7%**, under the 50% cutoff. `check_answer()` extracts the numbers from a model's reply and accepts it only if the EMI is within 1% and the ratio within 0.6 points. A 1–5 `RUBRIC` handles the parts a machine cannot grade, such as clarity.

**Why it matters:** the "best" model changes with the scenario. A cheap fast model can win for high-volume work, and a data-residency rule can rule out a hosted model entirely.

## Session 11 — Providers, sampling and temperature

**Question:** can one codebase work with any provider, and what does temperature really change?

**What I built** ([providers_utils.py](module01/providers_utils.py), [tickets_data.py](module01/tickets_data.py))
- Client factories for Groq, Gemini and Ollama, all through the OpenAI-compatible interface.
- A single `ask(client, model, system, user, temperature=...)` function used for every provider.
- Gemini model auto-discovery: `list_gemini_models` and `pick_gemini_model` filter out image, audio, embedding and other non-chat models and pick a usable chat model, so a retired model name does not break the notebook.
- `classify_ticket`, a support-ticket classifier returning structured output.
- A ticket set split into clear tickets and deliberately borderline tickets, to test temperature fairly.

**Findings**
- If the code differs between providers only in `BASE_URL`, `API_KEY` and `MODEL`, it is provider-agnostic. Switching provider is a config change, not a rewrite.
- Temperature only matters near a decision boundary. Clear tickets gave the same answer at every temperature I tried. Borderline tickets are where answers started to vary.

**Why it matters:** this is the habit that avoids vendor lock-in, and it shows that "set temperature to 0 for everything" and "turn it up for creativity" are both oversimplifications.

## Session 12 — Local models

**Question:** what can I run on my own machine, and when does that make sense?

**What I built** ([local_models_utils.py](module01/local_models_utils.py), [local_models_catalog.json](module01/local_models_catalog.json))
- A catalog of six local models from 1B to 120B parameters (llama3.2:1b and 3b, qwen2.5:7b, llama3.1:8b, gpt-oss:20b and 120b), each tagged with precision and tool-calling support.
- `model_size_gb`: memory estimated from parameters x bytes per parameter. The pre-read example: a 20B model needs roughly 40 GB at 16-bit but about 10 GB at 4-bit.
- `fits_on` and `laptop_options`: given a RAM size, list which models fit, keeping 2 GB of headroom for the system.
- `probe_tool_calling`: sends a test request with a tool definition and checks whether the model actually emits a structured tool call or only describes one in prose.
- `speed_table`: compares response speed across the models I tried.

**Findings**
- Quantization (storing weights in fewer bits) is what makes a 20B model laptop-sized, at a small accuracy cost.
- Not every small model can call tools. A model can write a fluent sentence about calling a function without ever producing the structured call. That decides whether it can power an agent.
- Why a bank might accept a slower local model: data never leaves the building.

## Session 13 — Vision and structured output

**Question:** how do I turn a photo of a document into data a downstream system can trust?

**What I built** ([vision_utils.py](module01/vision_utils.py), [make_sample_docs.py](module01/make_sample_docs.py))
- A script that generates three sample documents as images: an ID card, a utility bill and a deliberately noisy scan. Each has a ground-truth text file to compare against.
- `encode_image` and `vision_messages` to send an image as base64 inside a chat message.
- `find_vision_model` to pick an available vision-capable model from a preference list.
- `read_image_text` and `compare_to_truth` to transcribe an image and check, field by field, what the model got right.
- A **two-stage pipeline**: a vision model reads the picture into text, then a text model turns that text into a record. Each stage can use the cheapest model that is good enough.
- A `KycRecord` Pydantic model carrying business rules, for example the PAN number must match `^[A-Z]{5}[0-9]{4}[A-Z]$`.

**Three levels of getting JSON, implemented and compared**

| Level | Function | What is guaranteed |
|---|---|---|
| 1. Prompt only | `level1_prompt_only` | Nothing. The model usually complies, sometimes adds prose or markdown fences. |
| 2. JSON mode | `level2_json_mode` | Valid JSON, but of any shape. |
| 3. Schema-enforced | `level3_schema` | The exact shape, on models with strict mode such as `gpt-oss-20b`. |

`success_rate` runs each level repeatedly so I compare them on numbers rather than one lucky run.

**The key lesson, in code:** shape is not truth. Even a schema-enforced reply can contain a PAN with the wrong pattern or a misread digit. So `parse_and_validate` checks the business rules, and `extract_validated` **retries once** by feeding the exact validation error back to the model. If it still fails, the record goes to a human. Deciding where automation stops is a design decision, not a bug.

---

# Module 2 — Prompt engineering

Module 1 was about the model. Module 2 is about what I say to it, and how to treat prompts as engineered, tested, versioned assets.

## Session 14 — Prompt anatomy

**Question:** what makes one prompt reliably better than another?

**What I built** ([prompt_utils.py](module02/prompt_utils.py), [prompt_tasks.py](module02/prompt_tasks.py))
- `PromptSpec`: a prompt broken into five parts (role, task, context, constraints, output format), with `missing_parts` and `show_tips` that flag what a draft is missing.
- **Acceptance checks**, small functions that test an output: `max_words`, `max_chars`, `has`, `has_none_of`, `bullet_lines`, `matches`, `json_only`, `json_keys`, `json_value`. A `Task` bundles a prompt with its checks, and `run_task` reports pass/fail per check. I write the checks first, then improve the prompt until they pass.
- Three realistic tasks, including one grounded in a lending policy, so the model has to follow rules it can only learn from the prompt.
- A **prompt library**: `save_to_library` records each prompt version, the output it produced and the checks it passed, in a file kept under Git. Old versions are never edited; a new version is added beside them.
- A support-complaint classifier with 0, 1 or several examples (`classify_spec(n_examples)`), scored on a separate test set to show how few-shot examples teach house conventions such as "UPI problems are `account`".
- Repo tooling: `init_work_repo` and `check_work_repo` set up and validate my own Git repository, with a `.gitignore` that blocks secrets.

**Findings**
- A model cannot follow a policy it was never shown. Context has to be in the prompt.
- Examples are the best way to teach rules that are obvious inside an organisation and invisible to a model, but they cost tokens on every call.
- "Better" needs a number. Acceptance checks turn opinion into a test.

## Session 15 — Reasoning

**Question:** does asking a model to think help, and is it worth the cost?

**What I built** ([reasoning_utils.py](module02/reasoning_utils.py), [reasoning_tasks.py](module02/reasoning_tasks.py))

Four strategies, each a function run on the same problems:

| Strategy | Function | How it works | Cost |
|---|---|---|---|
| Plain | `solve_plain` | Reply with only the final answer. | 1 call |
| Chain of thought | `solve_cot` | Think step by step, then answer. | 1 longer call |
| Step back | `solve_stepback` | First list the rules and formulas without solving, then solve with them. | 2 calls |
| Self-consistency | `solve_self_consistency` | Ask 5 times at temperature 0.8 and take the majority vote. | 5 calls |

**The benchmark.** A loan-eligibility policy and ten applicants, each hiding a different trap: a value exactly on a limit, a loan term given in months, a rule that fails quietly. The correct answer for every case is computed independently in Python as ground truth, never taken from a model. Extra problems cover retail totals, insurance payouts, Bayes and dosage.

**What gets measured per strategy:** right or wrong, tokens used, seconds taken, and the number finance asks for, cost per 1,000 questions (`comparison_table`, `strategy_summary`, `case_table`, `accuracy_markdown`). At 200,000 questions a month, a strategy that costs five times as much is not a detail.

**Engineering around real API limits**
- `DiskCache` remembers every answer on disk, so re-running a cell costs nothing.
- `Meter` tracks tokens spent against the free-plan limits (8,000 tokens per minute, 200,000 per day).
- `rate_limit_wait` waits out a per-minute 429 politely, and `DailyLimit` stops cleanly when the daily limit is hit, with saved answers intact.
- `cost_usd` prices each run from the model's per-million-token rates.

**Hidden reasoning without leaking it.** Prompts ask for working inside `<scratchpad>` tags and the real reply inside `<final>` tags. `split_scratchpad` removes the scratchpad, acceptance checks run on `<final>` only, and `scratch_leaks` checks whether the working repeated something that must never be revealed, such as an internal score or cutoff.

**Prompt v2.** `run_spec`, `pass_rate` and `verdict` compare version 1 and version 2 of a prompt over repeated runs, so each improvement is justified with numbers and added to the library as v2, without editing v1.

**Findings**
- Some models already think before answering (hidden reasoning tokens are billed as output), so "think step by step" may add little, while a small local model can change a lot. This is measured, not assumed.
- Thinking cannot recover a rule the model was never told, and five votes on a wrong rule can never reach the right answer.
- Do not pay for a vote on arithmetic a calculator can do.

## Session 16 — Structured, production-grade prompting

**Question:** how do I build a prompt that is safe to reuse, easy to review and properly tested?

**What I built** ([structured_utils.py](module02/structured_utils.py), [structured_tasks.py](module02/structured_tasks.py))

*1. Keeping instructions and data apart*
- Four ways of presenting a customer ticket, compared in code: plain text, XML-style tags, a Markdown fence and JSON (`STYLES`), with `prompt_size` to compare their token cost.
- `escape_tags` neutralises my own tag names (`ticket`, `example`, `label`) inside customer text, so a customer cannot type a closing tag and break out. This removes accidental confusion; I treat it as the first layer of defence, not a complete answer to prompt injection.
- A set of **trap tickets** that quote the bank's own words, such as "reply with the word account", to show why tagged data survives them.

*2. Templates*
- Prompts are built from **Jinja** templates with loops for few-shot examples and a conditional that shows the examples block only when examples exist.
- **Strict undefined**: a missing variable is a loud error, never a silent blank. `render_check` verifies the template renders for five sample tickets.

*3. The system prompt as a versioned file*
- `load_prompt_file` reads `prompts/support_classifier/system.md` and `user.j2`, parses the `---` front matter holding name and version, and raises a clear `PromptFileError` if a file is missing or empty. Prompts live in Git with a reviewable history.

*4. Honest evaluation*
- A labelled set split into a **training pool** and a **held-out set** of 20 tickets that never appear in a prompt.
- `pick_examples` draws a fixed number of examples per label (reproducible by seed) from the training pool only, and `check_no_leak` raises `LeakError` if a held-out ticket sneaks into a prompt. That is the leakage that inflates scores by "marking your own homework".
- The structured prompt is measured against a one-line baseline on the held-out tickets. Results go into a **confusion table** and a mistakes table that show where errors go, and a Markdown report records the model and the SHA of the prompt files used (`heldout_markdown`, `save_heldout_report`). The target I worked to was 16 of 20.
- The classifier handles four labels (card, loan, account, other) and the bank's house rules, for example a change of personal details is `other` even if it mentions a card.

**Findings**
- Moving from a typed prompt to a prompt a team can ship takes three habits: separate data from instructions, build from a template that fails loudly, and keep prompts as versioned files.
- An accuracy number only means something if the test items never appeared in the prompt.

---

## Engineering practices

- **Tests for every session** in [tests/](tests/), from `test_setup.py` through `test_s16.py`. Offline tests need no key; live-API tests are kept separate.
- **Submission checkers** ([module02/check_submissions.py](module02/check_submissions.py) and the Session 15 and 16 versions) that fetch a GitHub repo and verify the expected files are present.
- **Reproducible environment**: dependencies pinned with `uv`, Python 3.12 pinned in `.python-version`.
- **Secrets handled properly**: `.env` is git-ignored and `.env.example` documents what is needed.
- **Written explanations**: every session has a glossary of the terms I learned and a pre-read with my own answers.
- **Python patterns for agents**: a one-page cheatsheet covering errors as data, registry + kwargs dispatch, decorators, typed state, Pydantic validation and JSON handling ([cheatsheet/python-for-agents.md](cheatsheet/python-for-agents.md)).

## Tech stack

Python 3.12 · uv · Jupyter · tiktoken · Pydantic · Jinja2 · pytest · NumPy (PCA) · Pillow · Groq API · Google Gemini API · Ollama (local models)

---

## Run it yourself

```powershell
uv sync                      # install pinned dependencies
copy .env.example .env       # paste your Groq key as API_KEY
uv run python hello.py       # first LLM call, prints token count
uv run pytest                # run all checkpoints
```

To use local models instead, comment out the Groq lines in `.env`, uncomment the Ollama lines, then run `ollama pull llama3.2:3b` and `ollama pull nomic-embed-text`.

Open any notebook with, for example, `uv run jupyter lab module01/s09_tokens.ipynb`. Tests that call a live API depend on provider uptime and may fail on a bad day.

**Troubleshooting:** `uv` not recognized — reopen all terminals. 401 error — check `.env`, not `.env.example`. Ollama connection refused — run `ollama serve`. 404 model not found — run `uv run python list_models.py`. 503 from Gemini — wait a minute and retry.

## Repository layout

```text
module01/      Sessions 9b–13: LLM foundations
module02/      Sessions 14–16: prompt engineering
showcase/      a2_insurance, a3_healthcare
tests/         checkpoints per session
cheatsheet/    python-for-agents.md
hello.py       first LLM call
list_models.py models your key can use
```
