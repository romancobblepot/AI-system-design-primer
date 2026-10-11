# Lesson 9: Evaluation and Observability

**Time:** 70-90 minutes
**Tool(s):** Conceptual (no single verified CLI) — real JSON schemas modeled on OpenAI's Evals framework and Langfuse/LangSmith's tracing and prompt-versioning conventions, plus a runnable Python pipeline, instead.

## Learning Objectives

By the end of this lesson, you will:

- Be able to explain why ordinary unit-test assertions fail for LLM output, building directly on Lesson 1's Concept A1 (non-determinism) rather than re-deriving it, and compute how often a naive exact-match assertion would falsely fail on output that's actually correct
- Be able to define golden dataset, LLM-as-judge, and regression suite in full, design a golden-dataset entry and an LLM-judge scoring schema, and resolve capstone #9's own forward reference to "Lesson 9, G1-G2" for generation-quality evaluation
- Be able to define observability, trace, and span in full, design a trace/span schema for an agent run, and compute the storage cost (and the savings a sampling rate buys back) of tracing a fleet of agent sessions at capstone #13's own scale
- Be able to define prompt versioning, A/B testing, and rollback in full, design a prompt-version config with a rollback pointer, and run a two-proportion significance check to decide whether an observed pass-rate improvement is real or noise
- Be able to point to exactly which already-written capstones (#9 RAG/contextual-retrieval, #10 LLM inference serving, #13 autonomous coding agent, #15 LLM API gateway) each Concept in this lesson connects to — including the one Concept (G2) that resolves an explicit forward reference capstone #9 already made by name before this lesson existed

---

## Concept 1: Why You Can't Unit-Test an LLM the Normal Way

### Why?

Lesson 1's Concept A1 already named the root cause: **non-determinism** — "the property that running the exact same prompt against the exact same model twice can produce two different outputs," because the model samples from a probability distribution over possible next tokens rather than always picking the single most likely one, and because "even with sampling turned all the way down, floating-point and batching effects on real serving hardware can still introduce small variation." That same Concept states why this lesson exists: "every piece of ordinary software testing assumes 'same input, same output.' AI application design can't assume that, which is the direct reason Lesson 9 exists (you need evals, not plain assertions, to know if an AI feature is 'working')." This Concept doesn't re-derive non-determinism (Lesson 1 already did that) — it names exactly why non-determinism breaks the standard testing tool, and what replaces it.

### What?

A **unit test** is a small, automated test that checks one piece of code's behavior in isolation by running it and comparing the actual output against one expected, hardcoded value. An **assertion** is the literal check inside that test — e.g. `assert actual_output == expected_output` — which fails the test the instant the two values don't match exactly. Both tools assume the property Lesson 1's A1 names ordinary software as having and AI applications as lacking: the same input, called twice, must produce the identical output every time, or something is broken.

An LLM call breaks that assumption in two distinct ways, only the first of which is non-determinism itself:

- **Sampling-level non-determinism** — the same prompt, sent twice, can come back with two different token sequences, for the reason Lesson 1's A1 already gives. An `assert actual == expected` check against one hardcoded string will intermittently fail even when the model's behavior hasn't changed at all.
- **Semantic equivalence** — even with perfectly deterministic output, there's often no single correct string to assert against in the first place. "New hires get 15 PTO days in year one" and "In their first year, new employees accrue 15 days of paid time off" are both fully correct answers to the same question — not a sampling artifact, but a property of natural language itself: many different strings can express the same correct meaning, and an exact-match assertion has no way to know that.

An **eval** (short for evaluation) is the replacement: a measurement run over a whole *set* of examples, using a scoring method that tolerates the right kind of variation — semantic similarity, a human or model-assigned quality score, or a looser structural check — rather than demanding byte-for-byte equality with one fixed expected string. An eval doesn't ask "did this exact output occur," the way an assertion does; it asks "how good, on average, is the system's behavior across a representative set of cases" — the only question actually answerable given the two properties above.

### How?

**Worked example — the false-failure rate a naive exact-match assertion produces on correct output.** Say a team wires up an old-style unit test for a RAG chatbot's answer to one fixed golden question (e.g. capstone #9's `solutions/rag-contextual-retrieval` enterprise knowledge-base assistant, asked "How many PTO days do new hires get in their first year?"), asserting the model's output exactly equals one hardcoded reference string. Illustrative, not a documented measurement: an audit of 50 independent, correct generations for this question finds only 8 byte-identical to that reference string — the other 42 are equally correct, just phrased differently (`exact_match_rate = 8/50 = 0.16`).

If this assertion runs in CI on every commit regardless of whether the prompt or model changed — ordinary unit-test behavior, which exists to catch *any* regression, not just ones the author anticipated — across 40 unrelated commits that touch nothing about this feature at all:

```
exact_match_rate = 0.16
unrelated_commits = 40

expected_false_failures = unrelated_commits × (1 − exact_match_rate)
                         = 40 × 0.84
                         = 33.6 ≈ 34 false failures out of 40 unrelated commits
```

A test that fails on roughly **34 of every 40 commits that didn't even touch the feature it's testing** is not a test anyone can act on — it fails so often, for reasons unrelated to correctness, that a team stops trusting it or stops running it, which is worse than not having it at all. This is the concrete case for why an eval (Concept 2, next) — scored for correctness-despite-phrasing-variation, across many examples, with a pass/fail *rate* rather than a single assert — is the tool that actually works here, not a nice-to-have alternative to assertions.

**Trade-offs considered:** Keeping exact-match assertions for the parts of an LLM application that genuinely are deterministic and structurally fixed — e.g. Lesson 8's Concept 4 schema-constrained tool-call validation, where `required` fields and types either match a JSON Schema or they don't — is still exactly the right tool; this Concept's point is narrower than "assertions are always wrong," it's "assertions are the wrong tool specifically for freeform generated content, where non-determinism and semantic equivalence both apply." Replacing every check with a loose eval would catch real regressions in open-ended generation, but would be a worse, slower tool than a plain assertion for the genuinely structured parts of the same system (a tool call's shape, an API's response code) — which is exactly why real production systems use both, applied to the parts each one actually fits.

**Case-study pointer:** capstone #9's own retrieval metric (`recall@20` — Step 1, Step 6) is the case where a deterministic check still works despite the model being involved: it asks "did the correct chunk ID appear anywhere in the top 20 retrieved chunks" — a discrete, exact membership check against a known-correct chunk ID, not a freeform-text comparison — so that metric is unaffected by this Concept's problem. The moment the question shifts to "is the *generated answer's text* correct" — capstone #9's own Scope note's explicitly deferred territory — this Concept's problem is exactly why that capstone couldn't extend `recall@20`'s exact-match logic to the generation step, and had to defer it here instead.

**Source(s) and further reading:**

- Lesson 1 (`lesson-1-ai-fundamentals-refresher.md`), Concept A1 — non-determinism and "the direct reason Lesson 9 exists," referenced in full above, not re-derived
- OpenAI, `openai/evals` (open-source repository) — the framework that formalized "write an eval, not an assertion" as the standard tool for measuring LLM behavior at scale, via templated eval definitions and custom scoring logic rather than single hardcoded expected values
- `solutions/rag-contextual-retrieval/README.md` (capstone #9), Step 1 and Step 6 — the `recall@20` metric this Concept's case-study pointer contrasts with freeform-text evaluation
- Lesson 8 (`lesson-8-safety-and-isolation.md`), Concept 4 — schema-constrained output, the genuinely-structured case where a plain assertion is still the right tool, referenced not re-derived

---

## Concept 2: Offline Evaluation — Golden Datasets, LLM-as-Judge, Regression Suites

### Why?

Concept 1 established that a single assertion can't tell you whether an LLM feature is "working." That leaves an open question: if not one assertion, what do you run before shipping a change to a prompt, a model, or a pipeline — and how do you score something as open-ended as a generated paragraph at all? Capstone #9's own Scope note named this Concept by number before this lesson existed: it explicitly defers "generation-quality evaluation of the final answer once retrieved chunks are handed to the model" to "Lesson 9's territory, G1-G2" — distinct from that capstone's own `recall@20` retrieval metric, which it does cover itself. This Concept is that deferred piece, resolved.

### What?

A **golden dataset** is a fixed, curated set of input examples paired with a hand-verified correct (or acceptable-range) output for each one — "golden" meaning the expected outputs are checked and trusted as ground truth, the way a labeled test set is trusted in classical ML. Unlike a single hardcoded assertion, a golden dataset holds many examples at once, so a pass *rate* across the set — not a single pass/fail — becomes the thing you measure and compare over time.

**LLM-as-judge** is the technique of using a separate LLM call to score a candidate output's quality against a rubric (a written set of criteria the judge checks, e.g. "faithfulness: does the answer only state facts supported by the provided source text?") instead of comparing it to one fixed expected string. This is the concrete answer to Concept 1's semantic-equivalence problem: a judge model can recognize that two differently-worded answers both satisfy the rubric, where an exact-match assertion cannot. Zheng et al., *"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"* (arXiv:2306.05685, NeurIPS 2023 Datasets and Benchmarks track), is the paper that validated this technique isn't just a convenient shortcut: using GPT-4 as a judge against both a controlled set of expert human ratings (MT-Bench) and a larger crowdsourced set (Chatbot Arena), the paper reports GPT-4's judgments agree with human preference **more than 80% of the time — roughly the same level of agreement human raters have with each other** — while documenting real judge biases (favoring longer answers, the first-listed answer, or its own family's writing style) that a rubric and prompt design must account for, not assume away.

A **regression suite** is a golden dataset run automatically every time a prompt, model, or pipeline component is about to change, to catch **regressions** — cases where a previously-correct behavior becomes incorrect because of the change — before that change ships, rather than discovering it from a production incident afterward.

### How?

**A golden-dataset entry and an LLM-as-judge scoring schema, built for exactly the generation-quality gap capstone #9's Scope note deferred here.**

```json
{
  "query_id": "pto-policy-001",
  "query": "How many days of PTO do new hires accrue in their first year?",
  "golden_chunk_ids": ["chunk_4821", "chunk_4822"],
  "golden_answer": "New hires accrue 15 PTO days in their first year, prorated monthly from their start date.",
  "category": "hr-policy"
}
```

`golden_chunk_ids` stays on the record even though this Concept's job is generation, not retrieval — so a failing case can be triaged correctly: a wrong *answer* with the right chunks retrieved is a generation-step failure (this Concept's territory); a wrong answer caused by wrong chunks is a retrieval-step failure (capstone #9's own `recall@20`, Concept 1's pointer) — the same record diagnoses both without guessing which stage broke.

```json
{
  "judge_model": "claude-opus-4-5",
  "query_id": "pto-policy-001",
  "candidate_answer": "New employees build up 15 days of paid time off during year one, added monthly.",
  "rubric": {
    "faithfulness": "Does the answer state only facts supported by golden_answer, with no invented details?",
    "relevance": "Does the answer actually address what was asked, not a related-but-different question?"
  },
  "faithfulness_score": 5,
  "relevance_score": 5,
  "rationale": "Matches golden_answer's PTO amount (15 days) and accrual pattern (monthly, first year); phrasing differs but no facts are added or contradicted.",
  "pass": true
}
```

The judge's output is itself structured (scores 1-5 plus a `pass` boolean from a threshold, e.g. `faithfulness_score >= 4 AND relevance_score >= 4`) — which makes "did this version pass the golden set" a countable rate across many examples, not a vibe.

**Worked example — a regression suite's gate, run before two different candidate prompt changes.** Say capstone #9's chatbot runs its generation prompt (version `v12`) against a 150-example golden dataset built in the shape above, with the judge's `pass` field aggregated into a pass rate: `129/150 = 0.86` (86%). Two candidate prompt edits are proposed:

```
baseline (v12):      129 / 150 pass = 0.8600  (86.0%)
candidate (v14):     102 / 150 pass = 0.6800  (68.0%)

regression_gate_threshold = 5 percentage points allowed drop

v14_drop_vs_baseline = (0.8600 − 0.6800) × 100 = 18.0 percentage points
18.0 > 5  →  regression suite BLOCKS v14 from shipping
```

`v14` dropped the pass rate by 18 points — well past the 5-point threshold this team set as acceptable noise — so the regression suite blocks it automatically, the same way a failing CI check blocks a merge, except here the check is a pass-rate comparison across a golden set rather than a single assertion. (A second candidate, `v13`, scores `136/150 = 0.9067` — an apparent *improvement* over `v12`. Whether that's real or noise is exactly the question Concept 4 answers, reusing these same three numbers.)

**Trade-offs considered:** LLM-as-judge scales to far more examples than human review can afford to check on every single prompt change, but it inherits the judge model's own biases and blind spots — per Zheng et al.'s own findings, a judge can be swayed by answer length or style independent of actual correctness, which is why a rubric has to name concrete, checkable criteria (faithfulness, relevance) rather than a vague "is this a good answer?" prompt. A golden dataset is only as good as its own labels and its own coverage — a set of 150 examples built at launch, never revisited, will silently stop representing the real traffic mix as the product's usage evolves, the same "stale eval set" risk capstone #9's own Step 6 already names and closes by routing real production failures back into the set (Concept 3's territory, below).

**Case-study pointer:** this Concept directly resolves capstone #9's own forward reference — its Scope note named "Lesson 9's territory, G1-G2" by number for exactly the generation-quality gap this Concept's golden-dataset-plus-LLM-judge pipeline fills, distinct from and complementary to that capstone's own `recall@20` retrieval metric (Concept 1's pointer). Capstone #13 (`solutions/autonomous-coding-agent`) is the instructive contrast at the other end of the offline-eval spectrum: its Step 6 reports Cognition's own SWE-bench resolve-rate figures (13.86% vs. a 1.96% prior baseline), graded by SWE-bench's fully deterministic criterion — "previously-failing tests now pass, previously-passing tests stay passing" — not an LLM judge at all, because a code patch's correctness *does* have an objective, checkable definition the way a free-text chatbot answer doesn't. The two capstones sit at opposite ends of the same spectrum: deterministic golden-dataset grading where "correct" is checkable by a test suite, LLM-as-judge grading where it isn't.

**Source(s) and further reading:**

- Zheng, Chiang, Sheng, et al., *"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,"* arXiv:2306.05685, NeurIPS 2023 Datasets and Benchmarks track — confirmed via the paper's own abstract and NeurIPS publication record; source of the >80% GPT-4/human agreement figure, confirmed as matching human-human agreement levels, and of the documented judge biases (position, verbosity, self-enhancement) referenced above
- OpenAI, `openai/evals` (open-source repository) — a real, widely-used framework for defining golden-dataset-style evals (templated examples plus custom scoring logic), referenced in Concept 1 and extended here
- `solutions/rag-contextual-retrieval/README.md` (capstone #9), Scope note, Step 1, Step 6 — the explicit "Lesson 9, G1-G2" forward reference this Concept resolves, and the stale-eval-set risk this Concept's trade-offs reference
- `solutions/autonomous-coding-agent/README.md` (capstone #13), Step 1 Sidebar and Step 6 — SWE-bench's deterministic grading criterion and Cognition's own reported resolve-rate figures, the deterministic-grading contrast case this Concept's pointer cites

---

## Concept 3: Online Observability — Tracing an Agent Run

### Why?

Concepts 1-2 are both about *before* a change ships — golden sets and regression suites run in CI against a fixed set of examples. Once an agent is live, a new problem appears that no offline eval set can catch: capstone #13's own Step 6 names it directly as "the specific failure mode this capstone has to design against" — "an agent going off-track for an hour before anyone notices," where "a plan step can keep 'succeeding' by the agent's own account while making no real forward progress." A multi-step agent run (Lesson 1's Concept D2 control-flow patterns — ReAct, plan-and-execute — already name the loop shape) can fail on its 40th tool call after 39 genuinely correct ones, and a single pass/fail signal at the end tells you nothing about *where* in that chain things went wrong. This Concept is the answer: visibility into the run's actual internal steps, not just its final output.

### What?

**Observability** is the property that a system's internal behavior can be understood from the data it emits — logs, metrics, and the trace/span records defined next — without having anticipated the exact question in advance. This is a meaningfully different bar than plain monitoring (watching a fixed, predefined set of metrics against thresholds): observability lets an engineer ask a *new* question after an incident ("which tool call in session X actually stalled?") and get an answer from data already being collected, rather than needing to have instrumented that specific question beforehand.

A **trace** is the complete record of one end-to-end operation — here, one agent session, from the moment a task is submitted to the moment it finishes (or is cancelled). A **span** is one discrete unit of work inside that trace — one LLM reasoning call, one tool invocation, one retrieval lookup — each with its own start time, end time, inputs, outputs, and metadata. Spans nest: a span can have a `parent_span_id` pointing to the span that triggered it, letting a tracing system reconstruct the full call tree of a session (which tool call happened inside which reasoning step) rather than a flat, unordered list of events. This trace/span vocabulary is the standard shape used by OpenTelemetry-based LLM observability tooling — e.g. Langfuse, an open-source LLM observability platform whose docs describe traces as containing "nested spans, generations (LLM calls), and events," built directly on OpenTelemetry; and LangSmith, whose docs define a "run" (one LLM call, one tool call, one retrieval step) as equivalent to an OpenTelemetry span, and a "trace" as the collection of runs/spans belonging to one operation.

**Percentile latency (p50 / p90 / p99)** is a way of summarizing a latency distribution that a single average can hide: the **p50** (median) is the latency value below which 50% of requests fall; **p90** and **p99** are the same idea at the 90th and 99th percentile — e.g. a p99 of 2 seconds means 99% of requests finish in under 2 seconds, and the slowest 1% take longer. An average can look fine while a small but real fraction of requests are badly slow; reporting p50/p90/p99 together, rather than one mean, is what surfaces that tail.

### How?

**A trace/span schema for one agent session**, built directly on capstone #13's own session-state fields (Step 3/5) — `session_id`, `plan_step_index`, the `shell`/`editor`/`browser` tool split (Step 5) — rather than inventing a conflicting shape:

```json
{
  "trace_id": "trace-7f3a2e91",
  "session_id": "devin-session-7f3a2e91",
  "spans": [
    {
      "span_id": "span-02",
      "parent_span_id": null,
      "name": "plan_step_02",
      "kind": "llm_reasoning",
      "start_time": "2026-10-11T14:03:12.100Z",
      "end_time": "2026-10-11T14:03:16.900Z",
      "input": {"plan_step_index": 2, "instruction": "run the config_loader test suite"},
      "output": {"decision": "call shell_tool"},
      "tokens": {"input": 3000, "output": 300},
      "cost_usd": 0.0135,
      "latency_ms": 4800
    },
    {
      "span_id": "span-03",
      "parent_span_id": "span-02",
      "name": "shell_tool_exec",
      "kind": "tool",
      "start_time": "2026-10-11T14:03:16.950Z",
      "end_time": "2026-10-11T14:03:17.792Z",
      "input": {"action": "pytest tests/ -k config_loader"},
      "output": {"exit_code": 0, "tests_passed": 14},
      "latency_ms": 842
    }
  ]
}
```

`span-03`'s `parent_span_id` of `"span-02"` records that the shell execution happened *because of* that specific reasoning step — reconstructing exactly the "which tool call happened inside which decision" chain this Concept's Why? names as missing from a flat log. `cost_usd` on the LLM-reasoning span, computed with the same formula shape Lesson 8's `guardrail_retry_cost_per_day` and capstone #13's own `llm_cost_per_task` both use ((tokens/1,000,000) × price, summed across token types), is what makes a per-step *cost* dashboard possible, not just a per-step *latency* one.

**Worked example — the storage cost of tracing a fleet of agent sessions, and what a sampling rate buys back.** Capstone #13's own Step 2 states a p90 task takes roughly 200 LLM reasoning/tool-call round-trips — reused directly here as "spans per session," rather than inventing a conflicting figure. Say this platform runs an illustrative 3,000 sessions/day fleet-wide (consistent with, though not identical to, that capstone's own 500-*concurrent*-sessions figure), and each span's stored record (inputs, outputs, tokens, cost, timestamps) averages 2 KB:

```
sessions_per_day   = 3,000
spans_per_session  = 200     (capstone #13's own p90 round-trip count, reused directly)
kb_per_span        = 2

spans_per_day = sessions_per_day × spans_per_session
              = 3,000 × 200
              = 600,000 spans/day

full_trace_storage_gb_per_day = (spans_per_day × kb_per_span) / 1,000,000
                               = (600,000 × 2) / 1,000,000
                               = 1.2 GB/day   (tracing every span of every session)
```

At a 10% sampling rate — tracing only one in ten sessions in full detail, a real and common observability trade-off:

```
sampled_storage_gb_per_day = full_trace_storage_gb_per_day × 0.10
                            = 1.2 × 0.10
                            = 0.12 GB/day
```

Sampling trades a 10x reduction in storage (and in whatever per-event ingestion cost a hosted observability vendor charges) for not having a full trace available for 90% of sessions when something goes wrong in one of them — a real cost, since this Concept's whole premise is that you can't always predict in advance which session will need the detailed trace until after it's already misbehaved.

**Trade-offs considered:** Tracing every span of every session gives complete after-the-fact debuggability for any session that goes wrong, at a storage/ingestion cost that scales linearly with fleet size and round-trip count — the same linear-cost shape Lesson 7's Concept 1 already establishes for redundancy generally. Sampling cuts that cost proportionally but means some fraction of sessions that later turn out to matter (the ones that stalled, or produced a bad PR) were never fully traced in the first place — a real blind spot, usually mitigated in practice by combining sampling with a rule that always captures a full trace for any session that trips an error or a stall-detection signal (capstone #13's own Step 6 monitoring rule), rather than sampling uniformly at random.

**Case-study pointer:** capstone #13's (`solutions/autonomous-coding-agent`) Step 5/Step 6 are the primary anchor for this entire Concept — its `status_url` progress-reporting channel and session-state record (Step 5) are exactly the data a trace captures, and its Step 6 "progress-reporting fidelity" monitoring bullet and stalled-session detection rule ("no `plan_step_index` advancement across K consecutive sandbox-tool-call cycles") are a real, already-designed observability rule built on this Concept's trace data, not a hypothetical. Capstone #10 (`solutions/llm-inference-serving`) Step 6 is the sibling case at the serving layer: its named dashboards — KV-cache utilization %, queue depth, p50/p99 TTFT, cost per 1M tokens served — are this Concept's "latency/cost dashboards per step" half, one layer below the agent-level tracing above. Capstone #15 (`solutions/llm-api-gateway`) Step 6 adds the gateway-layer version of the same idea: cache hit rate (tracked separately by cache type), per-key/team budget burn rate, and fallback-trigger frequency per provider — all per-step, per-component dashboards in this Concept's exact shape, just at the routing layer instead of the agent-execution layer.

**Source(s) and further reading:**

- Langfuse documentation, tracing concepts (langfuse.com/docs/tracing) — confirmed via the project's own docs: traces containing nested spans, generations, and events, built on OpenTelemetry — the source of this Concept's trace/span vocabulary
- LangSmith documentation, observability concepts (docs.smith.langchain.com, docs.langchain.com/langsmith) — confirmed via the project's own docs: a "run" is defined as directly equivalent to an OpenTelemetry span, and a "trace" as the collection of runs belonging to one operation
- `solutions/autonomous-coding-agent/README.md` (capstone #13), Step 5 and Step 6 — the session-state fields, progress-reporting channel, and stalled-session monitoring rule this Concept's schema and worked example build on directly
- `solutions/llm-inference-serving/README.md` (capstone #10), Step 6 — the KV-cache-utilization/queue-depth/p50-p99-TTFT/cost-per-token dashboard set this Concept's case-study pointer cites
- `solutions/llm-api-gateway/README.md` (capstone #15), Step 6 — the cache-hit-rate/budget-burn-rate/fallback-frequency dashboard set this Concept's case-study pointer cites
- Lesson 1 (`lesson-1-ai-fundamentals-refresher.md`), Concept D2 — ReAct and plan-and-execute control-flow patterns, referenced not re-derived, as the loop shape a trace's nested spans reconstruct
- Lesson 7 (`lesson-7-application-architecture-and-security.md`), Concept 1 — the linear cost-of-redundancy shape this Concept's full-vs-sampled tracing trade-off reuses

---

## Concept 4: Prompt Versioning and A/B Testing

### Why?

Concepts 2 and 3 together give you the two things you need to ship a prompt change responsibly: a way to measure whether a candidate is actually better (Concept 2's golden set and regression gate) and a way to watch what it does once live (Concept 3's tracing). What's still missing is the deployment discipline itself: a prompt, in most real systems, changes far more often than the application code around it — and unless it's treated with the same rigor as a code deployment (a specific version, a controlled rollout, a way back out), a bad prompt edit ships to 100% of users the instant someone saves the file, with no record of what the previous version even was.

### What?

A **deployable artifact** is anything with its own version identity that gets released and can be reverted independently of the rest of the system. Treating a prompt as a deployable artifact means the prompt's exact text — not just "the code that calls the model" — gets a version identifier, a change history, and a rollback path, the same way a compiled binary or a container image does. **Prompt versioning** is the practice of giving each distinct version of a prompt's text a stable identifier (a version number, or a content hash of the text itself) so that "which exact prompt produced this output" is always an answerable, auditable question, not a guess based on when a file was last edited.

**A/B testing** is running two or more versions of something concurrently against live traffic, splitting real requests between them, and comparing a measured outcome between the groups — here, splitting traffic between a baseline prompt version and a candidate, and comparing their golden-set-style pass rates (Concept 2) or production quality signals (Concept 3), rather than only testing offline before a full rollout. **Rollback** is reverting a live system to a previous, known-working version in response to a problem with the current one — for a prompt, this means routing traffic back to the previous version identifier, which is only possible if that previous version was kept as a named, retrievable artifact rather than overwritten.

### How?

**A prompt-version config with a rollback pointer and a traffic split**, reusing Concept 2's own `v12`/`v13` pass-rate numbers directly rather than inventing a conflicting set:

```json
{
  "prompt_name": "rag_answer_generation",
  "version_id": "v13",
  "content_hash": "sha256:9f2a7c4e1b...",
  "status": "canary",
  "traffic_split_pct": 10,
  "rollback_to": "v12",
  "golden_set_pass_rate": 0.9067,
  "golden_set_n": 150
}
```

`status: "canary"` plus `traffic_split_pct: 10` means `v13` is live but handling only 10% of real traffic while its production behavior is watched (Concept 3's tracing and dashboards) — not yet trusted with the full user base. `rollback_to: "v12"` is a concrete pointer to the exact previous version to revert to the instant something looks wrong, which only works because `v12`'s own text (and `content_hash`) was kept as a separate, retrievable artifact rather than overwritten the moment `v13` was authored — modeled on LangSmith's own prompt-management system, whose documentation describes promoting a specific, hash-identified commit of a prompt through named environments (e.g. staging, then production) and pinning production traffic to one specific commit hash rather than always pulling "whatever's newest."

**Worked example — is `v13`'s apparent improvement over `v12` real, or noise?** Concept 2 computed `v12`'s golden-set pass rate as `129/150 = 0.8600` and flagged a second candidate, `v13`, at `136/150 = 0.9067` — a 4.67-point raw improvement. Before shipping `v13` to 100% of traffic on the strength of that one number, a two-proportion comparison checks whether a difference this size is likely to be a real effect or something that could plausibly happen by chance on a golden set of only 150 examples:

```
p1 = 129/150 = 0.8600       (v12's pass rate)
p2 = 136/150 = 0.9067       (v13's pass rate)
n1 = n2 = 150

pooled_p = (129 + 136) / (150 + 150) = 265 / 300 = 0.8833

standard_error = sqrt(pooled_p × (1 − pooled_p) × (1/n1 + 1/n2))
               = sqrt(0.8833 × 0.1167 × (1/150 + 1/150))
               = sqrt(0.8833 × 0.1167 × 0.01333)
               ≈ 0.0371

z = (p2 − p1) / standard_error
  = (0.9067 − 0.8600) / 0.0371
  ≈ 1.26
```

A `z`-score of **1.26** corresponds to a two-tailed p-value of roughly **0.21** — well above the conventional 0.05 significance threshold (which would need `|z|` to exceed roughly 1.96 at this sample size). In plain terms: a difference this size, on a golden set this small, is well within the range you'd expect from which 150 examples happened to land in the set, even if `v13` and `v12` were actually equally good. This is exactly why the config above keeps `v13` at a cautious **10% canary** with `v12` as a ready `rollback_to` target, rather than shipping to 100% of traffic on the raw pass-rate number alone — the config's canary status is the direct, practical consequence of this calculation, not a separate, unrelated caution.

**Trade-offs considered:** A canary rollout (a small traffic split, watched closely, before a full rollout) catches a bad prompt change while it's only affecting a small fraction of users, but it's slower to reach full confidence than shipping straight to 100% — a real cost when a genuinely better prompt is held back by extra caution. Gating every prompt change behind a formal significance check (as above) avoids shipping noise-driven "improvements" that don't actually hold up, but requires a golden set large enough to detect a real effect at the sizes that typically matter in practice — a golden set of 150 examples, as this worked example shows, isn't large enough to confidently distinguish a 4.67-point improvement from chance, which is itself an argument for growing the golden set (Concept 2's own feedback-loop point) rather than trusting a small set's raw numbers at face value forever.

**Case-study pointer:** capstone #15's (`solutions/llm-api-gateway`) Step 4 rate-limit configuration — a JSON object scoping a token-bucket config independently per API key, per team, and per model — is the structural analog this Concept's prompt-version config borrows its shape from: both are small, independently-scoped JSON configs that govern *how much* of something gets through (tokens, in capstone #15's case; traffic percentage, here) and can be adjusted or reverted per-scope without touching the rest of the system. This is a deliberate structural parallel, not a claim that capstone #15 itself does prompt versioning — that document uses "prompt" only in the context of cache-key content and request payloads (e.g. "a hashed version of the prompt for cache-key purposes," "model + full prompt + parameters"), never in the sense of versioned, deployable prompt artifacts with rollback — the same honest-framing discipline Lesson 7 and Lesson 8 already apply to their own cross-capstone analogies.

**Source(s) and further reading:**

- LangSmith documentation, prompt management (docs.langchain.com/langsmith/manage-prompts) — confirmed via the project's own docs: commit hashes identify each version of a prompt, environments (e.g. staging, production) let a specific commit be promoted deliberately, and production code can pin a specific commit hash rather than always loading "latest" — the real mechanism this Concept's `content_hash`/`status`/`rollback_to` fields are modeled on
- `solutions/llm-api-gateway/README.md` (capstone #15), Step 4 — the per-key/team/model token-bucket config this Concept's case-study pointer cites as a structural (not literal) analog
- Concept 2 of this lesson — the `v12`/`v13`/`v14` golden-set pass rates this Concept's worked example reuses directly rather than inventing a conflicting set

---

## Hands-On Walkthrough

There's no single CLI spanning G1-G4 — work through the four schemas above plus this runnable Python pipeline, which reproduces every number computed by hand in this lesson's four Concepts.

```python
# Concept 1: expected false-failure count from a naive exact-match assertion
def expected_false_failures(unrelated_commits: int, exact_match_rate: float) -> float:
    return unrelated_commits * (1 - exact_match_rate)


# Concept 2: regression-suite gate -- does a candidate's pass-rate drop exceed the allowed threshold?
def regression_gate(baseline_pass_rate: float, candidate_pass_rate: float, max_allowed_drop_pct: float = 5.0) -> bool:
    """Returns True if the candidate is allowed to ship (drop within threshold), False if blocked."""
    drop_pct = (baseline_pass_rate - candidate_pass_rate) * 100
    return drop_pct <= max_allowed_drop_pct


# Concept 3: trace/span storage cost, full tracing vs. a given sampling rate
def trace_storage_gb_per_day(sessions_per_day: float, spans_per_session: float, kb_per_span: float, sampling_rate: float = 1.0) -> float:
    spans_per_day = sessions_per_day * spans_per_session * sampling_rate
    return (spans_per_day * kb_per_span) / 1_000_000  # decimal GB


# Concept 4: two-proportion z-score, to check whether a pass-rate improvement is likely real or noise
def ab_test_z_score(pass_a: int, n_a: int, pass_b: int, n_b: int) -> float:
    p1 = pass_a / n_a
    p2 = pass_b / n_b
    pooled_p = (pass_a + pass_b) / (n_a + n_b)
    standard_error = (pooled_p * (1 - pooled_p) * (1 / n_a + 1 / n_b)) ** 0.5
    return (p2 - p1) / standard_error


# Reproduces this lesson's own worked numbers:
print(expected_false_failures(40, 0.16))                    # 33.6

print(regression_gate(0.86, 0.68))                           # False  (v14: 18-point drop, blocked)
print(regression_gate(0.86, 0.9067))                          # True   (v13: an improvement, not a drop)

print(trace_storage_gb_per_day(3_000, 200, 2))                # 1.2    (full tracing, GB/day)
print(trace_storage_gb_per_day(3_000, 200, 2, sampling_rate=0.10))  # 0.12   (10% sampling, GB/day)

print(round(ab_test_z_score(129, 150, 136, 150), 2))          # 1.26
```

Confirm for yourself: `regression_gate` returns `False` for `v14` (the 102/150 = 68% candidate) because its 18-point drop exceeds the default 5-point threshold, and `True` for `v13` (the 136/150 = 90.67% candidate) because a pass-rate *improvement* is never a "drop," regardless of whether that improvement later turns out to be statistically significant — a separate question, which is exactly what `ab_test_z_score` answers: `ab_test_z_score(129, 150, 136, 150)` returns `1.26`, the identical value Concept 4 computes by hand, confirming a two-tailed p-value around 0.21 — not below the conventional 0.05 threshold most teams require before trusting an A/B result.

---

## Summary

| Concept | One-line takeaway |
|---|---|
| G1. Why you can't unit-test an LLM | Non-determinism (Lesson 1's A1) plus genuine semantic equivalence both break exact-match assertions — a naive test can false-fail on roughly 84% of unrelated commits in this lesson's own worked example, which is why evals (scored across many examples, tolerant of correct-but-differently-phrased output) replace single assertions for freeform generation. |
| G2. Offline evaluation | A golden dataset plus LLM-as-judge scoring (over 80% agreement with human raters, per Zheng et al.'s own confirmed MT-Bench figure) resolves capstone #9's own named forward reference for generation-quality evaluation; a regression suite gates ship/no-ship on a pass-rate drop threshold (18 points blocked a candidate in this lesson's own worked example). |
| G3. Online observability | Traces (one full agent session) made of nested spans (one tool call or LLM step each, linked by `parent_span_id`) are what let an engineer localize a failure inside a multi-step run — capstone #13's own "agent going off-track for an hour" failure mode is exactly what this closes; full tracing vs. 10% sampling is a real, computed storage trade-off (1.2 GB/day vs. 0.12 GB/day in this lesson's own fleet-scale example). |
| G4. Prompt versioning and A/B testing | Treating a prompt's exact text as a versioned, hash-identified, rollback-able artifact (modeled on LangSmith's real commit/environment model) is what makes a canary rollout and a safe revert possible; a two-proportion significance check (z ≈ 1.26, p ≈ 0.21 in this lesson's own worked example) is what stops a noise-driven pass-rate bump from shipping to 100% of traffic on the strength of one small golden-set comparison alone. |

## Key Formulas & Schema/Config Reference

```
Expected false failures from exact-match flakiness (Concept 1):
  expected_false_failures = unrelated_commits × (1 − exact_match_rate)

Regression-suite gate (Concept 2):
  drop_pct = (baseline_pass_rate − candidate_pass_rate) × 100
  allowed  = drop_pct <= max_allowed_drop_pct

Trace/span storage cost (Concept 3):
  storage_gb_per_day = (sessions_per_day × spans_per_session × sampling_rate × kb_per_span) / 1,000,000

Two-proportion A/B significance check (Concept 4):
  pooled_p       = (pass_a + pass_b) / (n_a + n_b)
  standard_error = sqrt(pooled_p × (1 − pooled_p) × (1/n_a + 1/n_b))
  z              = (p_b − p_a) / standard_error
```

```json
// Concept 2 -- golden-dataset entry (generation-quality gap deferred by capstone #9)
{
  "query_id": "pto-policy-001",
  "query": "How many days of PTO do new hires accrue in their first year?",
  "golden_chunk_ids": ["chunk_4821", "chunk_4822"],
  "golden_answer": "New hires accrue 15 PTO days in their first year, prorated monthly from their start date.",
  "category": "hr-policy"
}
```

```json
// Concept 2 -- LLM-as-judge scoring output
{
  "judge_model": "claude-opus-4-5",
  "query_id": "pto-policy-001",
  "faithfulness_score": 5,
  "relevance_score": 5,
  "rationale": "Matches golden_answer's facts; phrasing differs but nothing is invented or contradicted.",
  "pass": true
}
```

```json
// Concept 3 -- trace/span schema for one agent session (built on capstone #13's own session-state fields)
{
  "trace_id": "trace-7f3a2e91",
  "session_id": "devin-session-7f3a2e91",
  "spans": [
    {
      "span_id": "span-03",
      "parent_span_id": "span-02",
      "name": "shell_tool_exec",
      "kind": "tool",
      "tokens": {"input": 3000, "output": 300},
      "cost_usd": 0.0135,
      "latency_ms": 842
    }
  ]
}
```

```json
// Concept 4 -- prompt-version config with canary traffic split and rollback pointer
{
  "prompt_name": "rag_answer_generation",
  "version_id": "v13",
  "content_hash": "sha256:9f2a7c4e1b...",
  "status": "canary",
  "traffic_split_pct": 10,
  "rollback_to": "v12",
  "golden_set_pass_rate": 0.9067
}
```

**Next:** Checkpoint 9, then Lesson 10 — scaling patterns for agentic workloads, rate limiting and token budgets, streaming responses, and cost attribution.
