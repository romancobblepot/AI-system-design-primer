# Checkpoint 8: Safety and Isolation

## Purpose

This checkpoint verifies you can distinguish direct from indirect prompt injection and compute a realistic daily exposure rate for it, explain why agent execution needs microVM-level isolation and know where the real hands-on walkthrough lives, state the Gateway-as-choke-point pattern and compute the exposure-window reduction it buys over an embedded credential, define schema-constrained output/content filtering/human-in-the-loop approval gates and compute the retry cost a schema guarantee saves, and compute the blast-radius cost difference between a pooled and a siloed multi-tenant architecture.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1 (F1 — Prompt injection): What's the difference between direct and indirect prompt injection, and why are a RAG system's retrieved chunks and an agent's tool-call results genuinely an attack surface rather than just "data"? Using capstone #9's own figures (20,000 queries/day, top-20 chunks retrieved per query) and an illustrative 0.05% risky-chunk rate, how many queries/day are expected to surface at least one potentially-injectable chunk?</summary>

**Answer:** Direct prompt injection is the end user themselves writing the injected instruction into their own message (e.g., "ignore all previous instructions..."). Indirect prompt injection — named and systematically demonstrated by Greshake et al. (arXiv:2302.12173) — is the injected instruction planted in third-party content the model reads as part of its job: a retrieved document chunk, a web page, a tool's output. The attacker in the indirect case is not the person using the application at all. Both are genuinely an attack surface because a document or tool result is selected for relevance (the best semantic match, or whatever the tool actually returned), never for trustworthiness — nothing in a similarity search or an API response checks whether the content is safe to read as instructions, which is the exact gap Lesson 7's Concept 3 already flagged as having no equivalent of a SQL parameter boundary. The computation: `expected_risky_exposures_per_day = queries_per_day × chunks_per_query × risky_chunk_fraction = 20,000 × 20 × 0.0005 = 200 exposures/day`.

**Why this matters:** The 200/day figure, even at a tiny 0.05% assumed risky-chunk rate, shows this isn't a rare theoretical edge case at real production scale — it's a steady, daily occurrence, which is exactly why the lesson treats this as needing five layered mitigations (delimiting, least privilege, output guardrails, human approval, monitoring) rather than one fix.
</details>

<details>
<summary>Question 2 (F2 — Sandboxing): Why doesn't a plain Docker container provide strong enough isolation for untrusted, LLM-generated agent code, what does a microVM add on top of a container, and where does this lesson send you for the actual hands-on walkthrough rather than teaching it here?</summary>

**Answer:** A plain container still shares the host machine's kernel — the core OS program mediating every system call. For code you chose and trust, that shared-kernel risk is low; for arbitrary code an LLM just generated, it's a materially higher-stakes bet, because a kernel-level exploit or container-escape vulnerability can, in principle, reach the host directly. A microVM gives each sandboxed environment its own, separate kernel instead of a shared one — a stronger isolation boundary, while staying much lighter and faster to start than a full traditional VM. This lesson deliberately does not re-teach `sbx`'s actual commands or microVM mechanics in depth — per F2's own design and the lesson's own Concept 2, the real, verified hands-on walkthrough lives in `learn-docker-ai-agents/lessons/lesson-1-sandboxing-fundamentals.md`, confirmed by this lesson's own `sbx diagnose` / `kern.hv_support` excerpt quoted directly from that file.

**Why this matters:** Linking out instead of duplicating keeps one verified source of truth for the actual commands — re-explaining `sbx` here would risk drifting out of sync with the real tool the moment it changes.
</details>

<details>
<summary>Question 3 (F3 — Credential handling): What is the Gateway-as-choke-point pattern, and in this lesson's own worked example (5 tools with embedded credentials, up to 24 hours per manual rotation, vs. a gateway issuing 15-minute tokens), what's the exposure-window reduction ratio?</summary>

**Answer:** The Gateway-as-choke-point pattern means an agent never holds a tool's real, long-lived credential directly — a single gateway/broker service holds the actual secrets and issues each tool call a short-lived, narrowly-scoped token on demand (e.g., via AWS STS `AssumeRole` with a session `Policy` and a `DurationSeconds`). This matters specifically because the agent's own prompt and reasoning trace are exactly the surface Concept 1 names as exposed to indirect injection — if an injection gets the agent to reveal its configuration, it can only ever reveal a token that expires on its own and was never broadly powerful, not the real underlying secret. The computation: without a gateway, `worst_case_exposure_without_gateway_minutes = 5 tools × 24 hours × 60 = 7,200 minutes`; with a gateway issuing 15-minute tokens, `worst_case_exposure_with_gateway_minutes = 15 minutes`; `exposure_reduction_ratio = 7,200 / 15 = 480x`.

**Why this matters:** This is a different axis from Lesson 7's own 50x blast-radius ratio (how much a leak can reach) — this is how *long* a leak stays dangerous. Both matter, and a gateway choke point is specifically what shrinks the second one, independent of how narrowly any one credential is already scoped.
</details>

<details>
<summary>Question 4 (F4 — Guardrails): What does schema-constrained output actually guarantee (and not guarantee), and using this lesson's own figures (10,000 calls/day, 60% noncompliance without it, 500 input/50 output tokens per call at $3/1M-input, $15/1M-output), what's the extra daily cost of the retries that schema-constrained output eliminates?</summary>

**Answer:** Schema-constrained output (OpenAI's own confirmed figures: 100% conformance for `gpt-4o-2024-08-06` with `strict: true`, vs. under 40% for `gpt-4-0613` without it) guarantees the *shape* of a tool call matches a given JSON Schema — required fields present, correct types, no extra fields if `additionalProperties: false`. It does **not** guarantee the *values* inside that valid shape are safe or correct — a schema-conformant call to `delete_file` with a well-formed path argument is exactly as dangerous as a malformed one, which is why content filtering and human-in-the-loop gates exist as separate, later checks. The computation: `retries_needed_per_day = 10,000 × 0.60 = 6,000`; `cost_per_retry = (500/1,000,000)×$3 + (50/1,000,000)×$15 = $0.0015 + $0.00075 = $0.00225`; `extra_cost_per_day = 6,000 × $0.00225 = $13.50/day` — plus the added latency of 6,000 extra round trips, which the dollar figure alone doesn't capture.

**Why this matters:** This is the concrete version of "shape guarantees aren't safety guarantees" — a team that ships schema-constrained output and stops there has only solved the retry-cost problem, not the guardrail problem; the other layers (content filtering, human-in-the-loop) are what capstone #13's own Step 6 approval-gate design actually relies on for the parts schema validation alone can't catch.
</details>

<details>
<summary>Question 5 (F5 — Multi-tenant isolation): Name the three isolation models AWS's own whitepaper defines, and using this lesson's own worked example (150 tenants sharing one pooled `chunk_embeddings` table vs. one siloed table per tenant, with a missing `tenant_id`-filter bug), what's the blast-radius ratio between the two?</summary>

**Answer:** The silo model gives each tenant its own fully dedicated resources (strongest isolation, highest cost); the pool model has tenants share the same underlying resources with isolation enforced entirely in software (cheapest to run, but every guarantee is only as strong as the enforcement code); the bridge model is a hybrid, siloing some layers and pooling others. The computation: under the pool model, a missing `tenant_id` filter can retrieve chunks from all 150 tenants at once (`pooled_tenants_reachable_by_the_bug = 150`); under the silo model, the identical bug in the identical code can only ever reach the one tenant whose dedicated table that query was sent to (`siloed_tenants_reachable_by_the_bug = 1`); `tenant_blast_radius_ratio = 150 / 1 = 150x`.

**Why this matters:** This resolves a forward reference capstone #9's own Scope note already made by name ("Lesson 8, F5") before this lesson existed — and the 150x figure is the same shape of conclusion as Lesson 7's 50x credential-leak ratio and capstone #13's own 20x sandbox-co-location ratio, just computed one layer further down the stack, at the shared data/retrieval layer instead of a credential or a sandbox.
</details>

## Hands-On Self-Check

There's no single CLI spanning this whole lesson — confirm you can do each of the following, without looking back at it:

- [ ] I can state, from memory, the difference between direct and indirect prompt injection, and name at least three of the five mitigation layers this lesson lists (delimiting/labeling, least-privilege execution, output-side guardrails, human-in-the-loop approval, monitoring/detection).
- [ ] I can explain why a plain container's shared kernel is a materially different risk for LLM-generated code than for code I chose myself, and I can run `sbx diagnose` (or state what its `kern.hv_support` line confirms) without needing to look it up.
- [ ] I can state the Gateway-as-choke-point pattern in my own words and compute `exposure_reduction_ratio` given any `num_tools`, `hours_per_manual_rotation`, and `gateway_token_minutes` combination of my own choosing.
- [ ] I can explain what schema-constrained output does and does not guarantee, and compute `guardrail_retry_cost_per_day` given a fresh set of call-volume, noncompliance-rate, and token/pricing assumptions.
- [ ] I can name all three AWS tenant-isolation models (silo/pool/bridge) and compute `tenant_blast_radius_ratio` given any pooled-tenants-reachable / siloed-tenants-reachable pair.
- [ ] I can run (or reason through line by line) this lesson's Python snippet and confirm `process_agent_action` rejects a tool call that's missing a required field, and that the four numeric functions reproduce 200.0, 480.0, 13.5, and 150.0 respectively.
- [ ] I can name which already-written capstone (#9, #13, or #15) each of this lesson's five Concepts connects to, including which two Concepts (F4, F5) resolve a forward reference that capstone already made to "Lesson 8" by name.

## Next Step

Move to **Lesson 9: Evaluation and Observability**.
