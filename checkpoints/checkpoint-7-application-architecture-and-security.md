# Checkpoint 7: Application Architecture and Security

## Purpose

This checkpoint verifies you can compute why decomposing a monolith into microservices chained in series makes a system less available (not more) absent added redundancy, compute how a health-check interval and failure threshold together bound a dead instance's traffic exposure, state what encryption in transit and at rest each actually protect against and why neither substitutes for the other, compute the blast-radius reduction least privilege buys and connect it to Lesson 8's named prerequisites, and carry out the five-step back-of-envelope method including naming an estimate's most sensitive assumption.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1: A monolith with 99.9% availability is decomposed into a supervisor, a specialist, and a validator service (capstone #12's shape), each independently deployed and each, on its own, just as reliable as the original monolith (99.9%). Using Lesson 3's series-availability formula, what's the combined availability of the three-service chain, and why does splitting into more independently-deployable services make the system *less* available rather than more — unless something else is added?</summary>

**Answer:** Because a request has to pass through all three services in sequence, series availability applies: `combined = 0.999 × 0.999 × 0.999 = 0.997003`, i.e. 99.7003% available — about 26.3 hours/year of downtime, roughly 3x worse than the monolith's own 99.9% (~8.77 hours/year), even though every individual service is exactly as reliable as the thing it replaced. This happens because chaining services in series means a request fails if *any* one of them fails, not just the weakest one — decomposing a system into more pieces without adding redundancy multiplies failure probability across more links, not fewer. Fixing this requires adding redundancy: making each of the three services an active-active redundant pair (99.9999% available each, via Lesson 3's parallel-availability formula) and chaining those three redundant pairs in series brings the system to ≈99.9997% available (≈1.6 minutes/year downtime) — but at the cost of six total replicas instead of the monolith's one deployable unit.

**Why this matters:** Lesson 7's own text states this directly as the point of the worked example: "Decomposing into more services chained in series doesn't automatically buy more availability — per Lesson 3's own math, it does the opposite, unless redundancy is added to compensate." Single-responsibility decomposition buys independent scaling, deployment, and rollback — but only by paying for redundancy infrastructure, not for free.
</details>

<details>
<summary>Question 2: A Consul-style service registration sets `Check.Interval: "10s"` and the registry requires 3 consecutive failed health-check probes before marking an instance unhealthy and pulling it from rotation. For how long after an instance actually dies can it still be selected and sent live traffic, and what's the direct trade-off in tuning that interval and threshold?</summary>

**Answer:** `time_to_detect_and_remove = check_interval × consecutive_failures_required = 10s × 3 = 30 seconds`. For up to 30 seconds after an instance dies, it can still be selected and sent live traffic by a caller doing client-side discovery, or by a load balancer doing server-side discovery on the caller's behalf. The lesson names this directly as "the service-discovery analog of Lesson 4's Concept 1 DNS-TTL worst-case exposure" — here the staleness window is the health check's own interval × threshold rather than a DNS cache. The trade-off: a shorter interval or lower failure threshold detects a dead instance faster but generates more frequent health-check traffic against every instance and risks flapping an instance out of rotation over one slow-but-actually-fine response; a longer interval or higher threshold is gentler on the system but widens the window during which a caller can still be routed to something that's already dead.

**Why this matters:** This is a direct, tunable knob, not a fixed constant — the lesson's own trade-off language ("a direct, tunable trade") makes clear that choosing values here is a deliberate design decision with a real cost on both sides, not a default to leave alone.
</details>

<details>
<summary>Question 3: Encryption in transit (TLS) and encryption at rest (e.g. an S3 bucket's `SSEAlgorithm: AES256` default) are both "encryption," so why does Lesson 7 insist they're genuinely separate protections that neither one substitutes for the other?</summary>

**Answer:** They protect against two different threat models that exist at two different times. Encryption in transit protects data while it's moving across a network — so anyone who intercepts the traffic between two endpoints sees only ciphertext — and TLS does nothing for a stolen disk, because by the time the disk is stolen the data is already at rest, not in motion. Encryption at rest protects data while it's stored (on a database's disk, in a backup, in object storage) — so someone who gains access to the storage medium itself (a stolen disk, a misconfigured bucket, a cloud provider's own internal access) still can't read the content without the decryption key — and it does nothing for traffic sniffed mid-network, because it only engages once the data is sitting still. The lesson states this directly: "TLS does nothing for a stolen disk; at-rest encryption does nothing for traffic sniffed mid-network." In a microservices architecture, encryption in transit also extends to mutual TLS (mTLS), where both sides of an internal service-to-service connection present and verify a certificate, so one compromised service can't simply pretend to be another.

**Why this matters:** Skipping either protection doesn't just halve the coverage — per the lesson's own trade-offs line, "it leaves one entire threat model...completely uncovered." Treating "we encrypt" as a single checkbox misses that two distinct attack surfaces each need their own answer.
</details>

<details>
<summary>Question 4: An organization runs 50 S3 buckets. One tool's credential is scoped to least privilege (read-only on exactly one bucket); a broad alternative credential grants `s3:*` on `Resource: "*"`. If either credential leaks — for instance via a successful prompt-injection attack coercing the agent into revealing it — what's the blast-radius ratio between the two, and which two Lesson 8 Concepts does Lesson 7 name this as the direct prerequisite for?</summary>

**Answer:** `blast_radius_ratio = broad_buckets_exposed / scoped_buckets_exposed = 50 / 1 = 50x`. The least-privilege-scoped credential exposes exactly one bucket, read-only; the broad credential exposes all 50 buckets with full read/write/delete access — the identical leak event becomes a 50x larger incident purely because of which credential was behind the tool. Lesson 7 states explicitly that input sanitization and least privilege are "the direct foundations Lesson 8 names explicitly for F1 (prompt injection) and F3 (credential handling)" — F1 needs input sanitization as its starting point (extended to the fact that an LLM's input includes retrieved documents and tool outputs, not just the user's literal message), and F3 needs least privilege as its starting point (applied specifically to scoping each tool's own credential), neither of which Lesson 7 re-teaches in full.

**Why this matters:** Least privilege doesn't prevent a leak from happening — it bounds how much damage that leak can do once it happens, and the 50x figure is the concrete version of why "just give it admin, it's simpler" is a real, quantifiable risk rather than a vague caution.
</details>

<details>
<summary>Question 5: Walk through the five-step back-of-envelope method Lesson 7 teaches, and explain what Step 5 ("name the assumption the answer is most sensitive to") concluded for the lesson's own worked RAG-chatbot cost estimate — including the specific dollar figures.</summary>

**Answer:** The five steps are: (1) state your assumptions explicitly; (2) decompose into independently-estimable quantities; (3) compute step by step, carrying units; (4) sanity-check the order of magnitude against a known reference point; (5) name the assumption the answer is most sensitive to. In the lesson's worked example (50,000 users, 10 messages/day, 1,500 input + 300 output tokens/message), the $4,500/day total cost splits exactly evenly between its input-token half ($2,250) and output-token half ($2,250). Step 5 concludes the input-token half is the more sensitive one, because it's driven by how much retrieved context a RAG system injects per query — a design choice, not a fixed constant the way response length more often is. Doubling the injected context to 3,000 input tokens roughly doubles the input-token half of the cost ($2,250 → $4,500), pushing the daily total from $4,500 to $6,750 — a 50% total increase — with nothing else in the estimate changing.

**Why this matters:** Step 5 is what turns a one-off number into something actionable: it names the specific input worth actually measuring in a prototype before trusting the rest of the estimate's conclusions, rather than treating every assumption as equally risky.
</details>

## Hands-On Self-Check

There's no single CLI for this lesson — confirm you can do each of the following, without looking back at it:

- [ ] I can state, from memory, the single responsibility principle, and explain why "split into microservices" and "split into *how many* microservices" are different questions that SRP — not an arbitrary target count — answers.
- [ ] I can compute combined series availability for three newly-decomposed services and compute how adding an active-active redundant pair behind each one changes that result, including naming the total replica count that redundancy costs.
- [ ] I can compute `time_to_detect_and_remove = check_interval × consecutive_failures_required` given any interval and failure-threshold pair, and name the two concrete shapes of service discovery (client-side vs. server-side) by which party queries the registry.
- [ ] I can name all four security practices this lesson teaches in full (encrypt in transit, encrypt at rest, sanitize inputs/use parameterized queries, least privilege) and state, for each, the specific threat it addresses that the other three don't.
- [ ] I can compute a least-privilege blast-radius ratio given a broad-grant resource count and a scoped-grant resource count, and name which two Lesson 8 Concepts (by their F-number) this Concept is the stated prerequisite for.
- [ ] I can run (or reason through by hand) the five-step back-of-envelope method on a fresh scenario of my own choosing, ending with a Step 5 statement naming the single most sensitive assumption.
- [ ] I can run (or reason through line by line) the lesson's Python snippet and confirm `time_to_detect_failure(10, 3)` returns 30.0, `blast_radius_ratio(50, 1)` returns 50.0, and `back_of_envelope_daily_cost(...)` reproduces the $4,500 daily-cost figure.

## Next Step

Move to **Lesson 8: Safety and Isolation**.
