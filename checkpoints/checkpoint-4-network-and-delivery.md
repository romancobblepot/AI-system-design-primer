# Checkpoint 4: Network and Delivery

## Purpose

This checkpoint verifies you understand how DNS routing and TTLs bound failover speed, why model weights don't fit the CDN model even though they're large static-looking files, the real difference between L4 and L7 load balancing, and why a reverse proxy's job isn't the same as a load balancer's — including why classic request-based rate limiting breaks down for LLM traffic.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1: A DNS record has a 180-second TTL. If the region it points to fails and you update the record within 10 seconds, why might some clients still reach the dead region for nearly 3 minutes afterward?</summary>

**Answer:** A TTL tells resolvers how long they're allowed to cache a DNS answer before re-querying — it does not mean the authoritative server can push the update out to resolvers that already cached the old answer. A resolver that cached the old (now-stale) record just before the failure could have up to the full 180 seconds left on its cache before it's required to look up the record again and get the corrected answer. So the real worst-case exposure is your reaction time (10 seconds) *plus* up to a full TTL (180 seconds) for already-cached resolvers — roughly 3 minutes, not 10 seconds.

**Why this matters:** This is why TTL is a deliberate trade-off, not just a caching detail — a short TTL buys faster failover at the cost of far more repeat DNS queries, and the "update the record" step alone never tells you your real failover speed.
</details>

<details>
<summary>Question 2: Why can't you just treat a model's weight file like any other large static asset and serve it from a CDN edge node?</summary>

**Answer:** Three separate reasons: (1) model weights aren't fetched by end-user browsers the way a webpage's JS/CSS/images are — the actual consumer of the weights is the inference server, not the client making the request, so there's no "many clients downloading the same file" pattern for a CDN to amortize; (2) even if a weight file were perfectly cached at an edge node, running inference against it requires substantial colocated GPU compute, which a CDN edge node — built to cheaply serve static bytes over HTTP — doesn't have; (3) weight files are enormous and get replaced wholesale on retraining, so "pushing" updates to every edge node repeats a massive transfer at a scale ordinary CDN workloads never hit.

**Why this matters:** This is the kind of "looks like the same problem, isn't" case that trips people up if they only know CDNs from ordinary web development — AI serving distributes model artifacts through object storage and node-local caching instead, for structural reasons, not because nobody thought to try a CDN.
</details>

<details>
<summary>Question 3: What's the actual difference between what an L4 load balancer can see about a request and what an L7 load balancer can see — and why does that matter for routing LLM traffic specifically?</summary>

**Answer:** An L4 (transport-layer) load balancer only sees the TCP/UDP connection-level information — source/destination IP address and port — and has no visibility into the actual request content. An L7 (application-layer) load balancer parses the request itself — the HTTP method, URL path, headers, and sometimes the body — and can route based on what it finds there. For LLM traffic, this matters because the thing you'd often want to route on (which model was requested, e.g. a `model` field in the request body, or which endpoint path like `/v1/embeddings` vs. `/v1/chat/completions`) only exists inside the request content — an L4 load balancer structurally cannot make that distinction, no matter how it's configured.

**Why this matters:** Choosing L4 when you actually need model-aware or endpoint-aware routing isn't a configuration mistake you can fix later with a setting — it's a capability the layer itself doesn't have, so the choice has to be made correctly up front.
</details>

<details>
<summary>Question 4: What does SSL/TLS termination at a load balancer actually trade away, and what is SSL bridging for?</summary>

**Answer:** SSL termination means the load balancer itself decrypts incoming HTTPS traffic and forwards the now-plaintext request to backend servers over the internal network — this offloads the CPU cost of the cryptographic handshake and decryption from every backend onto the load balancer, which is the whole reason to do it. What it trades away is that the load-balancer-to-backend hop is now unencrypted by default — acceptable only if that hop stays strictly inside a trusted internal network, and a real exposure if it doesn't. SSL bridging exists to close that gap: the load balancer still terminates the original external connection, but then re-encrypts the request with its own certificate before forwarding it to the backend, so the whole path is encrypted end-to-end — at the cost of paying the cryptographic overhead twice (once per hop) instead of once.

**Why this matters:** Terminating SSL without asking "what happens on the backend hop" turns a legitimate performance optimization into an overlooked internal-network security gap — the same CPU-offload-vs-encrypted-everywhere tension shows up anywhere a trusted boundary is assumed rather than verified.
</details>

<details>
<summary>Question 5: Why does a classic request-based rate limit (e.g. "100 requests per minute") fail to actually bound an LLM API's cost or compute exposure, and what do real LLM gateway products do about it?</summary>

**Answer:** A request-based limit counts requests, not the work each request actually causes — and for LLM traffic, a single request's token count (and therefore its compute cost) can vary by orders of magnitude depending on context length (e.g. a 50-token request vs. a 128,000-token request against the same 100-requests/minute cap). The worst-case exposure under a pure request-based limit is requests_per_window × max_tokens_per_request, which for a long-context model can be enormous even while the "100 requests/minute" rule is technically being honored. Real LLM gateway products (LiteLLM, Portkey, Cloudflare AI Gateway, per capstone #15's sourcing) add token-aware rate limiting on top of classic request counting specifically to close this gap.

**Why this matters:** This is the single clearest example in this lesson of why a classic infrastructure pattern (rate limiting) doesn't transfer to LLM traffic unchanged — the unit the limit needs to be measured in changes, even though the mechanism (a gateway enforcing a cap) looks identical on the surface.
</details>

## Hands-On Self-Check

There's no CLI for this lesson — confirm you can do each of the following, without looking back at the lesson:

- [ ] I can compute the worst-case DNS failover exposure given a TTL and a detection-and-update time.
- [ ] I can state, from memory, the three separate reasons model weights are a poor CDN fit (not just "they're too big").
- [ ] I can compute a cache hit ratio given a request count and a cache-miss count, and explain why that number equals the origin-load reduction.
- [ ] I can explain, concretely, one thing an L7 load balancer can route on that an L4 load balancer structurally cannot.
- [ ] I can explain why a reverse proxy doesn't need to be load-balancing anything to still be doing useful work, with an example of a reverse-proxy job that isn't load distribution.
- [ ] I can compute the worst-case tokens/minute burst under a request-only rate limit, given a requests-per-minute cap and a model's context window size.

## Next Step

Move to **Lesson 5: Data Layer**.
