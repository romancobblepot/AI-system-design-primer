# Checkpoint 3: Scalability and Availability

## Purpose

This checkpoint verifies you can distinguish latency from throughput in an LLM-serving context, reason correctly about consistency trade-offs under CAP theorem, and compute combined availability for a multi-component serving chain — both in series and with parallel redundancy.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1: Why can increasing an LLM serving engine's batch size raise total system throughput while simultaneously making each individual request slower?</summary>

**Answer:** Throughput (tokens/sec across the whole system) and latency (time experienced by one request) are measuring different things. A larger batch lets the GPU process more requests' tokens in one forward pass, so the aggregate number of tokens produced per second across all requests goes up. But each individual request now shares the GPU with more concurrent work, so the time between that request's own tokens (inter-token latency) increases — e.g. going from batch size 1 (50ms/token, 20 tokens/sec aggregate) to batch size 32 (80ms/token, 400 tokens/sec aggregate) is a 60% latency increase for a 20x throughput gain. Both numbers are real and both move in the same direction as batch size grows — they just measure different things.

**Why this matters:** Treating "throughput" and "latency" as synonyms for "speed" leads to tuning a system for the wrong goal — a chat UI needs low per-token latency even at the cost of throughput, while an overnight batch-summarization job wants the opposite.
</details>

<details>
<summary>Question 2: What does CAP theorem actually say you can't have, and what's the real-world difference between an eventually consistent system and a strongly consistent one?</summary>

**Answer:** CAP theorem says that during an actual network partition (a break in communication between nodes that are each still running), a distributed system can provide at most two of Consistency (every read gets the latest write or an error), Availability (every request gets a non-error response), and Partition tolerance (the system keeps working despite the partition) — and since partitions do happen, the real choice is between staying consistent-but-sometimes-unavailable (CP) or available-but-sometimes-stale (AP). An eventually consistent system guarantees that, given enough time with no new writes, all replicas will converge to the same value — but a read immediately after a write might still see the old value. A strongly consistent system makes a write wait (often via a quorum — e.g. 2-of-3 replicas acknowledging) until enough replicas have it, so that once the write returns success, every subsequent read anywhere sees it immediately — at the cost of added write latency.

**Why this matters:** Choosing between these isn't optional once you have more than one replica — not choosing explicitly means you inherited whichever default your database ships with, often eventual consistency, without necessarily realizing it.
</details>

<details>
<summary>Question 3: Why might an agent appear to "forget" a fact it just stored in its long-term memory, even though nothing is actually broken?</summary>

**Answer:** If the long-term memory store (often a vector database, per Lesson 1's C2) defaults to eventual consistency between replicas, there's a real window of time after a write during which a read — including a read from that same agent, moments later in the same multi-step run — can be served by a replica that hasn't received the update yet, and so returns stale (pre-write) data. This looks like the agent "forgetting," but it's actually a consistency-window gap, not a logic bug or a memory failure.

**Why this matters:** This is the exact bridge between core CAP-theorem consistency patterns and Lesson 1's E2 (long-term memory) — recognizing this as a consistency-timing issue, not a memory-architecture issue, points you at the right fix (e.g. reading from the same replica you just wrote to, or using a store that offers a stronger consistency option for this specific access pattern).
</details>

<details>
<summary>Question 4: Why does chaining three components in series (e.g. gateway → inference backend → vector DB) always produce a combined availability that's lower than any single component's own availability?</summary>

**Answer:** Series availability is the product of each component's availability (A_combined = A1 × A2 × A3), and because each individual availability is a fraction less than 1, multiplying several of them together always produces a number smaller than the smallest one in the chain — because a request fails if *any* link in the chain fails, not just the weakest one. For example, 99.95% × 99.9% × 99.99% ≈ 99.84% — lower than even the 99.9% backend's own number, even though the other two components are each individually more available than that.

**Why this matters:** This is counter-intuitive if you assume "the chain is about as good as its weakest link" — the real math says it's worse than the weakest link, which is precisely why availability math (not intuition) has to drive decisions about where to add redundancy.
</details>

<details>
<summary>Question 5: What's the practical difference between active-passive and active-active failover, and why does making just the single weakest component in a serving chain redundant (active-active) produce a disproportionately large improvement in combined availability?</summary>

**Answer:** Active-passive keeps a standby replica idle, ready to take over only after the active one fails and the failure is detected and the standby promoted — there's a real failover delay during which requests fail. Active-active runs multiple replicas live and serving traffic simultaneously, so one replica's failure costs capacity but not availability — there's no cutover delay. The disproportionate improvement comes from the parallel-availability formula: combined availability of redundant replicas = 1 − [(1−A1) × (1−A2) × ...], which multiplies *failure* probabilities together rather than availabilities — and failure probabilities are small numbers (e.g. 0.1%), so multiplying two of them together produces an extremely small combined failure probability (0.1% × 0.1% = 0.0001%, i.e. 99.9999% available). In the worked example, making only the 99.9%-available inference backend redundant took the whole 3-component chain's downtime from ~14 hours/year to ~5.3 hours/year — most of the benefit came from fixing the single weakest link, not from adding redundancy everywhere.

**Why this matters:** This tells you where to spend a limited redundancy budget — doubling up on the already-most-reliable component buys almost nothing, while doubling up on the weakest link buys the most combined-availability improvement per dollar spent.
</details>

## Hands-On Self-Check

There's no CLI for this lesson — confirm you can do each of the following, by hand or with the Python snippet from the lesson, without looking back at it:

- [ ] I can compute total completion time for a request given TTFT, output token count, and inter-token latency.
- [ ] I can explain, in one sentence each, the difference between weak, eventual, and strong consistency.
- [ ] I can compute combined availability for a 3-component serving chain in series, given each component's individual availability.
- [ ] I can compute combined availability for two redundant (parallel) replicas of the same component, and explain why that number is higher than either replica's own availability.
- [ ] I can explain, without re-reading, why active-active eliminates failover delay but active-passive doesn't.

## Next Step

Move to **Lesson 4: Network and Delivery**.
