# Terms from Session 18 — what they are, and where they come back

| Term | What it is | Say it as | Comes back at |
|---|---|---|---|
| Prompt injection | Text inside the data a model reads, written to be followed as an instruction instead. | A fake memo slipped into your inbox. | S19; Module 12 Security |
| Direct injection | The attacker writes the malicious message themselves, in a field you know is attacker-controlled. | A stranger hands you a fake memo. | S18 attack set; Module 12 |
| Indirect injection | The attack is hidden inside a document or page a trusted user asked the model to read. | A bomb hidden inside a book your boss asked you to read aloud. | M5 RAG; Module 12 |
| Instruction hierarchy | A stated rule that only the system prompt counts as an instruction - nothing in the data overrides it, however it is phrased. | Only the signed contract changes the terms. | S19; Module 12 |
| Scratchpad / final split | The model's reasoning goes in one tag; only the other tag is read, shown or checked - the code does the discarding. | A sealed envelope: only the signed letter ships. | S34 the ReAct loop |
| Attack success | The visible answer is wrong or leaks something - never counted just because the model "noticed" an attempt. | Grade the exam, not the margin notes. | S52 evaluations; Module 12 |
| Leak marker | A known phrase from your own system prompt that should never appear in a normal reply. | A watermark on a photocopy. | Module 12 |
| Defense-in-depth | Several independent layers (hardened prompt, sealed scratchpad, output-side check) so one failing layer doesn't fail the whole system. | A vault with a lock, a guard, and a camera. | Module 12; S54 LLMOps |
| Obfuscation attack | Hiding an instruction from a keyword filter — scrambled letters, Base64/hex, invisible Unicode — while the model still reads it correctly. | A note written in code your teacher can't read but your friend can. | C6 assignment; Module 12 |
| Typoglycemia | The real phenomenon where both humans and models read a word correctly even with its middle letters scrambled, as long as the first and last letters stay put. | "Cna yuo sltil raed tihs?" — yes, and so can the model. | C6 assignment |
| Best-of-N (BoN) jailbreaking | Generating many small variations of one attack (capitals, spacing, rewording) and trying them until one gets through. A 2024 study reported 89% success on GPT-4o and 78% on Claude 3.5 Sonnet with up to 10,000 variations per request, for those tested setups. | Keep rattling every key on the ring until one turns. | C2 honest limits; S23 rate limits; Module 12 |

## Further reading: OWASP LLM Prompt Injection Prevention Cheat Sheet
Source for the Best-of-N statistic and the typoglycemia example in C2/C6 of the notebook:
<https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html>. Today covers
one slice of a much larger field — here is the full map, and where each piece not built today comes back.

**Attack types**

| Covered today | Comes back later |
|---|---|
| [Direct Prompt Injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#direct-prompt-injection) — all 4 families | [Remote/Indirect Prompt Injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#remoteindirect-prompt-injection) — Module 5, Module 12 |
| [System Prompt Extraction](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#system-prompt-extraction) — the exfiltrate family | [RAG Poisoning (Retrieval Attacks)](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#rag-poisoning-retrieval-attacks) — Module 5 |
| [Data Exfiltration](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#data-exfiltration) — leak markers | [Multi-Turn and Persistent Attacks](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#multi-turn-and-persistent-attacks) — S19 |
| [Encoding and Obfuscation Techniques](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#encoding-and-obfuscation-techniques), [Typoglycemia-Based Attacks](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#typoglycemia-based-attacks) — C6 | [Agent-Specific Attacks](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#agent-specific-attacks) — Module 6, Module 8 |
| [Best-of-N (BoN) Jailbreaking](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#best-of-n-bon-jailbreaking), [Jailbreaking Techniques](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#jailbreaking-techniques) — named, cited | [HTML and Markdown Injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#html-and-markdown-injection), [Multimodal Injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#multimodal-injection) — S23 rendering (HTML/Markdown), Module 5 multimodal RAG, Module 12 |

**Defenses**

| Covered today | Comes back later |
|---|---|
| [Structured Prompts with Clear Separation](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#structured-prompts-with-clear-separation) — the instruction hierarchy | [Human-in-the-Loop (HITL) Controls](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#human-in-the-loop-hitl-controls) — Module 6, Module 12 |
| [Output Monitoring and Validation](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#output-monitoring-and-validation) — scratchpad/final, leak markers | [Best-of-N Attack Mitigation](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#best-of-n-attack-mitigation) — S23 rate limits, Module 12 |
| [Input Validation and Sanitization](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#input-validation-and-sanitization) — partially (Session 16's tags) | [Remote Content Sanitization](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#remote-content-sanitization) — Module 5, Module 12 |
| [Least Privilege](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#least-privilege) — named (C2) | [Agent-Specific Defenses](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#agent-specific-defenses) — Module 6, Module 12 |
| | [Comprehensive Monitoring](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#comprehensive-monitoring), [Model-Based Guardrails](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html#model-based-guardrails) — S54 LLMOps (monitoring), Module 12 |
