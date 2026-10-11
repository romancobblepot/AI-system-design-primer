# Checkpoint 1: AI Fundamentals

## Purpose

This checkpoint verifies you have a solid working vocabulary for the AI/agentic fundamentals (Groups A-E: foundations, model serving, retrieval/RAG, agent architecture, and memory) that the rest of this repo assumes you already know, before moving on to the full-depth core system-design lessons.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1: Why doesn't doubling the amount of context you send an LLM simply double your cost and latency in a predictable, fixed way the way doubling a request's payload size might for a typical API call — and what does "token economics" actually mean?</summary>

**Answer:** AI providers price and time requests by the number of tokens processed, not by a flat per-request charge — and a "token" is a sub-word unit (roughly 3/4 of an English word on average, not one token per word or per character), so the exact token count of a given piece of text depends on the specific model's tokenizer. Input and output tokens are also often priced at different rates, and output tokens typically cost more in latency because they're generated one at a time, sequentially. So cost and latency scale with token count, but the token count of "the same" text isn't a fixed, obvious number — it varies by tokenizer, and the input/output split matters as much as the raw total. "Token economics" is the practice of reasoning about AI cost and performance in these token-based units instead of in requests, words, or characters.

**Why this matters:** Every back-of-envelope cost or latency estimate in this repo (Lesson 7's M4 technique, the appendix's token/latency numbers) is built on this unit conversion — getting it wrong means every downstream estimate is wrong too.
</details>

<details>
<summary>Question 2: In a RAG (Retrieval-Augmented Generation) pipeline, what are the two separate things that both have to go right before the model can give a factually grounded answer, and why does chunking strategy matter more than it might seem at first glance?</summary>

**Answer:** First, retrieval has to actually find the right passages — the user's query gets embedded, compared against a vector database of embedded document chunks, and the top-k closest chunks are pulled back; if the right information isn't retrieved, the model never sees it. Second, generation has to use what was retrieved correctly — the retrieved chunks are inserted into the prompt as context, and the model has to actually ground its answer in them rather than ignoring them or hallucinating. Chunking strategy matters more than it seems because if a document is split badly (e.g. a chunk loses the surrounding context it needs to make sense on its own, such as which product or section it's about), the embedding for that chunk may not even match the right queries in the first place — the failure happens before generation ever gets a chance.

**Why this matters:** This two-stage structure (retrieval, then generation) is why RAG failures are often retrieval failures wearing a "the model hallucinated" costume — and it's exactly the lesson capstone #9 (`case-studies/rag-contextual-retrieval`) is built to teach in depth.
</details>

<details>
<summary>Question 3: What's the actual difference between a chatbot and an agent, and what does the ReAct control-flow pattern add on top of that basic agent capability?</summary>

**Answer:** A chatbot can only produce a text (or voice) reply — it has no way to take an action that changes anything outside the conversation. An agent additionally has tool use / function calling: it can request that the surrounding application invoke a tool (call an API, run code, query a database) and receive that tool's result back. ReAct structures *how* an agent decides what to do with that capability: instead of deciding on one action and stopping, it loops through alternating reasoning ("Thought: ...") and acting (calling a tool) steps, observing each result before reasoning about the next step, continuing until it decides it has enough to answer.

**Why this matters:** Recognizing ReAct as a specific, nameable loop shape — not just "the agent being smart" — is what lets you compare it honestly against alternatives like plan-and-execute, which is a real design trade-off (flexibility vs. predictability), not a strictly better or worse choice.
</details>

<details>
<summary>Question 4: Why does the KV cache dominate GPU memory during serving, and how is that different from what batching and quantization each do?</summary>

**Answer:** The KV cache stores the key/value tensors for every token already processed in a conversation so that generating the next token only requires computing against the newest token, not recomputing attention over the entire conversation so far. Because this cache has to hold an entry for every token of every in-flight request's context, it grows with both context length and the number of concurrent requests — and on real serving hardware it's typically the single largest consumer of GPU memory, more than the model's own weights once enough requests are running concurrently. That's a different lever from batching, which is about *throughput*: grouping multiple requests into one forward pass so the GPU's parallelism isn't wasted on one request at a time — batching doesn't shrink anyone's memory footprint, it just uses the GPU's compute more efficiently. It's also different from quantization, which is about *the model's own memory footprint*: storing weights in fewer bits so the model itself takes up less GPU memory, trading off some output precision — a one-time footprint reduction independent of how many requests are being served. So: KV cache is a per-request, per-token memory cost that scales with concurrency and context; batching is a throughput lever; quantization is a fixed memory lever on the weights themselves — three separate, non-interchangeable things that all happen to live in "making serving efficient."

**Why this matters:** Conflating these three is exactly the mistake the lesson's Hands-On Self-Check calls out — and the KV cache specifically is the resource capstone #10 (`case-studies/llm-inference-serving`) is built around, since it's usually the first thing that caps how many users one GPU can actually serve.
</details>

<details>
<summary>Question 5: What's the difference between an agent's short-term memory, its long-term memory, and checkpointing — and why would conflating them cause a design mistake?</summary>

**Answer:** Short-term memory is the conversation history held in the current session's context window — it disappears when the session ends unless something saves it elsewhere, and it's bounded by the context window's size. Long-term memory is information deliberately stored outside the current conversation (often in a database or vector database) so it can be retrieved in a *future, separate* session — it persists specifically because it was saved somewhere other than the context window. Checkpointing is different from both: it's saving an agent's progress *through* one long-running multi-step task, so an interrupted run can resume from the last completed step instead of restarting from scratch — it's about surviving interruption within a task, not about remembering across separate conversations. Conflating these would mean, for example, assuming a crashed agent "remembers" where it left off just because it has long-term memory of the user — it doesn't, unless checkpointing was implemented separately.

**Why this matters:** These three solve three different failure modes (context window overflow, no memory across sessions, lost progress on interruption) — treating any two of them as interchangeable leaves one of those failure modes completely unhandled.
</details>

## Hands-On Self-Check

There's no CLI or tool to run for this lesson — it's a shared-vocabulary refresher. Instead, confirm you can explain each of the following out loud, in your own words, without looking back at the lesson:

- [ ] I can explain why "non-determinism" means an AI application can't rely on the same testing assumptions as ordinary deterministic software.
- [ ] I can explain the difference between batching, KV cache, and quantization as three *separate* levers on model-serving performance — not synonyms for "making it faster."
- [ ] I can explain, in order, what happens to a document from the moment it's added to a RAG knowledge base to the moment it's used to help answer a query.
- [ ] I can name the difference between ReAct, plan-and-execute, and reflection as three distinct control-flow patterns, not interchangeable terms for "the agent loop."
- [ ] I can explain why an agent's short-term memory, long-term memory, and task checkpointing are three different mechanisms, each solving a different failure mode.
- [ ] I can say, for each of B2 (local serving), D4 (MCP), and D6 (declarative orchestration), which `learn-docker-ai-agents` lesson has the actual hands-on walkthrough.

## Next Step

Move to **Lesson 2: Core System-Design Fundamentals**.
