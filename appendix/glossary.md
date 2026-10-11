# Glossary

Every term introduced across the 11 lessons and the `case-studies/` capstones, one line each, for fast lookup. Organized alphabetically, with letter-group headers, so both the `case-studies/`-sourced entries and the lesson-sourced entries below sit in one unified, lookup-friendly list.

---

### Numbers

- **429 Too Many Requests** — the standard HTTP status code a server uses to tell a client it has sent too much traffic and should slow down or retry later; one explicit-rejection mechanism implementing back pressure.

### A

- **A record** — the DNS record type that maps a domain name directly to an IPv4 address, returned at the end of a full DNS resolution.
- **A/B testing** — running two or more versions of something concurrently against live traffic, splitting real requests between them, and comparing a measured outcome (e.g. a golden-set pass rate) between the groups, rather than only testing offline before a full rollout.
- **ABAC (attribute-based access control)** — an access-control model where a single IAM policy references the calling identity's own attribute (e.g. a `tenant_id` tag) via a policy variable at evaluation time, so one policy document — not one per tenant — still enforces per-tenant scoping on a shared, pooled resource.
- **AbortController** — a standard browser/JavaScript API object whose `.abort()` call cancels an in-flight request it's attached to, including a streaming one; the client-side half of mid-stream cancellation.
- **Action grounding / action-grounding error** — translating a model's intended action on a graphical interface into the correct concrete low-level input (e.g. the exact pixel coordinate of a button) such that executing it actually produces the intended effect; an action-grounding error is when the plan was correct but the concrete input emitted didn't actually correspond to the intended target, so the action "succeeds" while still being wrong — used in `case-studies/computer-use-agent` as this capstone's central structural failure mode.
- **Active learning (for rare classes)** — a training methodology where the model/pipeline itself actively selects which not-yet-labeled examples get sent to human labelers next (e.g. via uncertainty sampling), rather than labeling a passive random sample, to maximize how much signal a scarce labeling budget buys for a rare category — used in `case-studies/harmful-content-detection` as OpenAI's own three-pipeline mechanism, reported there to capture undesired content 10+ times more effectively than random sampling.
- **Active-active failover** — multiple replicas handle live traffic simultaneously at all times, so one failing causes no cutover delay, only reduced total capacity until it's replaced.
- **Active-passive failover** — one replica handles all live traffic while one or more standby replicas sit idle, taking over only after a failover delay once the active one fails.
- **AES (Advanced Encryption Standard)** — the symmetric-key cipher (commonly used with a 256-bit key) applied to data at rest, e.g. in a cloud storage bucket's default server-side encryption configuration.
- **API (Application Programming Interface)** — a defined contract letting one piece of software call functionality in another without needing to know its internal implementation, only what requests it accepts and what responses it returns.
- **Assertion** — the literal check inside a unit test (e.g. `assert actual == expected`) that fails the instant two values don't match exactly; the tool that breaks down for non-deterministic, semantically-variable LLM output.
- **At-least-once delivery** — a message delivered one or more times: never lost, but it can be delivered more than once (e.g. a consumer processes a message, then crashes or times out before acknowledging it, so the broker redelivers the same message to another consumer) — the common default delivery guarantee, requiring idempotent consumers to be safe.
- **At-most-once delivery** — a message delivered zero or one times: never duplicated, but it can be silently lost (e.g. the broker removes a message from the queue before a consumer finishes processing it).
- **Attack surface** — the complete set of points at which an untrusted actor can supply input to, or otherwise influence, a system; for an LLM, every piece of text it reads (not just the user's literal message) is part of it.
- **Authoritative name server** — the server holding a domain's own actual DNS records, queried last in a full DNS resolution chain (after a TLD server) and the one that finally returns the real A record.
- **Autoscaling** — automatically adding or removing worker capacity (processes, containers, or VMs) in response to a measured load signal (e.g. task-queue depth), rather than running a fixed pool sized once by hand.
- **Availability (nines)** — the percentage of time a system can correctly handle requests, conventionally expressed in "nines" (99%, 99.9%, 99.99%...), each additional nine cutting annual downtime roughly 10x.
- **Availability in parallel** — combining redundant replicas of the same component, where a request only fails if all of them fail at once; combined availability = 1 − [(1−A1)×(1−A2)×...], always higher than any single replica.
- **Availability in series** — chaining distinct components where a request must pass through all of them in sequence; combined availability = A1×A2×...×An, always lower than the weakest link.

### B

- **Back pressure** — a system signaling its upstream producer(s) to slow down, pause, or have new work rejected once a downstream consumer or queue can no longer keep up, instead of letting unbounded work accumulate.
- **Back-of-envelope estimate** — a deliberately quick, order-of-magnitude numeric calculation, built via a five-step method (state assumptions, decompose, compute with units, sanity-check the magnitude, name the most sensitive assumption) to catch a design mistake before real benchmarking.
- **BASE** — the consistency philosophy most NoSQL databases follow instead of ACID: Basically Available (stays responsive even if a response isn't freshest), Soft state (stored state changes over time even without new writes, as replicas converge), Eventually consistent.
- **Batching (continuous / dynamic batching)** — grouping multiple in-flight requests into one GPU forward pass instead of processing them one at a time; continuous (dynamic) batching lets a new request join an in-progress batch rather than waiting for it to finish.
- **Binarized embeddings** — an embedding whose floating-point dimensions have each been collapsed to a single bit, cutting storage by roughly 32x and reducing similarity comparison to a cheap Hamming-distance/popcount operation — used in `case-studies/visual-search` for Pinterest's index storage/retrieval.
- **Blast radius** — the actual scope of systems, data, or users a single failure, bug, or compromised credential can reach and affect.
- **Blocking the producer** — a back-pressure mechanism where a bounded queue's "add" operation doesn't return until space frees up, forcing the producer to slow to the consumer's drain rate.
- **BM25** — a classic lexical (non-embedding) ranking algorithm that scores a document's relevance to a query from exact term matches, weighted by inverse document frequency and normalized for document length — used in `case-studies/rag-contextual-retrieval` as "Contextual BM25."
- **Body** — the actual payload of an HTTP request or response — the content being sent or returned, as opposed to the headers' metadata about it.
- **Bridge model (tenant isolation)** — a hybrid multi-tenant isolation model where some system layers are siloed per tenant and others are pooled across all tenants — the real-world default for most systems.
- **BSON** — Binary JSON, a binary-encoded superset of the JSON format commonly used to physically store documents in a document-store database.

### C

- **Cache** — a smaller, faster-to-access store holding a copy of data normally served by a slower source (typically a database), so repeat requests don't pay that slower source's cost again; explicitly disposable, since the original stays safe in its source of truth.
- **Cache hit ratio** — the percentage of requests an edge node (or any cache) serves directly from cache rather than falling through to the origin/underlying store.
- **Cache miss** — a request that isn't served from cache and falls through to the origin server or underlying database, whether from a first-ever request or an expired entry.
- **Cache-aside (lazy loading)** — on a read, check the cache first; on a miss, read the underlying store and write the result into the cache before returning it — the cache is populated only by read misses.
- **Cancellation mid-stream** — a client terminating an in-progress stream before it finishes; only effective server-side if the generation loop itself checks for the disconnection and halts, since closing the client connection doesn't automatically stop a server from continuing to generate.
- **CAP theorem** — a distributed data system can guarantee at most two of Consistency (every read sees the latest write), Availability (every request gets a response), and Partition tolerance (the system keeps working despite dropped/delayed messages between nodes) during an actual network partition.
- **CDN (Content Delivery Network)** — a geographically distributed network of proxy servers (edge nodes) that cache static content close to end users, so a request can be served from a nearby node instead of traveling to the origin.
- **Chatbot vs. agent** — a chatbot only replies in text with no ability to act; an agent can additionally invoke tools or take actions as part of producing its response, usually in an observe-then-decide loop.
- **Chunking strategy** — the method used to split a large source document into smaller pieces before embedding and indexing it, since embedding an entire document as one vector loses too much retrievable detail.
- **Client** — a program or device that initiates contact with another program over a network to ask it to do something or return something; a role a program plays in a given exchange, not a fixed identity.
- **Client-side discovery** — the calling service queries a service registry directly to get currently-healthy instances and picks one itself.
- **Congestion control** — TCP's throttling of a sender based on inferred network congestion, independent of the receiver's own buffer state.
- **Connection pooling** — maintaining a fixed pool of already-open database connections that application threads borrow and return, instead of opening/tearing down a new connection per request.
- **Consistency pattern** — how far behind a read is allowed to be from the most recent write: strong, eventual, or weak consistency.
- **Consistent hashing** — a hashing scheme mapping both data items and nodes onto a circular hash space so adding/removing a node only remaps the small slice of keys near it, avoiding a full dataset reshuffle.
- **Consul** — HashiCorp's service-networking tool, combining a service registry with built-in health checking and a DNS/HTTP interface for looking up healthy instances.
- **Content filtering** — checking a model's generated natural-language output against a policy (usually via a trained classifier, not a fixed deny-list) before it's released to a user or acted on.
- **Context window** — the maximum number of tokens (input plus output) a model can process in a single request; a hard ceiling set by the model, not a configurable option.
- **Contextual Retrieval** — Anthropic's technique of prepending a short, LLM-generated, chunk-specific explanatory blurb to a document chunk before it's embedded and lexically indexed, so the chunk retains context that would otherwise be lost when split from its source document — used in `case-studies/rag-contextual-retrieval` as that capstone's central technique.
- **Copy-on-write (KV cache)** — letting two requests share the same underlying KV-cache block until one of them needs to modify it, at which point only that one gets its own private copy.
- **Cosine similarity** — the cosine of the angle between two vectors, ranging from -1 to 1, where values near 1 mean the vectors point in nearly the same direction; the common distance measure for comparing embeddings.
- **Cost attribution** — assigning a system's total usage-based spend back down to the specific dimension that generated it (a request, user, tenant, or product feature), rather than leaving it visible only as one aggregate number.

### D

- **Database** — a system for storing data durably, so it survives independently of and outlives any single running program, while supporting structured querying; a database is the source of truth for the data it holds.
- **Datagram** — a self-contained UDP packet that either arrives or doesn't, with no ordering or reliability guarantee.
- **Declarative orchestration** — defining an agent's or multi-agent system's configuration (model, tools, instructions, hand-offs) in a structured config file rather than imperative wiring code.
- **Denormalization** — deliberately duplicating data across tables to avoid an expensive JOIN at read time, at the cost of extra storage and an obligation to keep every duplicate consistent.
- **Deployable artifact** — anything with its own version identity that gets released and can be reverted independently of the rest of the system; treating a prompt this way gives it a version ID, change history, and rollback path.
- **Direct prompt injection** — prompt injection where the end user themselves, in their own message, writes the injected instruction.
- **Distributed cache** — a dedicated caching service (e.g. Redis, Memcached) shared across every application-server instance, sitting between the application layer and the database.
- **DNS (Domain Name System)** — the distributed system that translates human-readable domain names into the IP addresses computers use to connect to each other.
- **DNS resolution** — the chain a client walks to resolve an unknown domain name: a recursive resolver queries a root server, then a TLD server, then the domain's own authoritative name server, which returns the actual A record.
- **Document store** — a NoSQL database storing semi-structured, JSON-like documents where each document can have a different internal shape, queryable on fields inside the document, not just a top-level key.

### E

- **Edge node (point of presence)** — one of a CDN's geographically distributed proxy servers that caches content close to end users.
- **Embeddings** — a numeric vector produced by an embedding model representing a piece of text's meaning, so texts with similar meaning end up with vectors close together by a distance measure such as cosine similarity.
- **Encryption at rest** — encrypting data while it's stored (on disk, in a backup, in object storage) so someone who gains access to the storage medium itself still can't read it without the key.
- **Encryption in transit** — encrypting data while it's moving across a network, so anyone intercepting the traffic sees only ciphertext.
- **Equity re-ranking (equality of opportunity / equalized odds)** — adjusting a model's raw ranked output so equally-qualified members of different groups receive statistically equal outcomes, rather than shipping a purely score-maximizing ranking unmodified — used in `case-studies/pymk-friend-recommendation` for LinkedIn's fairness pass correcting a recommendation-feedback-loop advantage for already-frequent members.
- **etcd** — a distributed, strongly-consistent key-value store built on the Raft consensus algorithm, used internally by Kubernetes to track cluster state including which service endpoints currently exist.
- **Eval** — a measurement run over a whole set of examples using a scoring method tolerant of correct-but-differently-phrased output, replacing a single hardcoded-string assertion for freeform LLM generation.
- **Eventual consistency** — after a write, replicas will converge to the same value given enough time with no further writes, but with no guarantee on how long that takes.
- **Exactly-once delivery** — a message delivered precisely one time, with no loss and no duplication — the hardest delivery guarantee to implement correctly in a genuinely distributed system.
- **Example age** — a training-time feature equal to how old a training example is relative to the end of the training window, set to zero/negative at serving time — used in `case-studies/video-recommendation` to correct YouTube's recommender for an implicit bias toward the past.
- **External fragmentation** — wasted memory between allocations, where free space exists but isn't contiguous enough to satisfy a new request — the problem fixed-size paged blocks eliminate.
- **Extreme multiclass classification / candidate sampling (sampled softmax)** — framing prediction as classification among an extremely large number of classes, trained efficiently via candidate sampling (computing loss only over the true label plus sampled negatives) — used in `case-studies/video-recommendation` as YouTube's candidate-generation training method.

### F

- **Failover delay** — the time to detect a failed active replica and promote a standby, during which requests may fail, under active-passive failover.
- **Failure threshold** — the number of consecutive failed health-check probes required before a service instance is actually marked unhealthy and pulled from routing.
- **Fan-out (agentic)** — one upstream unit of work (a single agent reasoning step) triggering several downstream tool calls at once instead of one, finishing in roughly the time of its slowest call instead of their sum — a production fan-out burst inflates a task queue's effective arrival rate well beyond its raw step rate.
- **Feature hashing (the hashing trick)** — mapping a high-cardinality categorical feature to a fixed-size set of buckets via a deterministic hash function instead of an explicit lookup table — used in `case-studies/ctr-prediction` as a technique Google's own paper explicitly tested and rejected for its sponsored-search system.
- **Federation (functional partitioning)** — splitting one database into several separate databases along functional/domain lines, each handling a smaller slice of traffic, at the cost of resolving cross-database joins in application code.
- **Flow control** — TCP's throttling of a sender so it never overwhelms the receiver's buffer.
- **Forward pass** — one full run of input through a neural network's layers to produce output.
- **FTRL-Proximal / per-coordinate learning rates** — an online-learning algorithm that reliably drives unneeded model coefficients to exactly zero, paired with a learning-rate schedule computed separately per feature — used in `case-studies/ctr-prediction` as Google's own confirmed training algorithm, reported to cut AucLoss by 11.2% over a single global learning rate.

### G

- **Gateway-as-choke-point pattern** — a credential-handling architecture where an agent never holds a tool's real, long-lived credential directly; a single gateway holds the actual secrets and issues each tool call a short-lived, narrowly-scoped token on demand, so a leak exposes something that expires on its own.
- **GBDT (gradient-boosted decision trees)** — an ensemble of many shallow decision trees, built one at a time so each new tree corrects the errors the ensemble-so-far is still making — used in `case-studies/airbnb-search-ranking` as Airbnb's pre-deep-learning production ranking model.
- **Generated column** — a database column whose value is computed automatically from other columns in the same row (e.g. `shard_key = user_id % N`) rather than written directly by the application.
- **Geolocation-based routing** — a DNS routing policy that returns the endpoint registered as closest to (or designated for) the querying resolver's geographic region.
- **Golden dataset** — a fixed, curated set of input examples paired with hand-verified correct outputs, used to measure a pass rate across many examples rather than a single pass/fail.
- **Graceful degradation** — responding to a resource constraint (e.g. a near-exhausted token budget) by deliberately reducing scope, size, or quality of service through intermediate tiers, instead of failing outright the instant the constraint is hit.
- **Graph database** — a NoSQL database storing data explicitly as nodes and edges, purpose-built for cheap traversal queries that would otherwise require a chain of expensive relational self-joins.
- **gRPC** — a binary RPC protocol built on HTTP/2, commonly used for service-to-service calls.

### H

- **Head-of-line (HOL) blocking** — a consequence of TCP's ordered-delivery guarantee: if one segment is lost, every byte sent after it is held back from the application until the lost segment is retransmitted, even if those later bytes already arrived.
- **Header** — a key-value piece of metadata attached to an HTTP request or response, separate from its actual content, e.g. stating the body's format or the target host.
- **Health check** — a periodic probe (commonly a lightweight HTTP request) used to decide whether a service instance stays in the pool of routable candidates.
- **Heterogeneous network** — a graph containing more than one type of node and more than one type of edge — used in `case-studies/pymk-friend-recommendation` to describe LinkedIn's production graph.
- **HNSW (Hierarchical Navigable Small World)** — a graph-based approximate-nearest-neighbor index letting a vector database find the nearest stored vectors to a query without comparing against every vector one by one.
- **Horizontal scaling** — handling more load by adding more machines that each run a copy of the same thing and spreading work across them, rather than making one machine bigger; no single hard ceiling, but requires something in front to divide the work.
- **Hosted vs. self-hosted serving** — hosted serving means calling a model through a provider's API, paying per token while the provider owns the infrastructure; self-hosted means running the model's weights yourself, trading convenience for control over cost, data residency, and customization.
- **HTTP (Hypertext Transfer Protocol)** — the protocol nearly every API, web page load, and LLM request rides on; an HTTP request carries a method, target address, headers, and an optional body, and an HTTP response carries a status code, headers, and an optional body.
- **HTTP/2** — the second major version of HTTP, multiplexing multiple logical request/response streams over a single TCP connection, succeeding HTTP/1.1's one-request-per-connection-at-a-time model.
- **Human-in-the-loop approval gate** — a checkpoint in an agent's execution where a specific class of action is deliberately held, pending explicit human sign-off, before it's allowed to execute at all.

### I

- **Idempotent (operation)** — an operation that has exactly the same effect whether performed once or multiple times, required of consumers under at-least-once delivery.
- **Idle timeout** — the maximum duration a load balancer or reverse proxy lets a single request/connection sit waiting for a response before forcibly closing it.
- **Index (database)** — an auxiliary, separately-maintained lookup structure (commonly a B-tree) letting a database find matching rows by a column's value without scanning every row, at the cost of extra storage and slower writes.
- **Indirect prompt injection** — prompt injection where the injected instruction is planted in third-party content the model reads as part of its job (a retrieved document, a fetched web page, a tool's output), not in the end user's own message.
- **Input sanitization** — checking, filtering, or transforming untrusted input before it's used, so it can't be interpreted as something other than inert data by whatever processes it next.
- **Inter-token latency** — the delay between each subsequent generated token during LLM streaming, since each token depends on all the ones generated before it.
- **Internal fragmentation** — wasted memory inside an allocated block that's bigger than what's actually used.

### J

- **JSON Schema** — a formal, machine-checkable specification of what shape a JSON document must have (required fields, types, whether extra fields are allowed), used to validate or constrain structured model output.
- **JSON-RPC 2.0** — a lightweight, text-based RPC specification encoding a procedure call as a JSON object carrying a method name, a parameters object, and a request ID.

### K

- **Keeping a knowledge base fresh** — the ongoing operational problem of updating a RAG system's vector database as source documents change, so retrieval doesn't confidently ground answers in stale content.
- **Kernel (OS)** — the core operating system program mediating every system call; a plain container shares the host's kernel, while a microVM gives each sandbox its own.
- **Key-value store** — a NoSQL database storing an opaque value addressed only by a unique key, with no query capability beyond get/set/delete by that key.
- **KV cache** — the stored "key" and "value" tensors a transformer has already computed for earlier tokens, reused so generating the next token doesn't require recomputing them for the whole conversation so far.
- **KV-cache reuse** — reusing a previously computed KV cache across requests or conversation turns that share a common prefix, instead of recomputing it from scratch each time.

### L

- **L4 (transport-layer) load balancing** — routing based only on TCP/UDP connection-level information (source/destination IP and port), fast and protocol-agnostic but blind to request content.
- **L7 (application-layer) load balancing** — routing based on actual request content (HTTP method, path, headers, body), enabling capacity-aware routing at the cost of parsing every request.
- **LambdaRank / pairwise learning-to-rank (NDCG-weighted)** — a ranking-model training technique trained on (relevant, not-relevant) example pairs, with loss scaled by how much NDCG would change if the pair's positions were swapped — used in `case-studies/airbnb-search-ranking` as the second stage of Airbnb's neural-ranker evolution.
- **Latency** — the time between sending a request and receiving some or all of its response; a duration, not a rate.
- **Latency-based routing** — a DNS routing policy returning whichever registered endpoint has historically had the lowest latency from the resolver's location.
- **Least privilege** — granting any identity, process, service, or credential only the minimum set of permissions it actually needs, and no more.
- **Little's Law** — a queueing-theory identity holding for any stable queue: the average number of items in the system (N) equals the average arrival rate (λ) times the average time an item spends in the system (W) — `N = λ × W` — used in `case-studies/multi-agent-customer-support` to estimate concurrent support sessions from disclosed monthly-conversation and resolution-time figures.
- **LLM-as-judge** — using a separate LLM call to score a candidate output's quality against a rubric, instead of comparing it to one fixed expected string.
- **Load balancer** — a component distributing incoming requests across multiple backend instances so none is overwhelmed, and routing around failed instances.
- **Load shedding** — a back-pressure mechanism that drops the newest or oldest queued item rather than queueing it, accepting data loss in exchange for a bounded queue.
- **Local/open-weight serving** — running a model whose weights are downloadable and runnable on your own hardware, typically via a local serving tool rather than a data-center GPU cluster.
- **Long-term memory** — information an agent stores outside the current conversation (often in a database or vector database) so it can be retrieved and reused in future, separate sessions.

### M

- **Master-master replication** — a database replication pattern where more than one node accepts writes directly, removing the single-primary write bottleneck but requiring conflict resolution for concurrent conflicting writes.
- **Master-slave replication** — a database replication pattern where one primary node accepts all writes and one or more read replicas receive a continuous copy of those writes to serve read-only queries.
- **MCP (Model Context Protocol)** — an open protocol standardizing how an AI application connects to external tools and data sources through a common client-server interface, so a tool provider implements one server once for any MCP-compatible client.
- **Message queue** — a durable, ordered (or at least orderable) channel into which one or more producers write discrete messages, and from which one or more consumers read and acknowledge them, mediated by a broker (the server process that actually stores and routes messages, e.g. Apache Kafka, RabbitMQ, Amazon SQS); delivery is either point-to-point (each message to exactly one consumer) or publish/subscribe (each message to every subscribed consumer).
- **Method** — the verb at the start of an HTTP request stating what kind of action is being asked for, commonly GET (retrieve something) or POST (submit data, often to create something or trigger an action).
- **Microservices** — an architectural style splitting an application into a suite of small, independently deployable services, each in its own process, communicating over a network.
- **MicroVM** — an isolation boundary giving each sandboxed environment its own kernel rather than sharing the host's, stronger than a plain container while far lighter than a traditional full VM.
- **Model cascade (cheap-filter-then-expensive-judge chain)** — a multi-tier inference pipeline where a fast, cheap model screens every item first, escalating only flagged/uncertain items to a slower, expensive model — used in `case-studies/harmful-content-detection`'s LLM-era extension to cut judge-tier cost by roughly 90% in its own worked example.
- **Model routing / gateway** — a layer in front of one or more models that decides, per request, which model/provider handles it based on cost, latency, or capability, often also providing a unified API, rate limiting, and failover.
- **Monolith** — an application built and deployed as a single, unified process, where every piece of functionality runs and deploys together.
- **Multi-agent orchestration** — an architecture where more than one agent, often with distinct roles (planner, executor, validator), collaborates on a single task, coordinated by a supervisor or a hand-off protocol.
- **Multi-task (embedding) learning** — training one model with a shared backbone and several task-specific output heads at once, so a single learned embedding serves every task — used in `case-studies/visual-search` to replace three specialized Pinterest embeddings with one.
- **Multi-tenant** — a single deployed system or platform serving more than one distinct customer or organization from shared underlying infrastructure, rather than each customer getting a separate deployment.
- **Mutual TLS (mTLS)** — a TLS variant where both sides of a connection present and verify a certificate, not just the client verifying the server, so one compromised internal service can't impersonate another.

### N

- **Non-determinism** — the property that running the exact same prompt against the same model twice can produce two different outputs, because the model samples from a probability distribution over next tokens rather than always picking the single most likely one.
- **NoSQL** — a family of databases ("not only SQL") trading some of an RDBMS's guarantees for a data model matched to a specific access pattern and horizontal scalability.

### O

- **Observability** — the property that a system's internal behavior can be understood from the data it emits (logs, metrics, traces/spans) without having anticipated the exact question in advance.
- **Online learning** — a training paradigm where a model updates its parameters immediately after each training example arrives, rather than training over a fixed dataset in repeated passes — used in `case-studies/ctr-prediction` so Google's CTR model can incorporate new clicks within minutes.
- **OSWorld** — a benchmark and execution environment evaluating an agent's ability to complete real computer tasks via free-form mouse/keyboard control, graded by an automated check of the environment's real final state — used in `case-studies/computer-use-agent` as the benchmark Anthropic's computer-use announcement reports results against.

### P

- **Paged block / block table** — a fixed-size chunk of KV-cache memory (a "page") and the per-request lookup table mapping logical cache positions to the physical blocks holding them.
- **PagedAttention** — an attention mechanism that stores a request's KV cache in fixed-size, non-contiguous memory blocks (modeled on OS virtual-memory paging), instead of one large contiguous allocation per request.
- **Parameterized queries** — passing user input to a database as a separate, explicitly-typed parameter rather than concatenating it into query text, preventing SQL injection.
- **Partial-result UX** — showing a response incrementally as it's generated instead of making the user wait for the entire response, reducing perceived (not actual) latency.
- **Per-tool credential scoping** — giving each distinct tool an agent can call its own credential, scoped to only what that specific tool needs, rather than one shared credential behind every tool.
- **Percentile latency (p50/p90/p99)** — a way of summarizing a latency distribution that an average can hide: the p50/p90/p99 is the latency value below which that percentage of requests fall.
- **Performance** — how quickly a single unit of work completes under a given load.
- **Plan-and-execute (control-flow pattern)** — the model produces a full multi-step plan up front, then executes each step in sequence, optionally revising the plan if a step's result changes what's needed.
- **Point-to-point (message queue)** — a message-queue delivery mode where each message is delivered to and processed by exactly one consumer, even if several are listening.
- **Pool model (tenant isolation)** — a multi-tenant isolation model where tenants share the same underlying resources, with isolation enforced entirely in software rather than by physical separation.
- **Preemptive scheduling (LLM serving)** — pausing or evicting a lower-priority in-flight request's KV cache to free capacity for a higher-priority one, then resuming it later.
- **Producer / consumer / broker (message queue)** — the producer writes messages into a queue, the consumer reads and acknowledges them, and the broker is the server process (e.g. Kafka, RabbitMQ, SQS) that actually stores and routes messages between them.
- **Prompt as attack surface** — the property that any text an LLM reads can contain instructions the model may follow, whether or not the developer intended that text to carry instructions.
- **Prompt caching** — a provider-side feature where a fixed or repeated portion of a prompt is processed and stored once, so subsequent requests reusing that prefix skip reprocessing it.
- **Prompt injection** — the attack exploiting the prompt-as-attack-surface property: crafted text, supplied through any input the model reads, that causes it to follow instructions other than the ones its developer intended.
- **Prompt versioning** — giving each distinct version of a prompt's text a stable identifier (a version number or content hash) so which exact prompt produced a given output is always answerable.
- **Protocol** — an agreed-upon set of rules two systems follow so their messages to each other are structured in a way both sides understand.
- **Publish/subscribe (pub/sub)** — a message-queue delivery mode where every message is delivered to every currently-subscribed consumer, used for broadcasting an event to multiple independent listeners.
- **Pull CDN** — a CDN that fetches content from the origin automatically on the first request through a given edge node, then serves subsequent requests from cache until it expires.
- **Push CDN** — a CDN where the origin proactively uploads content to CDN nodes ahead of any user requesting it.

### Q

- **QPS (queries per second)** — the classic measure of how many requests a system handles per second; the AI-world equivalent, measured at the token level, is token-generation throughput.
- **Quantization** — storing a model's weights using fewer bits per number than they were trained with, shrinking memory footprint and often speeding inference at some cost to output quality.
- **Queue-depth alerting** — a human-facing threshold that pages or notifies an on-call engineer when a task queue's depth crosses a level the autoscaler itself hasn't yet resolved, covering the reaction lag before new capacity comes online.
- **Quorum write** — a write that must be acknowledged by enough replicas (e.g. 2 of 3) before it's considered complete, the mechanism behind strong consistency.

### R

- **Raft consensus algorithm** — a protocol by which a cluster of nodes agrees on a single, consistent sequence of state changes even if some nodes fail; the mechanism underneath etcd's consistency guarantees.
- **RAG (Retrieval-Augmented Generation)** — the pipeline letting an LLM answer using information outside its training data: chunking and embedding a corpus ahead of time, retrieving the most relevant chunks at query time, and inserting them into the prompt as context.
- **Ranking function (multi-signal scoring)** — a scoring function combining several separate input signals (e.g. item popularity and predicted rating) into one score, rather than being identical to any one of them — used in `case-studies/netflix-feed-ranking` as Netflix's own illustrated starting point for row ranking.
- **Rate limit** — a cap on how much traffic a client is allowed to send in a given time window, to protect backends and enforce fair usage or billing tiers.
- **RDBMS** — a relational database management system built around fixed-schema tables joined via foreign keys and queried with SQL, typically offering ACID guarantees.
- **ReAct (control-flow pattern)** — the model alternates, in a loop, between a reasoning step, taking an action, observing the result, and reasoning again, until it decides it has enough to answer.
- **Read replica** — a database node that receives a continuous copy of a primary's writes and serves read-only queries, spreading read load across many nodes.
- **Recursive resolver** — the server (commonly run by an ISP or a public service like 8.8.8.8) a client directly asks to resolve a domain name, which itself walks the chain of root, TLD, and authoritative name servers on the client's behalf.
- **Reflection (control-flow pattern)** — giving the model a separate step to critique or evaluate its own prior output or action before finalizing it or moving on.
- **Refresh-ahead** — a caching strategy where the cache proactively re-fetches a soon-to-expire, still-popular entry before its TTL runs out, to avoid a thundering herd at expiry.
- **Regression suite** — a golden dataset run automatically before a prompt, model, or pipeline change ships, to catch cases where previously-correct behavior becomes incorrect.
- **Replication (availability)** — keeping more than one live copy of a service or its data across separate nodes, so one node's failure doesn't take the whole system down.
- **Replication lag** — the delay between a write committing on a database's primary and that write becoming visible on a given read replica.
- **Request** — the message a client sends to a server, asking it to perform an action or return data.
- **Request/response cycle** — the full round trip of a client sending a request, a server processing it and producing a response, and that response traveling back to the client; the basic, repeatable unit nearly every network interaction reduces to.
- **Reranker / reranking** — a second retrieval stage where a model scores each (query, candidate-chunk) pair jointly, producing a more precise relevance ranking than independent embedding-similarity lookup — used in `case-studies/rag-contextual-retrieval` as the final step before generation.
- **Response** — the message a server sends back to a client once it's done handling a request, containing the result, a confirmation, or an error.
- **Residual / base estimate** — a base estimate is an existing, simpler prediction from a separate system; a residual is the gap between the actual outcome and that estimate — predicting the residual rather than the absolute value means a model only has to learn the gap — used in `case-studies/uber-eta-prediction` as DeepETA's central pattern.
- **Resolve rate** — the percentage of a benchmark's tasks scored "resolved" under that benchmark's own grading criterion — used in `case-studies/autonomous-coding-agent` to report Cognition's own reported Devin figures.
- **REST (REpresentational State Transfer)** — an API style built around resources (nouns) addressed by URLs, manipulated through a small fixed set of HTTP verbs, with stateless requests.
- **Reverse proxy** — a server sitting in front of one or more backends, forwarding client requests on their behalf while hiding backend topology from the client; distinct from a load balancer in that it doesn't have to balance traffic across multiple instances.
- **Rollback** — reverting a live system back to a previous, known-working version in response to a problem with the current one.
- **Root server** — the server queried first in a full DNS resolution chain, responsible for directing a recursive resolver's query to the correct TLD server.
- **RPC (Remote Procedure Call)** — an API style built around invoking a named action (a verb): a client calls a method (e.g. `run_shell_command(cmd, cwd)`) that executes on a remote server, with the RPC framework handling argument serialization and the network call itself, so the call looks and feels like a local function call; gRPC and JSON-RPC 2.0 are concrete RPC frameworks.

### S

- **Scalability** — a system's ability to keep performance acceptable as load grows, typically by adding more resources.
- **Schema-constrained output** — forcing a model's structured output to conform to a predefined schema (commonly JSON Schema), either by constraining decoding directly or by validating and retrying after the fact.
- **Semantic caching** — a caching strategy for LLM apps that checks whether a new prompt is semantically similar enough to a cached prompt (via embedding similarity) to reuse its cached response, instead of requiring an exact string match.
- **Server** — a program or device that listens for incoming requests, does the work needed to handle one, and sends back a response; a role a program plays in a given exchange, not a fixed identity — a server can itself act as a client to some other server.
- **Server-Sent Events (SSE)** — a standardized, one-directional HTTP streaming mechanism where a server sends a sequence of `data:`-prefixed text events over a kept-open connection instead of one complete response body.
- **Server-side discovery** — the caller sends its request to a fixed address (a load balancer/gateway), which queries the service registry and routes on the caller's behalf.
- **Service discovery** — the mechanism by which services in a distributed system find each other's current network location without hardcoding an address.
- **Service rate** — the maximum rate at which a queue's consumer side can process arriving work; a queue is stable only while the arrival rate stays below it.
- **Service registry** — the data store tracking which instances of which services currently exist, and where.
- **Session persistence (sticky sessions)** — a load-balancer configuration routing all requests from the same client to the same backend instance repeatedly, needed when that backend holds per-client state.
- **Shard key** — the column (or function of it) used to decide which physical shard a given row belongs on.
- **Sharding (horizontal partitioning)** — splitting the rows of a single logical table across multiple physical database nodes, usually by a shard key, scaling both reads and writes for that table.
- **Short-term memory** — the information an agent keeps available within a single conversation or session, held in the context window and passed back to the model on every turn.
- **Silo model (tenant isolation)** — a multi-tenant isolation model where each tenant gets its own fully dedicated resources — the strongest isolation, at the cost of pooling's economies of scale.
- **Single responsibility principle (SRP)** — the design rule that a component should have one, and only one, reason to change, used to decide where service/module boundaries should go.
- **Source of truth** — the one authoritative store a system treats as correct when copies of the same data disagree — normally the database, with every cache ultimately checked against it or rebuilt from it.
- **Span** — one discrete unit of work inside a trace (one LLM call, one tool invocation), with its own start/end time, inputs, outputs, and metadata; spans nest via a parent-span id.
- **SQL injection** — untrusted input containing SQL syntax that, if concatenated directly into a query string, gets executed as part of the query rather than treated as a literal value.
- **SQL tuning** — making a single database node's own queries more efficient (indexing, query rewriting, connection pooling) without changing the topology above it.
- **SSL bridging** — re-encrypting traffic for the internal hop between a load balancer and backend after SSL/TLS termination, so that hop isn't left unencrypted.
- **SSL/TLS termination** — a load balancer decrypting incoming HTTPS traffic itself and forwarding the now-plaintext request to backends over an internal network.
- **State / checkpointing** — saving an agent's intermediate progress through a long-running, multi-step task at defined points, so an interrupted run can resume rather than restart from scratch.
- **Stateless requests** — a REST request design where each request carries everything the server needs to process it, independent of any prior request.
- **Status code** — a three-digit number at the start of an HTTP response summarizing the outcome: codes starting with 2 mean success, 4 mean the client's request was the problem, and 5 mean the server's own handling was the problem.
- **Strong consistency** — after a write completes, every subsequent read from any replica sees that write immediately, typically achieved via a quorum write.
- **STS AssumeRole (AWS)** — the AWS Security Token Service call that issues a short-lived, narrowly-scoped credential (via a session policy and a `DurationSeconds` expiry) instead of handing out a long-lived secret directly — the concrete mechanism behind the Gateway-as-choke-point pattern.
- **SWE-bench** — a benchmark of real GitHub issues paired with the human PR that originally fixed each one; a model-generated patch is scored "resolved" only if it meets a test-based grading criterion — used in `case-studies/autonomous-coding-agent` as the offline benchmark Cognition's Devin announcement reports results against.

### T

- **Task queue** — a message queue specialized for distributing units of work to a worker pool, adding job status tracking, retry policy, and result retrieval on top of a plain broker.
- **TCP (Transmission Control Protocol)** — a connection-oriented transport protocol requiring a three-way handshake before data flows, guaranteeing reliable, ordered delivery via flow and congestion control.
- **Tenant isolation** — the set of guarantees that one tenant's data, credentials, and usage can't be read, modified, or affected by another tenant on the same shared platform.
- **Three-way handshake** — the SYN, SYN-ACK, ACK exchange establishing a TCP connection and synchronizing initial sequence numbers before any application data moves.
- **Thundering herd** — a burst of many concurrent requests that all miss the cache for the same key at the same instant (e.g. right as its TTL expires) and fall through to the database simultaneously.
- **Throughput** — the rate at which a system completes units of work, a count per unit time, as distinct from latency's duration.
- **Time to first token (TTFT)** — the delay between sending a request and receiving the first generated token, dominated by how long the model takes to process the whole input prompt before producing output.
- **TLD server** — the server responsible for all domains under one top-level domain (e.g. all `.com` domains), queried during DNS resolution after a root server.
- **TLS (Transport Layer Security)** — the standard protocol for encryption in transit, in which two endpoints exchange and verify certificates and agree on encryption keys before all further data is encrypted.
- **Token bucket algorithm** — a rate-limiting method where a "bucket" holds a capped number of tokens that refill at a steady rate; requests are throttled once it's empty — used in `case-studies/llm-api-gateway` to rate-limit by token count rather than request count.
- **Token economics** — reasoning about AI costs in terms of tokens rather than requests: per-million-token pricing (usually cheaper for input than output), and a token averaging roughly 3/4 of an English word.
- **Token-based cost and latency** — the property that both the dollar cost and the response time of an AI request scale with the number of tokens processed and generated, not a fixed per-request charge.
- **Token-generation throughput** — the aggregate rate, across all requests a serving system is handling, at which it produces output tokens; the AI-world equivalent of QPS, measured at the token level.
- **Tool use / function calling** — a model generating a structured request to call a named function with specific arguments, which the surrounding application then actually executes.
- **Total completion time** — TTFT plus (output tokens − 1) × inter-token latency: the full time until the last token of a response arrives.
- **Trace** — the complete record of one end-to-end operation (e.g. one agent session), composed of nested spans.
- **Transformer** — the neural network architecture behind virtually all modern LLMs, processing a sequence by weighing how much each token should "attend to" every other token.
- **Triangle-closing** — a graph-based candidate-generation feature: if A knows B and B knows C, hypothesizing A and C are unusually likely to know each other too — used in `case-studies/pymk-friend-recommendation` as LinkedIn's core friends-of-friends signal.
- **TTL (time to live)** — a duration published with a DNS record or cache entry telling resolvers/clients how long they may trust a cached answer before re-checking it.
- **Two-stage retrieval-then-rank architecture (candidate generation + ranking)** — a recommender design where a cheap first-stage model narrows a huge corpus to a small candidate set, and a more expensive second-stage model scores only that set — used in `case-studies/video-recommendation` as YouTube's own split.

### U

- **UDP (User Datagram Protocol)** — a connectionless transport protocol with no handshake or setup cost, sending discrete datagrams with no ordering, reliability, or flow-control guarantee.
- **Unit test** — a small, automated test checking one piece of code's behavior in isolation by comparing its actual output against one expected, hardcoded value.
- **Usage-based cost model** — a pricing/cost structure where cost scales directly with how much a system is actually used (e.g. tokens processed), rather than a fixed charge regardless of volume.

### V

- **Validator/guardrail agent (and validator catch-rate)** — a distinct agent whose only job is checking another agent's proposed action against policy, correctness, and safety constraints before it executes; validator catch-rate is the fraction of actually-bad proposed actions it correctly blocks — used in `case-studies/multi-agent-customer-support` as that capstone's central teaching point.
- **Vector database** — a database purpose-built to store large numbers of embeddings and answer "find the k nearest vectors to this query" efficiently, via a specialized index such as HNSW.
- **Vertical scaling** — handling more load by making a single machine bigger or more powerful (more CPU, memory, faster disk) rather than adding more machines; has a hard ceiling, since there's always a biggest machine you can buy or rent.

### W

- **Weak consistency** — no guarantee at all about when, or whether, a given read will reflect a given write; used in systems optimized purely for speed.
- **Weighted round robin (DNS)** — a DNS routing policy returning different IPs to different queries according to configured weights, used for traffic splitting rather than failover.
- **Wide-column store** — a NoSQL database where every row is indexed by a single row key but different rows can have a hugely different, sparse set of columns, grouped into column families stored together on disk.
- **Write-behind (write-back)** — a caching strategy where a write is applied to the cache immediately and acknowledged right away, while the write to the underlying store is deferred and applied asynchronously.
- **Write-through** — a caching strategy where every write is applied to the cache and the underlying store together, synchronously, before the write is considered complete.

### Z

- **Zookeeper** — an older Apache coordination service providing distributed locks, configuration storage, and group membership, historically used e.g. by Kafka brokers to discover each other.
