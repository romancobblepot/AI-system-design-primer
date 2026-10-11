# Capstone #10: LLM Inference Serving at Scale

**Source(s):** Primary — Kwon et al., *"Efficient Memory Management for LLM Serving with PagedAttention,"* SOSP 2023 (arXiv:2309.06180) — the vLLM paper, source of the actual mechanism this capstone is built around. Secondary/unconfirmed — Character.AI's Noam Shazeer, June 2024 engineering post reporting a ~33x serving-cost reduction via KV-cache reuse across conversation turns.

**Confidence:** The PagedAttention mechanism (Steps 4-5 below) is grounded in a primary, peer-reviewed source — a named research team's own published paper with its own benchmark numbers. The Character.AI production result is **not** presented with the same confidence: it is widely covered secondhand, and no still-live primary URL for it could be confirmed. It's included because the ~33x figure is a genuinely useful illustration of what KV-cache-focused optimization can achieve in production, but treat it as a reported claim, not a verified one, and don't cite it as if it carries the same evidentiary weight as the vLLM paper.

**Scope note:** This capstone is the inference-serving layer only — one model, running efficiently, at scale, for one deployment. It does **not** cover routing a request across *multiple* providers or models, rate limiting, or fallback-on-outage — that's a distinct, separate concern covered by capstone #15 (`case-studies/llm-api-gateway`), which sits in front of a system like this one. It also does not cover model training, fine-tuning, or output quality/safety evaluation (Lesson 9's territory) — this capstone is purely "how do you serve a fixed, already-trained model's inference requests efficiently."

---

## Step 1: Clarify Requirements & Frame the Objective

Unlike a classic ML-prediction capstone (where Step 1's objective is a metric like precision@k or CTR), this is an infrastructure capstone — its "objective" is a set of **SLA** (service-level agreement — a committed performance target) and cost targets, not a prediction-quality metric. That's a legitimate variant of this step, not a shortcut around it: get these targets wrong and every downstream architecture decision (Steps 4-5) optimizes for the wrong thing, exactly the failure mode Step 1 exists to prevent.

**Functional scope:** Serve chat-completion-style requests (a prompt in, a streamed sequence of generated tokens out) for a single, already-trained LLM, across many concurrent users and conversations, on a fixed pool of GPU hardware.

**Non-functional targets (the actual numbers being optimized for):**
- **p50 / p99 time-to-first-token (TTFT)** — p50 (median) and p99 (99th-percentile, i.e. "no worse than this for 99% of requests") targets for the delay before the first generated token arrives. Example targets: p50 TTFT < 200ms, p99 TTFT < 1.5s.
- **p50 / p99 inter-token latency** — the delay between each subsequent token. Example targets: p50 < 40ms/token, p99 < 120ms/token.
- **Aggregate token-generation throughput** — the system-wide rate (tokens/sec) the serving cluster sustains under peak load.
- **Cost per 1M tokens served** — the actual dollar cost target, derived from GPU-hour cost divided by tokens served, which Step 2 and Step 6 both depend on.

**Equivalent of "ground truth / feedback signal":** for a prediction task this would be labeled data; here it's the production SLO (service-level objective — the internal target a team holds itself to, usually stricter than the externally promised SLA) compliance measurements themselves — real measured p99 latency and real measured cost-per-token, tracked continuously (Step 6), compared against the targets stated above.

**Explicitly out of scope:** multi-provider routing and fallback (capstone #15), model training/fine-tuning, and output-quality evaluation (Lesson 9).

**Trade-offs considered:** Setting an aggressive p50 TTFT target (prioritizing a snappy single-conversation experience) and a high aggregate-throughput target *at the same time* is itself a trade-off commitment, not a free combination — Lesson 3's Concept I1 shows exactly why: larger batch sizes raise aggregate throughput but raise individual-request latency. Stating both targets up front, with explicit priority if they conflict under real load, is what prevents an ad hoc "just lower the batch size when it's slow" fix from silently blowing the throughput target instead.

---

## Step 2: Back-of-Envelope Constraints

**Assumptions for this estimate** (realistic, not the only valid choice): a 13B-parameter-class model, 32 transformer layers, hidden dimension 4096, served at FP16 precision (16-bit floating point — 2 bytes per number), on a single 80GB GPU (e.g. an A100 80GB). Target: sustain 1,000 concurrent active conversations cluster-wide, average context length 2,000 tokens, average generation length 500 tokens per conversation.

**Model weight memory:** 13 billion parameters × 2 bytes/parameter = 26GB. That leaves roughly 80GB − 26GB − ~2GB (activations and other runtime overhead) ≈ **52GB available for KV cache** on this one GPU.

**KV-cache memory per token — the calculation that makes "KV cache is the bottleneck, not FLOPs" concrete rather than asserted.** The KV cache (Lesson 1's Concept B1 defines it in full: the stored key/value tensors from every previously-processed token, kept so each new token's attention computation doesn't have to recompute them) stores, per token, one key vector and one value vector for *every* layer:

```
KV-cache bytes per token = 2 (K and V) × num_layers × hidden_dim × bytes_per_value
                         = 2 × 32 × 4096 × 2
                         = 524,288 bytes
                         = 512 KB/token  (0.5 MB/token)
```

For one conversation reaching 2,500 tokens total (2,000 context + 500 generated) held resident in GPU memory at its peak:

```
KV cache for one full-length request = 2,500 tokens × 0.5 MB/token = 1,250 MB ≈ 1.22 GB
```

**That single number is the whole point of this step.** One request, at a realistic length, consumes over a gigabyte of GPU memory just for its KV cache — before counting a single FLOP of actual matrix-multiply compute. With ~52GB available for KV cache on this GPU:

```
Max concurrent full-length requests per GPU ≈ 52GB / 1.22GB ≈ 42 requests
```

To sustain the targeted 1,000 concurrent conversations cluster-wide, this implies roughly **1,000 / 42 ≈ 24 GPUs** of this class are needed *purely to hold KV cache* — a cluster-sizing number driven by memory capacity, not by how many FLOPs these GPUs can compute. This is the concrete evidence behind the capstone's own stated lesson: GPU compute (FLOPs) is rarely what runs out first in LLM serving; GPU memory, consumed by the KV cache, is.

**Trade-offs considered:** A smaller or more aggressively quantized model (Lesson 1's Concept B1 defines quantization) shrinks both the weight memory *and* the per-token KV-cache size proportionally, buying more concurrent-request headroom per GPU at some cost to output quality. Architectural changes like multi-query or grouped-query attention (sharing key/value projections across multiple attention heads) reduce per-token KV-cache size directly — but that's a training-time model-architecture decision, not something a serving team can retrofit onto an already-trained model at serving time.

---

## Step 3: Data / Knowledge Pipeline

For a classic ML-prediction capstone, this step is about training data — collection, labeling, freshness. That doesn't apply here in the same shape, and it would be dishonest to pretend it does: **this capstone has no training-data pipeline at all** — it serves an already-trained, fixed model. What actually "flows through" this system operationally is:

- **Incoming prompts** — the user's (or upstream application's) input text, tokenized on arrival.
- **Generated output tokens** — streamed back to the caller as they're produced.
- **Usage/cost telemetry** — input and output token counts per request, tagged by whatever caller/tenant identifier is relevant, feeding directly into the cost-per-token tracking Step 1 set as a target and Step 6 monitors continuously.
- **Latency telemetry** — TTFT and inter-token latency measured per request, feeding the p50/p99 dashboards Step 6 depends on.

**Trade-offs considered:** Logging full prompt and completion text for every request gives complete debuggability when something goes wrong, but means storing potentially sensitive user content at scale, with real storage cost and privacy/compliance exposure. Logging only token counts and latencies (no content) is cheaper and safer, but means a specific bad response can't be inspected after the fact — only its statistics.

---

## Step 4: Model/Agent Core Design — PagedAttention

### Why naive KV-cache allocation wastes memory

A naive serving system allocates each request's KV cache as a single contiguous block of GPU memory, sized up front for that request's *maximum possible* sequence length (since a basic attention implementation expects its K/V tensors to sit in one contiguous memory region). This produces two distinct kinds of waste, borrowing the vocabulary from operating-systems memory management:
- **Internal fragmentation** — if a request's actual generation ends up shorter than the maximum length it reserved space for, that unused reserved space sits idle inside the block and can't be handed to any other request, even though it's technically "free."
- **External fragmentation** — as different requests of different reserved sizes finish and free their memory at different times, the freed space ends up scattered into a patchwork of gaps too small or oddly-placed to satisfy a new request's contiguous-block requirement, even when the *total* free memory would otherwise be enough.

The vLLM paper reports that systems using this naive approach waste roughly **60-80% of allocated KV-cache memory** to exactly these two effects.

### What PagedAttention does instead

**PagedAttention** borrows the core idea of **virtual memory paging** from operating systems: instead of giving a process one contiguous block of physical memory, an OS divides its logical address space into fixed-size **pages**, maps each page to a (possibly non-contiguous) physical memory **frame** via a **page table**, and lets the process address memory logically without caring where its pages actually sit physically.

PagedAttention applies the same idea to KV cache: each request's KV cache is divided into fixed-size **blocks** (the KV-cache analog of a page), which can be stored **non-contiguously** anywhere in GPU memory. A per-request **block table** (the analog of a page table) tracks which physical block holds which logical position in that request's sequence. Critically, vLLM's custom GPU attention kernel is written to read K/V values across these non-contiguous blocks directly — something a naive contiguous-memory attention implementation cannot do — so this isn't just a bookkeeping change, it required a new attention kernel to actually exploit it.

Because any free block, located anywhere in memory, can now be handed to any request that needs one more block, both fragmentation types above are eliminated at the source rather than mitigated: there's no "reserved-but-unused" internal waste (blocks are only allocated as a sequence actually grows, one block at a time) and no external fragmentation (there is no contiguous-block requirement left to violate). The paper reports this reduces memory waste from the naive system's 60-80% down to under 4%.

**Cross-request block sharing:** because blocks are addressed indirectly through a block table rather than owned exclusively by one request, multiple requests sharing an identical prefix — e.g. several parallel decodes sampling from the same prompt, or multiple users whose conversations start with the same long system prompt — can literally point their block tables at the *same* physical blocks for that shared prefix, using **copy-on-write** (the same mechanism behind OS process forking: multiple logical owners share one physical copy until one of them needs to modify it, at which point only that owner gets a private copy). This turns a shared prefix into a one-time memory cost instead of a per-request duplicate.

A simplified sketch of the core allocator logic (illustrative, not vLLM's actual production code):

```python
BLOCK_SIZE = 16  # tokens per block, a tunable constant

class PagedKVCacheAllocator:
    def __init__(self, total_blocks: int):
        self.free_blocks = list(range(total_blocks))   # pool of physical block IDs
        self.block_tables: dict[str, list[int]] = {}    # request_id -> [physical_block_ids]

    def allocate_block(self, request_id: str) -> int:
        if not self.free_blocks:
            raise MemoryError("No free KV-cache blocks — evict, swap, or preempt a request")
        block_id = self.free_blocks.pop()
        self.block_tables.setdefault(request_id, []).append(block_id)
        return block_id

    def needs_new_block(self, request_id: str, tokens_generated_so_far: int) -> bool:
        blocks_held = len(self.block_tables.get(request_id, []))
        return tokens_generated_so_far > blocks_held * BLOCK_SIZE

    def free_request(self, request_id: str) -> None:
        self.free_blocks.extend(self.block_tables.pop(request_id, []))
```

**Trade-offs considered:** Static pre-allocation (the naive approach above) has slightly lower per-step bookkeeping overhead — no block-table indirection to resolve on every attention computation — but wastes the 60-80% of memory described above, meaning far fewer concurrent requests fit per GPU. Plain continuous batching (Lesson 1's Concept B1, Lesson 3's Concept I1) without PagedAttention still helps throughput by letting multiple requests share a GPU forward pass, but if the underlying KV-cache memory is still contiguously allocated per request, it still suffers the same fragmentation problem underneath — continuous batching and PagedAttention solve two different layers of the same problem (which requests are in the active batch, vs. how their memory is physically managed) and are complementary, not competing, techniques. PagedAttention's own block-table indirection is a real, if small, added cost per attention computation — the paper's benchmarks show this cost is comfortably outweighed by the throughput gained from serving far more concurrent requests per GPU.

---

## Step 5: Serving Architecture

The request lifecycle: an incoming request is tokenized and placed in a waiting queue. A **scheduler** admits waiting requests into the currently **running batch** as soon as enough free KV-cache blocks exist to hold at least one more block for a new or continuing request — note that admission is gated on *free blocks*, not on a fixed request-count limit, which is itself a direct consequence of Step 4's design. Each decode step, every request currently in the running batch produces one new token and consumes (at most) one new block; requests that finish free their blocks back into the shared pool for waiting requests.

Under memory pressure, the scheduler can use **preemptive scheduling**: temporarily evicting a lower-priority or longer-running request's blocks out to CPU memory (**swapping**, the same term used for OS virtual-memory swapping), freeing GPU memory immediately for a higher-priority request, then swapping the evicted request's blocks back into GPU memory to resume it later — trading a slower resume (the CPU-to-GPU transfer cost) for not having to reject the new request outright.

**This is the same batch-size/throughput-latency knob Lesson 3's Concept I1 walks through, applied at the scale this paper's benchmarks report.** Lesson 3's I1 table shows batch size trading per-token latency for aggregate throughput at a small illustrative scale (batch 1 → 20 tokens/sec at 50ms/token; batch 32 → 400 tokens/sec at 80ms/token). PagedAttention is what lets that batch size actually grow large in production — at the scale where GPU *memory* (not GPU compute) is the binding constraint, exactly the regime Step 2's arithmetic above puts this system in.

**This serving system is also the "inference backend" node in Lesson 3's Concept I3 availability chain.** That Concept's worked example computes combined availability for a gateway → inference backend → vector DB chain in series (≈99.84%, ~14 hours/year downtime), then shows that making just the inference backend redundant — an active-active pool of two independently-available replicas — brings the whole chain's downtime down to ~5.3 hours/year. A pool of PagedAttention-backed replicas like the one described in this step is literally the "inference backend" component that worked example is computing redundancy for.

**Trade-offs considered:** Preemptive swap-to-CPU avoids outright rejecting a request during a memory crunch, at the cost of a real resume latency once that request is swapped back in — versus simply queueing or rejecting new requests when the GPU is full, which avoids any swap overhead but makes admission latency worse for anything arriving during a saturated period.

---

## Step 6: Evaluation, Monitoring, and Iteration

**What to monitor in production:**
- **KV-cache utilization %** — blocks currently in use divided by total blocks available; the single most direct health signal for this specific system, since Steps 2 and 4 both established that memory, not compute, is the binding resource.
- **Queue depth** — the number of requests waiting for a batch slot; a growing queue at high KV-cache utilization is the clearest sign of genuine capacity exhaustion rather than a transient blip.
- **p50 / p99 TTFT and inter-token latency** — measured continuously against the Step 1 targets.
- **Cost per 1M tokens served** — derived from GPU-hour cost divided by tokens actually served, tracked against the Step 1 cost target.
- **KV-cache reuse hit rate across turns** — the secondary-sourced technique behind Character.AI's reported ~33x figure; tracked separately from the primary-sourced PagedAttention metrics above precisely because it rests on weaker evidence (per this doc's Confidence note).

**What triggers a change:** KV-cache utilization consistently near 100% *with* a growing queue depth is a real capacity signal — add more replicas, or evaluate a smaller/quantized model (Step 2's trade-off). p99 TTFT breaching its SLA target while utilization is *low* points at a scheduling or preemption misconfiguration, not a capacity problem — adding hardware wouldn't fix it. Cost-per-token creeping upward without a corresponding throughput or latency justification is a signal to re-audit batch-size tuning, or to consider routing a fraction of traffic to a cheaper model tier (the exact decision capstone #15's gateway sits in front of to make).

**Trade-offs considered:** Provisioning aggressive headroom (running well below max KV-cache utilization at all times) keeps p99 latency safe against traffic spikes but means paying for GPU capacity that sits idle most of the time. Running close to full utilization is cheaper per token served on average but leaves little margin before queue depth — and therefore p99 latency — starts climbing during any demand spike. Neither is correct in general; it's the same latency-vs-cost trade-off from Step 1, now informed by real monitored numbers instead of an upfront guess.

---

## Source(s) and Further Reading

- Kwon et al., *"Efficient Memory Management for LLM Serving with PagedAttention,"* SOSP 2023 (arXiv:2309.06180) — **primary**, the source of the PagedAttention mechanism, the fragmentation-waste percentages, and the virtual-memory-paging framing used throughout Steps 4-5.
- Character.AI / Noam Shazeer, June 2024 engineering post on serving-cost reduction via KV-cache reuse — **secondary/unconfirmed**; widely covered secondhand, no still-live primary URL confirmed. Cited only for the illustrative ~33x figure, not as a verified production benchmark.
- Lesson 1 (`lessons/lesson-1-ai-fundamentals-refresher.md`), Concept B1 — full definitions of KV cache, continuous batching, and quantization, referenced rather than re-derived throughout this document.
- Lesson 3 (`lessons/lesson-3-scalability-and-availability.md`), Concepts I1 and I3 — the throughput/latency batch-size table and the series/parallel availability math this capstone's Step 5 applies directly, rather than re-deriving.
