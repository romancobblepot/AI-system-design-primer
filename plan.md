# Plan: `ai-system-design-primer`

A system design repo for **AI engineering, AI applications, and agentic applications** — the topic depth and breadth of [`system-design-primer`](https://github.com/donnemartin/system-design-primer), delivered in the lesson/checkpoint teaching format of `learn-docker-ai-agents`.

This file is the blueprint. Nothing below is written yet — this is what gets built, in what shape, and in what order.

---

## 1. What's being merged, and why neither source works alone

**`system-design-primer` gives us:** an exhaustive, cross-referenced index of system design topics (consistency, availability, caching, databases, queues, communication protocols...), each explained with trade-offs rather than a single "right answer," plus a `solutions/` folder of fully worked interview questions (Pastebin, Twitter, a web crawler...) that each follow the same four-step method: outline use cases/constraints → high-level design → core components → scale the design, with real back-of-the-envelope math, table schemas, REST payloads, and Python sketches.

**What it's missing for our purpose:** it's a *reference you read*, not a *course you do*. There's no learning-objectives framing, no "run this yourself" verification loop, and nothing AI/agent-specific — no LLM serving, no RAG, no tool-calling, no agent memory, no prompt injection.

**`learn-docker-ai-agents` gives us:** a teaching *shape* — a README syllabus, numbered `lessons/` files that break each tool into Concept blocks with a strict **Why? / What? / How?** structure, a Hands-On Walkthrough of real verified commands, a Summary table, and a Command Reference; paired `checkpoints/` files with collapsible self-check Q&A (each answer followed by a "Why this matters" line) and a hands-on checklist before unlocking the next lesson.

**What it's missing for our purpose:** it only covers four Docker-specific tools end to end (`sbx`, `docker model`, `docker mcp`, `docker agent`) — it has no mechanism for covering a *broad topic index* the way `system-design-primer` does, and no equivalent of the worked interview-question solutions.

**The merge:** use `system-design-primer`'s topic index and worked-solution *content* as the raw material, and pour it through `learn-docker-ai-agents`'s Why/What/How lesson structure and checkpoint-gated pacing. The worked interview questions become a `solutions/` folder that keeps `system-design-primer`'s four-step method but is reframed for AI/agentic systems (e.g. "Design a RAG customer-support chatbot" instead of "Design Pastebin").

**Revised assumption — this repo now teaches core system design directly, not just links to it.** The first pass treated `system-design-primer` as an external prerequisite and scoped this repo to AI-native topics only. That got inverted after further review: most people building AI applications have already internalized the AI-native material (RAG, agent loops, embeddings, model serving) well enough — what's actually thin is the classic distributed-systems material those applications still run on top of (load balancing, caching, replication, sharding, queues, CAP trade-offs). So Lessons 3–7 (§3) now *teach that core material directly*, curated down to what an AI engineer specifically needs and immediately overlaid onto the real case studies in §6.2 — a curated, case-study-anchored subset of `system-design-primer`'s index, not a copy of it. `system-design-primer` remains the reference for going deeper than that curated subset (its own exhaustive company-architecture list, SQL-tuning internals, full OSI-layer detail) — see §6.3's Step 0 for exactly where that line is drawn. The old AI-native Groups A–E get compressed into one refresher lesson instead of six full ones (§3, §4); Lessons 8–10 are untouched by this revision.

---

## 2. Repo structure

```
ai-system-design-primer/
├── README.md                          # syllabus — mirrors learn-docker-ai-agents' README
├── lessons/
│   ├── lesson-1-ai-fundamentals-refresher.md      # compressed — old Groups A–E
│   ├── lesson-2-core-system-design-fundamentals.md # compressed — Group P (added in a later revision)
│   ├── lesson-3-scalability-and-availability.md   # new — Group I
│   ├── lesson-4-network-and-delivery.md           # new — Group J
│   ├── lesson-5-data-layer.md                     # new — Group K
│   ├── lesson-6-async-and-communication.md        # new — Group L
│   ├── lesson-7-application-architecture-and-security.md  # new — Group M
│   ├── lesson-8-safety-and-isolation.md           # unchanged — Group F
│   ├── lesson-9-evaluation-and-observability.md   # unchanged — Group G
│   ├── lesson-10-production-scaling.md             # unchanged — Group H
│   └── lesson-11-real-world-architectures.md      # promoted from appendix — Group N
├── checkpoints/
│   ├── checkpoint-1-ai-fundamentals.md
│   ├── checkpoint-2-core-system-design-fundamentals.md
│   ├── checkpoint-3-scalability-and-availability.md
│   ├── ...                            # checkpoint-N pairs 1:1 with lesson-N
│   └── checkpoint-11-real-world-architectures.md  # open-ended self-check, not fixed Q&A — see §5 exception
├── solutions/                         # mirrors system-design-primer's solutions/system_design/
│   ├── rag-contextual-retrieval/README.md
│   ├── autonomous-coding-agent/README.md
│   └── ...                            # one per §6.2 catalog entry
└── appendix/                          # now genuinely reference-only — see §3
    ├── token-and-latency-numbers.md    # AI-world equivalent of "latency numbers every programmer should know"
    └── glossary.md
```

Four top-level pieces, same division of labor as the two source repos:
- **`lessons/`** = teach one topic area deeply, Why/What/How, hands-on where a real tool exists.
- **`checkpoints/`** = gate progression; force active recall before the next lesson.
- **`solutions/`** = `system-design-primer`'s interview-question method, applied to AI/agentic system prompts, as the capstone-style synthesis exercises.
- **`appendix/`** = the reference material that doesn't belong inside a single lesson (numbers to memorize, further reading, glossary).

---

## 3. Topic taxonomy — the "index of topics" equivalent

**Revised after review.** The first draft gave AI-native material (RAG, agent loops, model serving, memory) the full lesson-by-lesson treatment and scoped classic distributed-systems fundamentals out entirely, on the assumption `system-design-primer` already covers the latter. That's backwards for the actual reader: someone already working as an AI engineer has usually internalized embeddings/RAG/agent-loop basics well enough already — what's actually thin, for most people building AI applications, is the classic system-design material those applications still run on top of (load balancing, caching, replication, sharding, queues, CAP trade-offs). **So the real material in this repo is now Lessons 3–7: core system design, taught directly, with every Concept immediately overlaid onto the real case studies in §6.2** — not a copy of `system-design-primer`'s index, but a curated subset of it, picked and framed for what an AI engineer specifically needs. The old AI-native Groups A–E get compressed into a single refresher lesson instead of six full ones; Lessons 8–10 (safety, evaluation, production scaling) are untouched by this revision.

**Lesson granularity rule:** `learn-docker-ai-agents` runs 3–5 Concepts per lesson. Lessons 3–10 keep following that; Lessons 1 and 2 are the two deliberate exceptions (see §4). **11 lessons total:**

**Revised again, after this repo's content was fully built out: a second compressed refresher was added as Lesson 2.** Lessons 3–7 (the core-system-design material) assume a reader already knows basic distributed-systems vocabulary — client/server, request/response, API, database, cache, latency/throughput at a glance — before diving into *why* a database gets sharded or *how* a cache-aside pattern works. That assumption doesn't hold for every reader this repo targets: someone coming from a pure ML/research background may know embeddings and training loops cold but have never needed to reason about a request/response cycle or what a cache actually is. Rather than have Lessons 3–7 stop and re-explain these basics inline (which would duplicate the same explanation across multiple Concepts), Lesson 2 compresses them into one refresher — the same move Lesson 1 already makes for AI-native vocabulary, just one layer further down the stack. Every lesson from 3 onward was renumbered up by one to make room for it; file names, cross-references, and the table below all reflect the final, 11-lesson state.

| # | Lesson file | Checkpoint file | Covers | Depth |
|---|---|---|---|---|
| 1 | `lesson-1-ai-fundamentals-refresher.md` | `checkpoint-1-ai-fundamentals.md` | Old Groups A–E (21 sub-topics: AI app foundations, model serving, retrieval/RAG, agent architecture, agent memory) | **Compressed** — refresher, not first-time teaching |
| 2 | `lesson-2-core-system-design-fundamentals.md` | `checkpoint-2-core-system-design-fundamentals.md` | New Group P — core system-design vocabulary primer (client/server, request/response, API, database, cache, latency/throughput, scaling at a glance) | **Compressed** — refresher, not first-time teaching |
| 3 | `lesson-3-scalability-and-availability.md` | `checkpoint-3-scalability-and-availability.md` | New Group I — performance/scalability, CAP theorem, consistency & availability patterns | Full |
| 4 | `lesson-4-network-and-delivery.md` | `checkpoint-4-network-and-delivery.md` | New Group J — DNS, CDN, load balancers, reverse proxies | Full |
| 5 | `lesson-5-data-layer.md` | `checkpoint-5-data-layer.md` | New Group K — RDBMS scaling, NoSQL types, caching strategies | Full |
| 6 | `lesson-6-async-and-communication.md` | `checkpoint-6-async-and-communication.md` | New Group L — message/task queues, back pressure, TCP/UDP, RPC/REST | Full |
| 7 | `lesson-7-application-architecture-and-security.md` | `checkpoint-7-application-architecture-and-security.md` | New Group M — microservices/service discovery, core security, back-of-envelope estimation | Full |
| 8 | `lesson-8-safety-and-isolation.md` | `checkpoint-8-safety.md` | Group F — unchanged | Full |
| 9 | `lesson-9-evaluation-and-observability.md` | `checkpoint-9-evaluation.md` | Group G — unchanged | Full |
| 10 | `lesson-10-production-scaling.md` | `checkpoint-10-scaling.md` | Group H — unchanged | Full |
| 11 | `lesson-11-real-world-architectures.md` | `checkpoint-11-real-world-architectures.md` | New Group N — AI infra building blocks, Company AI architectures, Company engineering blogs (promoted from the appendix — see below) | **Survey** — same lighter treatment as Lesson 1, see §4/§5 exceptions |

**Lesson 11 was promoted out of the appendix after review:** this content (the AI-world analogs of `system-design-primer`'s "Real world architectures" and "Company architectures" tables) is genuinely educational, not pure lookup reference like a glossary or a latency-numbers table — so it belongs in the syllabus's numbered sequence, visible and checkpoint-gated like everything else, not tucked into a folder most readers won't think to open. What's left in `appendix/` after this move is only true flip-back-to reference material (§3's Appendix section below).

**Non-negotiable addition from this revision:** every Concept in Lessons 3–7 must end with an explicit pointer to which §6.2 case study actually exercises it (e.g. Lesson 5's sharding Concept points at capstone #1's Pinterest index sharding and capstone #3's vector-DB sharding). This is the "overlap with real-world architectures" the revision asked for — without it, Lessons 3–7 would just be `system-design-primer` with different section breaks.

### Group 0 — AI/agentic fundamentals (compressed into Lesson 1 — no longer separate lessons)
*Old Groups A–E, kept here only as Lesson 1's source material. These are the sub-topics an AI engineer has typically already met; Lesson 1 refreshes them at a lighter depth than the rest of this repo (see §4's exception) instead of teaching each as its own lesson.*

- **A — Foundations:** A1. What makes AI application design different (non-determinism, token-based cost/latency, prompt as attack surface). A2. Context window as a resource. A3. Token economics.
- **B — Serving and running models:** B1. Model serving fundamentals (hosted vs. self-hosted, batching, KV cache, quantization). B2. Local/open-weight serving — one-line pointer to `learn-docker-ai-agents` Lesson 2 for hands-on. B3. Model routing/gateways. B4. Caching for LLM apps (semantic cache, prompt cache, KV-cache reuse) — explicitly cross-referenced from Lesson 5's K3/K4 as the AI-native cousin of classic caching.
- **C — Retrieval and knowledge:** C1. Embeddings. C2. Vector databases. C3. Chunking strategies. C4. RAG architecture end to end. C5. Keeping a knowledge base fresh.
- **D — Agent architecture:** D1. Chatbot vs. agent. D2. Control-flow patterns (ReAct, plan-and-execute, reflection). D3. Tool use/function calling. D4. MCP — pointer to `learn-docker-ai-agents` Lesson 3. D5. Multi-agent orchestration. D6. Declarative orchestration — pointer to `learn-docker-ai-agents` Lesson 4.
- **E — Memory and state:** E1. Short-term memory. E2. Long-term memory. E3. State/checkpointing across multi-step runs.

### Group P — Core system-design vocabulary primer → **Lesson 2** (new, added in a later revision)
*The classic-infra counterpart to Group 0: just as Lesson 1 refreshes AI-native vocabulary a reader has typically already met, Lesson 2 refreshes the basic distributed-systems vocabulary Lessons 3–7 build on, at a lighter depth than the rest of this repo (see §4's exception), instead of having each of those lessons stop to re-explain it inline.*

- **P1 — Client/server & the request/response cycle:** what a client and a server actually are, the request/response shape nearly every network interaction in this repo assumes, and why that shape matters before Lesson 4's load-balancer/reverse-proxy Concepts make sense.
- **P2 — APIs and protocols at a glance:** what an API is as a contract between two pieces of software, HTTP's request/response anatomy (method, status code, header, body) as the protocol nearly everything in this repo rides on top of — light enough to not duplicate Lesson 6's own deep RPC-vs-REST Concept (L4).
- **P3 — Databases and caches at a glance:** what a database is for (durable storage that outlives a single process) and what a cache is for (a faster copy of data you're willing to lose), stated plainly before Lesson 5's much deeper K1–K3 treatment of RDBMS scaling, NoSQL types, and caching strategies.
- **P4 — Latency, throughput, and scaling at a glance:** the everyday meaning of "slow" (latency) vs. "can't handle the load" (throughput), and vertical vs. horizontal scaling as the two basic levers — set up specifically so Lesson 3's I1 Concept can go straight to the AI-specific reframing of these terms instead of defining them from scratch.

### Group I — Scalability & availability fundamentals → **Lesson 3** (new)
- I1. Performance vs. scalability; latency vs. throughput — reframed for AI: token-generation throughput vs. per-request latency, and why "scalable" means something subtly different for an LLM app than for a CRUD app → overlaid on capstone #10 (LLM inference serving)
- I2. CAP theorem and consistency patterns (weak/eventual/strong) → overlaid on vector-DB consistency-after-write and agent long-term-memory consistency (Lesson 1's C2/E2)
- I3. Availability patterns — fail-over (active-passive/active-active), replication, the 9s math → overlaid on multi-region model-serving failover (capstone #15, LLM API gateway)

### Group J — Network & delivery layer → **Lesson 4** (new)
- J1. DNS
- J2. CDN (push vs. pull) → overlaid on serving static chat-UI assets, and why model weights themselves are a poor CDN fit
- J3. Load balancers (L4 vs. L7, SSL termination, session persistence) → overlaid on routing across inference-server replicas/GPU pools
- J4. Reverse proxy, and load-balancer-vs-reverse-proxy → overlaid on the "API gateway in front of an LLM" pattern (capstone #15)

### Group K — Data layer: databases & caching → **Lesson 5** (new)
- K1. RDBMS scaling — replication, federation, sharding, denormalization, SQL tuning → overlaid on capstone #1 (Pinterest index sharding) and capstone #6 (LinkedIn graph-scale data)
- K2. NoSQL types (key-value, document, wide-column, graph) and SQL-vs-NoSQL → overlaid on why a vector DB is architecturally closest to a wide-column/KV hybrid
- K3. Caching strategies — where to cache, cache-aside/write-through/write-behind/refresh-ahead → overlaid on capstone #10's KV-cache reuse and capstone #9's retrieval cache as AI-native variants of the same patterns
- K4. Explicit bridge back to Lesson 1's B4 (semantic caching) and C2 (vector DBs) — exists specifically to connect the classic pattern to its AI-native cousin, satisfying the "overlap" requirement from §3's intro

### Group L — Asynchronous systems & communication → **Lesson 6** (new)
- L1. Message queues vs. task queues
- L2. Back pressure
- L3. TCP vs. UDP
- L4. RPC vs. REST → overlaid on internal agent-to-tool calls (RPC-shaped) vs. the public chatbot API (REST-shaped), and why agentic systems lean on async queues far more than typical request/response apps (capstone #4/#13's long-running coding-agent tasks)

### Group M — Application architecture & security fundamentals → **Lesson 7** (new)
- M1. Monolith vs. microservices, single responsibility
- M2. Service discovery (Consul/etcd/Zookeeper)
- M3. Core security — encryption in transit/at rest, input sanitization, least privilege — the direct prerequisite for Lesson 8's F1 (prompt injection) and F3 (credential handling), explicitly cross-referenced
- M4. Back-of-envelope estimation technique + the latency-numbers table — the mechanical skill every §6.1 Step 2 depends on, taught once here instead of re-derived in every capstone

### Group F — Safety, security, and isolation → **Lesson 8** (unchanged)
- F1. Prompt injection — direct vs. indirect injection, why RAG and tool results are an attack surface, mitigation layers
- F2. Sandboxing agent execution (hands-on: directly reuses `learn-docker-ai-agents` Lesson 1 — `sbx`/microVMs — this Concept links out rather than re-teaching it)
- F3. Credential and secret handling for agents with tool access — least privilege per tool, the Gateway-as-choke-point pattern
- F4. Guardrails and output validation — schema-constrained output, content filtering, human-in-the-loop approval gates
- F5. Multi-tenant isolation — per-tenant data/credential isolation when one agent platform serves many customers

### Group G — Evaluation and observability → **Lesson 9** (unchanged)
- G1. Why you can't unit-test an LLM the normal way — non-determinism, the need for evals instead of assertions
- G2. Offline evaluation — golden datasets, LLM-as-judge, regression suites for prompts
- G3. Online observability — tracing an agent run (prompts, tool calls, intermediate reasoning), latency/cost dashboards per step
- G4. Prompt versioning and A/B testing — treating prompts as deployable artifacts with rollback

### Group H — Production operations and scaling → **Lesson 10** (unchanged)
- H1. Scaling patterns for agentic workloads — async execution, queues for long-running agent tasks, backpressure when agents fan out tool calls
- H2. Rate limiting and token budgets — per-user/per-tenant budget enforcement, graceful degradation when limits hit
- H3. Streaming responses — why/how to stream tokens to a UI, partial-result UX, cancellation mid-stream
- H4. Cost attribution — tracking spend per request/user/feature when cost is usage-based, not fixed infrastructure

### Group N — Real-world architectures & further reading → **Lesson 11** (new — promoted from the appendix)

The AI-world analog of `system-design-primer`'s own "Real world architectures," "Company architectures," and "Company engineering blogs" sections — proof that the patterns taught in Lessons 1–10 actually show up in production, beyond just the 14 capstones that got full treatment in §6.2.

- N1. **AI infrastructure building blocks** — the analog of `system-design-primer`'s MapReduce/Bigtable/GFS/Chubby/Kafka/Zookeeper table. Link + one-liner each, no worked solution: model-serving engines (vLLM, Triton, TensorRT-LLM, Ray Serve), vector/retrieval infra (Pinecone, Weaviate, Milvus, FAISS, pgvector), agent/workflow orchestration (LangGraph, Temporal), ML-ops infra (MLflow, Feast, Kubeflow), LLM observability/eval infra (LangSmith, Weights & Biases, Arize). Each row names which Lesson it reinforces (e.g. vLLM → Lesson 1's B1/B4 and capstone #10).
- N2. **Company AI architectures** — the analog of `system-design-primer`'s "Company architectures" table. Companies with a documented AI/agent architecture that *didn't* earn a full `solutions/` capstone (§6.2 already covers Pinterest, YouTube, Airbnb, LinkedIn, Uber, Netflix, Anthropic, Character.AI, Cognition): Perplexity's answer engine, GitHub Copilot, Replit Agent, Notion AI, Midjourney's diffusion serving, Shopify Sidekick, Duolingo Max, Discord's Clyde, Spotify's AI DJ, Stripe Radar. One row each — company | what they built | real reference link | one-line takeaway — same primary/secondary sourcing discipline as §6.2.
- N3. **Company engineering blogs** — the AI-specific subset of `system-design-primer`'s own blog list: OpenAI, Anthropic, Google DeepMind, Meta AI, Hugging Face, LangChain, Pinecone, Weights & Biases — plus the AI/ML teams inside companies already in the classic list (Netflix Tech Blog, Uber Engineering, Airbnb Engineering, Pinterest Engineering, LinkedIn Engineering), since several §6.2 Track 1 sources came from exactly those teams.
- N4. **How to read N1–N3** — the instruction `system-design-primer` gives, carried over directly: don't focus on nitty-gritty implementation details. Instead, identify shared principles and recurring technologies across entries, note what problem each one solves and where that approach breaks down, and note which Lesson (1–9) or §6.2 capstone each entry's core trick actually maps back to. An entry that doesn't connect back to something already taught is a dangling fact, not reinforcement — this Concept is Lesson 11's own depth-bar substitute (see §4/§7 exceptions).

### Appendix (reference only — the two things you flip back to, not read start-to-end)
- **Token/latency/cost numbers worth memorizing** (context window sizes, typical embedding dims, typical vector-search latency, $/1M tokens by provider tier) — extends Lesson 7's (M4) back-of-envelope technique with AI-specific figures.
- **Glossary** — every term introduced across all 11 lessons, one line each, for fast lookup.

---

## 4. Lesson template (every file in `lessons/` follows this exact skeleton)

```markdown
# Lesson N: <Title>

**Time:** <estimate>
**Tool(s):** <real tool(s), if any — or "Conceptual (no single verified CLI)" if none exists>

## Learning Objectives
- ...

## Concept 1: <name>
### Why?
### What?
### How?

## Concept 2: <name>
...

## Hands-On Walkthrough
<real, runnable commands if a tool exists; otherwise a worked numeric example>

## Summary
| Concept | One-line takeaway |

## Command/Reference
<verbatim command reference, or key API/code reference if no CLI>

**Next:** Checkpoint N, then Lesson N+1 — ...
```

**Non-negotiable per [[feedback-tutorial-depth]]:** every term, flag, parameter, or output field introduced in a Concept or the Hands-On Walkthrough gets a *full* definition inline, the first time it appears — not a one-line gloss assuming prior knowledge. This was explicit prior feedback on this exact repo format and applies here without exception: e.g. the first time "HNSW" appears, define what it stands for and what it actually does, not just "a fast index type."

**Where no single verified CLI exists** the Hands-On Walkthrough section still has to contain something concrete and checkable — a worked numeric example (e.g. actually compute token cost for a 50-page RAG context at a given $/1M-token rate), a real schema/payload (e.g. an actual OpenAI-style function-calling tool definition JSON), or a short runnable Python snippet using a real SDK (`openai`, a vector DB client) — never a purely abstract description with nothing to run or compute.

**Exceptions: Lessons 1, 2, and 11.** Lesson 1 compresses 21 already-familiar sub-topics (old Groups A–E) into a single refresher, so it does not follow the full Concept-per-topic Why/What/How skeleton above. Instead: one subsection per old Group (A–E), each a short paragraph plus a compact key-terms table, ending with a one-line "why this still matters for the lessons that follow" pointer (e.g. B4's semantic caching → Lesson 5's K4 bridge Concept). No numeric calculation or full Hands-On Walkthrough is required per sub-topic in Lesson 1 — it's a shared-vocabulary refresher, not first-time teaching.

Lesson 2 follows the exact same shape, one layer down the stack: it compresses Group P's four already-familiar sub-topics (P1–P4, §3) into a single refresher instead of teaching each as its own Lesson-3-style deep dive. Same format as Lesson 1 — one subsection per sub-topic, a short paragraph plus a compact key-terms table, ending with a "why this still matters" pointer forward (e.g. P3's cache-at-a-glance → Lesson 5's K3 deep dive) — and the same depth-bar exemption for the same reason: it's a shared-vocabulary refresher, not first-time teaching.

Lesson 11 is a **survey lesson**, not a teaching lesson: its Concepts (N1–N3, §3) are link-and-one-liner tables, not Why/What/How explanations — the thing being taught is already covered elsewhere (Lessons 1–10, §6.2's capstones); Lesson 11's job is pointing at *more* real examples of it. Its Hands-On Walkthrough is replaced by N4's reading instruction, and its depth-bar substitute is "every table row names which Lesson/capstone it reinforces" rather than a numeric calculation.

Only Lessons 3–10 and the `solutions/` capstones are held to the full depth bar in §7.

---

## 5. Checkpoint template (every file in `checkpoints/` follows this exact skeleton)

```markdown
# Checkpoint N: <Title>

## Purpose
<one sentence: what this verifies>

## Verification Questions
<details><summary>Question k: ...</summary>

**Answer:** ...

**Why this matters:** ...
</details>
... (aim for 5 questions, matching learn-docker-ai-agents' pattern)

## Hands-On Self-Check
<checklist of observable, checkable outcomes — [ ] not yet confirmed>

## Next Step
Move to **Lesson N+1: ...**
```

**Exception: Checkpoint 11.** Lesson 11 is a survey, not a teaching lesson (§4), so fixed Q&A-with-a-canned-answer doesn't fit — there's no single right answer to "what did Perplexity build." Checkpoint 11 replaces the Verification Questions block with an open-ended self-check instead: pick 3 entries from Lesson 11's N1–N3 tables and, for each, write one sentence naming which Lesson (1–9) or §6.2 capstone its core trick maps back to. The "Why this matters" framing still applies, just unscored — the check is whether the reader *can* make the connection, not whether they match a reference answer.

---

## 6. `solutions/` — the interview-style capstones, grounded in real case studies

This is the section that got revised after review. The requirement: don't invent generic prompts — root every capstone in a design that's **actually documented** (a named company engineering blog/paper, or a chapter in a recognized ML/AI system-design interview resource), so working through it teaches the real trade-offs someone already had to make, not trade-offs I made up. Every entry below was checked against a real source; where the primary source is thin, that's called out explicitly rather than papered over.

### 6.1 Methodology — a 6-step method, not `system-design-primer`'s 4

`system-design-primer`'s four steps (use cases/constraints → high-level design → core components → scale) are built for *infrastructure* systems, where the hard part is almost entirely the architecture diagram. AI/ML systems have an extra, prior problem that classic system design doesn't: **translating a business goal into a measurable model/agent objective** — this is the actual spine of the "Machine Learning System Design Interview" canon (Aminian & Xu / ByteByteGo) and of Educative's "Grokking the Machine Learning Interview," and it's the step most people skip straight past, which is exactly what makes answers sound like a checklist instead of like a designer. Every `solutions/` entry follows this 6-step method instead:

1. **Clarify requirements & frame the ML/AI objective** — functional scope, non-functional constraints (latency SLA, scale), and critically: what's the actual metric being optimized (CTR, precision@k, MAE, win-rate vs. a baseline), what counts as ground truth/feedback signal, and what's explicitly out of scope. This step is where most of the "thinking like a designer" actually happens — get the objective wrong and every downstream choice is wrong for a reason that looks like an infra mistake but isn't one.
2. **Back-of-envelope constraints** — the `system-design-primer`-style numeric estimate (QPS, data volume, tokens/sec, $/month), now carried through to Step 4's trade-offs.
3. **Data / knowledge pipeline** — what data exists, how it's collected/labeled/embedded, how it's kept fresh, and what happens when it's wrong or stale. (Classic infra system design has no equivalent of this step — it's the one most borrowed from the ML-interview canon.)
4. **Model/agent core design** — the actual modeling or agent-architecture choice (which model family, prompting vs. fine-tuning vs. RAG vs. an agent loop, single-model vs. multi-agent) stated as an explicit trade-off against at least one alternative, not as the only option.
5. **Serving architecture** — the `system-design-primer`-style infra diagram: APIs, caching, gateway/routing, sandboxing, scaling. This is where most of the direct overlap with the rest of the repo's `lessons/` content gets exercised.
6. **Evaluation, monitoring, and iteration** — offline eval before shipping, online metrics after shipping, the feedback loop back into Step 3's data, and the failure modes that show up only at scale.

Every `solutions/<slug>/README.md` is structured around these six numbered steps, each one ending with an explicit **Trade-offs considered** callout — a short list of the alternative choices at that step and why they were rejected or deferred, which is the part of "thinking like a designer" that a pure architecture diagram never shows.

### 6.2 Catalog — grounded case studies, by track

**Track 1 — Classic ML system design (the long-standing interview canon; every entry below has both a primary engineering source and a seat in a recognized ML-interview resource)**

1. **Visual search** — Pinterest's Flashlight/Lens/Shop-the-Look. Source: Zhai et al., *"Learning a Unified Embedding for Visual Search at Pinterest,"* KDD 2019 (arXiv:1908.01707) — a single multi-task embedding replacing several product-specific ones. Also a chapter in *Machine Learning System Design Interview* (Aminian & Xu, ByteByteGo). **Teaches:** when one shared embedding beats several specialized ones, and the precision/recall cost of binarizing embeddings for storage.
2. **Ad click-through-rate (CTR) prediction** — the original production-ML design question. Source: McMahan et al., *"Ad Click Prediction: a View from the Trenches,"* Google, KDD 2013. Also a core chapter across every ML-interview resource. **Teaches:** online learning under extreme class imbalance, and why "accuracy" is the wrong metric here.
3. **Video recommendation** — YouTube's candidate generation + ranking split. Source: Covington et al., *"Deep Neural Networks for YouTube Recommendations,"* RecSys 2016. **Teaches:** two-stage retrieval-then-rank architecture, and why you can't rank what you didn't first retrieve cheaply.
4. **Search ranking** — Airbnb listing search. Source: Haldar et al., *"Applying Deep Learning to Airbnb Search,"* KDD 2019 (arXiv:1810.09591). **Teaches:** the explicit lesson from the paper itself — going from GBDT to a neural ranker only paid off after the simpler model's gains had already plateaued; a direct lesson in not reaching for the fancier model first.
5. **Harmful content detection** — a staple "trust & safety" design question, now with a genuinely current primary source. Source: Markov et al. (OpenAI), *"A Holistic Approach to Undesired Content Detection in the Real World,"* arXiv:2208.03274 (submitted Aug. 2022, Oral presentation at AAAI-23) — covers taxonomy design, labeling instructions, active learning for rare classes, and overfitting risk in the classifier pipeline itself. (Corrected from an earlier "June 2024" date, which was only the publish date of OpenAI's own listing page for this paper, not the paper itself.) Also a chapter in *Machine Learning System Design Interview*. **Teaches:** that the hard part is the labeling/taxonomy pipeline, not the classifier architecture.
6. **Friend/connection recommendation ("People You May Know")** — LinkedIn. Sources: LinkedIn Engineering's 2020 post on building a heterogeneous-network recommender, and the 2021 *"Optimizing PYMK for Equity in Network Creation"* post. **Teaches:** triangle-closing as a graph feature, and a real example of a fairness trade-off (equity vs. raw predicted-connection-probability) being deliberately added after the fact.
7. **ETA / arrival-time prediction** — Uber. Source: *"DeepETA: How Uber Predicts Arrival Times,"* eng.uber.com. **Teaches:** the "predict the residual, not the absolute value" pattern — ML corrects a deterministic routing-engine estimate rather than replacing it outright, a trade-off between interpretability and raw accuracy.
8. **Personalized feed ranking** — Netflix row ranking. Source: Amatriain & Basilico, *"Netflix Recommendations: Beyond the 5 Stars"* (Netflix Tech Blog, 2012, two parts). **Teaches:** ranking is a separate problem from rating-prediction accuracy — a system can nail RMSE on ratings and still produce a bad row ordering.

**Track 2 — GenAI/LLM system design (the 2023–2025 canon, documented in primary company engineering sources)**

9. **RAG system design** — enterprise knowledge-base chatbot. Source: Anthropic, *"Introducing Contextual Retrieval,"* Sept. 2024 — prepending LLM-generated context to each chunk before embedding/indexing, combined with reranking, to fix the "chunk loses context when split from its document" failure mode. **Teaches:** chunking isn't a preprocessing detail, it's the single biggest lever on RAG accuracy, and the fix itself costs tokens that have to be budgeted for.
10. **LLM inference serving at scale** — Source: Kwon et al., *"Efficient Memory Management for LLM Serving with PagedAttention,"* SOSP 2023 (arXiv:2309.06180, the vLLM paper) for the mechanism; Character.AI's Noam Shazeer's June 2024 engineering post (widely covered secondhand — I could not confirm a still-live primary URL, flagged here rather than cited as confirmed-primary) for the production result: a reported ~33x serving-cost reduction via KV-cache reuse across turns. **Teaches:** KV-cache memory management is the actual bottleneck resource in LLM serving, not FLOPs — same shape of lesson as OS virtual memory paging, deliberately.
11. **AI content moderation pipeline (LLM era)** — same OpenAI source as #5, revisited through the LLM-specific lens: streaming moderation of generated output, not just user input, and a cheap-filter-then-expensive-judge model chain. **Teaches:** the moderation design problem doesn't change when the content is LLM-generated instead of user-generated — the taxonomy/labeling discipline from Track 1 still dominates.
12. **Multi-agent customer-support platform** — Sources: third-party technical write-ups of Sierra AI's architecture (a supervisor over a "constellation" of specialist models, plus a separate agent data platform unifying per-customer context; also described elsewhere as a planner/executor/validator split) and OpenAI's Klarna customer story. **Flagged explicitly:** neither Sierra nor Klarna has published their own primary engineering teardown as of this search — this entry is built from secondary technical coverage and should be labeled as such in the write-up, not presented as confirmed primary-source fact. **Teaches:** validator/guardrail agents as a distinct role from the agent that takes the action, so one bad tool call doesn't reach the customer unchecked.
15. **LLM API gateway** — multi-provider routing, rate limiting, token budgets, caching, fallback on provider outage. **Sources (secondary/product-documentation — no single company's primary engineering teardown exists for this pattern, confirmed via search):** LiteLLM's open-source proxy docs (OpenAI-compatible interface across 100+ providers; routing, retries, fallback, spend tracking, per-key/team/model rate limits), Portkey's product docs (managed control plane: routing, load balancing, fallbacks, caching, guardrails, budget limits), Cloudflare's AI Gateway docs (edge-hosted proxy: caching, rate limiting, analytics, logging). **Teaches:** classic API-gateway patterns (rate limiting, load balancing, caching, failover) don't transfer to LLM traffic unchanged — a traditional gateway rate-limits *requests*, not *tokens*, which every one of these real products had to add specifically for LLM traffic. (Numbered 15, out of position, rather than renumbering Track 3's already-referenced #13/#14 — added after the fact once Lesson 3's draft surfaced that it had been dropped during the earlier sourcing pass despite still being needed as a case-study target.)

**Track 3 — Agentic system design (this repo's core differentiator — the questions `system-design-primer` has no equivalent of at all)**

13. **Autonomous coding agent** — the "build something like Devin/Claude Code/Cursor" question. Source: Cognition Labs, *"Introducing Devin,"* March 2024 — sandboxed shell/editor/browser access, a plan-then-execute loop, continuous progress reporting, benchmarked on SWE-bench (Cognition's own reported 13.86% resolve rate vs. a prior 1.96% baseline — their own benchmark claim, stated as such). **Teaches:** giving an agent its own full dev environment (not just one tool at a time) is what turns single tool-calls into multi-hour autonomous task completion — and why that raises the sandboxing stakes from Group F of this same repo.
14. **Computer-use / browser agent** — an agent that operates a GUI directly (mouse/keyboard/screenshots) instead of through APIs. Source: Anthropic's "computer use" capability announcement (Claude 3.5 Sonnet, Oct. 2024). **Teaches:** the design cost of a screenshot-reasoning-action loop (latency per step, action-grounding errors) vs. a direct-API agent — a trade-off this repo's Group D (agent control-flow patterns) should make explicit.

Each gets its own `solutions/<slug>/README.md`, structured around the six steps in §6.1; large/complex ones (visual search, RAG, multi-agent platforms) may also get a diagram image and/or a `*_snippets.py`, mirroring `system-design-primer`'s per-solution file layout. Every entry's README opens with a **Source(s)** line naming the real reference(s) above — and an explicit **Confidence** note (primary source vs. secondary/third-party coverage) wherever that distinction matters, per the Sierra/Klarna and Character.AI entries above.

### 6.3 When a solution touches a concept with no lesson yet

The catalog in §6.2 is sourced from real case studies, which means it will keep surfacing concepts the taxonomy in §3 didn't anticipate — e.g. capstone #1 (Pinterest) needs "multi-task embedding learning" and "binarized embeddings for retrieval," capstone #5/#11 (OpenAI moderation) needs "active learning for rare classes," capstone #6 (LinkedIn PYMK) needs "triangle-closing as a graph feature," none of which have a Group A–H lesson. Without a rule, these either get silently skipped (undermining the depth bar) or get fully re-taught inline every time they recur (undermining the "don't duplicate" principle the plan already applies to `learn-docker-ai-agents`).

**But most of what Track 1's capstones need isn't AI-native at all — it's the classic infra stack.** Visual search needs a sharded index and a feature store; ad-click prediction and feed ranking need caching tiers, DB read replicas, and a batch/online split; every Track 1 capstone's Step 5 (serving architecture, §6.1) leans on load balancers, horizontal scaling, master-slave replication, message queues. After the revision in §1, that's no longer content this repo defers out for — Lessons 3–7 teach exactly this, directly, as the repo's primary new material. So the rule has a mandatory check *before* either of the two options below ever fires:

0. **Check Lessons 3–7 first, then `system-design-primer`.** If the concept is core system design now taught directly in this repo — scalability/availability patterns → Lesson 3, DNS/CDN/load-balancing → Lesson 4, databases/caching → Lesson 5, queues/communication → Lesson 6, app architecture/security → Lesson 7 — link to that lesson's Concept. Don't write a Sidebar and don't promote a new lesson for something already taught here. Only if the concept is classic infra *beyond* what Lessons 3–7 curate down to (e.g. B-tree index internals, a specific SQL query-cache tuning flag, a full OSI-layer breakdown) does it defer out to `system-design-primer` as the deeper reference — exactly how that repo's own `solutions/` folder links back to its own README rather than re-explaining a concept inline. Only concepts genuinely AI/agent-native, with no home in Lessons 1–7 either, proceed to steps 1–3.

1. **First appearance → inline Sidebar.** The solution doc explains it on the spot with a compact Sidebar block — same shape as a lesson Concept (Why?/What?/How?), same full-definition-on-first-use bar from §7 — directly inside whichever of the six steps (§6.1) it comes up in. It also gets a one-line entry added to `appendix/glossary.md` immediately, even if nothing else changes that day.
2. **Second appearance, anywhere → promotion candidate.** If a second `solutions/` entry (or a later-written lesson) needs the same concept, it's no longer "case-study-specific" — it gets promoted into a real lesson with a checkpoint, slotted into whichever existing Group A–H it fits (or, rarely, justifying a new Group if it fits none — that's itself a sign the §3 taxonomy was incomplete and should be revised, not worked around). The first solution's Sidebar is then rewritten as a link to the new lesson, exactly like D4/D6/F2/B2 already link out to `learn-docker-ai-agents` instead of re-teaching sandboxing or model-serving.
3. **Never promoted = fine.** A concept that only one case study ever needs (e.g. the specific detail of how Uber's routing engine computes segment-wise traversal time) stays a Sidebar forever. Not everything needs to become a lesson — only what turns out to be reused.
4. **Build-order consequence:** each phase in §8 ends with a **concept harvest** pass — scan every Sidebar written so far for second-appearances, and write any newly-triggered lessons before starting the next phase, rather than batching that discovery to the very end. This keeps the taxonomy honest and growing from real usage instead of being frozen as of this plan's first draft.

---

## 7. Depth bar (how we know we matched `system-design-primer`'s level)

A lesson or solution doc is **not done** until it has, at minimum:
- At least one concrete numeric calculation (latency, cost, memory, QPS — whatever's relevant), not just qualitative description
- At least one real schema, payload, or code snippet (not pseudocode-only, unless the source material itself only has pseudocode)
- Explicit trade-offs stated as trade-offs ("X is good for ___, bad for ___"), never a single "correct" answer presented as the only option
- Every new term defined in full on first use (per [[feedback-tutorial-depth]])
- A "Source(s) and further reading" list, matching `system-design-primer`'s convention on every topic section
- For every `solutions/` entry specifically: the named real-world source(s) from §6.2, each tagged **primary** (a named company's own engineering blog/paper) or **secondary** (third-party coverage only) — never presented as more authoritative than it is
- For every Concept in Lessons 3–7 specifically: an explicit pointer to which §6.2 case study exercises it (per §3's non-negotiable addition) — a core-system-design lesson with no case-study pointer isn't done

---

## 8. Build order

**Phase 1 — Lesson 1 first, fast.**
- Write the compressed refresher (Lesson 1) + its lighter Checkpoint 1 in one pass. Deliberately quick — it's a shared-vocabulary refresher, not new teaching (§4's exception) — the point is to get it out of the way before the real work starts.

**Phase 2 — Core system design, part 1: the resource/availability layer.**
- Lesson 3 (scalability & availability) + Checkpoint 3
- Lesson 4 (network & delivery) + Checkpoint 4
- First case-study overlay pass: write `solutions/llm-api-gateway` (capstone #15) and `solutions/llm-inference-serving` (capstone #10) far enough to confirm Lessons 3–4's Concepts actually produce useful case-study pointers (§7's new requirement) before writing the remaining three core lessons

**Phase 3 — Core system design, part 2: the data/communication layer.**
- Lesson 5 (data layer) + Checkpoint 5
- Lesson 6 (async & communication) + Checkpoint 6
- Lesson 7 (application architecture & security) + Checkpoint 7
- Overlay pass against `solutions/visual-search` (capstone #1), `solutions/rag-contextual-retrieval` (capstone #9), `solutions/autonomous-coding-agent` (capstone #13, Devin-style)

**Phase 4 — Lessons 8–10, unchanged scope.**
- Lesson 8 (safety/isolation) + Checkpoint 8 — F2 Concept still cross-links to `learn-docker-ai-agents` Lesson 1
- Lesson 9 (evaluation/observability) + Checkpoint 9
- Lesson 10 (production/scaling) + Checkpoint 10

**Phase 5 — Remaining `solutions/*` catalog entries.**
- Fill out the rest of §6.2's 14 capstones (Track 1's classic-ML entries #3–4, #6–8; Track 2/3's remaining entries #5/#11, #12, #14)

**Phase 6 — Lesson 11 + Checkpoint 11, last, on purpose.**
- Lesson 11's whole point is pointing back at Lessons 1–10 and the §6.2 capstones (N4's reading instruction), so it's written last, once there's something real to point back *to* — writing it earlier would mean guessing at cross-references that don't exist yet
- Appendix (token/latency numbers, glossary) finalized alongside it, pulling figures and terms from all 10 lessons that existed at the time

**Phase 7 — Depth-bar pass.** Re-check every lesson and solution against §7, including the case-study-pointer requirement for Lessons 3–7, the primary/secondary sourcing tags for every `solutions/` entry, and that every Lesson 11 table row actually names a Lesson/capstone per N4.

**Phase 8 — Post-build revision: insert Lesson 2 (added after Phases 1–7 were already complete).** Review of the finished repo found that Lessons 3–7 assumed a baseline of classic distributed-systems vocabulary (client/server, request/response, API, database, cache, latency/throughput) that not every reader has — the same gap Lesson 1 already addresses one layer up, for AI-native vocabulary. Rather than have Lessons 3–7 stop and re-explain this inline, a new Lesson 2 (Group P, §3) was inserted to compress it into one refresher, mirroring Lesson 1's own template exception. This meant: writing Lesson 2 + Checkpoint 2 through the same Writer → Reviewer → Rewriter pipeline as every other lesson; renumbering every lesson and checkpoint file from 2–10 up to 3–11; and updating every cross-reference across `plan.md`, `PROGRESS.md`, all lessons/checkpoints, and all `solutions/` capstones to match. Every lesson/checkpoint total mentioned anywhere in this plan (e.g. "10 lessons total," "all 10 lessons") now reads as 11 to reflect this.

---

## 9. Open decisions (need a call before or during Phase 1)

- **Repo name:** using `ai-system-design-primer` as a placeholder (mirrors the source name plus the AI scope). Could also go with `agentic-system-design` or `learn-ai-system-design` to match the `learn-*` naming already used for `learn-docker` / `learn-docker-ai-agents`.
- **Cross-linking vs. duplicating** with `learn-docker-ai-agents`: plan above assumes *linking* (pointing to that repo's Lessons 1–4 for sandboxing/model-serving/MCP/cagent hands-on) rather than re-explaining them, to avoid maintaining two copies of the same verified commands. Worth confirming that's the intended relationship between the two repos before Phase 1 starts.
- **How "hands-on" the non-Docker lessons get:** for topics with no single installed CLI (most of Groups C/D/E/F/G), the plan commits to code snippets against real SDKs (e.g. `openai`, `chromadb`/`pinecone`, `langchain`) rather than abstract description — worth confirming which specific libraries are acceptable to install/use for verification before writing those lessons.
