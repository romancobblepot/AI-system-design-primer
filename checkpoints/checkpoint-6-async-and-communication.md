# Checkpoint 6: Async and Communication

## Purpose

This checkpoint verifies you can distinguish message queues from task queues (and know when idempotency matters), compute how long a bounded queue takes to fill and what back pressure does once it does, distinguish TCP from UDP by what each guarantees and compute the real cost of a TCP handshake, and distinguish RPC from REST by calling shape — including why a long-running agentic task structurally cannot be served as one synchronous REST request.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1: A task queue delivers messages at-least-once, and a worker occasionally crashes after finishing a chunk-embedding task but before acknowledging it, causing that same task to be redelivered. Why doesn't this corrupt anything, and what would have to be true about the task for this same redelivery to actually cause a problem?</summary>

**Answer:** It doesn't corrupt anything because the task is idempotent: the embedding-and-store operation is keyed on a stable `chunk_id`, so redelivering and reprocessing the same task simply re-embeds the same chunk and overwrites its existing stored vector with the same (or equivalent) result — performing it twice has the same effect as performing it once. This would actually cause a problem if the task's effect were *not* idempotent — e.g. a task that unconditionally increments a "chunks processed" counter by one, rather than setting a per-chunk status to "done." A redelivery of that kind of task would double-count it, because at-least-once delivery only promises the task runs one or more times, never exactly once.

**Why this matters:** Choosing at-least-once delivery (the common, cheap default for most real message/task queue brokers) isn't free — it pushes an explicit obligation onto every consumer to make its own processing idempotent, and skipping that obligation is exactly how "redelivery" silently becomes "double-counted" in production.
</details>

<details>
<summary>Question 2: A task queue is receiving tasks at 150/sec while its worker pool can only drain 120/sec, and the queue is bounded at a maximum depth of 3,000 tasks. How long until the queue hits its bound, and what happens at that point?</summary>

**Answer:** Net growth rate = arrival_rate − drain_rate = 150 − 120 = 30 tasks/sec. Time to fill = max_queue_depth / net_growth_rate = 3,000 / 30 = 100 seconds. At that point, back pressure has to engage: depending on how the system is built, that's a blocking `queue.Queue.put()` call stalling the producer, an explicit rejection (e.g. HTTP 429 Too Many Requests), or load shedding (dropping the newest or oldest task) — in each case, the effective arrival rate the queue actually accepts gets capped at whatever the consumer can drain, so the queue stops growing further rather than consuming unbounded memory or letting every queued task's wait time grow forever.

**Why this matters:** An unbounded queue doesn't make an overload problem go away — it just relocates it from "a visible, immediate failure" to "an invisible, growing backlog that eventually becomes a crash or an unusably slow system." Back pressure is what makes the failure mode bounded and visible again.
</details>

<details>
<summary>Question 3: Why does a streamed LLM token response get sent over TCP rather than UDP, given that UDP has essentially zero connection-setup cost and TCP's three-way handshake adds real, measurable latency before any data can be sent?</summary>

**Answer:** TCP's handshake cost (one RTT for the TCP handshake, roughly another RTT for a TLS 1.3 handshake on top — e.g. ~80ms total at a 40ms RTT) is real, but it's paid once per connection, not once per token — amortized over a 500-token streamed response, that's roughly 0.16ms/token, negligible next to the typical 40-120ms-per-token inter-token latency an LLM-serving system already has. What TCP buys in exchange is reliable, ordered delivery: every token arrives exactly once and in the order it was generated, with lost data automatically retransmitted. UDP would skip the setup cost entirely, but provides no such guarantee — a lost or reordered UDP datagram carrying part of the token stream would require the application itself to detect and somehow recover from a gap or an out-of-order arrival in the middle of text it's actively streaming to a user, which risks silently returning corrupted or truncated response text. That trade only makes sense for traffic that can tolerate loss (DNS queries, real-time voice/video); it doesn't for response text.

**Why this matters:** "Lower setup cost" isn't the only axis that matters when choosing a transport protocol — what the protocol guarantees once the connection exists matters more for workloads where correctness of the delivered data (complete, in-order) isn't optional.
</details>

<details>
<summary>Question 4: What's the actual difference in calling shape between an RPC call and a REST call, and why does an agent's internal tool-calling mechanism (Lesson 1's function calling) naturally fit the RPC shape rather than the REST shape?</summary>

**Answer:** An RPC call is organized around a named *action* — a method name plus arguments (e.g. `run_shell_command(cmd, cwd)`) — that executes on a remote server and returns a result, the same shape as calling a local function. A REST call is organized around a *resource* (a noun, like a conversation or a document) addressed by a URL, manipulated through a small fixed set of HTTP verbs (GET/POST/PUT/DELETE), with each request carrying everything the server needs and nothing remembered between calls. An agent's tool-use/function-calling mechanism (Lesson 1, Concept D) already generates a structured request naming a specific function and its arguments — that's literally the RPC calling shape (an action plus arguments), even before you give it a formal name; it was never shaped like "create or update a resource," which is why naming it explicitly as RPC rather than REST isn't just terminology, it's recognizing a calling convention the mechanism already had.

**Why this matters:** The same agentic product typically uses both shapes at once — RPC internally for agent-to-tool calls, REST externally for its public API — and conflating the two obscures why those two parts of the same system behave so differently (e.g. why one is a stable, cacheable, widely-compatible interface and the other is a tightly-coupled set of named methods only the agent's own loop ever calls).
</details>

<details>
<summary>Question 5: A typical gateway or load balancer enforces a 60-second idle timeout on any single request/connection. Capstone #13's autonomous coding agent can run for multiple hours on one task. Why does that fact alone force the system to be built around an async task queue rather than a single synchronous REST call, and why doesn't capstone #4 belong in that same pairing?</summary>

**Answer:** A 90-minute (5,400-second) coding task run as a single held-open REST request would need the connection to stay open roughly 90x longer than a typical 60-second gateway idle timeout — the gateway would forcibly close the connection long before the task finishes, independent of anything the agent or backend wants to do. So the task has to be decomposed: a fast REST call submits the task and immediately returns a task ID; a task queue (Concept 1) runs the actual multi-step agent loop as a background job, fully decoupled from any one held-open connection; and a separate channel (polling, a webhook, or a reconnectable stream) delivers the "continuous progress reporting" capstone #13's own source describes. Capstone #4, by contrast, is Airbnb's search-ranking system (a model-architecture comparison between a GBDT and a neural ranker), which has no connection to long-running tasks, async queues, or agent loops at all; only capstone #13 actually supports this point.

**Why this matters:** This is the clearest version of this lesson's own core claim — "agentic systems lean on async queues far more than typical request/response apps" isn't a vague generalization, it's forced by a concrete number (task duration vs. gateway timeout) that makes a synchronous request/response shape structurally impossible, not just suboptimal. It's also a reminder to verify a cited source actually supports the specific claim being attached to it, rather than trusting a citation because it's already written down.
</details>

## Hands-On Self-Check

There's no CLI for this lesson — confirm you can do each of the following, without looking back at the lesson:

- [ ] I can state, from memory, what a task queue adds on top of a plain message queue, and name the three delivery guarantees (at-most-once, at-least-once, exactly-once).
- [ ] I can compute a bounded queue's time-to-full given an arrival rate, a drain rate, and a maximum depth, and name at least two different mechanisms a system could use to apply back pressure once it hits that bound.
- [ ] I can apply Little's Law (N = λ × W) to compute either the average wait time or the average number in a stable queue, given the other two values.
- [ ] I can state, from memory, the three concrete things TCP guarantees that UDP does not, and explain why head-of-line blocking is a direct consequence of one of them.
- [ ] I can run (or reason through line by line) the `submit_task` / `embed_chunk_worker` Python snippet and identify exactly which line implements back pressure and exactly which field makes the retry path idempotent.
- [ ] I can explain, in one sentence, why an agent's internal tool call is RPC-shaped while its public API is REST-shaped, using the same product as the example for both.

## Next Step

Move to **Lesson 7: Application Architecture and Security**.
