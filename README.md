# AI System Design Primer

I built this as a standalone resource for my own AI system design prep. But AI system design doesn't exist in a vacuum — it borrows most of its hard parts (scaling, caching, databases, queues, availability trade-offs) straight from classic system design. So rather than reinvent that, this repo is deliberately structured like [`system-design-primer`](https://github.com/donnemartin/system-design-primer) — the well-known reference for that material — and teaches it the way I actually learn best: as a guided lesson/checkpoint course, the same format I used in my [`learn-docker`](https://github.com/romancobblepot/learn-docker) and [`learn-docker-ai-agents`](https://github.com/romancobblepot/learn-docker-ai-agents) courses.

Put simply: `system-design-primer` gives the topic depth, `learn-docker-ai-agents` gives the teaching shape, and this repo is what you get when you point that shape at AI/agentic systems instead of Docker tooling.

## Why this exists

Most people building AI applications today have already picked up the AI-native vocabulary — embeddings, RAG, agent loops, model serving — well enough to get by. What's actually thin for a lot of us is the *classic* distributed-systems material those applications still run on top of: load balancing, caching, replication, sharding, queues, the CAP trade-offs. This repo starts with a quick AI-native refresher, then spends most of its time on that classic material — taught directly, not just linked to — with every concept immediately tied back to a real AI/agentic case study instead of a generic textbook example.

## What's inside

| Lesson | Topic |
|---|---|
| 1 | **AI Fundamentals Refresher** — a fast pass over AI-native vocabulary (embeddings, RAG, agent loops, model serving, routing, semantic caching) for anyone who needs a refresher before the rest of the course |
| 2 | **Core System-Design Fundamentals** — the absolute basics (client/server, APIs, databases, caches, latency/throughput) for anyone newer to system design in general |
| 3 | **Scalability and Availability** — vertical vs. horizontal scaling, load-balancing patterns, replication, the CAP theorem, and the "nines" math behind uptime |
| 4 | **Network and Delivery** — DNS, CDNs, load balancers, and reverse proxies |
| 5 | **Data Layer** — scaling relational databases (replication, federation, sharding, denormalization), NoSQL types, and caching strategies |
| 6 | **Async and Communication** — message queues vs. task queues, back pressure, TCP vs. UDP, and RPC vs. REST |
| 7 | **Application Architecture and Security** — monoliths vs. microservices, service discovery, core security practices, and back-of-envelope estimation |
| 8 | **Safety and Isolation** — prompt injection, sandboxing, credential handling, guardrails, and multi-tenant isolation for systems with AI agents in them |
| 9 | **Evaluation and Observability** — how you actually know an AI system is working: evals, tracing, and monitoring |
| 10 | **Production Scaling** — taking an AI system from a working prototype to something that holds up at production load |
| 11 | **Real-World Architectures** — a survey of how real companies and tools apply everything from Lessons 1–10, with pointers back to exactly which lesson or capstone each one maps to |

Each lesson is backed by a matching checkpoint (`checkpoints/`) you're meant to do before moving on — short, self-check exercises rather than graded tests.

On top of the 11 lessons, there are **14 worked capstone solutions** in `solutions/` — full system designs for things like a visual search engine, a recommendation feed, an LLM API gateway, a multi-agent customer-support system, and a coding agent — each one built the same way a real system design interview answer would be: constraints, back-of-envelope math, architecture, and explicit trade-offs, every real-world claim tagged by how confident the sourcing is.

## Structure

- **`lessons/`** — the 11 lessons, numbered in reading order
- **`checkpoints/`** — one self-check per lesson, same numbering
- **`solutions/`** — 14 worked capstone system designs, the "put it all together" exercises
- **`appendix/`** — flip-back reference material: a glossary of every term used across the course, and a table of real-world latency/token numbers for sanity-checking estimates

## How to work through it

This is meant to be read start to finish, in order — later lessons assume you've already read the earlier ones, and the numbering is the reading order:

1. **Read a lesson.** Each one explains a handful of concepts the same way: *why does this exist, what is it, and how does it actually work* — with a worked example and a pointer to a real capstone or case study that uses it.
2. **Do its checkpoint.** A short set of questions to confirm the lesson actually landed, before you move on. There's no answer key to grade yourself against for most of these — the point is just to notice whether you *can* answer them in your own words.
3. **Move to the next lesson.** Repeat through Lesson 11.
4. **Work through `solutions/` whenever you want the full picture.** The capstones aren't tied to a single lesson — each one pulls together concepts from several lessons at once, the way a real design actually would. They're worth doing both as you go (once a capstone uses a concept you just learned) and again after Lesson 11, once you have everything to draw on.
5. **Keep `appendix/` open as a reference, not something to read start to finish.** If a term shows up and you don't remember its definition, that's what the glossary is for.

If you've never touched classic system design before, start with Lesson 2 even though it's a short one — everything after it assumes you have that vocabulary. If you're already comfortable with AI-native concepts, Lesson 1 will mostly be a quick refresher rather than new material.

## How this relates to my other courses

- [`learn-docker`](https://github.com/romancobblepot/learn-docker) — Docker fundamentals, taught around a real todo-app project. No overlap in topic, but it's where I first used this lesson/checkpoint teaching format.
- [`learn-docker-ai-agents`](https://github.com/romancobblepot/learn-docker-ai-agents) — hands-on Docker tooling for AI agents (sandboxing, local model serving, MCP tools, and `cagent`). That repo is the *hands-on, tool-specific* companion to this one: it teaches you to actually run an agent safely on your machine, while this repo teaches the *system design* thinking behind why you'd architect an AI system the way you do. They're meant to be read side by side, not one instead of the other.
- [`system-design-primer`](https://github.com/donnemartin/system-design-primer) — the original reference this repo is structured after, and still the better place to go once you want to go deeper than this course's curated scope (its own exhaustive company-architecture list, SQL-tuning internals, full OSI-layer detail, and many more worked interview questions beyond AI/agentic ones).

## Who it's for

Anyone preparing for an AI/ML system design interview, or just trying to build a real mental model of how production AI systems are actually architected — especially if your AI-native vocabulary is already solid but the classic infrastructure side (caching, sharding, queues, availability) feels like a gap.

## Browsing it locally

Clone the repo and run the included preview server (no dependencies beyond Python 3):

```bash
git clone git@github.com:romancobblepot/ai-system-design-primer.git
cd ai-system-design-primer
python3 preview.py
```

Then open `http://127.0.0.1:8000`. It lists this repo's folders and files, and renders any `.md` file as formatted markdown in the browser.
