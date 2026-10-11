# Capstone #13: Autonomous Coding Agent — Devin-Style Plan-and-Execute Software Engineering

**Source(s):** Primary — Cognition Labs, *"Introducing Devin,"* March 2024 (originally published at cognition.ai/blog/introducing-devin; the domain now redirects to cognition.com/blog/introducing-devin — confirmed by directly fetching the live page, not secondhand coverage). Secondary/foundational — Jiménez et al., *"SWE-bench: Can Language Models Resolve Real-World GitHub Issues?,"* ICLR 2024 (arXiv:2310.06770) — not Cognition's own source, but the benchmark's own original paper, needed here to define SWE-bench and "resolve rate" accurately rather than taking Cognition's framing of them on faith.

**Confidence:** The qualitative architecture claims — sandboxed shell/editor/browser access, the agent's ability to "plan and execute complex engineering tasks requiring thousands of decisions," and real-time progress reporting — are **(source-confirmed)**: verified by fetching the live Cognition post directly. The SWE-bench resolve-rate numbers are **also (source-confirmed)** as a direct quote, but per this document's title, they must be read as **Cognition's own reported benchmark claim, not an independently verified or peer-reviewed result** — the post itself states a more detailed technical report was still forthcoming at publication time, and no independent SWE-bench technical report from Cognition could be found as of this writing. The post also attaches an asterisk to its own headline number with two methodology caveats, confirmed directly from the page and quoted in full in Step 1's Sidebar below — this document treats those caveats as load-bearing, not as fine print to skip past. Every number *not* traceable to either source is explicitly tagged **(illustrative)** throughout, including all of Step 2's back-of-envelope figures, which Cognition's post does not publish any version of.

**Scope note:** This capstone covers an agent that autonomously plans and executes a *multi-step* software engineering task end to end — reading a codebase, running shell commands, editing files, running tests, and (per the source) using a browser, across a session that can run for minutes to hours without a human approving each individual step. It does **not** cover: training or fine-tuning the underlying LLM (this capstone treats the model as an off-the-shelf, already-trained component, the same framing capstone #10's own Scope note uses); the model-serving infrastructure underneath that LLM (capstone #10's territory, referenced not re-derived); a GUI-driven **computer-use agent** that operates a screen via screenshots and simulated mouse/keyboard input instead of direct shell/file/API access (capstone #14's distinct architecture); or the detailed mechanics of prompt injection, output-guardrail, or human-in-the-loop-approval design (Lesson 8's F1 and F4 territory, referenced not re-derived).

---

## Step 1: Clarify Requirements & Frame the ML/AI Objective

**The actual objective — multi-step autonomous task completion, not single-shot code generation.** A single-shot code-generation tool (e.g. an inline-completion assistant) takes one prompt and produces one artifact in one model call, with no execution or verification loop at all — if it's wrong, nothing inside the tool itself catches that. This capstone's actual objective is structurally different: given a coding task (a bug report, a GitHub issue, a feature request) and real access to a codebase, the agent has to autonomously decide a sequence of actions — read files, run shell commands, edit code, run tests, consult documentation — observe the result of each one, and continue until it produces a complete, verified solution, without a human approving each individual step. The source names the scale of this directly **(source-confirmed)**: Devin is described as able to "plan and execute complex engineering tasks requiring thousands of decisions," "recall relevant context at every step, learn over time, and fix mistakes." The objective being optimized is therefore end-to-end task completion across many sequential decisions, not the quality of any single generated artifact.

**What counts as ground truth / feedback signal — two different bars, not one.**

1. **Benchmark ground truth: SWE-bench resolve rate.**

   **Sidebar — SWE-bench and resolve rate.** *(First appearance in this repo of either concept; it isn't classic infra Lessons 3-7 curate down to, and it isn't already taught in Lesson 1 either, so this gets the full inline Sidebar treatment plus a glossary entry, rather than a lesson link that doesn't exist.)*
   - **Why?** A model's own claim that it "fixed a bug" is meaningless without an objective, automatable way to check whether the fix actually works — the AI-agent equivalent of the question Lesson 1's Concept A1 already raises generally (non-determinism means you can't just eyeball one output and call it done).
   - **What?** **SWE-bench** is a benchmark, from Jiménez et al.'s ICLR 2024 paper, consisting of **2,294 real GitHub issues** drawn from **12 popular open-source Python repositories**, each one paired with the actual human-written pull request that originally fixed it. A model is given the issue description and the repository at the commit just before the fix, and has to produce its own patch. **Resolve rate** is the percentage of a benchmark's tasks a model's patch actually "resolves" under the benchmark's own grading criterion — for SWE-bench specifically, grading is **test-based, not a human or LLM judgment of whether the patch looks right**: the candidate patch is applied and the repository's real test suite is run; the task counts as resolved only if every test that was failing before the fix ("fail-to-pass" tests) now passes, *and* no test that was already passing before the fix ("pass-to-pass" tests) is broken by it. A single regression anywhere fails the whole task.
   - **How?** Applied to this capstone: Cognition's own announcement reports Devin's resolve rate on SWE-bench as the headline evidence for its multi-step-task-completion capability (Step 6 covers the exact figures and their caveats). Nothing about SWE-bench's own grading mechanism is Cognition-specific — it's the benchmark's own, independently defined pass/fail rule, applied here to one particular agent's submitted patches.

2. **Real-world ground truth: a PR that actually passes CI and gets merged.** SWE-bench's test-based grading is strictly narrower than what a real engineering team actually requires before merging a fix — a human reviewer also judges code style, whether the fix addresses the issue's actual intent (not just its symptom), and whether it introduces any risk the existing test suite doesn't happen to cover. A patch can pass every fail-to-pass and pass-to-pass test in SWE-bench's grading and still be a fix a human reviewer would reasonably reject. This capstone treats "a PR that passes CI and is accepted by a human reviewer" as the stricter, real-world bar that SWE-bench resolve rate is a cheaper, scalable, but genuinely narrower proxy for — not a replacement for it.

**Explicitly out of scope:** training or fine-tuning the underlying LLM; the GPU/model-serving layer underneath it (capstone #10); a screenshot-driven computer-use control loop (capstone #14); the internal mechanics of prompt-injection defense or output guardrails (Lesson 8's F1/F4, referenced not re-derived); evaluating output quality/safety in the general LLM-content sense (Lesson 9's territory).

**Trade-offs considered:** Framing the objective around multi-step completion rather than single-shot generation accepts a fundamentally larger failure surface — a single-shot generator either gets its one answer right or wrong in one model call's worth of risk, while a multi-step agent can go wrong at any one of dozens or hundreds of individual decisions, and those per-step error rates compound (Step 4 below makes this compounding concrete with real numbers, since it's also this capstone's central model-design trade-off, not just a Step 1 framing note). Choosing SWE-bench resolve rate as the primary offline metric buys a reproducible, automatable, test-based pass/fail signal that doesn't require a human reviewer for every evaluation run — but it's also a narrow slice of real engineering work (Python repositories only, issue-shaped tasks only, no architecture or design work, no code review of the *fix's* quality beyond "do the named tests pass") — which is exactly why this capstone also names the stricter CI-plus-human-review bar above rather than treating SWE-bench resolve rate as if it were a complete measure of "can this agent do a software engineer's job."

---

## Step 2: Back-of-Envelope Constraints

Lesson 7's Concept 4 defines a five-step back-of-envelope method (state assumptions, decompose, compute with units, sanity-check the order of magnitude, name the most sensitive assumption) specifically so it doesn't have to be re-derived in "capstone #9, #12, #13, or any future one" — its own words, naming this capstone directly. Applied here, not re-derived:

**Step 1 — state assumptions explicitly (all illustrative; Cognition's post confirms "multi-hour" capability as a general claim but publishes no task-duration distribution, concurrency figure, or cost figure):**
- A platform-wide fleet running **500 concurrent active agent sessions** at any given moment.
- **Task duration distribution:** median 20 minutes, p90 90 minutes, p99 240 minutes (p90/p99 — the 90th- and 99th-percentile duration: 90%, respectively 99%, of sessions finish faster than this — defined in full in Lesson 9's Concept 2). The p90 figure is deliberately the same 90-minute task Lesson 6's Concept 4 already used as its own illustrative example of a task that can't be served over one synchronous connection — reused here on purpose, for the same reason capstone #9 reused Lesson 6's 2,000,000-chunk figure rather than inventing a conflicting number.
- **Sandbox resource budget per session:** 4 vCPUs, 8 GB RAM, 20 GB disk — sized for a full dev environment (shell, editor, browser, and whatever language toolchain the target repo needs), not a single stateless tool call.
- **Round-trips per task:** ~200 LLM reasoning/tool-call round-trips for a 90-minute (p90) task.
- **Tokens per round-trip:** 3,000 input / 300 output tokens, at the same illustrative $3/1M-input, $15/1M-output pricing Lesson 7's own Concept 4 worked example already used, reused here for consistency rather than picking a new number.
- **Sandbox compute cost:** $0.20/hour (illustrative order-of-magnitude for a mid-size cloud VM/container).

**Step 2 — decompose:**
```
fleet_vcpu_needed      = concurrent_sessions × vcpu_per_session
fleet_ram_needed       = concurrent_sessions × ram_per_session
llm_cost_per_task      = (round_trips × input_tokens_per_rt  / 1,000,000) × input_price
                        + (round_trips × output_tokens_per_rt / 1,000,000) × output_price
sandbox_cost_per_task  = task_duration_hours × hourly_sandbox_rate
total_cost_per_task    = llm_cost_per_task + sandbox_cost_per_task
```

**Step 3 — compute step by step, carrying units:**
```
fleet_vcpu_needed = 500 sessions × 4 vCPU/session   = 2,000 vCPUs
fleet_ram_needed  = 500 sessions × 8 GB/session     = 4,000 GB RAM

(at the p90, 90-minute task, 200 round-trips)
input_tokens  = 200 round-trips × 3,000 tokens/round-trip  = 600,000 tokens  = 0.6M tokens
output_tokens = 200 round-trips ×   300 tokens/round-trip  =  60,000 tokens  = 0.06M tokens

llm_cost_per_task     = 0.6 × $3  +  0.06 × $15
                      = $1.80  +  $0.90
                      = $2.70

sandbox_cost_per_task = 1.5 hours × $0.20/hour = $0.30

total_cost_per_task   ≈ $3.00
```

**Step 4 — sanity-check the order of magnitude.** 2,000 vCPUs / 4,000 GB RAM of fleet-wide sandbox capacity is the same order of magnitude as a mid-size production Kubernetes cluster — plausible for a platform running hundreds of concurrent agent sessions, not an obvious order-of-magnitude error in either direction. Separately: running the full SWE-bench benchmark once (2,294 tasks, per Step 1's Sidebar — the benchmark's own confirmed task count) at this document's own ≈$3/task figure costs roughly `2,294 × $3 ≈ $6,882` — a plausible R&D compute cost for one evaluation pass, not a number that's off by orders of magnitude in either direction (not "$7" and not "$7 million"), which is this step's actual job: catching a mistake that size, not confirming Cognition's own real spend.

**Step 5 — name the assumption the answer is most sensitive to.** The **200-round-trips-per-task** figure is the most sensitive input in this whole estimate, and it's also the one number this document has the least grounding for: Cognition's own post gives no visibility into actual tool-call counts, only the qualitative claim that a task can require **"thousands of decisions"** (source-confirmed, Step 1). If a 90-minute task actually involves closer to 2,000 round-trips rather than 200 — entirely consistent with "thousands of decisions" — the LLM-cost term alone scales to roughly $27, swamping the $0.30 sandbox-compute term by nearly two orders of magnitude and pushing total cost per task from ≈$3 to ≈$27+. That's the number worth measuring first in a real prototype, not the sandbox compute budget.

**Trade-offs considered:** Provisioning a generous per-session sandbox budget (4 vCPU/8 GB) protects against a task that needs to run a heavy build or large test suite, but at 500 concurrent sessions that's 2,000 vCPUs/4,000 GB of fleet-wide reserved capacity, most of which sits idle during the many round-trips where the sandbox is simply waiting on an LLM response rather than executing anything — the same safety-margin-vs-fleet-cost trade-off Lessons 3 and 7 already establish generally, now sized concretely for this workload. Using a flat per-round-trip token estimate is also a simplification that understates real cost for long tasks: context accumulates as the agent's plan history and tool outputs grow (Lesson 1's Concept A2, context window as a resource, applies directly here), so a round-trip late in a 90-minute task costs strictly more tokens than one early in it — meaning this step's $2.70 figure should be read as a conservative floor, not a ceiling, independent of Step 5's own sensitivity finding above.

---

## Step 3: Data / Knowledge Pipeline

**What context the agent needs, mapped to concepts this repo already defines:**
- **Repository structure** — the file tree and, typically, a searchable index over file/symbol names, so the agent can locate relevant code without reading the entire repository into context on every step.
- **The issue/task description** — the natural-language input defining what "done" means for this run.
- **Relevant code** — located via the same retrieval mechanics Lesson 1's Concepts C1-C2 already define in full (embeddings, vector/keyword search), just applied to source code instead of a document corpus; this document doesn't re-derive that mechanism, only names where it comes from.
- **Test results as a feedback signal** — the single most important piece of context that a one-shot generator never gets and this agent depends on structurally: running the test suite mid-task tells the agent, with actual ground truth, whether its last edit helped or broke something, which is exactly the "observe the result of an action" half of the control-flow patterns Lesson 1's Concept D2 already names (detailed in Step 4 below).

**How context stays current across a long-running session — the one genuine difference from a RAG chatbot's corpus.** Capstone #9's RAG pipeline (`case-studies/rag-contextual-retrieval`) retrieves from a corpus that's largely static *during* any single query — it changes slowly, on its own schedule, independent of any one conversation. This capstone's "corpus" — the repository's actual file contents — is instead mutated by the agent's *own actions* turn over turn: every file edit and every test run changes the ground truth the next planning step has to reason about. Context here can't be fetched once up front and reused; each new step's context has to reflect the repository's current state, not its state when the task started. This is also exactly why **state/checkpointing** (Lesson 1's Concept E3, already fully defined there — referenced, not re-derived) is a structural requirement rather than a nice-to-have the moment a session can run for the 90+ minutes Step 2 assumes: if the process running the agent crashes or is interrupted at minute 70 of a 90-minute task, the alternative to checkpointing is re-running everything from minute 0, including every already-applied file edit and every already-passed test, which is both slow and risks re-applying an edit that's already been made.

**A real session-state record, showing exactly what "staying current" looks like concretely** (this is deliberately richer than Lesson 6's own task-queue job schema — `task_id`/`status`/`attempt_count` — since that schema tracks one discrete unit of work, while this one tracks an entire multi-step session's evolving state; Step 5 below reuses Lesson 6's schema for the individual steps *inside* this session):

```json
{
  "session_id": "devin-session-7f3a2e91",
  "repo_url": "https://github.com/example-org/example-repo",
  "issue_description": "TypeError raised when parsing a config file with a trailing comma in its JSON array.",
  "status": "running",
  "created_at": "2026-01-14T09:00:00Z",
  "sandbox_id": "sbx-c9e21a",
  "plan": [
    {"step_index": 0, "description": "Reproduce the reported error with a minimal test case", "status": "succeeded"},
    {"step_index": 1, "description": "Locate the JSON-parsing code path in src/config_loader.py", "status": "succeeded"},
    {"step_index": 2, "description": "Patch the parser to tolerate trailing commas; re-run the full test suite", "status": "running"},
    {"step_index": 3, "description": "Open a pull request with the fix and a regression test", "status": "pending"}
  ],
  "current_step_index": 2,
  "last_test_run": {"passed": 142, "failed": 1, "ran_at": "2026-01-14T09:41:00Z"},
  "last_progress_update_at": "2026-01-14T09:41:05Z",
  "max_duration_minutes": 120
}
```

`plan` is the full upfront plan from Step 4's control-flow design — not just the current step — which is what makes "staying current" auditable: a client reconnecting mid-session can see exactly which steps already succeeded, not just a single "in progress" status. `last_test_run` is the concrete test-results-as-feedback-signal field named above — `current_step_index`'s plan step reasons about its next action using this field's actual, current content, not a cached assumption from when the plan was first generated. `sandbox_id` ties this session to the specific sandboxed execution environment (Step 5) actually running its shell/editor/browser actions. `max_duration_minutes` is the session's own timeout — the mechanism that bounds the "went off-track for an hour before anyone noticed" failure mode Step 6 covers directly.

**Trade-offs considered:** Re-fetching and re-indexing the full repository state before every single planning step guarantees the agent never reasons about stale file contents, but is wasteful when most steps only touch one or two files — versus incrementally updating only the files a step's own action actually changed (the design implied by the schema above), which is cheaper per step but relies on the agent's own action log being complete and accurate; a missed or mis-recorded action could leave the agent reasoning about a file it believes is unchanged when it isn't. Storing the full plan array (rather than just the current step) in session state makes progress genuinely auditable and resumable after a crash, at the direct cost of session-state size growing with plan length — a real, if small, storage and transfer cost that a single-field "current status" design wouldn't have.

---

## Step 4: Model/Agent Core Design — the Plan-Then-Execute Loop as an Explicit Trade-off

**A terminology note worth being explicit about, in the spirit of this repo's own existing discipline around stale or inconsistent references (Lesson 6's Concept 4 flags exactly this kind of discrepancy for a different term):** Devin's architecture is sometimes described as a "plan-then-execute loop." Lesson 1's Concept D2 names the identical control-flow pattern **plan-and-execute**. These are the same pattern under two slightly different names — not two different patterns — and this document uses Lesson 1's own established terminology from here on, linking to that existing lesson Concept rather than re-teaching or re-naming it. Lesson 1's own full definition, referenced and not re-derived here: *"a control-flow pattern where the model first produces a full multi-step plan up front (before taking any actions), and only then executes each step in sequence — optionally revising the plan if a step's result changes what's needed — in contrast to ReAct's one-step-at-a-time reasoning."*

**Devin's own architecture, mapped onto that definition.** Cognition's post itself never uses Lesson 1's control-flow vocabulary at all — it describes the behavior ("plan and execute complex engineering tasks," "recall relevant context at every step... and fix mistakes") without naming its own control-flow pattern. Mapping that description onto plan-and-execute is this document's own reasoned categorization, not a claim that Cognition's post itself uses that term. One structural detail matters for that mapping: the quoted phrase "fix mistakes" implies an observe-and-correct step happening *during* execution, not a single fixed plan blindly executed start to finish with no checking in between — which makes Devin's actual loop (as best this document can characterize it from the source) a **hybrid**: an outer plan-and-execute structure (a real upfront plan exists and gets referenced throughout, as Step 3's session-state schema shows directly) wrapped around an inner, per-step observe-and-adjust behavior closer to what Lesson 1's Concept D2 separately names **reflection**. This is a deliberate design choice, not an oversight — Step 4's "Why this beats pure open-loop execution" below is the concrete argument for why.

**The trade-off, stated against two real alternatives, not presented as the only option:**

1. **Single-shot generation** (no control loop at all — one model call produces one complete diff, with no execution or test-running step afterward). Cheapest and fastest by far, and carries zero risk of the multi-hour runaway-session failure mode Step 6 covers. But it's structurally incapable of the task this capstone is actually scoped to (Step 1): it never runs a single test, never observes a single real result, and has no mechanism to recover from being wrong about the codebase's actual current state. Not a real contender for this capstone's own objective — included here only because it's the alternative every other option in this list is implicitly being compared against.

2. **A tight ReAct loop with no explicit upfront plan** (Lesson 1's Concept D2, referenced not re-derived: one-step-at-a-time reasoning, action, observation, repeat). More flexible moment-to-moment than committing to a plan up front — it can react immediately to a surprising result with no stale plan to revise or discard. But it has no natural artifact to report back to the user as "here's what I'm doing and why" (Cognition's own confirmed "reports on its progress in real time... works together with you through design choices as needed" — source-confirmed) short of narrating each individual step after the fact, and it gives up the auditability a stated-up-front plan provides: there's no single place to look to see "is this on track," only a trailing history of individual actions already taken.

3. **Plan-and-execute, with per-step observation** (this capstone's actual design, per the mapping above). The upfront plan is literally the artifact Step 3's `plan` field reports progress against and the thing a human reviewer (Step 1's real-world ground truth) can inspect mid-session to judge whether the agent's approach makes sense *before* it's finished — a real, structural advantage for the "continuous progress reporting" requirement Step 5 has to deliver on. The cost: a plan can become wrong once execution reveals something the plan didn't anticipate (e.g. step 2 discovers the bug isn't where step 1 assumed), which is exactly why "optionally revising the plan" is part of Lesson 1's own definition rather than an edge case — a plan-and-execute agent that can't revise its plan when reality disagrees with it is strictly worse than ReAct at handling surprises, not just differently flexible.

**Why this beats pure open-loop execution — the compounding-error math that makes "fix mistakes" load-bearing, not decorative.** Suppose a task decomposes into `n` sequential decisions, each independently correct with probability `p`, and — critically — suppose there's *no* per-step observation or correction at all: a genuinely open-loop design that commits to and blindly executes a fixed plan with no checking in between. The probability of the entire task completing with zero mistakes is:

```
P(task succeeds, no correction) = p^n
```

At `p = 0.95` (a 95% per-step success rate — already a strong per-step rate) and `n = 50` decisions (a conservative fraction of the "thousands of decisions" the source itself claims a full task can require):

```
P(success) = 0.95^50 ≈ 0.077   →   roughly a 7.7% chance of a fully clean run
```

A 95%-reliable-per-step agent, with no way to catch and fix its own mistakes along the way, would complete a 50-decision task cleanly less than 8% of the time — and that's before accounting for Cognition's own claim of tasks requiring *thousands*, not 50, decisions, which would push `p^n` far closer to zero. **This is an illustrative sanity check, not a claimed explanation of Cognition's actual reported figure** — it is not being presented as deriving the real 13.86% SWE-bench number (Step 6), only as showing why a resolve rate in that rough single-digit-to-low-double-digit range is unsurprising, even expected, for a task shape with this many sequential decisions, rather than being a sign that this particular agent is unusually bad at its job. It's also the concrete reason the "fix mistakes" half of the source's own description (observation and per-step correction, not blind plan execution) isn't an optional nicety: without it, `p^n` makes long multi-step autonomy essentially unachievable at any plausible single-step reliability.

**Trade-offs considered:** Single-shot generation and a plan-free ReAct loop are both real, cheaper alternatives for shorter or simpler tasks — this capstone's commitment to a plan-and-execute-with-observation hybrid is specifically a consequence of the task shape Step 1 scoped (multi-hour, many-decision, requiring real execution feedback), not a universal claim that plan-and-execute beats ReAct or single-shot generation in general; Lesson 1's own Concept D2 is explicit that this is a real trade-off (predictability vs. flexibility), not one pattern being strictly better. Building in per-step observation and plan revision (rather than a pure, non-revisable upfront plan) adds real complexity — the agent now needs logic for "is my current plan still valid," not just "execute the next step" — but per the compounding-error math above, skipping it isn't a simpler version of the same design, it's a design that's mathematically unlikely to complete a long task at all.

---

## Step 5: Serving Architecture

This step exists specifically to deliver on three concrete promises other, already-written documents in this repo made about this capstone before it existed. Each is quoted directly, then made concrete.

**Delivering on Lesson 6's Concept 4 promise — why this can't be one synchronous REST request.** Lesson 6's Concept 4 states directly: *"Capstone #13's autonomous coding agent is capable of 'multi-hour autonomous task completion' — take a conservative 90-minute (5,400-second) task as an illustrative example: `timeout_ratio = task_duration / typical_gateway_idle_timeout = 5,400 / 60 = 90x`."* This capstone's own Step 2 assumptions (p90 task duration = 90 minutes) were chosen specifically to match that figure exactly, rather than introduce a second, conflicting number — the two documents describe the same system. A task running 90x longer than AWS ALB's documented 60-second default idle timeout (Lesson 6's own cited source) cannot be held open as one synchronous request; the gateway kills the connection long before the task finishes, regardless of what the agent or backend want. Per Lesson 6's own decomposition, reused directly here as this capstone's actual design:

```
Client (IDE plugin / web UI)
   │
   │ 1. POST /v1/tasks   (REST — fast, well under any gateway timeout)
   ▼
API gateway  ──────────────────────────────►  Task queue (Lesson 6, Concept 1)
   │  returns 202 Accepted + task_id              one entry = one coding-agent session
   │  immediately, connection closes                       │
   ▼                                                        ▼
Client polls / subscribes:                          Orchestrator worker pool
GET /v1/tasks/{id}/status                           pulls a session, runs the
  or a streamed/webhook channel  ◄───────────────    plan-and-execute loop (Step 4)
  ("continuous progress reporting")                  inside a per-session sandbox
                                                             │
                                                             ▼
                                              Sandboxed compute environment
                                         (shell tool | editor tool | browser tool —
                                          three separately-scoped credentials, below)
```

```
POST /v1/tasks HTTP/1.1
Host: api.example.com
Content-Type: application/json

{"repo_url": "https://github.com/example-org/example-repo", "issue_description": "...", "max_duration_minutes": 120}
```
```
HTTP/1.1 202 Accepted
{"task_id": "devin-session-7f3a2e91", "status": "queued", "status_url": "/v1/tasks/devin-session-7f3a2e91/status"}
```

The submit call is REST-shaped and returns in milliseconds; everything that actually takes 90 minutes runs entirely inside the task queue's worker, decoupled from that one request/response pair — exactly Lesson 6's own three-part decomposition: "(1) a REST-shaped call that submits the task and immediately returns a task ID..., (2) a task queue running the actual multi-step agent loop as a background job..., and (3) a separate channel... for... 'continuous progress reporting.'" The `status_url` above is that third channel — the client polls `GET /v1/tasks/{id}/status` (or subscribes to a stream/webhook) and receives exactly the session-state record Step 3 already defined, which is what makes that record double as both this capstone's internal state *and* the external progress-reporting payload, rather than needing two separate schemas for the same information.

**Delivering on Lesson 6's Concept 1 promise — the agent's own steps as a task queue underneath the session.** Lesson 6's Concept 1 states directly: *"Capstone #13... is this Concept's sibling pattern one layer up: its 'plan-then-execute loop'... naturally decomposes into a task queue of individual agent steps (a shell command, a file edit, a test run), each one a discrete, retryable, idempotency-sensitive unit of work in the same shape as an embedding task."* Concretely: each entry in Step 3's `plan` array, once it's the orchestrator's turn to execute it, is itself enqueued as one task-queue job, reusing Lesson 6's own job schema fields directly (`task_id`, `status`, `attempt_count`, `max_attempts`) rather than inventing a second shape for the same concept:

```json
{
  "task_id": "step-7f3a2e91-02",
  "session_id": "devin-session-7f3a2e91",
  "plan_step_index": 2,
  "tool": "shell",
  "action": "pytest tests/ -k config_loader",
  "status": "running",
  "attempt_count": 0,
  "max_attempts": 2
}
```

Idempotency matters exactly as it did for capstone #9's embedding tasks (Lesson 6, Concept 1), but the specific risk differs by tool: re-running a `shell` action like a test command is typically safe to retry (running the same test suite twice doesn't corrupt anything), but re-running an `editor` action that applies a diff is *not* automatically safe — applying the same patch twice can fail outright or silently corrupt the file, which is why a real implementation has to check the file's current state (not just blindly retry) before reapplying an edit action, a distinction a plain shell-command retry doesn't need to make.

**Delivering on Lesson 7's Concept 3 promise — least privilege scoped per tool, not one undifferentiated credential.** Lesson 7's Concept 3 states directly: *"Capstone #13 grants 'sandboxed shell/editor/browser access' and explicitly notes this 'raises the sandboxing stakes from Group F' — each of those three distinct tools (shell, editor, browser) is exactly the kind of access that should be scoped to least privilege individually (a browser tool has no legitimate need for filesystem-delete access, for instance) rather than granted as one undifferentiated 'full dev environment' credential."* This capstone's own design confirms that inference directly, rather than overriding it — three separate scoped tool configurations, not one:

```json
{
  "shell_tool":   {"filesystem": "read-write:/workspace/repo", "network": "none",                          "max_runtime_sec": 120},
  "editor_tool":  {"filesystem": "read-write:/workspace/repo", "network": "none",                          "max_file_size_mb": 10},
  "browser_tool": {"filesystem": "none",                       "network": "allowlist:docs-and-registries-only", "no_shell_exec": true}
}
```

The `browser_tool` can reach the public internet (within an allowlist) but has no filesystem access at all and is explicitly barred from executing shell commands — the concrete form of Lesson 7's own example ("a browser tool has no legitimate need for filesystem-delete access"). The `shell_tool` and `editor_tool` can both touch the workspace but neither has open network access, since neither's job requires it. If any one tool's credential is ever leaked or hijacked (e.g. via a prompt-injection attack through a malicious web page the browser tool reads — Lesson 8's F1, not re-taught here), the blast radius (Lesson 7's own Concept 1 term, referenced not re-derived) is bounded to exactly that one tool's scope, not the full dev environment.

**Sandbox resource limits — the config underneath Step 2's own illustrative budget.** An illustrative, Docker-style resource-limit config for one session's sandbox, sized to Step 2's own per-session assumptions:

```json
{
  "cpu_limit": "4",
  "memory_limit": "8g",
  "pids_limit": 512,
  "disk_limit": "20g",
  "network_mode": "none-except-allowlist",
  "timeout_seconds": 7200
}
```

`pids_limit` caps the number of simultaneous OS processes the sandbox can spawn — a real guard against a single runaway or malicious shell command forking enough processes to exhaust the host's process table, independent of the CPU/memory limits above it. `timeout_seconds` (7,200s = 120 minutes) is the sandbox-level enforcement of Step 3's own `max_duration_minutes` field — two different layers each independently enforcing the same ceiling, so a bug in the session-state logic doesn't leave a sandbox running forever on its own.

**Why this "raises the sandboxing stakes" from Group F specifically, with a number, not just an assertion.** Lesson 8's Group F covers this directly: **F2** covers sandboxing a single agent's execution (hands-on, via `learn-docker-ai-agents` Lesson 1's `sbx`/microVMs — a lightweight, hardware-virtualized sandbox isolating one untrusted workload from the host and from other sandboxes); **F5** covers **multi-tenant isolation** — keeping one agent platform's many different customers' data and credentials from leaking into each other, when one platform serves them all on shared infrastructure. This capstone combines both concerns at once, and at a higher stake than either alone: a coding-agent sandbox doesn't just execute one-off, stateless tool calls (F2's baseline case) — it holds a real customer's actual source code, and that source code routinely contains real secrets (API keys in config files, database credentials in `.env` files, CI tokens), for a session that persists for up to Step 2's full 240-minute p99 duration, on a platform (F5's exact concern) serving many different customers' repositories concurrently. An illustrative, not sourced, blast-radius calculation in the same shape as Lesson 7's own 50x credential-leak example: if sandboxes are fully tenant-isolated (one customer's repo and credentials per physical sandbox), a single sandbox escape reaches exactly one customer's data. If sandboxes were instead bin-packed for infrastructure efficiency — say, 20 tenant sandboxes co-located on one physical host, sharing a kernel or hypervisor layer that a sufficiently severe escape could break out of — the same escape could reach all 20 co-located tenants' repos and credentials at once:

```
blast_radius_ratio = co_located_tenants_reachable / tenant-isolated_baseline = 20 / 1 = 20x
```

The identical sandbox vulnerability is a 20x larger incident purely because of the co-location decision — nothing about the vulnerability itself changed, only the ceiling on what it could reach, the same shape of conclusion Lesson 7's own least-privilege worked example reaches for a leaked credential rather than a sandbox escape.

**Trade-offs considered:** Decomposing each plan step into its own task-queue job (this step's second delivery) gives per-step retry and status tracking for free, at the cost of task-queue overhead on every individual shell command or file edit — overhead that's negligible against a multi-minute LLM round-trip but would be wasteful for a sub-millisecond operation, which is exactly why this pattern fits an agent's own tool calls (seconds to minutes each) and wouldn't fit, say, a tight in-process loop incrementing a counter. Scoping three separate least-privilege tool credentials (this step's third delivery) is more configuration to define and keep correct than one shared "full dev environment" grant, and every new tool added to the agent means a new scoped credential to design from scratch — but per the blast-radius math above, the alternative's convenience is bought at a cost that grows directly with how many tenants' sessions end up co-located, which is a cost that compounds with platform scale rather than staying fixed. Full per-tenant sandbox isolation (no co-location at all) eliminates the 20x exposure above entirely, at the direct infrastructure cost of lower bin-packing efficiency — the same isolation-vs-density trade-off any multi-tenant platform has to make, not one this capstone invents.

---

## Step 6: Evaluation, Monitoring, and Iteration

**Offline evaluation — SWE-bench resolve rate, with the honest framing this capstone's title commits to.** Cognition's own post reports, as a direct quote confirmed by fetching the page **(source-confirmed)**: Devin "correctly resolves 13.86%* of the issues end-to-end, far exceeding the previous state-of-the-art of 1.96%," and separately that prior models given the exact files to edit (an easier, assisted setup) "can only resolve 4.80% of issues." The asterisk on the headline figure attaches two caveats, both confirmed directly from the page rather than assumed **(source-confirmed)**: the evaluation ran on "a random 25% subset of the dataset," not the full 2,294-task benchmark; and "Devin was unassisted, whereas all other models were assisted" — meaning the comparison pits an agent that had to *locate* the relevant files itself against baselines that were simply told which files to edit, a harder task for Devin's side of the comparison, which cuts in favor of the reported gap being real rather than inflated by an easier setup on Devin's side, but it also means the 13.86% figure and the 1.96%/4.80% baselines were not measured under identical task framing — not an apples-to-apples resolve-rate comparison in the strictest sense. **Per this document's Confidence note, this 13.86% figure must be read as Cognition's own reported benchmark claim, not as an independently verified or peer-reviewed result** — no independent replication or Cognition-published technical report could be confirmed as existing at the time of writing.

**Online monitoring, mapped directly to Step 3's session-state fields and Step 5's architecture:**
- **Progress-reporting fidelity** — are `status_url` polls / stream updates actually reflecting `current_step_index` and `last_test_run` in near-real-time, the concrete form of the source's own confirmed "reports on its progress in real time" claim; a stale or lagging status feed defeats the entire point of the async architecture Step 5 built.
- **Intervention and cancellation mid-task** — a human has to be able to pause, redirect, or kill a running session before it finishes, not only inspect it after the fact (the concrete operational need behind Lesson 8's F4, "human-in-the-loop approval gates"). Concretely: a `DELETE /v1/tasks/{id}` endpoint that terminates the session's sandbox and marks its status `cancelled`, and/or an approval gate before specific high-risk plan steps (e.g. anything that pushes to a remote branch) execute at all.
- **Task-duration and cost distributions against Step 2's assumptions** — real measured p50/p90/p99 durations and real measured cost-per-task, tracked the same way capstone #10's Step 6 tracks its own SLA targets against real measurements, to catch Step 2's own flagged sensitivity (the round-trip-count assumption) drifting from reality.
- **Sandbox resource utilization against the limits in Step 5** — a session consistently hitting its `pids_limit` or `memory_limit` is a real signal the Step 2 budget is undersized for some class of repository, not necessarily a sign of a malicious or buggy session.

**The specific failure mode this capstone has to design against: an agent going off-track for an hour before anyone notices.** Nothing about a long-running, autonomous, multi-step loop guarantees it notices its own drift — a plan step can keep "succeeding" by the agent's own account while making no real forward progress (e.g. repeatedly editing the wrong file, or a flaky test making `last_test_run` bounce between pass and fail with no underlying progress). Three layered defenses, all already present in this capstone's own design rather than bolted on separately: `max_duration_minutes` (Step 3) and `timeout_seconds` (Step 5) bound the absolute worst case; a monitoring rule flagging "no `plan_step_index` advancement across K consecutive sandbox-tool-call cycles" catches a *stalled* session well before its hard timeout, distinct from a *failing* one; and the human intervention/cancellation path above is what a flagged, stalled session actually escalates to, rather than silently running to its timeout regardless.

**The feedback loop back into Step 3.** Sessions that time out, get manually cancelled, or produce a PR a human reviewer rejects (Step 1's stricter real-world ground truth) are exactly the cases worth reviewing for patterns — a recurring reason a plan goes stale, a repo structure the retrieval step consistently handles badly, a tool-permission boundary (Step 5) that blocked a legitimate action and forced an unnecessary failure. That review feeds back into the retrieval/context-construction step (Step 3) and the plan-generation prompting (Step 4), the same "route real production failures back into the thing that needs fixing" shape capstone #9's own Step 6 feedback loop already follows, just applied to agent sessions instead of a retrieval eval set.

**Trade-offs considered:** Auto-cancelling a session the moment it looks stalled (e.g. no plan advancement for 10 minutes) saves compute and avoids a silent hour-long drift, but risks killing a session that was actually in the middle of a slow-but-legitimate step — a large test suite or a slow network call to a package registry — a real false-positive risk in the same shape as Lesson 7's own health-check interval-vs-threshold trade-off (too aggressive a threshold detects real problems fast but also flags transient, harmless slowness). Requiring full human review before merging every agent-produced PR is the safest option against Step 1's stricter real-world bar, but doesn't scale once the agent succeeds often enough that review itself becomes the throughput bottleneck instead of task generation; auto-merging any PR that passes CI is faster but risks exactly the gap Step 1 named between SWE-bench's test-only grading and a human reviewer's broader judgment — a technically test-passing fix that's still substantively the wrong fix. Neither extreme is correct in general; which one a real deployment picks depends on how costly a wrong-but-passing merge actually is for that specific codebase, which is a business decision this capstone's own architecture doesn't make for it.

---

## Source(s) and Further Reading

- Cognition Labs, *"Introducing Devin,"* March 2024 (cognition.com/blog/introducing-devin, redirected from the original cognition.ai domain) — **primary**; confirmed by directly fetching the live page. Source of the sandboxed shell/editor/browser access claim, the "plan and execute complex engineering tasks requiring thousands of decisions" and "recall relevant context at every step, learn over time, and fix mistakes" quotes, the real-time progress-reporting claim, and the SWE-bench resolve-rate figures (13.86% / 1.96% / 4.80%) together with their asterisked methodology caveats (25% random subset; Devin unassisted vs. baselines assisted) — all treated per this document's Confidence note as Cognition's own reported benchmark claim, not an independently verified result. No independent Cognition SWE-bench technical report could be confirmed as published as of this writing.
- Jiménez, Yang, Wettig, Yao, Pei, Press, Narasimhan, *"SWE-bench: Can Language Models Resolve Real-World GitHub Issues?,"* ICLR 2024 (arXiv:2310.06770) — **primary** (for the benchmark's own definition, not for any Devin-specific claim); the source of SWE-bench's own task count (2,294 issues, 12 Python repositories) and its fail-to-pass/pass-to-pass test-based grading criterion, used in Step 1's Sidebar to define SWE-bench and resolve rate independently of Cognition's own framing of them.
- Lesson 1 (`lessons/lesson-1-ai-fundamentals-refresher.md`), Concept D2 — the original full definition of plan-and-execute (and ReAct, and reflection), referenced rather than re-derived throughout Step 4; Concept E3 — state/checkpointing, referenced in Step 3; Concept A2 — context window as a resource, referenced in Step 2's trade-offs; Concepts C1-C2 — embeddings/retrieval, referenced in Step 3 for code-context lookup.
- Lesson 6 (`lessons/lesson-6-async-and-communication.md`), Concept 1 — the task-queue job schema and idempotency discipline this capstone's Step 5 reuses directly for individual plan steps; Concept 4 — the REST-submit/task-queue/progress-channel decomposition and the 90x timeout-ratio argument this capstone's Step 5 confirms rather than overrides.
- Lesson 7 (`lessons/lesson-7-application-architecture-and-security.md`), Concept 1 — blast radius, referenced in Step 5; Concept 3 — least privilege, the per-tool-scoped-credential design this capstone's Step 5 confirms directly; Concept 4 — the five-step back-of-envelope method this capstone's Step 2 applies rather than re-derives, naming this capstone by number as one of its intended future beneficiaries.
- `case-studies/llm-inference-serving/README.md` (capstone #10) and `case-studies/rag-contextual-retrieval/README.md` (capstone #9) — structural and sourcing-discipline precedent for this document's own Scope note, Confidence note, and feedback-loop framing.
- Lesson 8 (`lessons/lesson-8-safety-and-isolation.md`), Group F — F2 (sandboxing, via `learn-docker-ai-agents` Lesson 1's `sbx`/microVMs) and F5 (multi-tenant isolation), referenced to explain concretely what "raises the sandboxing stakes from Group F" means.
- `appendix/glossary.md` — one-line entries for **SWE-bench** and **resolve rate**, added for this document's own Sidebar.
