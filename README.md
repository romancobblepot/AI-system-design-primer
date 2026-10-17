# AI System Design Primer

I built this as a standalone resource for my own AI system design prep. AI system design borrows most of its hard parts — scaling, caching, databases, queues, availability trade-offs — straight from classic system design, so this repo is deliberately structured like [`system-design-primer`](https://github.com/donnemartin/system-design-primer), and taught the way I learn best: a guided lesson/checkpoint format, same as my [`learn-docker`](https://github.com/romancobblepot/learn-docker) and [`learn-docker-ai-agents`](https://github.com/romancobblepot/learn-docker-ai-agents) repos.

## 💡 Why this exists

Most people building AI applications have already picked up the AI-native vocabulary (Transformers,embeddings, RAG, agent loops, model serving) well enough to get by. What's actually thin for most of us is the *classic* distributed-systems material those applications still run on top of:

- Load balancing
- Caching
- Replication & sharding
- Queues
- CAP trade-offs

So this repo starts with a quick AI-native refresher, then spends most of its time on that classic SysDesign material — taught directly, not just linked to, and tied back to a real AI/agentic case study instead of a generic textbook example.

## 📚 Lessons & checkpoints

Each lesson has a matching checkpoint — a short self-check, not a graded test — meant to be done right after the lesson, before moving on.

| # | Lesson | Checkpoint | Topic |
|---|---|---|---|
| 1 | [AI Fundamentals Refresher](lessons/lesson-1-ai-fundamentals-refresher.md) | [Checkpoint 1](checkpoints/checkpoint-1-ai-fundamentals.md) | A fast pass over AI-native vocabulary (embeddings, RAG, agent loops, model serving, routing, semantic caching) for anyone who needs a refresher before the rest of the course |
| 2 | [Core System-Design Fundamentals](lessons/lesson-2-core-system-design-fundamentals.md) | [Checkpoint 2](checkpoints/checkpoint-2-core-system-design-fundamentals.md) | The absolute basics (client/server, APIs, databases, caches, latency/throughput) for anyone newer to system design in general |
| 3 | [Scalability and Availability](lessons/lesson-3-scalability-and-availability.md) | [Checkpoint 3](checkpoints/checkpoint-3-scalability-and-availability.md) | Vertical vs. horizontal scaling, load-balancing patterns, replication, the CAP theorem, and the "nines" math behind uptime |
| 4 | [Network and Delivery](lessons/lesson-4-network-and-delivery.md) | [Checkpoint 4](checkpoints/checkpoint-4-network-and-delivery.md) | DNS, CDNs, load balancers, and reverse proxies |
| 5 | [Data Layer](lessons/lesson-5-data-layer.md) | [Checkpoint 5](checkpoints/checkpoint-5-data-layer.md) | Scaling relational databases (replication, federation, sharding, denormalization), NoSQL types, and caching strategies |
| 6 | [Async and Communication](lessons/lesson-6-async-and-communication.md) | [Checkpoint 6](checkpoints/checkpoint-6-async-and-communication.md) | Message queues vs. task queues, back pressure, TCP vs. UDP, and RPC vs. REST |
| 7 | [Application Architecture and Security](lessons/lesson-7-application-architecture-and-security.md) | [Checkpoint 7](checkpoints/checkpoint-7-application-architecture-and-security.md) | Monoliths vs. microservices, service discovery, core security practices, and back-of-envelope estimation |
| 8 | [Safety and Isolation](lessons/lesson-8-safety-and-isolation.md) | [Checkpoint 8](checkpoints/checkpoint-8-safety.md) | Prompt injection, sandboxing, credential handling, guardrails, and multi-tenant isolation for systems with AI agents in them |
| 9 | [Evaluation and Observability](lessons/lesson-9-evaluation-and-observability.md) | [Checkpoint 9](checkpoints/checkpoint-9-evaluation.md) | How you actually know an AI system is working: evals, tracing, and monitoring |
| 10 | [Production Scaling](lessons/lesson-10-production-scaling.md) | [Checkpoint 10](checkpoints/checkpoint-10-scaling.md) | Taking an AI system from a working prototype to something that holds up at production load |
| 11 | [Real-World Architectures](lessons/lesson-11-real-world-architectures.md) | [Checkpoint 11](checkpoints/checkpoint-11-real-world-architectures.md) | A survey of how real companies and tools apply everything from Lessons 1–10, with pointers back to exactly which lesson or case study each one maps to |

## 🧩 Case studies

On top of the 11 lessons, there are **14 worked SysDesign case studies** — full system designs covering constraints, back-of-envelope math, architecture, and explicit trade-offs. Each one pulls together concepts from several lessons at once, the way a real design actually would. Every real-world claim is labelled either *(source-confirmed)*, checked against a named primary source, or *(illustrative)*, this document's own planning assumption; figures are re-derived from the sources, and nothing is run on a live system.

Each case study also ships **two practice PDFs** in [`capstone-study-and-mock/`](capstone-study-and-mock/): a **Study edition** — scenario questions with layered follow-ups and worked, how-to-think answers — and a **Mock interview** — the same scenarios, numbered identically, with the answers removed. They are linked per row below.

| # | Case study | What it's based on | Practice |
|---|---|---|---|
| 1 | [Visual Search](case-studies/visual-search/README.md) | Pinterest's unified embedding search (Flashlight / Lens / Shop-the-Look) | [Study](capstone-study-and-mock/visual-search/capstone1_visual_search_study.pdf) · [Mock](capstone-study-and-mock/visual-search/capstone1_visual_search_mock.pdf) |
| 2 | [Ad Click-Through-Rate Prediction](case-studies/ctr-prediction/README.md) | Google's "View from the Trenches" | [Study](capstone-study-and-mock/ctr-prediction/capstone2_ctr_prediction_study.pdf) · [Mock](capstone-study-and-mock/ctr-prediction/capstone2_ctr_prediction_mock.pdf) |
| 3 | [Video Recommendation](case-studies/video-recommendation/README.md) | YouTube's candidate generation + ranking split | [Study](capstone-study-and-mock/video-recommendation/capstone3_video_recommendation_study.pdf) · [Mock](capstone-study-and-mock/video-recommendation/capstone3_video_recommendation_mock.pdf) |
| 4 | [Search Ranking](case-studies/airbnb-search-ranking/README.md) | Airbnb's listing search (GBDT → neural ranker) | [Study](capstone-study-and-mock/airbnb-search-ranking/capstone4_airbnb_search_ranking_study.pdf) · [Mock](capstone-study-and-mock/airbnb-search-ranking/capstone4_airbnb_search_ranking_mock.pdf) |
| 5 / 11 | [Harmful Content Detection & AI Content Moderation](case-studies/harmful-content-detection/README.md) | OpenAI's holistic undesired-content-detection system | [Study](capstone-study-and-mock/harmful-content-detection/capstone5_harmful_content_detection_study.pdf) · [Mock](capstone-study-and-mock/harmful-content-detection/capstone5_harmful_content_detection_mock.pdf) |
| 6 | [Friend/Connection Recommendation](case-studies/pymk-friend-recommendation/README.md) | LinkedIn's "People You May Know" | [Study](capstone-study-and-mock/pymk-friend-recommendation/capstone6_pymk_friend_recommendation_study.pdf) · [Mock](capstone-study-and-mock/pymk-friend-recommendation/capstone6_pymk_friend_recommendation_mock.pdf) |
| 7 | [ETA / Arrival-Time Prediction](case-studies/uber-eta-prediction/README.md) | Uber's DeepETA | [Study](capstone-study-and-mock/uber-eta-prediction/capstone7_uber_eta_prediction_study.pdf) · [Mock](capstone-study-and-mock/uber-eta-prediction/capstone7_uber_eta_prediction_mock.pdf) |
| 8 | [Personalized Feed Ranking](case-studies/netflix-feed-ranking/README.md) | Netflix's row ranking | [Study](capstone-study-and-mock/netflix-feed-ranking/capstone8_netflix_feed_ranking_study.pdf) · [Mock](capstone-study-and-mock/netflix-feed-ranking/capstone8_netflix_feed_ranking_mock.pdf) |
| 9 | [RAG System Design](case-studies/rag-contextual-retrieval/README.md) | Enterprise knowledge-base chatbot (Anthropic's Contextual Retrieval) | [Study](capstone-study-and-mock/rag-contextual-retrieval/capstone9_rag_contextual_retrieval_study.pdf) · [Mock](capstone-study-and-mock/rag-contextual-retrieval/capstone9_rag_contextual_retrieval_mock.pdf) |
| 10 | [LLM Inference Serving at Scale](case-studies/llm-inference-serving/README.md) | Production LLM serving infrastructure | [Study](capstone-study-and-mock/llm-inference-serving/capstone10_llm_inference_serving_study.pdf) · [Mock](capstone-study-and-mock/llm-inference-serving/capstone10_llm_inference_serving_mock.pdf) |
| 12 | [Multi-Agent Customer-Support Platform](case-studies/multi-agent-customer-support/README.md) | Sierra's supervisor architecture and Klarna's AI assistant | [Study](capstone-study-and-mock/multi-agent-customer-support/capstone12_multi_agent_customer_support_study.pdf) · [Mock](capstone-study-and-mock/multi-agent-customer-support/capstone12_multi_agent_customer_support_mock.pdf) |
| 13 | [Autonomous Coding Agent](case-studies/autonomous-coding-agent/README.md) | Devin-style plan-and-execute software engineering | [Study](capstone-study-and-mock/autonomous-coding-agent/capstone13_autonomous_coding_agent_study.pdf) · [Mock](capstone-study-and-mock/autonomous-coding-agent/capstone13_autonomous_coding_agent_mock.pdf) |
| 14 | [Computer-Use / Browser Agent](case-studies/computer-use-agent/README.md) | The screenshot-reasoning-action loop vs. a direct-API agent | [Study](capstone-study-and-mock/computer-use-agent/capstone14_computer_use_agent_study.pdf) · [Mock](capstone-study-and-mock/computer-use-agent/capstone14_computer_use_agent_mock.pdf) |
| 15 | [LLM API Gateway](case-studies/llm-api-gateway/README.md) | Provider-agnostic routing by cost, latency, and quality | [Study](capstone-study-and-mock/llm-api-gateway/capstone15_llm_api_gateway_study.pdf) · [Mock](capstone-study-and-mock/llm-api-gateway/capstone15_llm_api_gateway_mock.pdf) |

They're worth doing both as you go — once a case study uses a concept you just learned — and again after Lesson 11, once you have everything to draw on. Read the case study's README first, then take the Study edition, then sit the Mock with the answers closed.

## 🗂️ Structure

- **[`lessons/`](lessons/)** — the 11 lessons, numbered in reading order
- **[`checkpoints/`](checkpoints/)** — one self-check per lesson, same numbering
- **[`case-studies/`](case-studies/)** — 14 worked system designs, the "put it all together" exercises
- **[`capstone-study-and-mock/`](capstone-study-and-mock/)** — a Study edition and a Mock interview PDF for each of the 14 case studies, in the interview-playbook style
- **[`appendix/`](appendix/)** — flip-back reference material: a [glossary](appendix/glossary.md) of every term used across the course, and a [table of real-world latency/token numbers](appendix/token-and-latency-numbers.md) for sanity-checking estimates

## 🧭 How to work through it

This is meant to be read start to finish, in order — later lessons assume you've already read the earlier ones, and the numbering is the reading order:

1. **Read a lesson.** Each one explains a handful of concepts the same way: *why does this exist, what is it, and how does it actually work* — with a worked example and a pointer to a real case study that uses it.
2. **Do its checkpoint.** A short set of questions to confirm the lesson actually landed, before you move on. There's no answer key to grade yourself against for most of these — the point is just to notice whether you *can* answer them in your own words.
3. **Move to the next lesson.** Repeat through Lesson 11.
4. **Work through the case studies whenever you want the full picture** (see the table above). They aren't tied to a single lesson, so they're worth doing both as you go and again after Lesson 11, once you have everything to draw on.
5. **Keep `appendix/` open as a reference, not something to read start to finish.** If a term shows up and you don't remember its definition, that's what the glossary is for.

If you've never touched classic system design before, start with Lesson 2 even though it's a short one — everything after it assumes you have that vocabulary. If you're already comfortable with AI-native concepts, Lesson 1 will mostly be a quick refresher rather than new material.

## 🔗 How this relates to other repos

- [`system-design-primer`](https://github.com/donnemartin/system-design-primer) — the original reference this repo is structured after, and still the better place to go once you want to go deeper than this repo's curated scope (its own exhaustive company-architecture list, SQL-tuning internals, full OSI-layer detail, and many more worked interview questions beyond AI/agentic ones).
- [`learn-docker`](https://github.com/romancobblepot/learn-docker) — Docker fundamentals, taught around a real todo-app project. No topic overlap, but it's where I first used this lesson/checkpoint teaching format.
- [`learn-docker-ai-agents`](https://github.com/romancobblepot/learn-docker-ai-agents) — hands-on Docker tooling for AI agents (sandboxing, local model serving, MCP tools, `cagent`): the *tool-specific* companion to this repo's *system design* thinking. Best read side by side, not one instead of the other.

## 🌱 Still growing

This isn't a finished, one-and-done repo — I keep adding new case studies and sharpening existing lessons as I learn more and run into new real-world examples worth covering. So if something's outdated, a case study you'd love to see is missing, or you just have a correction, contributions are genuinely welcome — open an issue or send a PR.

## Credits 🙌 

This repo exists because of my interest in this domain, and my interest stems out of the immense impact these people have had on my learning journey and in the field of AI/ML in general so big ups to:

- **[Chip Huyen](https://huyenchip.com/)** — her two books, [*Designing Machine Learning Systems*](https://www.huyenchip.com/books/) and *AI Engineering* ([O'Reilly](https://www.oreilly.com/library/view/ai-engineering/9781098166298/)), are about as good as it gets for actually understanding how production ML/AI systems hold together. If you only read two books on this topic, make them these.
- **[Dr. Raj Dandekar, Dr. Rajat Dandekar, Dr. Sreedath Panat, and the rest of the team at Vizuara](https://www.youtube.com/@vizuara)** — MIT-PhD-level rigor on AI/ML fundamentals, explained without the usual jargon wall. A genuinely great resource if you want to go deeper on the ML/DL side.
- **[Hamel Husain](https://hamel.dev/)** — his blog is close to required reading if you care about LLM evals done properly. Incredibly generous about sharing hard-won, real-world lessons instead of just theory.
- **[Nitish Singh and CampusX](https://www.youtube.com/@campusx-official)** — one of the best channels out there for building real data science/ML intuition from the ground up, in a way that's actually approachable.
- **[`system-design-primer`](https://github.com/donnemartin/system-design-primer)** — the GOAT of system design repos, and honestly the whole reason this repo exists in the shape it does. Massive respect for putting together something this thorough and keeping it free and open for everyone.

Go check out their work — all of it is worth your time.

## 💻 Browsing it locally

Clone the repo and run the included preview server (no dependencies beyond Python 3):

```bash
git clone git@github.com:romancobblepot/ai-system-design-primer.git
cd ai-system-design-primer
python3 preview.py
```

Then open `http://127.0.0.1:8000`. It lists this repo's folders and files, and renders any `.md` file as formatted markdown in the browser.
