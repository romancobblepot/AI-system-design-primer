# Capstone #15: LLM API Gateway

**Source(s):** Secondary/product-documentation only — LiteLLM's open-source proxy documentation (an OpenAI-compatible interface across 100+ providers; routing, retries, fallback, spend tracking, per-key/team/model rate limits), Portkey's product documentation (a managed control plane: routing, load balancing, fallbacks, caching, guardrails, budget limits), and Cloudflare's AI Gateway documentation (an edge-hosted proxy: caching, rate limiting, analytics, logging).

**Confidence:** No single company has published a primary engineering teardown of this specific pattern — unlike, say, the vLLM paper behind capstone #10, there is no named team's own "how we built our LLM gateway" paper or blog post this capstone can point to as ground truth. This document instead synthesizes real, verifiable, publicly available product documentation from three actual products that implement this pattern in production. Treat every design choice below as "this is how real shipped products do it," not "this is how [Company X] does it" — there is no single company to attribute it to.

**Scope note:** This capstone is the routing/gateway layer only — it sits *in front of* one or more model-serving backends (like capstone #10's `solutions/llm-inference-serving`) and decides which backend/provider handles a given request. It does not cover the inference serving itself, nor content moderation (Lesson 8 / capstone #11's territory).

---

## Step 1: Clarify Requirements & Frame the Objective

**Functional scope:** A single API surface that proxies requests across multiple LLM providers and/or models, handling authentication, rate limiting, token-budget enforcement, response caching, and automatic fallback when a provider is unavailable.

**The central objective-framing insight, stated up front because it drives every later step:** a traditional API gateway's rate limiting counts *requests*. An LLM gateway has to count *tokens*, because — as Lesson 4's Concept J4 establishes — request count has no fixed relationship to compute cost for LLM traffic; one request can carry 50 tokens or 128,000. **The actual metric this gateway has to enforce and report against is tokens consumed per unit time (or per billing period) against a configured budget — not requests served.** This is this capstone's equivalent of a classic ML capstone's "what's the actual metric being optimized" question: get this wrong (build a gateway that only counts requests) and every downstream budget, alert, and cost-control decision is wrong in a way that looks like a minor oversight but is actually the whole design missing its point.

**Non-functional constraints:**
- **Gateway-added latency** should be small relative to the underlying model call itself — e.g. a target of under 20ms of gateway overhead (tokenizing the request to estimate its cost, checking budgets, routing logic, cache lookup), against a typical model TTFT (time-to-first-token, defined in Lesson 3's Concept I1) of 200ms-2s.
- **Gateway availability** matters disproportionately: because every provider behind the gateway becomes unreachable if the gateway itself is down, the gateway is a new single point of failure sitting in front of whatever redundancy exists behind it (Lesson 3's Concept I3).

**Equivalent of "ground truth / feedback signal":** metered token-usage logs measured against configured budgets (did actual consumption match what was predicted/allowed), and provider error/latency telemetry as the feedback signal driving fallback decisions (Step 4).

**Explicitly out of scope:** the inference serving of any individual model (capstone #10's job), model training/fine-tuning, and content-safety filtering of model outputs (Lesson 8, capstone #11).

**Trade-offs considered:** Optimizing purely for minimal gateway-added latency (e.g. skip tokenizing the request before routing it) conflicts directly with accurate token-based budget enforcement (which requires tokenizing or estimating the request's token count *before* deciding whether to allow it) — this exact tension is what the whole rest of this capstone works through, starting with the numeric example in Step 2.

---

## Step 2: Back-of-Envelope Constraints

**Why request-based accounting hides the real budget risk — a concrete numeric example (deliberately different from Lesson 4's worked example, to extend rather than repeat it).** Say a team is allotted a budget of 1,000,000 tokens/day, enforced historically (and naively) via a request-count limit of 500 requests/day, with no per-request token cap.

Suppose that team sends 490 small requests of 50 tokens each, plus 10 requests that each happen to carry a 128,000-token context (e.g. 10 long-document-summarization calls):

```
small requests:  490 × 50 tokens         =     24,500 tokens
large requests:   10 × 128,000 tokens    =  1,280,000 tokens
                                             -----------------
total consumed:                              1,304,500 tokens
```

A request-based accounting view would report **"500 of 500 requests used — 100% of quota"** — right at the limit, and looking completely normal for a system that's supposed to cap usage at 500 requests/day. The actual token-based view is **1,304,500 / 1,000,000 ≈ 130% of budget already consumed** — the team is already well over its real token budget while its request-based accounting shows nothing more alarming than "fully used, as expected." This is the concrete version of the gap Lesson 4's Concept J4 states conceptually: the two accounting systems can disagree substantially (100% vs. ~130%) on the exact same traffic — exactly within limits by one measure, already significantly over budget by the other.

**Tokenizing overhead is small relative to model latency — a quick check that Step 1's latency concern is a real but minor cost.** Tokenizing a ~2,000-token request with a fast byte-pair-encoding (BPE — a standard sub-word tokenization algorithm) tokenizer typically takes on the order of 1-2ms. Against a typical model TTFT of 200ms-2s (Step 1), that's a small fraction of a percent to about 1% overhead, depending on where in that TTFT range a given request falls — confirming that the latency cost of token-aware budget enforcement is real but small, not a reason to skip it.

**Trade-offs considered:** A hard per-request token cap (e.g. reject any single request over 20,000 tokens) would have prevented the scenario above entirely, but it also breaks legitimate long-context use cases — e.g. capstone #9's enterprise-chatbot "summarize this 80-page document" case needs exactly the kind of large single request a hard cap would reject. A softer, aggregate per-period budget (what's modeled above) allows occasional large requests through but requires real-time token metering infrastructure (Step 3) to actually enforce, rather than a single cheap per-request check.

---

## Step 3: Data Pipeline

What actually flows through this gateway operationally:
- **Request/response logs** — the request and response content (or a privacy-preserving hash/metadata-only version, per the trade-off below), timestamped and tagged by caller.
- **Token-usage metering records** — input and output token counts per request, tagged by API key / team / model, aggregated into running budget counters that Step 2's arithmetic depends on being accurate and close to real-time.
- **A cached-response store** — keyed by request content (Step 4 covers exact-match vs. semantic cache-key design in detail).
- **Provider health/latency telemetry** — rolling error rates and latency measurements per provider, feeding directly into the fallback logic in Step 4.

**Trade-offs considered:** Logging full request/response content gives complete debuggability and auditability when something goes wrong, at real privacy/compliance exposure and storage cost (the caller's actual prompts and completions are now stored somewhere). Logging only metadata (token counts, latencies, model/provider identifiers, a hashed version of the prompt for cache-key purposes) is cheaper and safer, but makes it much harder to debug a specific bad response after the fact — a real trade-off, not a solved problem.

---

## Step 4: Model/Agent Core Design — Routing, Fallback, and Caching Logic

**Routing strategies** — how the gateway picks which provider/model handles a given request:
- **Cost-based routing** — route to the cheapest provider/model that still meets a minimum required capability tier.
- **Capability-based routing** — route by a required feature (e.g. needs a 128K-token context window, needs function-calling support) that not every provider/model offers.
- **Latency-based routing** — route to whichever provider has the best recently-measured latency — the same underlying idea as DNS latency-based routing (Lesson 4's Concept J1), just applied at the application/request layer instead of the DNS layer, and able to react per-request instead of only as fast as a DNS TTL allows.

**Fallback logic:** the gateway tracks each provider's rolling error rate and latency over a short window (e.g. the last 60 seconds). If a provider's error rate exceeds a threshold (e.g. more than 5% of requests returning a 5xx server error — an HTTP status code in the 500-599 range indicating a server-side failure) or its p99 latency (the 99th-percentile response time — 99% of requests are faster than this value, 1% are slower; a standard way to measure tail latency rather than average-case performance, defined in full in Lesson 9's Concept 2) exceeds some multiple of its own recent baseline, the gateway marks it **unhealthy** and routes subsequent requests to the next provider in a configured priority list — retrying the failed request against that fallback provider if the failure is of a retryable kind (e.g. a timeout, not a content-policy rejection).

**Caching and routing interaction — a genuine, unresolved design tension, not a solved problem.** **Exact-match caching** keys a cached response on the literal request (model + full prompt + parameters) — simple, and always "correct" in the sense that an identical request previously got that exact answer, but it only produces a cache hit on byte-for-byte repeats. **Semantic caching** (Lesson 1's Concept B4 defines it in full: keying on an embedded representation of the prompt and matching on similarity rather than exact bytes) raises the hit rate substantially by matching near-duplicate-but-not-identical prompts — but this creates a real correctness question this capstone doesn't paper over: a semantic-cache hit returns an answer that was originally generated by *whichever* provider/model served the original request, which may not be the provider/model *this* request would have been routed to under the routing strategy above. Whether that's an acceptable approximation (the answer is "close enough" regardless of which model produced it) or a problem (different providers can have meaningfully different quality/behavior) is a product decision this gateway has to make explicit, not something a generic caching layer resolves for you.

**Sidebar — the token bucket algorithm.** *(First appearance in this repo of this specific algorithm; it doesn't yet have a lesson home.)*

- **Why?** Enforcing a rate limit needs an actual algorithm, not just "count things and reset periodically." A naive **fixed window** counter (e.g. "reset the counter to zero every 60 seconds") has a real flaw: a client can send the full limit right at the end of one window, then the full limit again right at the start of the next — two full limits' worth of traffic in a span of just a couple of seconds, right at the window boundary.
- **What?** A **token bucket** is a rate-limiting algorithm where a bucket holds up to some maximum capacity of "tokens" (a generic rate-limiting unit — not necessarily the same thing as an LLM token, though the next point makes them the same here on purpose). Tokens are added to the bucket at a steady, continuous rate up to that maximum capacity; each unit of incoming traffic consumes some number of tokens from the bucket; if the bucket doesn't have enough tokens available, the request is delayed or rejected. Because replenishment is continuous rather than a hard periodic reset, there's no window-boundary burst exploit the way there is with a fixed window.
- **How?** For this gateway specifically, the "tokens" consumed per request are literally set equal to that request's actual LLM token count (input and output) — so the bucket directly enforces a rate of LLM-tokens-per-second (or per day, for a daily budget), which is exactly the token-based (not request-based) enforcement this whole capstone's Step 1 objective calls for.

A concrete rate-limit config object showing how this is actually configured per key/team/model (illustrative, not any one product's literal schema):

```json
{
  "rate_limit_configs": [
    {
      "scope": "api_key",
      "id": "key_prod_team-growth",
      "bucket": {
        "capacity_tokens": 1000000,
        "refill_rate_tokens_per_sec": 11.57,
        "budget_period": "daily"
      }
    },
    {
      "scope": "team",
      "id": "team-growth",
      "bucket": {
        "capacity_tokens": 5000000,
        "refill_rate_tokens_per_sec": 57.87,
        "budget_period": "daily"
      }
    },
    {
      "scope": "model",
      "id": "large-context-model-v2",
      "bucket": {
        "capacity_tokens": 20000000,
        "refill_rate_tokens_per_sec": 231.48,
        "budget_period": "daily"
      }
    }
  ]
}
```

`capacity_tokens` is the bucket's maximum size (and the hard ceiling on burst size); `refill_rate_tokens_per_sec` is set so that a full bucket refills exactly once per `budget_period` (e.g. 1,000,000 tokens/day ÷ 86,400 seconds/day ≈ 11.57 tokens/sec). A single request can be checked against all three scopes it matches (its key, its team, and the model it targets) simultaneously, and is only admitted if every bucket it touches has enough tokens available.

**Trade-offs considered:** Cost-based routing minimizes spend but, used alone, can route a quality-sensitive request to a weaker/cheaper model purely because it's cheapest — it needs a capability floor gate in front of it, not use in isolation. Latency-based routing gives the best per-request user experience but can concentrate most traffic onto whichever single provider happens to be fastest at a given moment, undermining the provider-diversification benefit a multi-provider gateway was supposed to provide in the first place. Exact-match caching is simple and never introduces the cross-provider correctness question above, at the cost of a much lower hit rate than semantic caching would achieve.

---

## Step 5: Serving Architecture

**Request flow:** Client → Gateway (reverse proxy + L7 router + rate limiter + cache lookup, all in one component) → provider-selection logic (Step 4) → one of N backend providers/models → response flows back through the gateway (cache write, usage metering, logging) → client.

**Lesson 4's Concept J4 (reverse proxy vs. load balancer) is this capstone's whole premise, not an incidental overlap.** That Concept's point is that a single real product often plays reverse proxy (hiding the existence of multiple backend providers from the client, who only ever talks to one gateway endpoint), L7 load balancer (making routing decisions based on request *content* — the requested model, required capability — not just connection info), and rate limiter all at once. This gateway is exactly that: all three roles, one component, same as the real LiteLLM/Portkey/Cloudflare products this capstone is sourced from.

**Lesson 4's Concept J1 (DNS) sits one layer below this.** Before a client's request even reaches a specific regional deployment of this gateway, DNS-level geolocation or latency-based routing (Lesson 4's Concept J1) may already have picked which regional instance of the gateway handles it — a coarser-grained, slower-to-change routing decision than the per-request provider routing this gateway does once a request actually arrives.

**Lesson 3's Concept I3 (availability) applies directly to the gateway's own uptime.** Because every provider behind this gateway becomes unreachable if the gateway itself goes down (Step 1's non-functional constraint), the gateway needs its own redundancy — an active-active pool of gateway instances, not just a single instance — using the exact parallel-availability math Lesson 3's worked example runs (combining redundant replicas' failure probabilities, not their availabilities, to get a combined availability higher than any single instance).

**Trade-offs considered:** Running the gateway as a single logical service is simpler to reason about and monitor, but makes the gateway itself the weakest link in the entire serving chain — exactly the single-point-of-failure risk a multi-provider gateway was meant to protect *against*, just relocated one layer up instead of eliminated. Running it as an active-active redundant pool fixes that, at the cost of running (and keeping in sync — Step 3's telemetry and budget counters now need to be shared or reconciled across instances) more than one copy of the gateway itself.

---

## Step 6: Evaluation, Monitoring, and Iteration

**What to monitor in production:**
- **Cache hit rate**, tracked separately for exact-match and semantic caching, since (per Step 4) they carry different correctness guarantees and a blended number would hide which one is actually driving the hit rate.
- **Per-key/per-team budget burn rate** — tokens consumed vs. allotted, tracked close to real time so a team doesn't silently blow through its budget mid-period the way Step 2's worked example shows is possible under request-based accounting alone.
- **Fallback-trigger frequency per provider** — how often a given provider gets marked unhealthy; a rising trend over weeks is itself a signal, independent of any single incident.
- **Provider latency/error-rate dashboards**, per provider, feeding both the fallback logic (Step 4) and longer-term provider-selection decisions.

**What triggers a change:** A provider's fallback-trigger frequency trending upward over weeks (not just one bad day) is a signal to deprioritize or drop that provider from the routing pool entirely, rather than continuing to fall back to it repeatedly. A team's burn rate trending to exceed its budget before the period ends should trigger a proactive alert *before* a hard cutoff surprises them mid-task. A dropping cache hit rate after a product or prompt-template change is a signal to investigate whether the change broke the existing cache-key strategy (e.g. a prompt template that now embeds a timestamp defeats exact-match caching entirely, even though the semantically meaningful part of the prompt didn't change).

**Trade-offs considered:** Hard-cutting a team off the instant it hits 100% of its budget gives predictable, bounded cost control, but causes an outage for that team mid-task, possibly mid-conversation. A soft-overage model (let the team keep going, alert loudly, reconcile via billing afterward) keeps their workflow running uninterrupted, but requires an actual billing/reconciliation process to exist and risks real cost overrun if nobody acts on the alert in time. Neither option is universally correct — it's a product and finance decision as much as an engineering one.

---

## Source(s) and Further Reading

- LiteLLM open-source proxy documentation — **secondary/product-documentation** — OpenAI-compatible interface across 100+ providers; routing, retries, fallback, spend tracking, per-key/team/model rate limits.
- Portkey product documentation — **secondary/product-documentation** — managed control plane covering routing, load balancing, fallbacks, caching, guardrails, and budget limits.
- Cloudflare AI Gateway documentation — **secondary/product-documentation** — edge-hosted proxy covering caching, rate limiting, analytics, and logging.
- Lesson 1 (`lessons/lesson-1-ai-fundamentals-refresher.md`), Concepts B3 and B4 — model routing/gateways and LLM caching (semantic caching), referenced rather than re-derived.
- Lesson 3 (`lessons/lesson-3-scalability-and-availability.md`), Concept I3 — the series/parallel availability math this capstone's Step 5 applies directly to the gateway's own uptime.
- Lesson 4 (`lessons/lesson-4-network-and-delivery.md`), Concepts J1 and J4 — DNS-level routing underneath this gateway, and the reverse-proxy-vs-load-balancer framing that is this capstone's entire premise.
