# Checkpoint 9: Evaluation and Observability

## Purpose

This checkpoint verifies you can explain why exact-match assertions fail for LLM output and compute a false-failure rate for one, define golden datasets/LLM-as-judge/regression suites and resolve capstone #9's own forward reference for generation-quality evaluation, define trace/span and compute the storage cost of tracing an agent fleet, and define prompt versioning/A/B testing/rollback and run a two-proportion significance check before trusting a pass-rate improvement.

## Verification Questions

Try to answer each before revealing it.

<details>
<summary>Question 1 (G1 — Why you can't unit-test an LLM): Why does an ordinary `assert actual == expected` unit test fail as a tool for checking LLM-generated text, building on Lesson 1's Concept A1 rather than re-deriving non-determinism from scratch? Using this lesson's own illustrative figures (an 8/50 exact-match rate against one correct answer's phrasing, run across 40 unrelated commits), how many false failures would you expect?</summary>

**Answer:** Lesson 1's Concept A1 already names non-determinism — the same prompt against the same model can produce different outputs because the model samples from a probability distribution over next tokens, not always the single most likely one. A plain assertion assumes "same input, same output," which non-determinism breaks on its own. This lesson's Concept 1 adds a second, independent reason even deterministic output would still break an assertion: semantic equivalence — many different strings ("New hires get 15 PTO days" vs. "New employees accrue 15 days of paid time off in year one") can both be fully correct, and an exact-match check has no way to recognize that. The computation: `exact_match_rate = 8/50 = 0.16`; `expected_false_failures = 40 × (1 − 0.16) = 40 × 0.84 = 33.6 ≈ 34` false failures out of 40 commits that didn't even touch the feature being tested.

**Why this matters:** A test that fails on roughly 34 of 40 unrelated commits isn't a signal anyone can act on — it's exactly why evals (scored across many examples, tolerant of correct-but-differently-phrased output) replace single hardcoded assertions for freeform generation, while assertions remain the right tool for the genuinely structured parts of the same system (e.g. Lesson 8's schema-constrained tool calls).
</details>

<details>
<summary>Question 2 (G2 — Offline evaluation, part 1): What is a golden dataset, what is LLM-as-judge, and what specific forward reference from capstone #9 does this Concept resolve? What confirmed figure does Zheng et al.'s MT-Bench paper report for how often a GPT-4 judge agrees with human preference judgments?</summary>

**Answer:** A golden dataset is a fixed, curated set of input examples paired with hand-verified correct outputs, used to measure a pass *rate* across many cases rather than a single assertion. LLM-as-judge is using a separate LLM call, guided by a written rubric (e.g. faithfulness, relevance), to score a candidate output's quality — recognizing that two differently-worded answers can both satisfy the rubric, which a fixed-string assertion can't do. This Concept resolves capstone #9's own Scope note, which explicitly deferred "generation-quality evaluation of the final answer" to "Lesson 9's territory, G1-G2" — distinct from that capstone's own `recall@20` retrieval metric, which it evaluates itself. Zheng et al. (arXiv:2306.05685) confirms GPT-4-as-judge agrees with human preference judgments **more than 80% of the time — roughly the same level of agreement human raters have with each other** — while also documenting real judge biases (position, verbosity, self-enhancement) that a rubric has to guard against.

**Why this matters:** Without this confirmed figure, "just have a model grade the output" would be an unverified shortcut; with it, LLM-as-judge is a technique with real, measured validity (and known, named failure modes to design around), not a guess.
</details>

<details>
<summary>Question 3 (G2 — Offline evaluation, part 2): Using this lesson's own worked numbers — a `v12` baseline pass rate of 129/150 and a candidate `v14` pass rate of 102/150, with a 5-percentage-point maximum allowed drop — does the regression suite allow `v14` to ship? Show the computation. Separately, what makes capstone #13's SWE-bench offline eval a genuinely different shape of golden-dataset grading than this Concept's LLM-as-judge approach?</summary>

**Answer:** `v12` pass rate = 129/150 = 0.8600 (86.0%); `v14` pass rate = 102/150 = 0.6800 (68.0%); `drop_pct = (0.86 − 0.68) × 100 = 18.0` percentage points. Since `18.0 > 5` (the allowed threshold), the regression suite blocks `v14` from shipping. SWE-bench (capstone #13, Step 6) grades a code patch with a fully deterministic criterion — previously-failing tests now pass, previously-passing tests stay passing — because a patch's correctness has an objective, checkable definition. A free-text RAG answer has no single correct string, so it needs the softer, judgment-based grading this Concept's LLM-as-judge approach provides instead — the two capstones sit at opposite ends of the same offline-eval spectrum.

**Why this matters:** A regression suite only protects a shipped feature if its gate threshold is actually enforced automatically on every candidate change — an 18-point drop is exactly the kind of regression a golden dataset plus a hard gate catches before it reaches real users, which neither a single assertion (Concept 1) nor an un-gated "looks fine to me" review would reliably catch.
</details>

<details>
<summary>Question 4 (G3 — Online observability): Define trace and span in full, and explain how they let you localize a failure inside a multi-step agent run that a single pass/fail signal at the end can't. Using this lesson's own figures (3,000 sessions/day, 200 spans/session, 2 KB/span), what's the storage cost per day at full tracing, and at 10% sampling?</summary>

**Answer:** A trace is the complete record of one end-to-end operation (here, one agent session, start to finish). A span is one discrete unit of work inside that trace (one LLM reasoning call, one tool call), each with its own start/end time, inputs, outputs, and metadata, and a `parent_span_id` linking it to the span that triggered it — which is what reconstructs the full call tree of a session rather than a flat, unordered event list. This directly addresses capstone #13's own named failure mode — "an agent going off-track for an hour before anyone notices" — because a trace lets an engineer see exactly which step in a long chain first went wrong, instead of only knowing the final outcome was bad. The computation: `spans_per_day = 3,000 × 200 = 600,000`; `full_trace_storage_gb_per_day = (600,000 × 2) / 1,000,000 = 1.2 GB/day`; at 10% sampling, `0.12 GB/day`.

**Why this matters:** Observability isn't free — the 10x storage reduction from sampling is a real, computed trade-off against not having a full trace available for 90% of sessions, which is exactly why a real deployment usually combines sampling with a rule that always captures a full trace for any session that trips an error or stall-detection signal, rather than sampling uniformly at random.
</details>

<details>
<summary>Question 5 (G4 — Prompt versioning and A/B testing): What does it mean to treat a prompt as a deployable artifact, and what does a rollback pointer actually require to work at all? Using this lesson's own `v12` (129/150) vs. `v13` (136/150) golden-set pass rates, compute the two-proportion z-score — is `v13`'s apparent improvement statistically significant at the conventional 0.05 threshold?</summary>

**Answer:** Treating a prompt as a deployable artifact means its exact text gets its own stable version identifier (e.g. a content hash) and change history, the same way a compiled binary does — not just "whatever the file currently contains." A rollback pointer (`rollback_to: "v12"`) only works because the previous version's text was kept as a separate, retrievable artifact rather than being overwritten the moment a new version was authored. The computation: `p1 = 129/150 = 0.86`, `p2 = 136/150 = 0.9067`, `pooled_p = 265/300 = 0.8833`, `standard_error = sqrt(0.8833 × 0.1167 × (1/150 + 1/150)) ≈ 0.0371`, `z = (0.9067 − 0.86)/0.0371 ≈ 1.26`. A z-score of 1.26 corresponds to a two-tailed p-value of roughly 0.21, well above the conventional 0.05 threshold (which needs `|z|` past ≈1.96) — so `v13`'s apparent improvement is **not** statistically significant at this sample size.

**Why this matters:** Shipping `v13` to 100% of traffic on the strength of the raw 4.67-point pass-rate bump alone would be shipping noise as if it were a real improvement — which is exactly why this lesson's own prompt-version config keeps `v13` at a cautious 10% canary with `v12` as a ready rollback target, rather than a full rollout, until a larger golden set or real production signal (Concept 3's tracing) confirms the lift is real.
</details>

## Hands-On Self-Check

There's no single CLI spanning this whole lesson — confirm you can do each of the following, without looking back at it:

- [ ] I can state, from memory, why an exact-match assertion fails for LLM-generated text (both non-determinism and semantic equivalence), and I can compute `expected_false_failures` given any `unrelated_commits` and `exact_match_rate` of my own choosing.
- [ ] I can define golden dataset, LLM-as-judge, and regression suite in my own words, name the confirmed MT-Bench agreement figure (over 80%, matching human-human agreement), and explain exactly which gap in capstone #9's own Scope note this Concept closes.
- [ ] I can run (or reason through) `regression_gate` given a fresh baseline/candidate pass-rate pair and confirm it correctly blocks a drop past the threshold and allows an improvement through.
- [ ] I can define trace and span in my own words, explain what a `parent_span_id` reconstructs, and compute `trace_storage_gb_per_day` given any `sessions_per_day`, `spans_per_session`, `kb_per_span`, and `sampling_rate` combination of my own choosing.
- [ ] I can define deployable artifact, prompt versioning, A/B testing, and rollback in my own words, and compute `ab_test_z_score` given any two pass-count/sample-size pairs, stating whether the resulting z-score clears the conventional 1.96 significance threshold.
- [ ] I can name which already-written capstone (#9, #10, #13, or #15) each of this lesson's four Concepts connects to, including the one Concept (G2) that resolves a forward reference capstone #9 already made by name to "Lesson 9, G1-G2" before this lesson existed.

## Next Step

Move to **Lesson 10: Production Scaling**.
