# Lesson 7: Application Architecture and Security

**Time:** 75-90 minutes
**Tool(s):** Conceptual (no single verified CLI) — a real service-registry/health-check config, a real least-privilege IAM-style policy document, a real at-rest-encryption config, and a worked back-of-envelope estimation example instead

## Learning Objectives

By the end of this lesson, you will:

- Be able to distinguish a monolith from a microservices architecture, state the single responsibility principle, and compute — using Lesson 3's own series/parallel availability formulas — why decomposing a system into more independently-deployable services doesn't automatically make it more available, and what it actually costs to make it so
- Be able to define service discovery, name the concrete tools that provide it (Consul, etcd, Zookeeper), and compute how a health-check interval and failure threshold together bound how long a dead service instance keeps receiving traffic
- Be able to state, in full, what encryption in transit, encryption at rest, input sanitization, and least privilege each actually do, and explain exactly why this Concept is the direct prerequisite this repo names for Lesson 8's F1 (prompt injection) and F3 (credential handling for agents with tool access) — without this lesson re-teaching either
- Be able to carry out a complete back-of-envelope estimate — stating assumptions, decomposing the question, computing step by step, and sanity-checking the order of magnitude — and name why this is "taught once here" rather than re-derived in every capstone's own Step 2
- Be able to point to exactly which capstones (#12 multi-agent customer support, #9 RAG/contextual retrieval, #15 LLM API gateway, #10 LLM inference serving, #13 autonomous coding agent) each Concept in this lesson overlays onto, and which pairings are this lesson's own reasoned inference rather than a documented one-to-one claim

---

## Concept 1: Monolith vs. Microservices, Single Responsibility

### Why?

As an AI product grows from one model call into retrieval, several specialist models, a validator pass, and tool execution, it faces a question a single-model chatbot never had: does all that logic live in one deployable process, or split across several — and along what lines? Cramming everything into one process makes a single bug's **blast radius** — the actual scope of systems, data, or users a single failure, bug, or compromised credential can reach, as distinct from what it could theoretically reach unconstrained — the whole system. Splitting without a reason adds operational overhead for no benefit. This Concept names the two shapes and the rule for deciding where the lines go.

### What?

A **monolith** is an application built and deployed as a single, unified unit — one codebase, one running process (or replicated copies of it), where every piece of functionality (handling a request, talking to a database, calling a model) runs inside that same process and deploys as one artifact, every time. **Microservices** is an architectural style that splits an application into small, independently deployable services, each in its own process, communicating over a network (commonly the RPC/REST shapes Lesson 6's Concept 4 already defined), each deployable, scaled, and restarted on its own schedule without redeploying anything else.

The **single responsibility principle (SRP)** decides where those lines go: a component should have one, and only one, reason to change — responsible for one well-defined piece of behavior, not several unrelated ones bundled together for convenience. SRP is why "split into microservices" isn't the same question as "split into *how many*" — the right number and shape of services falls out of identifying distinct responsibilities, not picking an arbitrary piece count.

### How?

**Worked example — decomposing one responsibility at a time, then paying for it in Lesson 3's availability math.** Take a single-model customer-support chatbot built as one monolith: one process receives the message, builds the prompt, calls the model, and returns the response — one responsibility in one deployable unit, measured at 99.9% availability (Lesson 3 Concept 3's own single-component figure).

Now decompose that product the way capstone #12 describes an actual multi-agent customer-support architecture: a **supervisor** service that routes a request to the right specialist, one or more **specialist** services (each a distinct, narrowly-scoped model/role — e.g. billing, returns), and a separate **validator** service that checks a specialist's proposed response before it reaches the customer ("a supervisor over a 'constellation' of specialist models... also described elsewhere as a planner/executor/validator split," teaching "validator/guardrail agents as a distinct role from the agent that takes the action"). Three services, three responsibilities — SRP applied directly: the supervisor routes, the specialist generates a candidate answer, the validator checks it.

Assume each of the three new services, deployed independently, is just as reliable as the original monolith: 99.9% available. Since a request must pass through all three in sequence, Lesson 3 Concept 3's series-availability formula applies directly:

```
combined = 0.999 × 0.999 × 0.999 = 0.997003   →   99.7003% available
```

That's **≈26.3 hours/year of downtime** (0.002997 × 525,600 min/year ≈ 1,575 min ≈ 26.3 hours) — roughly **3x worse** than the monolith's 99.9% (~8.77 hours/year, Lesson 3's "nines" table), even though every piece is exactly as reliable as what it replaced. Decomposing into more services chained in series doesn't automatically buy more availability — per Lesson 3's math, it does the opposite, unless redundancy compensates.

Adding redundancy — an active-active pair behind each service, Lesson 3 Concept 3's parallel-availability pattern — brings each service's availability to 99.9999% (`1 - (0.001 × 0.001)`, Lesson 3's own result for a redundant pair of 99.9% components). Chaining three such redundant pairs in series:

```
combined = 0.999999 × 0.999999 × 0.999999 ≈ 0.999997   →   99.9997% available
```

≈1.6 minutes/year of downtime — far better than the monolith's 8.77 hours/year, but at the cost of running **six total replicas** (two per service × three services) instead of the monolith's one deployable unit. That six-fold compute/ops footprint, not the decomposition itself, is what single-responsibility decomposition actually buys you here: independent scaling, independent deployment, and a validator that can be redeployed or rolled back without touching the specialist or the supervisor at all — real benefits, but ones that cost real redundancy infrastructure to not also come with a worse availability number than you started with.

**Trade-offs considered:** A monolith is simpler to deploy, reason about, and keep available (one failure domain, not three) and has no network hop between its internal pieces — but a bug anywhere inside it can take down the entire system, and every unrelated piece of functionality has to be redeployed together even when only one small part changed. Microservices give each responsibility its own deployment lifecycle, its own scaling knob (a validator that's cheap to run doesn't need to scale with an expensive specialist model), and a genuinely smaller blast radius per service when something inside *that* service breaks — but, as the arithmetic above shows directly, decomposition without added redundancy makes the combined system less available, not more, and every new service boundary is a new network call that can itself fail, time out, or need discovering (Concept 2, next). Neither shape is simply "the more modern one" — SRP is the test for whether a split is earning its operational cost, not a mandate to split everything.

**Case-study pointer:** capstone #12 (`solutions/multi-agent-customer-support`) is this Concept's primary overlay — its supervisor/specialist/validator split is a direct, named instance of single-responsibility service decomposition. Its own Step 5 confirms this Concept's worked example directly, numbers and all, rather than only plausibly matching it: *"Lesson 7's own Concept 1 worked example, confirmed there and in Checkpoint 7's own Question 1, computes exactly this capstone's own three-service chain: a supervisor, a specialist, and a validator, each independently 99.9% available, chained in series, combine to 99.7003% available (≈26.3 hours/year downtime) — worse than a single 99.9% monolith, not better — unless each service is also made redundant (an active-active pair per service, 99.9999% each), which brings the chain to ≈99.9997% available (≈1.6 minutes/year) at the cost of six total replicas instead of one."* Every number in that quote is identical to this Concept's own derivation above, reused directly by the capstone rather than recomputed. Capstone #9 (`solutions/rag-contextual-retrieval`) is this Concept's contrast case on the *other* side of the comparison: Anthropic's Contextual Retrieval technique runs as a pipeline of distinct stages — chunking, context-generation, embedding/indexing, retrieval, reranking — each with its own latency and scaling profile (context-generation and embedding happen once, offline, at indexing time; retrieval and reranking happen online, per query), which is itself a real single-responsibility argument for decomposing *that* pipeline into separate services, even though it isn't itself described using the word "microservices" — this pairing is this lesson's own reasoned inference, not a documented claim.

**Source(s) and further reading:**

- `system-design-primer`'s "Microservices" section (under its "Application layer" heading) — the classic, non-AI framing this Concept curates from; confirmed directly against the live document for this lesson rather than cited from memory
- Lesson 3 (`lesson-3-scalability-and-availability.md`), Concept 3 — the series/parallel availability formulas and the 99.9%-component "nines" figure this Concept's worked example applies directly rather than re-deriving
- Lesson 6 (`lesson-6-async-and-communication.md`), Concept 4 — the RPC/REST calling shapes referenced above as how independently-deployed services actually talk to each other
- `solutions/multi-agent-customer-support/README.md` (capstone #12) — whose own Step 5 confirms this Concept's series/parallel-availability numbers directly, quoted above

---

## Concept 2: Service Discovery (Consul/etcd/Zookeeper)

### Why?

Concept 1's microservices (and Lesson 3's Concept 3 redundant replicas of any one of them) only deliver their availability and scaling benefits if a caller can actually find a currently-healthy instance to talk to — and in any real deployment, instances get added, removed, rescheduled onto different machines, and occasionally just die, all while keeping their own network address rather than a fixed one. Hardcoding an IP address for "the validator service" is exactly as fragile as it sounds the moment there's more than one instance of it, or the first time one gets restarted onto new infrastructure. Something has to track, continuously, which instances of a service actually exist right now and whether they're able to serve traffic.

### What?

**Service discovery** is the mechanism by which services in a distributed system find each other's current network location, without any caller needing to hardcode an address — typically backed by a **service registry** (the data store half: a record of which instances of which services currently exist, and where). A service instance **registers** itself with the registry on startup (or is registered on its behalf by an orchestrator) and is **deregistered** when it shuts down or is detected as unhealthy.

Staying registered correctly requires a **health check** — a periodic probe (commonly a lightweight HTTP request to a dedicated endpoint, e.g. `GET /health`, that returns success only if the instance is actually able to serve real traffic, not just that its process is running) used to decide whether an instance stays in the pool of candidates a caller can be routed to, or gets pulled out of rotation.

Two concrete shapes this takes in practice:

- **Client-side discovery** — the calling service queries the registry directly to get a list of currently-healthy instances, then picks one itself (often using a load-balancing strategy, Lesson 4's Concept 3) — the caller does the discovery work.
- **Server-side discovery** — the caller sends its request to a single, fixed address (a load balancer or gateway), and that intermediary queries the registry and does the routing on the caller's behalf — the caller never talks to the registry at all, which is exactly the shape Lesson 4's Concept 4 already described a reverse proxy/load balancer playing.

**Consul**, **etcd**, and **Zookeeper** are three real, named systems that implement this pattern — per `system-design-primer`'s own words, confirmed directly against its live text: "Consul, Etcd, and Zookeeper can help services find each other by keeping track of registered names, addresses, and ports." Briefly, by name:

- **Consul** — HashiCorp's service-networking tool, combining a service registry with built-in health checking and a DNS/HTTP interface for looking up healthy instances.
- **etcd** — a distributed, strongly-consistent key-value store built on the **Raft consensus algorithm** (a protocol by which a cluster of nodes agrees on a single, consistent sequence of state changes even if some nodes fail), used internally by Kubernetes itself to track, among other cluster state, which pods/service endpoints currently exist.
- **Zookeeper** — an older Apache coordination service providing distributed locks, configuration storage, and group membership — the mechanism, for instance, Kafka brokers historically used to discover each other and agree on cluster leadership.

### How?

**Worked example — a service-registry entry with a health check, and how long a dead instance keeps receiving traffic.** Here's an illustrative, Consul-style service-registration JSON for one replica of an inference-server pool (the kind of GPU replica pool capstone #10's own Step 2 sizes at roughly 24 GPUs for its target load):

```json
{
  "ID": "inference-replica-07",
  "Name": "llm-inference-backend",
  "Address": "10.0.4.23",
  "Port": 8080,
  "Check": {
    "HTTP": "http://10.0.4.23:8080/health",
    "Interval": "10s",
    "Timeout": "2s",
    "DeregisterCriticalServiceAfter": "1m"
  }
}
```

`ID` uniquely identifies this one instance (distinct from `Name`, which identifies the *service* — many instances share one `Name`); `Check.Interval` is how often the registry probes `Check.HTTP`; `Check.Timeout` is how long a single probe is allowed to take before it's counted as a failure; `DeregisterCriticalServiceAfter` is how long an instance can stay marked unhealthy before it's removed from the registry outright rather than just skipped for routing.

A health check doesn't fail an instance out of rotation on a single missed probe (one slow response could just be a transient blip) — it typically requires a **failure threshold**: a number of *consecutive* failed probes before the instance is actually marked unhealthy and pulled from the pool of candidates a caller (or the load balancer doing server-side discovery on the caller's behalf) can be routed to. Say this registry requires 3 consecutive failures:

```
time_to_detect_and_remove = check_interval × consecutive_failures_required
                           = 10s × 3
                           = 30 seconds
```

For up to 30 seconds after an instance actually dies, it can still be selected and sent live traffic — the service-discovery analog of Lesson 4's Concept 1 DNS-TTL worst-case exposure (a resolver sending traffic to a dead region until its cached answer expires): here, the "staleness window" isn't a DNS cache, it's the health check's own interval × threshold, and it's a direct, tunable trade — a shorter interval or lower threshold detects failure faster but runs more frequent health-check traffic against every instance and risks flapping an instance out over one slow-but-fine response.

**Trade-offs considered:** Client-side discovery avoids a single intermediary becoming a new bottleneck or point of failure, but pushes real complexity (querying the registry, load-balancing logic, handling a registry that's itself temporarily unreachable) into every single service that needs to call another one. Server-side discovery centralizes that complexity into one component (the gateway/load balancer), which is simpler for every individual service to rely on, but makes that intermediary's own availability matter disproportionately — exactly the concern capstone #15's own Step 1 raises about itself. A short health-check interval with a low failure threshold detects a dead instance fast but generates more health-check load and risks false positives on a transient blip; a longer interval/higher threshold is gentler on the system but widens the window during which a caller can still be routed to something that's actually dead.

**Case-study pointer:** capstone #15 (`solutions/llm-api-gateway`) is the strongest already-written overlay, with one caveat: its README describes the gateway tracking "each provider's rolling error rate and latency over a short window" and marking a provider "unhealthy" once its error rate or p99 latency (the 99th-percentile latency — 99% of requests are faster than this value; defined in full in Lesson 9's Concept 2) crosses a threshold, then routing subsequent requests elsewhere — architecturally the same registry-plus-health-check-plus-dynamic-routing shape this Concept defines, functioning as server-side discovery of which upstream providers are currently healthy. The README itself never uses the words "service discovery," "Consul," "etcd," or "Zookeeper" — this pairing is this lesson's own reasoned architectural mapping onto this Concept's vocabulary, not a claim capstone #15's text makes directly. Capstone #10 (`solutions/llm-inference-serving`) is the sibling case one layer down the stack: its Step 2 sizes a pool of roughly 24 GPU replicas to meet target concurrency, and its Step 5 scheduler has to know, continuously, which replicas currently have free KV-cache blocks — the same "which instances exist and are currently able to take work" problem, one level below the application-layer provider routing capstone #15 demonstrates directly.

**Source(s) and further reading:**

- `system-design-primer`'s "Service Discovery" section (under its "Application layer" heading), including its own naming of Consul, Etcd, and Zookeeper — confirmed directly against the live document for this lesson, not cited from memory
- HashiCorp Consul documentation — service registration and health-check configuration, the real schema this Concept's worked example is modeled on
- etcd documentation, and the Raft consensus paper (Ongaro & Ousterhout, *"In Search of an Understandable Consensus Algorithm,"* 2014) — the consensus mechanism underneath etcd's own consistency guarantees
- Apache Zookeeper documentation — the coordination-service pattern, including its historical use for Kafka broker discovery
- Lesson 4 (`lesson-4-network-and-delivery.md`), Concepts 3-4 — the load-balancing and reverse-proxy mechanics server-side discovery builds directly on top of
- `solutions/llm-api-gateway/README.md` (capstone #15) and `solutions/llm-inference-serving/README.md` (capstone #10) — this Concept's two case-study overlays

---

## Concept 3: Core Security — Encryption, Input Sanitization, Least Privilege

### Why?

Every concept so far has been about getting a request to the right, healthy place efficiently. None of it asks the question that matters the moment any of these services touch real user data, a real credential, or a real LLM tool call: can this data be read or tampered with in flight or at rest, can this input be trusted at face value, and does this service (or agent, or tool) have more access than it actually needs? This Concept is explicitly the foundation for two Concepts in Lesson 8 — what follows refreshes only what's needed to set that foundation, not Lesson 8's own content: **F1 (prompt injection)** — which needs the input-sanitization principle below as its starting point, extended to the fact that an LLM's "input" includes retrieved documents and tool outputs, not just the end user's literal message — and **F3 (credential and secret handling for agents with tool access)** — which needs the least-privilege principle below as its starting point, applied specifically to scoping each tool's own credential.

### What?

Per `system-design-primer`'s own "Security" section, confirmed directly against its live text, four of its bulleted security practices are the ones this Concept teaches in full: "Encrypt in transit and at rest," "Sanitize all user inputs...to prevent XSS and SQL injection," "Use parameterized queries to prevent SQL injection," and "Use the principle of least privilege."

**Encryption in transit** is encrypting data while it's moving across a network, so anyone who intercepts the traffic between two endpoints sees only ciphertext, not the actual content. **TLS (Transport Layer Security)** is the standard mechanism for this — a protocol in which the two endpoints of a connection first exchange and verify certificates to authenticate each other and agree on encryption keys (the "handshake"), after which all data sent over that connection is encrypted. TLS is defined here in full for the first time, though Lesson 6's Concept 3 already showed its real handshake cost in a TCP context (one extra round-trip time on top of the TCP handshake itself) — that cost figure is referenced here rather than re-derived. In a microservices architecture (Concept 1), this extends to **mutual TLS (mTLS)**: both sides of an internal service-to-service connection present and verify a certificate, not just the client verifying the server the way a normal browser-to-website TLS connection works — so one compromised service inside the network can't simply pretend to be another.

**Encryption at rest** is encrypting data while it's stored — on a database's disk, in a backup, in object storage — so that someone who gains access to the storage medium itself (a stolen disk, a misconfigured storage bucket, a cloud provider's own internal access) still can't read the content without the decryption key. A concrete, real example: Amazon S3's server-side encryption configuration, applied at the bucket level:

```json
{
  "ServerSideEncryptionConfiguration": {
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }
}
```

`SSEAlgorithm: AES256` names the actual cipher (**AES**, the Advanced Encryption Standard, operating here with a 256-bit key) applied to every object written to this bucket by default — encryption in transit and encryption at rest are genuinely separate protections, addressing separate threat models: TLS protects data while it's moving between two points; this config protects the same data once it's sitting still, and neither one substitutes for the other (TLS does nothing for a stolen disk; at-rest encryption does nothing for traffic sniffed mid-network).

**Input sanitization** is checking, filtering, or transforming untrusted input before it's used, so it can't be interpreted as something other than inert data by whatever processes it next. The classic example `system-design-primer` names directly is **SQL injection** — untrusted input containing SQL syntax that, if concatenated directly into a query string, gets executed as part of the query itself rather than treated as a literal value — mitigated by **parameterized queries** (passing user input to the database as a separate, explicitly-typed parameter, never concatenated into the query text, so the database engine can never confuse "data" for "code"). The AI-specific extension of this principle — which Lesson 8's F1 covers in depth, not repeated here — is that an LLM's "input" isn't only the end user's literal typed message: it's also every retrieved RAG chunk and every tool-call result the model reads (Lesson 1's Concept A1, "prompt as attack surface"), none of which has gone through anything resembling a SQL parameter boundary. The general principle — untrusted input needs to be checked before it's trusted — is identical; the mechanism for enforcing that boundary on natural-language input is genuinely different from a parameterized query, which is why it gets its own full Concept in Lesson 8 rather than a one-line corollary here.

**Least privilege** is the principle of granting any identity, process, service, or credential only the minimum set of permissions it actually needs to do its job — and no more. A credential scoped to least privilege can still cause damage if it's leaked or misused, but only within the narrow boundary it was actually granted; a broad, convenient "just give it admin" credential turns the exact same leak into a catastrophically larger incident. The AI-specific extension — Lesson 8's F3, not repeated here — is applying this per-tool: an agent that can call five different tools shouldn't have one shared, maximally-permissive credential behind all five; each tool's own access should be scoped to only what that specific tool needs.

### How?

**Worked example — quantifying the blast-radius reduction least privilege actually buys.** Say an organization runs 50 separate S3 buckets across its products, and one of them (`support-kb-bucket`) holds the document corpus a customer-support RAG agent's retrieval tool (Lesson 1's Concept C2) needs read access to. Here is that tool's credential, scoped to least privilege, as a real AWS IAM policy document:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DocumentRetrievalToolReadOnly",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::support-kb-bucket/*"
    }
  ]
}
```

Compare that against the broad, "simpler to set up" alternative — one shared credential with organization-wide access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": "s3:*", "Resource": "*" }
  ]
}
```

If either credential is ever leaked — for instance, via a successful prompt-injection attack (Lesson 8's F1) that coerces the agent into revealing or misusing its own tool's stored credential (Lesson 8's F3) — the least-privilege-scoped credential exposes exactly one bucket, read-only. The broad credential exposes all 50 buckets, with full read/write/delete (`s3:*`) on every object in every one of them:

```
blast_radius_ratio = broad_buckets_exposed / scoped_buckets_exposed
                    = 50 / 1
                    = 50x
```

The identical leak event is a 50x larger incident purely because of which credential was behind the tool — nothing about the leak itself changed; only the ceiling on what it could reach did.

**Trade-offs considered:** Least privilege adds real, ongoing operational cost — every tool, every service, every credential needs its own deliberately scoped policy, which is more things to define, audit, and keep in sync as a system's tools and services grow (Concept 1's single-responsibility split multiplies this: more services means more individual credentials to scope correctly, not fewer). A single broad credential is far simpler to set up and never blocks a legitimate new use case with a permissions error — at the direct cost of the 50x larger blast radius shown above the moment anything goes wrong. Encryption in transit and at rest both add real, if typically small, computational overhead (Lesson 6's Concept 3 already quantified TLS's handshake cost) in exchange for protection against two genuinely distinct threat models — skipping either one doesn't just halve the protection, it leaves one entire threat model (a sniffed connection, or a stolen disk) completely uncovered.

**Case-study pointer:** capstone #15 (`solutions/llm-api-gateway`) is the primary already-written anchor for the least-privilege half of this Concept: a gateway proxying requests across multiple LLM providers structurally needs a separate stored credential per upstream provider — the README's Step 1 scopes the gateway's job as "a single API surface that proxies requests across multiple LLM providers," implying per-provider credential separation, though the README doesn't spell out credential storage in detail; this inference is this lesson's own reasoned extension, not a documented detail of capstone #15's own text. Its already-shown rate-limit config JSON (a token budget per `api_key` / `team` / `model`, that capstone's Step 4) is a confirmed, directly-citable example of the same least-privilege-style scoping instinct — budget and capability, not just identity — applied per key rather than org-wide. Capstone #13 (`solutions/autonomous-coding-agent`, Devin-style) is the sibling case at the tool level: it grants "sandboxed shell/editor/browser access" — each of those three distinct tools is exactly the kind of access that should be scoped to least privilege individually (a browser tool has no legitimate need for filesystem-delete access, for instance), not granted as one undifferentiated "full dev environment" credential. Its own Step 5 quotes this Concept's reasoning back verbatim, then confirms it with a real, three-way-scoped tool-credential config rather than leaving it as an inference: *"Lesson 7's Concept 3 states directly: 'Capstone #13... each of those three distinct tools (shell, editor, browser) is exactly the kind of access that should be scoped to least privilege individually... rather than granted as one undifferentiated 'full dev environment' credential.' This capstone's own design confirms that inference directly, rather than overriding it — three separate scoped tool configurations, not one"* — concretely, `shell_tool` and `editor_tool` are each scoped to read-write access on the workspace only, with no network access, and `browser_tool` is scoped to an internet allowlist with *no* filesystem access and barred from shell execution, so "the `browser_tool` has no legitimate need for filesystem-delete access" is no longer this lesson's hypothetical — it's a real config field (`"browser_tool": {"filesystem": "none", ...}`) enforcing exactly that.

**Source(s) and further reading:**

- `system-design-primer`'s "Security" section — confirmed directly against the live document for this lesson: "Encrypt in transit and at rest," "Sanitize all user inputs...to prevent XSS and SQL injection," "Use parameterized queries to prevent SQL injection," "Use the principle of least privilege" — the exact four practices this Concept teaches in full
- Lesson 6 (`lesson-6-async-and-communication.md`), Concept 3 — the original full definition of TLS and its handshake cost, referenced rather than re-derived here
- Lesson 1 (`lesson-1-ai-fundamentals-refresher.md`), Concept A1 — "prompt as attack surface," the original statement of why an LLM's input includes retrieved/tool content, extended (not re-derived) here
- AWS Identity and Access Management (IAM) documentation — the real JSON policy-document schema used in this Concept's worked example
- AWS S3 documentation on default bucket encryption — the real `ServerSideEncryptionConfiguration`/`SSEAlgorithm` schema used above
- `solutions/llm-api-gateway/README.md` (capstone #15) — the per-key/team/model scoping precedent this Concept's case-study pointer builds on
- `solutions/autonomous-coding-agent/README.md` (capstone #13) — whose own Step 5 confirms this Concept's per-tool least-privilege scoping directly, quoted above

---

## Concept 4: Back-of-Envelope Estimation Technique + Latency Numbers

### Why?

Every capstone follows a 6-step method, and Step 2 of every single one of them is "back-of-envelope constraints" — a quick numeric estimate of scale (QPS, data volume, tokens/sec, $/month) carried forward into Step 4's and Step 5's trade-offs. Capstone #10's Step 2 and capstone #15's Step 2 (cited below) each *do* this — but neither one stops to teach the actual technique being used. This Concept is that teaching, done once, explicitly, so it doesn't have to be re-derived from scratch in every capstone.

### What?

A **back-of-envelope estimate** is a deliberately quick, approximate numeric calculation — meant to be right within an order of magnitude, not exactly precise — built from a small number of known or reasonably-assumed reference quantities and simple arithmetic, used to catch a design mistake (a plan that needs 600 GPUs when the team assumed 6) or to validate a plan's basic feasibility, before investing in real benchmarking or production measurement. The method, as it actually gets applied throughout the capstones, has five repeatable steps:

1. **State your assumptions explicitly.** Never silently assume a number — write down every input quantity you're treating as given (even an illustrative one), so anyone checking the estimate later knows exactly what it depends on.
2. **Decompose into independently-estimable quantities.** Don't try to guess the final answer directly — break it into smaller numbers you can each reason about on their own (e.g. "total tokens per day" splits into "users × messages per user × tokens per message," not one guess).
3. **Compute step by step, carrying units.** Multiply/divide the decomposed quantities together, writing the units at every step (tokens/day, not just a bare number) — carrying units is what catches a dimensional-analysis mistake before it becomes a wrong conclusion.
4. **Sanity-check the order of magnitude against a known reference point.** Compare the result against something already known to be true (an existing system's real numbers, a number computed earlier in this course) — the estimate doesn't need to be exact, but it does need to be in a plausible range.
5. **Name the assumption the answer is most sensitive to.** State explicitly which input, if it turned out to be wrong, would change the final answer the most — that's the number worth actually verifying first, before trusting the rest of the estimate.

Step 3 above depends on having a set of real reference numbers on hand — the actual point of a **"latency numbers every programmer should know"**-style table (`system-design-primer`'s own named Appendix section, confirmed directly against its live text), extended here with the AI-serving-specific numbers this repo has already established in earlier lessons and capstones:

| Reference quantity | Approximate value | Source |
|---|---|---|
| L1 cache reference | ~0.5 ns | `system-design-primer` Appendix (classic, non-AI) |
| Main memory reference | ~100 ns | `system-design-primer` Appendix (classic, non-AI) |
| Round trip within the same datacenter | ~500 µs | `system-design-primer` Appendix (classic, non-AI) |
| Read 1 MB sequentially from SSD | ~1 ms | `system-design-primer` Appendix (classic, non-AI) |
| HDD seek | ~10 ms | `system-design-primer` Appendix (classic, non-AI) |
| Packet round trip, California ↔ Netherlands | ~150 ms | `system-design-primer` Appendix (classic, non-AI) |
| TCP + TLS 1.3 handshake, at a 40ms RTT | ~80 ms (paid once per connection) | Lesson 6 Concept 3's worked example |
| Tokenizing a ~2,000-token request (BPE) | ~1-2 ms | Capstone #15 (`solutions/llm-api-gateway`) Step 2 |
| LLM gateway's own added-latency target | <20 ms | Capstone #15 Step 1 |
| p50 / p99 time-to-first-token (TTFT) | <200ms / <1.5s | Capstone #10 (`solutions/llm-inference-serving`) Step 1 |
| p50 / p99 inter-token latency | <40ms / <120ms per token | Capstone #10 Step 1 |

The first six rows are the classic, non-AI reference points — kept here deliberately because an AI-serving system still runs on top of all of this physical infrastructure, and a back-of-envelope estimate that only knows AI-specific numbers will badly misjudge anything that bottlenecks on plain network or disk latency. The AI-serving rows are each a number already established and verified elsewhere in this course, not a new unverified figure — this table is a convenience index, not a new source. (A fuller, AI-specific version of this table — context-window sizes, $/1M-token rates by provider tier, typical vector-search latency — is `appendix/token-and-latency-numbers.md`'s own job, extending this exact Concept with AI-specific figures.)

### How?

**Worked example — following the five-step method on a fresh scenario.** A team is scoping a new RAG customer-support chatbot (capstone #9's territory) and wants a rough daily cost and peak-throughput estimate before committing to an architecture.

**Step 1 — state assumptions explicitly:** 50,000 active users; each sends an average of 10 messages/day; each message's prompt (including retrieved context) averages 1,500 input tokens; each response averages 300 output tokens; the model's pricing is an illustrative $3/1M input tokens and $15/1M output tokens (not any single named provider's current, literal rate — an illustrative order-of-magnitude figure for a mid-tier model, stated as an assumption per Step 1 of the method itself); 40% of a day's total traffic lands inside a 4-hour peak window.

**Step 2 — decompose:**
```
daily_messages        = users × messages_per_user_per_day
daily_input_tokens    = daily_messages × input_tokens_per_message
daily_output_tokens   = daily_messages × output_tokens_per_message
daily_cost            = (daily_input_tokens / 1,000,000) × input_price
                      + (daily_output_tokens / 1,000,000) × output_price
peak_tokens           = daily_messages × peak_fraction × (input_tokens_per_message + output_tokens_per_message)
required_throughput   = peak_tokens / peak_window_seconds
```

**Step 3 — compute step by step, carrying units:**
```
daily_messages      = 50,000 users × 10 messages/user/day = 500,000 messages/day

daily_input_tokens  = 500,000 messages/day × 1,500 input tokens/message
                    = 750,000,000 input tokens/day   (750M tokens/day)

daily_output_tokens = 500,000 messages/day × 300 output tokens/message
                    = 150,000,000 output tokens/day  (150M tokens/day)

daily_cost = (750M / 1M) × $3  +  (150M / 1M) × $15
           = 750 × $3  +  150 × $15
           = $2,250  +  $2,250
           = $4,500/day   (≈ $135,000/month at 30 days)

peak_messages = 500,000 messages/day × 0.40 = 200,000 messages (in the 4-hour peak window)
peak_tokens   = 200,000 messages × (1,500 + 300) tokens/message = 360,000,000 tokens

peak_window_seconds = 4 hours × 3,600 sec/hour = 14,400 seconds

required_throughput = 360,000,000 tokens / 14,400 seconds = 25,000 tokens/sec  (aggregate, across the whole fleet)
```

**Step 4 — sanity-check the order of magnitude.** Cross-referencing against Lesson 3's Concept 1 batch-size table (itself an illustrative, not production-measured, hypothetical: batch size 32 → 400 tokens/sec aggregate on one GPU-equivalent unit), a required 25,000 tokens/sec implies roughly `25,000 / 400 ≈ 63` GPU-equivalent units running at that batch size — in the same broad range (tens, not hundreds or thousands) as capstone #10's own Step 2 estimate of ~24 GPUs for a comparable-order-of-magnitude concurrency target. The two estimates aren't meant to match exactly (they're sized for different assumptions and different model/hardware configurations) — the point of this sanity check is confirming "a few dozen GPUs" is the right order of magnitude for this scenario, not "6" and not "6,000," either of which would mean a real mistake happened somewhere in Step 3's arithmetic.

**Step 5 — name the most sensitive assumption.** The $4,500/day cost figure splits exactly evenly between its input-token half ($2,250) and output-token half ($2,250) at these particular assumptions — but the input-token half is the one most likely to move in practice, because it's driven by how much retrieved context a RAG system injects per query (Lesson 1's Concept C3/C4), a design choice, not a fixed constant the way a typical response length more often is. A RAG system that ends up retrieving and injecting twice as much context per query (3,000 input tokens instead of 1,500) roughly doubles the input-token half of the daily cost directly ($2,250 → $4,500), pushing the daily total from $4,500 to $6,750 — a 50% total increase — with no change to anything else in the estimate. That's the number worth actually measuring in a prototype before trusting the rest of this estimate's conclusions.

**Trade-offs considered:** A back-of-envelope estimate trades precision for speed — it's deliberately not a substitute for real load-testing or production telemetry (Step 6 of every capstone's own 6-step method) before committing real infrastructure spend, but it's fast enough to run during a design discussion, which real benchmarking never is. Skipping it entirely and going straight to "let's just build it and see" risks discovering an order-of-magnitude mistake (needing 60 GPUs, not 6) only after real money and engineering time have already been spent — exactly the failure mode this technique exists to catch early and cheaply.

**Case-study pointer:** capstone #10 (`solutions/llm-inference-serving`) Step 2 and capstone #15 (`solutions/llm-api-gateway`) Step 2 are both confirmed, already-written applications of exactly this technique: capstone #10's Step 2 decomposes KV-cache-bytes-per-token into per-layer, per-token arithmetic to arrive at a GPU count (the same decompose-then-compute shape as Steps 2-3 above); capstone #15's Step 2 runs the request-based-vs-token-based accounting comparison (the 500-request/1,000,000-token-budget example) as its own sanity check on why the gateway's whole design exists. Neither capstone's own README stops to name the five-step method explicitly the way this Concept does — this Concept is that naming, done once, so it doesn't have to be re-derived from scratch in capstone #9, #12, #13, or any future one.

**Source(s) and further reading:**

- `system-design-primer`'s "Back-of-the-envelope calculations" section (under "How to approach a system design interview question") and its "Latency numbers every programmer should know" section (under "Appendix") — both confirmed directly against the live document for this lesson, not cited from memory; the latter itself credits (via its own further-reading links) Jeff Dean's "Designs, Lessons, and Advice from Building Large Distributed Systems" talk and community-maintained reproductions (gists by GitHub users jboner and hellerbarde)
- `solutions/llm-inference-serving/README.md` (capstone #10), Step 2 — the KV-cache-bytes-per-token decomposition this Concept's method names explicitly
- `solutions/llm-api-gateway/README.md` (capstone #15), Steps 1-2 — the token-vs-request-accounting worked example this Concept's method names explicitly
- Lesson 3 (`lesson-3-scalability-and-availability.md`), Concept 1 — the illustrative batch-size/throughput table used as this Concept's Step 4 sanity-check reference

---

## Hands-On Walkthrough

There's no single CLI for "application architecture and security" in general — work through this real config, this real policy document, and this back-of-envelope exercise yourself, by hand or with the runnable Python snippet below.

**1. A service-registry entry and a least-privilege policy for the same service — linked only by naming convention.** Here's a service registration for one replica of a RAG retrieval tool's backing service, paired with the least-privilege IAM policy (Concept 3) scoping exactly what that service's own credential can touch:

```json
{
  "ID": "retrieval-tool-replica-03",
  "Name": "support-kb-retrieval-service",
  "Address": "10.0.6.11",
  "Port": 8081,
  "Check": {
    "HTTP": "http://10.0.6.11:8081/health",
    "Interval": "10s",
    "Timeout": "2s",
    "DeregisterCriticalServiceAfter": "1m"
  }
}
```

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SupportKBRetrievalServiceReadOnly",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::support-kb-bucket/*"
    }
  ]
}
```

Confirm for yourself: nothing in the Consul JSON above — `ID`, `Name`, `Address`, `Port`, `Check` — actually references `support-kb-bucket`, and nothing in the IAM policy references the Consul `Name` or `ID` either. The only thing connecting these two documents is that a human picked correlated, readable names: `support-kb-retrieval-service` (Consul), `SupportKBRetrievalServiceReadOnly` (the IAM `Sid`), and `support-kb-bucket` (the `Resource`) — naming convention and documentation discipline, not a schema-level or mechanical link enforced by either system. Consul has no field for "which IAM policy backs this service," and IAM has no field for "which registered service this policy belongs to." That gap is a real operational risk: nothing stops someone from renaming the bucket or re-scoping the policy without touching the Consul entry (or vice versa), and neither system would catch that drift automatically — a real least-privilege audit has to check this cross-document correlation by hand, precisely because the systems themselves don't enforce it.

**2. Your own health-check failure-detection calculation.** Pick your own `Interval` and your own consecutive-failure threshold (different from the 10s/3-failures example in Concept 2), and compute `time_to_detect_and_remove = check_interval × consecutive_failures_required`. Then halve your interval and recompute — confirm the detection time halves too, and name one operational cost of making that change (per Concept 2's own trade-off).

**3. A runnable Python snippet for both this lesson's calculations.**

```python
import math

def time_to_detect_failure(check_interval_sec: float, consecutive_failures_required: int) -> float:
    """Concept 2: worst-case time a dead service instance can keep receiving
    traffic before a health check pulls it from rotation."""
    return check_interval_sec * consecutive_failures_required


def blast_radius_ratio(broad_resources_exposed: int, scoped_resources_exposed: int) -> float:
    """Concept 3: how many times larger an identical credential leak becomes
    under a broad grant versus a least-privilege-scoped one."""
    return broad_resources_exposed / scoped_resources_exposed


def back_of_envelope_daily_cost(
    users: int,
    messages_per_user_per_day: float,
    input_tokens_per_message: int,
    output_tokens_per_message: int,
    input_price_per_million: float,
    output_price_per_million: float,
) -> dict:
    """Concept 4: Steps 2-3 of the five-step method, computed directly."""
    daily_messages = users * messages_per_user_per_day
    daily_input_tokens = daily_messages * input_tokens_per_message
    daily_output_tokens = daily_messages * output_tokens_per_message
    daily_cost = (daily_input_tokens / 1_000_000) * input_price_per_million \
        + (daily_output_tokens / 1_000_000) * output_price_per_million
    return {
        "daily_messages": daily_messages,
        "daily_input_tokens": daily_input_tokens,
        "daily_output_tokens": daily_output_tokens,
        "daily_cost_usd": daily_cost,
    }


def required_throughput_tokens_per_sec(
    daily_messages: float,
    peak_fraction: float,
    tokens_per_message: int,
    peak_window_hours: float,
) -> float:
    """Concept 4: the peak-throughput half of the same worked example."""
    peak_messages = daily_messages * peak_fraction
    peak_tokens = peak_messages * tokens_per_message
    peak_window_seconds = peak_window_hours * 3600
    return peak_tokens / peak_window_seconds


# Reproduces this lesson's own worked numbers:
print(time_to_detect_failure(10, 3))  # 30.0 seconds
print(blast_radius_ratio(50, 1))      # 50.0x
result = back_of_envelope_daily_cost(50_000, 10, 1_500, 300, 3.0, 15.0)
print(result["daily_cost_usd"])       # 4500.0
print(required_throughput_tokens_per_sec(result["daily_messages"], 0.40, 1_800, 4))  # 25000.0
```

Confirm for yourself: `back_of_envelope_daily_cost`'s return values match Concept 4's own Step 3 arithmetic exactly (750,000,000 / 150,000,000 input/output tokens, $4,500 total), and `required_throughput_tokens_per_sec` reproduces the 25,000 tokens/sec figure when called with `tokens_per_message=1_800` (1,500 input + 300 output combined, matching Concept 4's own `peak_tokens` line) and `peak_window_hours=4`.

---

## Summary

| Concept | One-line takeaway |
|---|---|
| Monolith vs. microservices, single responsibility | SRP decides where service boundaries go, not an arbitrary split count — and per Lesson 3's own series-availability math, decomposing into more services chained in series makes a system *less* available, not more, unless each new service also gets its own redundancy, as capstone #12's supervisor/specialist/validator split illustrates. |
| Service discovery | A service registry plus health checks is what lets a caller find a currently-healthy instance without hardcoding an address — and `check_interval × consecutive_failures_required` bounds how long a dead instance can still receive traffic, the same shape as Lesson 4's DNS-TTL exposure math, applied to capstone #15's provider-health tracking and capstone #10's GPU replica pool. |
| Core security | Encryption in transit (TLS) and at rest protect two genuinely different threat models; input sanitization and least privilege are the direct foundations Lesson 8 names explicitly for F1 (prompt injection) and F3 (credential handling) — and a leaked least-privilege-scoped credential can be a 50x smaller incident than a leaked broad one, for the identical leak event. |
| Back-of-envelope estimation + latency numbers | A five-step method (state assumptions, decompose, compute with units, sanity-check the order of magnitude, name the most sensitive assumption) is the mechanical skill every capstone's own Step 2 already uses without naming it — taught once here, grounded in a latency-numbers table spanning both classic infrastructure and this repo's own AI-serving figures. |

## Key Formulas & Policy/Config Reference

```
Series availability of N newly-decomposed services (no added redundancy):
  combined = A1 × A2 × ... × AN          (see Lesson 3, Concept 3, for the full formula)

Service-discovery failure-detection time:
  time_to_detect_and_remove = check_interval × consecutive_failures_required

Least-privilege blast-radius ratio:
  blast_radius_ratio = resources_exposed_under_broad_grant / resources_exposed_under_scoped_grant

Back-of-envelope method (5 steps):
  1. State assumptions explicitly
  2. Decompose into independently-estimable quantities
  3. Compute step by step, carrying units
  4. Sanity-check the order of magnitude against a known reference point
  5. Name the assumption the answer is most sensitive to
```

```json
// Consul-style service registration + health check, from Concept 2 / Hands-On Walkthrough
{
  "ID": "inference-replica-07",
  "Name": "llm-inference-backend",
  "Address": "10.0.4.23",
  "Port": 8080,
  "Check": {
    "HTTP": "http://10.0.4.23:8080/health",
    "Interval": "10s",
    "Timeout": "2s",
    "DeregisterCriticalServiceAfter": "1m"
  }
}
```

```json
// Least-privilege AWS IAM policy document, from Concept 3 / Hands-On Walkthrough
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DocumentRetrievalToolReadOnly",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::support-kb-bucket/*"
    }
  ]
}
```

```json
// AWS S3 default-bucket-encryption config (encryption at rest), from Concept 3
{
  "ServerSideEncryptionConfiguration": {
    "Rules": [
      { "ApplyServerSideEncryptionByDefault": { "SSEAlgorithm": "AES256" } }
    ]
  }
}
```

**Next:** Checkpoint 7, then Lesson 8 — prompt injection, sandboxing, credential handling for agents with tool access, guardrails, and multi-tenant isolation.
