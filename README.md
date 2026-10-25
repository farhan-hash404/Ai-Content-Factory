# 🚀 AI Content Factory: Stateful Multi-Agent Content Orchestration & Evaluation Engine
## 🎓 Final Year Project (FYP) — Core System Documentation

[![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Orchestration-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend_API-green.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React_19-TypeScript_&_Vite-blue.svg?logo=react&logoColor=white)](https://react.dev/)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-Native_Audio-purple.svg)](https://deepmind.google/technologies/gemini/)
[![DeepEval](https://img.shields.io/badge/DeepEval-G--Eval_Metrics-red.svg)](https://github.com/confident-ai/deepeval)
[![License](https://img.shields.io/badge/License-Apache_2.0-lightgrey.svg)](LICENSE)

A stateful, multi-agent AI system for automated research, content synthesis, multi-modal asset generation, and academic-grade evaluation. Built on **LangGraph**, **FastAPI**, and **React**, this project serves as a **Final Year Project (FYP)** demonstrating agent coordination, parallel processing, Human-in-the-Loop (HITL) workflows, Advanced RAG, and automated LLM-as-judge quality assessment.

## 📹 Demo Video

https://github.com/farhan-hash404/Ai-Content-Factory/raw/master/docs/demo.mp4

<sub>If the player above doesn't load, [**download / watch the demo (MP4)**](docs/demo.mp4).</sub>

---

> **🎬 Live demo (recorded).** `<LIVE_URL will go here>` — a **static replay of one
> real generation run** (article, podcast, 9:16 video, AI images, G-Eval +
> DeepEval scorecards). It needs no server, so it never sleeps and costs nothing.
> New content can't be generated there — the heavy multi-agent backend (torch,
> Whisper, ffmpeg, multi-minute jobs) can't run on a free static host. To drive
> the **full live system**, open the repo in **GitHub Codespaces** (one-click
> `.devcontainer`) or run it locally — see *Installation* below.

> **Scope.** This is a research and demonstration system, not a production
> deployment. It runs as a single API worker with a shared-secret access gate
> and no per-user accounts. The **Known Limitations** section at the end of this
> document states these boundaries precisely; read it before deploying anywhere
> reachable by other people.

---

## 🌟 Key Capabilities & Research Pillars

1. **Stateful Graph Orchestration:** Manages complex agent communications, loops, and conditions with [LangGraph](https://langchain-ai.github.io/langgraph/).
2. **Stateful Resumption & Checkpointer:** Employs [LangGraph's SqliteSaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/) to persist state. If the process is halted or the server crashes, the engine can resume execution from the exact last saved step without repeating expensive LLM calls or research operations.
3. **Advanced Document Ingestion (Advanced RAG):** Parses PDFs, DOCX, TXT, and Markdown files. Uses sentence-level embeddings (`gemini-embedding-001` at 1536 dimensions, or `text-embedding-3-small` on an OpenAI endpoint) to construct semantic chunks based on similarity thresholds. It executes cosine-similarity queries to match sections and pull targeted, grounded evidence.
4. **Human-in-the-Loop (HITL) Outline Control:** Pauses the writing process to present a draft outline plan to the user. The user can directly modify titles, goals, word counts, and bullet points via the UI, or write natural language feedback to request the LLM to automatically regenerate the plan.
5. **Parallelized Fan-Out Generation:** Speeds up content generation by writing body sections in parallel. Individual Worker agents are assigned specific sections, receiving only the evidence records matching their topic to prevent redundant text or source-stuffing.
6. **Multi-Modal Generation Studio:**
   - **Podcast Studio:** Scripts an 18–20 turn two-host episode, then synthesises each turn with a distinct neural voice through a three-provider chain — keyless Edge TTS, then OpenAI `tts-1-hd`, then single-voice Gemini narration — and merges the turns into one track with inter-turn silence.
   - **Video Generator:** Generates text-to-speech voiceovers, fetches stock B-roll clips from the Pexels API, matches them to the script, and renders videos with synchronized subtitles using MoviePy.
   - **SEO Keyword Optimizer:** Strategically integrates target keywords into headers, body paragraphs, and meta descriptions.
7. **Academic Evaluation (LLM-as-Judge):** Grades content against academic standards across four dimensions: Coherence, Relevance, Accuracy & Grounding, and Tone Alignment, using both in-house scoring and official [DeepEval](https://github.com/confident-ai/deepeval) GEval metrics.

---

## 📐 System Architecture

The workflow is a stateful, interruptible **cyclic** directed graph — cyclic
because the Quality Control → Revision feedback loop deliberately routes back on
itself, bounded at two attempts. The diagram below mirrors the edges declared in
[`build_graph()`](Agents_backend/main.py):

```mermaid
graph TD
    START([START]) --> B(Router)

    B -->|upload_id set| ING(Document Ingest / RAG)
    B -->|needs research| C(Research Agent)
    B -->|closed book| D(Orchestrator)
    ING -->|closed_book| D
    ING -->|hybrid / auto_topic| C
    C --> D

    D -.->|"interrupt_after — state persisted"| E[/"HITL — Plan Editor UI"/]
    E -.->|"approved, edited, or LLM-revised"| F{{Send fan-out}}

    subgraph PAR [Parallel Writing]
        F --> G0(Worker 0)
        F --> G1(Worker 1)
        F --> GN(Worker N)
    end

    G0 --> H
    G1 --> H
    GN --> H

    subgraph RED [Reducer subgraph]
        H(Merge Sections) -->|generate_images| H2("Plan and Place Images")
    end

    H --> CV(Completion Validator)
    H2 --> CV

    CV -->|generate_qa| I(Quality Control Auditor)
    CV -->|QA disabled| K
    I -->|"critical issues, under limit"| J(Revision Agent)
    J --> I
    I -->|"READY or revision limit reached"| K(Keyword SEO Optimizer)

    K --> P(G-Eval Scorecard)

    P --> L{Asset toggles}
    L -->|campaign| M(Campaign Generator)
    L -->|video| N(Video Synthesis)
    L -->|podcast| O(Gemini Podcast Studio)
    L -->|none enabled| Z

    M --> Z([END])
    N --> Z
    O --> Z

    DE(DeepEval G-Eval):::ondemand -.->|"POST /run-deepeval"| Z
    classDef ondemand stroke-dasharray: 5 5
```

The diagram above is hand-drawn for readability. To render the graph directly
from the compiled workflow — useful as ground truth when the two might drift:

```bash
cd Agents_backend && python -c "from main import build_graph; print(build_graph().get_graph().draw_mermaid())"
```

Two details the diagram makes explicit because they are easy to get wrong:

* **G-Eval runs before the media generators, not after.** Evaluation scores the
  article, so it is sequenced immediately after the SEO optimizer; the campaign,
  video and podcast nodes then fan out in parallel from it.
* **DeepEval is not a graph node.** It runs on demand from its own endpoint
  (dashed above), because adding four chain-of-thought judge calls to every
  generation is not a cost worth paying by default.

---

## 🤖 The Agent Roster

Not every node is an LLM call. Several stages are deterministic Python because
the task does not require judgement — the "Model" column says exactly which is
which, and `None` is a deliberate design choice rather than a missing feature.

> **Temperature is inert on the default model.** Several nodes request a
> specific sampling temperature (the planner asks for 0.7 to vary outlines, the
> writers for 0.3). Reasoning-family models such as `gpt-5-mini` accept only
> their default temperature, and `langchain-openai` drops the parameter silently
> rather than raising — so on an OpenAI reasoning model these values have no
> effect. They DO apply on the Gemini models used by default, and on a
> non-reasoning OpenAI model such as `gpt-4o-mini`. Guarded by
> `tests/test_evaluation.py::TestTemperatureIsInertOnReasoningModels`.

| Graph Node | Model | Code Implementation | Primary Responsibility & Logic |
| :--- | :--- | :--- | :--- |
| **Topic Guard** | `LLM_FAST_MODEL` | [topic_guard.py](Agents_backend/Graph/agents/topic_guard.py) | Two tiers: a free deterministic screen rejects malformed input (empty, too short/long, no letters, gibberish); the LLM then judges whether a well-formed topic is semantically unsafe. Runs before a job is created, so rejected topics cost no pipeline tokens. |
| **Router** | `LLM_FAST_MODEL` | [routing.py](Agents_backend/Graph/agents/routing.py) | Chooses `closed_book` / `hybrid` / `open_book`, drafts search queries, and sets the recency window Tavily filters on. |
| **Researcher** | `LLM_FAST_MODEL` + Tavily / DuckDuckGo | [research.py](Agents_backend/Graph/agents/research.py) | Runs queries in parallel, scrapes results (Jina Reader with a BeautifulSoup fallback), filters near-duplicates by Jaccard overlap, and extracts structured evidence. Downgrades the mode to `closed_book` if nothing usable is found, so an ungrounded post is never reported as grounded. |
| **Ingest / RAG** | `EMBEDDING_MODEL` + `LLM_FAST_MODEL` | [document_ingest.py](Agents_backend/Graph/agents/document_ingest.py) | Semantic chunking via sentence-embedding distance, ChromaDB indexing, and topic-scoped retrieval with a three-tier fallback (Chroma → local vectors → persisted evidence). Evidence is extracted only from retrieved chunks. |
| **Orchestrator** | `LLM_QUALITY_MODEL` | [orchestrator.py](Agents_backend/Graph/agents/orchestrator.py) | Plans the outline, then **partitions evidence across sections** so parallel workers cite different sources instead of converging on the same few statistics. A higher temperature is requested to vary outlines between runs; see the note below the table for when that takes effect. |
| **Worker (×N)** | selected model, else `LLM_QUALITY_MODEL` | [workers.py](Agents_backend/Graph/agents/workers.py) | Writes its assigned section in parallel via LangGraph `Send()`, receiving only its own evidence slice plus sibling section titles for transition context. |
| **Reducer** | **None** (deterministic) | [workers.py](Agents_backend/Graph/agents/workers.py) | Orders sections by task ID, joins them, and builds the references table from the evidence pool — all plain Python. The single LLM call in this module generates SEO metadata, not the merge itself. |
| **Completion Validator** | **None** (deterministic) | [completion_validator.py](Agents_backend/Graph/completion_validator.py) | Regex checks for missing sections and low word count, applies shared auto-repairs, and scores completeness. No model involved. |
| **Quality Control** | `LLM_QUALITY_MODEL` + deterministic check | [quality_control.py](Agents_backend/Graph/agents/quality_control.py) | Audits the draft against evidence for hallucinations and structure. A **non-LLM citation verifier** parses every hyperlink and checks it against the research evidence by URL and domain; any unmatched link forces `NEEDS_REVISION` and caps the score at 6.0 regardless of the model's opinion. |
| **Revision** | `LLM_QUALITY_MODEL` | [revision.py](Agents_backend/Graph/agents/revision.py) | Surgically rewrites only the sections carrying critical issues, falling back to a full-article edit. Bounded at 2 attempts; output shorter than 60% of the original is rejected. |
| **SEO Optimizer** | `LLM_QUALITY_MODEL` + deterministic analysis | [keyword_optimizer.py](Agents_backend/Graph/keyword_optimizer.py) | Keyword density and placement are computed in Python; the model is used only to weave under-represented keywords back into the weakest passages. |
| **Image Planner** | `LLM_FAST_MODEL` → Pollinations / Gemini / DALL·E → Pexels → local render | [multimedia.py](Agents_backend/Graph/agents/multimedia.py) | Plans placements and prompts, then generates through a five-link fallback chain. The selected `image_model` decides where the chain *starts*, not which providers may be used. Ordered by descending "actually generated" and ascending reliability: Pollinations is genuine generation but its anonymous tier answers `402` after a couple of images; Pexels then returns a real photograph (the log says so plainly); an offline Pillow-rendered captioned figure is last and cannot fail, so no figure slot ever ships as a broken image. |
| **Campaign Gen** | `LLM_FAST_MODEL` | [campaign.py](Agents_backend/Graph/agents/campaign.py) | Summarises the **full** article into a structured brief, then writes a LinkedIn post and an X/Twitter post in parallel. *Currently these two channels only* — the state carries fields for email, landing page, Facebook and YouTube, but they are not generated. |
| **Podcast Studio** | `gemini-2.5-flash` | [podcast_studio.py](Agents_backend/Graph/podcast_studio.py) | Generates a single-speaker audio podcast using Gemini's native audio output. |
| **Video Gen** | `LLM_QUALITY_MODEL` + Edge TTS + Whisper | [video.py](Agents_backend/Graph/agents/video.py) | Scripts the voiceover, synthesises speech via keyless Edge TTS (Gemini TTS as fallback), derives word-level timings with locally-run Whisper for karaoke captions, pulls portrait B-roll from Pexels, and composites a 9:16 MP4 with MoviePy. |
| **Academic Judge** | `LLM_JUDGE_MODEL` (defaults to `LLM_QUALITY_MODEL`) | [evaluation.py](Agents_backend/Graph/agents/evaluation.py) | In-house G-Eval scorecard (1–5) runs inside the graph; the weighted overall is computed in Python, not by the model. The official `deepeval` G-Eval runs **on demand** via its own endpoint, not as a graph node. |

---

## 🧪 Evidence-Distribution Experiment

The orchestrator partitions the evidence pool across sections so that parallel
workers cite different sources. That exists because of an observed defect: with
9 sections and 5 evidence items, every worker independently gravitated to the
same two or three prominent statistics, and one post repeated the same figure
seven times.

The system ships with the ablation needed to measure whether the fix works.
Setting `assign_evidence=False` skips partitioning, so every worker receives the
full pool — reproducing the pre-fix behaviour exactly.

```bash
cd Agents_backend

# Treatment arm — evidence partitioned across workers
RUN_GOLDEN_TESTS=1 GOLDEN_ASSIGN_EVIDENCE=1 pytest tests/golden -v -s

# Control arm — every worker receives the full pool
RUN_GOLDEN_TESTS=1 GOLDEN_ASSIGN_EVIDENCE=0 pytest tests/golden -v -s

# Aggregate both arms into a comparison + LaTeX table body
python -m tests.golden.report_ablation
```

Artefacts are written to `tests/golden/_runs/<case_id>__{assigned,fullpool}/`,
so the arms never overwrite each other. Two **deterministic** metrics are
recorded per run — no model scores them, so the numbers are not exposed to
judge bias:

| Metric | Meaning | Better |
| :--- | :--- | :--- |
| `repetition.repetition_rate` | Share of distinct statistics that surface in more than one section | Lower |
| `repetition.max_section_spread` | Section count for the single most-repeated statistic | Lower |
| `sources.concentration` | Share of cited sources appearing in more than one section | Lower |

The measurement code is [`tests/golden/metrics.py`](Agents_backend/tests/golden/metrics.py),
which carries its own self-check (`python -m tests.golden.metrics`).

> **On sample size.** One run per topic per arm measures a single sample of a
> stochastic generator, not an effect. Repeat each arm several times per topic
> before reporting a difference, and state `n` alongside any figure.

---

## 📊 Academic Quality & LLM-as-Judge Evaluation

The system evaluates the final content across four academic rubrics, generating scores and explanation logs:

1. **Coherence (Structure & Flow):** Evaluates logical progression, paragraph transitions, and structure.
2. **Relevance (Topic Coverage):** Evaluates how well the text matches user search queries and integrates keywords.
3. **Accuracy & Grounding:** Compares facts, numbers, and references against the source documents or research findings to flag hallucinations.
4. **Tone Alignment:** Evaluates target tone suitability and flags typical AI-generated phrases.

### In-House vs. DeepEval Scoring Modes
The system provides two evaluation workflows:
* **Custom Judge Node (`geval_scores`):** Runs automatically in the graph. Uses structured LLM outputs to rate sections on a **1.0 to 5.0** scale; the overall score is a code-computed weighted average (30% Coherence, 20% Relevance, 30% Accuracy, 20% Tone).
* **DeepEval G-Eval Node (`deepeval_scores`):** Runs **on demand** (the "Run Academic Audit" button → `POST /api/jobs/{job_id}/run-deepeval`), not inside the graph, since it makes 4 extra LLM calls per blog. Leverages Confident AI's `deepeval` library to execute Chain-of-Thought grading based on the G-Eval framework (Liu et al. 2023). Scores are normalized to a **0.0 to 1.0** scale.

Both reports are written to the `reports/` folder of each generated blog for academic audit trails.

---

## 🗂️ Project Directory Map

### 💻 Backend Components
* **Orchestration & Workflow:**
  - [api.py](Agents_backend/api/main.py) — FastAPI web application serving API routes, background tasks, and WebSocket streaming.
  - [main.py](Agents_backend/main.py) — Core CLI execution entry point and LangGraph workflow builder.
  - [db.py](Agents_backend/db.py) — SQLite database interface for jobs, metrics, and files.
  - [event_bus.py](Agents_backend/event_bus.py) — Message broker managing WebSocket connections and stream logs.
* **LangGraph Configuration:**
  - [state.py](Agents_backend/Graph/state.py) — Defines the Graph memory structures using [State TypedDict](Agents_backend/Graph/state.py#L85), [Plan](Agents_backend/Graph/state.py#L51), and [Task](Agents_backend/Graph/state.py#L29) definitions.
  - [nodes.py](Agents_backend/Graph/nodes.py) — Maps graph nodes to corresponding agent functions.
  - [templates.py](Agents_backend/Graph/templates.py) — System instructions, roles, and formatting guidelines.
  - [podcast_studio.py](Agents_backend/Graph/podcast_studio.py) — Scripts the two-host episode and synthesises it through the TTS provider chain.
  - [tts.py](Agents_backend/Graph/tts.py) — Keyless speech synthesis (Edge TTS) plus the ffmpeg resolution that makes locally-run Whisper work; shared by the podcast and video agents so both speak the same 24 kHz mono PCM.
* **Specialized Agent Implementation:**
  - [topic_guard.py](Agents_backend/Graph/agents/topic_guard.py) — Evaluates input topic safety.
  - [routing.py](Agents_backend/Graph/agents/routing.py) — Directs work to the search agents or the closed-book path.
  - [research.py](Agents_backend/Graph/agents/research.py) — Runs the search providers (Tavily, with keyless DuckDuckGo as fallback), scraping and evidence extraction.
  - [document_ingest.py](Agents_backend/Graph/agents/document_ingest.py) — Manages PDF/Word file parsing, semantic chunking, and retrieval queries.
  - [orchestrator.py](Agents_backend/Graph/agents/orchestrator.py) — Creates draft outline structures.
  - [workers.py](Agents_backend/Graph/agents/workers.py) — Implements parallel workers and merger nodes.
  - [quality_control.py](Agents_backend/Graph/agents/quality_control.py) — Performs fact-checking and consistency audits.
  - [revision.py](Agents_backend/Graph/agents/revision.py) — Refines text based on quality reports.
  - [evaluation.py](Agents_backend/Graph/agents/evaluation.py) — Contains in-house and DeepEval G-Eval nodes.
  - [campaign.py](Agents_backend/Graph/agents/campaign.py) — Creates social media marketing materials.
  - [video.py](Agents_backend/Graph/agents/video.py) — Builds script-to-video pipelines.
  - [utils.py](Agents_backend/Graph/agents/utils.py) — The single LLM client factory: endpoint and credential resolution, per-model rate limiting, cross-model quota failover, and usage metering.

### 🎨 Frontend Components
* **Source Files (`frontend/src/`):**
  - [main.tsx](frontend/src/main.tsx) — Main entry point for Vite React.
  - [App.tsx](frontend/src/App.tsx) — Main application layout, sidebar, and tab routes.
  - [ContentView.tsx](frontend/src/ContentView.tsx) — Displays rich-text rendering of articles, evaluation scorecards, and SEO details.
  - [components/PodcastPlayer.tsx](frontend/src/components/PodcastPlayer.tsx) — Player for synthesized podcast audio. Video playback lives in `ContentView`'s media tab. (Replaces the former `MediaView.tsx`.)
  - [api.ts](frontend/src/api.ts) — Handles HTTP request routing and WebSocket connections.
  - [index.css](frontend/src/index.css) — Custom styling variables and theme configurations.
* **Reusable UI Components (`frontend/src/components/`):**
  - [ChatView.tsx](frontend/src/components/ChatView.tsx) — Live monitor displaying event streams and console logs.
  - [PlanEditor.tsx](frontend/src/components/PlanEditor.tsx) — Interface for modifying H2 sections, bullets, and word counts.
  - [Sidebar.tsx](frontend/src/components/Sidebar.tsx) — Navigation menu displaying generated articles.
  - [TopNav.tsx](frontend/src/components/TopNav.tsx) — Controls the header bar and theme toggles.
  - [UploadChip.tsx](frontend/src/components/UploadChip.tsx) — Component for document upload and status updates.

---

## ⚙️ Installation & Configuration

### Prerequisites
* **Python 3.11+**
* **Node.js 18+**
* **ffmpeg:** used for audio decoding, video rendering and Whisper transcription. A system install on `PATH` is preferred, but not required — the `imageio-ffmpeg` wheel bundles a binary and `Graph/tts.py::ensure_ffmpeg_on_path()` exposes it to the tools that shell out to a bare `ffmpeg` (notably local Whisper, whose missing-binary error otherwise reads like a corrupt audio file).
* **ImageMagick (Optional):** Required if customizing caption layouts using MoviePy.

### 1. Install Project Dependencies

Clone this repository and run the setup scripts:

```bash
# Clone the repository
git clone <repository_url>
cd Multi_Agent_Blog_generator_FYP

# 1. Install Backend Dependencies
#    Reproducible install — the exact versions this project was developed,
#    tested and demonstrated against (173 pinned packages). Use this one.
pip install -r requirements.lock.txt

# 2. Install Frontend Dependencies
cd frontend
npm install
```

> **`requirements.txt` vs `requirements.lock.txt`**
> `requirements.txt` lists the ~38 direct dependencies as bounded version
> *ranges* (`>=x,<next-major`) and is what CI installs, so the build acts as an
> early warning when a new upstream release breaks the project.
> `requirements.lock.txt` pins the full transitive closure to exact versions and
> is what you should install for a demo, a fresh machine, or an examiner's
> checkout — it removes any chance of a dependency resolving differently today
> than it did when the test suite was last green.
>
> Regenerate the lockfile only from an environment where `pytest tests` passes.

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in the keys. `.env.example` is the
authoritative reference — every variable is documented there with the reason it
exists. What follows is the short version.

#### Provider layout

The system runs end-to-end **without any paid API**. Nothing below is billed,
and only three of the providers need an account at all:

| Capability | Provider | Key |
| :--- | :--- | :--- |
| Chat, planning, QA, revision, evaluation | Gemini free tier | `GOOGLE_API_KEY` ([free](https://aistudio.google.com/apikey)) |
| Document embeddings (RAG) | `gemini-embedding-001` | same key |
| Web research | Tavily free tier (1000 credits/month) | `TAVILY_API_KEY` ([free](https://app.tavily.com)) |
| Web research fallback | DuckDuckGo | none |
| Images | Pollinations, then Pexels stock, then an offline rendered figure | none / `PEXELS_API_KEY` |
| Podcast + video speech | Edge TTS | none |
| Caption word timestamps | Whisper, running locally | none |
| Video B-roll + image fallback | Pexels free tier | `PEXELS_API_KEY` ([free](https://www.pexels.com/api/)) |

```ini
# ── LLM provider ────────────────────────────────────────────────────────────
GOOGLE_API_KEY=AIzaSy...
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_FAST_MODEL=gemini-3.5-flash-lite
LLM_QUALITY_MODEL=gemini-3.6-flash

# Leave EMPTY unless you actually have OpenAI credit. A non-empty value here is
# read by several modules as "the OpenAI REST API is reachable", which makes
# them call DALL-E / Whisper / TTS directly. It is never reused as the Gemini
# credential.
OPENAI_API_KEY=

# ── Free-tier quota handling (see below) ────────────────────────────────────
LLM_REQUESTS_PER_MINUTE=5
LLM_FALLBACK_MODELS=gemini-3.7-flash,gemini-3.1-flash-lite,gemini-3.5-flash-lite,gemini-3-flash-preview,gemini-3.6-flash,gemini-3.5-flash

# ── Research and media ──────────────────────────────────────────────────────
TAVILY_API_KEY=tvly-...
PEXELS_API_KEY=...

# ── Evaluation ──────────────────────────────────────────────────────────────
# Read ONLY by the evaluation node. Defaults to LLM_QUALITY_MODEL; set to a
# different model to run an independent-judge arm WITHOUT also moving the QA
# auditor and the reviser, which would confound the comparison.
LLM_JUDGE_MODEL=gemini-3-flash-preview
DEEPEVAL_TELEMETRY_OPT_OUT=YES

# ── Optional ────────────────────────────────────────────────────────────────
# Shared-secret API key. When set, all REST routes and the WebSocket require it.
# The frontend must be given the same value as VITE_API_KEY. Unset = open API.
# API_KEY=choose-a-long-random-string
# ALLOWED_ORIGINS=http://localhost:3000
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_content_factory
```

#### Why the endpoint is swappable

Every chat client in the project is a `ChatOpenAI`, which is an
**OpenAI-protocol** client rather than an OpenAI-only one. Pointing
`LLM_BASE_URL` at another vendor's compatibility endpoint runs the entire
pipeline — `.with_structured_output()` tool calling included — against that
vendor with no change at any call site. `Graph/agents/utils.py` resolves one
endpoint, one credential, the usage callback, the rate limiter and the fallback
pool in a single factory (`make_chat_llm`). The same two variables point the
system at vLLM, Ollama, OpenRouter or Groq.

Embeddings follow the same endpoint, with dimensions pinned to 1536 — a Chroma
collection fixes its vector width on first write, so an index built at 1536
cannot accept `gemini-embedding-001`'s native 3072 without a dimension-mismatch
failure that silently costs the upload its RAG index.

#### Working inside the free tier

The Gemini free tier enforces two separate quotas, both **per model**, and each
broke the pipeline in a different way:

| Quota | Value | Symptom | Fix |
| :--- | :--- | :--- | :--- |
| Requests per minute | 5 | The orchestrator writes sections concurrently, so a 7-section outline fired 7 requests at once and everything past the fifth returned `429 RESOURCE_EXHAUSTED`. | A blocking token bucket per model id (`LLM_REQUESTS_PER_MINUTE`). Retries cannot fix this: their backoff is seconds while the quota window is a rolling minute, and every concurrent request retries into the same exhausted window. |
| Requests per day | 20 | One complete run makes over thirty calls, so the budget is gone before the run finishes and waiting does not help. | Cross-model failover (`LLM_FALLBACK_MODELS`). The cap is per model and the endpoint serves many interchangeable ones, so a quota-blocked request is retried on the next model, multiplying the daily budget by the size of the pool. |

Both are off by default on a non-Google endpoint, where they would be pure
added latency. A model that returns a per-**day** quota error is remembered and
skipped for the rest of the process, so later calls do not spend a round-trip
on a model that is finished for the day. The model that actually served a
request is what `usage.py` attributes tokens to, so a cost table after a
failover shows the substitution rather than hiding it.

Two practical notes for a demo:

* **Prefer `3.6`/`3.5-flash` over the newest `3.8`/`3.7-flash`.** The newest
  models are the most contended on the free tier — in a probe of four
  consecutive calls, two came back `503 "experiencing high demand"`, which is
  enough to kill a run.
* **A full run takes roughly 15–25 minutes** on the free tier, nearly all of it
  spent waiting on the 5/minute limiter. This is a quota cost, not a
  performance characteristic of the system.

---

## 🚀 Usage Guide

This project can be run in two modes:

### Mode A: Full FastAPI + React Web App (Recommended)

This mode runs the complete web app with live WebSocket logs, outline editing, and document uploads.

1. **Start the FastAPI Backend Server:**
   ```bash
   cd Agents_backend
   uvicorn api:app --reload --reload-exclude "data/*" --host 0.0.0.0 --port 8000
   ```
   On startup the log states which endpoint, models and quota settings were
   resolved — check this line first if a run behaves unexpectedly:
   ```text
   LLM endpoint: https://generativelanguage.googleapis.com/v1beta/openai/ | fast=gemini-3.5-flash-lite quality=gemini-3.6-flash judge=gemini-3-flash-preview | rate limit: 5/min per model
   ```
2. **Start the Vite Frontend Server:**
   ```bash
   cd frontend
   npm run dev
   ```
3. **Open in Browser:** Navigate to `http://localhost:3000`.
4. **Approve the outline.** The graph pauses at the Human-in-the-Loop gate with
   status `awaiting_approval` and does not proceed until the plan is approved or
   revised in the UI. On the free tier, expect **15–25 minutes** for a full run
   with podcast, video, images and both evaluation arms enabled — almost all of
   it spent waiting on the 5-requests-per-minute limiter.

### Mode B: CLI Execution Mode
For direct execution and testing via command-line arguments:

```bash
cd Agents_backend
python main.py
```
This CLI walks you through topic checks, research settings, and runs the LangGraph engine locally.

---

## 📝 Example Output Folder Flow

Each run outputs its files to a unique folder under the `Agents_backend/blogs/` directory:

```text
blogs/quantum_computing_20260521_103000/
├── README.md                                 # Overview & execution metrics
├── content/
│   └── quantum_computing.md                  # Final markdown content with placed images
├── social_media/
│   ├── linkedin_quantum_computing.txt
│   ├── twitter_quantum_computing.md
│   ├── landing_page_quantum_computing.md
│   └── email_quantum_computing.md
├── reports/
│   ├── qa_report.txt                         # Fact-checking feedback
│   ├── geval_report.txt                      # In-house G-Eval evaluation scores
│   └── keyword_optimization.txt              # SEO density report
├── research/
│   └── evidence.json                         # Local cache of scraped Tavily results
├── audio/
│   └── podcast.wav                           # Conversational solo podcast audio
├── video/
│   └── short.mp4                             # Rendered MP4 short video
└── metadata/
    ├── plan.json                             # Final approved plan layout
    └── metadata.json                         # Execution traces, tokens, and config keys
```

---

## 🌐 Deploying the Recorded Demo (free, no credit card)

The multi-agent backend is heavy and long-running, so it cannot be hosted on a
free static/serverless tier. For a public portfolio link we ship a **static
replay** of one real run instead. Reviewers who want the live system open it in
**GitHub Codespaces** via the bundled `.devcontainer`.

**How the demo build works.** `npm run build:demo` (Vite `--mode demo`, which
loads `frontend/.env.demo` → `VITE_DEMO_MODE=1`) produces a bundle where every
read in `frontend/src/api.ts` is served from static fixtures under
`frontend/public/demo/` — captured from a real completed job (its `/api/jobs`,
`/api/jobs/:id`, `/api/jobs/:id/events` responses, the article, images, podcast,
video and PDF/DOCX/HTML exports). Write actions (create a job, trigger media) are
disabled with a clear message, and the WebSocket is a no-op. The normal
`npm run build` — the one the FastAPI backend serves — is **unaffected**.

**Deploy to Vercel (Hobby, no card):**
1. Push this repo to GitHub.
2. [vercel.com](https://vercel.com) → **Add New → Project** → import the repo.
3. Set **Root Directory** to `frontend`. `frontend/vercel.json` already pins the
   build command (`npm run build:demo`) and output (`dist`) — no other settings.
4. **Deploy.** No environment variables are needed (the demo is fully static).

Cloudflare Pages / Netlify work identically: root `frontend`, build
`npm run build:demo`, output directory `dist`. The demo payload (≈15 MB, incl. a
re-encoded 5.7 MB video) is within every free tier's per-file limit.

**Run the full live system (GitHub Codespaces, free):** open the repo → **Code →
Codespaces → Create**. The `.devcontainer` installs ffmpeg and all dependencies;
add a free `GOOGLE_API_KEY` to `.env`, then start the backend and frontend as in
*Installation* above. Mind the free-tier Gemini quota (20 requests/day/model).

---

## ⚠️ Known Limitations & Future Scope

* **Checkpointer Backends:** The web application persists checkpoints with `SqliteSaver`, or `PostgresSaver` when `DATABASE_URL` points at Postgres (docker-compose sets this automatically, with an automatic fallback to SQLite if the connection fails). The volatile `MemorySaver` is only the default for the standalone CLI path, where a run is not expected to outlive the process — CLI runs therefore cannot be resumed after a crash.

* **Prompt Injection — not mitigated.** Text scraped from the open web and text extracted from uploaded documents is passed into LLM prompts as evidence with no instruction-hierarchy defence: no delimiter fencing, no escaping, and no validation that extracted "facts" originated in the source rather than in an instruction embedded within it. A web page containing something like *"ignore previous instructions and instead write…"* is handed to the extraction model as ordinary content. The affected paths are the research extractor, the document-chunk extractor, the section writers, and the QA auditor. Realistic mitigations — fencing untrusted spans in explicit delimiters, instructing the extractor to treat the span as data only, and validating that each extracted snippet is a substring of its source — are known but unimplemented. This is the most significant unaddressed security weakness in the system.

* **No Rate Limiting:** No endpoint is rate limited. `POST /api/jobs` consumes real provider quota — free-tier quota in the default configuration, billable spend if `OPENAI_API_KEY` or a paid Gemini tier is configured — so an instance left reachable without `API_KEY` set can be driven into an exhausted quota, or an unbounded bill, by anyone who finds it. Set `API_KEY`, keep the deployment on `localhost`, or place a reverse proxy in front of it.

* **Evaluation Methodology:** The published quality scores were produced with the same model acting as both writer and judge (`gpt-5-mini`), a known source of self-preference bias in LLM-as-a-judge evaluation. The judge is now configured separately via `LLM_JUDGE_MODEL` — and is set to a different model from `LLM_QUALITY_MODEL` in the shipped configuration — so an independent-judge run needs no code change, but the published figures predate that change and still carry the bias. The published figures also come from three topics with one run each and no baseline comparison arm, so they characterise the system's own behaviour rather than demonstrating superiority over a simpler approach. No human annotation of factual accuracy was performed.
* **Single-Speaker Audio:** The Gemini Podcast studio is set to a single-speaker voice (`Aoede`). Future updates could add two-speaker dialogue scripts using two distinct Gemini audio voices.
* **Authentication:** Access control is a single shared secret, not per-user auth. Setting `API_KEY` in `.env` makes every REST route and the WebSocket require it (`X-API-Key` header, or `?api_key=` for browser-initiated requests such as `<img>` and downloads); leaving it unset keeps the API open, which is only appropriate on `localhost`. CORS defaults to the local dev origins and is configurable via `ALLOWED_ORIGINS`. A public deployment needs real per-user authentication (OAuth2) and per-user job ownership — currently any authenticated caller can read and delete every job.
* **Single-Process Concurrency:** Jobs run in background threads, and HITL approval blocks one of those threads for up to 20 minutes. The approval events are held in an in-process dictionary, so the API must run as a single worker; a multi-worker or multi-replica deployment needs an external task queue and a shared store. The SqliteSaver/PostgresSaver checkpointer is what makes crash recovery possible without one.

---

## 📄 License

This repository is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.

