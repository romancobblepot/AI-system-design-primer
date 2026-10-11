# Checkpoint 11: Real-World Architectures

## Purpose

This checkpoint verifies you can take any entry from Lesson 11's N1-N3 tables and trace its core trick back to a Lesson (1-9) Concept or a capstone you already learned — not recall a fixed answer about any one tool, company, or blog.

## Open-Ended Self-Check

Lesson 11 is a survey, not a teaching lesson, so there's no single right answer to "what did Perplexity build" the way there is for, say, "what is PagedAttention." So instead of five fixed Verification Questions, do this:

**Pick 3 entries of your own choosing from Lesson 11's N1, N2, or N3 tables** (any mix — all three from one table, or one from each) and, for each, **write one sentence** naming which Lesson (1-9) Concept or capstone its core trick actually maps back to. That's it. This exercise is unscored — "The 'Why this matters' framing still applies, just unscored." There's no answer key to check against — the point, per N4, is whether you *can* make the connection, not whether your sentence matches anyone else's.

The three worked examples below show what that one sentence should look like — they are **illustrations of the exercise, not a menu to copy from**. Pick your own 3 entries; don't just restate these.

<details>
<summary>Worked example 1 (N1 — AI infrastructure building block): FAISS</summary>

**One sentence:** FAISS — Meta AI's library for efficient similarity search over dense vectors — supports both approximate-nearest-neighbor indexes (e.g. HNSW, Lesson 1's C2) and exact/binary ones (e.g. `IndexBinaryFlat`), and it's that second, exact mode that's the clearest tie to capstone #1 (`solutions/visual-search`): Pinterest's own design binarizes its embeddings specifically so a brute-force, *exact* Hamming-distance scan stays cheap, deliberately avoiding ANN approximation rather than relying on it.

**Why this matters:** This is the "shared principle across rows" move N4 asks for — but it's also a reminder that the principle isn't always the obvious one: FAISS's reputation is for ANN search, yet capstone #1's actual connection to it runs through its exact-search mode, not its approximate one. Making the connection well means matching the library's real capability to the paper's real technique, not to what its name suggests.
</details>

<details>
<summary>Worked example 2 (N2 — Company AI architecture): Notion AI</summary>

**One sentence:** Notion AI's per-task model routing by cost/latency/quality maps back to Lesson 1's B3 (model routing/gateway) and to capstone #15 (`solutions/llm-api-gateway`), whose entire design is this same routing decision made generic across providers rather than across Notion's own internal task categories.

**Why this matters:** This is a case where the mapping runs two levels deep at once — a Lesson Concept *and* a capstone — which is normal; N4 never said the mapping has to be exactly one target, only that there has to be one you can actually name, not a vague "this seems AI-related."
</details>

<details>
<summary>Worked example 3 (N3 — Company engineering blog): Anthropic's blog</summary>

**One sentence:** Anthropic's own blog (anthropic.com/news) isn't a technique to map to a Lesson Concept at all — it's the real primary source behind two capstones already in this repo, capstone #9's contextual-retrieval design and capstone #14's computer-use agent, so the "mapping" here is source-to-capstone rather than technique-to-concept.

**Why this matters:** N3 entries map back differently than N1/N2 entries do — a blog isn't itself a pattern, it's where a pattern's primary source lives — and noticing that difference is itself part of "reading N1-N3 well" rather than treating all three tables as the same kind of row.
</details>

## Hands-On Self-Check

There's no CLI for a survey lesson — confirm you can do each of the following without looking back at this checkpoint's own worked examples above:

- [ ] I can name at least 3 Lesson-10 entries (from N1, N2, or N3, my own choice) and the Lesson/capstone each one's core trick maps back to, in my own words.
- [ ] For at least one N1 entry, I can name a *second* N1 entry that converges on the same underlying principle (e.g. the paged/non-contiguous KV-cache idea showing up across more than one serving engine) — the "look across rows, not down one row" move N4 asks for.
- [ ] I can name at least one N1 or N2 entry flagged as secondary-sourced or unconfirmed (e.g. Midjourney's row in N2), and explain in my own words why that flag matters rather than skipping past it.
- [ ] I can explain, from memory, N4's three questions (shared principle across entries; what problem it solves and where that breaks down; which Lesson/capstone it maps to) without rereading Lesson 11.
- [ ] I can pick one N3 blog and name which capstone's primary source actually came from it.

## Next Step

This is the last checkpoint in the course — Lesson 11 is the final numbered lesson, with nothing scheduled after it beyond a depth-bar re-check pass, not new reader-facing content. There is no Lesson 11.

So instead of "move to Lesson N+1":

- **Go deepen your own practice in `solutions/`.** The 14 capstones are where everything from Lessons 1-11 actually gets exercised end to end — if you haven't worked through all of them yet, that's a better next step than anything new in this repo.
- **Go past this repo's curated depth, on purpose.** This repo deliberately curated core system design down to what an AI engineer specifically needs (Lessons 3-7) and AI-native material down to a single refresher (Lesson 1) — `system-design-primer` itself remains the reference for going further than that curation (its own exhaustive company-architecture list, SQL-tuning internals, full OSI-layer detail) once you know specifically what you want to go deeper on.
- **Otherwise: you're done.** You've completed all 11 lessons and their checkpoints. There's nothing further being added to the numbered sequence.
