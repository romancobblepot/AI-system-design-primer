# Capstone #12: Multi-Agent Customer-Support Platform — A Secondary-Source Synthesis of Sierra AI's Architecture and OpenAI's Klarna Customer Story

**Source(s):** Secondary technical coverage only, plus one primary-but-non-technical company blog post — this capstone's sourcing is genuinely different in kind from every other capstone in this repo, and the rest of this section exists to be precise about exactly how.

- **Sierra AI's architecture:** Sierra's own company blog, *"Constellation of models: the architecture powering Sierra's agents"* (sierra.ai/blog/constellation-of-models, Dec. 3, 2025) — confirmed directly by fetching the live page. This is a **primary** source (it's Sierra's own writing about its own product), but it is **not an engineering teardown**: confirmed directly from the fetched page, it names no specific models or providers, publishes no latency/accuracy/uptime numbers, includes no architecture diagram, and does not explain its own routing or model-selection logic beyond general description. It is a product-marketing overview, not the kind of primary source capstone #13's Cognition blog post or capstone #10's vLLM paper are. Everything else used in this document about Sierra is genuinely **secondary**: Atlan's third-party explainer *"What Is Sierra? The AI Agent Platform for Customer Service"* (atlan.com) — confirmed by direct fetch, and flagged because Atlan sells a competing data-context product and has a commercial interest in portraying vendor-built context layers as risky; third-party technical coverage of Sierra that characterizes Sierra's "Constellation" branding using **planner/executor/validator** terminology — this vocabulary is commonly associated with a Cybernews review, but a direct fetch of the live Cybernews page returned HTTP 403 on repeated attempts, and an independent search for the exact phrase turned up this framing more directly in other third-party write-ups (e.g. an Oboe interview-prep study guide, a separate blog's worked "$500 refund" example) than in any verifiable Cybernews text, so this document cannot confirm Cybernews specifically as the originating source and attributes the terminology to third-party coverage generally rather than standing behind one unconfirmed name, and nothing from it appears in quotation marks below; and RuntimeWire's coverage of Sierra's Context Engine announcement (tied to Sierra's "Horizon" platform) — secondary, and itself substantially built on Sierra's own announcement text, confirmed only at one remove.
- **OpenAI's Klarna customer story:** Two direct fetch attempts against `openai.com/customer-stories/klarna` and `openai.com/index/klarna/` both returned HTTP 403, and the Wayback Machine was not reachable from this environment either (the standing rule to try it before giving up on a source was followed; it simply didn't work here). This document therefore could **not** read OpenAI's own page text directly, and nothing attributed to it below is a verbatim quote. Instead, the figures used are corroborated across independent press coverage of the same announcement — CX Today, Silicon Canals, and VKTR all report the identical set of numbers, all explicitly attributed to Klarna's own statements and its CEO's own remarks, carried (per those articles) through OpenAI's customer-story page. Every Klarna number in this document is Klarna's own self-reported figure, one month after launch, not an independently audited result, and not a number this document confirmed by reading OpenAI's page itself.

**Confidence.** **Neither Sierra nor Klarna has published a primary engineering teardown of this system** — this search confirms that rather than turning up one — and Sierra's own blog, the one piece of truly primary material available, is itself non-technical. Two specific things in this document are **this repo's own synthesis, not a sourced architectural fact**, and are called out again at the point they're used: (1) whether the "supervisor over a constellation of specialist models" framing (Sierra's own term) and the "planner/executor/validator split" framing (a third party's characterization of Sierra's branding, not Sierra's own term) describe the *same* architecture or two *related-but-distinct* ones — Step 4 below treats this honestly as unresolved, not as a confirmed equivalence; (2) every number in this document's back-of-envelope and validator-catch-rate calculations (Steps 2 and 6) beyond the handful of Klarna figures named above is **illustrative**, invented for this document to make a real teaching point computable, not disclosed by Sierra, Klarna, or OpenAI. Nothing below should be read as "this is how Sierra's or Klarna's system actually works internally" — only as "this is the best reconstruction available from outside coverage, with every seam in that reconstruction marked."

**Scope note.** This capstone covers the architectural pattern — a routing/supervisory layer, one or more narrowly-scoped specialist agents, and an independent validation layer, operating over a unified per-customer context store — illustrated by Sierra's product and Klarna's deployment. It does **not** cover: training or fine-tuning any of the underlying models (treated as off-the-shelf, the same framing capstone #13 uses for Devin's underlying LLM); the specific enterprise integrations into a real CRM, billing, or order-management backend (represented here by a schema, not a real connector); prompt-injection defense mechanics (Lesson 8's F1, referenced not re-derived); content moderation of user-submitted text (capstones #5/#11's territory); or Sierra's actual proprietary routing/model-selection algorithm or Klarna's actual internal system design — neither company discloses either, and this document does not guess at them.

---

## Step 1: Clarify Requirements & Frame the ML/AI Objective

**The actual objective.** Resolve a customer-support request — a refund, a subscription change, a billing dispute, a cancellation, an order-status question (Klarna's own named categories, per the corroborated press coverage above: "refunds, returns, payment-related issues, cancellations, disputes, and invoice inaccuracies") — autonomously, end to end, without a human handling the conversation, **while keeping the rate of incorrect or policy-violating actions that actually reach the customer low enough to be acceptable**. That second clause is load-bearing, not decorative: a system graded only on "percentage of conversations the AI handled without a human" would be rewarded for confidently taking a wrong action just as much as a correct one, which is exactly the failure mode this entire capstone's central architectural choice (Step 4, Step 6) exists to prevent.

**What counts as ground truth / feedback signal — three distinct measures, not one:**
1. **Resolution rate** — the fraction of support conversations an agent handles to completion without being escalated to a human. Klarna's own disclosed figure, carried through OpenAI's customer story and corroborated by independent press, is that its assistant handled "two-thirds of customer service chats" in its first month. This document treats that as a resolution-rate-shaped number, with one honest caveat: "handled two-thirds of chats" is the figure Klarna actually disclosed, and it is not stated anywhere in the corroborating coverage whether that specifically means "resolved with zero human involvement at any point" versus "primarily handled by the assistant" — a distinction this document cannot resolve from the sources available, so it is named here rather than papered over.
2. **Escalation rate** — the fraction of conversations an agent deliberately hands off to a human, either because it can't complete the task (a policy exception, a request outside its scope) or because the validator layer (Step 4) blocks a proposed action and no safe alternative exists. This is the complement of resolution rate in the simplest framing, but the two are tracked separately in Step 6 because *why* a conversation escalates (an inherent capability gap vs. a caught mistake) is itself a useful signal, not just a single rate.
3. **Validator catch-rate** — defined in full in Step 4's Sidebar below, since it's this capstone's own central, previously-undefined concept — the fraction of actually-bad proposed actions that an independent checking layer correctly blocks before they reach the customer, as distinct from resolution/escalation rate, which only measures *whether* a human got involved, not whether the actions an agent actually took were correct.

Klarna's other disclosed, corroborated figures — doing the work of roughly 700 full-time agents, cutting average resolution time from 11 minutes to under 2, operating in 23 markets and 35+ languages, customer satisfaction reported on par with human agents, and an estimated $40M 2024 profit improvement — are all **outcome** metrics (speed, cost, satisfaction), not **correctness** metrics; this document uses them in Step 2 to size the system, not as evidence about how often the system's underlying actions were actually right, because none of the corroborated coverage discloses an error rate, a validator catch-rate, or anything else that would let that be checked from outside.

**Explicitly out of scope:** the underlying LLMs' training/fine-tuning; the real backend integrations (order management, billing, CRM) a production version would need, beyond the illustrative schema in Step 3; the exact classification/routing algorithm Sierra's supervisor layer uses internally (undisclosed); and any claim about Klarna's or Sierra's actual measured error or catch rates (undisclosed — every such number in this document is flagged illustrative at the point it's introduced).

**Trade-offs considered:** Optimizing purely for resolution rate (minimizing escalations) is the easiest objective to measure and the one most visible in the corroborated press coverage — but a system tuned only against it has a direct incentive to avoid escalating even when it should, which is precisely the risk a dedicated validation layer (Step 4) exists to catch independently of whatever the resolution-rate metric alone would reward. Treating customer satisfaction as a proxy for correctness is tempting (Klarna's own reported CSAT parity with human agents is genuinely good news) but satisfaction and correctness aren't the same axis — a customer can be satisfied by a fast, friendly, confidently-wrong answer they don't have the information to catch themselves, which is exactly why Step 6 tracks validator catch-rate as its own, separate number rather than inferring correctness from satisfaction.

---

## Step 2: Back-of-Envelope Constraints

**Anchoring to Klarna's own disclosed scale, corroborated across independent press.** 2.3 million AI-handled conversations in the assistant's first month, reported as roughly two-thirds of Klarna's total customer-service chat volume — which implies a total chat volume (AI-handled plus human-handled) of approximately 2.3M ÷ (2/3) ≈ **3.45 million conversations/month**, of which roughly 1.15 million/month still go to (or get escalated to) a human. These are Klarna's own self-reported numbers, not independently audited, carried here exactly as disclosed.

```
ai_handled_per_month = 2,300,000
ai_handled_share     = 2/3

total_chat_volume_per_month = ai_handled_per_month / ai_handled_share
                             = 2,300,000 / 0.6667
                             ≈ 3,450,000 conversations/month

human_handled_per_month = total_chat_volume_per_month - ai_handled_per_month
                        ≈ 3,450,000 - 2,300,000
                        = 1,150,000 conversations/month
```

**Daily AI-handled volume, and concurrent sessions via Little's Law.**

```
ai_handled_per_day = 2,300,000 / 30 days ≈ 76,667 conversations/day
```

**Sidebar — Little's Law.** *(First appearance in this repo of this specific formula; it's a general queueing-theory result, not core infra Lessons 3-7 already curate down to by name, and not already taught in Lesson 1 either, so it gets the inline-Sidebar-plus-glossary treatment rather than a lesson link that doesn't exist.)*
- **Why?** Klarna's own disclosed numbers give a monthly conversation count and an average resolution time, but neither of those is the number a platform actually has to provision for: how many sessions are open, consuming compute and holding state, *at the same moment*. Converting "conversations per month" into "concurrent sessions right now" needs an actual formula, not a guess.
- **What?** **Little's Law** is a queueing-theory result stating that, for a system in steady state, the average number of items *in* the system (`L`) equals the average arrival rate of new items (`λ`, items per unit time) multiplied by the average time each item spends in the system (`W`): **`L = λ × W`**. It holds regardless of the arrival pattern or the service-time distribution, which is exactly why it's usable here from only two disclosed numbers.
- **How?** Applied to Klarna's own figures: `λ` is the AI-handled arrival rate in conversations/second, and `W` is the assistant's own disclosed average resolution time (2 minutes, down from a prior 11).

```
lambda = ai_handled_per_day / seconds_per_day
       = 76,667 / 86,400
       ≈ 0.887 conversations/sec

W = 120 seconds   (Klarna's own disclosed ~2-minute average resolution time)

L = lambda × W
  = 0.887 × 120
  ≈ 106 concurrent sessions, on average, platform-wide
```

**Latency budget per turn — the real constraint this capstone's own architecture (Step 4) has to fit inside.** A multi-agent design where a supervisor classifies the request, a specialist drafts a response or action, and a validator checks it before anything executes (Step 4) runs those three model calls **sequentially**, not in parallel, because each one needs the previous one's output. Using illustrative per-call latencies (none of these are disclosed by Sierra or Klarna) — a short classification call (~400ms), a longer generation call (~900ms), and a shorter verification call (~500ms):

```
sequential_three_call_latency_floor = 400 + 900 + 500 = 1,800 ms  (1.8 seconds)

versus a single-call monolithic design (one model drafts a reply with no separate check):
single_call_latency_floor ≈ 900 ms

latency_floor_ratio = 1,800 / 900 = 2x
```

Before any network, gateway, or queuing overhead, the three-role architecture imposes roughly **twice** the response-time floor of a single-call design — a real, concrete cost of this capstone's central architectural choice, not a free improvement, and the number Step 4's trade-off against a monolithic agent has to be weighed against directly.

**Trade-offs considered:** The 106-concurrent-session figure is an *average*, not a provisioning target — real support traffic isn't uniform across 24 hours, and Little's Law says nothing about peak load; a platform that provisions only for the 24-hour average will be under capacity during Klarna's own likely peak hours, so a real deployment would size for something like 2-4x this average as a rough peak-to-average ratio (illustrative — Klarna discloses no hourly distribution). The per-call latency assumptions feeding the 1.8-second floor are this estimate's most sensitive input, in the same sense capstone #13's Step 2 names its own round-trip-count assumption as its most sensitive one: if the validator call alone takes 2 seconds instead of 500ms (plausible if it has to re-retrieve policy context, Step 3), the three-call floor more than doubles again, which is exactly the kind of number worth measuring first in a real prototype rather than trusting this illustrative split.

---

## Step 3: Data / Knowledge Pipeline

**Two genuinely different data sources, not one — a distinction worth being explicit about before either gets conflated with the other.**

1. **Per-customer context** — what Sierra's own secondary coverage names the **Agent Data Platform** (and, per a later Sierra announcement covered by the same secondary sources, a "Context Engine"): a data-integration layer that unifies a given customer's history and current state — billing status, subscription state, prior conversation transcripts, order/shipment history — across sessions, channels, and backend systems of record, so an agent isn't starting every conversation from zero. This is **not** a new concept this repo needs a fresh home for: it's Lesson 1's own Concept E2, **long-term memory** ("information about a user, a task, or past interactions that an agent stores *outside* the current conversation... so it can be retrieved and reused in future, separate sessions"), applied at enterprise, cross-channel, cross-system scale rather than within a single agent's own private store. The genuinely new piece Sierra's secondary coverage adds on top of E2's basic definition is the **unification** step itself: per the Atlan explainer (secondary, flagged above for its commercial interest in this specific framing), the argument is that raw CRM and billing records alone aren't enough for an agent to act on a customer's order or account — something has to merge them into one queryable representation first, which is a data-integration problem layered on top of E2's memory concept, not a replacement for it.
2. **Policy/knowledge-base data** — the company's refund rules, eligibility policies, and FAQ content that *every* customer's conversation draws on, regardless of which specific customer is asking. This is a shared corpus, not a per-customer one, and it's exactly the retrieval problem Lesson 1's Concepts C1-C4 and capstone #9 (`solutions/rag-contextual-retrieval`) already cover in full — referenced here, not re-derived. The distinction matters operationally: a specialist agent (Step 4) needs *both* kinds of context for a single request (this customer's own billing history, *and* the general refund policy that applies to everyone), retrieved from two structurally different sources with two different freshness and consistency profiles.

**Freshness and consistency — where Lesson 3's CAP-theorem material applies directly.** Per-customer context has a real consistency requirement capstone #9's largely-static document corpus doesn't: if a specialist agent just processed a refund in this same conversation, the *very next* turn's context has to reflect that refund as already applied — a stale read here isn't just an inconvenience, it's the direct cause of a double-refund or a contradictory reply. This is Lesson 3's Concept 2 (CAP theorem, consistency patterns) applying to exactly the case Lesson 1's own E2 entry already flagged generically ("long-term memory... inherits the same consistency questions... that Lesson 3's CAP-theorem concept covers generally") — referenced here as that flag's own resolution: the per-customer context store needs **strong consistency** (Lesson 3's own term, referenced not re-derived) for at least the subset of fields a just-completed action touches, even if the rest of the store can tolerate eventual consistency.

**An illustrative per-customer context record** (Sierra and Klarna disclose no real schema; this is this document's own construction, shaped the way Atlan's secondary description implies — unifying several systems' data under one customer identity):

```json
{
  "customer_id": "cust_8f21a0",
  "last_updated_at": "2026-10-11T14:32:05Z",
  "subscription_state": {"plan": "pay_in_4", "status": "active", "next_payment_due": "2026-10-20"},
  "recent_orders": [
    {"order_id": "ord_55213", "status": "delivered", "amount_cents": 8499, "last_action": null}
  ],
  "open_disputes": [],
  "conversation_history_summary": "Asked about a late delivery on 2026-10-05; resolved by the assistant with a shipping-delay explanation, no action taken.",
  "channel_history": ["app", "email"]
}
```

`last_updated_at` is the field a strong-consistency write (e.g. a just-processed refund) has to update synchronously, so the very next read in the same conversation reflects it; `recent_orders[].last_action` is exactly the field a double-refund bug would show up in first, if a stale read let a specialist agent re-propose an action a prior turn had already taken.

**Trade-offs considered:** Unifying per-customer data across every channel and backend system into one queryable store (the Agent Data Platform pattern) buys real continuity — an agent that doesn't re-ask a question the customer already answered somewhere else — but concentrates a large volume of sensitive account and billing data into one layer that now has to be the platform's single most carefully access-controlled component, a multi-tenant-isolation concern (Lesson 8's F5, already defined in full there — silo/pool/bridge, referenced not re-derived) that gets sharper, not milder, the more systems get unified into it. Keeping per-customer context and shared policy knowledge in two separate retrieval paths (rather than merging them into one corpus) costs an extra retrieval call per turn, but avoids the correctness risk of ever indexing one customer's private billing data alongside content that's meant to be the same for every customer.

---

## Step 4: Model/Agent Core Design — Supervisor/Specialist/Validator, and the Honest Gap With "Planner/Executor/Validator"

**The architecture, confirmed from Sierra's own blog (primary-but-non-technical, per the Confidence note above).** A **supervisor agent** is, per Lesson 1's own Concept D5 (multi-agent orchestration, referenced not re-derived), "a designated 'supervisor' agent that delegates subtasks" — concretely here, the agent that receives an incoming request and decides which **specialist agent** — a distinct, narrowly-scoped model or role assigned to one category of task (a billing specialist, a returns specialist, a subscription-management specialist) — should handle it. Sierra's own confirmed language for the specialist layer is a **"constellation of models"**: agents "assembled using 15+ frontier, open-weight, and proprietary models," selected per task by need (the blog names low-latency tool calling, high-precision classification, long-context reasoning, and tone as separate needs with separate model fits), with "task-specific evaluations" deciding which model earns which role, and automated failover to an equivalent model if a provider degrades.

**The validator/guardrail agent — this capstone's own central concept, genuinely new, no existing Lesson 1-6 or Lesson 8 home for the *architectural role* specifically.**

**Sidebar — Validator/guardrail agent as a distinct architectural role.** *(First appearance in this repo of this specific role-level concept; a glossary entry is added alongside it.)*
- **Why?** Lesson 8's F4 Concept already defines the *mechanisms* a guardrail can use — schema-constrained output, content filtering, human-in-the-loop approval gates — in full, and this document deliberately does not re-derive any of them. But F4 is silent on a different question: *who* runs those checks, relative to *who* decided the action in the first place. A specialist agent asked to "double-check your own answer" (Lesson 1's own **reflection** control-flow pattern, already defined there) is still the same model, in the same conversation, with the same context and the same blind spots that produced the original answer — Lesson 9's own cited finding about LLM-as-judge (Zheng et al., referenced not re-derived: a judge model can favor its own family's writing style) is a confirmed instance of exactly this risk in a different setting, and it generalizes here as a reasoned inference, not a claim either Lesson 9 or this capstone's own sources make directly: a model checking its own proposed action is structurally less independent than a *separate* check would be, even before asking whether that separate check uses a different mechanism (F4's territory) at all.
- **What?** A **validator (or guardrail) agent** is a distinct agent — a separate model invocation, with its own, narrower context and its own, narrower job — whose only responsibility is checking a specialist agent's *proposed* action against policy, correctness, and safety constraints **before that action executes or reaches the customer**, as opposed to being folded into the same call that produced the action in the first place. This is an architectural separation-of-roles claim, distinct from and complementary to F4's own mechanism-level content: a validator agent's check can itself be implemented using F4's schema-constrained output, F4's content filtering, or F4's human-in-the-loop gate — the point of giving it its own role is that the check happens in a separate invocation that the specialist agent's own reasoning never sees or influences, not that it uses a different technique.
- **How?** Applied to this capstone directly: this capstone's teaching point is that validator/guardrail agents are a distinct role from the agent that takes the action, so one bad tool call doesn't reach the customer unchecked — the architecture below, and Step 6's worked numbers, are this document's concrete answer to exactly that framing. **Validator catch-rate** — this concept's own evaluation metric, used throughout Step 6 — is the fraction of actually-bad proposed actions (ones that would have been incorrect or policy-violating if executed unchecked) that the validator agent correctly blocks or flags, out of all actually-bad actions proposed to it; it is a recall measure over the validator's own judgment, not a measure of the specialist's error rate itself (Step 6 keeps those two numbers explicitly separate).

**The planner/executor/validator framing — a different secondary source's characterization, honestly reconciled rather than silently merged.** Third-party technical coverage of Sierra's product (secondary; this vocabulary is commonly associated with a Cybernews review, but repeated direct-fetch attempts against the live Cybernews page returned HTTP 403, and an independent search for the exact phrase found it more directly in other third-party write-ups than in any verifiable Cybernews text — so this document cannot confirm Cybernews specifically as the originating source and attributes it to third-party coverage generally, per the Confidence note) describes Sierra's "Constellation architecture" using **planner/executor/validator** vocabulary: a planner agent that figures out what the customer wants and decomposes the request into steps, executor agents that carry those steps out against connected systems, and validator agents that check the result against company policy before anything is finalized. Sierra's own blog, fetched directly, does **not** use this terminology — it describes model selection per task-type plus "supervisors" enforcing guardrails, without naming a formal planner/executor/validator trio. This document's own honest reconciliation, offered as reasoned synthesis and flagged as such rather than as a sourced fact: **supervisor/specialist and planner/executor are plausibly the same underlying idea described two ways** — a supervisor that routes by domain (Sierra's own framing) is functionally similar to a planner that decomposes a request into steps the right executor(s) then carry out (this third-party framing), especially for a request that only needs one specialist's single action. They are **not obviously identical**, though, for a request needing *several* sequential actions from *one* specialist — that shape is closer to Lesson 1's own **plan-and-execute** control-flow pattern (already defined there in full) running *inside* a single specialist's own turn, with the supervisor's routing decision happening only once, up front. Both framings agree completely on one point, which is also the one this document treats as confirmed rather than speculative: a validator (whatever it's called) sits structurally apart from whichever agent actually drafted or took the action.

**The explicit trade-off against a single monolithic agent handling everything.** A monolithic design — one model, one call, drafts the reply *and* decides whether to send it — is simpler to build, has no 1.8-second three-call latency floor (Step 2), and avoids the coordination cost of defining who routes what to whom. But it fails exactly the independence argument this Sidebar makes: the same context window, the same training-data blind spots, and the same prompt framing that produced a wrong answer are also what the model would use to "check" that same answer — which is exactly why this capstone's teaching point is a distinct role, not a second question tacked onto the first model's own turn. The three-role design pays a real latency and infrastructure cost (Step 2's 2x floor, three services to deploy and keep healthy instead of one — Lesson 7's own Concept 1 series-availability math, referenced not re-derived, applies directly: three services chained in series, each independently as reliable as a single monolith, is *less* available than the monolith absent redundancy) specifically to buy the independence a monolithic design structurally cannot offer.

**A supervisor-routing and validator-check pseudocode sketch, this document's own construction, in the same style as Lesson 8's Hands-On Walkthrough:**

```python
SPECIALISTS = {"billing": billing_specialist, "returns": returns_specialist, "subscription": subscription_specialist}

def handle_support_turn(session, customer_message):
    # Supervisor: routing only -- no drafting, no action-taking
    intent = supervisor_classify(customer_message, session.context_summary)
    specialist = SPECIALISTS[intent]

    # Specialist: drafts a reply and/or a proposed action, using both data
    # sources from Step 3 -- per-customer context and shared policy knowledge
    draft = specialist.propose(customer_message, session.per_customer_context, policy_kb.retrieve(intent))

    if draft.proposed_action is None:
        return draft.reply_text  # pure Q&A turn -- no state-changing action to validate

    # Validator: a SEPARATE call, never sees the specialist's own reasoning trace,
    # only the proposed action plus the policy/context it needs to check it against
    verdict = validator_check(draft.proposed_action, session.per_customer_context, policy_kb.retrieve(intent))

    if verdict.approved:
        execute(draft.proposed_action)
        return draft.reply_text
    else:
        return escalate_to_human(session, draft.proposed_action, verdict.reason_code)
```

A proposed-action schema and the validator's own verdict schema, both schema-constrained per Lesson 8's F4 (referenced, not re-derived — the mechanism this validator call would actually use):

```json
{
  "name": "propose_refund",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "ticket_id": {"type": "string"},
      "customer_id": {"type": "string"},
      "refund_amount_cents": {"type": "integer", "minimum": 0},
      "reason_code": {"type": "string"}
    },
    "required": ["ticket_id", "customer_id", "refund_amount_cents", "reason_code"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "validator_verdict",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "approved": {"type": "boolean"},
      "reason_code": {"type": "string"},
      "policy_citation": {"type": "string"}
    },
    "required": ["approved", "reason_code", "policy_citation"],
    "additionalProperties": false
  }
}
```

`policy_citation` on the verdict schema is a deliberate design choice, not a filler field: it forces the validator's own output to name *which* policy rule it checked the proposed `refund_amount_cents` against, which is what makes a rejected (or approved) verdict auditable after the fact rather than a bare yes/no with no trace of the reasoning behind it.

**Trade-offs considered:** Routing by domain (billing vs. returns vs. subscription) up front, Sierra's own apparent framing, is simpler to reason about and lets each specialist's prompt and fine-tuning stay narrowly scoped — but it assumes a request maps cleanly onto one domain, which breaks down for a request that's genuinely both (a subscription cancellation that also needs a prorated refund); a planner-style decomposition (this third-party framing) handles that case more naturally by not committing to a single specialist up front, at the cost of the extra planning step's own latency and failure surface. Keeping the validator's call structurally separate from the specialist's (never sharing the specialist's reasoning trace, only its proposed action) is what buys the independence this Sidebar argues for, but it also means the validator has to re-retrieve whatever policy/context it needs on its own (Step 3's shared and per-customer data both get fetched twice, once per role) rather than reusing the specialist's own retrieval — a real, duplicated cost paid specifically to avoid the correlated-blind-spot risk a shared context would reintroduce.

---

## Step 5: Serving Architecture

**Request flow at serving time.** Client (chat UI) → load balancer/gateway (Lesson 4's Concept 3, **L7** content-based routing, referenced not re-derived: the supervisor's classification result is exactly the kind of request-content-dependent signal L7 routing exists to act on, directing a billing-intent request to the billing-specialist pool and a returns-intent request to a different pool) → supervisor service → the routed specialist-pool replica → validator service → execute-or-escalate → response streamed back to the client over the same Server-Sent Events wire format Lesson 10's Concept 3 already defines in full (referenced, not re-derived), so the customer sees tokens arrive progressively rather than waiting for the full three-call sequence (Step 2's 1.8-second floor) to finish silently.

**Delivering on Lesson 4's own forward reference — quoted exactly, then built out concretely.** Lesson 4's Concept 2 (CDN) states directly: *"capstone #12 (`solutions/multi-agent-customer-support`) — its subject is a customer-support platform (grounded in the Sierra/Klarna case studies), which directly implies a large, distributed, external user base, exactly the kind of audience that makes a CDN worth having in front of its chat UI's static front-end assets (not its multi-agent orchestration logic). Worth being precise about the boundary: capstone #12's own write-up and sourcing is about multi-agent orchestration and hand-off design, not about its UI's asset delivery — this pointer connects to that capstone's necessary-but-unwritten-about front-end, not to its documented core lesson."* This is that front-end, made concrete, with its own numbers (deliberately different from Lesson 4's own 10,000-requests/day worked example, to extend rather than repeat it):

Klarna's own disclosed 23-markets, 35-plus-languages footprint (Step 1) is exactly the "large, distributed, external user base" Lesson 4's own pointer names — a chat widget's JS bundle, CSS, and logo assets are the same bytes for a customer in one market as another, and serving them from a nearby edge node rather than a single origin is a pure win with no correctness question attached (unlike the orchestration logic above it, which genuinely can't be cached this way). Using Step 2's own 76,667 AI-handled conversations/day as the base rate, and an illustrative 6 static assets fetched per fresh chat-widget load (JS bundle, stylesheet, two logo/icon images, a web font, and a small config file):

```
daily_static_asset_requests = ai_handled_per_day × assets_per_load
                             = 76,667 × 6
                             ≈ 460,000 requests/day

illustrative cache_hit_ratio = 97%   (deliberately different from Lesson 4's own 95% example)

hits  = 460,000 × 0.97 = 446,200 requests/day served from edge cache
misses = 460,000 × 0.03 =  13,800 requests/day falling through to origin

origin_load_reduction = (460,000 - 13,800) / 460,000 = 97%
```

A pull CDN (Lesson 4's own full definition, referenced not re-derived) in front of these assets cuts the origin server's load for them by 97% directly — and, per Lesson 4's own "why model weights are a poor CDN fit" argument (referenced not re-derived), this is precisely where a CDN belongs in this capstone's architecture and precisely where it doesn't: the chat widget's static bytes are a textbook CDN fit, while the supervisor/specialist/validator calls above them are not static content at all and have no CDN-cacheable shape, confirming the boundary Lesson 4's own pointer was careful to draw.

**Multi-tenant serving — Sierra as a platform serving many customers like Klarna, not just Klarna.** Per Lesson 8's own F5 Concept (multi-tenant isolation, referenced not re-derived: the silo/pool/bridge models), a platform like Sierra necessarily serves many enterprise tenants from shared infrastructure — Klarna is one tenant among presumably many. Whether each tenant's per-customer context store (Step 3) and specialist/validator configuration is siloed, pooled, or bridged is exactly the question F5 already answers in general; this capstone doesn't re-derive that model, only notes that the Step 3 context store's own sensitivity (real billing and account data) makes it the layer where F5's own stakes are highest in this specific architecture.

**Series-availability math, reused directly rather than re-derived.** Lesson 7's own Concept 1 worked example, confirmed there and in Checkpoint 7's own Question 1, computes exactly this capstone's own three-service chain: a supervisor, a specialist, and a validator, each independently 99.9% available, chained in series, combine to **99.7003%** available (≈26.3 hours/year downtime) — worse than a single 99.9% monolith, not better — unless each service is also made redundant (an active-active pair per service, 99.9999% each), which brings the chain to **≈99.9997%** available (≈1.6 minutes/year) at the cost of **six total replicas** instead of one. This document reuses that figure directly rather than recomputing it, per this repo's own standing discipline of not inventing a second, conflicting number for the same system.

**Trade-offs considered:** Validating synchronously, in-line, before any action executes (this capstone's own design, Step 4) guarantees nothing unchecked ever reaches the customer, at the direct cost of Step 2's 1.8-second latency floor on every action-taking turn. An async alternative — let the specialist's action execute immediately, and validate (or audit) it afterward, rolling back if the validator later disagrees — would remove that latency floor entirely, at the cost of a real window during which an unchecked action has already taken effect (a refund already sent, a subscription already cancelled) before any check ran at all; for a reversible, low-stakes action this trade might be worth taking, but for anything resembling Klarna's own named categories (refunds, disputes, cancellations — all involve real money or a real commitment), the synchronous design's latency cost is the one this capstone treats as worth paying, consistent with this capstone's teaching point of preventing a bad action from reaching the customer, not catching it afterward.

---

## Step 6: Evaluation, Monitoring, and Iteration

**This capstone's central teaching point is validator/guardrail agents as a distinct role, so one bad tool call doesn't reach the customer unchecked — and the numbers below are this document's own worked illustration of exactly why that role earns its cost. Every rate below (bad-action rate, catch rate, per-call token counts) is illustrative, invented for this calculation; only the ≈30,667-actions/day anchor is derived from Klarna's own disclosed scale (Step 2), not from any disclosed Sierra/Klarna error or catch-rate figure, because none exists in the sources available to this document.**

**Sizing the daily validated-action volume.** Not every one of Step 2's 76,667 daily AI-handled conversations involves a state-changing action a validator needs to check — a pure informational question ("when is my next payment due?") has nothing to validate. Taking an illustrative 40% of conversations as involving at least one proposed action (a refund, a cancellation, a subscription change):

```
validated_actions_per_day = 76,667 × 0.40 = 30,666.8 ≈ 30,667 actions/day
```

**The catch-rate calculation.**

```
illustrative_bad_action_rate = 0.03     (3% of proposed actions are wrong or policy-violating)
illustrative_validator_catch_rate = 0.90 (validator correctly blocks 90% of actually-bad actions)

bad_actions_if_unchecked = 30,667 × 0.03 = 920.01 ≈ 920 bad actions/day

caught_by_validator      = 920 × 0.90 = 828 bad actions/day blocked before reaching the customer
residual_reaching_customer = 920 × (1 - 0.90) = 92 bad actions/day

reduction_ratio = 920 / 92 = 10x
```

A 90% catch rate turns 920 potential bad actions a day into 92 that actually reach the customer unchecked — a 10x reduction, at the real cost of the validator's own compute.

**The cost side — using the same $3/1M-input, $15/1M-output illustrative pricing anchor Lessons 7 and 8 already establish, for direct comparability rather than a new assumption:**

```
cost_per_validation_call = (300 / 1,000,000) × $3   +   (20 / 1,000,000) × $15
                          = $0.0009 + $0.0003
                          = $0.0012

total_validator_cost_per_day = 30,667 × $0.0012 = $36.80/day

cost_per_bad_action_actually_prevented = $36.80 / 828 ≈ $0.044   (about 4.4 cents)
```

**Why this number matters, even granting every assumption above is wrong by a wide margin.** $0.044 to catch one bad action before it reaches a customer is cheap against almost any plausible cost of the alternative — even a deliberately conservative illustrative estimate of $5 as the average cost of one bad action reaching a customer unchecked (a wrong refund amount, the support time to find and reverse it, the dent to the satisfaction score Step 1 cares about) puts the daily numbers at:

```
cost_of_bad_actions_prevented = 828 × $5 = $4,140/day
validator_cost                = $36.80/day

net_benefit_ratio = $4,140 / $36.80 ≈ 112x
```

This is this document's own illustrative argument, not a sourced one, for exactly the same reason capstone #13's own compounding-error math is presented as "not deriving the real figure, only showing why a number in this rough range is unsurprising" — the point isn't that $0.044 or 112x are real numbers Sierra or Klarna would report, it's that the validator's own cost is small enough, relative to almost any non-trivial estimate of what an uncaught bad action costs, that the real design question isn't "is a validator worth it" but "how high can the catch rate realistically go, and what happens when it's wrong."

**Failure modes — the validator can be wrong in two directions, not just one.** A **false negative** (the validator approves an action that was actually bad) is the failure this capstone's architecture is centrally worried about — exactly the residual 92/day above, the cases this whole architecture exists to shrink. A **false positive** (the validator blocks an action that was actually fine) is the opposite, quieter failure: it doesn't let anything wrong through, but it directly hurts the resolution rate Step 1 also cares about, by forcing an unnecessary escalation for a correct action. Tuning the validator to catch more (raising recall on the bad-action class) tends to also raise false positives (lowering precision on the good-action class) — the same precision/recall trade-off capstone #5/#11's own AUPRC discussion already names in a different setting (referenced, not re-derived), applied here to validation decisions instead of content-moderation labels.

**A correlated-failure risk worth naming explicitly, as this document's own reasoned inference rather than a sourced claim about Sierra specifically.** If the specialist and the validator are drawn from the same underlying model family (plausible, given Sierra's own confirmed "15+ frontier, open-weight, and proprietary models" pool, which could assign the same family to both roles for a given task), a shared training-data blind spot could make the validator *miss exactly the class of mistake the specialist is most prone to* — the same risk Lesson 9's own cited LLM-as-judge finding (Zheng et al.: a judge can favor its own family's style) already confirms in a sibling setting, extended here as an inference, not a confirmed Sierra-specific fact. The mitigation this document's own architecture (Step 4) already provides a partial answer to: the validator's verdict schema requires a `policy_citation`, forcing at least part of its check to be grounded in an explicit, checkable policy reference rather than a free-floating judgment call that a shared blind spot could corrupt silently in both roles at once — a real, if partial, defense, not a complete one.

**The feedback loop.** Every escalated or validator-rejected case is exactly the input a real deployment would route back into Step 3's policy knowledge base (a recurring rejection reason that turns out to be a policy-interpretation gap, not an actual error) and Step 4's specialist prompting (a specialist that keeps proposing an action the validator keeps correctly blocking is a sign that specialist's own training or prompt needs correcting, not that the validator is being overly strict) — the same "route real production failures back into the thing that needs fixing" shape capstone #9's and capstone #13's own Step 6 feedback loops already follow, applied here to validator rejections instead of a retrieval eval set or a stalled coding-agent session.

**What to monitor in production:** resolution rate and escalation rate (Step 1), tracked separately because a *rising* escalation rate could mean either "the validator is catching more real problems" (good) or "the specialists are getting worse" (bad) — the two need to be told apart, not blended into one number; validator catch-rate itself, which (per the correlated-failure risk above) can only be estimated via some form of targeted human audit of validator-approved actions, the same "stratified, not random" auditing discipline capstone #5/#11's own confirmed methodology already establishes for a structurally similar rare-event detection problem (referenced as a real precedent, not re-derived); and per-specialist-domain error rate, since a rising error rate isolated to one specialist (billing, say) points at a narrower fix than a platform-wide one.

**Trade-offs considered:** Auto-executing every validator-approved action with no further human spot-check scales cleanly to Klarna's own disclosed volume, but means a validator blind spot (the correlated-failure risk above) could run unnoticed indefinitely — there's no independent check on the independent check. Sampling a fraction of validator-approved actions for human audit (mirroring, not re-deriving, capstone #5/#11's own stratified-auditing precedent) catches that blind spot, but costs real, ongoing human review time that scales with platform volume, the same recurring-cost-vs.-one-time-investment trade Lesson 9's own prompt-versioning Concept already names in a different setting. Neither extreme is correct in general — how much audit sampling is worth paying for depends on how costly a residual bad action actually is in a given domain (Step 6's own illustrative $5-per-bad-action floor would justify far more audit spend than a domain where a bad action is nearly free to reverse), which is a business decision this capstone's own architecture doesn't make for it, the same honest limitation capstone #13's own Step 6 names for its auto-merge-vs-human-review question.

---

## Source(s) and Further Reading

- Sierra AI, *"Constellation of models: the architecture powering Sierra's agents"* (sierra.ai/blog/constellation-of-models, Dec. 3, 2025) — **primary** (Sierra's own blog), but confirmed by direct fetch to be a non-technical, marketing-level overview: no named models or providers, no latency/accuracy/uptime figures, no architecture diagram. Source of the "15+ frontier, open-weight, and proprietary models," "task-specific evaluations," and "supervisors... enforce guardrails, policies, and quality checks" claims used in Step 4.
- Atlan, *"What Is Sierra? The AI Agent Platform for Customer Service"* (atlan.com) — **secondary**; confirmed by direct fetch. Flagged throughout for Atlan's own commercial interest in portraying vendor-built context layers (like Sierra's Agent Data Platform) as risky, since Atlan sells a competing product. Source of the Agent Data Platform/Context Engine framing used in Step 3.
- Third-party technical coverage describing a "planner/executor/validator" characterization of Sierra's "Constellation architecture" — **secondary**; this vocabulary is commonly associated with a Cybernews review, but a direct fetch of the live Cybernews page returned HTTP 403 on repeated attempts, and an independent search found the exact terminology more directly in other third-party write-ups (e.g. an Oboe interview-prep study guide, a separate blog's "$500 refund" example) than in any verifiable Cybernews text — so this document could not confirm Cybernews specifically as the originating source, and names the attribution only as "third-party coverage" rather than standing behind an unconfirmed specific source, per Step 4's own honest framing of that limitation.
- RuntimeWire's coverage of Sierra's Context Engine announcement (tied to Sierra's "Horizon" platform) — **secondary**; confirmed by direct fetch to discuss Context Engine and Horizon only — it does not mention "Agent Data Platform" by name, so that specific framing used in Step 3 is credited to Atlan above, not to RuntimeWire. Used in Step 3 for the cross-channel/cross-system unification framing, itself substantially built on Sierra's own announcement text.
- OpenAI's customer story on Klarna (`openai.com/customer-stories/klarna`) — **could not be fetched directly** (HTTP 403 on two URL variants; the Wayback Machine was unreachable in this environment). Every Klarna figure in this document (2.3M conversations/month, two-thirds of chat volume, ~700 FTE-equivalent, 11-to-2-minute resolution time, 23 markets, 35+ languages, ~$40M 2024 profit improvement, satisfaction parity with human agents) is corroborated across independent press coverage of the same disclosed announcement — CX Today, Silicon Canals, and VKTR — all of which attribute every figure to Klarna's own statements, not to an independent audit.
- Lesson 1 (`lessons/lesson-1-ai-fundamentals-refresher.md`), Concepts D2 (control-flow patterns — plan-and-execute, reflection), D5 (multi-agent orchestration), and E2 (long-term memory) — referenced throughout rather than re-derived; this capstone is D5's own named example.
- Lesson 3 (`lessons/lesson-3-scalability-and-availability.md`), Concept 2 (CAP theorem/consistency, applied to per-customer context freshness in Step 3) and Concept 3 (availability math, reused directly in Step 5).
- Lesson 4 (`lessons/lesson-4-network-and-delivery.md`), Concept 2 (CDN) — the exact forward reference this document's Step 5 quotes and resolves — and Concept 3 (L7 load balancing, applied to supervisor-routed traffic).
- Lesson 5 (`lessons/lesson-5-data-layer.md`), Concept 2 — the KV/wide-column storage shape underlying the per-customer context record in Step 3, referenced not re-derived.
- Lesson 7 (`lessons/lesson-7-application-architecture-and-security.md`), Concept 1 (blast radius, SRP, and the series-availability worked example this document's Step 5 reuses directly, confirmed also in Checkpoint 7's own Question 1) and Concept 4 (the $3/1M-input, $15/1M-output illustrative pricing anchor reused in Step 6).
- Lesson 8 (`lessons/lesson-8-safety-and-isolation.md`), Concept 4 (guardrails and output validation — the mechanism-level cousin of this capstone's validator-agent Sidebar, deliberately not duplicated) and Concept 5 (multi-tenant isolation, referenced in Step 5).
- Lesson 9 (`lessons/lesson-9-evaluation-and-observability.md`), Concept 2 — the LLM-as-judge definition and Zheng et al.'s own documented judge-model biases, the basis for this document's own reasoned inference about correlated specialist/validator failure risk in Step 6.
- Lesson 10 (`lessons/lesson-10-production-scaling.md`), Concept 3 — the Server-Sent Events streaming format this capstone's Step 5 serving architecture is built on top of, referenced not re-derived.
- `solutions/rag-contextual-retrieval/README.md` (capstone #9) and `solutions/autonomous-coding-agent/README.md` (capstone #13) — structural precedent for this document's own feedback-loop framing (Step 6) and its honest "this number is illustrative, flagged as such" discipline throughout.
- `solutions/harmful-content-detection/README.md` (capstones #5/#11) — precedent for this document's stratified-auditing reference in Step 6 and its repeated, not single-disclaimer, flagging of sourced-vs-extrapolated content throughout.
- `appendix/glossary.md` — new entries added for **Little's Law** and **validator/guardrail agent (and validator catch-rate)**; both are defined in full on first use above rather than assumed familiar.
