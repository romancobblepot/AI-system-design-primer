# Checkpoint 10: Production Scaling

## Purpose

This checkpoint verifies you can define fan-out and autoscaling and compute how agentic fan-out inflates a task queue's arrival rate and the worker count needed to absorb it, design a tiered graceful-degradation budget-enforcement policy and compute the request-count extension and queued-wait time it buys, define Server-Sent Events/partial-result UX/cancellation and compute both the perceived-latency win streaming buys and the wasted-compute cost of an unpropagated cancellation, and design a cost-attribution record and compute a per-feature cost breakdown that reveals a volume/spend mismatch.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1 (H1 — Scaling patterns for agentic workloads, part 1): What is fan-out in this lesson's agentic sense, and why doesn't Lesson 6's own task-queue/back-pressure arithmetic already account for it? Using this lesson's own figures (a baseline round-trip rate of 100/sec, 15% of round-trips fanning out to 6 parallel tool calls each), compute the effective task-arrival rate.</summary>

**Answer:** Fan-out is the pattern where one agent reasoning step dispatches several tool calls in parallel instead of one, so a single step can enqueue several task-queue jobs at once. Lesson 6's own worked examples (task queues, Concept 1; back pressure, Concept 2) implicitly assumed one step = one enqueued task — they never modeled a step producing more than one task at once, which is exactly the gap this Concept fills rather than re-deriving queues or back pressure from scratch. The computation: `effective_tasks_per_round_trip = (0.85 × 1) + (0.15 × 6) = 0.85 + 0.90 = 1.75`; `new_arrival_rate = 100 × 1.75 = 175 tasks/sec`.

**Why this matters:** A fleet monitoring only its raw agent-step rate (100/sec, unchanged) would badly underestimate real task-queue load — the actual arrival rate a worker pool and an autoscaler have to react to is 75% higher, purely from fan-out, with no change in session or step count at all.
</details>

<details>
<summary>Question 2 (H1 — Scaling patterns for agentic workloads, part 2): Using the 175 tasks/sec arrival rate from Question 1 against a 120 tasks/sec drain rate and a 2,000-task bound, how long does this queue take to fill, and how does that compare to Lesson 6's own burst scenario (150 tasks/sec, same drain rate and bound, which took 66.7 seconds)? What does a Kubernetes `HorizontalPodAutoscaler`'s `metrics[].type: External` field let it scale on that CPU/memory-based autoscaling can't?</summary>

**Answer:** `net_growth_rate = 175 − 120 = 55 tasks/sec`; `time_to_full = 2,000 / 55 ≈ 36.4 seconds` — notably *faster* than Lesson 6's own 66.7-second burst scenario, even though this lesson's raw step rate (100/sec) never actually increased the way Lesson 6's burst did (to 150/sec) — the fan-out multiplier alone closes the gap faster than an equivalent-looking raw-rate burst would. An `External` metric type lets the autoscaler scale on an application-level signal published by the system itself (here, `task_queue_depth`) rather than only the built-in CPU/memory resource metrics every pod already exposes — the only way to scale a worker pool directly on the thing that actually matters for this workload (queue depth), not a proxy for it.

**Why this matters:** Fan-out can make a queue fill dangerously fast even when the metric a team is used to watching (raw agent-step rate) looks unremarkable — which is exactly why queue-depth-based autoscaling (and queue-depth alerting, for the lag while new workers start) has to be the actual signal monitored, not agent-step throughput alone.
</details>

<details>
<summary>Question 3 (H2 — Rate limiting and token budgets): What does graceful degradation mean for a token budget specifically, and what gap in capstone #15's own Step 6 does it resolve? Using this lesson's own figures (250,000 tokens remaining, a normal request at 3,300 tokens, a degraded request at 500 tokens), compute the request-count extension ratio, and the queued wait time for one more degraded request once the budget hits 100% at a refill rate of 57.87 tokens/sec.</summary>

**Answer:** Graceful degradation, for a token budget, means a request passes through intermediate tiers (capped output length, then reduced context plus a smaller model, then a bounded queued wait) as consumption crosses thresholds, instead of jumping straight from full service to an outright reject at 100%. It resolves capstone #15's own Step 6 trade-off, which named "hard cutoff" and "soft overage" as two extremes without building the tiered middle ground between them. The computation: `remaining_requests_at_normal_size = 250,000 / 3,300 ≈ 75.8`; `remaining_requests_at_degraded_size = 250,000 / 500 = 500`; `extension_ratio = 500 / (250,000 / 3,300) = 6.6x` (computed from the exact, unrounded request counts — not from the floored "75"). At 100%, `queued_wait_seconds = 500 / 57.87 ≈ 8.6 seconds` for one more degraded request's worth of tokens to refill.

**Why this matters:** A tiered policy serves roughly 6.6x more requests before a budget actually runs dry than continuing to serve full-size requests until the wall is hit, and even at the hard limit, an 8.6-second queued wait is a far less disruptive failure mode than an open-ended `429` rejection — without reinventing or contradicting capstone #15's own token-bucket mechanism, which keeps enforcing the underlying bucket unchanged.
</details>

<details>
<summary>Question 4 (H3 — Streaming responses): Define Server-Sent Events and explain what the literal `data: [DONE]` line is for. Using capstone #10's own SLA figures (p50 TTFT 200ms, p50 inter-token latency 40ms/token, a 500-token response), compute the perceived-latency ratio between streaming and waiting for the full response. Separately, if a client cancels after 150 of 500 tokens and the server doesn't propagate that cancellation, how many GPU-hours/day are wasted at this lesson's own fleet scale (20,000 queries/day, 8% cancellation rate)?</summary>

**Answer:** Server-Sent Events is a one-directional HTTP streaming mechanism (`text/event-stream`) where a server sends a sequence of `data:`-prefixed text events over one kept-open connection instead of one complete response and a close. The literal `data: [DONE]` line is the actual end-of-stream signal a client should wait for, rather than inferring completion from any one JSON chunk's own fields. The computation: `total_generation_ms = 200 + 40 × 500 = 20,200ms`; `perceived_wait_ratio = 20,200 / 200 = 101x` — streaming lets a user perceive roughly a 200ms wait instead of a 20.2-second one, even though total generation time is unchanged. For the cancellation case: `tokens_wasted = 500 − 150 = 350`; at 20,000 × 0.08 = 1,600 cancelled requests/day, `wasted_gpu_seconds_per_day = 1,600 × 350 × 40ms = 22,400,000ms ≈ 6.22 GPU-hours/day`.

**Why this matters:** Streaming's perceived-latency win is real and large, but it's a UX improvement, not a throughput one — the GPU-hours wasted by an uncancelled stream are real compute that a propagated cancellation (calling capstone #10's own `free_request()` the moment a client disconnects) would free immediately for an actual waiting request, instead of silently burning capacity generating tokens nobody will see.
</details>

<details>
<summary>Question 5 (H4 — Cost attribution): What does cost attribution add on top of Lesson 9's per-span `cost_usd` tracking and capstone #15's per-tenant budget-burn-rate tracking? Using this lesson's own three-feature breakdown (chat: 14,000 req × $0.0135; summarization: 4,000 req × $0.04; code review: 2,000 req × $0.12), compute the total daily spend and the cost-to-volume ratio for code review.</summary>

**Answer:** Cost attribution adds a `feature` dimension — tagging each cost record with which product feature generated it — that neither Lesson 9's per-span tracking (request/session-level) nor capstone #15's per-tenant burn-rate tracking (tenant-level) captures; without it, a team only sees one aggregate spend number with no way to tell which feature is actually driving it. The computation: `chat = 14,000 × $0.0135 = $189.00`; `summarization = 4,000 × $0.04 = $160.00`; `code_review = 2,000 × $0.12 = $240.00`; `total = $589.00/day`. `code_review_cost_share = 240 / 589 ≈ 0.4075` (40.75% of spend) against a `code_review_volume_share` of `2,000 / 20,000 = 0.10` (10% of requests); `cost_to_volume_ratio = (240/589) / 0.10 ≈ 4.07x`.

**Why this matters:** The $589.00/day aggregate figure alone hides that one feature responsible for only 10% of request volume accounts for roughly 41% of total spend — a 4.07x mismatch that a flat per-subscription price (or any pricing decision made off the aggregate number alone) would badly misjudge, which is exactly the kind of margin-eroding gap cost attribution exists to surface before it's discovered too late.
</details>

## Hands-On Self-Check

There's no single CLI spanning this whole lesson — confirm you can do each of the following, without looking back at it:

- [ ] I can define fan-out and autoscaling in my own words, and compute `fanout_arrival_rate` and `time_to_full` given any baseline rate, fan-out fraction/multiplier, drain rate, and queue bound of my own choosing — and explain why this builds on Lesson 6's Concepts 1-2 rather than re-deriving them.
- [ ] I can read a Kubernetes `HorizontalPodAutoscaler` with an `External` metric type and explain what `scaleTargetRef`, `minReplicas`/`maxReplicas`, and `target.type: AverageValue` each control.
- [ ] I can define graceful degradation in my own words, design a tiered budget-enforcement policy of my own (at least two thresholds plus a terminal queued-wait tier), and compute `remaining_requests` and `queued_wait_seconds` for a fresh set of token-budget numbers — and state exactly which capstone #15 trade-off this Concept resolves.
- [ ] I can define Server-Sent Events, partial-result UX, and cancellation mid-stream in my own words, and compute `perceived_wait_ratio` and `wasted_cancellation_cost` given any TTFT, inter-token latency, token count, and cancellation point of my own choosing.
- [ ] I can define usage-based cost model and cost attribution in my own words, design a cost-attribution record with at least a `feature` and `tenant_id` field, and compute a per-feature cost breakdown and cost-to-volume ratio for a fresh set of feature-mix numbers.
- [ ] I can name which already-written capstone (#9, #10, #13, or #15) and which earlier lesson (Lesson 1's A1/A3/B1, Lesson 6's Concepts 1-3, Lesson 9's Concept 3) each of this lesson's four Concepts connects to, including the one Concept (H2) that resolves a trade-off capstone #15's own Step 6 raised without fully building, before this lesson existed.

## Next Step

Move to **Lesson 11: Real-World Architectures**.
