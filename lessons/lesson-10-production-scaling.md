# Lesson 10: Production Scaling

**Time:** 75-90 minutes
**Tool(s):** Conceptual (no single verified CLI) — a real Kubernetes autoscaling-policy schema, a per-tenant budget-enforcement/graceful-degradation config, a Server-Sent-Events stream (modeled on OpenAI's own real chat-completions streaming format), and a cost-attribution record schema, plus a runnable Python pipeline reproducing every number computed by hand in this lesson.

## Learning Objectives

By the end of this lesson, you will:

- Be able to define fan-out and autoscaling in full, building directly on Lesson 6's Concepts 1-2 (task queues, back pressure) rather than re-deriving them, and compute how an agentic fan-out pattern inflates a task queue's effective arrival rate and the worker count an autoscaling policy needs to absorb it
- Be able to define graceful degradation in full, design a tiered per-tenant budget-enforcement policy that extends capstone #15's own token-bucket rate limiting rather than re-deriving the algorithm, and compute how many additional requests a degraded-service tier buys a tenant before a hard exhaustion wall, and how long a queued request waits for the bucket to refill instead of failing outright
- Be able to define Server-Sent Events, partial-result UX, and cancellation mid-stream in full, and compute both the perceived-latency reduction streaming buys over a non-streamed response and the wasted-compute cost of a cancellation that isn't propagated down to the generation loop
- Be able to define usage-based cost model and cost attribution in full, design a cost-attribution record, and compute a per-feature cost breakdown that reveals a feature consuming spend disproportionate to its usage share
- Be able to point to exactly which already-written capstones (#9 RAG/contextual retrieval, #10 LLM inference serving, #13 autonomous coding agent, #15 LLM API gateway) and which earlier lessons (Lesson 6's Concepts 1-3, Lesson 1's A1/A3/B1/C2, Lesson 9's Concept 3) each Concept in this lesson connects to, rather than re-teaching material this repo has already taught

---

## Concept 1: Scaling Patterns for Agentic Workloads

### Why?

Lesson 1's Concept B1 already named the fork this lesson sits downstream of: hosted vs. self-hosted serving "determines whether your Lesson 10 scaling problem is 'manage your rate limits with a vendor' or 'manage your own GPU fleet.'" This Concept, and H2 below, are written for the hosted-serving side — a team calling one or more provider APIs and needing to scale its own request-handling layer in front of them. The self-hosted side's scaling problem — sizing and autoscaling a GPU fleet so it holds enough KV-cache capacity for the target concurrency — is capstone #10's own Step 2 (fleet-sizing arithmetic) and Step 5 (the scheduler admitting requests only as free KV-cache blocks exist) territory, already worked out there in full; this Concept doesn't duplicate it. Lesson 6's Concepts 1-2 already gave this repo task queues and back pressure in general. What neither covers is the specific thing that makes an *agentic* workload's queueing behavior different from a plain batch-ingestion workload like Lesson 6's own RAG-indexing example: a single agent step can fan out to several tool calls at once, and a production fleet has to react to that automatically, not just absorb it with a fixed worker pool sized for yesterday's traffic shape.

### What?

**Fan-out**, in this agentic context, is the pattern where one upstream unit of work — here, a single agent reasoning step — triggers several downstream calls at once instead of one. A plan step that needs to check three related files, run a test suite, and query a documentation search tool can dispatch all four tool calls in parallel rather than sequentially, so the step finishes in roughly the time of its *slowest* tool call instead of the sum of all four. (This is a different use of "fan-out" than Lesson 5's Concept 1 example, which described a multi-shard database query reaching several shards at once — same word, same "one triggers many" shape, but a different layer of the stack; this Concept doesn't reuse that example's numbers.) The production consequence Lesson 6's own task-queue arithmetic didn't have to account for: a fan-out step enqueues several task-queue jobs (Lesson 6, Concept 1) at once, so the *task* arrival rate a queue actually sees can run well ahead of the *step* rate an agent fleet is nominally executing.

**Autoscaling** is the automated practice of adding or removing worker capacity (processes, containers, or VMs) in response to a measured load signal, rather than running a fixed pool sized once by hand. For a task-queue-backed worker pool, the natural signal to scale on is **queue depth** — the number of jobs waiting to be picked up by a worker, the same quantity Lesson 6's Concept 2 named as the capacity-exhaustion signal ("a growing queue at high KV-cache utilization is the clearest sign of genuine capacity exhaustion," in capstone #10's own words, reused there for GPU memory and here for worker count). **Queue-depth alerting** is a separate, human-facing signal built on the same measurement: a threshold that pages an on-call engineer when queue depth crosses a level the autoscaler hasn't yet resolved — necessary because autoscaling has a real reaction lag (a new worker process has to start before it can drain anything), so a sudden fan-out-driven spike can still blow through a queue's back-pressure bound before new capacity comes online, which is exactly the gap alerting exists to cover with a human in the loop rather than letting the system silently ride it out.

### How?

**Worked example — fan-out inflates the task-arrival rate Lesson 6's own worked example assumed was fixed.** Lesson 6's Concept 2 computed a back-pressure time-to-full of 66.7 seconds for a task queue hit by a burst of λ = 150 tasks/sec against a drain rate of μ = 120 tasks/sec, with a 2,000-task bound. That example implicitly assumed one agent step equals one enqueued task. Say capstone #13's own fleet (500 concurrent sessions, ~200 round-trips/session, per that capstone's Step 2) runs its *normal* steady-state task-arrival rate at Lesson 6's own non-burst figure of λ = 100 tasks/sec — but 15% of those round-trips are fan-out steps that each dispatch 6 parallel tool calls instead of 1, while the remaining 85% are ordinary single-tool-call steps:

```
effective_tasks_per_round_trip = (0.85 × 1) + (0.15 × 6)
                                = 0.85 + 0.90
                                = 1.75

new_arrival_rate = baseline_round_trip_rate × effective_tasks_per_round_trip
                  = 100 tasks/sec × 1.75
                  = 175 tasks/sec
```

The *same* round-trip rate Lesson 6 treated as 100 tasks/sec now produces 175 actual task-queue arrivals per second, purely because 15% of those round-trips are multi-tool-call fan-out steps rather than single-tool-call ones — no change to session count or round-trip count at all. Against the same μ = 120 tasks/sec drain rate and the same 2,000-task bound Lesson 6 used:

```
net_growth_rate = 175 - 120 = 55 tasks/sec
time_to_full    = 2,000 / 55 ≈ 36.4 seconds
```

Compare this to Lesson 6's own burst scenario: a raw step-rate increase to 150 tasks/sec (a 50% jump, no fan-out) took 66.7 seconds to fill the same queue. Here, a *lower* raw step-rate (100 tasks/sec, unchanged from baseline) still fills the queue in roughly half the time (36.4s), purely because of the fan-out multiplier — the reason a production fleet has to monitor and alert on fan-out-weighted task arrivals, not just raw agent-step throughput, which would badly underestimate how fast this queue can fill.

**Autoscaling the worker pool to absorb it.** Reusing Lesson 6's own per-worker throughput figure (5 tasks/sec/worker, from its RAG-ingestion worker-sizing example) for consistency rather than inventing a new one:

```
workers_needed = ceil(new_arrival_rate / throughput_per_worker)
               = ceil(175 / 5)
               = 35 workers
```

A real Kubernetes `HorizontalPodAutoscaler` (API version `autoscaling/v2`), scaling a worker deployment on exactly this queue-depth signal rather than CPU/memory:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-tool-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-tool-workers
  minReplicas: 10
  maxReplicas: 50
  metrics:
  - type: External
    external:
      metric:
        name: task_queue_depth
        selector:
          matchLabels:
            queue: tool-call-tasks
      target:
        type: AverageValue
        averageValue: "50"
```

`scaleTargetRef` names the worker `Deployment` this policy scales. `metrics[].type: External` tells the autoscaler to pull its signal from a metric that isn't a built-in resource (CPU/memory) but an application-level one — here, `task_queue_depth`, published by whatever system monitors the queue. `target.type: AverageValue` with `averageValue: "50"` means the autoscaler adds replicas until queue depth divided by current replica count is at or below 50 — i.e., targeting roughly 50 queued-but-undrained tasks per worker, not a fixed total queue depth regardless of fleet size. `minReplicas: 10` keeps a baseline pool running even at idle (so a sudden burst doesn't start from zero); `maxReplicas: 50` is a hard ceiling, both to bound cost and because this worker pool's downstream dependency (e.g. the LLM provider behind it, H2's territory next) has its own capacity limits a larger pool wouldn't help saturate past.

**Trade-offs considered:** A fan-out step finishes faster for the *session* that issued it (its slowest tool call, not the sum of all of them) — a real latency win for that one agent — but at the system-wide cost of a proportionally larger task-queue arrival burst, the same latency-per-request-vs-system-wide-capacity trade-off Lesson 3's own batch-size example already established for a different resource (GPU batching) rather than task-queue capacity. Autoscaling on queue depth reacts to real, current load rather than a fixed guess, but a new worker replica takes real time to start (image pull, process startup, warm-up) — during that lag, queue-depth alerting (this Concept's second half) is what keeps a human aware the autoscaler's own reaction hasn't caught up yet, rather than the system silently riding out a growing backlog until it hits its back-pressure bound.

**Case-study pointer:** capstone #13 (`solutions/autonomous-coding-agent`) is this Concept's primary anchor — its Step 2 fleet figures (500 concurrent sessions, ~200 round-trips/session) are reused directly above, and this Concept's fan-out worked example is this repo's own extension of that capstone's plan-and-execute loop (Step 4), not a documented detail of that capstone's text. Lesson 6's Concepts 1 and 2 (task queues, back pressure, Little's Law) are referenced throughout, not re-derived — this Concept's job is the agentic-fan-out and production-autoscaling angle those Concepts didn't cover. Capstone #10 (`solutions/llm-inference-serving`) is the self-hosted-fork sibling named in this Concept's "Why?": its Step 2/Step 5 GPU-fleet-sizing and KV-cache-gated admission are the scaling problem Lesson 1's B1 fork points at on the self-hosted side, distinct from and not re-taught here.

**Source(s) and further reading:**

- Lesson 6 (`lesson-6-async-and-communication.md`), Concepts 1 and 2 — task queues, back pressure, and Little's Law, referenced throughout, not re-derived; the 100/120/150 tasks-per-sec and 2,000-task-bound figures this Concept's worked example extends directly
- Lesson 1 (`lesson-1-ai-fundamentals-refresher.md`), Concept B1 — the hosted-vs-self-hosted fork this Concept's own scope note resolves
- Kubernetes documentation, *"Horizontal Pod Autoscaler"* (kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) and the `HorizontalPodAutoscaler` v2 API reference — the real `autoscaling/v2` schema (`scaleTargetRef`, `metrics[].type: External`, `external.metric.selector`, `target.type`/`averageValue`) this Concept's YAML is written against
- `solutions/autonomous-coding-agent/README.md` (capstone #13), Step 2 — the fleet-concurrency and round-trip figures this Concept's worked example reuses directly
- `solutions/llm-inference-serving/README.md` (capstone #10), Steps 2 and 5 — the self-hosted-fleet-sizing and KV-cache-gated-admission territory this Concept's "Why?" names as the sibling scaling problem it doesn't duplicate

---

## Concept 2: Rate Limiting and Token Budgets

### Why?

Lesson 1's Concept A1 already named why this Concept has to exist: AI cost and latency "scale with the number of tokens processed... not with some fixed per-request charge," which is why a rate-limiting scheme for AI traffic can't just count requests the way a classic API gateway does — capstone #15's own Step 2 makes that point concretely (a request-based quota can look "100% used" while the real token-based view is already 130% over budget). Capstone #15's own Step 4 already gave this repo a real, working rate-limiting mechanism on top of that insight — the token bucket algorithm (also defined in `appendix/glossary.md`) — and a real per-key/per-team/per-model budget-scoping config. That capstone's own Step 6 trade-offs went further and raised, without fully resolving, the exact question this Concept answers: "Hard-cutting a team off the instant it hits 100% of its budget gives predictable, bounded cost control, but causes an outage for that team mid-task... A soft-overage model... keeps their workflow running uninterrupted, but requires an actual billing/reconciliation process... Neither option is universally correct." This Concept doesn't re-derive the token bucket algorithm or the per-key/team/model scoping — both are capstone #15's territory, linked not repeated — it builds the middle ground that capstone #15's own binary framing (hard cutoff vs. soft overage) left unbuilt: a real, tiered policy between those two extremes.

### What?

**Graceful degradation** is the practice of responding to a resource constraint — here, an exhausted or nearly-exhausted usage budget — by deliberately reducing the scope, size, or quality of service while remaining at least partially functional, instead of ignoring the constraint entirely or failing outright the instant it's hit. Applied to a token budget, graceful degradation means a request doesn't go straight from "fully served" to "rejected" the moment a tenant crosses 100% of its allotment — it passes through one or more intermediate tiers, each consuming the budget more slowly than the last, so the remaining capacity stretches further before any request fails.

### How?

**A per-tenant budget-enforcement config with degradation tiers**, built directly on capstone #15's own `team-growth` bucket numbers (`capacity_tokens: 5,000,000`, `refill_rate_tokens_per_sec: 57.87`, Step 4) rather than inventing a conflicting tenant:

```json
{
  "tenant_id": "team-growth",
  "budget_tokens_per_day": 5000000,
  "refill_rate_tokens_per_sec": 57.87,
  "degradation_tiers": [
    {
      "consumed_pct_gte": 80,
      "action": "cap_max_output_tokens",
      "max_output_tokens": 500
    },
    {
      "consumed_pct_gte": 95,
      "action": "reduce_context_and_downgrade_model",
      "retrieval_top_k": 3,
      "fallback_model": "small-context-model-v1",
      "max_output_tokens": 256
    },
    {
      "consumed_pct_gte": 100,
      "action": "queue_until_refill",
      "max_queue_wait_sec": 300
    }
  ]
}
```

`consumed_pct_gte` is checked against how much of `budget_tokens_per_day` the tenant has already consumed today — the same quantity capstone #15's own token bucket already tracks (`capacity_tokens` minus tokens consumed so far this period), just read as a percentage rather than used only for the bucket's binary admit/reject decision. The 80% tier caps response length (a request still gets a full-context, full-model answer, just a shorter one); the 95% tier additionally shrinks the retrieved context (`retrieval_top_k`, Lesson 1's Concept C2 territory) and routes to a smaller, cheaper model — both reduce *future* token consumption, the only lever that actually extends a token budget, since routing to a cheaper model changes dollar cost (H4, below) but not token count itself. The 100% tier doesn't reject outright: `queue_until_refill` holds the request until the token bucket's steady refill (capstone #15's mechanism, unchanged) accumulates enough tokens to admit it, up to a bounded `max_queue_wait_sec` — graceful in the sense that a short wait, not an error, is the tenant's experience at the hard limit.

**Worked example — how many more requests graceful degradation buys a tenant before the bucket actually runs dry.** Say the `team-growth` tenant has consumed 4,750,000 of its 5,000,000-token daily budget (95% consumed, 250,000 tokens remaining), triggering the second degradation tier above. At a normal, undegraded request size — reusing capstone #13's own round-trip figure (3,000 input + 300 output tokens = 3,300 tokens/request) for consistency:

```
remaining_requests_at_normal_size = tokens_remaining / tokens_per_normal_request
                                   = 250,000 / 3,300
                                   ≈ 75.8  →  75 more requests before exhaustion
```

Under the 95% tier's degraded request shape (reduced context plus the 256-token output cap pushing a typical request down to roughly 500 tokens total):

```
remaining_requests_at_degraded_size = tokens_remaining / tokens_per_degraded_request
                                     = 250,000 / 500
                                     = 500 more requests before exhaustion

extension_ratio = remaining_requests_at_degraded_size / remaining_requests_at_normal_size
                 = 500 / (250,000 / 3,300)
                 = 6.6x   (exact — computed from the unrounded request counts, not the floored "75")
```

Degrading request size at the 95% tier buys this tenant roughly **6.6x more requests** before the budget hits zero for the day, compared to serving full-size requests until the wall is hit — the concrete payoff of graceful degradation over a binary "full service, then nothing" policy. And once the bucket is fully exhausted, a queued request doesn't wait indefinitely:

```
wait_for_one_more_degraded_request = tokens_per_degraded_request / refill_rate_tokens_per_sec
                                    = 500 / 57.87
                                    ≈ 8.6 seconds
```

An 8.6-second queued wait for one more degraded request's worth of tokens to refill is a far less disruptive failure mode than an outright `429` rejection with no path forward until the next billing period — the same `queue_until_refill` action named in the config above, now with a concrete, bounded wait time rather than an open-ended one.

**Trade-offs considered:** A tiered degradation policy serves meaningfully more requests per budget period than a hard cutoff, but every tier adds real configuration surface (what counts as "degraded," which model is the fallback, how much context to cut) that a flat binary policy doesn't need — and a tenant degraded without clear signaling (a response header noting degraded mode, say) may simply perceive silently worse answers rather than understanding why, which is its own support-and-trust cost. `queue_until_refill`'s bounded wait avoids an outright failure, but `max_queue_wait_sec: 300` (5 minutes) is itself long enough to collide with exactly the risk Lesson 6's Concept 4 named for synchronous long-held requests: AWS ALB's documented 60-second default idle timeout, cited there, would kill a caller's connection well before a 300-second queued wait ever resolves — meaning `queue_until_refill` is only safe to implement as a synchronous hold if the wait is kept short relative to whatever gateway idle timeout sits in front of it, or is implemented asynchronously (Lesson 6's own submit-then-poll pattern) instead.

**Case-study pointer:** capstone #15 (`solutions/llm-api-gateway`) is this Concept's direct, confirmed anchor — its Step 4 token-bucket config (`capacity_tokens`, `refill_rate_tokens_per_sec`) and Step 6 hard-cutoff-vs-soft-overage trade-off are exactly what this Concept's degradation-tier config and worked example extend into a concrete, intermediate policy, reusing that capstone's own `team-growth` numbers rather than inventing a conflicting tenant. Capstone #13's (`solutions/autonomous-coding-agent`) 3,000-input/300-output round-trip figure (Step 2) is reused directly for the "normal request size" half of this worked example. Lesson 1's Concept A3 (token economics) and Concept C2 (vector databases, the `retrieval_top_k` lever) are both referenced, not re-derived.

**Source(s) and further reading:**

- `solutions/llm-api-gateway/README.md` (capstone #15), Step 1, Step 2, Step 4, and Step 6 — the request-vs-token-accounting objective framing and its concrete numeric example, the token-bucket config, and the hard-cutoff-vs-soft-overage trade-off this Concept's degradation-tier policy directly extends
- `appendix/glossary.md` — the token bucket algorithm's own full definition, referenced not re-derived
- Lesson 1 (`lesson-1-ai-fundamentals-refresher.md`), Concept A1 — token-based cost and latency, this Concept's own motivation, referenced not re-derived; Concept A3 — token economics; Concept C2 — vector databases and retrieval top-k, both referenced not re-derived
- `solutions/autonomous-coding-agent/README.md` (capstone #13), Step 2 — the 3,000-input/300-output round-trip token figure this Concept's worked example reuses

---

## Concept 3: Streaming Responses

### Why?

Lesson 6's Concept 3 already established *why* a token stream rides over TCP rather than UDP — reliable, ordered delivery, amortizing a one-time handshake cost over hundreds of tokens — and that Concept is referenced, not re-derived, here. What Lesson 6 didn't cover is the layer above the transport protocol: the actual wire format an application uses to stream partial output to a UI, why that matters to the person watching it arrive, and what has to happen when that person decides, mid-stream, that they don't want the rest.

### What?

**Server-Sent Events (SSE)** is a standardized, one-directional HTTP streaming mechanism: a client opens an ordinary HTTP request and keeps it open, the server responds with the MIME type `text/event-stream`, and instead of sending one complete response body and closing the connection, it sends a sequence of text-formatted events over that same connection as they become available, each prefixed `data:` and separated by a blank line. It's a W3C/WHATWG-standardized browser API (`EventSource`), and it's the real mechanism OpenAI's own Chat Completions API uses when a client sets `stream: true`: each partial chunk of the response arrives as its own `data:` line carrying a JSON object (the new text fragment in a `delta.content` field), and the stream ends with a literal `data: [DONE]` line the client uses as its signal to stop reading, rather than relying on any one chunk's own metadata.

**Partial-result UX** is the user-facing payoff of streaming: showing a response incrementally, token by token (or chunk by chunk), as it's generated, instead of making the user stare at a blank or loading state until the entire response completes. This doesn't change the model's actual total generation time — it changes *perceived* latency, the time a user experiences as "waiting," which is bounded by time-to-first-token (TTFT, already fully defined in capstone #10's own Step 1) rather than by the full response's total generation time.

**Cancellation mid-stream** is a user (or client application) terminating an in-progress stream before it finishes — clicking "stop" on a chat UI mid-response, for instance. On the client side, this is typically implemented with an **`AbortController`** (a standard browser/JavaScript API object whose `.abort()` call cancels an in-flight request it's attached to, including a streaming one). What matters for this Concept is the server side: a client closing its end of the connection doesn't automatically stop the server from generating tokens nobody will ever see, unless the server is specifically built to detect that disconnection and halt generation — the gap this Concept's worked example quantifies next.

### How?

**A real SSE stream**, in OpenAI's own documented wire format, showing three chunks of a streamed response followed by the terminator:

```
data: {"id":"chatcmpl-7f3a","choices":[{"index":0,"delta":{"content":"The"},"finish_reason":null}]}

data: {"id":"chatcmpl-7f3a","choices":[{"index":0,"delta":{"content":" refund"},"finish_reason":null}]}

data: {"id":"chatcmpl-7f3a","choices":[{"index":0,"delta":{"content":" has been processed."},"finish_reason":"stop"}]}

data: [DONE]
```

Each `data:` line is a complete, independently-parseable JSON object; `delta.content` carries only the *new* text fragment for that chunk, not the full response so far, so a client must concatenate `delta.content` across chunks to reconstruct the complete message; the third chunk's `finish_reason: "stop"` signals the model decided it was done (as opposed to hitting a length limit), and the final bare `data: [DONE]` line — not any field inside the JSON chunks — is the actual end-of-stream signal a client should wait for before closing its own side.

**A runnable Python generator showing where cancellation actually has to be checked, and the server-side cost if it isn't.**

```python
import time

def stream_response(tokens: list[str], cancel_flag: dict) -> "Iterator[str]":
    """Yields SSE-formatted chunks one token at a time, checking cancel_flag
    before generating each one -- this is the ONLY thing that actually stops
    wasted generation; closing the HTTP connection on the client side alone
    does not, unless the server loop itself checks for that disconnection."""
    for i, token in enumerate(tokens):
        if cancel_flag.get("cancelled"):
            # Concept 4 territory: a cost-attribution record would still log
            # the tokens actually generated up to this point, not the full response.
            return
        time.sleep(0.04)  # stand-in for ~40ms/token inter-token latency (capstone #10, Step 1)
        yield f'data: {{"delta": {{"content": "{token}"}}}}\n\n'
    yield "data: [DONE]\n\n"


# Concept 3: perceived-latency ratio, streaming vs. non-streaming
def perceived_wait_ratio(ttft_ms: float, inter_token_latency_ms: float, total_tokens: int) -> float:
    total_generation_ms = ttft_ms + inter_token_latency_ms * total_tokens
    return total_generation_ms / ttft_ms  # streaming's perceived wait is ~ttft_ms alone


# Concept 3: wasted output-token cost from an uncancelled generation loop
def wasted_cancellation_cost(tokens_wasted: int, output_price_per_1m: float) -> float:
    return (tokens_wasted / 1_000_000) * output_price_per_1m
```

**Worked example — the perceived-latency win, using capstone #10's own confirmed SLA targets.** Capstone #10's Step 1 states p50 (the median — 50% of requests are faster than this value, 50% slower; percentile latency is defined in full in Lesson 9's Concept 2) TTFT < 200ms and p50 inter-token latency < 40ms/token. For a 500-token response:

```
total_generation_ms_no_stream = ttft_ms + inter_token_latency_ms × total_tokens
                               = 200 + 40 × 500
                               = 200 + 20,000
                               = 20,200 ms  (≈20.2 seconds, if the user saw nothing until it was all done)

perceived_wait_streaming_ms ≈ ttft_ms = 200 ms  (the user sees the first token arrive, then a continuous stream)

perceived_wait_ratio = 20,200 / 200 = 101x
```

A user watching a streamed response perceives something close to a **200ms** wait (TTFT) before output starts appearing, instead of a **20.2-second** wait for the complete response — a 101x difference in perceived latency, even though the model's actual total generation time (20.2 seconds) hasn't changed. This is the concrete case for why partial-result UX matters independent of any actual speed improvement: it changes what the user experiences as "waiting," not how fast the system is.

**Worked example — the wasted-compute cost of a cancellation that isn't propagated to the generation loop.** Say a user cancels a 500-token response after the first 150 tokens have already streamed to them. If the server-side generation loop (unlike the Python sketch above) doesn't check for the client's disconnection and keeps generating all 500 tokens regardless of whether anyone's still listening:

```
tokens_wasted = total_tokens - tokens_already_sent
              = 500 - 150
              = 350 tokens generated for a client that's already gone

wasted_cost_per_cancelled_request = (350 / 1,000,000) × $15   (output-token price, Lesson 7/8's own $15/1M-output figure)
                                   = $0.00525
```

At capstone #9's own query-volume scale (20,000 queries/day) and an illustrative 8% client-cancellation rate:

```
cancelled_requests_per_day = 20,000 × 0.08 = 1,600

wasted_cost_per_day = 1,600 × $0.00525 ≈ $8.40/day   (dollar cost alone)

wasted_gpu_seconds_per_day = 1,600 × 350 tokens × 40 ms/token = 22,400,000 ms ≈ 6.22 GPU-hours/day
```

The dollar figure ($8.40/day) is modest, but the **6.22 GPU-hours/day** of wasted generation compute is the more load-bearing number: on capstone #10's own serving fleet, where Step 2's arithmetic already established GPU memory and compute as the binding, carefully-rationed resource, that's 6+ GPU-hours/day spent generating tokens for clients who disconnected and will never see them — capacity a propagated cancellation would free immediately for an actual waiting request instead. Concretely, propagating a cancellation means the server's generation loop, on detecting the disconnect, calls the same `free_request()` method capstone #10's own `PagedKVCacheAllocator` sketch (Step 4) already defines to release a finished request's blocks — early, rather than waiting for the now-pointless generation to run to its natural end.

**Trade-offs considered:** SSE's one-directional simplicity (no handshake beyond the initial HTTP request, built on infrastructure every HTTP client and proxy already understands) is exactly why it's the real mechanism chat-completions APIs use, but it offers the client no built-in way to send anything *back* to the server over the same connection (e.g., "please stop") — cancellation has to be a separate signal (closing the connection, or a distinct cancel-request API call) that the server has to actively detect, not something SSE itself carries. A bidirectional protocol like WebSockets would let a client send an explicit cancel message over the same connection, at the cost of a heavier protocol and connection-management model than a plain HTTP streaming response needs for a mostly one-directional "model talks, user mostly listens" interaction pattern.

**Case-study pointer:** capstone #10 (`solutions/llm-inference-serving`) is this Concept's primary anchor — its Step 1 TTFT/inter-token-latency SLA targets are reused directly in both worked examples above, and its Step 4 `PagedKVCacheAllocator.free_request()` method is the concrete mechanism this Concept's cancellation discussion ties back to. Capstone #9's (`solutions/rag-contextual-retrieval`) 20,000-queries/day figure is reused for this Concept's fleet-scale cancellation-cost estimate. Lesson 6's Concept 3 (TCP vs. UDP, the handshake-amortization argument for streaming over TCP) and Lesson 7/8's own $15/1M-output pricing figure are both referenced, not re-derived.

**Source(s) and further reading:**

- OpenAI, Chat Completions API reference, streaming (platform.openai.com/docs/api-reference/streaming) — the real `data:` / `delta.content` / `data: [DONE]` wire format this Concept's SSE example is written against
- WHATWG HTML Standard, *Server-Sent Events* (`EventSource`, `text/event-stream`) and MDN Web Docs, *Using server-sent events* — the standardized mechanism this Concept's `stream_response` snippet models
- MDN Web Docs, `AbortController` — the standard client-side cancellation primitive referenced in this Concept's "What?"
- `solutions/llm-inference-serving/README.md` (capstone #10), Step 1 and Step 4 — the TTFT/inter-token-latency targets and the `free_request()` mechanism this Concept's worked examples and cancellation discussion both build on directly
- `solutions/rag-contextual-retrieval/README.md` (capstone #9), Step 2 — the 20,000-queries/day figure reused in this Concept's cancellation-cost worked example
- Lesson 6 (`lesson-6-async-and-communication.md`), Concept 3 — TCP vs. UDP, referenced not re-derived

---

## Concept 4: Cost Attribution

### Why?

Lesson 9's Concept 3 already put a `cost_usd` field on every traced span, and capstone #15's Step 6 already tracks "per-key/per-team budget burn rate." Both give a per-request or per-team cost number. Neither answers a different, equally real question a product team has to ask: *which feature of the product is actually driving that spend* — because, per Lesson 1's own Concept A1, AI cost is **usage-based**, not the flat, fixed infrastructure bill a typical CRUD feature adds to a shared server's cost regardless of how often that feature is used. A usage-based cost model means two features built on the exact same infrastructure can cost wildly different amounts in practice, purely because of how many tokens each processes per use — and without attributing spend to that granularity, a team only ever sees one aggregate number, with no way to tell which part of the product is actually expensive.

### What?

A **usage-based cost model** is a pricing/cost structure where the amount a system costs to run scales directly with how much it's actually used (here, tokens processed), rather than with a fixed charge that stays constant regardless of usage volume (a flat monthly server rental, for instance) — the AI-specific instance of the property Lesson 1's Concept A1 already named generally ("token-based cost and latency... scale with the number of tokens processed... not with some fixed per-request charge"). **Cost attribution** is the practice of assigning a system's total usage-based spend to the specific dimension that actually generated it — a request, a user, a tenant, or (the dimension this Concept adds that Lesson 9 and capstone #15 didn't cover) a specific *product feature* — so spend can be analyzed, billed, or optimized at that granularity, instead of only ever being visible as one aggregate number on a monthly bill.

### How?

**A cost-attribution record**, deliberately sharing field shapes with Lesson 9's own trace-span schema (`tokens`, `cost_usd`) but adding the dimensions a debugging trace doesn't need and a billing/attribution record does:

```json
{
  "request_id": "req-9c4f21",
  "timestamp": "2026-10-11T15:02:33Z",
  "tenant_id": "team-growth",
  "user_id": "user-48221",
  "feature": "code_review",
  "model": "large-context-model-v2",
  "input_tokens": 9000,
  "output_tokens": 600,
  "cost_usd": 0.036
}
```

`feature` is this Concept's own addition — Lesson 9's span schema and capstone #15's per-key/team burn-rate tracking both stop at the request/tenant level; tagging each request with which product feature generated it (chat, summarization, code review, …) is what makes a feature-level cost breakdown possible at all, rather than only a tenant-level or request-level one. `cost_usd` here uses the same formula shape as Lesson 9's span cost and capstone #13's `llm_cost_per_task` — `(input_tokens/1,000,000) × input_price + (output_tokens/1,000,000) × output_price` — applied per-record rather than per-session, so many records can be summed by any dimension (`feature`, `tenant_id`, `user_id`) after the fact.

**Worked example — a per-feature cost breakdown that an aggregate daily-spend number hides completely.** Say a product has three AI-powered features sharing the same underlying model/pricing, at capstone #9's own 20,000-queries/day scale: **chat** (70% of requests, averaging the now-familiar 3,000-input/300-output-token shape, $0.0135/request per Lesson 9's own span-cost worked example), **summarization** (20% of requests, larger input, averaging $0.04/request), and **code review** (10% of requests, the largest input/output of the three, averaging $0.12/request):

```
chat:          14,000 requests × $0.0135  = $189.00/day
summarization:  4,000 requests × $0.0400  = $160.00/day
code_review:    2,000 requests × $0.1200  = $240.00/day
                                            ------------
total daily AI spend:                        $589.00/day

code_review_cost_share  = 240.00 / 589.00 ≈ 0.4075  (40.75% of total spend)
code_review_volume_share = 2,000 / 20,000 = 0.10     (10% of total requests)

cost_to_volume_ratio = (240.00 / 589.00) / 0.10 ≈ 4.07x
```

Without cost attribution, a team sees exactly one number: **$589.00/day** of AI spend, trending however it trends. With it, the same $589.00/day decomposes to show that **code review — only 10% of request volume — accounts for roughly 41% of total spend**, a cost share **4.07x** larger than its share of usage. That's the actionable finding cost attribution exists to surface: if this product charges the same subscription price regardless of which features a customer uses, code review is quietly far more expensive to serve per use than chat is, a fact the aggregate $589.00/day figure alone could never reveal — exactly the kind of margin-eroding mismatch a team would only discover by accident (or too late) without attributing spend to the feature actually generating it.

**Trade-offs considered:** Tagging every request with a `feature` field (and, by extension, every downstream cost record) is cheap to add at request time but has to be done consistently — a feature added later without the same tagging discipline silently falls into an "unattributed" bucket that undermines the whole breakdown, the same kind of silent coverage gap Lesson 9's own golden-dataset staleness risk already illustrates for a different kind of data going stale. Attributing cost down to the individual-request level (rather than only tenant or feature aggregates) gives the finest-grained picture, but means storing or aggregating a much larger volume of small records — a real storage/processing cost of its own, the same linear-cost-of-granularity shape Lesson 9's Concept 3 already established for full-vs-sampled tracing, now applied to billing records instead of debugging traces.

**Case-study pointer:** Lesson 9 (`lesson-9-evaluation-and-observability.md`), Concept 3's `cost_usd`-bearing trace-span schema is this Concept's direct structural ancestor — this Concept's record reuses that same per-record cost formula and extends it with the `feature`/`tenant_id` dimensions a debugging trace doesn't need. Capstone #13's (`solutions/autonomous-coding-agent`) `llm_cost_per_task` figure (Step 2, $2.70/task) is itself a form of cost attribution — attributing spend to one coding-agent task — that this Concept generalizes to the feature and tenant dimensions that capstone doesn't itself need (it only has one feature). Capstone #15's (`solutions/llm-api-gateway`) per-key/per-team budget-burn-rate tracking (Step 6) is the tenant-level sibling of this Concept's feature-level breakdown — the same underlying telemetry, aggregated along a different dimension. Capstone #9's (`solutions/rag-contextual-retrieval`) 20,000-queries/day figure is reused directly for this worked example's scale.

**Source(s) and further reading:**

- Lesson 1 (`lesson-1-ai-fundamentals-refresher.md`), Concept A1 — token-based cost and latency, the usage-based-cost-model property this Concept names in full and builds on
- Lesson 9 (`lesson-9-evaluation-and-observability.md`), Concept 3 — the trace-span `cost_usd` field and formula this Concept's cost-attribution record reuses and extends
- `solutions/autonomous-coding-agent/README.md` (capstone #13), Step 2 — the `llm_cost_per_task` figure this Concept's case-study pointer generalizes
- `solutions/llm-api-gateway/README.md` (capstone #15), Step 6 — the per-key/team budget-burn-rate tracking this Concept's feature-level breakdown sits alongside
- `solutions/rag-contextual-retrieval/README.md` (capstone #9), Step 2 — the 20,000-queries/day figure this Concept's worked example reuses

---

## Hands-On Walkthrough

There's no single CLI spanning H1-H4 — work through the four schemas above plus this runnable Python pipeline, which reproduces every number computed by hand in this lesson's four Concepts.

```python
import math

# Concept 1: fan-out-inflated task-arrival rate, worker sizing, and back-pressure time-to-full
def fanout_arrival_rate(baseline_rate: float, fanout_fraction: float, fanout_multiplier: int) -> float:
    effective_tasks_per_step = (1 - fanout_fraction) * 1 + fanout_fraction * fanout_multiplier
    return baseline_rate * effective_tasks_per_step


def workers_needed(arrival_rate: float, throughput_per_worker: float) -> int:
    return math.ceil(arrival_rate / throughput_per_worker)


def time_to_full(max_queue_depth: float, arrival_rate: float, drain_rate: float) -> float:
    net_growth = arrival_rate - drain_rate
    return max_queue_depth / net_growth


# Concept 2: graceful-degradation request-count extension and queued-wait time
def remaining_requests(tokens_remaining: float, tokens_per_request: float) -> float:
    return tokens_remaining / tokens_per_request


def queued_wait_seconds(tokens_needed: float, refill_rate_tokens_per_sec: float) -> float:
    return tokens_needed / refill_rate_tokens_per_sec


# Concept 3: perceived-latency ratio and wasted-cancellation cost
def perceived_wait_ratio(ttft_ms: float, inter_token_latency_ms: float, total_tokens: int) -> float:
    total_generation_ms = ttft_ms + inter_token_latency_ms * total_tokens
    return total_generation_ms / ttft_ms


def wasted_cancellation_cost(tokens_wasted: int, output_price_per_1m: float) -> float:
    return (tokens_wasted / 1_000_000) * output_price_per_1m


# Concept 4: per-feature cost attribution and cost-to-volume ratio
def feature_cost_breakdown(requests: int, cost_per_request: float) -> float:
    return requests * cost_per_request


def cost_to_volume_ratio(cost_share: float, volume_share: float) -> float:
    return cost_share / volume_share


# Reproduces this lesson's own worked numbers:
print(round(fanout_arrival_rate(100, 0.15, 6), 2))          # 175.0
print(workers_needed(175, 5))                                # 35
print(round(time_to_full(2000, 175, 120), 1))                 # 36.4

print(round(remaining_requests(250_000, 3_300), 1))           # 75.8
print(round(remaining_requests(250_000, 500), 1))             # 500.0
print(round(queued_wait_seconds(500, 57.87), 1))              # 8.6

print(perceived_wait_ratio(200, 40, 500))                     # 101.0
print(round(wasted_cancellation_cost(350, 15.0), 5))          # 0.00525

chat = feature_cost_breakdown(14_000, 0.0135)
summarization = feature_cost_breakdown(4_000, 0.04)
code_review = feature_cost_breakdown(2_000, 0.12)
total = chat + summarization + code_review
print(round(total, 2))                                        # 589.0
print(round(cost_to_volume_ratio(code_review / total, 0.10), 2))  # 4.07
```

Confirm for yourself: `fanout_arrival_rate(100, 0.15, 6)` returns `175.0` — the identical figure Concept 1 computes by hand for a fleet whose raw round-trip rate never changed, purely from 15% of steps fanning out to 6 parallel tool calls each. `remaining_requests(250_000, 500) / remaining_requests(250_000, 3_300)` returns `6.6`, reproducing Concept 2's own exact extension ratio. `wasted_cancellation_cost(350, 15.0)` returns `0.00525`, the exact per-cancelled-request dollar figure Concept 3 computes by hand before scaling it to a fleet-wide daily total. `cost_to_volume_ratio(code_review / total, 0.10)` returns `4.07`, confirming code review's cost share really is about 4x its volume share, not an artifact of rounding in the prose walkthrough.

---

## Summary

| Concept | One-line takeaway |
|---|---|
| H1. Scaling patterns for agentic workloads | Fan-out (one agent step dispatching several parallel tool calls) inflates a task queue's effective arrival rate well beyond its raw step rate — 100 steps/sec became 175 tasks/sec in this lesson's own worked example, filling a back-pressure bound in 36.4s rather than 66.7s — which is exactly the signal a queue-depth-driven autoscaling policy (and queue-depth alerting, for the lag while new capacity starts) has to react to, building on Lesson 6's task-queue/back-pressure foundations rather than re-deriving them. |
| H2. Rate limiting and token budgets | Graceful degradation — tiered response-size and model-tier cuts triggered at 80%/95%/100% of a token budget, ending in a bounded queued wait rather than an outright reject — turned 75 more full-size requests into 500 more degraded-size ones in this lesson's own worked example, resolving the hard-cutoff-vs-soft-overage trade-off capstone #15's own Step 6 raised without fully building, and reusing (not re-deriving) that capstone's own token-bucket mechanism. |
| H3. Streaming responses | Server-Sent Events let a user perceive roughly a 200ms wait (time-to-first-token) instead of a 20.2-second wait for a full response — a 101x perceived-latency win in this lesson's own worked example — but only if a mid-stream cancellation is actually propagated down to the generation loop (capstone #10's own `free_request()`), since an uncancelled stream wastes real GPU time (6.22 GPU-hours/day at this lesson's own fleet scale) generating tokens nobody will see. |
| H4. Cost attribution | Tagging each cost record with the product feature that generated it (not just the request or tenant) turned one opaque $589.00/day AI-spend figure into a breakdown showing one feature (10% of request volume) responsible for 41% of total spend — a 4.07x cost-to-volume mismatch an aggregate number alone could never reveal, extending Lesson 9's per-span cost tracking and capstone #15's per-tenant burn-rate tracking to a dimension neither one covers. |

## Key Formulas & Schema/Config Reference

```
Fan-out-inflated arrival rate (Concept 1):
  effective_tasks_per_step = (1 − fanout_fraction) × 1 + fanout_fraction × fanout_multiplier
  new_arrival_rate         = baseline_rate × effective_tasks_per_step

Worker sizing and back-pressure time-to-full (Concept 1, building on Lesson 6):
  workers_needed = ceil(arrival_rate / throughput_per_worker)
  time_to_full   = max_queue_depth / (arrival_rate − drain_rate)

Graceful-degradation request extension and queued wait (Concept 2):
  remaining_requests  = tokens_remaining / tokens_per_request
  queued_wait_seconds = tokens_needed / refill_rate_tokens_per_sec

Perceived-latency ratio and wasted-cancellation cost (Concept 3):
  total_generation_ms  = ttft_ms + inter_token_latency_ms × total_tokens
  perceived_wait_ratio = total_generation_ms / ttft_ms
  wasted_cost          = (tokens_wasted / 1,000,000) × output_price_per_1m

Per-feature cost attribution (Concept 4):
  feature_cost        = requests × cost_per_request
  cost_to_volume_ratio = cost_share / volume_share
```

```yaml
# Concept 1 -- Kubernetes HorizontalPodAutoscaler, scaling on external task-queue-depth metric
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-tool-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-tool-workers
  minReplicas: 10
  maxReplicas: 50
  metrics:
  - type: External
    external:
      metric:
        name: task_queue_depth
        selector:
          matchLabels:
            queue: tool-call-tasks
      target:
        type: AverageValue
        averageValue: "50"
```

```json
// Concept 2 -- per-tenant budget-enforcement config with graceful-degradation tiers
{
  "tenant_id": "team-growth",
  "budget_tokens_per_day": 5000000,
  "refill_rate_tokens_per_sec": 57.87,
  "degradation_tiers": [
    {"consumed_pct_gte": 80, "action": "cap_max_output_tokens", "max_output_tokens": 500},
    {"consumed_pct_gte": 95, "action": "reduce_context_and_downgrade_model", "retrieval_top_k": 3, "fallback_model": "small-context-model-v1", "max_output_tokens": 256},
    {"consumed_pct_gte": 100, "action": "queue_until_refill", "max_queue_wait_sec": 300}
  ]
}
```

```
# Concept 3 -- SSE stream, OpenAI's own wire format
data: {"id":"chatcmpl-7f3a","choices":[{"index":0,"delta":{"content":"The"},"finish_reason":null}]}

data: {"id":"chatcmpl-7f3a","choices":[{"index":0,"delta":{"content":" refund has been processed."},"finish_reason":"stop"}]}

data: [DONE]
```

```json
// Concept 4 -- cost-attribution record
{
  "request_id": "req-9c4f21",
  "tenant_id": "team-growth",
  "user_id": "user-48221",
  "feature": "code_review",
  "model": "large-context-model-v2",
  "input_tokens": 9000,
  "output_tokens": 600,
  "cost_usd": 0.036
}
```

**Next:** Checkpoint 10, then **Lesson 11: Real-World Architectures** — the AI-world analog of `system-design-primer`'s own "Real world architectures," "Company architectures," and "Company engineering blogs" sections, pointing back at every lesson and capstone this repo has already built rather than teaching new material.
