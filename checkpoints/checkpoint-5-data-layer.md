# Checkpoint 5: Data Layer — Databases and Caching

## Purpose

This checkpoint verifies you can distinguish the five RDBMS scaling techniques and reason about what each trades away, place a vector database correctly on the NoSQL spectrum instead of treating it as its own category, compute how a cache's hit rate directly determines the load reaching a database, distinguish the four caching strategies by what each risks, and trace semantic caching as cache-aside with similarity search in place of exact-key lookup.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1: Adding read replicas behind a primary database scales read throughput — but why doesn't it help a write-throughput problem, and what consistency question does adding replicas reopen from Lesson 3?</summary>

**Answer:** In master-slave replication, only the primary node accepts writes — read replicas receive a copy of those writes asynchronously and serve read-only queries, but they never accept writes themselves, so adding more replicas adds more read capacity without adding any write capacity at all; a write-throughput ceiling can only be addressed by sharding (splitting writes across multiple independently-writable nodes) or master-master replication, not by adding read replicas. Adding replicas also reopens Lesson 3's Concept I2 consistency question: replication lag (the delay between a write committing on the primary and that write becoming visible on a given replica) means a replica is an eventually consistent copy of the primary, so a read served by a lagging replica can return data that's milliseconds-to-seconds stale.

**Why this matters:** Treating "add replicas" as a universal scaling fix misses that it only ever buys read capacity — a system bottlenecked on writes needs a structurally different fix, and every replica added also adds a small but real staleness window the application has to be aware of.
</details>

<details>
<summary>Question 2: Why is a vector database best understood as a KV/wide-column hybrid with a similarity index bolted on, rather than a genuinely new category of NoSQL database?</summary>

**Answer:** Look at its actual storage shape rather than its marketing: each row is addressed by a row/vector ID (key-value's defining trait), the "value" is a fixed-width numeric array (the embedding) plus a sidecar of metadata fields, and at scale that data is sharded across nodes by vector ID in the same row-key-sharding shape a wide-column store uses. None of that is new — what's actually new is the index type (e.g. HNSW, an approximate-nearest-neighbor graph-based index), which sits on top of an otherwise ordinary KV/wide-column storage model. Capstone #1 (Pinterest)'s decision to binarize its embeddings specifically to make them cheap to store and search only makes sense once you see the vector database as sitting on this ordinary storage spectrum rather than as some fundamentally different kind of database.

**Why this matters:** Mistaking a specialized index for a wholly separate storage paradigm leads to re-deriving sharding, replication, and consistency decisions from scratch for a vector database, when in fact Concept 1 and Concept 2's classic answers mostly still apply directly — only the index logic is genuinely new.
</details>

<details>
<summary>Question 3: An application serves 40,000 reads/sec against a database that saturates at 5,000 queries/sec, behind a cache-aside layer. At a 92% cache hit rate, how many queries/sec reach the database, and is it within capacity? If a cache-eviction storm drops the hit rate to 85%, what happens?</summary>

**Answer:** At 92% hit rate: queries reaching the DB = 40,000 × (1 − 0.92) = 40,000 × 0.08 = 3,200 queries/sec, which is comfortably under the 5,000 qps ceiling (1,800 qps / 36% headroom to spare). At 85% hit rate: queries reaching the DB = 40,000 × (1 − 0.85) = 40,000 × 0.15 = 6,000 queries/sec, which exceeds the 5,000 qps ceiling by 1,000 qps (20% over capacity) — the database is now overloaded. A 7-percentage-point drop in hit rate flipped the system from comfortably under capacity to overloaded, because the database only ever sees the missed fraction of total traffic, and that fraction grows disproportionately fast in absolute terms as the hit rate falls even a little.

**Why this matters:** Cache hit rate isn't a soft "nice to have" metric — it's a direct input to a real capacity calculation, and a small-looking drop in it can be the actual root cause of a database suddenly falling over under what looks like unchanged traffic.
</details>

<details>
<summary>Question 4: What risk does write-behind caching take on that write-through doesn't, and when is refresh-ahead's extra background work actually worth it?</summary>

**Answer:** Write-through writes to the cache and the database together, synchronously, before acknowledging the caller — so the cache is never ahead of the database and a crash can't lose an acknowledged write. Write-behind writes to the cache and acknowledges the caller immediately, then applies the write to the database asynchronously afterward — this makes writes fast, but creates a real window where the cache's view is ahead of the database's, and if the cache fails before that deferred database write completes, the write is lost outright, with no durability guarantee behind it. Refresh-ahead's extra background work (proactively refetching a soon-to-expire entry before it actually expires) is worth it specifically for genuinely hot keys accessed by many concurrent requests — it prevents a thundering herd (many requests missing the same expiring key simultaneously and all hitting the database at once). For a cold or rarely-accessed key, that same background refresh is simply wasted work, since nothing was likely to re-request it before natural expiry anyway.

**Why this matters:** Write-behind and refresh-ahead both trade a guarantee (durability, or efficient use of background work) for speed or smoothness — picking either one without knowing which keys are actually hot, or which writes can tolerate loss, turns a performance optimization into a silent correctness or waste problem.
</details>

<details>
<summary>Question 5: Walk through what a semantic cache does differently from a classic exact-match cache-aside pattern when a new prompt arrives, and explain why a low similarity threshold raises the hit rate at a correctness risk that exact-match caching structurally cannot have.</summary>

**Answer:** Classic cache-aside checks for an exact key match: is this literal string already a key in the cache? A semantic cache instead embeds the incoming prompt, then queries a vector database for the nearest previously-cached prompt embedding and checks whether its similarity clears a configured threshold — a nearest-neighbor check instead of an equality check. On a hit (similarity above threshold), it returns the cached response without calling the LLM at all; on a miss, it calls the LLM, then embeds and stores the new prompt-response pair for future reuse — otherwise the identical cache-aside algorithm. Lowering the similarity threshold means more incoming prompts clear the bar and register as hits, raising the hit rate (and therefore the cost/latency savings, by the same arithmetic as Question 3) — but it also raises the odds of a false-positive hit: returning a cached answer to a question that was similar in wording or topic but not actually the same question. An exact-match cache cannot produce this failure mode at all, because it can only ever return the literal, previously-given answer to the literal same key — there's no "close enough" judgment call to get wrong.

**Why this matters:** This is the concrete version of the trade-off this lesson's Concept 4 draws explicitly: semantic caching buys a real hit-rate win unavailable to exact-match caching, but it does so by trading away a correctness guarantee that exact-match caching never had to give up — the same shape of bet as CAP theorem's consistency-vs-availability choice, one layer higher in the stack.
</details>

## Hands-On Self-Check

There's no CLI for this lesson — confirm you can do each of the following, without looking back at the lesson:

- [ ] I can derive a shard count from a total data-volume estimate and a target max size per shard, and explain why sharding on `user_id` rather than `pin_id` colocates a user's rows on one shard.
- [ ] I can compute the queries/sec reaching a database given total load and a cache hit rate, and explain why the headroom-vs-overload boundary is sensitive to small hit-rate changes.
- [ ] I can state, from memory, what each of replication, federation, sharding, and denormalization optimizes for and what each gives up.
- [ ] I can state, from memory, what distinguishes cache-aside, write-through, write-behind, and refresh-ahead on both a read and a write.
- [ ] I can trace, step by step, what a semantic cache does on an incoming prompt, and name the one step that differs from classic cache-aside.
- [ ] I can run the `get_pin` / `update_pin_embedding` Python snippet (or reason through it line by line) and identify which function implements cache-aside and which implements write-through.

## Next Step

Move to **Lesson 6: Async and Communication**.
