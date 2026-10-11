# Capstone #9: RAG System Design — Enterprise Knowledge-Base Chatbot (Contextual Retrieval)

**Source(s):** Primary — Anthropic, *"Introducing Contextual Retrieval,"* published Sep. 19, 2024 (anthropic.com/news/contextual-retrieval). The post's own technique — prepending LLM-generated, chunk-specific context to each chunk before embedding and indexing, combined with reranking — is Anthropic's own documented engineering work, confirmed by directly fetching the post's text, not secondhand coverage.

**Confidence:** Strong, primary source — a named company's own engineering/research post, with its own stated benchmark numbers. Every specific figure below tagged **(source-confirmed)** was verified by fetching the real post directly: the retrieval-failure-rate reductions (35% / 49% / 67%), the embedding model used for that benchmark (Gemini's `text-embedding-004`), the reranker used (Cohere's reranker), the context-generation model (Claude 3 Haiku), the context length (50-100 tokens), the reranking candidate-pool sizes (top-150 in, top-20 out), and the ingestion cost figure ($1.02 per million document tokens, under the post's own stated assumptions). Every figure tagged **(illustrative)** is this document's own worked assumption — corpus size, query volume, embedding dimensionality, latency targets — used because the post itself doesn't publish a specific enterprise deployment's numbers; these are kept clearly separate from the post's own confirmed figures throughout, never blended into them. Nothing below is tagged source-confirmed unless it was actually found in the fetched post text, rather than inferred and presented as if it were a stated fact.

**Scope note:** This capstone covers retrieval accuracy for an internal, enterprise knowledge-base chatbot (think: an internal support/ops assistant answering questions against product docs, runbooks, and policy documents) — the chunking/context/embedding/retrieval/reranking pipeline, end to end. It does **not** cover generation-quality evaluation of the final answer once retrieved chunks are handed to the model (Lesson 9's territory, G1-G2), multi-tenant access control over *which* documents a given user is even allowed to retrieve from (Lesson 8's F5), or the chat UI itself. Base RAG mechanics — what an embedding is, what a vector database is, what chunking and "keeping a knowledge base fresh" mean in general — are **not** re-taught here; Lesson 1's Concepts C1-C5 already cover them, and this document links to them rather than re-deriving them.

---

## Step 1: Clarify Requirements & Frame the ML/AI Objective

**Functional scope:** an employee types a natural-language question into an internal chatbot; the system retrieves the most relevant passages from a corpus of enterprise documents (product specs, internal wikis, support tickets, policy PDFs) and hands them, as context, to an LLM that generates a grounded answer citing its sources.

**The actual metric being optimized:** not the final answer's fluency or helpfulness (that's a generation-quality question, out of scope per the Scope note above) — this capstone's objective is **retrieval accuracy**: given a query, did the retrieval step surface the chunk(s) that actually contain the answer, within the top-*k* chunks handed to the model? The standard metric for this is **recall@k** (recall at k) — of all the chunks in the corpus that are actually relevant to a given query, the fraction of them that appear somewhere in the top *k* retrieved results. Anthropic's own post reports the complementary quantity, **retrieval failure rate**, defined as `1 − recall@k` at `k = 20` — the fraction of queries for which *none* of the truly relevant chunks made it into the top 20 results returned to the generation step. A high failure rate means the model is being asked to answer from context that doesn't contain the answer at all — a failure mode no amount of prompting or model quality can fix downstream, because the information genuinely isn't in front of the model.

**What counts as ground truth / feedback signal:** a labeled evaluation set of **(query, correct-chunk-ID) pairs** — real or representative employee questions, each hand-labeled with which chunk(s) in the corpus actually contain the answer. This is the eval-set equivalent of capstone #1's held-out evaluation query/image corpora (Step 6 there, not Step 1 — capstone #1's own Step 1 describes its three *training*-label datasets, while its genuinely held-out evaluation corpora, kept separate per product, are described in Step 6) — same idea, applied to text retrieval instead of visual search. Building this set is itself real, ongoing work: new document types and new question phrasings keep appearing, so the eval set needs the same "keeping it fresh" discipline Lesson 1's Concept C5 names for the corpus itself, just applied to the labels instead of the documents.

**Explicitly out of scope:** generation-quality evaluation of the final answer (Lesson 9, G1-G2); per-tenant/per-user document access control (Lesson 8, F5 — multi-tenant isolation); the chat UI and conversation-memory layer (Lesson 1's Group E, already covered there); fine-tuning the embedding model or the generation model (this capstone uses off-the-shelf models throughout, per Step 4).

**Trade-offs considered:** Optimizing purely for recall@20 (did *a* relevant chunk make the top 20) is the right target for *this* capstone's scope, but a real production system also cares about **precision** — how much of what's retrieved is actually relevant, since irrelevant chunks still consume context-window tokens (Lesson 1, Concept A2) and can distract the generation model even when the correct chunk is also present. This capstone follows Anthropic's own post in treating recall@20 as the primary metric (it's the number the post itself reports), while flagging precision as a related but distinct concern Step 6's monitoring also has to watch, not something recall@20 alone guarantees.

---

## Step 2: Back-of-Envelope Constraints

**Assumptions for this estimate (illustrative):** a corpus of 400,000 enterprise documents (product docs, wikis, tickets, policies), averaging 4,000 tokens/document. Chunked at **800 tokens/chunk** — the exact chunk size Anthropic's own post uses in its cost-estimate assumptions (source-confirmed as an assumption in that calculation, not stated as a universally-recommended chunk size), giving roughly 5 chunks/document:

```
total_chunks = 400,000 documents × 5 chunks/document = 2,000,000 chunks
```

This deliberately lands on the same 2,000,000-chunk figure Lesson 6's Concept 1 worked example already used for "the kind capstone #9's design depends on" — not a coincidence; it's chosen here specifically so this capstone's own numbers and that lesson's forward-looking worked example describe the same system rather than two different ones.

**Context-generation cost — using Anthropic's own confirmed per-token rate.** The post states the one-time cost to generate contextualized chunks is **$1.02 per million *document* tokens (source-confirmed)**, under its own stated assumptions (800-token chunks, 8K-token documents, 50 tokens of instructions, 100 tokens of generated context per chunk, with prompt caching covering the repeated whole-document context). Applying that confirmed rate to this corpus's illustrative total token volume:

```
total_document_tokens = 400,000 documents × 4,000 tokens/document = 1,600,000,000 tokens

context_generation_cost = 1,600,000,000 tokens ÷ 1,000,000 × $1.02/million tokens
                         = 1,600 × $1.02
                         ≈ $1,632  (one-time ingestion cost, illustrative corpus size × source-confirmed rate)
```

That ~$1,632 is the concrete number behind this fix's own cost: the contextualization step itself costs tokens that have to be budgeted for. It's a one-time cost (paid again only when the corpus is re-chunked or the context-generation prompt changes), not a per-query cost — which is exactly why Step 5's framing of this as a cache write, not a cache *lookup*, matters.

**Embedding storage.** Using an illustrative 1,024-dimensional embedding model (illustrative — the post's own benchmark used Gemini's `text-embedding-004`, source-confirmed as the model used for *that specific* reported comparison, but the post does not mandate one specific embedding model or dimensionality for production use):

```
float32 embedding storage = 2,000,000 chunks × 1,024 dims × 4 bytes/dim
                          = 8,192,000,000 bytes ≈ 8.2 GB

contextualized chunk text storage (for the BM25 index and for re-embedding later):
  ≈ 800 tokens chunk + 100 tokens context ≈ 900 tokens/chunk ≈ 3.6 KB/chunk (at ~4 bytes/token, illustrative)
  2,000,000 chunks × 3.6 KB ≈ 7.2 GB
```

**Query volume and latency budget (illustrative):** 50,000 employees, 20% daily-active, 2 queries/day per active user → 20,000 queries/day → average ≈ 0.23 queries/sec, with a 10x business-hours peak-to-average ratio (illustrative, same kind of planning assumption capstone #1's Step 2 used for its own peak-traffic estimate) → peak ≈ 2.3 queries/sec. Latency budget: end-to-end p50 response time (the median across retrieval + rerank + generation combined — 50% of requests finish faster than this value; percentile latency is defined in full in Lesson 9's Concept 2) under 3 seconds — loose compared to capstone #10's inference-serving targets, because this is a human reading a chat response, not a token-by-token streaming SLA being raced against.

**Trade-offs considered:** A smaller chunk size (e.g. 400 tokens instead of 800) gives retrieval finer-grained precision — a matched chunk contains less irrelevant surrounding text — but doubles the chunk count for the same corpus, doubling both the context-generation cost above and the embedding-storage footprint, and increases the odds that a single relevant passage gets split across two chunks' boundaries in the first place. A larger chunk size reduces both costs but risks diluting a chunk's embedding with enough unrelated content that its similarity to a narrowly-phrased query drops. This capstone follows the post's own 800-token assumption as a reasonable illustrative middle ground, not as a universally correct answer — Lesson 1's Concept C3 already covers this general chunk-size trade-off, and nothing here overrides that.

---

## Step 3: Data / Knowledge Pipeline

**Chunking and freshness — linked, not re-taught.** How a document gets split into chunks in the first place is Lesson 1's Concept C3's territory in full; how the corpus is kept from going stale as documents change is Lesson 1's Concept C5's territory in full. This capstone doesn't re-derive either — it assumes both as given inputs and focuses on what's actually new here: **what happens to each chunk between being produced by C3's chunking step and being embedded and indexed.**

**The problem Contextual Retrieval exists to fix.** Anthropic's post frames the core failure mode directly (source-confirmed): *"traditional RAG solutions remove context when encoding information."* A chunk like "the warranty period is 12 months from purchase" means something different depending on which product's documentation it came from — but a naive chunking pipeline embeds that sentence with no indication of which product it's actually about, so a query like "what's the warranty on the X200 model" can fail to retrieve it even though it's the exact right passage, simply because nothing in the chunk's own text (or its embedding) ties it back to "X200."

**Sidebar — Contextual Retrieval.** *(First full technical treatment in this repo; "prepend extra context to each chunk" is gestured at in Lesson 1's Concept C3 as one chunking approach among several, but the actual mechanism — an LLM generating that context per chunk, at indexing time, combined with a lexical index and reranking — isn't taught there. This isn't classic infra (Lessons 3-7 have no home for it) and isn't already fully taught in Lesson 1 either, so it gets the full inline Sidebar treatment here plus a glossary entry.)*
- **Why?** An embedding model can only encode what's actually in the text it's given. If the surrounding context that disambiguates a chunk (which document, which section, which product) never makes it into the chunk's own text, no amount of embedding-model quality can recover it at retrieval time — the information was discarded before embedding ever ran.
- **What?** **Contextual Retrieval** is Anthropic's name (source-confirmed) for prepending a short, chunk-specific explanatory blurb — generated by an LLM, from the whole source document and that one chunk — to the chunk's text, *before* that text is embedded and *before* it's indexed into a lexical (keyword) index, so both retrieval paths see the disambiguating context, not just the embedding path. The post's own two named sub-techniques (source-confirmed): **Contextual Embeddings** (the context-prepended chunk is what gets embedded into the vector index) and **Contextual BM25** (the context-prepended chunk is also what gets indexed into a lexical index). **BM25** (Best Matching 25) is a classic lexical ranking algorithm — not an AI/embedding-based technique at all — that scores how relevant a document is to a query based on how often the query's exact terms appear in it (term frequency), how rare those terms are across the whole corpus (inverse document frequency, which down-weights common words like "the"), and a length-normalization adjustment so longer documents aren't unfairly favored just for containing more words. It finds exact or near-exact keyword matches — a part number, an acronym, a product SKU — that a semantic embedding can miss entirely if the query's wording doesn't closely match the chunk's phrasing in meaning-space, which is exactly why Contextual Retrieval runs both an embedding index and a BM25 index over the *same* contextualized text and combines their results, rather than relying on embeddings alone.
- **How?** The context-generation prompt (source-confirmed shape, from the post): the whole document is wrapped in `<document>` tags, the specific chunk in `<chunk>` tags, and the model (the post uses **Claude 3 Haiku**, source-confirmed) is instructed to produce "a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk," answering "only with the succinct context and nothing else" — producing roughly 50-100 tokens of context per chunk (source-confirmed). The post notes (source-confirmed) that a custom, domain-specific version of this prompt can perform better than the generic one — e.g. an enterprise deployment's own prompt might specifically ask the model to name the product, version, and document type a chunk came from, rather than leaving that open-ended.

**A real chunk-with-context record, as it would be written at indexing time:**

```json
{
  "chunk_id": "doc-00482-chunk-17",
  "document_id": "doc-00482",
  "document_title": "X200 Service Manual v3",
  "raw_chunk_text": "The warranty period is 12 months from the date of purchase, extendable to 24 months with the Premium Care add-on.",
  "generated_context": "This chunk is from the Warranty section of the X200 Service Manual (v3), describing standard and extended warranty terms for the X200 product line.",
  "contextualized_text": "This chunk is from the Warranty section of the X200 Service Manual (v3), describing standard and extended warranty terms for the X200 product line.\n\nThe warranty period is 12 months from the date of purchase, extendable to 24 months with the Premium Care add-on.",
  "embedding_model": "text-embedding-004",
  "embedding_version": "2025-01-ingest-v2",
  "token_count": 142,
  "indexed_at": "2026-01-14T09:32:11Z"
}
```

`contextualized_text` — the concatenation of `generated_context` and `raw_chunk_text` — is what actually gets embedded and what actually gets indexed into BM25, not `raw_chunk_text` alone; `raw_chunk_text` and `generated_context` are kept separately in the record specifically so the raw chunk (without the generated preamble) is what's ultimately shown to the end user or passed to the final generation step, keeping the LLM-generated scaffolding invisible to them. `embedding_version` exists for the same reason capstone #1's `embedding_version` column did (Step 5 there): it lets a re-embedding rollout (e.g. after switching embedding models) be staged and rolled back without ambiguity about which row was produced by which model generation.

**Freshness, inheriting Lesson 1's C5 directly, with one addition this technique introduces.** A document that's added, edited, or deleted still goes through exactly the re-chunk/re-embed/re-index cycle Lesson 1's Concept C5 already describes — but Contextual Retrieval adds one more step to that cycle that a plain chunking pipeline doesn't have: the context-generation LLM call has to re-run for every chunk of an edited document too, not just its embedding, since `generated_context` depends on the document's current content and could go stale (wrong section reference, wrong version number) even if the underlying chunking and embedding steps were somehow skipped.

**Trade-offs considered:** Generating context per chunk independently (as described above) means every chunk's context-generation call is a separate, parallelizable unit of work — good for throughput (Step 5), but it means two chunks from the same document each pay their own LLM call rather than sharing one. Prompt caching (the mechanism Lesson 5's Concept 4 already names from Anthropic's own documentation) is what makes this affordable: the whole document is loaded into the prompt cache once, and each chunk's individual context-generation call reuses that cached document rather than resending and reprocessing it from scratch — without this, the post's own $1.02/million-token figure would be dramatically higher, since every one of a document's ~5 chunks would otherwise pay to reprocess the entire document's tokens from zero.

---

## Step 4: Model/Agent Core Design

**Embedding model choice.** This capstone doesn't commit to one single embedding model as "the" answer — Anthropic's own post benchmarked Contextual Retrieval's improvement across multiple embedding model families (the headline 35%/49%/67% figures below are reported using Gemini's `text-embedding-004`, source-confirmed), which is itself evidence that Contextual Retrieval's benefit isn't tied to one specific vendor's embedding model — it's a preprocessing technique applied *before* whichever embedding model is chosen, per Lesson 1's Concept C1's general definition of what an embedding model does. For this capstone's own design: a general-purpose, commercially available text-embedding model (illustrative; dimensionality assumed at 1,024 per Step 2), selected the same way Lesson 1's Concept C1/C2 already frames that choice — not re-derived here.

**Trade-off #1 — Contextual Retrieval vs. plain chunking.** This is the capstone's central modeling decision, and the post's own confirmed numbers make it concrete rather than qualitative. Using the post's own reported **retrieval failure rate** (`1 − recall@20`, Step 1's definition), measured with Gemini `text-embedding-004` embeddings (source-confirmed, all figures below):

| Configuration | Retrieval failure rate | Reduction vs. baseline |
|---|---|---|
| Plain embeddings (baseline, no contextual preprocessing) | 5.7% | — |
| **Contextual Embeddings** alone | 3.7% | **35% reduction (source-confirmed)** |
| Contextual Embeddings + Contextual BM25 | 2.9% | **49% reduction (source-confirmed)** |

Going from a plain embedding to a contextualized one alone — no BM25, no reranking, just prepending the LLM-generated context before embedding — cuts the failure rate more than a third. Adding the lexical BM25 index on top of the same contextualized text (catching the exact-keyword-match cases embeddings alone can miss, per Step 3's Sidebar) very nearly doubles that reduction. **The cost side of this trade-off is Step 2's $1.02/million-document-token figure** — Contextual Retrieval is not a free accuracy win; it's an accuracy win that has to be budgeted for at ingestion time.

**Trade-off #2 — reranking as a second, separable technique.** **Reranking** is a distinct second step, and the post's own pipeline shape confirms how it composes with the above (source-confirmed): run initial retrieval (the combined embedding + BM25 candidate pool) to get the **top 150** chunks, pass those 150 chunks plus the user's query through a **reranker** — a model (the post uses Cohere's reranker, source-confirmed) that scores each *(query, chunk)* pair jointly, rather than comparing two independently-computed embeddings the way the initial retrieval step does — and keep only the **top 20** reranked chunks to actually hand to the generation model. A reranker is more expensive per comparison than an embedding-similarity lookup (it has to run a fresh forward pass over each query-chunk pair, rather than a cheap vector-distance computation against a precomputed embedding), which is exactly why it's applied only to a *narrowed* candidate pool (150) rather than the whole corpus — the initial embedding+BM25 retrieval step's job is specifically to cut millions of chunks down to a manageable 150 cheaply, so the expensive reranker only ever has to look at 150 candidates, not 2 million.

| Configuration | Retrieval failure rate | Reduction vs. baseline |
|---|---|---|
| Contextual Embeddings + Contextual BM25 (no reranking) | 2.9% | 49% reduction |
| **Contextual Embeddings + Contextual BM25 + reranking** | **1.9%** | **67% reduction (source-confirmed)** |

Reranking alone buys roughly another third off the already-reduced failure rate (2.9% → 1.9%) — a real, separate accuracy gain on top of Contextual Retrieval's own, at the cost of one additional model call per query (not per chunk, so this cost scales with query volume, not corpus size — a materially different cost shape than Step 3's per-chunk context-generation cost, which scales with corpus size instead).

**Trade-offs considered:** Shipping Contextual Retrieval without reranking (the 49%-reduction configuration) is cheaper per query and architecturally simpler — one retrieval call, no second-stage scoring model to operate — and may be sufficient for a lower-stakes internal tool. Adding reranking buys the full 67%-reduction result but adds a second model dependency, a second per-query cost, and a second thing that can be slow or down — exactly the kind of "which failure now shows up where" question Step 6's monitoring has to track once this is in production. Skipping Contextual Retrieval entirely and relying on reranking alone to fix retrieval quality isn't a real option the post's own numbers support: reranking's gain (49%→67%) is a smaller marginal improvement than Contextual Retrieval's own gain (0%→49%), and reranking only ever gets to rerank whatever the first-stage retrieval already found — if the genuinely relevant chunk wasn't embedded well enough to make the top 150 in the first place (Contextual Retrieval's whole point), no reranker downstream can recover it, since it never gets the chance to see it.

---

## Step 5: Serving Architecture

This step exists specifically to deliver on three concrete promises already made about this capstone by lessons written before this document existed — Lesson 5's Concept 2 (K2), Lesson 5's Concept 3 (K3), and Lesson 6's Concept 1 (L1). Each is quoted directly below, then made concrete.

**Delivering on Lesson 6's L1 promise — the async ingestion pipeline.** Lesson 6's Concept 1 already built this capstone's worker-pool sizing as its own worked example, explicitly flagged there as "a reasoned architectural inference...not...a documented detail of capstone #9's own design" (since this document didn't exist yet when that lesson was written). This capstone's own design confirms that inference rather than overriding it: chunking, context-generation, and embedding genuinely are structurally a bursty, horizontally-parallelizable, per-chunk-independent workload — exactly the shape a task queue (Lesson 6, Concept 1) exists for — so this document reuses Lesson 6's own numbers directly rather than inventing a conflicting set:

```
corpus: 2,000,000 chunks (Step 2), ingestion window: 4 hours = 14,400 seconds

required_throughput = 2,000,000 / 14,400 ≈ 138.9 chunks/sec

throughput_per_worker = 5 chunks/sec   (bottlenecked on the context-generation LLM round-trip, Step 3)

workers_needed = ceil(138.9 / 5) = 28 workers
```

Each worker pulls a chunking+context-generation+embedding task off a task queue (Lesson 6's exact job schema — `task_id`, `document_id`, `chunk_id`, `status`, `attempt_count`, `max_attempts` — reused directly here, since this *is* the system that schema was written for), keyed for idempotent retry on `chunk_id`: a redelivered task (at-least-once delivery, Lesson 6's Concept 1) re-generates context and re-embeds the same chunk, overwriting its existing stored row rather than creating a duplicate — safe for exactly the reason Lesson 6's Concept 1 names idempotency as a requirement for at-least-once consumers.

**Delivering on Lesson 5's K2 promise — the embedding storage format.** Lesson 5's Concept 2 states directly: *"Capstone #9...depends on exactly this same storage-and-retrieval layer to hold its chunk embeddings — Anthropic's technique prepends LLM-generated context to each chunk before embedding and indexing it, but the resulting embeddings still live in a database with precisely this KV/wide-column shape underneath."* Concretely, following capstone #1's own sharded-table pattern directly — including deriving the shard count from this capstone's own numbers, the same discipline Lesson 5's own `pins` worked example and capstone #1's `pin_embeddings` table (Step 5 there) both apply, rather than asserting one:

```
Step 2's own totals: 8.2 GB embeddings + 7.2 GB contextualized/raw text ≈ 15.4 GB total

target_max_per_shard = 5 GB   (deliberately small — at this capstone's actual ~15.4 GB scale, a
                                single unsharded table would comfortably fit on one modern node
                                with room to spare; this target is chosen small enough to actually
                                produce more than one shard, specifically so the generated-shard-key
                                pattern below has something to demonstrate, rather than because this
                                capstone's own data volume requires sharding at all)

shards_needed (bare minimum)        = ceil(15.4 GB / 5 GB) = ceil(3.08) = 4 shards
required_capacity_with_20%_headroom = 15.4 GB × 1.20 = 18.48 GB
shards_needed_with_headroom         = ceil(18.48 GB / 5 GB) = ceil(3.696) = 4 shards
```

4 shards, not because this capstone's data volume demands sharding at all (it doesn't — 15.4 GB is a rounding error for a single node's disk) but to demonstrate the same generated-shard-key mechanism Lesson 5's `pins` example and capstone #1's `pin_embeddings` table use, at a deliberately small illustrative per-shard target chosen to make the pattern visible rather than vacuous. A real enterprise deployment at this corpus size would be well served by one unsharded table; sharding only becomes load-bearing once the corpus — and therefore this storage footprint — grows by roughly two more orders of magnitude, the regime capstone #1's own ~1.28 TB index actually lives in.

```sql
-- Contextualized-chunk embedding index, following Lesson 5's generated-shard-key pattern
-- (4 shards: illustrative at this capstone's own ~15.4 GB scale — see derivation above)
CREATE TABLE chunk_embeddings (
    chunk_id             VARCHAR(64)   NOT NULL,
    shard_key            SMALLINT      GENERATED ALWAYS AS (CRC32(chunk_id) % 4) STORED,
    document_id          VARCHAR(64)   NOT NULL,
    embedding            BINARY(4096)  NOT NULL,  -- 1,024-dim float32 vector, fixed-width
    embedding_version    VARCHAR(32)   NOT NULL,  -- which embedding-model generation produced this row
    raw_chunk_text       TEXT          NOT NULL,  -- the chunk's own text, no generated preamble (Step 3's record) — what's shown to the end user / passed to the generation step
    generated_context    TEXT          NOT NULL,  -- the LLM-generated disambiguating preamble (Step 3's record) — never shown to the end user directly
    contextualized_text  TEXT          NOT NULL,  -- generated_context + raw_chunk_text, precomputed and stored redundantly so the embedding step and the BM25 index can each read one column directly instead of reconstructing the concatenation on every write or query
    indexed_at           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (shard_key, chunk_id)
);
```

`embedding` is a fixed-width binary blob keyed by `chunk_id` — exactly the "fixed-width value, sharded by key" shape Lesson 5's Concept 2 says every vector database reduces to underneath its similarity index, not a fifth category of database with its own rules. The row carries all three text fields from Step 3's record, not just their concatenation: `raw_chunk_text` and `generated_context` are kept as their own columns specifically so the system can read `raw_chunk_text` alone when it's time to show a source passage to the end user or hand it to the generation step — delivering on Step 3's own promise that the LLM-generated scaffolding stays invisible to them — while `contextualized_text` (the concatenation of the two, per Step 3's record) is stored too, as a precomputed, denormalized copy kept purely so the embedding step and the separate BM25 lexical index can each read it directly, rather than reconstructing it from the other two columns on every write or every query.

**Delivering on Lesson 5's K3 promise — the retrieval cache framing.** Lesson 5's Concept 3 states directly: *"Anthropic's Contextual Retrieval technique computes an LLM-generated context prefix for each document chunk once, at indexing time, specifically so that expensive step never has to be repeated for every future query against that chunk — a one-time write that's then read many times, which is precisely the workload cache-aside and write-through both exist to optimize for."* This capstone's design is literally that claim, made structural: `generated_context` (Step 3's record) is computed exactly once, at ingestion time, by one context-generation LLM call per chunk — the expensive step — and written into `chunk_embeddings.generated_context` (and folded into `contextualized_text`) above. Every subsequent query that happens to retrieve this chunk (Step 2's estimated ~20,000 queries/day, indefinitely, for as long as this chunk remains in the corpus) reads that already-computed value directly, at zero marginal LLM cost — the same "pay once on a write, amortize across every future read" shape Lesson 5's Concept 3 defines for write-through caching in general, just with "the cache" being the persistent chunk-embeddings table itself rather than a separate, short-TTL cache layer in front of it.

**The query-time retrieval path, end to end:** a query arrives → it's embedded with the same embedding model used at ingestion (Step 4) → the embedding is used for an approximate-nearest-neighbor search (HNSW, Lesson 1's Concept C2, already fully defined there) against the sharded `chunk_embeddings` table above, *in parallel* with a BM25 lexical search against the same chunks' `contextualized_text` → both ranked lists are combined into one candidate pool, deduplicated, and cut down to the top 150 → the top 150, plus the original query, are sent to the reranker (Step 4) → the reranker's top 20 are handed to the generation model along with the original query.

**Trade-offs considered:** Running the chunking/context-generation/embedding pipeline as 28 parallel async workers (above) clears the 4-hour ingestion window comfortably, but every worker crash mid-task relies on the task queue's retry policy (Lesson 6, Concept 1) to recover rather than losing that chunk silently — a real operational dependency, not a detail that can be assumed away. Storing `raw_chunk_text`, `generated_context`, and `contextualized_text` directly in the same row as the embedding (rather than normalizing any of them into a separate table keyed by `chunk_id`) denormalizes the schema in exactly the way Lesson 5's Concept 1 describes — faster reads (one row fetch gets the vector, the user-facing raw text, and the BM25-indexed contextualized text all at once) — at the cost of `contextualized_text` being a derived copy of the other two that has to be kept in sync with them on any future re-contextualization, on top of the embedding itself needing to stay in sync with whichever text last produced it.

---

## Step 6: Evaluation, Monitoring, and Iteration

**Offline evaluation (the metric Step 1 committed to).** Before shipping any change to chunking, the context-generation prompt, the embedding model, or the reranker, re-run the labeled (query, correct-chunk) eval set from Step 1 and measure retrieval failure rate (`1 − recall@20`) against it — the same metric, computed the same way, as the post's own confirmed 5.7%/3.7%/2.9%/1.9% progression in Step 4. A change that regresses this number, even if it reduces cost or latency, is a real regression against this capstone's own Step 1 objective, not an acceptable trade unless explicitly decided as one.

**Online monitoring:** per-query retrieval latency (embedding + ANN search + BM25 search + reranking, broken out by stage, so a regression can be localized to one stage rather than treated as one opaque number); reranker-call cost and latency specifically, since Step 4 named it as a separate per-query cost with its own failure mode (a slow or down reranker degrades the whole request, even if initial retrieval succeeded); an explicit "no chunk retrieved above a confidence threshold" signal, distinct from a genuine answer — this is the live-traffic analog of Step 1's offline failure-rate metric, since in production there's no labeled ground truth to compare against in real time; and user-facing feedback signals (a thumbs-up/down on the chatbot's answer, or an escalation-to-a-human-agent action) as an indirect, noisier proxy for retrieval quality in the absence of a live ground-truth label.

**The feedback loop back into Step 3:** queries that get a thumbs-down, an escalation, or no confident retrieval at all are exactly the candidates for new (query, correct-chunk) labels to add to the Step 1 eval set — the same "stale eval set" risk Step 1 already flagged, closed by routing real production failures back into it rather than letting the eval set freeze at whatever it looked like on launch day.

**Failure modes that show up only at scale:** the context-generation prompt (Step 3) is tuned against the document types available at launch — a genuinely new document type (e.g. the enterprise onboards a new content source with a very different structure, like raw support-ticket transcripts instead of structured manuals) can produce low-quality generated context the prompt was never validated against, silently degrading retrieval for that whole new slice of the corpus until it's specifically eval'd; an embedding-model upgrade (Step 3's `embedding_version` field exists for exactly this) requires re-embedding the *entire* corpus, not just new documents, since old and new embeddings aren't directly comparable in the same similarity space — a full backfill, the same operational cost capstone #1's Step 3 names for Pinterest's own embedding upgrades; and reranker cost scales with query volume (Step 4), so a usage spike that's perfectly fine for the embedding/BM25 retrieval stage can still make the reranking stage the actual bottleneck, which is specifically why Step 5's monitoring breaks latency out by stage rather than reporting one end-to-end number.

**Trade-offs considered:** Gating every chunking/prompt/model change behind a full offline eval-set re-run is slower to iterate than shipping and watching online metrics directly, but catching a retrieval regression before it reaches real users is worth that slower cycle for a knowledge-base chatbot specifically, where a wrong or missing answer in an internal tool can itself cause a costly downstream mistake. Relying on user thumbs-up/down as a production signal is cheap to collect but is a noisy, indirect proxy for retrieval quality specifically (a bad answer can come from good retrieval and a bad generation step, or vice versa) — which is exactly why it's treated here as a feedback-loop input for growing the eval set, not as a direct replacement for Step 1's own offline recall@20 metric.

---

## Source(s) and Further Reading

- Anthropic, *"Introducing Contextual Retrieval,"* Sep. 19, 2024 (anthropic.com/news/contextual-retrieval) — **primary**; the source, confirmed by directly fetching the post, of the Contextual Embeddings/Contextual BM25 technique, the context-generation prompt shape and model (Claude 3 Haiku), the reranking pipeline shape (top-150 → Cohere reranker → top-20), the retrieval-failure-rate figures (5.7% baseline; 3.7%/35% reduction for Contextual Embeddings alone; 2.9%/49% reduction adding Contextual BM25; 1.9%/67% reduction adding reranking — all measured with Gemini `text-embedding-004` embeddings), and the $1.02-per-million-document-token ingestion cost figure.
- Lesson 1 (`lessons/lesson-1-ai-fundamentals-refresher.md`), Concepts C1-C5 — the original full definitions of embeddings, cosine similarity, vector databases, HNSW, chunking strategies, RAG end to end, and keeping a knowledge base fresh, referenced rather than re-derived throughout this document.
- Lesson 5 (`lessons/lesson-5-data-layer.md`), Concept 2 (NoSQL types / vector-DB-as-KV-wide-column-hybrid) and Concept 3 (caching strategies / the write-once-read-many framing) — the two Concepts this capstone's Step 5 is built specifically to deliver on, quoted directly above rather than re-derived.
- Lesson 5 (`lessons/lesson-5-data-layer.md`), Concept 4 — the prompt-caching mechanism this capstone's Step 3 depends on to make per-chunk context generation affordable.
- Lesson 6 (`lessons/lesson-6-async-and-communication.md`), Concept 1 — the async task-queue worker-pool sizing (28 workers, 2,000,000 chunks, 4-hour window) this capstone's Step 5 reuses directly, confirming rather than overriding that lesson's own flagged architectural inference.
- `appendix/glossary.md` — one-line entries for **Contextual Retrieval**, **BM25**, and **reranker/reranking**, added for this document's own Sidebar entries introduced above.
