import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas that performs a two-pass calculation for accurate 'Page X of Y' numbering."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Skip header/footer on title cover page
            return
        
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        
        # Header
        self.drawString(54, letter[1] - 36, "AI Content Factory — FYP Comprehensive Viva Defense Guide")
        self.drawRightString(letter[0] - 54, letter[1] - 36, "Confidential / Academic Defense")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)
        
        # Footer
        self.line(54, 45, letter[0] - 54, 45)
        self.drawString(54, 32, "Final Year Project (BS Computer Science) — State & Architecture Reference")
        self.drawRightString(letter[0] - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_pdf(filename="AI_Content_Factory_Viva_Preparation_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1E3A8A")     # Deep Blue
    c_secondary = colors.HexColor("#0D9488")   # Teal
    c_dark = colors.HexColor("#0F172A")        # Slate 900
    c_light_bg = colors.HexColor("#F8FAFC")    # Slate 50
    c_border = colors.HexColor("#E2E8F0")      # Slate 200
    c_accent = colors.HexColor("#B91C1C")      # Crimson Red
    c_code_bg = colors.HexColor("#F1F5F9")     # Slate 100

    # Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        alignment=1, # Center
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=25
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=c_primary,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B")
    )

    q_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True
    )

    a_style = ParagraphStyle(
        'AnswerStyle',
        parent=body_style,
        fontSize=9,
        leading=13,
        spaceAfter=8
    )

    story = []

    # ==========================================
    # COVER / HEADER BLOCK
    # ==========================================
    story.append(Spacer(1, 15))
    story.append(Paragraph("AI CONTENT FACTORY", title_style))
    story.append(Paragraph("Stateful Multi-Agent Orchestration & Evaluation Engine<br/><b>FINAL YEAR PROJECT (FYP) — COMPREHENSIVE VIVA DEFENSE GUIDE</b>", subtitle_style))
    
    meta_table_data = [
        [Paragraph("<b>Candidate Project:</b> AI Content Factory", body_style),
         Paragraph("<b>Date of Viva:</b> September 2026", body_style)],
        [Paragraph("<b>Focus Domain:</b> Multi-Agent Systems, RAG & Databases", body_style),
         Paragraph("<b>Primary Backend:</b> FastAPI + LangGraph + SQLite/ChromaDB", body_style)],
    ]
    t_meta = Table(meta_table_data, colWidths=[250, 250])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_light_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=5, spaceAfter=15))

    # ==========================================
    # SECTION 1: DATABASE ARCHITECTURE (DEEP DIVE)
    # ==========================================
    story.append(Paragraph("1. Exhaustive Database Architecture (Primary Defense Focus)", h1_style))
    story.append(Paragraph(
        "In this project, the data persistence tier is deliberately decoupled into <b>three distinct, specialized storage layers</b>. "
        "Each layer serves a fundamentally different purpose, handles different concurrency characteristics, and uses dedicated storage algorithms:",
        body_style
    ))

    db_overview_data = [
        [Paragraph("<b>Storage Layer</b>", body_style), Paragraph("<b>Technology / Engine</b>", body_style), Paragraph("<b>Primary Responsibility</b>", body_style), Paragraph("<b>File / Location</b>", body_style)],
        [
            Paragraph("<b>Relational Jobs Database</b>", body_style),
            Paragraph("SQLite 3 (WAL mode) / PostgreSQL", body_style),
            Paragraph("CRUD metadata for jobs, topics, configs, final markdown, SEO scores, media file links, and status transitions.", body_style),
            Paragraph("<code>Agents_backend/data/web_jobs.db</code>", body_style)
        ],
        [
            Paragraph("<b>State Graph Checkpointer</b>", body_style),
            Paragraph("LangGraph SqliteSaver / PostgresSaver", body_style),
            Paragraph("Binary state persistence, execution snapshots at every graph step, crash recovery, and Human-in-the-Loop (HITL) outline review resumption.", body_style),
            Paragraph("<code>Agents_backend/data/checkpoints.db</code>", body_style)
        ],
        [
            Paragraph("<b>Vector Embedding Database</b>", body_style),
            Paragraph("ChromaDB (HNSW index) / Chroma Cloud", body_style),
            Paragraph("Dense vector indexing of document chunks (PDF/DOCX/TXT) using 1536-dim OpenAI embeddings for cosine similarity RAG retrieval.", body_style),
            Paragraph("<code>Agents_backend/data/chroma_db/</code>", body_style)
        ]
    ]
    t_db = Table(db_overview_data, colWidths=[100, 110, 180, 110])
    t_db.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_code_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_db)
    story.append(Spacer(1, 10))

    # Subsection: Relational DB
    story.append(Paragraph("1.1 Relational Job Store (`web_jobs.db`)", h2_style))
    story.append(Paragraph(
        "<b>Table Name:</b> <code>web_jobs</code> | <b>Primary Key:</b> <code>id (TEXT / UUIDv4)</code><br/>"
        "<b>Key Columns:</b> <code>topic, tone, sections, status, created_at, completed_at, blog_folder, qa_score, qa_verdict, geval_scores (JSON), deepeval_scores (JSON), blog_file, podcast_file, video_file, plan_json (JSON), config_json (JSON)</code>.",
        body_style
    ))
    story.append(Paragraph("<b>Concurrency & Performance Engineering:</b>", body_style))
    story.append(Paragraph("• <b>WAL Mode (Write-Ahead Logging):</b> Enabled via <code>PRAGMA journal_mode=WAL;</code>. In traditional SQLite rollback journals, writers block all readers and readers block writers. In WAL mode, SQLite writes new transactions to a separate <code>.wal</code> file. Readers read committed snapshots concurrently without locking out background worker threads writing progress updates.", bullet_style))
    story.append(Paragraph("• <b>Busy Timeout:</b> <code>PRAGMA busy_timeout=30000;</code> instructs the SQLite engine to wait up to 30 seconds for locks to clear instead of immediately throwing <i>database is locked</i> exceptions.", bullet_style))
    story.append(Paragraph("• <b>Synchronous Setting:</b> <code>PRAGMA synchronous=NORMAL;</code> ensures safety while eliminating synchronous disk flushes on every write, improving transaction speed tenfold.", bullet_style))
    story.append(Paragraph("• <b>Thread Safety & Connection Lifecycle:</b> Managed using Python's <code>@contextmanager</code> in <code>db.py</code> (guaranteeing <code>conn.close()</code>) combined with an in-memory <code>_db_lock = threading.Lock()</code> for schema migrations.", bullet_style))
    story.append(Paragraph("• <b>Zero-Downtime Dynamic Auto-Migration:</b> <code>init_db()</code> queries <code>PRAGMA table_info(web_jobs)</code> at application boot. If new columns (such as <code>geval_scores</code> or <code>image_quality</code>) are missing, it executes atomic <code>ALTER TABLE ADD COLUMN</code> statements on the fly.", bullet_style))
    story.append(Paragraph("• <b>Dual Database Engine Support:</b> When <code>DATABASE_URL</code> is present (e.g., in Docker containerized deployments), <code>db.py</code> automatically redirects queries to <b>PostgreSQL</b> using <code>psycopg</code> connection pooling and translates parameter placeholders from <code>?</code> to <code>%s</code> via <code>_format_sql()</code>.", bullet_style))

    story.append(Spacer(1, 8))

    # Subsection: Checkpointer DB
    story.append(Paragraph("1.2 LangGraph State Checkpointer (`checkpoints.db`)", h2_style))
    story.append(Paragraph(
        "<b>Why is a State Checkpointer critical in Multi-Agent AI?</b><br/>"
        "Traditional LLM applications are stateless or rely on volatile RAM (like LangGraph's <code>MemorySaver</code>). If a generation takes 5 minutes and the server reboots, all intermediate work is lost. "
        "More critically, Human-in-the-Loop (HITL) requires halting the graph at the Orchestrator stage so the user can review and edit the outline in the frontend. While waiting for human input (up to 20 minutes), the thread must persist state durably.",
        body_style
    ))
    story.append(Paragraph("<b>Mechanics of LangGraph SqliteSaver / PostgresSaver:</b>", body_style))
    story.append(Paragraph("• <b>Thread Identification:</b> Every generation job receives a unique <code>thread_id = job_id</code> passed in <code>thread_cfg = {\"configurable\": {\"thread_id\": job_id}}</code>.", bullet_style))
    story.append(Paragraph("• <b>Internal Checkpoint Tables:</b> Managed automatically by <code>memory.setup()</code>, creating <code>checkpoints</code> and <code>writes</code> tables that store serialized state dictionaries (JSON/msgpack/binary blobs).", bullet_style))
    story.append(Paragraph("• <b>Interrupt After Orchestrator:</b> The graph is compiled with <code>interrupt_after=[\"orchestrator\"]</code>. When the Orchestrator finishes planning the outline, LangGraph writes the state snapshot and pauses. The API reads the plan, pushes it to the UI via WebSocket, and sets status to <code>awaiting_approval</code>.", bullet_style))
    story.append(Paragraph("• <b>Seamless Resumption:</b> When the user approves or refines the outline, the backend invokes <code>graph.stream(None, thread_cfg)</code>. Passing <code>None</code> signals LangGraph to fetch the latest state from <code>checkpoints.db</code> and resume directly into the parallel Worker fan-out without re-running Router or Research!", bullet_style))
    story.append(Paragraph("• <b>Crash Recovery:</b> If the API process crashes mid-generation, calling resume immediately recovers the exact step reached, saving real API tokens and avoiding repeated web research.", bullet_style))

    story.append(Spacer(1, 8))

    # Subsection: Vector DB
    story.append(Paragraph("1.3 ChromaDB Vector Store & Advanced RAG (`vector_store.py`)", h2_style))
    story.append(Paragraph(
        "<b>Why a Vector Database?</b> Relational databases excel at exact scalar queries (e.g. <code>id = '...'</code>), but cannot calculate conceptual semantic similarity. ChromaDB stores high-dimensional dense vector embeddings representing the mathematical meaning of text.",
        body_style
    ))
    story.append(Paragraph("<b>Technical Specifications:</b>", body_style))
    story.append(Paragraph("• <b>Collection Name:</b> <code>ai_content_factory_documents</code>", bullet_style))
    story.append(Paragraph("• <b>Embedding Model:</b> OpenAI <code>text-embedding-3-small</code> producing dense <b>1536-dimensional</b> floating point vectors.", bullet_style))
    story.append(Paragraph("• <b>Indexing Algorithm:</b> <b>HNSW</b> (Hierarchical Navigable Small World) graph index configured with Cosine Distance via <code>metadata={\"hnsw:space\": \"cosine\"}</code>. HNSW achieves logarithmic query complexity O(log N) for Approximate Nearest Neighbor (ANN) searches.", bullet_style))
    story.append(Paragraph("• <b>Chunking & Ingestion Strategy:</b> Uploaded PDFs/DOCXs are parsed via <code>pypdf</code> or <code>python-docx</code>. The system performs character chunking (6,000 characters ≈ 1,500 tokens with 400 char overlap) and semantic chunking using cosine similarity boundaries across adjacent sentence embeddings.", bullet_style))
    story.append(Paragraph("• <b>Three-Tier Fail-Safe Retrieval:</b> (1) Query ChromaDB collection filtered by <code>upload_id</code>; (2) In-memory NumPy cosine similarity calculation if Chroma server has transient issues; (3) Fallback to extracted document evidence pool. This guarantees the pipeline never crashes on retrieval.", bullet_style))

    story.append(Spacer(1, 15))

    # ==========================================
    # SECTION 2: SYSTEM ARCHITECTURE
    # ==========================================
    story.append(Paragraph("2. Complete End-to-End System Architecture", h1_style))
    story.append(Paragraph(
        "The system follows an asynchronous, decoupled client-server architecture. The backend engine coordinates a <b>stateful, cyclic directed graph</b> powered by LangGraph, FastAPI, and WebSocket streaming.",
        body_style
    ))
    
    arch_steps = [
        ("1. Topic Guard & Validation", "Deterministic regex screen rejects empty/gibberish input; gpt-5-mini verifies semantic safety before job creation to protect API budget."),
        ("2. Router Agent", "Evaluates prompt complexity to choose between closed_book (no search), hybrid (doc RAG + search), or open_book (web search only)."),
        ("3. Document Ingest / RAG", "Executes semantic chunking and ChromaDB HNSW indexing. Retrieves topic-focused evidence slices."),
        ("4. Research Agent", "Fires parallel queries to Tavily Search API, scrapes full web content via Jina Reader (BeautifulSoup fallback), filters duplicate content via Jaccard similarity."),
        ("5. Orchestrator Agent (HITL)", "Plans outline (H2 titles, bullet points, word counts) and partitions evidence across sections. Graph interrupts execution for human outline approval."),
        ("6. Parallel Worker Fan-Out", "LangGraph Send() primitive spawns concurrent Worker agents. Each worker writes its section using ONLY its assigned evidence partition (preventing source-stuffing)."),
        ("7. Reducer Subgraph", "Deterministic Python module that joins sections in order, generates SEO metadata, and places AI-generated images (DALL-E 3 / Flux)."),
        ("8. Completion Validator", "Regex validation checking for missing headers and word count thresholds with automated repair routines."),
        ("9. Quality Control Auditor", "Audits content for hallucinations. Runs a non-LLM citation verifier checking every URL against research evidence; flags critical issues."),
        ("10. Revision Agent (Cyclic Loop)", "Surgically rewrites only sections with critical errors. Loops back to QA Auditor (bounded at 2 revisions max to prevent infinite recursion)."),
        ("11. Keyword SEO Optimizer", "Deterministic density calculation; weaves underrepresented keywords into passages."),
        ("12. G-Eval Scorecard", "In-house LLM judge grading Coherence (30%), Relevance (20%), Accuracy (30%), and Tone (20%) on a 1.0–5.0 scale."),
        ("13. Parallel Media Fan-Out", "Forks simultaneously into Campaign Gen (LinkedIn/Twitter), Video Gen (MoviePy + Whisper captions + Pexels B-roll), and Podcast Studio (Gemini 2.5 Flash audio)."),
        ("14. On-Demand DeepEval Audit", "Independent academic audit (Liu et al. 2023) triggered via separate REST endpoint on demand.")
    ]

    for title, desc in arch_steps:
        story.append(Paragraph(f"<b>{title}:</b> {desc}", bullet_style))

    story.append(Spacer(1, 15))

    # ==========================================
    # SECTION 3: TECH STACK BREAKDOWN & RATIONALE
    # ==========================================
    story.append(Paragraph("3. Technology Stack Breakdown & Contribution", h1_style))
    story.append(Paragraph(
        "Examiners frequently ask: <i>'Why did you choose this specific library instead of alternative X?'</i> Here is the technical justification for every key tool:",
        body_style
    ))

    tech_table_data = [
        [Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Version</b>", body_style), Paragraph("<b>Role in Project</b>", body_style), Paragraph("<b>Why Chosen / Contribution</b>", body_style)],
        [
            Paragraph("<b>FastAPI</b>", body_style),
            Paragraph("0.115+", body_style),
            Paragraph("Backend Web Framework", body_style),
            Paragraph("Asynchronous ASGI performance, automatic OpenAPI/Swagger docs, native WebSocket support for streaming live agent execution events to the UI.", body_style)
        ],
        [
            Paragraph("<b>LangGraph</b>", body_style),
            Paragraph("1.2+", body_style),
            Paragraph("Multi-Agent Orchestrator", body_style),
            Paragraph("Provides stateful cyclic graph execution, checkpoint persistence, Send() parallel fan-out, and interrupt_after for Human-in-the-Loop workflows.", body_style)
        ],
        [
            Paragraph("<b>ChromaDB</b>", body_style),
            Paragraph("1.5+", body_style),
            Paragraph("Vector Database", body_style),
            Paragraph("Embedded open-source vector store with native HNSW indexing, cosine similarity metrics, and local disk persistence without requiring a standalone daemon.", body_style)
        ],
        [
            Paragraph("<b>SQLite 3 (WAL)</b>", body_style),
            Paragraph("Built-in", body_style),
            Paragraph("Relational & State Storage", body_style),
            Paragraph("Zero-config, serverless, embeddable. Configured with Write-Ahead Logging (WAL) and 30s busy timeout for high-concurrency background threads.", body_style)
        ],
        [
            Paragraph("<b>MoviePy 2 + FFmpeg</b>", body_style),
            Paragraph("2.2+", body_style),
            Paragraph("Automated Video Rendering", body_style),
            Paragraph("Programmatic compositing of 9:16 vertical short videos, audio synchronization, stock B-roll clip trimming, and subtitle burning.", body_style)
        ],
        [
            Paragraph("<b>OpenAI Whisper</b>", body_style),
            Paragraph("20250625", body_style),
            Paragraph("Audio Transcription & Alignment", body_style),
            Paragraph("Provides word-level timestamps on synthesized TTS audio to render synchronized, karaoke-style video captions.", body_style)
        ],
        [
            Paragraph("<b>DeepEval</b>", body_style),
            Paragraph("4.2+", body_style),
            Paragraph("Academic LLM Evaluation", body_style),
            Paragraph("Implements the official G-Eval framework (Liu et al. 2023) using chain-of-thought grading for academic rigor and audit trails.", body_style)
        ],
        [
            Paragraph("<b>React 19 + Vite</b>", body_style),
            Paragraph("19.0 / 6.2+", body_style),
            Paragraph("Frontend UI & Tooling", body_style),
            Paragraph("Ultra-fast HMR, component modularity, real-time WebSocket state management, interactive outline plan editor, and rich markdown rendering.", body_style)
        ],
        [
            Paragraph("<b>Tailwind CSS v4</b>", body_style),
            Paragraph("4.1+", body_style),
            Paragraph("UI Styling Engine", body_style),
            Paragraph("Modern CSS theme variables, fluid responsive layouts, glassmorphic dark-mode aesthetics, and zero runtime CSS overhead.", body_style)
        ]
    ]

    t_tech = Table(tech_table_data, colWidths=[90, 55, 120, 235])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_code_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 15))

    # ==========================================
    # SECTION 4: MODELS & EXTERNAL APIS
    # ==========================================
    story.append(Paragraph("4. AI Models & External APIs Catalog", h1_style))
    story.append(Paragraph(
        "The system harnesses specialized, state-of-the-art models matched to specific tasks to balance reasoning accuracy, execution latency, and cost:",
        body_style
    ))

    model_table_data = [
        [Paragraph("<b>Model / API</b>", body_style), Paragraph("<b>Provider</b>", body_style), Paragraph("<b>Pipeline Function</b>", body_style), Paragraph("<b>Key Characteristics</b>", body_style)],
        [
            Paragraph("<b>gpt-5-mini / gpt-4o-mini</b>", body_style),
            Paragraph("OpenAI", body_style),
            Paragraph("Routing, Research Extraction, Workers, QA, Revision, Campaigns", body_style),
            Paragraph("Fast reasoning, high context window, JSON mode structured outputs, highly cost-effective for parallel worker fan-out.", body_style)
        ],
        [
            Paragraph("<b>text-embedding-3-small</b>", body_style),
            Paragraph("OpenAI", body_style),
            Paragraph("Semantic Chunking & Vector RAG", body_style),
            Paragraph("1536 embedding dimensions, high MTEB benchmark score, cosine similarity normalized.", body_style)
        ],
        [
            Paragraph("<b>gemini-2.5-flash</b>", body_style),
            Paragraph("Google DeepMind", body_style),
            Paragraph("Gemini Podcast Studio", body_style),
            Paragraph("Native audio generation direct from model (voice 'Aoede') — not synthetic robotic TTS, but human-like conversational inflection.", body_style)
        ],
        [
            Paragraph("<b>Gemini TTS & Whisper</b>", body_style),
            Paragraph("Google & OpenAI", body_style),
            Paragraph("Video Voiceover & Word Alignment", body_style),
            Paragraph("Gemini synthesizes natural voiceover script; Whisper generates precise word-level SRT timestamps for subtitles.", body_style)
        ],
        [
            Paragraph("<b>DALL·E 3 / Flux</b>", body_style),
            Paragraph("OpenAI / Pollinations", body_style),
            Paragraph("Blog Article Image Generation", body_style),
            Paragraph("3-provider fallback chain (OpenAI -> Gemini Imagen -> Pollinations Flux) ensures image generation never fails.", body_style)
        ],
        [
            Paragraph("<b>Tavily Search API</b>", body_style),
            Paragraph("Tavily AI", body_style),
            Paragraph("Web Research Intelligence", body_style),
            Paragraph("Engineered specifically for AI agents: returns clean, structured search results and raw text without web scraping boilerplate.", body_style)
        ],
        [
            Paragraph("<b>Pexels Video API</b>", body_style),
            Paragraph("Pexels", body_style),
            Paragraph("B-roll Video Retrieval", body_style),
            Paragraph("Queries royalty-free portrait (9:16) HD video clips matching the topic for background montage in video synthesis.", body_style)
        ]
    ]

    t_mod = Table(model_table_data, colWidths=[105, 85, 140, 170])
    t_mod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_code_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_mod)
    story.append(Spacer(1, 15))

    # ==========================================
    # SECTION 5: VIVA QUESTIONS & WINNING DEFENSE
    # ==========================================
    story.append(Paragraph("5. Top 15 Examiner Database & Architecture Questions (With Winning Answers)", h1_style))
    story.append(Paragraph(
        "These are the exact high-probability questions examiners ask during FYP vivas, paired with high-scoring, technically precise answers:",
        body_style
    ))

    qa_list = [
        (
            "Q1: Why did you choose SQLite for this project instead of a full client-server database like MySQL or MongoDB?",
            "<b>Winning Answer:</b> For our architecture, SQLite is an intentional engineering decision, not a compromise. "
            "First, SQLite is serverless and embeds directly into the Python process memory space, eliminating network socket latency (IPC) for state lookups. "
            "Second, with <b>WAL mode (Write-Ahead Logging)</b> enabled (<code>PRAGMA journal_mode=WAL</code>), readers do not block writers and writers do not block readers, providing excellent read/write concurrency for background worker threads. "
            "Third, our codebase is architected with dual-database capability in <code>db.py</code>: if <code>DATABASE_URL</code> is supplied, the entire persistence layer seamlessly redirects to <b>PostgreSQL</b> using <code>psycopg</code> connection pooling. Thus, SQLite powers self-contained local development, while PostgreSQL is ready for multi-container production."
        ),
        (
            "Q2: What is WAL Mode in SQLite and why did you enable it?",
            "<b>Winning Answer:</b> By default, SQLite uses a rollback journal where a write operation locks the entire database file, causing <code>sqlite3.OperationalError: database is locked</code> when multiple concurrent threads or background API workers execute. "
            "In WAL mode (Write-Ahead Logging), changes are written sequentially to a separate <code>.wal</code> file while the original database remains untouched. Readers can read committed database pages concurrently while the background worker appends writes. Combined with <code>PRAGMA busy_timeout=30000;</code>, WAL mode completely eliminates locking crashes during parallel agent execution."
        ),
        (
            "Q3: What is LangGraph's checkpointer database and why couldn't you just use Python global variables?",
            "<b>Winning Answer:</b> Python global variables or in-memory state (like <code>MemorySaver</code>) are volatile: if the application server restarts, crashes, or scales across processes, all active state is wiped. "
            "Our system uses <b>SqliteSaver</b> (and <b>PostgresSaver</b>) pointing to <code>checkpoints.db</code>. It stores a binary snapshot of the entire graph state at each node transition keyed by <code>thread_id</code>. "
            "This enables two mission-critical capabilities: "
            "1) <b>Human-in-the-Loop (HITL) Outline Control:</b> The graph pauses after the Orchestrator node (<code>interrupt_after=['orchestrator']</code>) and the thread yields. The user can take 15 minutes to review and edit the outline in the frontend. When submitted, the backend resumes from the checkpoint via <code>graph.stream(None, thread_cfg)</code>. "
            "2) <b>Crash Recovery:</b> If the server crashes mid-pipeline, the job can be resumed from the exact last saved step without repeating expensive research or LLM calls."
        ),
        (
            "Q4: Why do you need ChromaDB if you already have SQLite? Can't SQLite store vectors?",
            "<b>Winning Answer:</b> SQLite is a relational B-Tree database optimized for exact match lookups (O(log N)) and structured relational joins. It cannot calculate high-dimensional geometric distances. "
            "In our Advanced RAG pipeline, documents are embedded into <b>1536-dimensional vectors</b> using OpenAI's <code>text-embedding-3-small</code>. "
            "ChromaDB implements the <b>HNSW (Hierarchical Navigable Small World)</b> graph indexing algorithm. HNSW enables Approximate Nearest Neighbor (ANN) search across dense vector spaces in logarithmic time O(log N) using <b>Cosine Similarity</b>. Doing this in relational SQLite would require scanning every row (O(N)) and computing dot products in Python, which is computationally prohibitive on large corpora."
        ),
        (
            "Q5: How does your RAG pipeline chunk documents and prevent hallucination?",
            "<b>Winning Answer:</b> Ingestion follows a two-tier strategy in <code>document_ingest.py</code>: "
            "1) Character chunking (6,000 characters with 400-character overlap) preserves paragraph context. "
            "2) Semantic chunking calculates cosine similarity deltas across adjacent sentence embeddings to split text at natural topical shifts. "
            "Each chunk preserves metadata including <code>page_start</code> and <code>page_end</code>. "
            "To prevent hallucination, the Orchestrator partitions evidence across parallel workers so workers cite distinct sources. Furthermore, the <b>Quality Control Auditor</b> runs a deterministic Python citation verifier that parses all generated URLs and cross-references them against the original evidence; any ungrounded claim forces a revision."
        ),
        (
            "Q6: Explain the database schema of `web_jobs`. How did you handle unstructured data like configs and scores?",
            "<b>Winning Answer:</b> The <code>web_jobs</code> table uses a hybrid structured-unstructured design: "
            "Standard scalar attributes (<code>id, topic, tone, sections, status, created_at, completed_at, blog_folder</code>) are strongly typed columns with indexes for fast sorting and filtering. "
            "Complex nested structures — such as <code>config_json</code> (generation settings), <code>plan_json</code> (outline tree), <code>geval_scores</code>, and <code>deepeval_scores</code> (academic evaluation rubrics) — are serialized as JSON strings. "
            "In <code>db.py</code>, helper functions automatically serialize and deserialize these fields, providing the schema flexibility of a document store like MongoDB with the relational integrity of SQLite/PostgreSQL."
        ),
        (
            "Q7: How did you handle schema migrations when you added new features?",
            "<b>Winning Answer:</b> Rather than requiring a heavy external migration framework like Alembic for our SQLite setup, <code>db.py</code> implements a lightweight, zero-downtime auto-migration pattern in <code>init_db()</code>. "
            "On server startup, it executes <code>PRAGMA table_info(web_jobs)</code>, inspects existing column names, and runs dynamic <code>ALTER TABLE web_jobs ADD COLUMN ...</code> statements for any new features (e.g. <code>geval_scores, deepeval_scores, config_json</code>). This ensures seamless backward compatibility with existing databases."
        ),
        (
            "Q8: What happens if two users generate blogs at the exact same time? How does your system handle concurrency?",
            "<b>Winning Answer:</b> Concurrency is handled across three layers: "
            "1) <b>FastAPI & Asynchronous Event Loop:</b> FastAPI handles HTTP requests asynchronously on Uvicorn worker threads. "
            "2) <b>Thread Isolation:</b> Each job runs inside a dedicated background worker thread with a unique <code>job_id</code> and <code>thread_id</code>. State is never shared between jobs. "
            "3) <b>Database Level:</b> SQLite WAL mode allows concurrent readers while writes wait up to 30 seconds (<code>busy_timeout=30000</code>). In PostgreSQL deployments, connection pooling (<code>ConnectionPool(max_size=20)</code>) guarantees dedicated client connections for parallel transactions."
        ),
        (
            "Q9: What is the LangGraph `Send()` API and how is it used in your parallel workers?",
            "<b>Winning Answer:</b> <code>Send()</code> is LangGraph's dynamic map-reduce primitive for fan-out orchestration. "
            "After the outline is approved, the Orchestrator produces a list of section tasks. The graph edge uses <code>Send('worker', task_state)</code> to spawn N independent worker executions concurrently. "
            "Each worker receives only its assigned section task and its partitioned evidence slice. When all parallel workers complete, LangGraph collects their state outputs and forwards them to the <b>Reducer</b> node to assemble the complete draft."
        ),
        (
            "Q10: Why is G-Eval run before media generators and not after?",
            "<b>Winning Answer:</b> G-Eval evaluates the quality of the written article itself (Coherence, Relevance, Accuracy, Tone). "
            "Because Campaign, Video, and Podcast generation nodes depend on the validated, SEO-optimized text produced by the earlier nodes, running G-Eval immediately after the Keyword Optimizer ensures that media generators receive the finalized, scored content. It also allows media generators to execute in parallel fan-out without blocking evaluation."
        ),
        (
            "Q11: What is the difference between In-house G-Eval and DeepEval in your project?",
            "<b>Winning Answer:</b> Our project offers two complementary evaluation modes: "
            "1) <b>In-House G-Eval (`geval_scores`):</b> Runs automatically inside the graph pipeline using structured LLM outputs to grade sections on a 1.0–5.0 scale across 4 rubrics. The overall score is calculated via deterministic Python weights (30% Coherence, 20% Relevance, 30% Accuracy, 20% Tone). "
            "2) <b>Official DeepEval (`deepeval_scores`):</b> Runs <b>on demand</b> via a dedicated endpoint (<code>POST /api/jobs/{job_id}/run-deepeval</code>) using the Confident AI DeepEval library. It executes full Chain-of-Thought (CoT) evaluation (Liu et al. 2023) normalized to a 0.0–1.0 scale. It is kept on demand to avoid incurring 4 extra judge calls on every default generation."
        ),
        (
            "Q12: How does the Gemini Podcast Studio work? Is it text-to-speech?",
            "<b>Winning Answer:</b> It is not traditional robotic TTS (like gTTS or Windows Speech). "
            "It utilizes Google DeepMind's <b>Gemini 2.5 Flash native audio output</b> via the <code>google-genai</code> SDK. We prompt the model to generate spoken conversational audio directly (voice 'Aoede') in raw PCM/WAV format. The model produces natural breathing, conversational pauses, and speech inflections that conventional concatenative or parametric TTS engines cannot replicate."
        ),
        (
            "Q13: How does the Video Synthesis pipeline work?",
            "<b>Winning Answer:</b> Video generation in <code>video.py</code> is an automated multi-step pipeline: "
            "1) The LLM writes a vertical short script with scene breakdowns and voiceover narration. "
            "2) Voiceover audio is generated via Gemini TTS. "
            "3) <b>OpenAI Whisper</b> processes the synthesized audio to generate exact word-level timestamps. "
            "4) The <b>Pexels API</b> queries and downloads vertical (9:16) royalty-free B-roll footage matching the script topics. "
            "5) <b>MoviePy and FFmpeg</b> composite the B-roll clips, synchronize background music, and render synchronized karaoke captions into a final MP4 video."
        ),
        (
            "Q14: Explain the cyclic loop between QA Agent and Revision Agent. How do you prevent infinite loops?",
            "<b>Winning Answer:</b> Unlike traditional acyclic DAGs, LangGraph allows cyclic graphs. "
            "The QA Agent audits the draft against the research evidence pool and identifies hallucinated claims or citation errors. "
            "If critical issues exist, the conditional edge routes to the <b>Revision Agent</b>, which surgically rewrites only the defective sections and routes back to the QA Agent. "
            "To prevent infinite loops and unbounded token consumption, the loop is strictly bounded by <code>MAX_REVISIONS = 2</code>. If the limit is reached, the pipeline accepts the best-effort draft and proceeds to the Keyword Optimizer."
        ),
        (
            "Q15: What are the primary limitations of this system?",
            "<b>Winning Answer:</b> As documented in our thesis, the key limitations are: "
            "1) <b>Single-worker concurrency for HITL:</b> Approval events are held in an in-memory event dictionary; scaling across multiple server instances requires a distributed Redis queue. "
            "2) <b>Prompt Injection defense:</b> Content scraped from the open web is treated as data, but advanced adversarial prompt injection defenses (e.g. instruction fencing) are identified as future scope. "
            "3) <b>Authentication:</b> Access is secured via a shared-secret API key rather than full multi-tenant OAuth2 user accounts."
        )
    ]

    for q, a in qa_list:
        card_data = [
            [Paragraph(q, q_style)],
            [Paragraph(a, a_style)]
        ]
        t_card = Table(card_data, colWidths=[500])
        t_card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_light_bg),
            ('BOX', (0,0), (-1,-1), 1, c_border),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_card)
        story.append(Spacer(1, 6))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF Generated successfully at: {Path(filename).resolve()}")

if __name__ == "__main__":
    out_pdf = sys.argv[1] if len(sys.argv) > 1 else "AI_Content_Factory_Viva_Preparation_Guide.pdf"
    build_pdf(out_pdf)
