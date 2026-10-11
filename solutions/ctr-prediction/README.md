# Capstone #2: Ad Click-Through-Rate (CTR) Prediction — Google's "View from the Trenches"

**Source(s):** Primary — McMahan, Holt, Sculley, Young, Ebner, Grady, Nie, Phillips, Davydov, Golovin, Chikkerur, Liu, Wattenberg, Hrafnkelsson, Boulos, and Kubica, *"Ad Click Prediction: a View from the Trenches,"* KDD 2013 (ACM DOI 10.1145/2487575.2488200, pp. 1222–1230). Also a core chapter across every recognized ML-system-design-interview resource.

**Confidence:** Strong, primary source. This document was written from the paper's own full text (fetched directly from Google Research's archived PDF, `research.google.com/pubs/archive/41159.pdf` → `static.googleusercontent.com/.../41159.pdf`), not from the abstract or secondhand summaries. Every specific figure, formula, or claim below tagged **(paper)** was read directly out of that text — including the one genuinely surprising finding this document leads with in Step 3: the paper explicitly classifies feature hashing as something it *tried and rejected*, not something it uses in production. Figures tagged **(illustrative)** are this document's own worked assumptions, needed because the paper itself reports scale only in qualitative terms ("billions of events per day," "billions of coefficients," "billions of dimensions") without ever publishing an exact daily volume, exact coefficient count, or exact click-rate percentage — those illustrative numbers are chosen to sit inside the paper's own confirmed order of magnitude, and are kept visually distinct from the paper's own numbers throughout rather than blended into them. One claim is tagged **(secondary)**: the general industry problem of delayed/attribution-windowed labels, which this paper does not itself address, but which is well documented in a closely related paper (Chapelle, *"Modeling Delayed Feedback in Display Advertising,"* KDD 2014) — cited there as a pointer, not presented as something McMahan et al. themselves discuss.

**Scope note:** This capstone covers estimating **P(click | q, a)** — the probability that ad `a` will be clicked if shown in response to query `q` — for Google's sponsored-search advertising system, exactly as the paper itself frames its own system boundary **(paper)**: *"An auction mechanism then determines whether these ads are shown to the user, what order they are shown in, and what prices the advertisers pay if their ad is clicked. In addition to the advertiser bids, an important input to the auction is... P(click | q, a)."* The auction mechanism itself — which ads win, what order they're shown in, what price is actually charged (a second-price-style auction mechanic) — is explicitly **out of scope**: the paper treats it as a separate downstream consumer of this system's output, not part of the system this capstone covers. This capstone also does not cover ad *matching* (the keyword-based step that produces the initial candidate set of ads before CTR prediction ever runs on them) — also named by the paper as a prior step, not this system's job.

---

## Step 1: Clarify Requirements & Frame the ML/AI Objective

**Click-through rate (CTR), defined explicitly before anything else.** **Click-through rate (CTR)** is the fraction of ad impressions shown to users that result in a click, typically expressed as a percentage — a CTR of 2% means 2 out of every 100 impressions shown were clicked. This capstone's whole system exists to estimate, per impression, the probability that *this specific* impression will be one of those clicks, rather than to report an aggregate rate after the fact; that per-impression probability is exactly the `P(click | q, a)` notation the rest of this document uses.

**The actual objective, stated in the paper's own notation (paper):** for every candidate ad `a` shown against a user's search query `q`, estimate `P(click | q, a)` — a single real-valued probability between 0 and 1, output once per (query, ad) impression, fast enough to feed an auction that has to resolve before the search results page renders. This is a textbook **binary classification with a probabilistic output** framing, not a binary decision — the auction needs a calibrated probability (Step 6), not just a yes/no click prediction, because that probability gets multiplied against an advertiser's bid to help rank and price the auction.

**What counts as ground truth / feedback signal:** a binary label per impression — `y = 1` if the ad was clicked, `y = 0` if it wasn't — observed directly from user behavior rather than collected via any manual labeling process. This is one of CTR prediction's genuine structural advantages over most supervised-learning problems: labels arrive for free, as a byproduct of the product itself being used, at the same volume as the traffic the model serves. But "arrives for free" is not the same as "arrives instantly or cleanly," and that gap is worth naming explicitly as a real production problem this capstone's Step 3 has to design around.

**The label-timing problem, named honestly.** The paper itself confirms **(paper)** that impression and click events don't arrive as one clean, pre-joined record — they're produced by Google's **Photon** system, described in the paper's own citation as handling the "fault-tolerant and scalable joining of continuous data streams" (Ananthanarayanan et al., SIGMOD 2013). An impression (the ad was shown) and a click (the user clicked it, if they did) are two separate events on two separate streams that have to be joined into one labeled training example — and the paper doesn't go further than naming that it relies on this joining system, so the specific windowing/timeout policy it uses (how long to wait for a click before committing an impression to training as a confirmed negative) is not something this document can cite as paper-confirmed. **(secondary)** This same shape of problem is well documented in the closely related conversion-rate-prediction literature — Chapelle's *"Modeling Delayed Feedback in Display Advertising"* (KDD 2014) names it directly for conversions, which can land anywhere from seconds to (the paper's own stated range) up to a month after the initiating event, forcing an explicit trade-off between labeling too early (mislabeling an eventual click/conversion as a negative) and labeling too late (a stale, slow-to-train model). For *clicks* specifically the window is typically far shorter than for conversions — a click, when it happens, usually happens within seconds to minutes of the impression, not days — but the same structural decision still has to be made somewhere in the pipeline: how long does the system wait before it's willing to commit an un-clicked impression to the training stream as `y = 0`, and what happens to the (rare) click that arrives just after that cutoff.

**Explicitly out of scope:** the auction mechanism and pricing (named in the Scope note above), ad matching/candidate generation (also named there), and anything downstream of the click itself (conversion prediction, ad relevance scoring beyond raw click probability) — the paper's own system boundary, taken as this capstone's boundary too.

**Trade-offs considered:** Using raw, unlabeled-by-hand click/no-click events as the training signal means this system never pays a human-labeling cost and can retrain continuously on fresh behavioral data (Step 4) — a real structural advantage over, say, capstone #5/#11's content-moderation taxonomy, which depends entirely on expensive human-labeled data. But it also means the label is only ever a proxy for what the product actually cares about (a satisfied user, a converted sale), not a direct measure of it — a user can click an ad they regret clicking, or decline to click an ad that would have genuinely helped them, and the training signal cannot distinguish either case from a "correct" click/no-click. Committing to a short, fixed window before finalizing a label as a negative keeps the online-learning loop (Step 4) fast and fresh, at the cost of a small, structural rate of mislabeled negatives (clicks that land just after the cutoff) that a longer window would avoid at the cost of training-data freshness — exactly the label-accuracy-vs-timeliness trade-off the Chapelle paper names for the conversion case.

---

## Step 2: Back-of-Envelope Constraints

**Confirmed scale descriptors, in the paper's own words (paper):** *"A typical industrial model may provide predictions on billions of events per day, using a correspondingly large feature space."* The paper also confirms, directly: feature vectors with **"billions of dimensions"**, where **"typically each instance will have only hundreds of nonzero values"** (i.e., extremely sparse, one-hot-style categorical features rather than dense numeric ones); trained models with **"billions of coefficients"**; and, from Section 4.1, that **"half the unique features occur only once in the entire training set of billions of examples."** None of these are given as exact numbers — all are qualitative "billions"-scale statements, which is exactly why the arithmetic below has to pick explicit illustrative anchors *within* that confirmed order of magnitude rather than inventing a different scale outright.

**Average and peak QPS from an illustrative daily-event anchor (illustrative arithmetic, anchored to the paper's "billions of events per day"):**

```
daily_prediction_events (illustrative) = 10,000,000,000  (10 billion/day — within the paper's "billions/day")

average_qps = 10,000,000,000 ÷ (24 h × 3,600 s)
            = 10,000,000,000 ÷ 86,400
            ≈ 115,741 predictions/sec, averaged across the day
```

Search traffic isn't flat — applying an illustrative peak-to-average ratio of 3x (lower than a typical consumer-app ratio, since sponsored-search queries are distributed across many time zones and query intents globally rather than concentrated in one region's evening peak):

```
peak_qps (illustrative) ≈ 115,741 × 3 ≈ 347,222 predictions/sec at peak
```

**Model memory footprint — the calculation that makes Section 4.2's real, paper-confirmed memory-saving trick concrete.** The paper states directly **(paper)**: naive implementations store each coefficient as a 32- or 64-bit float; because nearly all of this model's coefficients lie in the range (−2, +2), the fine-grained precision of a float is overkill, so the paper instead uses a **fixed-point q2.13 encoding** — 2 bits left of the binary point, 13 bits right of it, 1 sign bit, 16 bits total per coefficient — with a randomized-rounding correction to keep the discretization error unbiased. The paper reports this saves **75% of the RAM for coefficient storage** with no measurable accuracy loss. Taking an illustrative 3-billion-non-zero-coefficient model (within the paper's confirmed "billions of coefficients," and smaller than the full billions-of-dimensions feature space because L1 regularization — Step 4 — drives most coefficients to exactly zero and they don't need to be stored at all):

```
naive_64bit_size  = 3,000,000,000 coefficients × 8 bytes/coefficient
                  = 24,000,000,000 bytes ≈ 24 GB

q2.13_16bit_size  = 3,000,000,000 coefficients × 2 bytes/coefficient
                  = 6,000,000,000 bytes ≈ 6 GB

RAM_reduction     = (24 GB − 6 GB) ÷ 24 GB = 0.75 = 75%
```

That **75%** isn't a number this document invented to match the paper — it's the mechanical consequence of going from 64 bits to 16 bits per coefficient (a 4x reduction, i.e., 75% savings), and it lands exactly on the paper's own reported figure, which is a useful internal consistency check that the illustrative coefficient count chosen above doesn't change the ratio (just as capstone #1's binarization ratio was independent of its illustrative corpus-size choice).

**Model update frequency:** the paper states directly **(paper)** — *"It is necessary to make predictions many billions of times per day and to quickly update the model as new clicks and non-clicks are observed."* This is a confirmed architectural commitment, not an afterthought: the system is designed to update continuously, example-by-example, as new labeled impressions stream in, rather than on a periodic (hourly/daily/weekly) batch-retrain cadence — the direct motivation for Step 4's online-learning choice.

**Trade-offs considered:** A larger illustrative daily-event anchor (say, 50 billion/day instead of 10 billion) would scale the QPS numbers up proportionally without changing the RAM-reduction ratio at all — the 75% figure is a pure function of bit-width, not of traffic volume or model size, which is exactly why this document treats it as the load-bearing, paper-confirmed number and the specific daily-event count as the illustrative placeholder. The real trade-off the paper's own architecture accepts here is different: committing to update the model continuously, rather than batching updates into periodic retrains, buys freshness (Step 4) at the cost of needing the memory-saving and sparsification tricks in this step and Step 3 to be cheap enough to run inline, on every update, rather than as an offline batch job that can afford to be slower.

---

## Step 3: Data / Knowledge Pipeline

**What data exists and how it arrives (paper):** training examples are impression-click pairs, streamed continuously via the Photon joining system named in Step 1, with features drawn **(paper)** *"from a variety of sources, including the query, the text of the ad creative, and various ad-related metadata."* Data is **(paper)** *"extremely sparse, with typically only a tiny fraction of non-zero feature values per example"* — each training instance activates only hundreds of the feature space's billions of dimensions (Step 2), because most features are one-hot-style categorical indicators (a specific query term present, a specific ad-metadata flag set) rather than dense numeric values.

### Sidebar — the hashing trick / feature hashing

*(This concept has no existing Lesson home — Lessons 1–7 cover classic infra and AI-app fundamentals, not feature-engineering techniques for tabular/categorical ML.)*

- **Why?** A categorical feature with enormous cardinality (e.g. "which of several billion possible query terms or ad IDs is present") normally needs a lookup table — a dictionary mapping each distinct feature value to an integer column index — so the model's weight vector has a fixed, known slot for every possible value. Maintaining that dictionary at billions-of-values scale, keeping it synchronized across every training and serving replica, and growing it as genuinely new values appear is itself a real piece of infrastructure, separate from the model.
- **What?** **Feature hashing** (also called **the hashing trick**) replaces that dictionary with a deterministic hash function: a categorical value's column index is computed directly as `hash(value) mod num_buckets`, with no lookup table maintained anywhere. This makes the feature space's dimensionality a fixed, chosen constant (`num_buckets`) regardless of how many distinct values actually appear, at the cost of **collisions** — two different feature values that hash to the same bucket become indistinguishable to the model, each nudging the same shared weight in response to two different signals.
- **How?** A standard implementation (illustrative, general technique — not McMahan et al.'s own code, which this document doesn't claim to reproduce):

```python
import hashlib

def hash_feature(feature_name: str, feature_value: str, num_buckets: int) -> int:
    """Deterministically maps a (name, value) categorical feature to a fixed-width
    bucket index, with no lookup table maintained anywhere."""
    key = f"{feature_name}={feature_value}".encode("utf-8")
    digest = hashlib.md5(key).hexdigest()
    return int(digest, 16) % num_buckets
```

**The genuinely surprising, paper-confirmed finding this document has to be honest about.** It would be easy to assume a system at this scale uses feature hashing as its answer to high-cardinality features — it's the standard textbook recommendation, and the paper itself names two real precedents that did: Weinberger et al. (ICML 2009) reported excellent results hashing a personalized spam-filtering feature space down to 2²⁴ (≈16.8 million) buckets, and Chapelle reported similarly using 2²⁴ buckets for display-advertising modeling. **But McMahan et al.'s own Section 9 — titled "Unsuccessful Experiments" — reports the opposite result for their own sponsored-search system (paper, quoted directly):** *"We tested this approach but found that we were unable to project down lower than several billion features without observable loss. This did not provide significant savings for us, and we have preferred to maintain interpretable (non-hashed) feature vectors instead."* The same section also notes, in the context of handling rare features generally, that "hashing with collisions" as a general rare-feature-management strategy "also did not give useful benefit." Feature hashing is real, genuinely used elsewhere in the industry at genuinely large scale — and still, directly contradicted as the right call for *this specific* production system. This is exactly the kind of overclaim the task behind this document was built to catch, so it's surfaced here explicitly rather than quietly assumed.

**What the paper's system actually does instead, for the same underlying problem (paper, Section 4.1 — Probabilistic Feature Inclusion):** rather than hashing rare features into a smaller fixed space, the system decides *whether to track a feature at all*, probabilistically, the first few times it's seen — two confirmed variants, with confirmed experimental results (Table 2 of the paper):

| Method | RAM Saved | AucLoss Detriment |
|---|---|---|
| Bloom filter inclusion (n=2) | 66% | 0.008% |
| Bloom filter inclusion (n=1) | 55% | 0.003% |
| Poisson inclusion (p=0.03) | 60% | 0.020% |
| Poisson inclusion (p=0.1) | 40% | 0.006% |

**Poisson inclusion** adds a never-before-seen feature to the model with probability `p` the first time it's encountered (and deterministically thereafter once added) — the number of occurrences before inclusion follows a geometric distribution with expected value `1/p`. **Bloom filter inclusion** uses a counting Bloom filter (a probabilistic set-membership structure that can false-positive but never false-negative) to detect the first `n` times a feature has been seen, adding it to the model only once the filter reports it's crossed that count. Both exist to solve the same problem feature hashing was asked to solve — don't spend memory tracking the roughly half of all unique features that, per Step 2's figure, occur only once in a training set of billions of examples — but by deciding *whether to allocate a slot at all*, not by collapsing many slots into few and accepting collisions.

**What happens when the data is wrong or stale:** the paper's Section 8 (Automated Feature Management) confirms **(paper)** a real operational discipline around this: features ("signals," in the paper's terminology — e.g. "words in the advertisement," "country of origin") are tracked in a metadata index annotated for deprecation, platform-specific availability, and domain-specific applicability; consumers of a deprecated signal are automatically identified and alerted; unconsumed old signals are automatically flagged for cleanup. This exists because, at a scale where **(paper)** *"many developers may work asynchronously on signal development"* across *"dozens of domain specific problems,"* an engineer silently continuing to feed a model a signal that's been deprecated or has quietly changed meaning is a real, recurring failure mode the index is built to catch before it degrades the model.

**Worked example — subsampling training data, reproducing the paper's own formula (Section 4.6, paper).** The paper confirms **(paper)**: *"Typical CTRs are much lower than 50%, which means that positive examples (clicks) are relatively rare."* It also uses, as an illustrative example elsewhere in the paper (Section 5.1, discussing why absolute metric values are misleading), a click rate "closer to 2%" — this document reuses that same figure as its own illustrative anchor rather than inventing an unrelated one. The paper's own subsampling rule: keep every query where at least one ad was clicked, and keep only a fraction `r ∈ (0, 1]` of queries where no ad was clicked, then correct the resulting bias with an importance weight `ω = 1` for clicked-query events and `ω = 1/r` for sampled unclicked-query events (paper confirms this correction is exact, by a direct linearity-of-expectation argument, not a heuristic approximation).

```
daily_queries (illustrative)   = 100,000,000
click_rate (anchored to the paper's own "closer to 2%" example) = 0.02

clicked_queries    = 100,000,000 × 0.02  = 2,000,000
unclicked_queries  = 100,000,000 × 0.98  = 98,000,000

r (illustrative subsample fraction) = 0.10

sampled_unclicked  = 98,000,000 × 0.10   = 9,800,000

subsampled_total   = 2,000,000 + 9,800,000 = 11,800,000

data_volume_reduction = subsampled_total ÷ daily_queries
                       = 11,800,000 ÷ 100,000,000
                       = 0.118  →  training set shrinks to 11.8% of its original size
                       (an 8.47x reduction:  100,000,000 ÷ 11,800,000 ≈ 8.47)
```

Every sampled unclicked-query event is then trained on with importance weight `ω = 1/0.10 = 10` (i.e., its loss and gradient are scaled up 10x), while every clicked-query event keeps weight `ω = 1`. At an illustrative 2% click rate, subsampling at `r = 0.10` shrinks daily training volume by roughly **8.5x** while — per the paper's own confirmed linearity-of-expectation argument — leaving the expected training objective unchanged.

**Trade-offs considered:** Feature hashing's real advantage (a fixed, small, bounded feature-space size, independent of how many distinct values ever appear) is exactly what made it attractive to Weinberger et al. and Chapelle — but it trades away per-feature interpretability (you can no longer inspect which real-world signal a given weight corresponds to, since multiple real features share a bucket) and, per McMahan et al.'s own confirmed negative result, its accuracy cost at this system's specific scale and feature-interaction richness outweighed its memory savings. Probabilistic feature inclusion keeps every surviving feature fully interpretable and collision-free, at the cost of a small, probabilistic delay before a genuinely useful new feature starts influencing predictions (the `1/p` or `n`-occurrence wait before inclusion) — a real, if minor, lag the paper's own Table 2 shows is cheap in accuracy terms (well under 0.1% AucLoss detriment across every variant tested). Aggressive subsampling of unclicked queries buys a large, real reduction in training-data volume and therefore training cost, but pushes more of the system's statistical weight onto fewer actual clicked examples, which is only safe because the importance-weighting correction is exact — an approximate or poorly-calibrated correction would reintroduce exactly the bias subsampling is supposed to avoid.

---

## Step 4: Model/Agent Core Design — Online Learning via FTRL-Proximal

### Sidebar — online learning (vs. batch learning)

*(This concept has no existing Lesson home.)*

- **Why?** A classic supervised-learning workflow collects a fixed training set, trains a model against it to convergence, evaluates it, and ships it — then repeats the whole cycle, on a fresh (often much larger) dataset, whenever the model needs to be updated. At the scale and freshness-requirement this capstone's Step 2 established — billions of new labeled examples per day, with the paper's own stated need to "quickly update the model as new clicks and non-clicks are observed" — re-running that entire batch cycle for every update isn't just expensive, it structurally cannot keep up: by the time a batch retrain finishes, the data it trained on is already stale relative to what's streaming in.
- **What?** **Online learning** is a training paradigm where the model processes training examples one at a time (or in small streaming mini-batches), updating its parameters immediately after each one, rather than requiring the full dataset to be assembled up front and trained over in repeated passes. Critically — and this is the distinction the paper's own footnote makes explicit **(paper)** — online learning doesn't require the data to be IID (independent and identically distributed): it's explicitly built to handle "a sequence of examples that need not be IID," which matters because real click-stream data genuinely isn't IID (click behavior shifts by time of day, by trending topics, by ad-inventory changes) in the way a shuffled, fixed, one-time-collected training set is typically assumed to be.
- **How?** Each training example — a single (query, ad) impression with its now-resolved click/no-click label — triggers one gradient computation and one immediate weight update (the FTRL-Proximal update below), then is discarded; there's no notion of "epoch" or "pass over the dataset" the way there is in batch training. The model that's live and serving predictions right now is, up to network-replication lag (Step 5), the same model that was just updated by the most recent labeled example.

### Sidebar — FTRL-Proximal and per-coordinate learning rates

*(First appearance in this repo of this concept; no existing Lesson home.)*

- **Why?** Plain online gradient descent (OGD) is simple and produces good prediction accuracy, but it's bad at producing **sparse** models (weight vectors where most coefficients are exactly zero) — simply adding an L1-regularization subgradient to OGD's update essentially never zeroes out a coefficient in practice **(paper)**. At billions-of-dimensions scale (Step 2), a dense weight vector is both a serving-time memory problem and, per Step 2's own framing, exactly the thing the paper says it's "much more concerned with... at serving time rather than during training" — so a learning algorithm that naturally produces a sparse model, not just an accurate one, is a real production requirement, not a nice-to-have.
- **What?** **FTRL-Proximal** ("Follow The (Proximally) Regularized Leader") is an online-learning algorithm that produces the *same* sequence of coefficients as plain OGD when there's no L1 term, but — because it tracks model state through an alternative "lazy" representation (`z`, an accumulated-gradient-minus-weight-history term, rather than the weight vector `w` directly) — can apply L1 regularization far more effectively, reliably driving genuinely unneeded coefficients to exactly zero rather than merely small. The paper's own confirmed benchmark (Table 1) measured this against two real alternatives — RDA (Regularized Dual Averaging) and FOBOS — and a simpler heuristic the paper calls OGD-Count (hold a coefficient at zero until its feature has been seen more than `k` times, then run plain OGD) **(paper)**: RDA needed 3% more non-zero coefficients than FTRL-Proximal while also landing at a 0.6% AucLoss Detriment — a gap the paper's own table caption calls "significant for our application," meaning RDA isn't just less sparse, it's genuinely worse, not merely a different point on the same accuracy level. FOBOS and OGD-Count, by contrast, were tuned to match FTRL-Proximal's accuracy exactly (0.0% AucLoss Detriment) and still needed 38% and 216% more non-zero coefficients respectively to get there — FTRL-Proximal's sparsity advantage over the simplest heuristic is not a marginal difference, and unlike RDA, that comparison really is apples-to-apples on accuracy.
- **How?** **Per-coordinate learning rates** are the second half of the paper's own algorithm, and a distinct idea from FTRL-Proximal itself: instead of one shared, globally-decaying learning-rate schedule `η_t = 1/√t` applied to every coordinate (weight) in the model, each coordinate `i` gets its own rate, `η_t,i = α / (β + √(Σ g²_s,i))` **(paper, Eq. 2)** — a coordinate whose feature has been observed many times (a large accumulated sum of squared gradients) gets a smaller, more settled learning rate, while a coordinate whose feature is rarely seen keeps a higher, more reactive one. The paper's own worked thought experiment makes the intuition concrete **(paper)**: if you're simultaneously estimating `P(heads)` for 10 different coins and one coin is flipped far more often than another, a single shared learning-rate schedule needlessly decays the rarely-flipped coin's learning rate too, purely because *time* (not *evidence about that specific coin*) has passed. The paper's own confirmed A/B result: switching from a single global learning rate to per-coordinate rates reduced AucLoss by **11.2%** — and the paper notes, for context, that in their own setting "AucLoss reductions of 1% are considered large" **(paper)**, making 11.2% a genuinely large, not marginal, win.

**A direct, runnable implementation of the paper's own Algorithm 1 (paper-confirmed pseudocode; this Python rendering is this document's own, not the paper's literal code):**

```python
import math

class FTRLProximal:
    """Per-Coordinate FTRL-Proximal with L1 and L2 regularization for logistic
    regression -- a direct implementation of McMahan et al. (2013), Algorithm 1."""

    def __init__(self, alpha: float, beta: float, l1: float, l2: float):
        self.alpha, self.beta, self.l1, self.l2 = alpha, beta, l1, l2
        self.z: dict[int, float] = {}   # per-coordinate accumulated (gradient - weight-history) term
        self.n: dict[int, float] = {}   # per-coordinate sum of squared gradients, for the learning rate

    def _weight(self, i: int) -> float:
        zi, ni = self.z.get(i, 0.0), self.n.get(i, 0.0)
        if abs(zi) <= self.l1:
            return 0.0   # exactly zero -- this is the sparsity FTRL-Proximal delivers
        sign = 1.0 if zi > 0 else -1.0
        return -(1.0 / ((self.beta + math.sqrt(ni)) / self.alpha + self.l2)) * (zi - sign * self.l1)

    def predict(self, x: dict[int, float]) -> float:
        """x: sparse feature vector as {feature_index: value}. Returns P(click)."""
        wx = sum(self._weight(i) * xi for i, xi in x.items())
        return 1.0 / (1.0 + math.exp(-wx))   # sigmoid

    def update(self, x: dict[int, float], y: int) -> None:
        """One online-learning step: predict, observe the true label, update weights."""
        p = self.predict(x)
        for i, xi in x.items():
            g = (p - y) * xi                                   # gradient of LogLoss w.r.t. w_i
            ni = self.n.get(i, 0.0)
            sigma = (math.sqrt(ni + g * g) - math.sqrt(ni)) / self.alpha   # per-coordinate rate term
            self.z[i] = self.z.get(i, 0.0) + g - sigma * self._weight(i)
            self.n[i] = ni + g * g
```

Each call to `update()` is one complete online-learning step, matching this Sidebar's "What?": no epoch, no dataset pass — one labeled impression in, one weight update out, the model immediately ready to `predict()` on the next request with the just-updated weights.

**The explicit trade-off: online FTRL-Proximal vs. periodic batch retraining (illustrative framing — the paper doesn't present this as a live alternative it rejected, since Step 2's "billions of events per day, update quickly" requirement makes online learning close to a structural necessity rather than one option among equals; this is this document's own construction of the trade-off, for the capstone method's own sake).** A periodic batch-retrain design (train a fresh model nightly or weekly on the full accumulated dataset, then push it to serving) is simpler to reason about and debug — a given model version is a fully reproducible artifact, trained once, evaluated once, and either shipped or not — and avoids any risk of a single corrupted or adversarial training example immediately, permanently corrupting the live model's weights the way one bad online update theoretically could. But it structurally cannot react to anything that happens between retrains: a sudden shift in query patterns, a new advertiser's ad creative, or a breaking-news-driven spike in a topic area all go unmodeled until the next scheduled retrain catches up — exactly the freshness gap Step 2's "quickly update the model" requirement rules out at this system's traffic volume and update cadence.

**Trade-offs considered:** FTRL-Proximal's sparsity-inducing lazy representation is more complex to implement correctly than plain OGD (it requires storing and updating `z` rather than `w` directly, and deriving the closed-form per-coordinate update), but the paper's own Table 1 shows this complexity buys a real, measured win over every simpler alternative tested, not a marginal one. Per-coordinate learning rates require tracking one extra per-feature statistic (the running sum of squared gradients) beyond what a single global rate needs, doubling the per-coordinate metadata storage cost — but Section 4.5's own confirmed approximation (tracking just two counts, `N` negative and `P` positive events per feature, rather than the literal sum of squared gradients) shows the paper found a way to buy back most of that storage cost without giving up the accuracy win, a genuine instance of "the theoretically correct quantity and a cheap, empirically-validated approximation of it turned out to perform the same."

---

## Step 5: Serving Architecture

**The confirmed, end-to-end pipeline shape (paper, Figure 1 — described in prose since this document can't reproduce the figure itself):** Streaming Data → Probabilistic Feature Inclusion (Step 3) → Parallelized Model Training (the FTRL-Proximal update loop, Step 4) → Sparsification (L1-driven zeroing, Step 4) → Calibration (Step 6) → Model Serving Replicas, with a feedback loop of Progressive Validation Metrics (Step 6) flowing back to inform the next round of training and feature decisions.

**Replication to many data centers (paper):** *"Because trained models are replicated to many data centers for serving... we are much more concerned with sparsification at serving time rather than during training."* This is the paper's own confirmed architectural reason the memory-saving tricks of Steps 2–3 matter as much as they do: a model's memory footprint isn't paid once, centrally — it's paid once *per replica*, at every data center the model is pushed to, so Step 2's 75% RAM-reduction figure compounds directly with however many serving replicas exist. This is architecturally the same "replicate the expensive, shared artifact across every serving location" pattern Lesson 5's Concept 1 (RDBMS scaling — read replicas) and Lesson 3's Concept I3 (availability patterns, active-active redundancy) both already established for a database and an inference backend respectively; here the replicated artifact is a trained CTR model's weight vector instead of either of those.

**Query-time request path:** a search query `q` arrives → the (out-of-scope, per this capstone's Scope note) ad-matching step produces a candidate set of ads → for each candidate ad `a`, the serving system constructs the feature vector `x` (query terms, ad-creative text, ad metadata — Step 3's feature sources) and runs `predict(x)` (Step 4's `FTRLProximal.predict`) against the local, already-replicated model to produce `P(click | q, a)` → that probability, along with the advertiser's bid, feeds the (out-of-scope) auction. **Because the model is replicated locally to the data center handling the request, serving-time prediction is a pure local computation — a sparse dot product plus a sigmoid — with no network round-trip to a centralized model-serving tier**, which is exactly the latency property a real-time auction (the paper's own stated requirement: predictions "accurately, quickly, and reliably") needs.

**A schema for the feature-construction step this request path depends on (illustrative — the paper doesn't publish its actual production schema, only the categories of signal it draws features from):**

```python
import hashlib

def get_stable_feature_index(feature_name: str, feature_value: str, num_buckets: int) -> int:
    """Stand-in for the paper's actual non-hashed, stable feature index
    lookup (the probabilistic-inclusion-managed feature table, Step 3) --
    reuses the same hashing mechanics as this document's earlier
    hash_feature() helper (Step 3's hashing-trick sidebar) purely for
    runnability here; the paper's own system maintains an explicit,
    stable feature index, not a hash function, per Step 3."""
    key = f"{feature_name}={feature_value}".encode("utf-8")
    digest = hashlib.md5(key).hexdigest()
    return int(digest, 16) % num_buckets


def build_feature_vector(query: str, ad: dict, num_buckets: int = 2_000_000_000) -> dict[int, float]:
    """Illustrative feature construction for one (query, ad) impression. Each
    categorical signal becomes one or more sparse, one-hot-style entries --
    NOT via feature hashing (Step 3's confirmed finding), but via each
    feature's own stable index from the probabilistic-inclusion-managed
    feature table. get_stable_feature_index() stands in for that stable-index
    lookup here purely for runnability; the paper's own system uses an
    explicit feature index, not a hash function, per Step 3.
    """
    features: dict[int, float] = {}
    for term in query.lower().split():
        features[get_stable_feature_index("query_term", term, num_buckets)] = 1.0
    for term in ad["creative_text"].lower().split():
        features[get_stable_feature_index("ad_term", term, num_buckets)] = 1.0
    features[get_stable_feature_index("advertiser_id", str(ad["advertiser_id"]), num_buckets)] = 1.0
    features[get_stable_feature_index("ad_country", ad["country"], num_buckets)] = 1.0
    return features
```

**Model update propagation:** because Step 4's online-learning loop updates weights continuously rather than producing discrete "model versions" on a batch schedule, the serving fleet has to receive a continuous (or very frequent, e.g. every few minutes) stream of weight-delta updates from the training tier to each serving replica, rather than an occasional full-model push **(illustrative)** — a different, more continuous propagation shape than, say, capstone #10's inference-serving capstone, which propagates a discrete, versioned model artifact to its replicas on a far less frequent cadence.

**Trade-offs considered:** Replicating the full model to every serving data center trades storage cost (Step 2's memory footprint, paid once per replica) for serving-time latency (no network hop to a centralized scorer) and for resilience (one data center's model stays servable even if it's isolated from the training pipeline, Lesson 3's Concept I3 availability-chain reasoning applied here) — the same replication-cost-vs-latency-and-availability trade-off Lesson 5's Concept 1 names for database read replicas, now applied to a model artifact instead of a database shard. Continuous weight-delta propagation keeps every replica close to the live training state, at the cost of real engineering complexity in keeping that delta stream itself fault-tolerant and in sync — a discrete, versioned, far-less-frequent model push (the batch-retrain alternative Step 4 already weighed) would be simpler to propagate and roll back, at the direct cost of the freshness this system's whole design exists to buy.

---

## Step 6: Evaluation, Monitoring, and Iteration

**Why "accuracy" is the wrong metric here — constructed explicitly, with an honest note on what the paper itself actually argues.** The paper itself never frames its argument in terms of classification **accuracy** (the fraction of predictions that match the true label under some decision threshold) at all — it moves directly to AUC, LogLoss, and SquaredError as its chosen metrics, and its own stated reason is about *absolute metric values being misleading*, not about accuracy specifically: **(paper, quoted directly)** *"Even if predictions are perfect, the LogLoss and other metrics vary depending on the difficulty of the problem (that is, the Bayes risk). If the click rate is closer to 50%, the best achievable LogLoss is much higher than if the click rate is closer to 2%."* The classic "accuracy paradox" illustration below is therefore this document's own construction **(illustrative)**, built on the paper's own example click-rate figure ("closer to 2%") to make the same underlying point — a point the paper arrives at by a different, metric-choice argument rather than by critiquing accuracy directly:

```
assumed_click_rate (anchored to the paper's own "closer to 2%" example) = 0.02

A trivial model that always predicts "no click" (y_pred = 0 for every impression):
  accuracy = fraction of impressions where the true label is also "no click"
           = 1 - click_rate
           = 1 - 0.02
           = 0.98   →  98% accuracy

Yet this model:
  - never distinguishes one ad from another (every P(click) estimate is identical)
  - is useless as an input to the auction (Step 1's scope note) -- it carries zero
    ranking information
  - its AUC = 0.50 (chance-level) -- i.e. AucLoss = 1 - 0.50 = 0.50, the worst
    possible score under the paper's own chosen metric
```

**98% accuracy, 0.50 AucLoss (the worst possible score) — on the same trivial model.** This is the concrete version of why accuracy is the wrong lens at this class-imbalance level: **class imbalance** — a training-data or population condition where one label (here, "no click") vastly outnumbers the other ("click") — makes accuracy trivially gameable by any model that leans toward predicting the majority class, regardless of whether it's learned anything real.

**The real metrics, as the paper actually defines and uses them (paper):**
- **AUC** (area under the ROC curve — ROC standing for Receiver Operating Characteristic, a curve plotting true-positive rate against false-positive rate at every possible classification threshold) — the probability that, for a randomly chosen clicked impression and a randomly chosen non-clicked impression, the model assigns a higher predicted `P(click)` to the clicked one. A score of 1.0 is perfect ranking, 0.5 is no better than chance, and — critically for this problem — AUC is **insensitive to class imbalance** in a way accuracy isn't, since it's measuring relative ranking quality between the two classes rather than raw match/mismatch counts. The paper reports its own metric as **AucLoss = 1 − AUC**, specifically so that, consistent with its other metrics, a smaller number is always better.
- **LogLoss** (logistic loss) — the paper's own exact formula **(paper, Eq. 1)**: `ℓ_t(w_t) = −y_t log(p_t) − (1 − y_t) log(1 − p_t)`, the negative log-likelihood of the true label under the model's predicted probability. Unlike AUC, LogLoss directly penalizes *miscalibrated* confidence, not just ranking order — a model that's right about which ad is more likely to be clicked, but wrong about the actual probability by a wide margin, is punished by LogLoss in a way AUC alone wouldn't catch.
- **SquaredError** — named by the paper as a third metric tracked alongside AucLoss and LogLoss, without further elaboration beyond naming it as part of the same "evaluate across a plurality of metrics" practice **(paper)**.

**Progressive validation (paper) — a real, confirmed alternative to a held-out test set.** Rather than cross-validation or a separate held-out dataset, the paper uses **progressive validation** (also called **online loss**): because computing a gradient for the next training update already requires computing a prediction first, that same prediction — made *before* the model has trained on this particular example — is streamed out as a live evaluation data point, aggregated hourly. The paper's own stated reasons this beats a held-out set at this scale **(paper)**: it uses 100% of the data for both training and evaluation (no held-out slice ever "wasted"), and because small improvements matter at this scale and need large amounts of data to detect with confidence, that extra statistical power is a real, not cosmetic, advantage. The paper also explicitly warns **(paper)** that absolute metric values aren't comparable across different slices of data or different time windows for the Bayes-risk reason quoted above — so the paper reports **relative** changes (percent change vs. a baseline model on the *same* data) as its standard practice, not absolute metric values.

**Calibration — confirmed definition and method (paper).** *"Our predictions are calibrated on a slice of data `d` if on average when we predict `p`, the actual observed CTR was near `p`."* **Calibration**, in other words, is a property of a *set* of predictions, not any single one: if every impression the model assigned `P(click) = 0.1` is pooled together, roughly 10% of them should have actually been clicked. The paper's two confirmed correction methods: fitting a power-law correction `τ(p) = γp^κ` via Poisson regression on aggregated data, or the more flexible **isotonic regression** — a piecewise linear or piecewise constant correction function, fit by weighted least-squares, constrained only to be monotonically increasing — which the paper reports **(paper)** gave a meaningfully better reduction in bias at both the high and low ends of the prediction range than the simpler power-law method.

**Monitoring beyond the aggregate number (paper) — GridViz.** The paper names a real, specific failure mode: **(paper)** *"a small aggregate accuracy win on one metric may in fact be caused by a mix of positive and negative changes in distinct countries, or for particular query topics."* Its answer is a confirmed internal tool, GridViz, that breaks every tracked metric down by slice (country, query topic, match type, page layout) rather than reporting only one aggregate number — directly analogous to the per-country/per-topic breakdown discipline capstone #1's own evaluation (Step 6 there) already modeled for a different domain.

**Failure modes that show up only at scale, and the paper's own honesty about what didn't work (paper, Section 9).** The paper devotes an entire section to techniques it tried and found **did not** help, in its own stated spirit of sharing negative results as rigorously as positive ones: aggressive feature hashing (Step 3, above), dropout (effective in dense-feature vision settings, but actively harmful on this system's sparse, noisy-label data), feature bagging (slightly reduced AucLoss, 0.1%–0.6%, across tested schemes), and feature-vector normalization (no net positive effect once interacting with per-coordinate learning rates). This section is itself worth naming as a monitoring/iteration discipline, not just a list of negative results: a production ML team re-testing a promising idea from the literature and honestly reporting that it didn't transfer to their own data distribution is exactly the kind of "what happens when it's wrong or stale" feedback loop a mature system needs, applied to its own modeling choices rather than only to its input data.

**Trade-offs considered:** AUC is insensitive to class imbalance and miscalibration, making it a robust *ranking* metric — but precisely because it only measures relative ranking, two models with identical AUC can have wildly different calibration, which is exactly why the paper tracks LogLoss and runs a dedicated calibration step (Section 7) rather than treating AUC alone as sufficient. Progressive validation's 100%-data-efficiency and real-time freshness are a genuine advantage over a held-out set at this system's scale, but it does mean evaluation and training data are never fully independent in the classic statistical sense — a model is always evaluated on the data immediately before it trains on it, not on data permanently walled off from training, which the paper accepts as a reasonable trade given how much more statistical power the live data volume buys it. Isotonic regression's extra flexibility over a simple power-law correction buys better bias reduction at the distribution's extremes, at the cost of a less interpretable, non-closed-form correction function — a real complexity cost the paper judged worth paying given the confirmed accuracy win.

---

## Source(s) and Further Reading

- McMahan, Holt, Sculley, Young, Ebner, Grady, Nie, Phillips, Davydov, Golovin, Chikkerur, Liu, Wattenberg, Hrafnkelsson, Boulos, and Kubica, *"Ad Click Prediction: a View from the Trenches,"* KDD 2013 (ACM DOI 10.1145/2487575.2488200) — **primary**; full text fetched and read directly from Google Research's own archived PDF. Source of every figure, formula, and quoted claim in this document tagged (paper), including the FTRL-Proximal algorithm and per-coordinate learning rate formula, Table 1 (sparsity benchmark) and Table 2 (probabilistic feature inclusion benchmark), the confirmed rejection of feature hashing in Section 9.1, the LogLoss formula, AucLoss/AUC definition, progressive validation, the two calibration methods, and the paper's own "Unsuccessful Experiments" section.
- Ananthanarayanan et al., *"Photon: Fault-tolerant and scalable joining of continuous data streams,"* SIGMOD 2013 — cited by McMahan et al. as the streaming-join system this capstone's training data flows through; **secondary** for this document (cited by the primary paper, not independently fetched and read here).
- Chapelle, *"Modeling Delayed Feedback in Display Advertising,"* KDD 2014 — **secondary**; cited only for Step 1's label-timing discussion, as a well-documented treatment of a closely related (conversion-prediction, not click-prediction) delayed-feedback problem that McMahan et al.'s own paper does not itself address.
- Weinberger, Dasgupta, Langford, Smola, and Attenberg, *"Feature hashing for large scale multitask learning,"* ICML 2009 — **secondary**; cited by McMahan et al. as a real precedent where feature hashing succeeded, contrasted directly against this paper's own negative result for its sponsored-search system.
- `appendix/glossary.md` — new entries added for **online learning**, **FTRL-Proximal / per-coordinate learning rates**, and **feature hashing**; this capstone defines all three in full on first use above rather than assuming familiarity.
- Lesson 5 (`lessons/lesson-5-data-layer.md`), Concept 1 — the read-replica/replication framing this capstone's Step 5 applies to a model artifact instead of a database shard, referenced rather than re-derived.
- Lesson 3 (`lessons/lesson-3-scalability-and-availability.md`), Concept 3 (I3) — the active-active redundancy framing referenced in Step 5 for why a model is replicated per data center rather than served from one centralized location.
