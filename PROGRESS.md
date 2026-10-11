# Implementation Progress — `ai-system-design-primer`

Tracks execution of `plan.md` §8's build order, phase by phase. Check items off as they're actually written and verified against §7's depth bar — not just drafted.

---

## Phase 1 — Lesson 1 first, fast ✅ DONE
**Goal:** get the compressed refresher out of the way before the real work starts. Lighter template per §4/§5 exceptions — no full depth bar.
- [x] `lessons/lesson-1-ai-fundamentals-refresher.md` (old Groups A–E, 21 sub-topics, light-touch) — Writer → Reviewer (6 findings, "needs minor fixes") → Rewriter, all applied
- [x] `checkpoints/checkpoint-1-ai-fundamentals.md` — same pipeline; question coverage rebalanced to one per group (A–E)

## Phase 2 — Core system design, part 1: resource/availability layer ✅ DONE
**Goal:** prove Lessons 3–7's case-study-pointer requirement (§7) actually works before writing the remaining three.
- [x] `lessons/lesson-3-scalability-and-availability.md` (Group I) — Writer → Reviewer (capstone-numbering bug + 1 arithmetic error found) → Rewriter, both fixed
- [x] `checkpoints/checkpoint-3-scalability-and-availability.md` — reviewed, no fixes needed
- [x] `lessons/lesson-4-network-and-delivery.md` (Group J) — Writer → Reviewer (6 findings, incl. a DNS-worst-case logic error + CDN capstone retarget) → Rewriter, all fixed
- [x] `checkpoints/checkpoint-4-network-and-delivery.md` — Q4 swapped (session persistence → SSL/TLS termination) to close an actual zero-coverage gap
- [x] `solutions/llm-api-gateway/README.md` (capstone #15) — Writer → Reviewer (arithmetic error + missing code artifact + 4 smaller findings) → Rewriter, all fixed
- [x] `solutions/llm-inference-serving/README.md` (capstone #10) — Writer → Reviewer (clean pass, 1 stale-note fix) → Rewriter

## Phase 3 — Core system design, part 2: data/communication layer ✅ DONE
- [x] `lessons/lesson-5-data-layer.md` (Group K) — Writer → Reviewer (1 major: shard-key mismatch between DDL and Python snippet, + 3 minor sourcing nits) → Rewriter, all fixed
- [x] `checkpoints/checkpoint-5-data-layer.md` — reviewed, no fixes needed
- [x] `lessons/lesson-6-async-and-communication.md` (Group L) — Writer caught a stale §3 capstone pairing (#4/#13 → #13 only) and a live uncorrected "capstone #2" bug in Lesson 1 (fixed directly, #2→#15) → Reviewer (4 sourcing/attribution findings) → Rewriter, all fixed
- [x] `checkpoints/checkpoint-6-async-and-communication.md` — reviewed, no fixes needed
- [x] `lessons/lesson-7-application-architecture-and-security.md` (Group M) — Writer crashed on rate limit after finishing the lesson (checkpoint done by a resumed fresh instance) → Reviewer (3 findings: missing "blast radius" definition, misattributed TLS back-reference, overstated Consul/IAM link) → Rewriter, all fixed
- [x] `checkpoints/checkpoint-7-application-architecture-and-security.md` — written from completed lesson content, reviewed (spot-checked grounding), no fixes needed
- [x] `solutions/visual-search/README.md` (capstone #1) — Writer fetched/verified real Pinterest paper (arXiv:1908.01707), added 2 glossary entries → Reviewer (4 findings: modulo/consistent-hashing self-contradiction + 3 overclaimed paper attributions) → Rewriter, all fixed
- [x] `solutions/rag-contextual-retrieval/README.md` (capstone #9) — Writer fetched/verified real Anthropic post (all source-confirmed figures held up) → Reviewer (3 findings: schema dropped fields its own prose promised, unjustified shard count, misattributed cross-reference) → Rewriter, all fixed
- [x] `solutions/autonomous-coding-agent/README.md` (capstone #13) — Writer fetched/verified real Cognition Labs post + SWE-bench paper (all source-confirmed figures held up, incl. asterisked caveats) → Reviewer verdict: ready as-is, no fixes needed

## Phase 4 — Lessons 8–10 (unchanged scope) ✅ DONE
- [x] `lessons/lesson-8-safety-and-isolation.md` (Group F) — F2 cross-links to `learn-docker-ai-agents` Lesson 1 (verbatim-verified); Writer resolved forward-references already planted in capstones #9/#13/#15 → Reviewer verdict: ready as-is, no fixes needed
- [x] `checkpoints/checkpoint-8-safety.md` — 1 question per concept (F1-F5), verified, no fixes needed
- [x] `lessons/lesson-9-evaluation-and-observability.md` (Group G) — resolved forward-refs from Lesson 1/capstone #9 → Reviewer (2 findings: false "never mentions prompts" claim + formula misattribution) → Rewriter, both fixed
- [x] `checkpoints/checkpoint-9-evaluation.md` — 5 questions (G2 doubled), verified, no fixes needed
- [x] `lessons/lesson-10-production-scaling.md` (Group H) — Writer self-caught 2 arithmetic bugs before handback; resolved forward-refs from Lesson 1 → Reviewer (4 findings: misattributed capstone step, incomplete capstone enumeration, internal inconsistency, minor concept-list gap) → Rewriter, all fixed
- [x] `checkpoints/checkpoint-10-scaling.md` — 5 questions (H1 doubled), fixed alongside the lesson

## Phase 5 — Remaining `solutions/*` catalog entries ✅ DONE
Capstones #3–4, #6–8 (Track 1) and #5/#11, #12, #14 (Track 2/3) — see `plan.md` §6.2 for the full list and sourcing notes.
- [x] `solutions/visual-search/README.md` — already covered in Phase 3
- [x] `solutions/ctr-prediction/README.md` (Track 1 capstone #2) — Writer fetched/verified real McMahan et al. paper in full (incl. the feature-hashing-rejection catch) → Reviewer (5 findings: imprecise accuracy claim, missing CTR definition, unexpanded ROC, missing illustrative tag, confusing naming) → Rewriter, all fixed
- [x] `solutions/video-recommendation/README.md` (Track 1 capstone #3, YouTube) — Writer fetched/verified real Covington et al. paper in full → Reviewer (4 findings: backward terminology claim, unfulfilled depth-bar promise, overstated ANN claim, 2 silently-corrected typo'd quotes) → Rewriter, all fixed
- [x] `solutions/airbnb-search-ranking/README.md` (Track 1 capstone #4) — Writer fetched/verified real Haldar et al. paper in full (5-stage architecture confirmed), carefully hedged negative claims → Reviewer (4 findings: 2 misquotes, 1 overclaimed attribution, 1 downstream cache-pattern mismatch) → Rewriter, all fixed
- [x] `solutions/pymk-friend-recommendation/README.md` (Track 1 capstone #6, LinkedIn) — Writer fetched/verified 3 real LinkedIn sources (caught plan.md's own framing error: triangle-closing isn't in the 2020 post, found it on a 3rd page) → Reviewer (1 finding: missing XGBoost definition) → Rewriter, fixed
- [x] `solutions/uber-eta-prediction/README.md` (Track 1 capstone #7) — Writer character-verified the companion arXiv paper directly (blog post URL dead) → Reviewer (5 findings: 2 quote-rule violations incl. 1 real misquote conflating two sentences, overstated access claim, taxonomy mischaracterization, number typo) → Rewriter, all fixed
- [x] `solutions/netflix-feed-ranking/README.md` (Track 1 capstone #8) — Writer character-verified both real Netflix posts via Wayback Machine (caught a plan.md error: posts use RMSE, not MAE — fixed in plan.md §6.2) → Reviewer verdict: ready as-is, 1 optional Step 5 polish applied
- [x] `solutions/harmful-content-detection/README.md` (capstone #5/#11, classic-ML + LLM-era angle combined) — Writer fetched/verified real Markov et al. (OpenAI) paper in full via ar5iv, flagged plan.md's "June 2024" date as wrong (paper is 2022 arXiv/2023 AAAI; June 2024 is only OpenAI's publication-index page date — now corrected in plan.md §6.2 entry #5) → Reviewer (2 minor findings) → Rewriter fixed the README footnote attribution; both fixes applied
- [x] `solutions/multi-agent-customer-support/README.md` (capstone #12 — primary/secondary sourcing caveat made explicit) — Writer fetched/verified real Sierra/Atlan/press sources, honest about Klarna page being unreachable → Reviewer (5 findings: 2 quote errors, 1 misattribution, 1 unconfirmed attribution softened, 1 arithmetic slip) → Rewriter, all fixed
- [x] `solutions/computer-use-agent/README.md` (capstone #14) — Writer fetched/verified real Anthropic announcement + GitHub reference implementation + OSWorld paper → Reviewer (6 findings: 2 misquotes, 2 untagged truncations, 1 overclaimed numeric range, 1 missing acronym expansion, 1 tagging gap) → Rewriter, all fixed. **All 14 §6.2 capstones now written.**

## Phase 6 — Lesson 11 + Checkpoint 11, last, on purpose ✅ DONE
**Goal:** write this only once Phases 1–5 give it something real to point back to (§8's note on why this is sequenced last).
- [x] `lessons/lesson-11-real-world-architectures.md` (Group N) — Writer verified ~40 external entities via WebSearch (17 tools, 10 companies incl. 1 explicitly-flagged-unconfirmable, 13 blogs) → Reviewer (1 finding: wrong Lesson-1 sub-concept citation) → fixed directly
- [x] `checkpoints/checkpoint-11-real-world-architectures.md` (open-ended self-check, per §5 exception) — Reviewer caught a real error inherited from Lesson 11 itself (FAISS/capstone #1 mischaracterized as HNSW/ANN when it's actually exact binary search) → both files fixed together
- [x] `appendix/token-and-latency-numbers.md` — Writer pulled real internal figures from 5 lessons/capstones + verified external pricing/context-window figures live → Reviewer (2 findings: a misapplied ratio, an understated pricing range) → Rewriter, both fixed
- [x] `appendix/glossary.md` — Writer finalized by compiling all 10 lessons' full-definition terms (grew from 38 to 229 entries, reorganized alphabetically) → Reviewer (full audit of 3 lessons + spot-checks: 4 missing terms, 1 inconsistent exclusion, 4 alphabetization slips) → Rewriter, all fixed (236 final entries)

## Phase 8 — Post-build revision: insert Lesson 2 (core system-design fundamentals) ✅ DONE
**Goal:** per user feedback after Phase 7 completed — Lessons 3–7 assumed classic-infra vocabulary (client/server, API, database, cache, etc.) some readers don't have yet. Mirrors Lesson 1's own template exception, one layer down the stack.
- [x] Renumbered every lesson/checkpoint file from 2–10 up to 3–11 (backup taken first: `ai-system-design-primer-backup-*.tar.gz` in the parent directory)
- [x] Updated every textual cross-reference across `plan.md`, `PROGRESS.md`, all lessons/checkpoints, all `solutions/` capstones — including several conjunction/slash-notation forms ("Lessons N and M", "Lesson N/M") a first-pass regex missed, found via targeted re-grep and fixed by hand
- [x] Updated `plan.md` §2/§3/§4/§8 to document the new Lesson 2/Group P structure, the new 11-lesson total, and this revision's own history
- [x] Write `lessons/lesson-2-core-system-design-fundamentals.md` (Group P: P1 client/server & request/response, P2 APIs/protocols at a glance, P3 databases/caches at a glance, P4 latency/throughput/scaling at a glance) — light-touch template per §4 exception, mirroring Lesson 1 → Reviewer (3 findings: 2 bridge-line overclaims, missing glossary terms; also caught that Lesson 1/Checkpoint 1's "Next" pointers still skipped past Lesson 2) → all fixed
- [x] Write `checkpoints/checkpoint-2-core-system-design-fundamentals.md` — same pipeline, same fixes applied
- [x] Re-finalized `appendix/glossary.md` — added Lesson 2's 17 new terms + fixed stale "10 lessons" header (253 total entries)
- [x] Removed all plan.md/PROGRESS.md/draft-process meta-references from lesson, checkpoint, and solutions/ content — 3 parallel batches (capstones #1-7, capstones #8-15, lessons 4-11 + checkpoints 3/6/8/11), ~90 instances removed total, verified clean via repo-wide grep (zero hits for plan.md, PROGRESS.md, Reviewer/Writer/Rewriter, "not yet written," and stray "§N" section-citations)
- [x] Verbosity reduction pass across all 11 lessons (extra focus on Lessons 4/5/6 — network-and-delivery/data-layer/async-and-communication — per explicit user request), markdown spacing fixes, paragraph-to-bullets conversion where it aids clarity — 6 parallel agents, each file re-verified after for intact numeric calculations/code blocks/trade-offs/Source(s)/cross-references and zero remaining markdown-spacing violations. Net effect was mostly narrative-prose tightening and spacing fixes rather than large word-count cuts, since most of each file's length lives in protected content (term-definition tables in Lessons 1-3, Trade-offs/Source(s)/code blocks/worked math everywhere, Lesson 11's N1-N3 tables) that was deliberately left untouched per the full-definitions preference and the hard constraints. Lessons 4/5/6 each got targeted analogies added for their previously terse/jargon-dense spots (DNS resolver chain, L4/L7, reverse proxy/hotel-desk, NoSQL-type analogies, back pressure/Little's Law, TCP handshake/UDP postcard, RPC/REST phone-vs-mail), roughly offsetting their word count even while adding real clarity.

## Phase 7 — Depth-bar pass ✅ DONE
Re-checked everything against `plan.md` §7 via 3 parallel audits:
- [x] Every Lesson 3–6 Concept has a case-study pointer — 18/19 passed; Lesson 3's I2 (CAP theorem) was missing one, fixed (now points to capstone #12)
- [x] Every `solutions/` entry tags each source primary vs. secondary — 14/14 passed clean, no fixes needed
- [x] Every Lesson 11 table row names a Lesson/capstone (N4) — 36/40 passed; 4 N3 blog rows (DeepMind, Meta AI, Hugging Face, W&B) were missing one, fixed (DeepMind honestly left as a general-only connection, no forced match)
- [x] Every term/flag defined in full on first use (feedback-tutorial-depth) — spot-check sample passed; found "p99" used undefined in 7 locations across the repo, all fixed with inline definitions + pointers to Lesson 9's canonical definition
- [x] Every lesson/solution has a numeric calculation + real schema/code + explicit trade-offs + "Source(s) and further reading" — spot-check sample (6 files incl. 2 "higher risk" picks) passed, all ~20+ numeric calculations independently re-derived and correct
- [x] Bonus fix: Lesson 7 had two stale "capstone #12/#13 doesn't exist yet" claims, now resolved with direct quotes from the (now-written) capstones

---

## Open decisions still unresolved (plan.md §9)
These don't block Phase 1, but will need answers before Phase 2 content gets too far:
- [ ] Final repo name (currently `ai-system-design-primer`, placeholder)
- [ ] Confirm cross-link-not-duplicate relationship with `learn-docker-ai-agents` (Lessons 1 & 8's pointers assume this)
- [ ] Which real SDKs are fair game for hands-on snippets in Lessons 3–7 / `solutions/` (e.g. `openai`, a vector DB client)

---

**Status key:** unchecked = not started. Update this file as each item is actually written, not drafted-then-forgotten.
