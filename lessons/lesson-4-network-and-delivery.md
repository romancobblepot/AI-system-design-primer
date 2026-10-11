# Lesson 4: Network and Delivery

**Time:** 75-90 minutes
**Tool(s):** Conceptual (no single verified CLI) — worked numeric examples and real config/payload schemas instead

## Learning Objectives

By the end of this lesson, you will:

- Understand how DNS resolution and routing policies work, and be able to compute the real-world impact of a DNS TTL on failover speed
- Understand the push vs. pull CDN trade-off, and be able to explain specifically why model weights themselves are a poor fit for a CDN
- Be able to distinguish L4 from L7 load balancing, explain what SSL termination trades away, and know when session persistence matters for LLM traffic specifically
- Be able to distinguish a reverse proxy's job from a load balancer's job, and explain why a traditional API gateway's request-based rate limiting breaks down for LLM traffic
- Be able to point to exactly which capstone exercises each of these patterns

---

## Concept 1: DNS

### Why?

Every request starts with a domain name like `api.example.com`, not an IP address — something has to resolve that name to an actual IP before anything else can happen. *Which* IP comes back can itself be a routing decision: for a multi-region AI-serving deployment, DNS is where "which region/replica handles this request" gets decided first, at the coarsest grain, before any other layer in the stack is even involved.

### What?

**DNS (Domain Name System)** is the distributed system that translates human-readable domain names into the IP addresses computers actually use to connect to each other. No single server stores the IP address for every domain on the internet, so the first lookup for a name is handed off hop by hop through a chain of servers — each one knowing only "who to ask next" — until one of them has the actual answer:

1. The client asks a **recursive resolver** (usually run by your ISP, or a public service like 8.8.8.8).
2. The resolver queries a **root server**.
3. The root server points it to a **TLD (top-level domain) server** — e.g. the server responsible for all `.com` domains.
4. The TLD server points it to the domain's own **authoritative name server**, which returns the actual IP address: an **A record**, the DNS record type that maps a name directly to an IPv4 address.

Every DNS record is published with a **TTL (time to live)** — how many seconds a resolver may cache that answer before looking it up again. A short TTL means cached answers go stale and get re-checked quickly; a long TTL means fewer repeat lookups but slower propagation of any change.

Beyond a plain A record, authoritative DNS services support **routing policies** that return a *different* answer depending on context, instead of always returning the same IP:

- **Weighted round robin** — returns different IPs to different queries according to configured weights (e.g. 70% of queries get region A's IP, 30% get region B's). Used for traffic splitting (e.g. a gradual rollout), not true failover.
- **Latency-based routing** — returns whichever registered endpoint has historically had the lowest network latency from the resolver's location.
- **Geolocation-based routing** — returns the endpoint registered as closest to (or designated for) the querying resolver's geographic region, regardless of measured latency.

### How?

**Worked example — TTL and failover speed.** Say `api.example.com` has an A record with a 300-second (5-minute) TTL, pointing at Region A. Region A fails at t = 0.

- DNS doesn't push updates to resolvers holding a cached answer — they keep using it until it expires. A resolver that cached the answer at t = -60s (240 seconds left on its TTL when Region A fails) keeps sending clients to the dead region for up to 240 more seconds, even if you repoint the record to Region B the instant Region A fails.
- Only resolvers that *haven't* cached an answer yet (or whose cache just expired) see the corrected record on their next lookup.

So the real worst-case client-visible outage isn't just "however long it takes you to notice and update the record" — it's **that, plus up to one full TTL** for already-cached resolvers. At a 300-second TTL, that's up to 5 extra minutes of clients being sent to a dead endpoint, on top of detection-and-update time.

**Trade-offs considered:**

- **Short TTL (e.g. 30s):** caps worst-case exposure to 30 seconds, but resolvers re-query your authoritative DNS roughly 10x as often — more load on your DNS infrastructure, plus a small repeated lookup cost for clients.
- **Long TTL (e.g. 3600s):** cheaper to serve and caches better, but a real regional outage can keep sending traffic to a dead endpoint for up to an hour after you've already fixed the record.

Neither is "correct" — it's a direct trade against how fast you need failover to actually take effect.

**Case-study pointer:** Best fit is capstone #15 (`case-studies/llm-api-gateway`) — its premise is multi-provider routing and fallback on provider outage, and DNS-level geolocation/latency routing is the network layer underneath that gateway's own application-level routing logic, directing a client to the nearest healthy *region* before any request-level routing decision happens at all. This pairing is a reasoned judgment call, not a one-to-one mapping.

**Source(s) and further reading:**

- Cloudflare's "What is DNS?" learning-center explainer
- AWS Route 53 documentation on routing policies (weighted, latency-based, geolocation)
- `system-design-primer`'s own DNS section

---

## Concept 2: CDN

### Why?

Any part of an application that's identical for every user — a JS bundle, a stylesheet, a logo — is wasteful to re-fetch from a single origin server on every request from every user worldwide. A CDN keeps a cached copy of that unchanging content physically close to each user instead. The interesting question: where does that idea extend to AI-specific content, and where does it not?

### What?

A **CDN (Content Delivery Network)** is a geographically distributed network of proxy servers (**edge nodes** or **points of presence**) that cache copies of static content close to end users, so a request can be served from a nearby edge node instead of traveling all the way to the origin server.

- **Push CDN** — the origin proactively uploads content to CDN nodes before any user requests it. Good for content that changes rarely and needs every edge node primed in advance; you pay for storage of everything you push, whether or not it's ever requested.
- **Pull CDN** — the CDN fetches content from the origin the first time *any* user requests it through a given edge node (a **cache miss**), then serves later requests from cache until the entry expires. Good for content that changes often and for skipping manual uploads — at the cost of a slower first request per edge node (it has to round-trip to the origin first).
- **Cache hit ratio** — the percentage of requests an edge node serves directly from cache, versus falling through to the origin (a **cache miss** — either a first-ever request or an expired entry). A higher hit ratio means less load reaching the origin.

**Why model weights themselves are a poor CDN fit.** It's tempting to treat a model's weight file like any other large static file — cache it at the edge, same as a video or a dataset. Three things break that analogy:

1. **No "many clients, one file" pattern.** A CDN pays off when many users' browsers fetch the *same* file. Model weights aren't fetched by browsers at all — the inference server is the only consumer, so there's no fan-out to amortize.
2. **The edge can't act on the file once it has it.** Answering a request needs substantial GPU compute colocated with the weights. A CDN edge node is built to cheaply serve static bytes over HTTP, not to run GPU inference — so even a perfectly cached weight file at the edge still can't produce an answer there. Think of a CDN edge node as a vending machine stocked with pre-made snacks near you: fast, because the "cooking" already happened elsewhere. Serving a model is more like a live kitchen — you need the equipment on-site, not just the ingredients.
3. **Updates are enormous and total.** Weight files run multi-gigabyte to multi-hundred-gigabyte, and retraining or fine-tuning replaces them wholesale. "Pushing" a new version means repeating that transfer across the whole CDN footprint — a scale typical CDN workloads (small, frequently-reused web assets) never have to handle.

This is why model serving instead relies on object storage plus node-local disk caching on the inference hosts themselves (Lesson 1, Concepts B1/B2), not a CDN.

### How?

**Worked example — cache hit ratio for a chatbot's static assets.** Say a customer-facing chat UI's static assets (its JS bundle, CSS, and logo images — *not* the model itself) receive 10,000 requests/day through a pull CDN. 9,500 of those are served directly from edge cache; 500 are cache misses that fall through to the origin server.

```
cache_hit_ratio = hits / total_requests = 9,500 / 10,000 = 95%
origin_load_without_CDN  = 10,000 requests/day
origin_load_with_CDN     = 500 requests/day   (only the misses)
origin_load_reduction    = (10,000 - 500) / 10,000 = 95%
```

A 95% cache hit ratio for static assets means the origin server only has to handle 5% of the request volume it would otherwise see — the same percentage, directly, as the bandwidth and compute saved at the origin.

**Trade-offs considered:**

- **Push CDN:** predictable, always-warm edge caches and a fast first byte for every user — but you manage every update actively, and pay for storage whether or not content is ever requested.
- **Pull CDN:** hands-off, only caches what's actually requested — but the first user hitting a cold edge node after a deploy or cache expiry pays a real latency penalty on that cache-miss round trip to the origin, and popular-but-frequently-expiring content can repeatedly flood the origin with near-identical "first" requests from different edge nodes.

**Case-study pointer:** Best fit is capstone #12 (`case-studies/multi-agent-customer-support`) — its subject is a customer-support platform (grounded in the Sierra/Klarna case studies), implying a large, distributed, external user base: exactly the audience that makes a CDN worth having in front of its chat UI's static front-end assets, not its multi-agent orchestration logic. Note the boundary: capstone #12's own write-up and sourcing cover orchestration and hand-off design, not asset delivery — this pointer connects to that capstone's necessary-but-unwritten-about front-end, not its documented core lesson. This pairing is a reasoned judgment call, not a one-to-one mapping.

**Source(s) and further reading:**

- `system-design-primer`'s CDN section (push vs. pull, in its original non-AI framing)
- Cloudflare's and Akamai's own CDN product documentation
- vLLM and Ray Serve documentation on model weight loading, as a contrast case for how model artifacts actually get distributed to serving nodes

---

## Concept 3: Load Balancers

### Why?

DNS-level routing (Concept 1) is coarse and slow to change — it decides "which region/IP does this client's resolver get," cached for a whole TTL at a time. Once a request reaches a region, something still has to decide, per request, in real time, which specific inference-server replica or GPU pool handles it: that's a load balancer's job, and it has to make that call on every request without becoming the bottleneck itself.

### What?

A **load balancer** distributes incoming requests across multiple backend server instances, so no single instance is overwhelmed while others sit idle, and so a failed instance can be quietly routed around. Load balancers operate at one of two layers of the network stack — "layer" here just means how deep into a request a device is willing to look before deciding what to do with it. Lower layers see less and decide faster; higher layers see more and can decide smarter, at the cost of having to actually read more of the request first:

- **L4 (Layer 4 / transport-layer) load balancing** — routes using only the TCP/UDP connection info (source/destination IP address and port), without looking at the request's actual content. It's fast and protocol-agnostic — it doesn't need to understand HTTP, gRPC (a binary RPC protocol built on HTTP/2, commonly used for service-to-service calls), or anything else riding on top — but it can't decide based on *what* a request is actually asking for.
- **L7 (Layer 7 / application-layer) load balancing** — inspects the actual request content (HTTP method, URL path, headers, and sometimes the body) and routes based on that — e.g. sending `/v1/embeddings` requests to one backend pool and `/v1/chat/completions` to another, or routing on a `model` field inside the body. This flexibility costs more CPU and a little more latency per request, since the load balancer has to actually parse the request before deciding where it goes.

The difference is visibility, not just mechanism: think of L4 as a mail sorter who only reads the address on the envelope, and L7 as one who opens the envelope and reads the letter before deciding where it goes.

**SSL/TLS termination** is when the load balancer decrypts incoming HTTPS traffic itself (ending, or "terminating," the encrypted connection there) and forwards the plaintext request to backend servers over an internal network. This offloads the handshake-and-decryption cost from every backend onto the load balancer — at the cost of that internal hop being unencrypted, unless it's deliberately re-encrypted too (a pattern called **SSL bridging**).

**Session persistence** (also called **sticky sessions**) routes all requests from the same client to the *same* backend instance, instead of spreading them freely — needed whenever a backend holds per-client state other replicas don't share.

### How?

**Worked example — what L4 can't see that L7 can.** Here's a (simplified) HTTP request body for an LLM completion endpoint:

```json
POST /v1/chat/completions HTTP/1.1
Host: api.example.com

{
  "model": "large-context-model-v2",
  "messages": [{"role": "user", "content": "Summarize this 80-page report..."}]
}
```

An **L4** load balancer only ever sees the destination IP address and port (e.g. `203.0.113.10:443`) — it has no visibility into the `model` field, the URL path, or anything else inside this payload. So it can't route "large-context-model-v2" requests to a GPU pool with more memory while sending smaller/cheaper models to a leaner pool; every request to that IP:port gets the same routing decision. An **L7** load balancer parses the request far enough to see the `model` field and the `/v1/chat/completions` path, and can route accordingly — but that parsing on every single request is exactly the extra CPU/latency cost called out above.

**Trade-offs considered:**

- **L4:** cheaper and faster per request, but blind to what the request contains — fine when every backend behind it is truly interchangeable.
- **L7:** enables real capacity-aware routing (e.g. sending large-context requests to replicas provisioned with more GPU memory), but adds parsing overhead to every request — and if it's also doing SSL termination, that's decryption overhead on top.
- **Session persistence:** solves a real problem — if a multi-turn streaming conversation's follow-up request lands on a *different* replica than the one holding that conversation's KV cache (Lesson 1, Concept B1) in GPU memory, that replica has to recompute the KV cache from scratch, wasting the exact GPU memory and compute the cache existed to save. But it can also create uneven load, since the load balancer loses the freedom to redistribute a "sticky" client's traffic elsewhere.

**Case-study pointer:** capstone #10 (`case-studies/llm-inference-serving`) is the confirmed fit here — this Concept is best framed as "routing across inference-server replicas/GPU pools," which is exactly what capstone #10's PagedAttention/KV-cache-management subject matter sits behind.

**Source(s) and further reading:**

- `system-design-primer`'s load-balancer section (L4 vs. L7, in its original non-AI framing)
- NGINX's documentation on L4 vs. L7 load balancing and SSL termination
- Kwon et al., *"Efficient Memory Management for LLM Serving with PagedAttention"* (vLLM paper, SOSP 2023) — the KV-cache-per-replica reasoning behind why session persistence matters for LLM traffic specifically

---

## Concept 4: Reverse Proxy, and Load-Balancer-vs-Reverse-Proxy

### Why?

"Load balancer" and "reverse proxy" get used interchangeably in casual conversation, and a single component in a real LLM-serving stack often does both jobs at once. That makes it easy to lose track of which behavior comes from which role — and to miss that a role built for ordinary web traffic doesn't automatically fit LLM traffic.

### What?

A **reverse proxy** is a server that sits in front of one or more backend servers and forwards client requests to them on the backends' behalf, hiding the backends' existence and topology from the client entirely — the client only ever talks to the proxy. It's the same idea as a hotel front desk: guests only ever talk to the desk, never directly to housekeeping or maintenance, even though the desk is the one routing their requests to whichever staff member actually handles them. A reverse proxy's defining job is being that intermediary — for reasons that may have nothing to do with distributing load across multiple instances. Classic reverse-proxy responsibilities, all possible even in front of a *single* backend:

- SSL termination
- Caching responses
- Compressing responses
- Rewriting URLs
- Enforcing rate limits

The distinction from a load balancer: a **load balancer's** defining job is distributing traffic across *multiple* backend instances, for scale and availability. A reverse proxy doesn't have to balance anything — it can sit in front of exactly one backend and still do useful work. In practice, most real products collapse both roles: NGINX, Envoy, and the LLM-gateway products referenced below are simultaneously reverse proxies, load balancers, L7 routers, and rate limiters, all in the same box.

A **rate limit** caps how much traffic a client is allowed to send in a given time window, to protect backends from being overwhelmed and to enforce fair usage or billing tiers. The classic version is **request-based rate limiting** (e.g. "100 requests per minute per API key").

### How?

**Worked example — why request-based rate limiting doesn't actually bound LLM cost exposure.** Suppose a gateway enforces a classic limit of 100 requests/minute per API key, and the underlying model supports a 128,000-token context window.

```
worst-case burst if every request maxes out context:
  100 requests/min × 128,000 tokens/request = 12,800,000 tokens/min

versus a token-based limit of, say, 500,000 tokens/min:
  500,000 tokens/min actually bounds total compute/cost exposure,
  regardless of whether that's spread across 3 huge requests
  or 5,000 tiny ones
```

A request-based limit of "100/minute" is satisfied identically whether each of those 100 requests carries 50 tokens or 128,000 tokens — the actual GPU compute and dollar cost behind those two scenarios differ by roughly 2,560x, and the request-based limit is blind to all of it. This is exactly the gap every real LLM-gateway product examined for capstone #15 — LiteLLM, Portkey, Cloudflare AI Gateway — ran into: a traditional API gateway rate-limits *requests*, and had to add token-aware limiting on top because request counting alone doesn't transfer to LLM traffic.

**Trade-offs considered:** Request-based rate limiting is simple to implement and cheap to check (just count requests) but doesn't bound actual compute/cost exposure for LLM traffic, since token count per request varies by orders of magnitude. Token-based rate limiting (or a hybrid of both) actually bounds cost, but requires either tokenizing the request up front or estimating its token count before deciding whether to allow it — adding a small amount of per-request latency and complexity purely to make the admission decision, on top of whatever the request itself costs once admitted.

**Case-study pointer:** capstone #15 (`case-studies/llm-api-gateway`) is the confirmed fit for this Concept. Its sourcing is explicitly secondary/product-documentation (no single company has published a primary engineering teardown of this specific pattern) — drawn from LiteLLM's open-source proxy docs (OpenAI-compatible multi-provider routing, retries, fallback, per-key/team/model rate limits), Portkey's product docs (managed routing, load balancing, fallbacks, caching, guardrails, budget limits), and Cloudflare's AI Gateway docs (edge-hosted proxy with caching, rate limiting, analytics). Its own stated lesson is exactly the one this Concept's worked example demonstrates: classic gateway patterns (rate limiting, load balancing, caching, failover) don't transfer to LLM traffic unchanged.

**Source(s) and further reading:**

- `system-design-primer`'s reverse-proxy section (the classic load-balancer-vs-reverse-proxy framing)
- LiteLLM, Portkey, and Cloudflare AI Gateway product documentation (secondary/product-documentation sourcing, as capstone #15 itself discloses)
- NGINX and Envoy documentation on combined reverse-proxy/load-balancer configurations

---

## Hands-On Walkthrough

There's no single CLI for this lesson's content — work through these yourself, by hand, before moving on.

**1. DNS failover exposure.** Your API's DNS record has a 120-second TTL. A region fails at 2:00:00pm and you update the DNS record at 2:00:30pm (30 seconds to detect and react). What's the latest possible time a resolver that cached the old answer at 1:59:50pm could still be sending traffic to the dead region? *(For the resolver that cached at 1:59:50pm specifically, it had 110 seconds left on its TTL at the moment of failure — 1:59:50pm + 120s = 2:01:50pm, so that particular resolver stops being a problem by 2:01:50pm. But that's not the true worst case: a resolver that happens to do a fresh lookup just before the fix lands — say at 2:00:29pm, one second before the record is corrected at 2:00:30pm — gets back the stale answer and starts a brand-new, full 120-second TTL on it from that moment, exposing traffic until 2:02:29pm. Applying the lesson's own formula directly — worst_case_delay = detection_and_update_time + ttl_remaining_at_moment_of_failure, with ttl_remaining at its maximum (the full TTL) — gives 30s (detection/fix time) + 120s (full TTL) = 150s after the 2:00:00pm failure = 2:02:30pm. So the true worst case is ~2:02:30pm, not 2:01:50pm, and it absolutely does depend on how fast you react: a slower fix widens this window further, since every extra second before the record is corrected is another second a freshly-querying resolver could start a full new TTL on the stale answer.)*

**2. Cache hit ratio, with your own numbers.** Pick a daily request volume and a cache-miss count of your own for a chat UI's static assets, compute the cache hit ratio, and compute what percentage reduction in origin load that represents. Confirm the two percentages (hit ratio and origin-load reduction) come out equal, and explain in one sentence why they must.

**3. Request-based vs. token-based rate limits.** Pick your own requests/minute limit and your own model's context window size, compute the worst-case tokens/minute burst under a pure request-based limit, and compare it against a token-based limit of your choosing. Confirm for yourself how large the gap is between "requests allowed" and "actual compute/cost bounded."

---

## Summary

| Concept | One-line takeaway |
|---|---|
| DNS | DNS routing policies (weighted, latency-based, geolocation-based) decide which region a client reaches before any other layer runs — and a record's TTL sets a hard floor on how fast a DNS-level failover can actually take effect. |
| CDN | Push vs. pull trades manual sync effort against cold-cache latency for ordinary static assets — but model weights fail the CDN fit entirely, since inference needs colocated GPU compute a CDN edge node doesn't have. |
| Load balancers | L4 is fast but content-blind; L7 can route on what's actually in the request (e.g. which model) at the cost of parsing every request — and session persistence protects a replica's KV cache at the cost of even load distribution. |
| Reverse proxy vs. load balancer | A reverse proxy's job (intermediary, caching, SSL termination, rate limiting) doesn't require balancing anything — and a classic request-based rate limit doesn't actually bound LLM cost exposure, since token count per request varies by orders of magnitude. |

## Key Formulas & Config Reference

```
DNS worst-case failover exposure:
  worst_case_delay = detection_and_update_time + ttl_remaining_at_moment_of_failure
  (ttl_remaining can be up to the full configured TTL)

CDN cache hit ratio:
  cache_hit_ratio = cache_hits / total_requests
  origin_load_reduction = cache_hit_ratio   (the two are numerically identical)

Token-based burst exposure under a request-only rate limit:
  worst_case_tokens_per_window = requests_per_window × max_tokens_per_request
```

```json
// Example weighted-routing-style DNS record set (illustrative, Route53-style)
{
  "Name": "api.example.com",
  "Type": "A",
  "TTL": 60,
  "SetIdentifier": "region-a",
  "Weight": 70,
  "ResourceRecords": [{ "Value": "203.0.113.10" }]
}
```

**Next:** Checkpoint 4, then Lesson 5 — RDBMS scaling, NoSQL types, and caching strategies for the data layer.
