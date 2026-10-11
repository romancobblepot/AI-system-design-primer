# Checkpoint 2: Core System-Design Fundamentals

## Purpose

This checkpoint verifies you have a solid working vocabulary for the classic distributed-systems basics (P1-P4: client/server, APIs/HTTP, databases/caches, latency/throughput/scaling) that the rest of this repo's core system-design lessons assume you already know, before moving on to the full-depth teaching in Lesson 3.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1: What's the actual difference between a client and a server, and why does nearly every network interaction in this repo start from the same request/response shape?</summary>

**Answer:** A client is whichever side initiates an exchange — it sends a request asking the other side to do something or return something. A server is whichever side listens for that request, handles it, and sends back a response. These are roles a given program plays in a specific exchange, not fixed identities — a server can act as a client to some other server (e.g. an API server calling a database). Nearly every network interaction in this repo reduces to the same repeatable unit — client sends request, server processes and responds, client receives the response — because that cycle is the one thing almost every more complex pattern (a load balancer choosing a server, an agent calling a tool, a multi-step task) is ultimately built out of, not something fundamentally different from it.

**Why this matters:** Lesson 4's load-balancer and reverse-proxy Concepts are entirely about deciding *which* server a given request's cycle gets routed to — that only makes sense once "client," "server," and "request/response cycle" are already familiar, not new vocabulary to parse at the same time.
</details>

<details>
<summary>Question 2: What makes something an "API" as opposed to just two programs that happen to exchange bytes, and what are the four parts HTTP's anatomy breaks a request/response pair into?</summary>

**Answer:** An API is a *defined contract* — it specifies exactly what requests are accepted and what responses come back, letting one piece of software use another's functionality without knowing how it's implemented internally. Two programs exchanging arbitrary bytes with no agreed structure aren't using an API; they just happen to be connected. HTTP, the protocol nearly everything in this repo rides on, structures a request around a **method** (what kind of action is being asked for, e.g. GET or POST) and a **body** (the actual payload), plus **headers** (metadata about the request, separate from its content) — and structures a response around a **status code** (a three-digit summary of the outcome) plus its own headers and body.

**Why this matters:** Lesson 6's Concept 4 (RPC vs. REST) assumes you can already name a method and a body — it spends its own depth comparing calling *shapes* (actions vs. resources), not re-explaining HTTP's basic anatomy.
</details>

<details>
<summary>Question 3: What's the fundamental difference in purpose between a database and a cache — and why is it acceptable for a cache to lose its data when it would not be acceptable for a database to lose the same data?</summary>

**Answer:** A database is durable storage and the **source of truth** — it's designed so data survives independently of, and outlives, any single running process, including a crash, and it's the one place a given piece of data is guaranteed correct and complete. A cache is a smaller, faster copy of data that's normally served by a slower source (typically the database), kept specifically so repeat requests don't have to pay that slower source's cost again. Losing a cache's contents is acceptable precisely because the original, authoritative copy still exists safely in the database — the cache can simply be rebuilt or refetched. Losing a database's contents is not acceptable in the same way, because there is no other authoritative copy to rebuild it from.

**Why this matters:** This durable-vs-disposable distinction is exactly what Lesson 5's Concepts 1-3 build on without re-explaining — RDBMS scaling and NoSQL types assume you already know a database must not lose data, and the four caching strategies (cache-aside, write-through, write-behind, refresh-ahead) assume you already know why losing a cache is a tolerable, recoverable event.
</details>

<details>
<summary>Question 4: In plain terms, what's the difference between latency and throughput — and why can a system have high throughput while still feeling slow to one particular user (or the reverse)?</summary>

**Answer:** Latency is a per-request experience: how long one single thing takes to happen, the "this feels slow" complaint. Throughput is an aggregate, system-wide measure: how much work gets done in a given stretch of time, the "can this system actually keep up with the volume" complaint. These move independently — a system can process a huge number of requests per second in aggregate (high throughput) while any one individual request still takes a while to come back (high latency), because high throughput is often achieved precisely by processing many requests together rather than rushing any single one. Conversely, a system could respond to one request almost instantly (low latency) while still being unable to sustain many such requests per second at once (low throughput) if it has no spare capacity for concurrent work.

**Why this matters:** This plain-language split gives you an early first pass at the distinction Lesson 3's Concept 1 reframes for LLM serving — time-to-first-token and inter-token latency on one side, token-generation throughput on the other. Lesson 3 does redefine latency and throughput in its own right rather than assuming this split going in, but having already met it in plain language here makes that fuller, AI-specific treatment land as a refinement, not entirely new material.
</details>

<details>
<summary>Question 5: What's the difference between vertical scaling and horizontal scaling as two ways of handling more load, and what's the basic limitation of each?</summary>

**Answer:** Vertical scaling handles more load by making a single machine bigger or more powerful — more CPU, more memory, a faster disk — without adding any additional machines. Its basic limitation is a hard ceiling: there's always a biggest machine you can actually buy or rent, so vertical scaling alone eventually runs out of room. Horizontal scaling handles more load by adding more machines that each run a copy of the same thing and splitting the work across all of them. It has no single hard ceiling the way vertical scaling does, but it requires something in front of those machines — a mechanism to actually divide incoming work between them — which doesn't exist until you build or add it.

**Why this matters:** Nearly every pattern taught in Lessons 3-7 (replication, sharding, load balancing) is a precise, production-grade way of actually doing horizontal scaling — recognizing "add more machines and split the work" as the plain-language version of what those Concepts implement is what makes their added detail land as a refinement, not as entirely new material.
</details>

## Hands-On Self-Check

There's no CLI or tool to run for this lesson — it's a shared-vocabulary refresher. Instead, confirm you can explain each of the following out loud, in your own words, without looking back at the lesson:

- [ ] I can explain why "client" and "server" are roles a program plays in a given exchange, not fixed identities — and give an example of something that's a server in one exchange and a client in another.
- [ ] I can name the four parts of HTTP's request/response anatomy (method, status code, header, body) and say which side of the exchange each one belongs to.
- [ ] I can explain why a database must not lose data but a cache losing its data is an acceptable, recoverable event.
- [ ] I can explain, without using the word "speed" for both, the actual difference between latency and throughput.
- [ ] I can explain the difference between vertical and horizontal scaling, and name the basic limitation of each.

## Next Step

Move to **Lesson 3: Scalability and Availability**.
