# Lesson 2: Core System-Design Fundamentals — A Compressed Refresher

**Time:** 30-45 minutes
**Tool(s):** Conceptual refresher — no single tool; this is a shared-vocabulary primer, not a hands-on tool lesson

## Learning Objectives

By the end of this lesson, you will:

- Have a shared, precise vocabulary for the classic distributed-systems basics (P1-P4 below) that this repo's core system-design lessons assume you already know
- Understand the client/server request/response cycle, what an API and HTTP actually are, what a database and a cache are each for, and the everyday meaning of latency, throughput, and scaling
- Know exactly where each of these ideas gets picked up again and taught at full depth later in this repo (Lessons 3-6)

---

## P1. Client/server & the request/response cycle

Almost every interaction between two programs over a network reduces to the same shape: one side asks, the other side answers. That shape has names for its two participants and for the message pair itself — names used constantly from here on.

| Term | Full definition | Why it matters |
|---|---|---|
| **Client** | A program or device that initiates contact with another program over a network to ask it to do something or return something — a web browser, a mobile app, another backend service, or an AI agent calling a tool are all clients in this sense. A client doesn't have to be "a person's device"; it's just whichever side starts the exchange. | Nearly every diagram in this repo starts with "a client sends a request" — recognizing which side is playing this role is the first step in reading any of them. |
| **Server** | A program or device that listens for incoming requests, does whatever work is needed to handle one, and sends back a response. A server can itself act as a client to some other server (e.g. an API server that calls a database server) — "client" and "server" are roles a given program plays in a specific exchange, not fixed identities. | This is the role every load balancer, reverse proxy (Lesson 4), and database (Lesson 5) ultimately sits in front of or behind — those components all exist to manage traffic between clients and servers, not to replace either role. |
| **Request** | The message a client sends to a server, asking it to perform an action or return data. | A request is the unit of work everything downstream (load balancing, rate limiting, caching) ends up operating on. |
| **Response** | The message a server sends back to the client once it's done handling a request — containing the result, a confirmation, or an error. | Whether a response ever arrives, and how long it takes, is the literal definition of availability and latency used throughout this repo. |
| **Request/response cycle** | The full round trip: a client sends a request, the server processes it and produces a response, and the response travels back to the client. This is the basic unit nearly every network interaction in this repo assumes — even a multi-step agent task (Lesson 6) is ultimately built out of many of these cycles, not something fundamentally different from one. | Understanding this as one repeatable unit is the prerequisite for Lesson 4's load balancers and reverse proxies, which exist specifically to decide *which* server a given request's cycle actually gets routed to. |

**Why this still matters for later lessons:** P1's client/server roles and request/response cycle are what Lesson 4's load-balancer and reverse-proxy Concepts (J3/J4) assume you already have a name for — those Concepts are entirely about deciding which server a request reaches, which only makes sense once "client," "server," and "request/response cycle" aren't new vocabulary.

---

## P2. APIs and protocols at a glance

Once two programs agree to talk via requests and responses, they still need to agree on *how* — what a request may ask for, and what shape the answer takes. That agreement is an API; HTTP is the specific, near-universal protocol nearly everything in this repo rides on to make it concrete.

| Term | Full definition | Why it matters |
|---|---|---|
| **API (Application Programming Interface)** | A defined contract that lets one piece of software call functionality in another piece of software, without needing to know how that other software is actually implemented internally — only what requests it accepts and what responses it returns. | "API" is used constantly in this repo (model APIs, gateway APIs, tool-calling APIs) to mean exactly this: a stable contract, not an implementation detail. |
| **Protocol** | An agreed-upon set of rules two systems follow so their messages to each other are structured in a way both sides understand — covering things like how a message starts, what fields it must have, and how a reply is matched back to its request. | Without an agreed protocol, "client" and "server" could send bytes at each other that neither side could actually parse — a protocol is what makes the request/response cycle (P1) actually work in practice. |
| **HTTP (Hypertext Transfer Protocol)** | The specific protocol that nearly every API, web page load, and LLM request in this repo is built on top of. An HTTP request has a **method** stating what kind of action is being requested, a target address, a set of **headers**, and an optional **body**; an HTTP response has a **status code** stating the outcome, its own headers, and an optional body. | Every JSON payload, every gateway, and every load balancer later in this repo (Lessons 3-7) is described in terms of an HTTP request or response — this is the one protocol whose anatomy is worth knowing by name up front. |
| **Method** | The verb at the start of an HTTP request stating what kind of action is being asked for — commonly **GET** (retrieve something, without changing it) and **POST** (submit data, often to create something or trigger an action). | The method is the first thing any router, gateway, or API documentation page tells you about a request — it's the "what kind of ask is this" field. |
| **Status code** | A three-digit number at the start of an HTTP response summarizing the outcome at a glance — by convention, codes starting with 2 mean success (e.g. 200 OK), codes starting with 4 mean the client's request was the problem (e.g. 404 Not Found), and codes starting with 5 mean the server's own handling was the problem (e.g. 500 Internal Server Error). | Status codes are how a caller finds out what happened without parsing the whole response body — later lessons reference specific codes (e.g. 429 Too Many Requests in Lesson 6) assuming this category system is already familiar. |
| **Header** | A key-value piece of metadata attached to an HTTP request or response, separate from its actual content — e.g. stating what format the body is in, or which host the request is addressed to. | Headers are where routing, authentication, and caching instructions typically live — a load balancer or reverse proxy (Lesson 4) often makes its routing decision by reading headers, not the body. |
| **Body** | The actual payload of an HTTP request or response — the content being sent or returned, as opposed to the headers' metadata about it. For an API, this is usually structured data such as JSON. | The body is what carries the substance of a request (e.g. the prompt being sent to a model) — distinguishing it from headers matters because the two are handled very differently by the systems in between client and server. |

**Why this still matters for later lessons:** P2's HTTP anatomy — specifically **method** and **body** — is exactly what Lesson 6's Concept 4 (RPC vs. REST) assumes you can already name, so that Concept can go straight into comparing *calling shapes* — actions vs. resources — instead of first explaining what a method or a body is.

---

## P3. Databases and caches at a glance

Once a server needs to remember something between requests — or across a restart — it needs somewhere to keep that data. Two very different tools get reached for here, and conflating them is a common, costly mistake: one is built to never lose data, the other to be fast even if it occasionally does.

| Term | Full definition | Why it matters |
|---|---|---|
| **Database** | A system for storing data durably — meaning the data survives independently of, and outlives, any single running program or process, including a crash or restart — while supporting structured ways to query and retrieve it later. A database is the **source of truth**: the one place a given piece of data is guaranteed to be correct and complete, even if other copies of it exist elsewhere. | Every other store described in this repo (a cache, below, or a vector database, Lesson 1's C2) is judged against this standard — "is this durable storage, or just a faster copy of something durable stored elsewhere." |
| **Cache** | A smaller, faster-to-access store that holds a copy of data normally served by a slower source (typically a database), specifically so repeat requests for the same data don't have to pay that slower source's cost again. A cache is explicitly disposable: because the original data still lives safely in its source of truth, losing the cached copy (to a restart, an eviction, or an expiry) is an acceptable, recoverable event, not data loss. | The entire point of a cache is this disposability trade-off — speed, in exchange for being willing to lose or serve a slightly stale copy — which is the exact trade-off Lesson 5's caching-strategies Concept (K3) spends a full Concept examining in depth. |
| **Source of truth** | The one authoritative store a system treats as correct when there's any disagreement between copies of the same data — normally the database, with every cache ultimately checked against it or rebuilt from it. | Knowing which store is the source of truth is what tells you which one is safe to lose and which one isn't — without naming this, "database" and "cache" can start to sound interchangeable, which they aren't. |

**Why this still matters for later lessons:** P3 (databases and caches) is stated here plainly, before Lesson 5's much deeper Concepts 1-3 take on RDBMS scaling (replication, sharding), NoSQL database types, and the four specific caching strategies (cache-aside, write-through, write-behind, refresh-ahead) — those Concepts build directly on "durable source of truth" and "faster, disposable copy" rather than re-explaining what a database or a cache is for.

---

## P4. Latency, throughput, and scaling at a glance

Once a system handles real traffic, two everyday complaints show up, and they're not the same: "this is slow" and "this can't keep up." Telling those apart — and knowing the two basic ways to add capacity — is worth doing in plain language before Lesson 3 reframes both for LLM-serving traffic.

| Term | Full definition | Why it matters |
|---|---|---|
| **Latency** | In everyday terms: how long one single thing takes to happen — the delay between asking for something and getting it. This is the "it feels slow" complaint: a single request taking a long time to come back, regardless of how many other requests are happening at the same time. | Latency is a per-request experience — a system can have excellent latency for the one request you're watching while quietly struggling under load elsewhere, which is exactly why throughput (below) is a separate idea, not a rephrasing of the same one. |
| **Throughput** | In everyday terms: how much work gets done in a given stretch of time — the "can this system actually handle the volume being thrown at it" complaint. A system with low throughput isn't necessarily slow for any one user; it simply can't process enough requests per second to keep up with how many are arriving. | Throughput is what actually determines whether a system falls over under real traffic, independent of how fast any single request feels — a system can be fast per-request and still collapse if it can't sustain enough requests per second. |
| **Vertical scaling** | Handling more load by making a single machine bigger or more powerful — more CPU, more memory, a faster disk — rather than adding more machines. It's the simpler of the two levers, but it has a hard ceiling: there's a biggest machine you can actually buy or rent. | Vertical scaling is the first, easiest lever to reach for, which is exactly why knowing its ceiling matters — it's the lever that eventually forces the move to horizontal scaling. |
| **Horizontal scaling** | Handling more load by adding more machines that each run a copy of the same thing, and spreading the work across all of them, rather than making any one machine bigger. It has no single hard ceiling the way vertical scaling does, but it requires something in front of those machines to actually divide the work between them. | This is the lever nearly every pattern in Lessons 3-7 (replication, sharding, load balancing) is a more detailed way of actually doing — "add more machines" is the plain-language version of what those later Concepts implement precisely. |

**Why this still matters for later lessons:** P4's everyday latency/throughput/scaling vocabulary gives you an early, plain-language pass at these ideas before Lesson 3's Concept 1 gives them the fuller, AI-specific treatment — time-to-first-token, inter-token latency, token-generation throughput, and why "scalable" means something subtly different for an LLM-serving app than a CRUD app. Lesson 3 does redefine these terms rather than skipping past them, but meeting the plain-language versions here makes that fuller treatment land as a refinement, not entirely new material.

---

## Summary

| Sub-topic | One-line takeaway |
|---|---|
| P1 — Client/server & request/response | Every network interaction in this repo reduces to a client asking and a server answering, in one repeatable request/response cycle — the unit Lesson 4's load balancers and reverse proxies route. |
| P2 — APIs and protocols | An API is a software contract; HTTP is the protocol nearly everything here runs on, with requests carrying a method/headers/body and responses carrying a status code/headers/body. |
| P3 — Databases and caches | A database is durable storage and the source of truth; a cache is a faster, disposable copy of it — losing a cache is fine, losing a database is not. |
| P4 — Latency, throughput, scaling | Latency is "how long one thing takes," throughput is "how much gets done per unit time," and the two basic levers for more capacity are making one machine bigger (vertical) or adding more machines (horizontal). |

**Next:** Checkpoint 2, then Lesson 3 — scalability and availability, where the full-depth teaching begins.
