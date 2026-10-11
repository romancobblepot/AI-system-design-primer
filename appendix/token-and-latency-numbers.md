# Token, Latency, and Cost Numbers Worth Memorizing

This is the AI-world equivalent of `system-design-primer`'s own "Latency numbers every programmer should know" table (itself credited there to Jeff Dean's "Designs, Lessons, and Advice from Building Large Distributed Systems" talk). It's a **flip-back reference, not a lesson** — skim it once, then come back to it whenever you need an order-of-magnitude anchor for a back-of-envelope estimate (Lesson 7, Concept 4) instead of guessing or re-deriving a number from scratch. Nothing here is new teaching; every figure either restates something this repo already established (with a pointer to exactly where), or is a freshly-verified external fact (with a source and a verification date, because pricing and context windows move fast enough that an unstamped number is close to useless).

**Provenance key, used on every row below:**
- **(this repo: Lesson N / capstone #X)** — already established elsewhere in this repo; the number here is transcribed, not re-derived, and the pointer tells you where to find the original derivation and its own trade-off discussion.
- **(verified via [source], as of 2026-10-11)** — confirmed by directly fetching or searching a live external source on the date this appendix was written. Treat it as correct as of that date, not permanently — re-verify before using it for a real budget or SLA, especially for pricing and context-window figures, which this repo's own verification pass found change within months.

---

## 1. Classic infrastructure latency numbers (carried forward from Lesson 7)

An AI-serving system still runs on top of all of this — a back-of-envelope estimate that only knows AI-specific numbers will badly misjudge anything that bottlenecks on plain network or disk latency. Reproduced here (not re-derived) because this appendix is the thing you actually flip back to, not Lesson 7's Concept 4 prose.

| Reference quantity | Approximate value | Provenance |
|---|---|---|
| L1 cache reference | ~0.5 ns | (this repo: Lesson 7, Concept 4 — originally `system-design-primer`'s own Appendix) |
| Main memory reference | ~100 ns | (this repo: Lesson 7, Concept 4) |
| Round trip within the same datacenter | ~500 µs | (this repo: Lesson 7, Concept 4) |
| Read 1 MB sequentially from SSD | ~1 ms | (this repo: Lesson 7, Concept 4) |
| HDD seek | ~10 ms | (this repo: Lesson 7, Concept 4) |
| Packet round trip, California ↔ Netherlands | ~150 ms | (this repo: Lesson 7, Concept 4) |
| TCP three-way handshake, at 40ms RTT | 1 RTT = 40 ms (paid once per connection) | (this repo: Lesson 6, Concept 3's worked example) |
| TCP + TLS 1.3 handshake, at 40ms RTT | ≈2 RTT = 80 ms (paid once per connection) | (this repo: Lesson 6, Concept 3 / Lesson 7, Concept 4) |
| AWS ALB default idle timeout | 60 seconds | (this repo: Lesson 6, Concept 4 — cited from AWS's own ALB documentation) |

---

## 2. Context window sizes

**Hosted frontier models** (verified by directly fetching each provider's own current model-overview/pricing pages — not a third-party aggregator — on 2026-10-11):

| Model family | Context window | Max output | Provenance |
|---|---|---|---|
| Claude (Opus 5.5, Sonnet 5.5, Haiku 5.5, Fable 5.1 — current lineup) | 1,000,000 tokens, all four | 128,000 tokens | (verified via platform.claude.com/docs, as of 2026-10-11) |
| GPT (gpt-6-astra, gpt-6.1-sol, gpt-6-sol, gpt-6-luna — current text lineup) | 1,050,000 tokens (≈1.05M), all four | 128,000 tokens | (verified via developers.openai.com/api/docs/models, as of 2026-10-11) |
| Gemini (2.5 Flash, confirmed directly; 2.5 Pro / 3.1 Pro, widely reported but not confirmed on Google's own pricing page in this pass) | 1,000,000 tokens (2.5 Flash confirmed; Pro tier reported at 1,048,576 tokens by third-party aggregators, not independently confirmed here) | Not stated on the fetched page | (verified via ai.google.dev/gemini-api/docs/pricing for Flash, as of 2026-10-11; Pro figure — lower confidence, third-party-sourced) |

**Takeaway worth remembering, not just the raw numbers:** every current *hosted* frontier model family has converged on a context window in the 1,000,000–1,050,000-token range — this is itself a useful anchor: if a design assumption is "a 32K or 128K context ceiling," check whether that's still true for the model actually being targeted, since the frontier moved well past that in the time this repo's own Lesson 1 (Concept A2) was first framing "context window as a resource."

**Open-weight models** (lower confidence — these figures come from third-party comparison blogs, not each model's own primary model card, and this appendix's own verification pass found real disagreement between sources on at least one figure below; re-check the primary model card before relying on any of these for a real design decision):

| Model family | Reported context window | Provenance |
|---|---|---|
| Llama 4 Scout | 10,000,000 tokens (reported) | (verified via web search aggregators, as of 2026-10-11 — not independently confirmed against Meta's own model card in this pass) |
| Llama 4 Maverick | 1,000,000 tokens reported by one source, 130,000 tokens reported by another — **genuinely conflicting**, not resolved here | (verified via web search aggregators, as of 2026-10-11 — flagged low-confidence) |
| DeepSeek V4 (Pro / Flash) | 1,000,000 tokens, both variants | (verified via web search aggregators, as of 2026-10-11) |
| Mistral Large 3 / Small 4 | 256,000 tokens, both | (verified via web search aggregators, as of 2026-10-11) |

---

## 3. $/1M-token pricing by provider tier

**The illustrative anchor this repo actually computes with.** Lesson 7's Concept 4 and capstone #13 (`solutions/autonomous-coding-agent`) both deliberately reuse the *same* illustrative rate for every back-of-envelope cost calculation in this repo — **$3/1M input tokens, $15/1M output tokens** — explicitly stated in both places as "not any single named provider's current, literal rate," chosen for consistency across this repo's own worked examples, not as a claim about real market pricing. **(this repo: Lesson 7, Concept 4 / capstone #13, Step 2)**. Don't confuse this anchor with the real provider tiers below — they're kept deliberately separate throughout this repo, and this appendix keeps that separation too.

**Real provider pricing** (verified by directly fetching each provider's own current pricing page on 2026-10-11 — these are official first-party sources, not aggregators, but see the note below on how fast they're already churning):

| Provider / model | Input $/1M tokens | Output $/1M tokens | Provenance |
|---|---|---|---|
| Claude Haiku 5.5 | from $0.10 (≤100K prompt) | from $0.50 (≤100K prompt) | (verified via platform.claude.com/docs/en/about-claude/pricing, as of 2026-10-11) |
| Claude Sonnet 5.5 | $2 | $10 | (verified via platform.claude.com/docs, as of 2026-10-11) |
| Claude Opus 5.5 | $4 | $20 | (verified via platform.claude.com/docs, as of 2026-10-11) |
| Claude Fable 5.1 | $10 | $50 | (verified via platform.claude.com/docs, as of 2026-10-11) |
| GPT gpt-6-luna | $0.10 | $0.50 | (verified via developers.openai.com/api/docs/pricing, as of 2026-10-11) |
| GPT gpt-6.1-sol / gpt-6-sol | $2.00 | $10.00 | (verified via developers.openai.com/api/docs/pricing, as of 2026-10-11) |
| GPT gpt-6-astra | $10.00 | $50.00 | (verified via developers.openai.com/api/docs/pricing, as of 2026-10-11) |
| Gemini 2.5 Flash | $0.30 (text) | $2.50 | (verified via ai.google.dev/gemini-api/docs/pricing, as of 2026-10-11) |
| Gemini 2.5 Pro | $1.25 (≤200K prompt) | $10.00 (≤200K prompt) | (verified via ai.google.dev/gemini-api/docs/pricing, as of 2026-10-11) |
| Gemini 3.1 Pro | $2.00 (≤200K prompt) | $12.00 (≤200K prompt) | (verified via ai.google.dev/gemini-api/docs/pricing, as of 2026-10-11) |

**Common cost-reduction levers, all confirmed directly on these same pricing pages:** batch processing at roughly 50% off the standard rate (Claude and GPT both confirm this); prompt-cache reads at 2.5–10% of the base input price on Claude — the rate varies by model tier, not a single flat discount: standard models (e.g. Haiku 5.5) get 0.1x (10%), Opus 5.5 and Sonnet 5.5 get 0.05x (5%), and Claude Fable 5.1 and Mythos 5.1 — two of the four models in this very pricing table above — get the lowest rate, 0.025x (2.5%); long-context surcharges once a prompt crosses a provider-specific threshold (200,000 tokens for Gemini's Pro tier; 272,000 tokens for GPT's "long context" tier, per the fetched pricing page). **(verified via each provider's own pricing page, as of 2026-10-11)**

**The one-line lesson this whole section teaches, independent of which exact numbers are current by the time you're reading this:** every major provider's pricing page is already several model generations past whatever this document's own training data would have guessed — tagging a number with its verification date isn't bureaucratic caution, it's the only thing that makes the number trustworthy at all. Re-run the fetch before you budget against any figure in this table.

---

## 4. Embedding dimensions

| Model | Dimensions | Provenance |
|---|---|---|
| OpenAI `text-embedding-3-small` | 1,536 (default; can be shortened via the `dimensions` parameter) | (verified via OpenAI's own embeddings documentation, as of 2026-10-11) |
| OpenAI `text-embedding-3-large` | 3,072 (default; shortenable the same way) | (verified via OpenAI's own embeddings documentation, as of 2026-10-11) |
| Cohere `embed-english-v3.0` | 1,024 | (verified via Cohere product documentation, as of 2026-10-11) |
| Voyage `voyage-3-large` / `voyage-4-large` | 256 / 512 / 1,024 / 2,048 (Matryoshka — one model, selectable output size; 1,024 or 2,048 is the reported default depending on source) | (verified via Voyage AI product pages, as of 2026-10-11 — the exact default conflicts slightly between sources, flagged as lower confidence) |
| Gemini `text-embedding-004` | Used in Anthropic's own Contextual Retrieval benchmark (the model behind the 35%/49%/67% failure-rate-reduction figures in §6 below) | (this repo: capstone #9, Step 1 — the model name is source-confirmed there; its exact dimensionality is not stated in that source) |
| This repo's own illustrative assumptions | 2,048-dim (capstone #1, Pinterest visual search) and 1,024-dim (capstone #9, RAG/Contextual Retrieval) | (this repo: capstone #1, Step 2 / capstone #9, Step 2 — both explicitly flagged there as illustrative, not stated by either source paper) |

**Pattern worth remembering:** "hundreds to low thousands of dimensions" (Lesson 1, Concept C1's own phrasing) holds up across every real embedding model checked here — 1,024 and 1,536 are the two most common defaults among current commercial models, with 3,072 (OpenAI's large tier) and a 256-to-2,048 Matryoshka range (Voyage) as the outliers on either end.

---

## 5. Vector-search (ANN) latency

| Scenario | Latency | Provenance |
|---|---|---|
| Pinecone, dense index, 10M records, one namespace | p50 16 ms / p90 21 ms / p99 33 ms | (verified via Pinecone's own product page, as of 2026-10-11 — Pinecone's own marketing figures; query rate, hardware, and vector dimensionality behind these numbers aren't disclosed on that page) |
| Pinecone, sparse index, 10M records, one namespace | p50 8 ms / p90 20 ms / p99 51 ms | (verified via Pinecone's own product page, as of 2026-10-11) |
| Pinecone, real production workload, 135M vectors, 600 QPS sustained | p50 45 ms / p99 96 ms | (verified via a Pinecone customer case study reported by Blocks and Files, as of 2026-10-11 — one customer's workload, not a general benchmark) |
| Pinecone, load test, same 135M-vector deployment, 2,200 QPS | p50 60 ms / p99 99 ms | (verified via the same Blocks and Files report, as of 2026-10-11) |

**Cross-reference to this repo's own mechanism explanation:** every figure above is produced by the HNSW-style approximate-nearest-neighbor indexing Lesson 1's Concept C2 defines in full (a graph-based index trading exact correctness for sub-linear query time) — this section gives the real-world *latency numbers* that mechanism produces at scale; Lesson 1 gives the *mechanism*, and capstone #1's own Hamming-distance brute-force scan (over *binarized* embeddings, a different technique entirely — see §4 and §7 below) is this repo's own worked example of the scatter-gather query pattern these latencies are measured against. **(this repo: Lesson 1, Concept C2 / capstone #1, Step 5)**

**Order-of-magnitude takeaway:** real production ANN query latency across these data points lands in the **tens of milliseconds at p50, under 100ms at p99**, fairly consistently from 10M to 135M vectors — a useful sanity-check anchor per Lesson 7's Concept 4 Step 4 (an estimate that comes out at "3ms" or "3 seconds" for a vector-search step is almost certainly a units or scale mistake, not a real result).

---

## 6. Token-generation latency (TTFT and inter-token)

| Metric | Target | Provenance |
|---|---|---|
| p50 time-to-first-token (TTFT) | < 200 ms | (this repo: capstone #10, `solutions/llm-inference-serving`, Step 1) |
| p99 TTFT | < 1.5 s | (this repo: capstone #10, Step 1) |
| p50 inter-token latency | < 40 ms/token | (this repo: capstone #10, Step 1) |
| p99 inter-token latency | < 120 ms/token | (this repo: capstone #10, Step 1) |
| LLM gateway's own added-latency budget, on top of the above | < 20 ms | (this repo: capstone #15, `solutions/llm-api-gateway`, Step 1) |
| Tokenizing a ~2,000-token request (BPE) | ~1–2 ms | (this repo: capstone #15, Step 2) |
| Illustrative batch-size/throughput trade-off: batch 1 | 50 ms/token → 20 tokens/sec aggregate | (this repo: Lesson 3, Concept 1 — explicitly an illustrative, not production-measured, table) |
| Illustrative batch-size/throughput trade-off: batch 32 | 80 ms/token → 400 tokens/sec aggregate | (this repo: Lesson 3, Concept 1) |

**Why TTFT and inter-token latency are tracked separately, not as one number:** TTFT is dominated by how long the model takes to process the *entire input prompt* before producing any output at all; inter-token latency is the steady-state per-token cost once generation has started. A system can hit its inter-token target comfortably while still blowing its TTFT target on a long-context request, or vice versa — which is exactly why capstone #10's own Step 1 states both as separate SLA targets rather than one blended "response latency" number. **(this repo: Lesson 3, Concept 1 / capstone #10, Step 1)**

---

## 7. KV-cache memory per token

| Quantity | Value | Provenance |
|---|---|---|
| KV-cache bytes per token, formula | `2 (K and V) × num_layers × hidden_dim × bytes_per_value` | (this repo: capstone #10, Step 2) |
| Worked result for a 13B-class model (32 layers, hidden dim 4096, FP16) | 512 KB/token (0.5 MB/token) | (this repo: capstone #10, Step 2) |
| KV cache for one full-length 2,500-token conversation (2,000 context + 500 generated), same model | ≈1.22 GB | (this repo: capstone #10, Step 2) |
| Max concurrent full-length requests on one 80GB GPU, same model (≈52GB available for KV cache after weights) | ≈42 requests | (this repo: capstone #10, Step 2) |
| Naive (non-PagedAttention) KV-cache memory waste, from internal + external fragmentation | 60–80% of allocated memory | (this repo: capstone #10, Step 4 — sourced from the vLLM/PagedAttention paper, Kwon et al., SOSP 2023) |
| Same waste, under PagedAttention | under 4% | (this repo: capstone #10, Step 4 — same source) |
| Character.AI's reported KV-cache-reuse serving-cost reduction (secondary/unconfirmed) | ~33x | (this repo: capstone #10, Step 1/6 — explicitly flagged there as a widely-covered-secondhand claim with no confirmed still-live primary source, not carrying the same evidentiary weight as the vLLM paper's own figures above) |
| GPU memory capacities this math is sized against | H100: 80GB · H200: 141GB · B200: 180–192GB (sources disagree on the exact B200 figure) | (verified via web search aggregators of vendor datasheets, as of 2026-10-11) |

**Why this is the single most important derivation in this whole appendix to actually be able to reproduce:** capstone #10's own stated lesson is that GPU *memory*, not GPU *compute* (FLOPs), is what actually runs out first in LLM serving — and the formula in the first row above is the entire reason that's true: KV-cache memory grows linearly with context length and concurrent requests, while most back-of-envelope intuition (carried over from CPU-bound systems) reaches for compute first. **(this repo: capstone #10, Step 2)**

---

## 8. $/1M-token cost worked examples already computed in this repo

Not new numbers — a pointer to where this repo already did the arithmetic, so you don't have to re-derive it:

| Scenario | Result | Provenance |
|---|---|---|
| 50,000-user RAG chatbot, 10 msg/user/day, 1,500 input + 300 output tokens/msg, at the $3/$15 illustrative anchor | $4,500/day (≈$135,000/month); required peak throughput ≈25,000 tokens/sec | (this repo: Lesson 7, Concept 4) |
| Anthropic's own confirmed Contextual Retrieval ingestion cost | $1.02 per million *document* tokens (one-time, at indexing time) | (this repo: capstone #9, Step 2 — source-confirmed directly from Anthropic's own "Introducing Contextual Retrieval" post) |
| Autonomous coding agent, illustrative per-task cost at 200 round-trips/task, $3/$15 anchor | ≈$3.00/task ($2.70 LLM + $0.30 sandbox compute) | (this repo: capstone #13, Step 2 — explicitly flagged as highly sensitive to the round-trip-count assumption; could rise to ≈$27+/task if round-trips are closer to the source's own "thousands of decisions" claim) |
| Running the full SWE-bench benchmark once (2,294 tasks) at that same ≈$3/task figure | ≈$6,882 | (this repo: capstone #13, Step 2 — a sanity-check figure, not a claim about Cognition's actual spend) |

---

## 9. Availability ("nines") quick reference

Reproduced directly from Lesson 3, Concept 3 — the formulas and the table both, since this is exactly the kind of thing you flip back to mid-estimate rather than re-derive:

| Availability | Nines | Downtime/year |
|---|---|---|
| 99% | "two nines" | ~3.65 days |
| 99.9% | "three nines" | ~8.77 hours |
| 99.99% | "four nines" | ~52.6 minutes |
| 99.999% | "five nines" | ~5.26 minutes |

```
Series availability (chain, all must succeed):     A_combined = A1 × A2 × ... × An
Parallel availability (redundant, one must succeed): A_combined = 1 − [(1−A1) × (1−A2) × ...]
```
**(this repo: Lesson 3, Concept 3)**

**Worked results already on record elsewhere in this repo**, so you don't have to recompute them:

| Scenario | Combined availability | Downtime/year | Provenance |
|---|---|---|---|
| Gateway (99.95%) → inference backend (99.9%) → vector DB (99.99%), in series | 99.8401% | ≈14 hours | (this repo: Lesson 3, Concept 3) |
| Same chain, with the inference backend made active-active redundant | 99.9399% | ≈5.3 hours | (this repo: Lesson 3, Concept 3) |
| Three newly-decomposed microservices (supervisor/specialist/validator), each 99.9%, in series, no added redundancy | 99.7003% | ≈26.3 hours | (this repo: Lesson 7, Concept 1) |
| Same three services, each made active-active redundant first | 99.9997% | ≈1.6 minutes | (this repo: Lesson 7, Concept 1 — at the cost of 6 total replicas instead of 3) |

---

## 10. Caching hit-rate reference points

| Scenario | Hit rate | Downstream effect | Provenance |
|---|---|---|---|
| Exact-match prompt cache, real support-chatbot traffic | ~5% | Database/LLM load reduced by only 5% — most repeat questions are phrased differently each time | (this repo: Lesson 5, Concept 4) |
| Same traffic, semantic cache at a 0.95 cosine-similarity threshold | ~40% | 8x the hit rate of exact-match, at some false-positive risk | (this repo: Lesson 5, Concept 4) |
| CDN pull-cache example, chat-UI static assets | 95% | Origin server load reduced by 95% (the two percentages are numerically identical by definition) | (this repo: Lesson 4, Concept 2) |
| Database cache-aside layer, before a cache-eviction storm | 92% hit rate → 3,200 QPS reaching a 5,000-QPS-ceiling DB | 36% headroom | (this repo: Lesson 5, Concept 3) |
| Same system, after the storm | 85% hit rate → 6,000 QPS reaching the same DB | 20% *over* capacity — a 7-point hit-rate drop flips the system from comfortable to overloaded | (this repo: Lesson 5, Concept 3) |

---

## 11. Queueing and async reference numbers

| Quantity | Value/formula | Provenance |
|---|---|---|
| Little's Law | `N = λ × W` (average items in system = arrival rate × average time in system) | (this repo: Lesson 6, Concept 2 — original proof: Little, 1961) |
| Bounded-queue time to fill under back pressure | `time_to_full = max_queue_depth / (arrival_rate − drain_rate)` | (this repo: Lesson 6, Concept 2) |
| Worked example: 2,000-depth queue, net overflow of 30 tasks/sec | ≈66.7 seconds to hit the bound | (this repo: Lesson 6, Concept 2) |
| Task-queue worker sizing, RAG ingestion (2M chunks / 4-hour window, 5 chunks/sec/worker) | 28 workers | (this repo: Lesson 6, Concept 1 / capstone #9, Step 5 — the same figure, confirmed consistent across both documents) |
| HTTP 429 ("Too Many Requests") | the standard explicit-rejection back-pressure signal | (this repo: Lesson 6, Concept 2) |
| Timeout ratio, 90-minute agent task vs. a 60-second gateway idle timeout | 90x | (this repo: Lesson 6, Concept 4 / capstone #13, Step 5 — the same figure, confirmed consistent across both documents) |

---

## 12. Network, DNS, and CDN reference numbers

| Quantity | Value/formula | Provenance |
|---|---|---|
| DNS worst-case failover exposure | `detection_and_update_time + ttl_remaining_at_moment_of_failure` (up to the full TTL) | (this repo: Lesson 4, Concept 1) |
| Worked example: 300-second TTL | up to 5 extra minutes of traffic to a dead region, on top of detection/fix time | (this repo: Lesson 4, Concept 1) |
| Request-based vs. token-based rate-limit blind spot, 100 req/min at a 128K-token context window | worst case 12,800,000 tokens/min — 25.6x the exposure a 500,000-tokens/min token-based limit would actually bound (`12,800,000 ÷ 500,000`) | (this repo: Lesson 4, Concept 4) |
| Same blind spot, per-request spread it hides (128,000-token request vs. a 50-token request, both counted identically as "1 request" under a request-based limit) | ~2,560x difference in actual GPU compute/cost between the two requests (`128,000 ÷ 50`) — this is the figure Lesson 4's own worked example states; don't confuse it with the 25.6x row above, which is a different comparison | (this repo: Lesson 4, Concept 4) |
| Token-bucket refill rate for a 1,000,000-token/day budget | ≈11.57 tokens/sec (`1,000,000 ÷ 86,400`) | (this repo: capstone #15, Step 4) |

---

## 13. Reading this table going forward

Per Lesson 7's Concept 4 Step 4 (sanity-checking an estimate's order of magnitude): the numbers in §§6–7 and §9–12 are this repo's own already-verified internal figures — safe to cite directly, with a pointer back to their original derivation if anyone asks "where did that come from." The numbers in §§2–3 and §5 (context windows, $/1M pricing, open-weight context claims, vector-search latency) are external facts with a **verification date stamped on every single row** — re-fetch before trusting them for a real budget, SLA, or architecture decision, because this appendix's own research pass found meaningful drift (new model generations, changed pricing tiers) versus what this repo's own lessons assumed when they were first written. That drift is itself the one number worth remembering above all the others: **assume any unstamped AI pricing or context-window figure you encounter elsewhere is already stale.**
