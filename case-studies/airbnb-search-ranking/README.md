# Capstone #4: Search Ranking — Airbnb Listing Search (GBDT → Neural Ranker)

## At a glance

| Topic | Summary |
|---|---|
| Source | Haldar, Abdool, Ramanathan, Xu, Yang, Duan, Zhang, Barrow-Williams, Turnbull, Collins and Legrand, "Applying Deep Learning to Airbnb Search," arXiv:1810.09591 (October 2018), published at KDD 2019. |
| Problem | Order the thousands of listings that match a guest's search so that the listing the guest would book comes first. A gradient-boosted tree model had improved bookings and then plateaued. |
| Core idea | Replace the tree model with a neural ranker in stages, trained on pairs of booked and not-booked listings with a loss weighted by the change in NDCG. The paper stresses that this is a rethink of the whole system and not a drop-in model swap. |
| Timeline | Figure 2 labels the launches: simple NN in 04/2017, LambdaRank NN in 06/2017, tree and factorization machine hybrid in 03/2018, deep NN in 06/2018 *(source-confirmed)*. |
| Label | The impression of the booked listing has relevance 1 and every other impression 0. Training pairs come from the searches of guests who booked *(source-confirmed)*. |
| Final model | Input of 195 features, then 127 ReLU units, then 83, trained on 1.7 billion pairs. Scaling the data 10 times let it replace the hybrid's complexity *(source-confirmed)*. |
| Failed attempts | A listing ID embedding overfit. A multi-task model with long views raised long views and left bookings neutral. Dropout hurt, and hand-shaped noise gave about 1% offline NDCG and no significant online gain *(source-confirmed)*. |
| First to break | The training input pipeline, then scoring inside the Java search stack. A pipeline that parsed CSV left the GPU at about 25%, and a Protobuf and Dataset pipeline gave a 17 times speedup *(source-confirmed)*. |
| Easy-to-miss traps | The GPU-resident static embedding speeds training, and it is not a serving cache. A GBDT can also be trained for NDCG. 25% to 90% GPU use cannot explain 17 times. The positional discount is part of the metric, not a bias correction. |
| Practice PDFs | [Study edition](../../capstone-study-and-mock/airbnb-search-ranking/capstone4_airbnb_search_ranking_study.pdf) · [Mock interview](../../capstone-study-and-mock/airbnb-search-ranking/capstone4_airbnb_search_ranking_mock.pdf) |

Evidence labels used below: *(source-confirmed)* means the figure or claim is in the paper. *(illustrative)* means it is this document's planning assumption. The paper gives few numbers in its text. Most results appear only as unlabeled bar charts.

### Concepts this case study builds on

| Concept | Where it is taught | One-line recap |
|---|---|---|
| Embeddings and high-cardinality categorical features | [Lesson 1, Group C](../../lessons/lesson-1-ai-fundamentals-refresher.md#c-retrieval-and-knowledge) | A learned vector for an ID, which needs enough data per ID to converge. |
| Back-of-envelope estimation and latency numbers | [Lesson 7, Concept 4](../../lessons/lesson-7-application-architecture-and-security.md#concept-4-back-of-envelope-estimation-technique--latency-numbers) | State assumptions, convert to rates and sizes, find the binding resource. |
| Offline evaluation | [Lesson 9, Concept 2](../../lessons/lesson-9-evaluation-and-observability.md#concept-2-offline-evaluation--golden-datasets-llm-as-judge-regression-suites) | Gate changes on a fixed measurement and know what it cannot show. |
| GBDT, LambdaRank | [Glossary](../../appendix/glossary.md) | Boosted trees, and a pairwise loss weighted by the change in NDCG. |

---

## Step 1: Clarify Requirements & Frame the ML/AI Objective

### The objective

A guest searches for homes in a place on given dates. The paper describes the task as responding with an ordered list of a handful of listings from the thousands available in the inventory *(source-confirmed)*. Successful sessions end with the guest booking a listing. The model discussed is the most complex piece of the ranking puzzle, and it orders listings by the guest's likelihood of booking. Other models in the ecosystem predict whether a host accepts a request and whether the guest will rate the trip five stars.

### Ground truth

In offline evaluation the impression of the booked listing has relevance 1 and every other impression has relevance 0 *(source-confirmed)*. For training, the paper builds pairs of one booked listing and one not-booked listing from the listings seen by a guest who booked. Three consequences follow:

- Only searches by guests who booked produce positive examples. Sessions that end without a booking supply no pairs, which is a reading of the paper's description.
- The model learns from logs of the models already in production, which decided what guests saw. The paper says this and does not discuss the selection effects.
- The paper observes that the logs hold no objective truth. It is hard even for people at Airbnb to tell which listing was booked, and the choice depends on a guest's budget and taste, which stay hidden.

### Out of scope

- Retrieval, which narrows the inventory to the candidate set.
- Smart Pricing, a separate model that appears only as an input feature.
- The results page layout.

### Trade-offs considered

A booking is a stronger signal than a click, because the guest commits and the listing has to match. It is also rarer and slower to arrive. Each ranking model is tested online in an A/B test for a statistically significant increase in conversions.

---

## Step 2: Back-of-Envelope Constraints

### What the paper gives

It gives few numbers *(source-confirmed)*:

- Thousands of listings in the inventory for a search.
- A deep model with 195 input features after categorical features are expanded to embeddings, then 127 and 83 ReLU units.
- Training on 1.7 billion pairs.
- A 17 times training speedup and GPU use near 90%, up from about 25%.

It gives no inventory size, search rate or market count. None is needed here, because ranking sees only the candidate set.

### Scoring cost per query

```text
layer 1 = 195 × 127 = 24,765 multiply-adds
layer 2 = 127 ×  83 = 10,541
output  =  83 ×   1 =     83
total   = 35,389 multiply-adds per candidate = 70,778 FLOPs
2,000 candidates per query (illustrative) = 141.6 million FLOPs, about 0.14 GFLOP
```

That is a small amount of work for one query. The binding constraints in this paper are elsewhere.

### Training cost against input cost

One training pair needs a forward and backward pass for two listings. With about 3 times the forward cost for the backward pass *(illustrative)*:

```text
FLOPs per pair   = 2 listings × 70,778 × 3 = 424,668
one pass over 1.7 billion pairs = 7.2 × 10^14 FLOPs
at 5 TFLOP/s sustained (assumed) = about 144 seconds
```

The paper says static listing features such as location, bedrooms, amenities and guest rules were read as part of every training example, which created an input bottleneck of multiple kilobytes per example. With an assumed 4 KB:

```text
1.7 billion pairs × 2 listings × 4 KB = 13.9 TB read per pass
at 1 GB/s = about 13,900 seconds, roughly 97 times the compute time
```

This matches the paper's account: the GPU sat at about 25% while the time went into parsing CSV and copying data. The paper's remedy keeps those features in a table in GPU memory, indexed by listing ID. Its size depends on the number of listings, not on the number of examples. With an assumed 2 million listings at 4 KB, the table is 8.2 GB.

### Why 17 times is not 25% to 90%

Raising GPU use from 25% to 90% is a factor of 3.6. The paper reports 17 times for the retooled pipeline, so use alone does not account for it. The rest came from removing parsing and copying work, and the paper does not split the two. Do not derive one number from the other.

### Trade-offs considered

More candidates raise scoring cost in proportion and do not change the conclusion. A larger inventory changes retrieval and leaves ranking untouched. The training pipeline, not the network's arithmetic, set the pace of iteration.

---

## Step 3: Data / Knowledge Pipeline

### Features

The features fed to the deep model are mostly simple properties of listings such as price, amenities and historical booking count, fed directly with minimal feature engineering *(source-confirmed)*. Two exceptions come from other models:

- The price of listings that have Smart Pricing enabled, from a specialized pricing model.
- The similarity of the listing to the user's past views, computed from co-view embeddings.

Both tap data that is not part of the ranking training examples. The pricing model is Ye et al., "Customized Regression Model for Airbnb Dynamic Pricing" (KDD 2018), and the co-view embeddings are from Grbovic and Cheng (KDD 2018), both cited in the paper's references.

### Feature normalization

The first attempt fed the neural network every feature used by the tree model. The paper says it went very badly: the loss saturated mid-training and more steps had no effect. The cause was unnormalized features.

- Trees depend only on the order of feature values. Neural networks are sensitive to their numeric values.
- Values outside the usual range cause large gradients, which can permanently shut off a ReLU through vanishing gradients.
- The fix keeps every feature within a small range, with the bulk in the interval from −1 to 1 and the median at 0.

Two transforms do this. A feature that looks normal is rescaled as (feature − mean) ÷ standard deviation. A feature that looks like a power law is transformed as log((1 + feature) ÷ (1 + median)).

### Smooth distributions

The paper gives three reasons to care about smooth feature distributions *(source-confirmed)*:

- Spotting bugs. Prices logged in the wrong currency for some geographies, and a monthly price in place of a daily one for stays over 28 days, showed up as spikes in distribution plots.
- Generalization. Hidden layers produce progressively smoother distributions, which the paper believes lets upper layers interpolate for unseen values. A sanity check scaled the test values of a feature such as price to 2, 3 and 4 times, and NDCG stayed remarkably stable.
- Completeness. Occupancy was not smooth because listings have different minimum stays. Adding average length of stay and normalizing by it fixed the shape.

Latitude and longitude were replaced by the offset from the center of the map the user is viewing, then the logarithm of the offset. This is a lossy many-to-one map, and it lets the model learn properties that depend on distance. Location preferences come from a separate categorical feature.

### Neighborhood preference as a categorical feature

The paper hashes the city in the query together with the level-12 S2 cell of the listing into one integer, for example the pair "San Francisco" and cell 539058204 mapped to 71829521. It maps this to an embedding, which training infers by backpropagation. The old tree model needed a heavily engineered pipeline to track bookings over neighborhoods and cities, and that pipeline did not factor in prices of booked listings.

### Why a listing ID embedding failed

An embedding per listing ID mostly overfit. NDCG improved on the training set and not on the test set (Figure 5). The paper's explanation is that embeddings need substantial data per item, and listings are limited by the physical world: even the most popular listing can be booked at most 365 times a year, and typical listings far fewer. Videos and words have no such limit.

### The multi-task attempt to fix it

Views of a listing page are far more plentiful than bookings, by orders of magnitude, and long views correlate with bookings. The model predicted booking and long view from a shared hidden layer, with a shared listing ID embedding. The booking loss got a higher weight, and each long view's loss was scaled by the logarithm of its view duration. Scoring online used the booking prediction only.

Online, long views rose by a large margin and bookings stayed neutral. The paper's inspection found reasons for the gap: high-end but high-priced listings, long descriptions that are hard to parse, and unique or humorous listings *(source-confirmed)*. Long views correlate with bookings and have a large orthogonal component.

### Trade-offs considered

Minimal feature engineering is cheap and makes normalization compulsory. Features from other models save work and tie ranking to those models' correctness. A per-listing embedding would capture individual patterns, and the data does not support it.

---

## Step 4: Model/Agent Core Design — GBDT, Then a Sequence of Neural Rankers

### Sidebar: gradient-boosted decision trees

A gradient-boosted decision tree (GBDT) model is a sum of many shallow decision trees, built one at a time, each trained to correct the errors of those before it. Scoring a candidate means following each tree from root to leaf and adding the leaf values. It handles tabular features and their interactions with little feature scaling.

Replacing the manually crafted scoring function with a GBDT gave one of the largest step improvements in bookings in Airbnb's history. The gains then saturated, with long spells of neutral experiments, and that made the moment ripe for sweeping changes *(source-confirmed)*.

### The sequence of models

| Stage | What it was | Result |
|---|---|---|
| Simple NN, 04/2017 | One hidden layer of 32 ReLU units, same features as the GBDT, L2 regression loss with booked = 1 and not booked = 0 | Booking neutral. It showed that the whole NN pipeline was production ready. |
| LambdaRank NN, 06/2017 | The same family with a pairwise loss weighted by change in NDCG | The first breakthrough. |
| Hybrid, 03/2018 | An NN fed the GBDT's leaf index per tree and a factorization machine's prediction | Combined three models that ranked differently. |
| Deep NN, 06/2018 | 195 inputs, 127 then 83 ReLU units, data scaled 10 times | Replaced the hybrid's complexity. |

The paper tells the first stage as a lesson. It started with intricate custom architectures and was overwhelmed by their complexity. Karpathy's advice is "don't be a hero", and the paper adapts it to "don't be a hero, in the beginning". Starting simple "got us off to a start, but not very far". Early on it saw regressions in offline metrics, and the paper says moving to deep learning is not a drop-in replacement but a matter of scaling the system.

### Sidebar: NDCG and LambdaRank

Normalized discounted cumulative gain (NDCG) rewards finding relevant results near the top of a list. Each position carries a discount, the gains are summed, and the total is divided by the best possible total for that query. With one booked listing at relevance 1, NDCG is the discount at the booked listing's position. A common discount for a 1-based position r is 1 ÷ log2(r + 1).

```text
position 1: 1.000     position 2: 0.631     position 9: 0.301     position 10: 0.289
moving the booked listing from 2 to 1 gains 1.000 − 0.631 = 0.369
moving it from 10 to 9 gains            0.301 − 0.289 = 0.012    (31 times less)
```

LambdaRank, as the paper uses it, has two parts *(source-confirmed)*:

- A pairwise form. Each training example is a pair of a booked and a not-booked listing, and the loss is cross-entropy on the score difference between them.
- A weight on each pair equal to the change in NDCG if the two listings swapped places. Improving a booked listing from position 2 to 1 gets priority over 10 to 9.

```python
import math

def discount(rank: int) -> float:               # rank counts from 1
    return 1.0 / math.log2(rank + 1)

def pair_loss(score_booked, score_other, booked_rank, other_rank):
    weight = abs(discount(booked_rank) - discount(other_rank))
    return weight * math.log(1.0 + math.exp(-(score_booked - score_other)))
```

In the paper's code the ranks come from sorting the model's current scores within a training session's sampled listings. For a score gap of 0.5 and the booked listing at rank 2 against rank 1, the loss is 0.369 × 0.474 = 0.175.

A GBDT can be trained for NDCG as well. LambdaMART, cited in the paper's references through Burges, does this. The paper's GBDT used L2 regression, and it did not test a ranking-loss GBDT. So the paper shows the objective mattered for the neural network, not that trees could not use it.

### The hybrid and the deep model

The hybrid started from an observation: the other models, a GBDT with different sampling of training searches and a factorization machine (FM), performed comparably on test data, yet the listings they up-ranked were quite different. An FM maps listings and queries into a 32-dimensional space and predicts the booking probability. The hybrid took the FM's prediction as a feature and each tree's leaf index as a categorical feature.

The paper calls the resulting complexity staggering, and it cites technical-debt concerns. Its final step deprecated that complexity by scaling the training data 10 times and moving to a network with two hidden layers. Figure 4 shows that training on 1.7 billion pairs closed the gap between training and test NDCG. Whether the deep model could have been launched directly is a question the paper raises and does not answer outright.

### Retrospective

The paper recommends deep learning with a wholehearted yes, and says part of the reason is how it changed the roadmap: from better math on features to the optimization objective and whether all users are represented. It adds that confined to smaller scales, models like GBDT are arguably at par and easier to handle, and the team continues to use them for focused medium-sized problems.

### Trade-offs considered

Trees need little feature scaling and make a strong baseline fast. They plateaued here. Neural networks need normalization discipline, are harder to interpret, and kept improving with 10 times the data. The hybrid bought ground quickly and left three models to run.

---

## Step 5: Serving Architecture

### The stack

The paper summarizes the pipeline *(source-confirmed)*:

- A guest's search reaches a Java server that does retrieval and scoring.
- The server writes logs stored as serialized Thrift instances.
- A Spark pipeline turns the logs into training data.
- TensorFlow trains the models.
- Tools in Scala and Java evaluate models and compute offline metrics.
- Models are uploaded to the Java server. Everything runs on AWS instances.

### Scoring inside the Java stack

When the team began shipping TensorFlow models in early 2017, it found no efficient way to score them in a Java stack. Passing data back and forth between Java and another language added latency that was a blocker. To meet search's strict latency requirement it wrote a custom neural network scoring library in Java. The paper expects to revisit this. It gives no latency figure.

### Training pipeline: Protobuf and Dataset

The tree model's training data was in CSV format, and the pipeline was reused with TensorFlow's feed_dict. GPU use was near 25%, and most of the time went into parsing CSV and copying data. Producing the data as Protobufs and reading it with the Dataset API gave a 17 times speedup and GPU use near 90%. This allowed scaling the training data from weeks to months.

### Refactoring the static features

Many features are properties of a listing that rarely change. The paper stops reading them with each example. It uses only the listing ID as a categorical feature, and packs all quasi-static listing features into a non-trainable embedding indexed by that ID, resident in GPU memory. This removed multiple kilobytes of data per training example that used to be loaded from disk through the CPU.

The cost is stated: for features that changed during the training period, the embedding holds one value, which trades a small level of noise against training speed. This is a training-time optimization. The paper does not describe a serving cache, and does not say how the embedding is built or refreshed.

### What the paper does not say

- How candidates are retrieved, or how many.
- The latency budget, or how the Java library compares with other options.
- How a new or changed listing reaches the embedding table.

### A sketch of scoring

```python
def score_candidates(features: list[list[float]], model) -> list[int]:
    scores = model.predict(features)             # one row per candidate listing
    return sorted(range(len(features)), key=lambda i: scores[i], reverse=True)
```

### Decision table

| Decision | This system's choice | Choose differently when |
|---|---|---|
| Model family | Neural ranker after the tree model plateaued | A tree model for a focused, medium-sized problem |
| Training loss | Pairwise, weighted by change in NDCG | Pointwise regression for a first working pipeline |
| Static features in training | GPU-resident table indexed by listing ID | Per-example features if they change quickly |
| Training data format | Protobuf and Dataset | CSV only for a small prototype |
| Scoring | A custom library in the serving language | A model server if its call overhead fits the latency budget |
| Per-listing ID embedding | Not used | If listings had enough data per ID |

### Trade-offs considered

The static table speeds training and freezes features that changed during the training period. The custom Java library avoids cross-language overhead and has to be maintained. The pipeline investment is what allowed training data to grow from weeks to months.

---

## Step 6: Evaluation, Monitoring and Iteration

### Offline and online

NDCG is the principal offline metric. A model is then tested online in an A/B test for a statistically significant increase in conversions *(source-confirmed)*. Figure 2 shows relative gains of each model in offline NDCG and in online bookings as unlabeled bars, so no values can be quoted.

The paper gives two clear cases where an offline or auxiliary measure moved and the booking result did not:

- The long-view model raised long views by a large margin, with neutral bookings.
- Hand-shaped noise for regularization improved offline NDCG by about 1% and gave no statistically significant online improvement.

### Hyperparameters

The paper reports that a broad search gave no meaningful improvements and some confidence in its choices *(source-confirmed)*:

| Setting | Choice | Note |
|---|---|---|
| Dropout | Not used | Every flavor slightly degraded offline metrics. The randomness produced invalid scenarios that distracted the model. |
| Noise | Hand-crafted shapes per feature | About 1% offline NDCG, no significant online gain |
| Initialization | Xavier for weights, uniform in −1 to 1 for embeddings | All-zero initialization was "the worst way to start training" |
| Learning rate | Adam with default settings, in a lazy variant | Faster with large embeddings |
| Batch size | Fixed at 200 | Hard to judge its effect on the model |

### Feature importance

The paper says estimating feature importance is where the team took a step back with neural networks. Four methods:

- Score decomposition. Attributing the final score to input nodes was a conceptual error, since influence cannot be separated across a ReLU.
- Ablation. Dropping a single feature changed performance by about as much as retraining noise, since the model made up for it from redundant features. It leads to a Ship-of-Theseus problem.
- Permutation. Shuffling one feature gave nonsensical results, such as the number of rooms as one of the most important features. Shuffling one at a time assumes independence, and rooms are tied to price, guests and amenities. It did help to find features that did not matter.
- TopBot, which compares feature values of top-ranked and bottom-ranked listings without perturbing anything. Top-ranked prices skewed lower, which showed price sensitivity. Review distributions looked alike, which suggested the model was not using reviews as expected.

### Bias, which the paper does not discuss

The paper says nothing about position bias, the tendency of a listing shown first to be booked because it was first. It also does not discuss how training on logs of earlier models, which chose what guests saw, shapes the data. The positional discount in NDCG is part of the metric. It weights top positions more. It does not correct for exposure, so it should not be read as a bias treatment.

### What breaks first at 10×

| Quantity | At 10× | Reason |
|---|---|---|
| Scoring per query | 10 times the FLOPs for 10 times the candidates | Scales with candidates |
| Training input | 10 times the bytes if features stay per example | The static table keeps the cost near the number of listings |
| Static table | Grows with listings, not examples | One row per listing |
| Feature checks | More plots and more bugs to spot | Distribution plots caught real data errors |
| Offline and online gaps | More candidate models to test | Each needs an A/B test |

### Risks

- A static table that is stale for a changed listing, which adds noise the paper accepts.
- Feedback from earlier models in the logs, which the paper does not analyze.
- Interpretation: the paper reports that feature importance became much harder to read.

### Trade-offs considered

Offline NDCG steers iteration and A/B tests decide. Feature analysis methods each mislead in a different way, and together they still point to gaps such as the unused reviews.

---

## Sources and Further Reading

- Haldar, Abdool, Ramanathan, Xu, Yang, Duan, Zhang, Barrow-Williams, Turnbull, Collins and Legrand, "Applying Deep Learning to Airbnb Search," arXiv:1810.09591, KDD 2019. The primary source for every figure and claim marked source-confirmed.
- Ye et al., "Customized Regression Model for Airbnb Dynamic Pricing," KDD 2018, and Grbovic and Cheng, "Real-time Personalization using Embeddings for Search Ranking at Airbnb," KDD 2018, both cited by the paper as the origin of two input features. Not read for this document.
- Burges, "From RankNet to LambdaRank to LambdaMART: An Overview," the reference the paper gives for LambdaRank.
- [Lesson 1](../../lessons/lesson-1-ai-fundamentals-refresher.md), Group C: embeddings.
- [Lesson 7](../../lessons/lesson-7-application-architecture-and-security.md), Concept 4: the estimation method used in Step 2.
- [Capstone #3, Video Recommendation](../video-recommendation/README.md): the same offline-against-online evaluation policy.
- [Glossary](../../appendix/glossary.md): GBDT, LambdaRank.

Labels: *(source-confirmed)* is in the paper. *(illustrative)* is a planning assumption of this document.
