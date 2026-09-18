import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
            return
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        self.drawString(54, letter[1] - 36, "AI Content Factory — Simplified Viva Cheat Sheet")
        self.drawRightString(letter[0] - 54, letter[1] - 36, "Student Defense Companion")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)
        
        self.line(54, 45, letter[0] - 54, 45)
        self.drawString(54, 32, "Plain English Explanation — FYP Viva 2026")
        self.drawRightString(letter[0] - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf(filename="AI_Content_Factory_Viva_CheatSheet_Easy.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()

    c_primary = colors.HexColor("#1E40AF")     # Blue
    c_secondary = colors.HexColor("#047857")   # Emerald
    c_dark = colors.HexColor("#1F2937")
    c_bg = colors.HexColor("#F9FAFB")
    c_card_bg = colors.HexColor("#F0FDF4")     # Light green tint
    c_border = colors.HexColor("#E5E7EB")

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=c_primary,
        alignment=1,
        spaceAfter=8
    )

    sub_style = ParagraphStyle(
        'SubStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4B5563"),
        alignment=1,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1Style',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=c_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    q_style = ParagraphStyle(
        'QStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=c_primary,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    a_style = ParagraphStyle(
        'AStyle',
        parent=body_style,
        fontSize=9,
        leading=13,
        spaceAfter=6
    )

    story = []

    # Title Block
    story.append(Paragraph("AI CONTENT FACTORY — VIVA CHEAT SHEET", title_style))
    story.append(Paragraph("<b>Easy Terms & Plain English Guide for Tomorrow's Defense</b>", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=0, spaceAfter=12))

    # Big Picture
    story.append(Paragraph("💡 The 1-Minute Pitch (What is this project?)", h1_style))
    story.append(Paragraph(
        "<i>'Sir, my project is like an automated digital publishing house. A user gives it a topic or uploads a document (like a PDF). A team of AI agents then works together to research the topic on Google, plan an outline, write the sections in parallel, fact-check the writing, generate high-quality images, create an audio podcast with human-like voice, and render a short video with captions. The user also has full control to edit the outline before the article is written.'</i>",
        body_style
    ))
    story.append(Spacer(1, 8))

    # The 3 Databases
    story.append(Paragraph("🗄️ The 3 Databases Explained (Very Simple Terms)", h1_style))
    story.append(Paragraph(
        "Examiners love databases! Tell them: <b>'Sir, we use 3 different databases because each one does a completely different job.'</b>",
        body_style
    ))

    db_data = [
        [Paragraph("<b>Database</b>", body_style), Paragraph("<b>Everyday Analogy</b>", body_style), Paragraph("<b>What it actually stores in simple words</b>", body_style)],
        [
            Paragraph("<b>1. SQLite (web_jobs.db)</b>", body_style),
            Paragraph("<b>The Office Register</b>", body_style),
            Paragraph("Keeps a row for each article: What was the topic? Is it running or finished? What is the final text? Where are the video and podcast files saved? What were the scores?", body_style)
        ],
        [
            Paragraph("<b>2. Checkpointer (checkpoints.db)</b>", body_style),
            Paragraph("<b>The Video Game Save Point</b>", body_style),
            Paragraph("Saves the AI's exact memory step-by-step. When the AI finishes planning the outline, it pauses and saves here. The user can take 10 minutes to review the outline. When clicked 'Approve', it resumes from this save point without starting over.", body_style)
        ],
        [
            Paragraph("<b>3. ChromaDB (Vector DB)</b>", body_style),
            Paragraph("<b>The Smart Library Brain</b>", body_style),
            Paragraph("Regular databases search for exact words. ChromaDB understands <i>meaning</i>. When you upload a 50-page PDF, it turns text into math numbers (vectors). When writing about 'cost', it instantly finds the exact pages about 'pricing' and 'budget' even if the exact word isn't there.", body_style)
        ]
    ]
    t_db = Table(db_data, colWidths=[130, 110, 260])
    t_db.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_db)
    story.append(Spacer(1, 10))

    # Crucial SQLite terms
    story.append(Paragraph("🔑 3 SQLite Terms You MUST Know Tomorrow:", h2_style))
    story.append(Paragraph("• <b>WAL Mode (Write-Ahead Logging):</b> Normally in SQLite, if one person writes, nobody can read. WAL mode creates a small notepad file (.wal). The AI writes its progress to the notepad while the frontend reads the database without freezing or locking up.", bullet_style))
    story.append(Paragraph("• <b>Busy Timeout:</b> Tells SQLite: <i>'If another thread is writing, don't crash! Wait up to 30 seconds for it to finish.'</i>", bullet_style))
    story.append(Paragraph("• <b>PostgreSQL Ready:</b> SQLite is used for local running. But in Docker/production, setting one environment variable switches everything to PostgreSQL automatically.", bullet_style))

    story.append(Spacer(1, 10))

    # The Architecture
    story.append(Paragraph("🏗️ How the Project Works (The Factory Assembly Line)", h1_style))
    story.append(Paragraph("Imagine a conveyor belt with specialized workers at each station:", body_style))
    
    steps = [
        ("Station 1: Topic Guard", "Checks if the user's prompt is sensible and safe before spending any API money."),
        ("Station 2: Router", "Decides: Do we need Google search? Or do we use the uploaded PDF? Or can the AI write from general knowledge?"),
        ("Station 3: Researcher", "Searches the web via Tavily API and scrapes real articles so the blog has real facts and sources."),
        ("Station 4: Orchestrator (Manager)", "Plans the outline (headings and bullet points). Then it <b>pauses and asks YOU</b> in the UI: <i>'Do you like this outline?'</i> (This is Human-in-the-Loop)."),
        ("Station 5: Parallel Writers", "Instead of writing chapter by chapter, 3 or 4 AI writers write different sections <b>at the exact same time</b>. This makes generation 3x faster!"),
        ("Station 6: Reducer & Validator", "Glues the sections together into one article, checks word counts, and generates nice images."),
        ("Station 7: Quality Control & Revision", "A strict AI fact-checker reads the draft. If it finds made-up claims or bad links, it sends it to the Revision Agent to rewrite it (up to 2 times)."),
        ("Station 8: Media Studio", "Creates a LinkedIn post, an X (Twitter) thread, an audio podcast (using Google's Gemini voice), and a short 9:16 video with captions."),
    ]
    for s_title, s_desc in steps:
        story.append(Paragraph(f"• <b>{s_title}:</b> {s_desc}", bullet_style))

    story.append(Spacer(1, 10))

    # Tech Stack & Models
    story.append(Paragraph("⚙️ Tech Stack & Models in Plain English", h1_style))
    story.append(Paragraph("• <b>FastAPI:</b> The Python backend that talks to the frontend and streams live logs.", bullet_style))
    story.append(Paragraph("• <b>LangGraph:</b> The AI manager that controls the flow, loops, parallel writing, and pause/resume.", bullet_style))
    story.append(Paragraph("• <b>React 19 + Vite + Tailwind:</b> The frontend dashboard where you type the topic, view live progress, edit outlines, and play video/podcasts.", bullet_style))
    story.append(Paragraph("• <b>MoviePy & Whisper:</b> MoviePy stitches B-roll videos from Pexels; Whisper listens to the audio and puts word-by-word karaoke subtitles on the screen.", bullet_style))
    story.append(Paragraph("• <b>OpenAI (gpt-5-mini / gpt-4o):</b> The main brain for writing, researching, and fact-checking.", bullet_style))
    story.append(Paragraph("• <b>Google Gemini 2.5 Flash:</b> Used for the Podcast Studio because it produces natural human voice directly, not robotic robotic text-to-speech.", bullet_style))

    story.append(Spacer(1, 10))

    # Top Examiner Questions
    story.append(Paragraph("🎯 Exact Answers to Speak in Your Viva Tomorrow", h1_style))

    qa_simple = [
        (
            "Examiner: 'Why did you use SQLite and not MySQL / MongoDB?'",
            "<i>'Sir, SQLite runs directly inside our Python application without needing to set up or manage a separate database server. It is extremely fast for our use case. Also, with WAL mode enabled, it handles our background threads smoothly without locking. Furthermore, our code is written so that if we deploy with Docker, setting DATABASE_URL switches it to PostgreSQL with zero code changes.'</i>"
        ),
        (
            "Examiner: 'What is a Vector Database (ChromaDB) and why is it needed?'",
            "<i>'Sir, regular databases can only find exact words like WHERE name=\"John\". But when someone uploads a 50-page PDF and asks a question, we need to find text based on meaning. ChromaDB converts text into mathematical coordinates (vectors). When you search, it finds the paragraphs closest in meaning in milliseconds.'</i>"
        ),
        (
            "Examiner: 'What is Checkpointing in LangGraph?'",
            "<i>'Sir, checkpointing is like a game save file. If our AI generation takes 3 minutes and the computer restarts, normal memory is lost. But LangGraph saves the state at each step to checkpoints.db. It also allows our Human-in-the-Loop feature: the AI plans the outline, saves its state, waits for the user to edit or approve the outline in the UI, and then resumes seamlessly.'</i>"
        ),
        (
            "Examiner: 'How do you prevent the AI from hallucinating (making things up)?'",
            "<i>'Sir, three ways: First, we do RAG and Google search to feed it real evidence. Second, our Orchestrator splits evidence so different sections cite different sources. Third, we have a Quality Control agent that checks every URL and claim against the collected evidence. If something doesn't match, it forces a rewrite.'</i>"
        ),
        (
            "Examiner: 'What is Human-in-the-Loop (HITL)?'",
            "<i>'Sir, fully automated AI can sometimes write about the wrong focus. Human-in-the-Loop means the system pauses before writing the full article and lets the human review and modify the outline in the UI. Only when the human is satisfied does the system continue.'</i>"
        )
    ]

    for q, a in qa_simple:
        box_data = [
            [Paragraph(f"<b>{q}</b>", q_style)],
            [Paragraph(a, a_style)]
        ]
        t_box = Table(box_data, colWidths=[500])
        t_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#A7F3D0")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_box)
        story.append(Spacer(1, 5))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("[SUCCESS] Easy Viva PDF Generated!")

if __name__ == "__main__":
    build_pdf("AI_Content_Factory_Viva_CheatSheet_Easy.pdf")
